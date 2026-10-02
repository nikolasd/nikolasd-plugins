---
name: delivery
description: Enforces fully verified delivery and a per-action approval gate. Checks the work against all acceptance criteria before it is called done, and requires an explicit "approve" before each commit, push, rebase, amend, PR, or branch checkout change.
when_to_use: |
  Trigger phrases: "is this done", "ready to commit", "mark this complete", "commit it", "push it", "push this to origin", "force-push", "rebase", "amend", "open a PR", "let's ship it". Any request to run a gated git action (see below) loads this skill, however it is phrased.
  Also when behavior-changing code is about to be written (failing test first).

  Not for: read-only code questions, docs-only edits, or RED-GREEN-REFACTOR mechanics (see `superpowers:test-driven-development`).
---

# Disciplined Delivery

## Overview
Understand before changing, test before implementing, verify before claiming done, and get one explicit approval per irreversible action. When a choice is the user's to make or a requirement is ambiguous, stop and ask — options plus a recommendation, never a guess on the user's behalf.

**REQUIRED SUB-SKILL:** `superpowers:test-driven-development` (invoke it with the Skill tool; assumes RED before GREEN). If it is unavailable, write a failing test first yourself.
**RECOMMENDED:** `superpowers:verification-before-completion`, `superpowers:requesting-code-review`.

## The contract

**Before coding.** Read the files you will touch and their tests, follow the repo's existing patterns, and check library behaviour in the real documentation instead of from memory. Do the one requested change, nothing more. A behavior change gets a failing test first; skip that for docs, config and throwaway spikes, and say you skipped it.

**"Fully implemented" means ALL of:**
- Covers the spec, not a subset.
- Every acceptance criterion satisfied.
- Full suite green — not just the touched file.
- If the repo measures coverage: changed modules at ≥80%.
- If the repo keeps ADRs: every non-trivial decision recorded in one.
- Docs updated to match.

Missing any one is not "basically done" — name the gap. If the repo measures no coverage or keeps no ADRs, say so in the report.

When verification is not clean, say so instead of claiming "fully verified":
- **The suite was already failing** before your change: name the failures that predate it and report only the new ones as yours.
- **There is no test runner, or the suite is too slow or cannot run here:** say what you could not run and why.

**Self-review.** Read your diff adversarially, hunting for what's wrong. Stay scoped.

**Decisions and contracts.** Record a non-trivial decision in an ADR if the repo keeps them, and leave only a short pointer in the code: a comment next to the change is lost when the code moves. When you change a data contract, migrate every consumer and pin the contract with a test, because updating only the obvious consumer breaks the others silently. Test behavior, not source text: a test that greps the source passes while the behavior is wrong, so find a real check or drop the test.

**Reporting.** "Plan executed" ≠ "requirements met." State what's verified, assumed, or open, and the real baseline used.

**Approval — one approval, one action.** Approval is only informed if the user has seen what will happen. So before each gated action, show the diff stat, the test result and the exact commit message (or the push target, or the rebase range), then wait for a reply that clearly says go ("approve", "yes", "go ahead"). An instruction given before you showed anything ("commit it") is not approval: show, then ask. Approval covers that one action; "continue" after a push does not cover the next commit.

Gated means any git command that publishes, rewrites history, discards uncommitted work, or moves the main worktree's HEAD: commit, push, force-push, rebase, amend, reset, clean, stash drop, tag, merge, cherry-pick, branch deletion, opening a PR, and a checkout or switch in the main worktree. These are the actions that cannot be cheaply undone or that other people see.

If the user declines, stop: do not retry or reword the request, and report what is ready. If nobody can approve (you are a subagent, or the session is non-interactive), do not perform the gated action; report what is ready instead.

**Stakeholder text:** plain words, attributed by branch, PR or commit. Don't use labels only you know (a task number from your own plan, a private file path). Show the PR body or question to the user at the gate before sending it.

## Red flags
| Thought | Reality |
|---|---|
| "Close enough to done" | Check all six "fully implemented" criteria explicitly |
| "Just this once", skip showing the diff first | Every gated action shows its diff, tests and message first — no exceptions |
| "The user probably wants X" | It's their choice — ask with options and a recommendation |
