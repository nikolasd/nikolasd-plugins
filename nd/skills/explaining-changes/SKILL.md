---
name: explaining-changes
description: Explains a finished code change to the engineer who will maintain it. Use when an implementation (feature, bug fix, refactor) is finished and is being reported back, after each task of a multi-task plan, at the end of a branch, or when the user asks to explain or walk through the changes.
when_to_use: |
  Trigger phrases: "explain the changes", "walk me through what you changed", "explain it like to a junior engineer", "what patterns did you use", "report back", "wrap up and report back", "what did you change". Also: the moment an implementation is done and you are about to report back to the user, after each task completes in plan execution, and once for the whole branch before a PR.

  A question about one change ("why did you change X") gets an answer about that change only, with its Why and Principle, not the whole walkthrough.

  Not this skill: reviewing someone else's diff for defects (a review skill), writing a commit message or PR description, a report-back to another agent (an architect session or a plan controller keeps its own evidence format), or a trivial change (a one-line fix, a constant or rename, a typo, a config tweak), which gets a sentence or two.
---

# Explaining Changes

The reader is the engineer who will maintain this code; assume a junior engineer unless the user says otherwise. After reading, they know what changed in every file, why it had to change, and which principle the change follows, so they could make the next change the same way.

## The source

Explain the **final diff**, never the commits. `<base>` is where the work started: the merge base with the target branch, or the commit before the current task in plan execution.

- Work not committed yet (the usual case right after implementing): `git diff <base>` compares with the working tree, and `git status --porcelain` lists the untracked files that no diff shows. Read each new file in full.
- Everything committed: `git diff <base>..<head>`.

Read every hunk before writing. Take the file list from `git diff --stat` plus the untracked files, and make sure every file appears in the explanation. Generated, vendored and lock files share one line: named, not walked through.

## The shape

Write in this order:

1. **Scope**, one line: the range, the number of files, and that it is the final diff.
2. **Big picture**, two to four sentences: what the change does and how its parts connect. Add a small diagram only when data flows across several components.
3. **One section per file**, a file that others use before the files that use it. For each change in the file:
   - **Added / Deleted / Changed `exact_name`**: what it is or did, in one or two sentences.
   - **Why**: the problem it solves, what would break without it, and where that came from (ticket, bug, review finding, test failure).
     When you did not make the change in this session, mark a reason read off the code as inferred and say when the source is unknown; never invent a ticket or a bug.
   - **Principle**: the named pattern, principle or practice, and why it applies *here*. For a purely mechanical change (rename, formatting, an extra blank line), say so plainly, without inventing a principle.
   - For a deletion, say why the code had to go and what replaces it, if anything.
4. **Tests**: per test file, the behaviour it proves, and the testing practice it follows.
5. **Weak points**: edge cases not handled, behaviour changes callers will notice, deferred items, and anything verified only by reading.

## Rules for the reader

- Define a term the first time it appears, and show why the obvious alternative fails (for example, `0.1 * 3` with floats gives `0.30000000000000004`).
- Use the exact names in the code, and make every claim match the diff. Mark a behaviour you did not run or test as unverified.
- Size each part to its change: one line for a trivial change, a paragraph for a design decision. Group several trivial changes into one line.
- Explain a principle fully the first time it appears; later changes that follow it name it and say what it does there, without repeating the general case.

## Common mistakes

| Mistake | Instead |
|---|---|
| A table or sections per commit | Sections per file, from the final diff |
| `base..HEAD` while work is uncommitted | `git diff <base>` plus the untracked files |
| Only additions explained | Each deletion gets its own "Deleted" line and reason |
| "Follows best practices" | The named principle, and why it applies here |
| A list of what changed, no reasons | Every change has a Why |
| A reason guessed from the code stated as fact | Marked as inferred |
| Cosmetic changes hidden | Listed and called cosmetic |
| Everything sounds equally important | The big picture first; detail sized to the change |
