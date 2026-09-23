# Contributing

This is a personal plugin marketplace, but the conventions below apply to any change,
including ones made in future sessions by an AI assistant.

## Adding or changing a skill

1. Follow the skill-authoring guidance in Anthropic's Claude Code skills reference —
   a tight `description` and `when_to_use` block matter more than the body. A
   near-miss case in the eval suite (below) is how an over-broad `description` gets
   caught.
2. Every skill in `nd/skills/` should have eval coverage in `nd/evals/`: at minimum a
   **trigger** case (natural phrasing that should fire it), a **near-miss** case
   (adjacent phrasing that should *not* fire it), and an **applied** case (the skill
   doing its actual job, with the real behaviour asserted).
3. Run the suite before merging — see [`nd/evals/README.md`](nd/evals/README.md) for
   exact commands, cost estimates, and machine-specific gotchas. **Never draw a
   conclusion from a single run**; the judge is noisy, which is why every case sets
   `runs: 5` and a Sonnet judge is the documented default, not Haiku.
4. If a case needs a specific starting filesystem/git state (a dirty repo, a missing
   `.git`, files matching a narrative in the prompt), give it a `scaffold_script`
   rather than relying on the harness's default sandbox state or the prompt alone —
   see `nd/evals/handoff/*/setup.sh` for examples, and `nd/evals/README.md`'s
   "Resolved" sections for what happens when a case skips this.

## Adding a new plugin

1. `<plugin-name>/.claude-plugin/plugin.json` — include `name`, `displayName`,
   `version`, `description`, `author`, `license`, `keywords`, and `repository`
   (`https://github.com/nikolasd/nikolasd-plugins` — the marketplace's own identifier
   in `.claude-plugin/marketplace.json` is `nikolad-plugins`, a separate string, don't
   conflate the two).
2. Register it in `.claude-plugin/marketplace.json` with a relative `source` path.
3. Run `claude plugin validate <plugin-dir>` before committing.
4. Add a row to the plugin table in `README.md`.

## Commit and changelog conventions

- One semantic commit per change; the commit body should explain *why*, not restate
  the diff.
- Update `CHANGELOG.md` under `[Unreleased]` for anything a user of the plugins would
  notice (new/changed/removed skill behaviour, new eval cases, manifest changes).
  Internal housekeeping (doc formatting, session notes) doesn't need an entry.
- Bump the affected plugin's `version` in its `plugin.json` when cutting a release,
  and move the `[Unreleased]` entries under a new dated version heading in
  `CHANGELOG.md`.

## Basic Memory

This repo's Basic Memory project is rooted at `docs/memory/` inside the checkout, so
notes travel with the repo. `.claude/settings.local.json` (gitignored) holds the local
path mapping and does not travel — run `/basic-memory:bm-setup` on a new machine to
recreate it.
