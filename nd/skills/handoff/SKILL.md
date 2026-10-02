---
name: handoff
description: Writes a HANDOFF.md at the repo root capturing state, non-obvious decisions and next steps, so a fresh session or agent can continue without this conversation. Use when ending a session, running low on context, or handing work to another agent.
when_to_use: |
  Trigger phrases: "hand off", "write a handoff", "I'm running out of context", "wrap up for the next session", "continue this in a new session".

  Not this skill: recording a single decision or fact (use the basic-memory MCP directly); "compact", "summarize so far" or "recap" while staying in this session (just summarise it, or use /compact).
argument-hint: "What will the next session be used for?"
---

Produce a handoff document so a fresh agent can continue the work without needing this conversation.

Next session's focus: $ARGUMENTS

If that focus is non-empty, let it drive which sections get the most detail, and call it out in a short opening paragraph at the top of the document. If it is empty (usual when the skill triggers on its own), infer the likely focus from the conversation and state it in that paragraph; don't ask.

## Prerequisite

Run `git rev-parse --git-dir`. If it fails, this is not a git repo: skip steps 1 and 5, still write `HANDOFF.md`, and tell the user at the end that the file is uncommitted.

## Steps

**1. Deal with pending work.**
Run `git status --short` and `git diff --stat`. If the tree is clean, go to step 2.

Otherwise show the user both outputs, list the files you propose to stage, and wait for confirmation before committing. The only goal is that `HEAD` reflects the final state of the work being handed off.

- Never `git add -A` or `git add .` — stage the listed files by path.
- Leave untracked files alone unless the user names them.
- Stay on the current branch; a handoff does not warrant a new one.
- If the user declines, go to step 2 and record the uncommitted state under Outstanding Work.

**2. Locate the target file.**
Check whether `HANDOFF.md` already exists in the repo root.
- If it exists: read it. If it describes the same work, keep the sections that are still true (Architecture, Commands), rewrite What Was Built, Outstanding Work and Testing Notes for this session, and remove items that are done: a handoff is state for the next session, not a changelog. If it describes unrelated work, ask before overwriting.
- If it does not exist: create it.

The repo root is `git rev-parse --show-toplevel` (the working directory if this is not a git repo).

Do not use `mktemp` — the file must be version-controlled and discoverable by the next session.

**3. Write the handoff with these sections:**

```markdown
# [Project] Handoff

Date: <today, from `date +%F`>
Repo: <absolute path>
Branch: <current branch>
HEAD of the work (excluding this file): <short sha> <commit message>

## Next Steps
The first thing the next session should do, then the following one or two. Put open questions or decisions the user still owes here too.

## What Was Built This Session
2–4 bullets summarising the work done.

## Key Implementation Details
Non-obvious decisions, gotchas, and workarounds that are NOT visible in
the code or commit messages and that a fresh agent would waste time
re-discovering. Examples: why a specific technique was chosen over the
obvious alternative, a numerical constant derived from measurement, a
CSS/layout quirk, a third-party API behaviour that surprised you.

## Architecture / File Map (if changed this session)
Only include files touched this session. Omit architecture that did not
change — earlier descriptions are in this file's git history if needed.

## Assets & Dependencies (if relevant)
Files, environment variables, external services the next session needs.

## Commands
Minimal set: run, test, lint.

## Testing Notes
How to exercise the feature just built. Known states to set up first.

## Outstanding Work
Unfinished items, known issues, or things deliberately deferred.

## Suggested Skills for Next Session
List skills the next session is likely to need (e.g. superpowers:test-driven-development).
```

**4. Content rules.**
- Do NOT duplicate content already captured in formal artifacts (PRDs, ADRs, issues, diffs, commit messages). Reference them by path or URL instead.
- DO document implementation gotchas and non-obvious decisions even if the code change is small — these are the hardest things to reconstruct from a diff.
- Outstanding Work is never left empty: record deferred items and known issues, or write that there are none.
- Keep each section tight. The handoff is a quick-read, not a spec: aim for under about 80 lines, and link to a file or artifact instead of quoting it.
- Before listing a file path, command or environment variable, confirm it exists (`ls`, `grep`): a wrong path costs the next agent more than a missing one. Write from the repo, not only from memory of the conversation.
- Never write a secret value (API key, token, password, private key, connection string with credentials), even if the user asks you to include it. `HANDOFF.md` is committed and may be pushed, so a value written here stays in git history. Name the variable or file and say where to get the value ("`PAYMENTS_API_KEY`, in the team vault under payments-sandbox"), and tell the user you left the value out.
- Before saving, scan the draft: `grep -nE 'AKIA|ghp_|xox[abp]-|sk[-_](live|test)?[-_]?[A-Za-z0-9]{12,}|BEGIN [A-Z ]*PRIVATE KEY|://[^ /@]+:[^ /@]+@|(secret|token|passw|api[_-]?key)[A-Za-z_]*[:=] *["'"'"']?[A-Za-z0-9/+_=.-]{16,}' HANDOFF.md`. Remove every hit that is a real value.

**5. Commit the handoff.**
Stage and commit `HANDOFF.md` by path (`git add HANDOFF.md`, then `git commit -m "docs: update HANDOFF.md" -- HANDOFF.md`) so the repo ends in a clean state. Never push. Skip the commit, and tell the user why, if this is not a git repo (see Prerequisite) or the current branch is `main`, `master` or otherwise protected: committing there is a decision for the user. If a stricter approval rule is active in this session (such as `nd:delivery`'s per-action gate), follow it for this commit too.

## Completion checklist

- [ ] Prerequisite checked — git repo confirmed, or steps 1 and 5 consciously skipped
- [ ] Pending work committed with user confirmation, or recorded under Outstanding Work
- [ ] `HANDOFF.md` written at the repo root, updating in place if it already existed
- [ ] Next session's focus reflected in section emphasis, if one was given
- [ ] Gotchas and non-obvious decisions documented — not just a summary of the diff
- [ ] Nothing duplicated that a linked artifact already captures
- [ ] No secret value in the file (scanned); the user told if one was left out
- [ ] `HANDOFF.md` committed by path on an unprotected branch, or the user told it is uncommitted
