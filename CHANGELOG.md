# Changelog

All notable changes to this repository's plugins are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and each plugin's `version` in its own `plugin.json` follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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
