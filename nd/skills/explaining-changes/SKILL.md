---
name: explaining-changes
description: Explains a finished code change to the engineer who will maintain it. Use when an implementation (feature, bug fix, refactor) is finished and is being reported back, after each task of a multi-task plan, at the end of a branch, or when the user asks to explain or walk through the changes.
when_to_use: |
  Trigger phrases: "explain the changes", "walk me through what you changed", "explain it like to a junior engineer", "why did you change X", "what patterns did you use". Also: the moment an implementation is done and you are about to report back, after each task completes in plan execution, and once for the whole branch before a PR.

  Not this skill: reviewing someone else's diff for defects (a review skill), writing a commit message or PR description, or a change that is only a typo fix in prose.
---

# Explaining Changes

The reader is a junior engineer who will maintain this code. After reading, they know what changed in every file, why it had to change, and which principle the change follows, so they could make the next change the same way.

## The source

Explain the **final diff**, never the commits: `git diff <base>..<head>` (`<base>` is where the work started, such as the merge base with the target branch). Read every hunk before writing. Run `git diff --stat <base>..<head>` and make sure every listed file appears in the explanation.

## The shape

Write in this order:

1. **Scope**, one line: the range, the number of files, and that it is the final diff.
2. **Big picture**, two to four sentences: what the change does and how its parts connect. Add a small diagram only when data flows across several components.
3. **One section per file**, in the order the data flows (what others depend on comes first). For each change in the file:
   - **Added / Deleted / Changed `exact_name`**: what it is or did, in one or two sentences.
   - **Why**: the problem it solves, what would break without it, and where that came from (ticket, bug, review finding, test failure).
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
| Only additions explained | Each deletion gets its own "Deleted" line and reason |
| "Follows best practices" | The named principle, and why it applies here |
| A list of what changed, no reasons | Every change has a Why |
| Cosmetic changes hidden | Listed and called cosmetic |
| Everything sounds equally important | The big picture first; detail sized to the change |
