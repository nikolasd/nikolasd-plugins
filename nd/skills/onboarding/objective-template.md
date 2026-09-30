# Goal-mode objective template

Fill the `<...>` slots from the interview answers, then call `goal` with `op: "create"` (no `goal` tool: use this text as the session todo list). Defaults to propose: `docs/onboarding/`, ≥25 citations, 2 rounds, read-only outside the output dir, `UNKNOWN — needs human`.

```markdown
## Objective
Produce a code-grounded onboarding documentation set for `<repo>` in `<docs_dir>` by spawning
specialist subagents (solution architect → C4; software engineer → engineering; AI engineer →
AI design; DevOps → infrastructure + deployment; <one per track when tracked>; principal
engineer → ONBOARDING). Evidence is code only — not README/CLAUDE.md/existing docs/comments.

## Success criteria
- Files exist: <list per layout: single = c4/01-context.md, c4/02-containers.md,
  c4/03-components.md, engineering.md, ai-design.md, infrastructure.md, deployment.md,
  ONBOARDING.md; tracked = the same under common/ plus <track>/README.md, <track>/components.md,
  <track>/agents.md for each track, OWNERSHIP.md, ONBOARDING.md>.
- `python <skill_dir>/checker.py <docs_dir> --layout <single|tracked> [--track ...] [--ai-doc runtime-design.md --agents-doc workloads.md if renamed]` prints PASS:
  0 dangling backtick-quoted paths, 0 bad line/symbol anchors, 0 inadmissible citations
  (README/CLAUDE.md/AGENTS.md/docs/), 0 placeholders, ≥25 unique citations per doc (ONBOARDING ≥40), mermaid in
  every C4/components doc, ONBOARDING links every sibling, relative links resolve,
  <tracked: track-leak regexes 0 hits; domain packages in common/ only under "Domain extension points">.
- OWNERSHIP.md (tracked only) maps every top-level source entry, tool module, seed/eval script
  and test group to a track with importer evidence; ambiguities carry a decision and reason.
- Every fact not derivable from code is the literal `UNKNOWN — needs human`; no placeholders.
- An independent review pass has checked the docs at the agreed depth (<full | targeted>) and
  applied corrections; checker PASS after the pass (or, if no interpreter works and the user
  accepted it, the gate is reported NOT RUN with the command).

## Verification
Run the checker yourself (orchestrator, not a subagent) after each round and after the review pass; skim each doc
once for stubs. Report PASS output, claims-checked and correction counts.

## Boundaries
Writes only in `<docs_dir>`. Read-only elsewhere; no git mutations, no running
server/tests/docker, no network (read-only Grep/Glob, or shell grep/find/wc where a shell exists, is fine). Existing prose (`README.md`,
`CLAUDE.md`, `AGENTS.md`, `docs/**`, `reference/**`, PRDs, `.docx`, docstrings) is not evidence;
it may be listed once, in ONBOARDING under a heading "Existing in-repo prose (unverified)".
Max 2 writer rounds per agent (initial + one revision).

## Stop conditions
Halt and surface to the user if: a fact the docs cannot stand without (for example, how the
system starts) cannot be derived from code; a write outside `<docs_dir>` would be needed; a
checker failure remains that the orchestrator cannot fix itself; an ownership decision cannot
be made from imports. Other undeterminable facts are recorded as `UNKNOWN — needs human`;
finish autonomously and report them grouped by owner.
```
