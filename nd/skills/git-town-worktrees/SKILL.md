---
name: git-town-worktrees
description: Syncs a Git Town branch tree when some of its branches are checked out in other git worktrees, which `git town sync` skips without an error. Runs the bundled git-town-sync.ps1 (PowerShell 7), which merges like `git town sync` with the merge strategy, in whichever worktree holds each branch. Use when asked to run git town sync, sync a stack, or update a branch from its parent, trunk or main in a repo that uses worktrees, or when git says a branch "is already used by worktree".
when_to_use: |
  Trigger phrases: "git town sync", "sync my branches", "sync main > trunk > this branch", "sync the stack", "update this branch from trunk", "git town can't sync branches in worktrees", "fatal: 'trunk' is already used by worktree at", "active in another worktree".

  Check first with `git worktree list`: when no branch in the lineage being synced is checked out in another worktree, plain `git town sync` works; use it.

  Not this skill: a rebase or compress sync strategy; creating, shipping, renaming or deleting branches (`git town hack`, `ship`, `delete`); setting a branch's parent (`git town set-parent`); a repo that does not use Git Town.
---

# Git Town sync across worktrees

Git Town skips every branch that is checked out in another worktree ("active in another worktree") and finishes as if all went well. In a stack such as main > trunk > feature, with trunk in the main checkout and the feature in a worktree, `git town sync` run from the feature leaves trunk behind main, so the feature misses what trunk should have brought in. The bundled script runs the same sync and does each merge where the branch is checked out.

`<skill_dir>` below is the directory holding this SKILL.md.

## Steps

1. **Find the lineage and the worktrees.**
   ```bash
   git config --get-regexp '^git-town-branch\.'
   git worktree list
   ```
   The branches to sync are the current branch and its ancestors, plus every branch below it for a stack sync. If none of them is checked out in another worktree, run `git town sync` and stop here.
2. **Preview.** Pick the scope the user asked for: no flag for the current branch and its ancestors, `-Stack` to add its descendants, `-All` for every branch, `-Branch <name>` to start from another branch.
   ```bash
   pwsh -NoProfile -File <skill_dir>/git-town-sync.ps1 -DryRun [-Stack | -All] [-Branch <name>]
   ```
   It fetches, prints each step as `[branch] git ...`, and reports a merge that would conflict.
3. **Show the preview and ask before the real run.** The run merges into branches in other worktrees, where the user or another agent may be working, and pushes them. A request to "sync" made before the preview was shown is not approval of these exact steps.
4. **Run it** with the same flags, without `-DryRun`. Exit code 0: everything synced. 1: a branch was skipped or the run stopped at a conflict (the output says which). 2: a usage or configuration error.
5. **Conflicts.** The run stops at the first one and prints the worktree and the conflicted files. When the branch was not checked out anywhere, the script made a worktree for it, `sync-<branch>`, next to the current one. Resolve each file there, keeping the intent of both sides; regenerate generated files with their generator instead of merging them by hand. Then:
   ```bash
   git -C <worktree> add <files>
   git -C <worktree> commit --no-edit
   ```
   Run the same command again: branches already merged need no work. When the sync is done, remove a `sync-<branch>` worktree with `git worktree remove <path>`.
6. **Report** what was synced, what was skipped and why, and any notes, in the script's own words.

## Skipped branches

| Reason in the output | What to do |
|---|---|
| `<worktree> has uncommitted changes` | Someone may be working there. Ask the user before rerunning with `-Stash`, which stashes those changes and restores them after the merge. |
| `its parent <branch> was not synced` | Fix the parent's problem first; the child follows on the next run. |
| `its branch on origin was deleted (shipped?)` | Tell the user. The script never deletes a branch; `git town sync` or `git branch -d` does. |
| `have both moved on; perennial branches are only fast-forwarded` | The local main or perennial branch has commits that are not on the remote. Ask the user; do not reset it. |
| `would conflict` (dry run only) | Expected; the real run stops there for step 5. |

Uncommitted changes in the worktree the script runs from are stashed and restored automatically, like `git town sync` does. If the run stops at a conflict there, the output says the changes are still stashed; restore them with `git stash pop` after the merge commit.

## What the script does

Settings come from local git config, then `git-town.toml`, then global git config, the order Git Town uses. Branch types follow Git Town:

| Type | Steps |
|---|---|
| main, perennial | fast-forward to the remote branch, push local commits |
| feature | merge the remote branch, merge the parent, push |
| prototype | as feature, without the push |
| contribution | merge the remote branch, push |
| observed | merge the remote branch |
| parked | skipped unless it is the branch being synced |

| Where the branch is | How it is merged |
|---|---|
| checked out in a worktree | `git -C <worktree> merge --no-edit` |
| not checked out, fast-forward | `git update-ref`, no checkout |
| not checked out, clean merge | `git merge-tree` + `git commit-tree` + `git update-ref`, no checkout |
| not checked out, conflicts | new worktree `sync-<branch>`, merge there, stop |

Other options: `-NoPush` merges only; `-Stash` stashes in other worktrees too. Full help: `Get-Help <skill_dir>/git-town-sync.ps1 -Full`.

Needs PowerShell 7.2 or later (`pwsh`) and git 2.38 or later. Only the merge sync strategy is supported; with `rebase` or `compress` the script refuses and changes nothing.

## Don't

- Don't check out, switch to, or detach a branch another worktree holds, and don't remove a worktree, to make `git town sync` work.
- Don't read a clean `git town sync` as proof that every branch was synced: branches in other worktrees were skipped.
- Don't rebase, reset or force-push to resolve anything here.
