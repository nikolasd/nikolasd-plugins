---
title: architect-engineer-evals
type: task
status: active
permalink: nikolad-plugins/tasks/architect-engineer-evals
description: Add eval coverage for the nd architect and engineer skills
started: 2026-09-24
---

# architect-engineer-evals

The `architect` and `engineer` skills landed without the trigger / near-miss / applied cases that CONTRIBUTING.md asks for. The user deferred the evals on 2026-09-24; this note tracks them.

## Observations
- [status] active
- [description] Add eval coverage for the nd architect and engineer skills
- [context] Candidate applied scenarios from the 2026-09-24 skill review: engineer missing, so architect spawns via herdr instead of a subagent; approval for step 1 doesn't carry to step 2; architect commit instruction without user authorization, so engineer asks the user.
- [context] Test across Haiku, Sonnet and Opus per Anthropic's skill best practices; `runs: 5`, Sonnet judge, per nd/evals/README.md.

## Steps
1. Trigger + near-miss + applied case for `architect` in `nd/evals/architect/`.
2. Trigger + near-miss + applied case for `engineer` in `nd/evals/engineer/`.
3. Cases that need a shell get the `requires-bash` tag and a positive-control grader.
4. Run the suite and record results under `docs/memory/evals/`.
