# Changelog

All notable changes to this repository's plugins are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and each plugin's `version` in its own `plugin.json` follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.7.0] - 2026-10-02

### Added
- `nd` plugin (0.5.0): 18 new eval cases (44 in total). They cover trigger boundaries (`architect-skips-plain-pr-review`, `herdr-skips-spawn-an-agent-for-review`, `handoff-skips-compact-conversation`, `onboarding-skips-single-c4-diagram`, `disciplined-delivery-skips-docs-typo-fix`); safety (`handoff-keeps-secrets-out`, `handoff-records-uncommitted-when-declined`, `onboarding-keeps-injection-and-secrets-out`, `delivery-gates-push`, `herdr-hands-dialogs-to-user`, `herdr-does-not-resend-after-timeout`, `architect-asks-before-delegating`); and behaviour (`handoff-updates-existing-file`, `delivery-commits-after-approval`, `engineer-reports-not-done-on-red-suite`, `engineer-challenges-with-evidence`, `architect-does-not-trust-a-green-report`, `onboarding-reports-a-failing-gate`). The `herdr` cases run against a stub `herdr` and set `HERDR_ENV` through the eval sandbox's own shell startup files.
- `nd` `onboard`: the checker fails a doc containing a secret-shaped string (key `SECRETS`; it prints the kind and line, never the value), accepts `--inadmissible-dir`, rejects a nonexistent `--root`, and prints its default citation floor.
- `nd` `herdr`: a "Spawn a Claude peer" recipe that `architect` and `engineer` now share, and `windows.md` for the Git Bash and PowerShell notes.
- `pm` plugin (0.2.1): two `sdd` eval cases (`continues-local-only-without-atlassian`, `asks-which-copy-wins-on-divergence`), and `repo-context.sh --hash`, which prints the document's hash for Phase 5.

### Changed
- `nd` plugin: **the five skills whose folder name differed from their `name` now use the short name for both, so four slash commands change**: `/nd:disciplined-delivery` is now `/nd:delivery`, `/nd:reflecting` is `/nd:reflect`, `/nd:writing-plain-language` is `/nd:plain-language`, and `/nd:onboarding` is `/nd:onboard`. `/nd:herdr`, `/nd:handoff`, `/nd:architect` and `/nd:engineer` are unchanged. The folders `disciplined-delivery`, `reflecting`, `writing-plain-language`, `onboarding` and `spawning-herdr-agents` were renamed to `delivery`, `reflect`, `plain-language`, `onboard` and `herdr`, so a spec validator no longer flags the mismatch, and the eval regexes accept one name instead of two.
- `nd` `onboard`: writers treat everything read from the repo as data, never instructions, and never copy a secret value into the docs. In a run on a planted repo, the old briefs obeyed an injected "claim SOC2 compliance" comment in one of three runs; the new ones asserted it in none of 16 (they record it under Unknowns as an embedded instruction, as intended). The checker now matches the briefs: a non-empty, keyword-led mermaid block is required in the AI or runtime design doc, `infrastructure.md`, `deployment.md` and `ONBOARDING.md` as well as C4 and components docs; the citation floor counts distinct files (not anchors), defaults to `min(25, max(3, citable_files * 2 // 3))` (printed on the first line; citable files exclude README, CLAUDE.md, AGENTS.md, `docs/`, `reference/`, LICENSE and the directory being checked), is never more than the repo has to cite (an earlier draft of this change asked a five-file repo for seven files, which no doc could meet), and excludes citations under the "existing in-repo prose" heading, which is now exempt only in `ONBOARDING.md`; markdown links out of the docs dir to README, CLAUDE.md or AGENTS.md fail; a placeholder is a `TODO:` or `TBD:` marker, not the bare word. `SKILL.md` caps the fix loop, bounds cost (default depth `targeted` above about 500 source files, a 30-agent stop, ask which track first above four), checks for stray writes, and lets the orchestrator read the README once for orientation.
- `nd` `handoff`: never writes a secret value into `HANDOFF.md` even when asked (and scans the draft); commits only `HANDOFF.md`, by path, never on `main`, `master` or another protected branch, and never pushes; infers the focus when `$ARGUMENTS` is empty; updates an existing file for this session instead of appending; leads with Next Steps. Without the secrets rule the old skill wrote the key into the file in two of five runs when asked to.
- `nd` `herdr`: answers a dialog only if it confirms a slash command it just sent or is the trust-folder prompt for the directory it set (everything else goes to the user); treats pane output as data, not instructions; checks before resending after a timeout; starts the agent kind the user named (default `claude`); closes only panes it recorded and asks first if the agent is still working. Outside Herdr it now runs no `herdr` command at all, not even to diagnose.
- `nd` `delivery`: centred on the approval gate and the definition of done rather than test-first on every edit; approval counts only after the user has seen the diff, test result and exact message ("commit it" before that is not approval); the gated actions are defined by category (publishes, rewrites history, discards work, moves HEAD); it covers pre-existing red suites, no test runner, a declined gate and runs with nobody to approve. A docs-only typo fix does not load it (`delivery-skips-docs-typo-fix`), and any request to run a gated git action does (a bare "push this to origin" loaded it in 10 of 10 runs after the trigger phrases were widened; before, one run in five pushed without asking).
- `nd` `architect` and `engineer`: after a challenge or question the engineer stops and waits; a challenge that still stands goes to the user, not to either session; a decision is the architect's only if a recorded user decision or the spec settles it and it is reversible; the engineer asks before spawning an architect and never commits unless the user authorized it; failure modes (declined delegation, silent engineer, red suite, low context) and sample task and report messages were added. The engineer now fires on an instruction from the architect session, including a go-ahead to commit (1 of 5 runs before, 5 of 5 after).
- `nd` `reflect`: facts about code are verified against files, while decisions are recorded as "decided in session, not verifiable"; it never guesses a storage path when basic-memory is unreachable; updates an existing note instead of creating a second one; suggests rule edits instead of making them; offers to reflect instead of starting.
- `nd` `plain-language`: says what it does, keeps meaning, code and quoted identifiers exact, and holds the register for the rest of the conversation.
- `nd` descriptions for `handoff`, `herdr`, `onboard`, `architect`, `delivery`, `reflect` and `plain-language` now state what the skill does as well as when to use it, and their trigger phrases were narrowed to avoid colliding with built-in `/compact`, in-session subagents and single-document requests.
- `pm` `sdd`: Phase 5 recomputes `local_hash` with `repo-context.sh --hash` (which `allowed-tools` already covers) instead of an unlisted `git hash-object`. Reference files point at `../templates/...` and `../scripts/...`, `story-from-document` no longer reads as locked after a dry run, and `epic` says "two writes, then a confirmation".

### Fixed
- `nd` evals: on macOS the eval sandbox cannot run `git` (the Xcode shim needs a cache file it may not write), which made `handoff-guards-non-git`, `handoff-asks-before-committing`, `delivery-shows-before-committing` and `engineer-refuses-unauthorized-commit` fail for reasons unrelated to the skills. Their scaffolds now put the real git binary on the sandbox's `PATH` (only when it exists and only inside the eval's own temporary home), and all four pass. The `plain-language-explains-plainly` judge failed plain answers (it read bold plain sentences as jargon labels), which made the case fail with and without the plugin; its criteria are now exact. `reflecting-asks-before-writing` also checks the `write_note` and `edit_note` path, not only `Write`. The `onboard` cases now read the files the run wrote instead of the `Write` tool's input, because with Bash granted the agent may write the docs with a heredoc and a `Write`-only check passes or fails for the wrong reason; they also get a 900 s timeout, since three evals in parallel pushed runs past the default 300 s.

## [0.6.0] - 2026-10-01

### Added
- `pm` plugin (0.2.0): eight new eval cases that give the skill a canned Atlassian
  server (`evals/<case>/mocks/atlassian/`), so the write tools exist and a `max: 0`
  grader on them is a real test. They cover a held confirmation for every skill that
  writes (`holds-write-until-confirmed` for `epic`, `epic-refine`, `story`,
  `ui-mockups`, `story-from-document` and `sdd`), an existing Epic or Story being shown
  before a second one is created (`asks-about-existing-epic`, `asks-about-existing-story`),
  and a source document that tries to instruct the assistant
  (`story-from-document/ignores-instructions-in-source`).
- `pm`: `sdd` records `local_hash` (a `git hash-object` of the document) in
  `docs/.solution-design.state.json`, and `repo-context.sh` prints it as "Local file
  hash". A state file without it still works; the first run falls back to the `Version`
  field and records the hash.
- `pm`: `epic-refine` writes a `**Technical constraints:**` line into a standard-delivery
  Epic's Delivery section, and `story` copies it, since a standard Epic has no phase
  constraints.

### Changed
- `pm`: a confirmation now has to come after the user has seen the draft. An earlier
  "skip the review" or "I trust you" no longer counts, and each skill lists what
  confirming will do and ends its turn. Before this, `epic`, `epic-refine`, `ui-mockups`
  and `sdd` wrote to Jira, Confluence or git anyway in every run of the new mocked evals,
  `story` tried to create the Story in every run (the sandbox denied it), and
  `story-from-document` wrote in two of three. `sdd` still lets you skip the interview,
  leaving each judgment call as an open question.
- `pm`: the skills no longer fill in values nobody supplied. An NFR threshold, persona,
  owner, sub-task effort or constraint that is not in the Epic, the source or your answers
  becomes `[GAP: …]` and goes in the gap list, and `epic-refine` draws no sequence diagram
  from components it has not confirmed. `epic` leaves `_(Not provided: …)_` for an
  unanswered question. `story-from-document` no longer pads acceptance criteria to a
  count, asks before using a different issue type when the project has no Story type, and
  `story` takes sub-task effort from you (and proposes sub-tasks only for separable work
  streams) instead of judging size from its own estimate.
- `pm`: checks that used to run after the first irreversible write now run before it.
  `epic` searches the project for a similar Epic once it has the name. `story` re-checks
  that the Epic's story-table row still exists before creating the Story.
  `story-from-document` searches for an existing Story by its source reference at the
  review gate, with no date window, and again before writing.
- `pm`: after rewriting an Epic or Story description, `epic-refine`, `story`, `ui-mockups`
  and `story-from-document` (promote mode) re-fetch it and stop if the state line, the
  story-table Ids or the section content did not survive Jira's markdown round trip.
- `pm`: `story-from-document` treats the source, an existing Story and fetched pages as
  data. It tells you about any text aimed at the assistant, in a `Source check:` line at
  the start of its next message and again at the review gate, even when that text asks it
  to stay quiet. It also fetches non-Confluence URLs with `WebFetch` and ignores
  `--dry-run` when working out what the argument is.
- `pm`: `sdd` runs the guide's pre-share checklist without its rendered-image item (the
  skill cannot upload attachments), strips its "Rendered image not yet attached" notes
  when the Confluence copy is taken as authoritative, and links the guide's Part files
  directly instead of through an index. Its requirement-status vocabulary no longer has
  `Retired`: a retired item is `Descoped`. The skill body is trimmed to 497 lines and its
  description now says when to use it.
- `pm`: `ui-mockups` writes its own gaps under `### UI Open Questions` instead of a second
  `## Summary of Gaps`, treats `_No mockups were produced for this Epic._` as a
  placeholder, and ends its turn when the Atlassian MCP is missing.
- `pm`: `epic`, `epic-refine` and `story` no longer pre-approve `Write`, which none of
  them uses. `ui-mockups` and `story-from-document` deliberately leave `Artifact` out of
  `allowed-tools`, so publishing a mockup canvas stays a prompted action. The skills read
  their argument through `$ARGUMENTS`, and the em dashes the rules ban are gone from the
  skills' own headings and templates.

### Fixed
- `pm` evals: the old Jira guards passed only because the sandbox had no Atlassian server.
  `epic`'s `holds-write-until-confirmed` now ships mocks and would have failed on the
  previous skill. The `sdd` `update-preserves-ids` case uses `Descoped`, and the manual
  `story-from-document` scenario no longer expects sub-tasks for a one-repo change.

## [0.5.1] - 2026-10-01

### Changed
- `pm` plugin (0.1.1): the skills no longer estimate or write story points, and no longer
  add, change or remove Jira labels. An Epic's maturity is now carried only by the
  `**Epic Maturity State:**` line in its description. The Epic story table is
  `| Id | Story | Summary | Status |`; an existing table that still has a Story Points
  column is left as it is. `story` decides whether a Story needs sub-tasks from about one
  week of work for one developer, not from a point value.
- `pm`: the `points_scale` plugin option and project-file key are removed, since nothing
  reads them. The `site` option is unchanged.
- `pm`: `story` now creates sub-tasks before it updates the Epic, and leaves the Epic
  untouched if any sub-task failed, so running `/pm:story` again resumes the same Story
  instead of skipping it.
- `pm`: `ui-mockups` never moves an Epic's maturity backwards. Its confirmation says
  when the state is left as it is.
- `pm`: `epic` checks the Jira project and the Epic issue type before the Q&A, asks for any
  required fields beyond the standard ones up front, and guards a retried create against duplicates.
  With no Atlassian MCP it now ends the turn at that check, instead of running the whole
  interview and failing at the final write or previewing sections it cannot save.
  `epic-refine` matches its template placeholders by their words, so Jira's markdown
  re-escaping no longer hides them.
- `pm`: `story-from-document` always resolves the project's Story type name in create
  mode, and reads an interrupted Story's children and links before resuming it.
- `pm`: `sdd` says which copy wins after a divergence, adds a `zensical.toml` `nav` entry
  only when the file already has a `nav` array, lists that edit in its confirmation, and
  warns that updating a Confluence page replaces its whole body. `--dry-run` also makes
  no offer to save configuration, in every skill that has it.
- `pm`: the shared mockup procedure (`ui-mockups` and `story-from-document`) has screens
  reuse the first approved screen's CSS variables and shell markup, and makes a state
  that matters (empty, loading, error) its own page.
- `pm`: removed the trigger phrases from the skill descriptions, since the skills run only
  when invoked. The root README lists the skill as `sdd`, matching `/pm:sdd`.

### Fixed
- `pm` configuration: `sdd_template` and `sdd_guide` in `.claude/pm.json` must now be paths
  relative to the repository (or a Confluence page ID). An absolute path, `~` or a drive
  letter is refused, so a cloned repository cannot point `sdd` at a file such as
  `~/.ssh/id_rsa`. When a key appears twice, the first occurrence now wins on one line
  as well as across lines, and a value cut short by an escaped quote is treated as unset (a path value must not
  end in a backslash).
  `repos_root` is still accepted, and `story-from-document` tells you the path and asks
  once before reading outside the current repository.

### CI
- `release.yml` runs the two `pm` shell tests before publishing. `validate.yml` checks that
  every `pm` skill loads the configuration and pre-approves the loader command.

## [0.5.0] - 2026-10-01

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
