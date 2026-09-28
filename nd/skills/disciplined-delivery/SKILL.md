---
name: delivery
description: Use when about to write or change code — any feature, fix, or edit, however small — or when declaring work done, reporting status, or before any commit, push, rebase, amend, PR, or checkout change.
when_to_use: |
  Trigger phrases: "is this done", "ready to commit", "mark this complete", "let's ship it".
  Also before writing or changing any code, and when status is being reported.

  Not this skill: RED-GREEN-REFACTOR mechanics — see `superpowers:test-driven-development`.
---

# Disciplined Delivery

## Overview
Understand before changing, test before implementing, verify before claiming done, and get one explicit approval per irreversible action. When a choice is the user's to make or a requirement is ambiguous, stop and ask — options plus a recommendation, never a guess on the user's behalf.

**REQUIRED SUB-SKILL:** `superpowers:test-driven-development` — assumes RED before GREEN.
**RECOMMENDED:** `superpowers:verification-before-completion`, `superpowers:requesting-code-review`.

## The contract

**Before coding.** Understand the code touched, apply SOLID, DRY, YAGNI, KISS and the language's idioms, and ground decisions in real documentation. One task at a time.

**"Fully implemented" means ALL of:**
- Covers the spec, not a subset.
- Every acceptance criterion satisfied.
- Full suite green — not just the touched file.
- If the repo measures coverage: changed modules at ≥80%.
- If the repo keeps ADRs: every non-trivial decision recorded in one.
- Docs updated to match.

Missing any one is not "basically done" — name the gap. If the repo measures no coverage or keeps no ADRs, say so in the report.

**Self-review.** Read your diff adversarially, hunting for what's wrong. Stay scoped.

**Reporting.** "Plan executed" ≠ "requirements met." State what's verified, assumed, or open, and the real baseline used.

**Approval — one approval, one action.** Show the diff stat, test result, and exact message first, then wait for an explicit "approve" — for every commit, never inherited. A push, rebase, amend, PR, or checkout change (switching the branch of the main worktree) each needs its own "approve" too.

**Stakeholder text:** plain words, attributed by branch/PR/commit — never internal labels or private paths.

## Red flags
| Thought | Reality |
|---|---|
| "Continue" after a push approves the next commit | Approval is per commit, not inherited |
| Permission to use worktrees covers switching the main worktree's branch | A checkout change needs its own "approve" |
| The plan is complete, so the ticket is implemented | A plan built on assumptions isn't the requirements |
| The baseline was "before this branch" — from memory | State the actual baseline SHA and what was reused |
| Rationale belongs in a code comment next to the change | Rationale goes in an ADR if the repo keeps them; code gets a short pointer |
| A test that asserts on source text is good enough | Not a behavior test; find a real check or drop it |
| Change a data contract and update only the obvious consumer | Migrate every consumer; pin the contract with a test |
| "Close enough to done" | Check all six "fully implemented" criteria explicitly |
| "Just this once", skip showing the diff first | Every commit shows diff, tests, message first — no exceptions |
| "The user probably wants X" | It's their choice — ask with options and a recommendation |

## Quick reference
| Situation | Required action |
|---|---|
| Writing implementation code | Have a failing test first |
| Saying "done" | Check all six "fully implemented" criteria explicitly |
| A choice is the user's, or a requirement is ambiguous | Ask with options and a recommendation |
| About to commit | Diff stat, test result, exact message; wait for "approve" |
| About to push, rebase, amend, open a PR, or change checkout | Its own "approve", never inherited |
| Writing a PR body or stakeholder question | Plain language, attributed by branch/PR/commit, no internal paths |
