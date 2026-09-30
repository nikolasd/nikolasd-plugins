# Changelog

All notable changes to this repository's plugins are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and each plugin's `version` in its own `plugin.json` follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `pm` plugin (0.1.0): project-management skills for Jira and Confluence, using the
  official Atlassian MCP server (registered as `atlassian`). All six skills run only
  when invoked, because each can write to Jira, Confluence or git, and each asks
  for explicit confirmation of a full draft before it writes anything.
  - `epic`, `ui-mockups`, `epic-refine` and `story`: a staged Epic-to-Story
    pipeline. `epic` turns a business-level Q&A (optionally seeded from a PRD)
    into a high-level Epic; `ui-mockups` optionally adds screens for business
    review; `epic-refine` adds technical detail grounded in code the agent has
    read; `story` creates one Story at a time from the Epic's story table. The
    Epic's maturity is tracked by a state line and a label, and each skill
    updates the Epic in one write, carrying existing labels forward.
  - `story-from-document`: builds a verified Story from a source document or
    brief, or promotes an existing Story in place (keeping the original text),
    with sub-tasks and dependency links. It checks claims against the real
    repositories with `file:line` evidence, never duplicates sub-tasks or links
    from an earlier run, and supports `--dry-run`, which writes nothing anywhere
    (Jira, Confluence or claude.ai).
  - `sdd` (`/pm:sdd`): creates or refreshes one living Solution Design Document per
    repository, grounded in the code, as a local markdown file and a Confluence
    page kept in sync. It detects hand edits on either side by page version and
    uncommitted changes, adopts an existing page with the standard title, preserves
    every ID on updates, and commits only the paths it names after one
    confirmation that lists every side effect. The bundled template and authoring
    guide are organisation-neutral, and either can be replaced with your own (a
    file or a Confluence page). The guide is split by Part and loaded per Part; its
    fictional examples are never copied into a document, and template text cannot
    override the skill's rules.
- `pm` configuration: two plugin options (`site`, `points_scale`) plus an optional
  per-project `.claude/pm.json` (`project_key`, `repos_root`, `sdd_template`,
  `sdd_guide`, `sdd_space`, `sdd_parent_id`), resolved by `pm/scripts/config.sh` and
  injected into every skill. Project-file values are format-checked, and invalid
  ones are ignored. Anything not configured is asked for, with an offer to save it.
- `pm` mockups: each screen is rendered to a PNG by Chrome, Edge, Chromium or
  Brave on macOS, Linux or Windows (`PM_BROWSER` selects one), falling back to a
  private Claude Design canvas (after asking, and never during a dry run), then to
  HTML files only.
- `pm` quality checks: an eval suite in `pm/evals/` (ten cases; see its README for
  what it can and cannot cover and for how they were calibrated), and deterministic
  tests for the configuration loader and the `sdd` repository-context script,
  `pm/tests/`, which run in CI.

### Changed
- The marketplace identifier is now `nikolasd-plugins` (it was misspelled
  `nikolad-plugins`) and matches the GitHub repo name. If you added the marketplace
  under the old name, remove it and add it again; plugins install as
  `nd@nikolasd-plugins`, `pm@nikolasd-plugins` and `ty-lsp@nikolasd-plugins`.

## [0.4.0] - 2026-10-01

### Added
- `nd` plugin: `onboarding` skill (frontmatter `name: onboard`; the command is
  `/nd:onboarding`, from the folder name), moved in from personal
  `~/.claude/skills` — a workflow for producing a code-grounded onboarding
  documentation set (C4 context/containers/components, engineering, AI design,
  infrastructure, deployment, ownership map, fork-style ONBOARDING) for any repo,
  with a three-layer `common/` + per-track layout when the repo holds several
  discrete products. Ships `checker.py` (citation/dangling-path/mermaid/link/
  track-leak acceptance gate with `--layout`, `--track NAME:REGEX`, `--ai-doc`,
  `--agents-doc`), `briefs.md` (subagent and reviewer briefs) and
  `objective-template.md` (goal-mode objective). What was verified, and how, is in
  the next entry and in `nd/evals/README.md`.
- `nd` plugin: `onboarding` now runs outside the original harness (subagent and
  goal-tool fallbacks, explicit phase order, an inventory step before briefing) and
  `checker.py` enforces the code-only rule: it fails inadmissible citations (README,
  CLAUDE.md, `docs/`, `reference/`) outside an "Existing in-repo prose" section, line
  and symbol anchors that don't exist, TODO/TBD placeholders, and ONBOARDING entries
  that mention a sibling without linking it; paths match case-exactly, and MIME
  types, `~`/`@` strings and `path:func()` anchors are handled. Agents now report in
  fixed plain-text headings instead of JSON. The minimum-citations rule now counts
  unique citations (path plus anchor) rather than unique files, and the rules say a
  file the docs call absent is named in plain text. `SKILL.md` gained a workflow
  checklist, a Python preflight (an unrun gate is reported NOT RUN, never PASS), a
  "running short" rule, and a verification-depth choice (`full` or `targeted`); track
  detection and gate details moved to `tracks.md` and `gate.md`. Reviewers are
  capped by group size, work alone (no helper agents) and must return a report with a
  `Covered` line, after a real run showed one oversized reviewer stall, spawn helpers
  that applied nothing, and leave the orchestrator to reconcile about 35 findings.
  The checker now also keeps the README exemption open across sub-headings, counts
  route-group paths like `src/app/(auth)/login/page.tsx` and bare `*.config.*` files,
  ignores symbols that occur only in comment lines, and `gate.md` has a failure-to-action
  table, a definition of "fails twice", and an always-pass-`--root` rule. The brief
  tells writers to backtick a file only when citing its real path and to write "to-do
  comments" instead of the literal placeholder words; in a mixed repo `agents.md`
  covers agents and workloads, and the reviewer count for tracked repos is stated
  (and marked unmeasured).
  84 tests in `tests/onboarding/` (the checker, plus consistency tests that tie the
  brief, `gate.md` and `SKILL.md` to the checker).
  Evidence, with its limits: 4 eval cases. The trigger case fires on natural phrasing
  (5/5 with the plugin); its Δ +1.00 is structural, since a baseline cannot load a skill
  it lacks. The near-miss does not over-fire. The applied case passes but does not
  discriminate from a baseline (Δ 0.00). The full-workflow case is one run each on two
  real repos, both single-layout Next.js apps: the second finished (score 0.82, 10 agents,
  824 claims checked and 68 corrected by the agents' own count) and its output passes the
  checker when run afterwards, but its final-report grader was skipped, not passed, and
  the agent had no shell to run the checker itself. That run used a repo about eight times
  smaller than the one where a reviewer stalled, so it does not show the review-group cap
  fixes that stall. The tracked layout, round-2 fixes, `targeted` depth and Haiku/Opus
  have not been exercised by an agent.

## [0.3.0] - 2026-09-28

### Added
- `nd` plugin: `disciplined-delivery` skill (frontmatter `name: delivery`; the command
  is still `/nd:disciplined-delivery`, from the folder name) — a delivery protocol
  that applies before any code is written or changed, however small the edit:
  research before code, test first, the definition of "fully implemented" (coverage
  and ADR criteria apply where the repo uses them), adversarial self-review, honest
  status reporting, and one explicit "approve" per commit, push, rebase, amend, PR or
  checkout change. Test-first mechanics are delegated to
  `superpowers:test-driven-development`.
- `nd/evals/disciplined-delivery/`: 4 cases. `tests-first` (a plain coding request
  must get a test edited before the code), `flags-incomplete-done` (trigger),
  `skips-code-explanation` (near-miss), and `shows-before-committing` ("Commit it"
  must still get the diff stat, test result and commit message shown, and an
  "approve" asked for, first). Run 2026-09-28 on Windows (5 runs × 2 arms, Sonnet
  judge): `tests-first` 1.00 with the plugin vs 0.00 without (Δ +1.00, skill fired
  5/5); `flags-incomplete-done` and `skips-code-explanation` 1.00 in both arms; and
  `engineer-skips-solo-task` re-run at 1.00, since the new skill now also fires on
  solo coding tasks. `tests-first` checks edit order with a regex over the trace; an
  llm judge failed correctly ordered runs because it judged the final reply.
  The skill's earlier description ("starting a coding task") fired on only
  6 of 12 small-edit runs, which is why the description now names any edit.
  `shows-before-committing` needs Bash and has not been run yet: this machine's
  unreadable Automox PATH entry blocks it, so it still needs a Linux run.

## [0.2.0] - 2026-09-24

### Added
- `nd` plugin, two skills moved in from personal `~/.claude/skills`: `architect`
  (plans, reviews and delegates to a separate engineer session) and `engineer`
  (implements architect tasks with TDD, reports back with evidence). Each spawns its
  missing peer via Herdr and sets the peer's model with `/model`, since a skill's
  `model:` field only lasts one turn.
- `nd/evals/architect/` and `nd/evals/engineer/`: trigger / near-miss / applied eval
  cases for both new skills (6 cases), closing the gap tracked in
  `docs/memory/tasks/architect-engineer-evals.md`. The applied cases regression-test
  the two highest-severity rules: `architect-stops-without-herdr` (no engineer session
  + `HERDR_ENV` unset must stop delegation, not fall back to self-implementing or a
  subagent) and `engineer-refuses-unauthorized-commit` (an architect instruction to
  commit only counts if it says the user authorized it). Run for real 2026-09-24 (5
  runs × 2 arms, Sonnet judge): all six at 1.00 score / 1.00 pass rate with the plugin,
  after fixing three test-authoring bugs surfaced along the way — see
  `nd/evals/README.md`'s Resolved section. No changes needed to either `SKILL.md`.

## [0.1.1] - 2026-09-23

No plugin behaviour changed — repository packaging and tooling only.

### Added
- `README.md`, `CONTRIBUTING.md`, this changelog.
- `repository` field on both `nd` and `ty-lsp` `plugin.json`.
- CI: `.github/workflows/validate.yml` validates both plugin manifests (schema only,
  no API credentials) on every push and PR into `main`.
- Release pipeline: `.github/workflows/release.yml` publishes a GitHub Release with
  notes pulled from this file whenever a `vX.Y.Z` tag is pushed.

### Removed
- `HANDOFF.md` — its session-continuity purpose is done (both review items verified
  on Linux); its substantive findings live on in `nd/evals/README.md` and this file.

## [0.1.0] - 2026-09-23

Initial release of both plugins.

### Added
- `ty-lsp` plugin: Python code intelligence via Astral's `ty` language server.
- `nd` plugin, four skills: `handoff`, `reflecting`, `spawning-herdr-agents`,
  `writing-plain-language`.
- `nd/evals/`: a 12-case eval suite for the four skills (trigger / near-miss /
  applied per skill), run with `claude plugin eval`.
- MIT license.
- Basic Memory knowledge base at `docs/memory/`, version-controlled with the repo.

### Changed
- `handoff`: added a git-repo Prerequisite check, a confirm-before-committing step for
  pending work, a non-git guard, a mistakes table, and a completion checklist.
- `reflecting`: removed frontmatter overrides (model/effort/allowed-tools), narrowed to
  a single note destination.
- `spawning-herdr-agents`: added PowerShell variants, tightened the trigger
  description.
- `writing-plain-language`: rewritten from an always-on prohibition list into a
  request-triggered skill built on a positive recipe. A "Common swaps" table added
  during the rewrite was later removed after an eval A/B showed it added no
  measurable benefit over the recipe's own "Everyday words" guidance.

### Fixed
- `handoff-guards-non-git` (eval case): the case initially had no scaffold, so neither
  its "not a git repo" premise nor its prompt's narrative had any supporting evidence
  in the sandbox — a model that checked for evidence correctly declined to fabricate a
  handoff. A first scaffold fix (`rm -rf .git` plus stub files matching the prompt)
  improved but didn't fully resolve it, because the harness's seeded git repo's root
  doesn't necessarily match the scaffold script's own working directory. The scaffold
  now asks git where its repo actually is and removes exactly that, verified with a
  clean 5/5 run on Linux. `handoff/SKILL.md` itself needed no changes for this.
