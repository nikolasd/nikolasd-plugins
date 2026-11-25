#Requires -Version 7.2
<#
.SYNOPSIS
    Syncs Git Town branches the way `git town sync` does, including branches that are checked
    out in other worktrees.

.DESCRIPTION
    `git town sync` skips every branch that is checked out in another worktree. This script
    syncs those branches too. It reads the branch tree Git Town keeps in git config
    (git-town-branch.<name>.parent and .branchtype) and the settings in git-town.toml, fetches
    once, then works through the branches parents first:

      main, perennial     fast-forward to the tracking branch (ff-only), then push local commits
      feature, prototype  merge the tracking branch, merge the parent, push (prototype: no push)
      contribution        merge the tracking branch, push
      observed            merge the tracking branch
      parked              skipped, unless it is the branch being synced

    Where each merge runs:

      checked out in a worktree           git -C <worktree> merge --no-edit
      not checked out, fast-forward       git update-ref (no checkout)
      not checked out, clean merge        git merge-tree + commit-tree + update-ref (no checkout)
      not checked out, with conflicts     a new worktree "sync-<branch>" next to the current one

    The run stops at the first conflict and names the worktree that holds it. Resolve the files
    there, commit, and run the script again: branches that are already merged need no work.

    Uncommitted changes to tracked files are stashed before a merge into the current worktree
    and restored afterwards. A branch checked out in another worktree with uncommitted changes
    is skipped, with every branch below it, unless -Stash is given.

    Settings are read like Git Town reads them: local git config, then git-town.toml, then
    global git config. Only the merge sync strategy is supported; a rebase or compress
    strategy is refused. Perennial branches are always fast-forwarded only.

    The script never deletes a branch. A branch whose tracking branch was deleted on the remote
    (usually shipped) is reported and skipped with the branches below it. A branch without a
    tracking branch is synced but not pushed.

    Exit codes: 0 everything synced; 1 a branch was skipped or the run stopped at a conflict;
    2 a usage or configuration error.

.PARAMETER Branch
    Sync this branch (and its ancestors) instead of the current branch.

.PARAMETER Stack
    Also sync every branch below the branch, like `git town sync --stack`.

.PARAMETER All
    Sync every local branch Git Town knows, like `git town sync --all`.

.PARAMETER Stash
    Stash and restore uncommitted changes in other worktrees too, instead of skipping them.

.PARAMETER NoPush
    Merge only; push nothing.

.PARAMETER DryRun
    Print the steps without changing any branch, worktree or remote. It still fetches, so the
    plan reflects the remote.

.EXAMPLE
    git-town-sync.ps1
    Syncs the current branch and every branch above it.

.EXAMPLE
    git-town-sync.ps1 -Stack -DryRun
    Shows what syncing the whole stack around the current branch would do.
#>
[CmdletBinding()]
param(
    [string]$Branch,
    [switch]$Stack,
    [switch]$All,
    [switch]$Stash,
    [switch]$NoPush,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

class SkipBranch : System.Exception {
    SkipBranch([string]$Message) : base($Message) {}
}

class StopSync : System.Exception {
    [string]$Branch
    [string]$Worktree
    StopSync([string]$Branch, [string]$Worktree) : base("merge conflict on $Branch in $Worktree") {
        $this.Branch = $Branch
        $this.Worktree = $Worktree
    }
}

function Invoke-Git {
    <#
    .SYNOPSIS
        Runs git and returns its exit code and combined output.
    .PARAMETER Arguments
        The git arguments.
    .PARAMETER Dir
        Run as `git -C <Dir>`; the current directory when empty.
    .OUTPUTS
        An object with Code (int) and Out (string).
    #>
    param([string[]]$Arguments, [string]$Dir)
    $prefix = if ($Dir) { @('-C', $Dir) } else { @() }
    $out = & git @prefix @Arguments 2>&1 | ForEach-Object { "$_" }
    [pscustomobject]@{ Code = $LASTEXITCODE; Out = ($out -join "`n").TrimEnd() }
}

function Get-Git {
    <#
    .SYNOPSIS
        Runs a read-only git command and returns its output.
    .PARAMETER Arguments
        The git arguments.
    .PARAMETER Dir
        Run as `git -C <Dir>`.
    .OUTPUTS
        The trimmed output.
    .NOTES
        Throws when git exits non-zero.
    #>
    param([string[]]$Arguments, [string]$Dir)
    $r = Invoke-Git $Arguments $Dir
    if ($r.Code -ne 0) { throw "git $($Arguments -join ' ') failed: $($r.Out)" }
    $r.Out
}

function Test-Git {
    <#
    .SYNOPSIS
        Returns whether a git command exits 0.
    #>
    param([string[]]$Arguments, [string]$Dir)
    (Invoke-Git $Arguments $Dir).Code -eq 0
}

function Invoke-Step {
    <#
    .SYNOPSIS
        Prints a git command that changes something as "[branch] git ...", then runs it unless -DryRun.
    .PARAMETER Label
        The branch the step belongs to.
    .PARAMETER Arguments
        The git arguments.
    .PARAMETER Dir
        The worktree to run in.
    .PARAMETER AllowFail
        Return a failed result instead of throwing.
    .OUTPUTS
        An object with Code and Out; Code 0 in a dry run.
    #>
    param([string]$Label, [string[]]$Arguments, [string]$Dir, [switch]$AllowFail)
    $where = if ($Dir) { "  (in $Dir)" } else { '' }
    Write-Host "[$Label] git $($Arguments -join ' ')$where"
    if ($DryRun) { return [pscustomobject]@{ Code = 0; Out = '' } }
    $r = Invoke-Git $Arguments $Dir
    if ($r.Out) { Write-Host $r.Out }
    if ($r.Code -ne 0 -and -not $AllowFail) { throw "git $($Arguments -join ' ') failed" }
    $r
}

function Read-TownToml {
    <#
    .SYNOPSIS
        Reads the flat keys of git-town.toml as "section.key" => value.
    .DESCRIPTION
        Covers what Git Town's file uses: [section] headers, quoted and literal strings,
        booleans, and string arrays (also over several lines). Comments are dropped.
    .PARAMETER Path
        The file; a missing file gives an empty table.
    .OUTPUTS
        A hashtable.
    #>
    param([string]$Path)
    $values = @{}
    if (-not (Test-Path -LiteralPath $Path)) { return $values }
    $section = ''
    $pendingKey = $null
    $pending = ''
    foreach ($line in Get-Content -LiteralPath $Path) {
        $t = $line.Trim()
        if ($pendingKey) {
            $pending += ' ' + $t
            if ($t -match '\]') { $values[$pendingKey] = ConvertFrom-TomlValue $pending; $pendingKey = $null }
            continue
        }
        if (-not $t -or $t.StartsWith('#')) { continue }
        if ($t -match '^\[([^\[\]]+)\]') { $section = $Matches[1].Trim(); continue }
        if ($t -match '^([A-Za-z0-9_-]+)\s*=\s*(.*)$') {
            $key = if ($section) { "$section.$($Matches[1])" } else { $Matches[1] }
            $raw = $Matches[2]
            if ($raw.StartsWith('[') -and $raw -notmatch '\]') { $pendingKey = $key; $pending = $raw; continue }
            $values[$key] = ConvertFrom-TomlValue $raw
        }
    }
    $values
}

function ConvertFrom-TomlValue {
    <#
    .SYNOPSIS
        Converts one TOML value (string, boolean or string array) to a PowerShell value.
    .PARAMETER Raw
        The text after "key =".
    #>
    param([string]$Raw)
    $raw = $Raw.Trim()
    $stringPattern = '"((?:[^"\\]|\\.)*)"|''([^'']*)'''
    if ($raw.StartsWith('[')) {
        return , @([regex]::Matches($raw, $stringPattern) | ForEach-Object { ConvertFrom-TomlString $_ })
    }
    $m = [regex]::Match($raw, "^(?:$stringPattern)")
    if ($m.Success) { return ConvertFrom-TomlString $m }
    if ($raw -match '^(true|false)\b') { return $Matches[1] -eq 'true' }
    ($raw -replace '\s+#.*$', '').Trim()
}

function ConvertFrom-TomlString {
    <#
    .SYNOPSIS
        Returns the text of a matched basic ("...") or literal ('...') TOML string.
    #>
    param([System.Text.RegularExpressions.Match]$Match)
    if ($Match.Groups[1].Success) { return [regex]::Replace($Match.Groups[1].Value, '\\(["\\])', '$1') }
    $Match.Groups[2].Value
}

function Get-Setting {
    <#
    .SYNOPSIS
        Returns a Git Town setting: local git config, then git-town.toml, then global git config.
    .PARAMETER GitKey
        The git config key, for example git-town.push-hook.
    .PARAMETER TomlKey
        The "section.key" in git-town.toml, for example sync.push-hook.
    .PARAMETER Default
        The value when none of the three sets it.
    #>
    param([string]$GitKey, [string]$TomlKey, $Default)
    if ($script:LocalConfig.ContainsKey($GitKey)) { return $script:LocalConfig[$GitKey] }
    if ($script:Toml.ContainsKey($TomlKey)) { return $script:Toml[$TomlKey] }
    if ($script:GlobalConfig.ContainsKey($GitKey)) { return $script:GlobalConfig[$GitKey] }
    $Default
}

function Read-GitConfig {
    <#
    .SYNOPSIS
        Loads git config once into $script:LocalConfig (local and worktree scope) and
        $script:GlobalConfig (global and system scope), and Git Town's lineage into
        $script:Parents and $script:Types.
    .DESCRIPTION
        One git call: on some machines every git process costs half a second.
    #>
    $script:LocalConfig = @{}
    $script:GlobalConfig = @{}
    $script:Parents = @{}
    $script:Types = @{}
    foreach ($line in (Get-Git @('config', '--list', '--show-scope')) -split "`n") {
        if ($line -notmatch '^(\w+)\t([^=]+)=(.*)$') { continue }
        $scope, $key, $value = $Matches[1], $Matches[2], $Matches[3]
        if ($scope -in 'local', 'worktree') { $script:LocalConfig[$key] = $value }
        elseif ($scope -in 'global', 'system') { $script:GlobalConfig[$key] = $value }
        if ($scope -in @('local', 'worktree') -and $key -match '^git-town-branch\.(.+)\.(parent|branchtype)$') {
            if ($Matches[2] -eq 'parent') { $script:Parents[$Matches[1]] = $value }
            else { $script:Types[$Matches[1]] = $value }
        }
    }
}

function ConvertTo-Flag {
    <#
    .SYNOPSIS
        Reads a git or TOML boolean.
    #>
    param($Value)
    if ($Value -is [bool]) { return $Value }
    "$Value" -match '^(true|yes|on|1)$'
}

function Test-SamePath {
    <#
    .SYNOPSIS
        Compares two directory paths, case-insensitively on Windows.
    #>
    param([string]$A, [string]$B)
    $na = [IO.Path]::GetFullPath($A).TrimEnd('\', '/')
    $nb = [IO.Path]::GetFullPath($B).TrimEnd('\', '/')
    $comparison = if ($IsWindows) { [StringComparison]::OrdinalIgnoreCase } else { [StringComparison]::Ordinal }
    [string]::Equals($na, $nb, $comparison)
}

function Get-BranchType {
    <#
    .SYNOPSIS
        Returns main, perennial, feature, prototype, contribution, observed or parked.
    .PARAMETER Name
        The branch.
    #>
    param([string]$Name)
    if ($Name -ceq $script:Main) { return 'main' }
    if ($script:Perennials -ccontains $Name) { return 'perennial' }
    if ($script:PerennialRegex -and $Name -cmatch $script:PerennialRegex) { return 'perennial' }
    if ($script:Types.ContainsKey($Name)) { return $script:Types[$Name] }
    if ($script:Parents.ContainsKey($Name)) { return 'feature' }
    'observed'
}

function Get-Ancestors {
    <#
    .SYNOPSIS
        Returns the branch's ancestors, nearest first.
    #>
    param([string]$Name)
    $result = [System.Collections.Generic.List[string]]::new()
    $b = $Name
    while ($script:Parents.ContainsKey($b)) {
        $b = $script:Parents[$b]
        if ($result.Contains($b) -or $b -ceq $Name) { throw "Git Town's branch lineage has a cycle at $b" }
        $result.Add($b)
    }
    , $result
}

function Get-Descendants {
    <#
    .SYNOPSIS
        Returns every branch below the branch in the lineage.
    #>
    param([string]$Name)
    $result = [System.Collections.Generic.List[string]]::new()
    $queue = [System.Collections.Generic.Queue[string]]::new()
    $queue.Enqueue($Name)
    while ($queue.Count) {
        $b = $queue.Dequeue()
        foreach ($child in $script:Parents.Keys | Where-Object { $script:Parents[$_] -ceq $b } | Sort-Object) {
            if (-not $result.Contains($child)) { $result.Add($child); $queue.Enqueue($child) }
        }
    }
    , $result
}

function Get-TrackingState {
    <#
    .SYNOPSIS
        Returns present (the remote branch exists), gone (it was deleted) or none (never pushed).
    #>
    param([string]$Name)
    if ($script:RemoteBranches.Contains($Name)) { return 'present' }
    $key = "branch.$Name.remote"
    if ($script:LocalConfig.ContainsKey($key) -and $script:LocalConfig[$key] -ceq $script:Remote) { return 'gone' }
    'none'
}

function Test-Dirty {
    <#
    .SYNOPSIS
        Returns whether a worktree has uncommitted changes to tracked files.
    #>
    param([string]$Dir)
    [bool](Get-Git @('status', '--porcelain', '--untracked-files=no') $Dir)
}

function Save-Changes {
    <#
    .SYNOPSIS
        Stashes uncommitted changes in a worktree before a merge into it.
    .DESCRIPTION
        The current worktree is always stashed; another worktree only with -Stash, otherwise the
        branch is skipped. Each worktree is stashed at most once per branch.
    .PARAMETER Name
        The branch checked out there.
    .PARAMETER Dir
        The worktree.
    #>
    param([string]$Name, [string]$Dir)
    if ($script:Stashes.ContainsKey($Dir) -or -not (Test-Dirty $Dir)) { return }
    if (-not (Test-SamePath $Dir $script:Top) -and -not $Stash) {
        throw [SkipBranch]::new("$Dir has uncommitted changes; commit them, or run again with -Stash")
    }
    $null = Invoke-Step $Name @('stash', 'push', '-m', "git-town-sync: $Name") $Dir
    $script:Stashes[$Dir] = if ($DryRun) { '' } else { Get-Git @('rev-parse', 'refs/stash') }
}

function Restore-Changes {
    <#
    .SYNOPSIS
        Restores the changes Save-Changes stashed in the branch's worktree, if any.
    .PARAMETER Name
        The branch.
    #>
    param([string]$Name)
    if (-not $script:Worktrees.ContainsKey($Name)) { return }
    $dir = $script:Worktrees[$Name]
    if (-not $script:Stashes.ContainsKey($dir)) { return }
    $sha = $script:Stashes[$dir]
    $script:Stashes.Remove($dir)
    if ($DryRun) { $null = Invoke-Step $Name @('stash', 'pop') $dir; return }
    $r = Invoke-Step $Name @('stash', 'apply', $sha) $dir -AllowFail
    if ($r.Code -ne 0) {
        $script:Notes.Add("${Name}: the stashed changes in $dir did not apply cleanly; they are kept in the stash as $sha (git stash list)")
        return
    }
    $index = [array]::IndexOf(@((Get-Git @('stash', 'list', '--format=%H')) -split "`n"), $sha)
    if ($index -ge 0) { $null = Invoke-Step $Name @('stash', 'drop', "stash@{$index}") $dir }
}

function New-ConflictWorktreePath {
    <#
    .SYNOPSIS
        Returns a free path "sync-<branch>" next to the current worktree.
    #>
    param([string]$Name)
    $base = Join-Path (Split-Path $script:Top -Parent) ('sync-' + ($Name -replace '[\\/:*?"<>| ]', '-'))
    $path = $base
    $i = 2
    while (Test-Path -LiteralPath $path) { $path = "$base-$i"; $i++ }
    $path
}

function Get-Sha {
    <#
    .SYNOPSIS
        Returns the commit a ref points to; for a local branch in a dry run, the commit it would
        point to after the steps planned so far.
    .PARAMETER Ref
        A local branch name or another ref (for example origin/main).
    #>
    param([string]$Ref)
    if ($script:Planned.ContainsKey($Ref)) { return $script:Planned[$Ref] }
    $full = if ($script:LocalBranches.Contains($Ref)) { "refs/heads/$Ref" } else { $Ref }
    Get-Git @('rev-parse', '--verify', "$full^{commit}")
}

function Merge-Into {
    <#
    .SYNOPSIS
        Merges Source into the local branch Target, wherever Target is checked out.
    .PARAMETER Target
        The local branch to update.
    .PARAMETER Source
        The ref to merge in (a remote-tracking branch or the parent).
    .PARAMETER Message
        The merge commit message when no worktree is involved.
    .PARAMETER FastForwardOnly
        Refuse anything but a fast-forward (perennial branches).
    .NOTES
        Throws SkipBranch when the merge cannot run, StopSync on a conflict. In a dry run it
        prints the step and records the resulting commit in $script:Planned; a clean merge
        commit is written to the object store then, but no ref.
    #>
    param([string]$Target, [string]$Source, [string]$Message, [switch]$FastForwardOnly)
    $t = Get-Sha $Target
    $s = Get-Sha $Source
    # "<only in target> <only in source>": no source-only commits means nothing to merge,
    # no target-only commits means a fast-forward.
    $onlyTarget, $onlySource = (Get-Git @('rev-list', '--left-right', '--count', "$t...$s")) -split '\s+'
    if ([int]$onlySource -eq 0) { return }
    $ff = [int]$onlyTarget -eq 0
    if ($FastForwardOnly -and -not $ff) {
        throw [SkipBranch]::new("$Target and $Source have both moved on; perennial branches are only fast-forwarded")
    }
    $tree = $null
    $conflict = $false
    if (-not $ff) {
        $mt = Invoke-Git @('merge-tree', '--write-tree', '--name-only', $t, $s)
        if ($mt.Code -gt 1) { throw "git merge-tree failed: $($mt.Out)" }
        $conflict = $mt.Code -eq 1
        $tree = ($mt.Out -split "`n")[0]
    }
    $dir = if ($script:Worktrees.ContainsKey($Target)) { $script:Worktrees[$Target] } else { $null }
    if ($dir) { Save-Changes $Target $dir }

    if ($DryRun) {
        if ($conflict) {
            throw [SkipBranch]::new("merging $Source into $Target would conflict; a real run stops there for you to resolve it")
        }
        $how = if ($dir) { "merge --no-edit $Source  (in $dir)" }
        elseif ($ff) { "fast-forward to $Source  (update-ref, no checkout)" }
        else { "merge $Source  (merge-tree + commit-tree + update-ref, no checkout)" }
        Write-Host "[$Target] $how"
        $script:Planned[$Target] = if ($ff) { $s } else { Get-Git @('commit-tree', $tree, '-p', $t, '-p', $s, '-m', $Message) }
        return
    }

    if ($dir) {
        $mode = if ($FastForwardOnly) { '--ff-only' } else { '--ff' }
        $r = Invoke-Step $Target @('merge', '--no-edit', $mode, $Source) $dir -AllowFail
        if ($r.Code -ne 0) {
            if (Test-Git @('rev-parse', '-q', '--verify', 'MERGE_HEAD') $dir) { throw [StopSync]::new($Target, $dir) }
            throw [SkipBranch]::new("git merge $Source failed in $dir")
        }
        return
    }
    if ($ff) {
        $null = Invoke-Step $Target @('update-ref', "refs/heads/$Target", $s, $t)
        return
    }
    if (-not $conflict) {
        $commit = Get-Git @('commit-tree', $tree, '-p', $t, '-p', $s, '-m', $Message)
        Write-Host "[$Target] merged $Source without a checkout: $($commit.Substring(0, 8))"
        $null = Invoke-Step $Target @('update-ref', "refs/heads/$Target", $commit, $t)
        return
    }
    $path = New-ConflictWorktreePath $Target
    $null = Invoke-Step $Target @('worktree', 'add', $path, $Target)
    $script:Worktrees[$Target] = $path
    $null = Invoke-Step $Target @('merge', '--no-edit', '--ff', $Source) $path -AllowFail
    throw [StopSync]::new($Target, $path)
}

function Push-Branch {
    <#
    .SYNOPSIS
        Pushes the branch when it is ahead of its tracking branch.
    .PARAMETER Name
        The branch.
    #>
    param([string]$Name)
    if ($NoPush -or -not $script:PushBranches) { return }
    if ((Get-TrackingState $Name) -ne 'present') {
        $script:Notes.Add("${Name}: no branch on $script:Remote, so not pushed (publish it with: git push -u $script:Remote $Name)")
        return
    }
    $ahead = [int](Get-Git @('rev-list', '--count', "$script:Remote/$Name..$(Get-Sha $Name)"))
    if ($ahead -eq 0) { return }
    $arguments = @('push')
    if (-not $script:PushHook) { $arguments += '--no-verify' }
    $r = Invoke-Step $Name ($arguments + @($script:Remote, $Name)) -AllowFail
    if ($r.Code -ne 0) { throw [SkipBranch]::new("git push failed") }
}

function Sync-Branch {
    <#
    .SYNOPSIS
        Syncs one branch according to its Git Town branch type.
    .PARAMETER Name
        The branch.
    #>
    param([string]$Name)
    $type = Get-BranchType $Name
    $tracking = Get-TrackingState $Name
    if ($tracking -eq 'gone') {
        throw [SkipBranch]::new("its branch on $script:Remote was deleted (shipped?); delete it with git town or git branch -d")
    }
    $remoteRef = "$script:Remote/$Name"
    $fromRemote = "Merge remote-tracking branch '$remoteRef' into $Name"
    $pullRemote = $tracking -eq 'present'
    switch ($type) {
        { $_ -in 'main', 'perennial' } {
            if ($pullRemote) { Merge-Into $Name $remoteRef $fromRemote -FastForwardOnly }
            Push-Branch $Name
        }
        'observed' {
            if ($pullRemote) { Merge-Into $Name $remoteRef $fromRemote }
        }
        'contribution' {
            if ($pullRemote) { Merge-Into $Name $remoteRef $fromRemote }
            Push-Branch $Name
        }
        default {
            if ($type -eq 'prototype' -and $script:PrototypeStrategy -cne 'merge') {
                throw [SkipBranch]::new("prototype branches use the '$script:PrototypeStrategy' strategy; only merge is supported")
            }
            if ($pullRemote) { Merge-Into $Name $remoteRef $fromRemote }
            if ($script:Parents.ContainsKey($Name)) {
                $parent = $script:Parents[$Name]
                Merge-Into $Name $parent "Merge branch '$parent' into $Name"
            }
            if ($type -ne 'prototype') { Push-Branch $Name }
        }
    }
}

try {
    $top = Invoke-Git @('rev-parse', '--show-toplevel')
    if ($top.Code -ne 0) { throw 'not inside a git worktree' }
    $script:Top = $top.Out
    $tomlPath = @('git-town.toml', '.git-town.toml') | ForEach-Object { Join-Path $script:Top $_ } |
        Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    $script:Toml = if ($tomlPath) { Read-TownToml $tomlPath } else { @{} }
    Read-GitConfig

    $script:Main = Get-Setting 'git-town.main-branch' 'branches.main' $null
    if (-not $script:Main) { throw 'no main branch configured (git-town.toml [branches] main, or git config git-town.main-branch)' }
    $perennials = Get-Setting 'git-town.perennial-branches' 'branches.perennials' @()
    $script:Perennials = @(@($perennials) | ForEach-Object { "$_" -split '\s+' } | Where-Object { $_ })
    $script:PerennialRegex = Get-Setting 'git-town.perennial-regex' 'branches.perennial-regex' ''
    $featureStrategy = Get-Setting 'git-town.sync-feature-strategy' 'sync.feature-strategy' 'merge'
    if ($featureStrategy -cne 'merge') {
        throw "the feature sync strategy is '$featureStrategy'; this script only supports merge, so use git town sync"
    }
    $script:PrototypeStrategy = Get-Setting 'git-town.sync-prototype-strategy' 'sync.prototype-strategy' $featureStrategy
    $script:PushBranches = ConvertTo-Flag (Get-Setting 'git-town.push-branches' 'sync.push-branches' $true)
    $script:PushHook = ConvertTo-Flag (Get-Setting 'git-town.push-hook' 'sync.push-hook' $true)
    $syncTags = ConvertTo-Flag (Get-Setting 'git-town.sync-tags' 'sync.tags' $true)
    $script:Remote = Get-Setting 'git-town.dev-remote' 'hosting.dev-remote' 'origin'
    $remotes = @((Get-Git @('remote')) -split "`n")
    if ($remotes -cnotcontains $script:Remote) { throw "no remote named '$script:Remote'" }
    $script:Notes = [System.Collections.Generic.List[string]]::new()
    if ((ConvertTo-Flag (Get-Setting 'git-town.sync-upstream' 'sync.upstream' $true)) -and $remotes -ccontains 'upstream') {
        $script:Notes.Add("the 'upstream' remote is not synced into $script:Main; run git town sync on $script:Main for that")
    }

    $script:Worktrees = @{}
    $dir = $null
    foreach ($line in (Get-Git @('worktree', 'list', '--porcelain')) -split "`n") {
        if ($line.StartsWith('worktree ')) { $dir = $line.Substring(9) }
        elseif ($line.StartsWith('branch refs/heads/')) { $script:Worktrees[$line.Substring(18)] = $dir }
    }
    $script:Stashes = @{}
    $script:Planned = @{}

    $current = Invoke-Git @('symbolic-ref', '--quiet', '--short', 'HEAD')
    $start = if ($Branch) { $Branch } elseif ($current.Code -eq 0) { $current.Out } else { $null }
    $script:LocalBranches = [System.Collections.Generic.HashSet[string]]::new(
        [string[]]@((Get-Git @('for-each-ref', '--format=%(refname:short)', 'refs/heads')) -split "`n" | Where-Object { $_ }))
    if ($All) {
        $candidates = @($script:Main) + $script:Perennials + @($script:Parents.Keys) +
        @($script:LocalBranches | Where-Object { (Get-BranchType $_) -eq 'perennial' })
    }
    else {
        if (-not $start) { throw 'HEAD is detached; name the branch with -Branch' }
        $candidates = @($start) + (Get-Ancestors $start)
        if ($Stack) { $candidates += Get-Descendants $start }
    }
    $depth = @{}
    $order = @($candidates | Where-Object { $_ } | Select-Object -Unique | ForEach-Object {
            $depth[$_] = (Get-Ancestors $_).Count
            $_
        } | Sort-Object { $depth[$_] }, { $_ })

    $fetchArgs = @('fetch', '--prune', $(if ($syncTags) { '--tags' } else { '--no-tags' }), $script:Remote)
    Write-Host "git $($fetchArgs -join ' ')"
    $null = Get-Git $fetchArgs
    $remotePrefix = "$script:Remote/"
    $script:RemoteBranches = [System.Collections.Generic.HashSet[string]]::new(
        [string[]]@((Get-Git @('for-each-ref', '--format=%(refname:short)', "refs/remotes/$script:Remote")) -split "`n" |
            Where-Object { $_.StartsWith($remotePrefix) } | ForEach-Object { $_.Substring($remotePrefix.Length) }))
    if ($DryRun) { Write-Host '(dry run: the steps below are printed, not run)' }

    $blocked = [System.Collections.Generic.HashSet[string]]::new()
    $skipped = [System.Collections.Generic.List[string]]::new()
    $synced = [System.Collections.Generic.List[string]]::new()
    foreach ($b in $order) {
        $parent = if ($script:Parents.ContainsKey($b)) { $script:Parents[$b] } else { $null }
        if ($parent -and $blocked.Contains($parent)) {
            $null = $blocked.Add($b); $skipped.Add("${b}: its parent $parent was not synced"); continue
        }
        if (-not $script:LocalBranches.Contains($b)) {
            $null = $blocked.Add($b); $skipped.Add("${b}: not a local branch"); continue
        }
        if ((Get-BranchType $b) -eq 'parked' -and $b -cne $start) {
            $script:Notes.Add("${b}: parked, not synced"); continue
        }
        try {
            Sync-Branch $b
            Restore-Changes $b
            $synced.Add($b)
        }
        catch [SkipBranch] {
            Restore-Changes $b
            $null = $blocked.Add($b)
            $skipped.Add("${b}: $($_.Exception.Message)")
        }
    }

    Write-Host ''
    $label = if ($DryRun) { 'Would sync' } else { 'Synced' }
    if ($synced.Count) { Write-Host "${label}: $($synced -join ', ')" }
    foreach ($s in $skipped) { Write-Host "Skipped $s" }
    foreach ($n in $script:Notes) { Write-Host "Note: $n" }
    exit $(if ($skipped.Count) { 1 } else { 0 })
}
catch [StopSync] {
    $stop = $_.Exception
    $files = (Invoke-Git @('diff', '--name-only', '--diff-filter=U') $stop.Worktree).Out -split "`n" | Where-Object { $_ }
    Write-Host ''
    if ($synced.Count) { Write-Host "Synced before the conflict: $($synced -join ', ')" }
    foreach ($s in $skipped) { Write-Host "Skipped $s" }
    Write-Host "Merge conflict on $($stop.Branch) in $($stop.Worktree)"
    foreach ($f in $files) { Write-Host "  conflicted: $f" }
    Write-Host 'Resolve the files there, commit (git commit --no-edit), then run this script again.'
    if ($script:Stashes.ContainsKey($stop.Worktree)) {
        Write-Host "Your uncommitted changes there are stashed as $($script:Stashes[$stop.Worktree]); restore them after the commit with: git stash pop"
    }
    if (-not (Test-SamePath $stop.Worktree $script:Top) -and (Split-Path $stop.Worktree -Leaf).StartsWith('sync-')) {
        Write-Host "When the sync is done you can remove that worktree: git worktree remove `"$($stop.Worktree)`""
    }
    exit 1
}
catch {
    Write-Host "git-town-sync: $($_.Exception.Message)"
    exit 2
}
