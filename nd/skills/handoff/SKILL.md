---
name: handoff
description: Use when ending a session, running low on context, or handing work to another agent — produces a HANDOFF.md the next session can start from without this conversation.
when_to_use: |
  Trigger phrases: "hand off", "write a handoff", "I'm running out of context", "wrap up for the next session", "continue this in a new session", "compact this conversation".

  Not this skill: recording a single decision or fact — use the basic-memory MCP directly. Summarising a conversation the user will keep reading — just summarise it.
argument-hint: "What will the next session be used for?"
---

Produce a handoff document so a fresh agent can continue the work without needing this conversation.

Next session's focus: $ARGUMENTS

If that focus is non-empty, let it drive which sections get the most detail, and call it out in a short opening paragraph at the top of the document.

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
- If it exists: read it, then update it in place (preserve sections that are still accurate, replace what changed).
- If it does not exist: create it.

Do not use `mktemp` — the file must be version-controlled and discoverable by the next session.

**3. Write the handoff with these sections:**

```markdown
# [Project] Handoff

Date: <today>
Repo: <absolute path>
Current HEAD: <short sha> <commit message>

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
- Keep each section tight. The handoff is a quick-read, not a spec.

**5. Commit the handoff.**
Stage and commit `HANDOFF.md` by path so the repo ends in a clean state. Skip if this is not a git repo (see Prerequisite).

## Common mistakes

| Mistake | Fix |
|---|---|
| `git add -A` in step 1, sweeping up unrelated or untracked files | Stage only the files you listed and the user confirmed, by path |
| Writing the handoff to a temp file or a scratch directory | It must be at the repo root and version-controlled, or the next session cannot find it |
| Restating the diff in "What Was Built" | Reference the commits; spend the words on gotchas a diff cannot show |
| Duplicating a PRD, ADR, or issue into the handoff | Link it by path or URL |
| Committing in step 1 before showing the user what would be staged | Show `git status --short` and `git diff --stat` first, then wait |
| Leaving Outstanding Work empty because the session "finished" | Record deferred items and known issues, or say explicitly that there are none |

## Completion checklist

- [ ] Prerequisite checked — git repo confirmed, or steps 1 and 5 consciously skipped
- [ ] Pending work committed with user confirmation, or recorded under Outstanding Work
- [ ] `HANDOFF.md` written at the repo root, updating in place if it already existed
- [ ] Next session's focus reflected in section emphasis, if one was given
- [ ] Gotchas and non-obvious decisions documented — not just a summary of the diff
- [ ] Nothing duplicated that a linked artifact already captures
- [ ] `HANDOFF.md` committed, or the user told it is uncommitted
