# Phase 3.5: UI mockups

Read this when the user wants mockups for the story (`SKILL.md` Phase 3.5).

If the story involves a user-facing screen or change, offer to generate UI
mockups for it. Ask the user once whether mockups would help, and default to
skipping for backend-only, library, or infrastructure work where there is
nothing to show.

If the user wants mockups, do not reinvent the mockup workflow here. Follow the
shared procedure in
[`../../ui-mockups/references/mockup-core.md`](../../ui-mockups/references/mockup-core.md),
the same core the `ui-mockups` skill uses, supplying:

- **`<context>`**: the high-level summary agreed in Phase 3 (the problem, the
  shape of the work, and any personas it implies).
- **`<artifact-id>`**: in promote mode, the existing story key; in create mode,
  a slug derived from the story (for example `audit-log-filters`), because no
  Story key exists yet.
- **`<product-repo-path>`**: the absolute path of the primary enhancement-scope
  repository from Phase 2.1, where the design language is scanned.
- **`<render-script>`**: `${CLAUDE_PLUGIN_ROOT}/skills/ui-mockups/scripts/render.sh`
- **Dry run**: yes when this run is a `--dry-run`, otherwise no.

The procedure settles the screen list, shows each screen for iterative review (a
rendered PNG, or a private Claude Design canvas when no browser is available),
and assembles a `User Interface Mockups` section. When it returns, fold the
assembled section into the Story body under a `## User Interface Mockups`
heading, and remember the visual evidence it reports (the PNG files, the canvas
link, or neither) so you can tell the user what to attach or share once the Story
is created. This skill does not post the Q&A transcript the core also returns;
ignore it. The structure of the assembled section comes from
[`../../ui-mockups/templates/mockup-section.md`](../../ui-mockups/templates/mockup-section.md):
read it when you assemble the section.

Under `--dry-run`, still generate and review the mockups locally, include the
assembled section in the draft Story body, and report the PNG directory. Do not
publish a canvas: use rendering or files only.
