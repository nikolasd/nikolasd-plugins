# The gate

Read this before step 6 of the workflow. You run the checker yourself (the orchestrator, not a subagent).

## Command

```
python <skill_dir>/checker.py <docs_dir> --root <evidence_root> --layout single|tracked [--track NAME:REGEX ...]
```

`<skill_dir>` is the directory holding `SKILL.md`. **Always pass `--root`**, set to the evidence root recorded in the inventory (step 3): the directory that every cited path is relative to. The default (the nearest parent of `<docs_dir>` containing `.git`) is wrong whenever the target is a subfolder of a monorepo, and every citation then comes back dangling.

| Option | Use |
|---|---|
| `--root <evidence_root>` | always (see above) |
| `--min-cites N` | only if the user changed the default of 25 (ONBOARDING always needs 40) |
| `--ai-doc`, `--agents-doc` | when the AI and agents docs were renamed (see [tracks.md](tracks.md)) |
| `--track NAME:REGEX` | tracked layout only, once per track (see [tracks.md](tracks.md)); quote the regex for your shell, since `\|` and `/` mean different things in bash and PowerShell |
| `--allow-placeholders` | downgrade TODO/TBD from failure to warning; use only if the user asks |

It exits 0 on PASS and 1 on FAIL, and prints one line per doc.

## What it checks, and what it cannot

It checks that cited things exist and are spelled exactly, that anchors are plausible, and that the rules in the briefs were followed. It cannot check that a claim is true: a `:symbol` anchor is matched as a whole word in the file's non-comment lines, so a symbol that appears only in a docstring (Python triple quotes) still passes. Truth is the review pass's job.

## Failure to action

Each line of output names the failing doc and a key. Fix in this order, doc by doc.

| Key in the output | Who fixes | Action |
|---|---|---|
| `dangling` (shorthand such as `billing/`, or a file the doc says is absent) | last editor, round 2 | Send the round-2 message from `briefs.md` with the exact flagged strings: full path, or drop the backticks. |
| `dangling` (a path that should exist but does not, or differs in letter case) | last editor, round 2 | Same message; the writer corrects the path or replaces the claim with `UNKNOWN — needs human`. |
| `FAIL: <N cites` | last editor, round 2 | Ask for more anchored citations of claims already made, not new claims. |
| `FAIL: no mermaid` | last editor, round 2 | Ask for the missing diagram of the required kind. |
| `INADMISSIBLE` | orchestrator if only backticks need dropping; else last editor | Remove the citation of README, CLAUDE.md, AGENTS.md, `docs/`, `reference/` or a `.docx`, or move the mention under "Existing in-repo prose (unverified)" in ONBOARDING. |
| `bad_anchors` | last editor, round 2 | Correct the line range or symbol against the code; do not guess. |
| `LEAK`, `DOMAIN_LEAK` | last editor, round 2 | Generalize the passage or move it under "Domain extension points" or to `OWNERSHIP.md`. |
| `MISSING` | the writer of that doc | Re-dispatch that writer; if the AI doc was renamed, you probably forgot `--ai-doc`. |
| `missing_links`, `broken_links` | orchestrator | Add or repair the markdown links yourself. |
| `placeholder` | orchestrator | Replace with `UNKNOWN — needs human` plus what was searched, or remove. |

## Fix loop

1. The two-round cap is per file and counts writer rounds only. A doc **fails twice** when it still fails after its round-2 message. Halt then, per the stop conditions, and report the doc and the failing keys to the user.
2. After the review pass the last editor is a finished reviewer, so the orchestrator makes the fixes in the table itself, then re-runs the checker. It halts only when it cannot fix one.
3. Re-run the checker after every edit, not only at the end.
