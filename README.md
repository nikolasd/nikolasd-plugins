# nikolad-plugins

A [Claude Code](https://code.claude.com) plugin marketplace: personal workflow skills
and a Python language server integration.

## Plugins

### `nd` — Personal Skills

Personal workflow skills for session handoff, session reflection, plain-language
writing, spawning/controlling agents via Herdr, and a paired architect/engineer
session workflow.

| Skill | Command | What it does |
| :--- | :--- | :--- |
| `handoff` | `/nd:handoff` | Produces a `HANDOFF.md` so a fresh agent can continue the work without the current conversation. |
| `reflecting` | `/nd:reflecting` | Consolidates learnings from a session into project notes after a significant conversation, refactor, or rule change. |
| `spawning-herdr-agents` | `/nd:herdr` | Spawns, runs, and controls other coding-agent sessions via Herdr — panes, tabs, and agent sessions. |
| `writing-plain-language` | `/nd:writing-plain-language` | Rewrites jargon-heavy text in plain language for a non-specialist reader. |
| `architect` | `/nd:architect` | Plans, reviews and validates changes, and delegates implementation to a separate engineer session spawned via Herdr. Every decision stays with the user. |
| `engineer` | `/nd:engineer` | Implements tasks from a separate architect session with TDD and spec verification, and reports back with evidence. |

Backed by an 18-case eval suite (`nd/evals/`) run with `claude plugin eval` — see
[`nd/evals/README.md`](nd/evals/README.md) for how to run it, known
machine-specific gotchas (macOS git sandboxing, Linux sandbox dependencies), and
past findings.

### `ty-lsp` — ty Language Server

Python code intelligence via Astral's [`ty`](https://github.com/astral-sh/ty)
language server — diagnostics and code intelligence for `.py`/`.pyi` files.

## Installation

Add this marketplace in Claude Code:

```
/plugin marketplace add nikolasd/nikolasd-plugins
```

Then install a plugin (the marketplace's own identifier is `nikolad-plugins`, distinct
from the GitHub repo name `nikolasd-plugins`):

```
/plugin install nd@nikolad-plugins
/plugin install ty-lsp@nikolad-plugins
```

For local development, install straight from a checkout instead:

```
/plugin marketplace add /path/to/nikolad-plugins
```

## Repository layout

```
.claude-plugin/marketplace.json   # marketplace manifest — registers both plugins
.github/workflows/                # manifest validation (every push) + release-on-tag
nd/                                # Personal Skills plugin
  .claude-plugin/plugin.json
  skills/<skill-name>/SKILL.md
  evals/                          # eval suite, run with `claude plugin eval`
ty-lsp/                           # ty Language Server plugin
  .claude-plugin/plugin.json
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
