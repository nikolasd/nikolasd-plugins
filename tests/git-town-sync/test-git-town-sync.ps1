#Requires -Version 7.0
# Scenario tests for nd/skills/git-town-worktrees/git-town-sync.ps1. Each test builds a
# throwaway repository with a bare "origin", Git Town lineage (main > trunk > feat > child)
# and worktrees, runs the script, and checks local refs, working trees and the remote.
# No network, no model. Needs git >= 2.38 and PowerShell 7.
#
#   pwsh tests/git-town-sync/test-git-town-sync.ps1
#
# Exits non-zero if any check fails.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$SyncScript = (Resolve-Path (Join-Path $PSScriptRoot '../../nd/skills/git-town-worktrees/git-town-sync.ps1')).Path
$Root = Join-Path ([IO.Path]::GetTempPath()) ('gts-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory $Root | Out-Null
$script:Failures = 0

# Keep the user's git configuration (aliases, hooks, signing) out of the fixtures.
$savedEnv = @{ GIT_CONFIG_GLOBAL = $env:GIT_CONFIG_GLOBAL; GIT_CONFIG_NOSYSTEM = $env:GIT_CONFIG_NOSYSTEM }
$globalConfig = Join-Path $Root 'gitconfig'
Set-Content -LiteralPath $globalConfig -Value @'
[user]
	name = Test
	email = test@example.invalid
[init]
	defaultBranch = main
[core]
	autocrlf = false
[advice]
	detachedHead = false
'@
$env:GIT_CONFIG_GLOBAL = $globalConfig
$env:GIT_CONFIG_NOSYSTEM = '1'

function g {
    # Runs git for fixture setup; throws on failure.
    $out = & git @args 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') failed: $($out -join "`n")" }
    ($out -join "`n").Trim()
}

function Test-Git {
    # Runs git and returns whether it exited 0.
    & git @args *> $null
    $LASTEXITCODE -eq 0
}

function Check([string]$Name, [bool]$Condition, [string]$Detail = '') {
    if ($Condition) { Write-Host "ok    $Name" }
    else { Write-Host "FAIL  $Name $Detail"; $script:Failures++ }
}

function Add-Commit([string]$Dir, [string]$File, [string]$Content) {
    Set-Content -LiteralPath (Join-Path $Dir $File) -Value $Content -NoNewline
    g -C $Dir add -- $File | Out-Null
    g -C $Dir commit -q -m "change $File" | Out-Null
}

function New-Fixture([string]$Name) {
    # main (README, git-town.toml) > trunk > feat (f.txt) > child (c.txt), all pushed.
    # repo/ has trunk checked out, wt-feat/ has feat; main and child are not checked out.
    $d = Join-Path $Root $Name
    New-Item -ItemType Directory $d | Out-Null
    $origin = Join-Path $d 'origin.git'
    $repo = Join-Path $d 'repo'
    g init -q --bare $origin | Out-Null
    g clone -q $origin $repo | Out-Null
    Set-Content -LiteralPath (Join-Path $repo 'git-town.toml') -NoNewline -Value @'
[branches]
main = "main"
perennial-regex = "^featint$"

[sync]
feature-strategy = "merge"
push-hook = false
'@
    Set-Content -LiteralPath (Join-Path $repo 'README.md') -Value 'readme' -NoNewline
    g -C $repo add -A | Out-Null
    g -C $repo commit -q -m init | Out-Null
    g -C $repo push -q -u origin main | Out-Null
    g -C $repo checkout -q -b trunk | Out-Null
    g -C $repo push -q -u origin trunk | Out-Null
    g -C $repo checkout -q -b feat | Out-Null
    Add-Commit $repo 'f.txt' 'feat'
    g -C $repo push -q -u origin feat | Out-Null
    g -C $repo checkout -q -b child | Out-Null
    Add-Commit $repo 'c.txt' 'child'
    g -C $repo push -q -u origin child | Out-Null
    g -C $repo checkout -q trunk | Out-Null
    g -C $repo config git-town-branch.trunk.parent main | Out-Null
    g -C $repo config git-town-branch.feat.parent trunk | Out-Null
    g -C $repo config git-town-branch.child.parent feat | Out-Null
    $wt = Join-Path $d 'wt-feat'
    g -C $repo worktree add -q $wt feat | Out-Null
    $other = Join-Path $d 'other'
    g clone -q $origin $other | Out-Null
    [pscustomobject]@{ Dir = $d; Origin = $origin; Repo = $repo; Wt = $wt; Other = $other }
}

function Push-Upstream($Fx, [string]$Branch, [string]$File, [string]$Content) {
    # Someone else pushes a commit to $Branch on origin.
    g -C $Fx.Other fetch -q origin | Out-Null
    g -C $Fx.Other checkout -q -B $Branch "origin/$Branch" | Out-Null
    Add-Commit $Fx.Other $File $Content
    g -C $Fx.Other push -q origin $Branch | Out-Null
}

function Invoke-Sync([string]$Dir, [string[]]$Arguments = @()) {
    $out = & pwsh -NoProfile -NonInteractive -WorkingDirectory $Dir -File $SyncScript @Arguments 2>&1 |
        ForEach-Object { "$_" }
    [pscustomobject]@{ Code = $LASTEXITCODE; Out = ($out -join "`n") }
}

function Rev($Fx, [string]$Ref) { g -C $Fx.Repo rev-parse $Ref }
function OriginRev($Fx, [string]$Branch) { g -C $Fx.Origin rev-parse "refs/heads/$Branch" }
function Contains($Fx, [string]$Ancestor, [string]$Branch) {
    Test-Git -C $Fx.Repo merge-base --is-ancestor $Ancestor $Branch
}
function Content([string]$Dir, [string]$File) { Get-Content -Raw -LiteralPath (Join-Path $Dir $File) }

try {
    Write-Host '# default: syncs the current branch and its ancestors across worktrees'
    $fx = New-Fixture 'default'
    Push-Upstream $fx 'main' 'm.txt' 'main'
    Add-Commit $fx.Repo 't.txt' 'trunk'
    $r = Invoke-Sync $fx.Wt
    Check 'exit 0' ($r.Code -eq 0) $r.Out
    Check 'main fast-forwarded to origin/main' ((Rev $fx main) -eq (OriginRev $fx main))
    Check 'trunk contains main' (Contains $fx main trunk)
    Check 'trunk worktree has the merged file and is clean' (
        (Test-Path (Join-Path $fx.Repo 'm.txt')) -and -not (g -C $fx.Repo status --porcelain))
    Check 'feat contains trunk' (Contains $fx trunk feat)
    Check 'feat worktree has both new files' (
        (Test-Path (Join-Path $fx.Wt 'm.txt')) -and (Test-Path (Join-Path $fx.Wt 't.txt')))
    Check 'trunk pushed' ((OriginRev $fx trunk) -eq (Rev $fx trunk))
    Check 'feat pushed' ((OriginRev $fx feat) -eq (Rev $fx feat))
    Check 'child left alone without -Stack' (-not (Contains $fx main child))

    Write-Host '# -Stack: merges a child that is not checked out, without a checkout'
    $fx = New-Fixture 'stack'
    Push-Upstream $fx 'main' 'm.txt' 'main'
    $r = Invoke-Sync $fx.Wt @('-Stack')
    Check 'exit 0' ($r.Code -eq 0) $r.Out
    Check 'child contains feat' (Contains $fx feat child)
    Check 'child tip is a merge commit' (((g -C $fx.Repo rev-list --parents -n 1 child) -split ' ').Count -eq 3)
    Check 'child pushed' ((OriginRev $fx child) -eq (Rev $fx child))
    Check 'no extra worktree created' (((g -C $fx.Repo worktree list --porcelain) -split "`n" |
            Where-Object { $_ -like 'worktree *' }).Count -eq 2)

    Write-Host '# conflict in a branch that is not checked out: stops in a new worktree, re-run finishes'
    $fx = New-Fixture 'conflict-unchecked'
    Add-Commit $fx.Wt 'x.txt' 'feat side'
    Push-Upstream $fx 'child' 'x.txt' 'child side'
    $r = Invoke-Sync $fx.Wt @('-Stack')
    $syncWt = Join-Path $fx.Dir 'sync-child'
    Check 'exit non-zero on conflict' ($r.Code -ne 0) $r.Out
    Check 'conflict worktree created next to the current one' (Test-Path $syncWt) $r.Out
    Check 'output names the conflict worktree' ($r.Out.Contains('sync-child')) $r.Out
    Check 'conflicted file is unmerged there' (
        (Test-Path $syncWt) -and ((g -C $syncWt diff --name-only --diff-filter=U) -eq 'x.txt'))
    Set-Content -LiteralPath (Join-Path $syncWt 'x.txt') -Value 'resolved' -NoNewline
    g -C $syncWt add x.txt | Out-Null
    g -C $syncWt commit -q --no-edit | Out-Null
    $r = Invoke-Sync $fx.Wt @('-Stack')
    Check 're-run exit 0' ($r.Code -eq 0) $r.Out
    Check 'child contains feat after re-run' (Contains $fx feat child)
    Check 'child pushed after re-run' ((OriginRev $fx child) -eq (Rev $fx child))

    Write-Host '# uncommitted changes in the current worktree are stashed and restored'
    $fx = New-Fixture 'stash-current'
    Push-Upstream $fx 'trunk' 'tr.txt' 'trunk upstream'
    Set-Content -LiteralPath (Join-Path $fx.Wt 'f.txt') -Value 'dirty' -NoNewline
    $r = Invoke-Sync $fx.Wt
    Check 'exit 0' ($r.Code -eq 0) $r.Out
    Check 'feat contains origin/trunk' (Contains $fx origin/trunk feat)
    Check 'merged file present' (Test-Path (Join-Path $fx.Wt 'tr.txt'))
    Check 'uncommitted change restored' ((Content $fx.Wt 'f.txt') -eq 'dirty')
    Check 'stash list empty' (-not (g -C $fx.Repo stash list))

    Write-Host '# uncommitted changes in another worktree: skipped, or stashed with -Stash'
    $fx = New-Fixture 'dirty-other'
    Add-Commit $fx.Repo 't.txt' 'trunk'
    Push-Upstream $fx 'main' 'm.txt' 'main'
    Set-Content -LiteralPath (Join-Path $fx.Repo 'README.md') -Value 'dirty readme' -NoNewline
    $r = Invoke-Sync $fx.Wt
    Check 'exit non-zero when a branch is skipped' ($r.Code -ne 0) $r.Out
    Check 'output names the skipped branch' ($r.Out.Contains('trunk')) $r.Out
    Check 'trunk not merged' (-not (Contains $fx main trunk))
    Check 'feat (below trunk) not merged' (-not (Contains $fx main feat))
    Check 'other worktree change untouched' ((Content $fx.Repo 'README.md') -eq 'dirty readme')
    $r = Invoke-Sync $fx.Wt @('-Stash')
    Check '-Stash: exit 0' ($r.Code -eq 0) $r.Out
    Check '-Stash: trunk contains main' (Contains $fx main trunk)
    Check '-Stash: feat contains trunk' (Contains $fx trunk feat)
    Check '-Stash: other worktree change restored' ((Content $fx.Repo 'README.md') -eq 'dirty readme')
    Check '-Stash: stash list empty' (-not (g -C $fx.Repo stash list))

    Write-Host '# conflict in a checked-out worktree: stops with the merge in progress there'
    $fx = New-Fixture 'conflict-worktree'
    Add-Commit $fx.Repo 'x.txt' 'trunk side'
    Push-Upstream $fx 'main' 'x.txt' 'main side'
    $r = Invoke-Sync $fx.Wt
    Check 'exit non-zero' ($r.Code -ne 0) $r.Out
    Check 'merge in progress in the trunk worktree' (Test-Git -C $fx.Repo rev-parse -q --verify MERGE_HEAD)
    Check 'feat not merged' (-not (Contains $fx main feat))

    Write-Host '# main that diverged from origin/main: ff-only refuses and changes nothing'
    $fx = New-Fixture 'diverged-main'
    Push-Upstream $fx 'main' 'm.txt' 'main'
    $local = g -C $fx.Repo commit-tree 'main^{tree}' -p main -m 'local only'
    g -C $fx.Repo update-ref refs/heads/main $local | Out-Null
    $r = Invoke-Sync $fx.Wt
    Check 'exit non-zero' ($r.Code -ne 0) $r.Out
    Check 'local main untouched' ((Rev $fx main) -eq $local)
    Check 'trunk not merged with origin/main' (-not (Contains $fx origin/main trunk))

    Write-Host '# -DryRun changes no branch, locally or on origin'
    $fx = New-Fixture 'dry-run'
    Push-Upstream $fx 'main' 'm.txt' 'main'
    Add-Commit $fx.Repo 't.txt' 'trunk'
    Set-Content -LiteralPath (Join-Path $fx.Wt 'f.txt') -Value 'dirty' -NoNewline
    $localBefore = g -C $fx.Repo for-each-ref refs/heads
    $originBefore = g -C $fx.Origin for-each-ref refs/heads
    $r = Invoke-Sync $fx.Wt @('-DryRun', '-Stack')
    Check 'exit 0' ($r.Code -eq 0) $r.Out
    Check 'local branches unchanged' ((g -C $fx.Repo for-each-ref refs/heads) -eq $localBefore)
    Check 'origin branches unchanged' ((g -C $fx.Origin for-each-ref refs/heads) -eq $originBefore)
    Check 'uncommitted change untouched' ((Content $fx.Wt 'f.txt') -eq 'dirty')
    # The plan carries each planned step forward: main's fast-forward makes trunk take main,
    # and main, now equal to origin/main, has nothing to push.
    Check 'plans the merge of main into trunk' ($r.Out -match '\[trunk\] merge --no-edit main') $r.Out
    Check 'plans the merge of trunk into feat' ($r.Out -match '\[feat\] merge --no-edit trunk') $r.Out
    Check 'plans no push of main' ($r.Out -notmatch '\[main\] git push') $r.Out

    Write-Host '# a rebase strategy in local git config (wins over git-town.toml) is refused'
    $fx = New-Fixture 'rebase-refused'
    Push-Upstream $fx 'main' 'm.txt' 'main'
    g -C $fx.Repo config git-town.sync-feature-strategy rebase | Out-Null
    $before = g -C $fx.Repo for-each-ref refs/heads
    $r = Invoke-Sync $fx.Wt
    Check 'exit non-zero' ($r.Code -ne 0) $r.Out
    Check 'output names the strategy' ($r.Out.Contains('rebase')) $r.Out
    Check 'no branch changed' ((g -C $fx.Repo for-each-ref refs/heads) -eq $before)
}
finally {
    foreach ($k in $savedEnv.Keys) {
        if ($null -eq $savedEnv[$k]) { Remove-Item "env:$k" -ErrorAction SilentlyContinue }
        else { Set-Item "env:$k" -Value $savedEnv[$k] }
    }
    Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction SilentlyContinue
}

if ($script:Failures) { Write-Host "$script:Failures check(s) failed"; exit 1 }
Write-Host 'all checks passed'
