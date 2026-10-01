# nikolasd-plugins

A [Claude Code](https://code.claude.com) plugin marketplace: personal workflow skills
and a Python language server integration.

## Plugins

### `nd` — Personal Skills

Personal workflow skills for session handoff, session reflection, plain-language
writing, spawning/controlling agents via Herdr, a paired architect/engineer
session workflow, a disciplined-delivery protocol for test-first, fully
verified changes with per-action approval gates, and a code-grounded
onboarding-documentation workflow.

| Skill | Command | What it does |
| :--- | :--- | :--- |
| `handoff` | `/nd:handoff` | Produces a `HANDOFF.md` so a fresh agent can continue the work without the current conversation. |
| `reflecting` | `/nd:reflecting` | Consolidates learnings from a session into project notes after a significant conversation, refactor, or rule change. |
| `spawning-herdr-agents` | `/nd:herdr` | Spawns, runs, and controls other coding-agent sessions via Herdr — panes, tabs, and agent sessions. |
| `writing-plain-language` | `/nd:writing-plain-language` | Rewrites jargon-heavy text in plain language for a non-specialist reader. |
| `architect` | `/nd:architect` | Plans, reviews and validates changes, and delegates implementation to a separate engineer session spawned via Herdr. Every decision stays with the user. |
| `engineer` | `/nd:engineer` | Implements tasks from a separate architect session with TDD and spec verification, and reports back with evidence. |
| `disciplined-delivery` | `/nd:disciplined-delivery` | Research-before-code, test-first implementation, the definition of "fully implemented," adversarial self-review, honest reporting, and per-action git approval gates. |
| `onboarding` | `/nd:onboarding` | Produces a 360° onboarding doc set (C4, engineering, AI design, infra/deploy, ownership) grounded on code only, via specialist subagents, a bundled acceptance checker, and a mandatory verify-and-fix review pass. |

Backed by a 26-case eval suite (`nd/evals/`) run with `claude plugin eval` — see
[`nd/evals/README.md`](nd/evals/README.md) for how to run it, known
machine-specific gotchas (macOS git sandboxing, Linux sandbox dependencies), and
past findings.

### `pm` — Project Delivery Toolkit

Project-management skills for Jira and Confluence, via the official Atlassian MCP
server: a guided Epic-to-Story authoring pipeline and per-repository Solution Design
Document authoring, each grounded in the actual codebase. Originally created by Mark
Ransome. See [`pm/README.md`](pm/README.md).

| Skill | Command | What it does |
| :--- | :--- | :--- |
| `epic` | `/pm:epic` | Step 1: business-level Q&A that creates a new Jira Epic with High Level Requirements. |
| `ui-mockups` | `/pm:ui-mockups` | Step 1.5 (optional): screen mockups for business review, written back into the Epic. |
| `epic-refine` | `/pm:epic-refine` | Step 2: technical Q&A that reads the codebase and completes the Epic. |
| `story` | `/pm:story` | Step 3: generates one Jira Story at a time from the Epic's story table. |
| `story-from-document` | `/pm:story-from-document` | Builds or promotes a single verified Jira Story, with sub-tasks and dependency links, without an Epic. |
| `sdd` | `/pm:sdd` | Creates or refreshes one living Solution Design Document per repository. |

### `ty-lsp` — ty Language Server

Python code intelligence via Astral's [`ty`](https://github.com/astral-sh/ty)
language server — diagnostics and code intelligence for `.py`/`.pyi` files.

## Installation

Add this marketplace in Claude Code:

```
/plugin marketplace add nikolasd/nikolasd-plugins
```

Then install a plugin (the marketplace's identifier, `nikolasd-plugins`, is the same as
the GitHub repo name):

```
/plugin install nd@nikolasd-plugins
/plugin install pm@nikolasd-plugins
/plugin install ty-lsp@nikolasd-plugins
```

For local development, install straight from a checkout instead:

```
/plugin marketplace add /path/to/nikolasd-plugins
```

## Repository layout

```
.claude-plugin/marketplace.json   # marketplace manifest — registers all plugins
.github/workflows/                # manifest validation (every push) + release-on-tag
nd/                                # Personal Skills plugin
  .claude-plugin/plugin.json
  skills/<skill-name>/SKILL.md
  evals/                          # eval suite, run with `claude plugin eval`
pm/                                # Project Delivery Toolkit plugin
  .claude-plugin/plugin.json
  skills/<skill-name>/SKILL.md
ty-lsp/                           # ty Language Server plugin
  .claude-plugin/plugin.json
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
