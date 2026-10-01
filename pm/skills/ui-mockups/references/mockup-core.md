# Mockup generation core

The destination-agnostic procedure for producing UI screen mockups. It is
shared by more than one skill, so it knows nothing about where the result
ends up. A calling skill supplies the inputs below, runs this procedure, and
then writes the output to its own destination (a Jira Epic, a Jira Story, or
anywhere else).

Owners and callers today:

- [`../SKILL.md`](../SKILL.md) — the `ui-mockups` skill (Epic destination).
- `../../story-from-document/SKILL.md` — the `story-from-document` skill (Story
  destination).

## Contents

- [Inputs the caller must provide](#inputs-the-caller-must-provide)
- [Output the caller receives](#output-the-caller-receives)
- [Content rules](#content-rules)
- [Working directory and rendering](#working-directory-and-rendering)
- [Step A: Scan the codebase for the design language](#step-a-scan-the-codebase-for-the-design-language)
- [Step B: Ask for additional design references](#step-b-ask-for-additional-design-references)
- [Step C: Settle the screen list](#step-c-settle-the-screen-list)
- [Step D: Generate and iterate, one screen at a time](#step-d-generate-and-iterate-one-screen-at-a-time)
- [Step E: Assemble the section](#step-e-assemble-the-section)

## Inputs the caller must provide

- **`<context>`** — a description of the work the mockups are for: its
  objective, scope, success criteria, and any named personas. The `ui-mockups`
  skill derives this from the Epic; `story-from-document` derives it from the
  high-level summary it has already agreed with the user. This procedure does
  not care where it came from.
- **`<artifact-id>`** — a short slug used to name the temporary working
  directory and the Claude Design canvas, and to label the screens in the assembled section. Use the
  Epic or Story key when one exists, otherwise a slug derived from the work
  (for example `audit-log-filters`).
- **`<product-repo-path>`**: the absolute path of the repository whose design
  language the mockups should match. Step A scans it, wherever the session
  was started.
- **`<render-script>`**: the absolute path of `render.sh`. The caller defines it
  from `${CLAUDE_PLUGIN_ROOT}`, which is not substituted inside this file.
- **Dry run** (optional): if the caller is in a dry run, rung 2 below is not
  allowed.

## Output the caller receives

- The complete `User Interface Mockups` section as markdown, assembled from
  [`../templates/mockup-section.md`](../templates/mockup-section.md).
- The visual evidence, which is one of: a working directory of PNG files (one
  per approved screen), a link to a private Claude Design canvas, or neither
  (descriptions only). Report which one, so the caller can tell the user what
  to attach or share.
- A transcript of the screen-list Q&A (Steps C and D). A caller that posts an
  audit comment (`ui-mockups`) uses it; a caller that does not can ignore it.

The caller is responsible for writing the section to its destination and for
telling the user what to attach or share there. This procedure never writes
to Jira.

## Content rules

Apply the calling skill's content rules. In addition: screen descriptions are
written for a business reader, not an engineer, and every bullet is a complete
sentence.

## Working directory and rendering

Render all HTML and PNG files to a temporary directory, never into the repo.
Run `mktemp -d "${TMPDIR:-/tmp}/pm-mockups-<artifact-id>.XXXXXX"` once and hold
the result as `<work-dir>` (this works on macOS, Linux, and Git Bash on
Windows). The repo holds working code only; mockup images must not be committed
because they go stale.

Each screen is shown to the user by the first of these rungs that works. Stay
on one rung for the whole session unless it fails:

1. **PNG from a local browser.** `scripts/render.sh` finds Chrome, Edge,
   Chromium or Brave on macOS, Linux, or Windows (Git Bash) and renders
   headless. Nothing needs installing if one of those is present; set the
   `PM_BROWSER` environment variable to a browser path or command to choose a
   specific one.
2. **A Claude Design canvas**, only when rung 1 fails (no browser found, or
   rendering fails) or the user asks for a shareable page, the `Artifact` tool is
   available, and the caller is not in a dry run.
3. **Files only.** Give the user the path of each HTML mockup to open in any
   browser; the descriptions and annotations then carry the whole record.

Never block the session on rendering.

---

## Step A: Scan the codebase for the design language

Scan `<product-repo-path>`. Dispatch the `Explore` sub-agent via the `Agent` tool
with this prompt (if sub-agents are not available, use `Grep`, `Glob` and `Read`
on the same questions):

> "I am about to generate UI screen mockups for a new feature. Return a
> 200-word orientation on this product's user interface so the mockups match
> its real look and feel. Identify: the frontend framework, any component
> library or design system in use, the colour palette and typography (theme
> tokens, CSS variables, or a brand/style file if present), the overall layout
> pattern (top bar, sidebar, page structure), and the names of a few existing
> screens or components I can use as visual reference. Focus on visual and
> structural conventions, not business logic. Avoid a full audit."

Use the returned summary to skin the mockups so they look like the existing
product. If the repo has no frontend, note that and use a clean, neutral
modern style.

## Step B: Ask for additional design references

Ask once:

> "Are there any existing design references I should match? For example a
> Confluence page, a brand guide, a Figma link, or screenshots. Share any
> links now or reply 'none' to skip."

If provided, fetch each with the appropriate tool (Atlassian MCP for
Confluence, WebFetch for URLs, Read for uploaded files) and summarise in 1-2
sentences each.

## Step C: Settle the screen list

Ask one question at a time. Offer numbered options where helpful; always
include "(other)" as a free-text option.

**C.1 Propose the screen list.** Derive a candidate list of screens from
`<context>` (scope, success criteria, personas). Present the list with a
one-line purpose for each, then ask the user to confirm, amend, add, or remove
screens. Keep the list focused on the journeys that matter for sign-off.

**C.2 Capture each screen's intent.** For each confirmed screen, capture in
turn:
- **Primary persona** — who uses this screen (from `<context>` personas or a
  new one the user names).
- **Purpose** — what the user is trying to accomplish on this screen.
- **Key elements** — the main content, controls, and data the screen must show.
- **Important states** — which of empty, loading, error, and populated states
  matter. Default to the populated state if the user is unsure.
- **Style constraints** — any specific brand or layout requirement. Default to
  the design language found in Step A.

Keep this lightweight: enough direction to draft a first mockup the user can
react to, not a complete specification.

## Step D: Generate and iterate, one screen at a time

The core loop. Do not batch-render every screen before the user has seen the
first one. For each screen:

**D.1 Author the HTML mockup.** Write one page per screen to
`<work-dir>/<screen-slug>.html`, in the design language found in Step A and for
the screen's intent from Step C. Build the screen from plain HTML and inline
CSS only: no web fonts, image URLs or CDN links, so it renders offline in any
headless browser. Use CSS shapes, emoji or inline SVG for icons and placeholder
imagery. Define the product's palette and typography once as CSS variables in
`:root`, and reuse them across every screen of the Epic so the screens look like
one product.
Size the page to a fixed 1440x1024 canvas (an element with that width and height
and `overflow: hidden`) so the screenshot captures the whole screen cleanly. For
another size, pass matching width and height arguments to the renderer.
Each screen is its own file, so carry the look across by copying: once the first
screen is approved, reuse its `:root` variables and its shell markup (top bar,
navigation, content area) verbatim in every later screen and change only the
content. Show a state that matters (empty, loading, error) as its own page,
`<screen-slug>-<state>.html`, and treat it as its own screen in the section.

**D.2 Show the screen to the user**, using the rung chosen above.

*Rung 1, PNG.* Run the bundled renderer, using the `<render-script>` the caller
gave you:

```
sh "<render-script>" "<work-dir>/<screen-slug>.html" "<work-dir>/<screen-slug>.png"
```

It prints `Rendered: <path>` and exits 0. Exit 1 means a bad argument or a
missing HTML file: fix the call. Exit 2 means no browser was found, so move to
rung 2. Exit 3 means a browser ran but produced no image: retry once, then move
to rung 2. In a dry run, move to rung 3 instead of rung 2. When it succeeds, `Read` the PNG yourself to confirm the
whole screen rendered (not blank, not cut off) and fix the HTML if it did not,
before the user sees it. Then open it for the user with `open "<png>"` on
macOS, `xdg-open "<png>"` on Linux, or `cmd.exe /c start "" "<png>"` on Windows
under Git Bash. If opening is not possible, such as in a remote session, give
the path instead.

*Rung 2, Claude Design canvas.* This publishes the mockup content to
claude.ai as a private page, so ask first:

> "I can't render images here. I can publish these screens as a private Claude
> Design canvas on claude.ai instead. Only you can open it until you share it.
> Shall I?"

If the user declines, or the `Artifact` tool is not available, use rung 3.
Otherwise:

1. Call `Artifact` with `action: "quickstart"`, `intent: "design"` and
   `design_systems: false`. If a Design type is listed, create one canvas from
   its `type_url` with the title `<artifact-id> UI mockups`, then follow the
   instructions the create call returns for the file layout and how to fill it.
   Never hard-code a type URL: it belongs to the account. If no Design type is
   listed, use rung 3; do not publish a plain page.
2. Author each screen as its own artboard from the same layout, copy and design
   language as its HTML mockup. Do not publish the HTML as it is: the
   Design format has its own rules, so carry the content across and follow the
   type's instructions. The canvas is one artifact for the whole screen list;
   add one artboard per screen, sized to the 1440x1024 canvas unless
   the design needs otherwise.
3. Hold the returned link as `<design-url>`. It is private. Tell the user that
   others cannot open it until they share it from the page's Share menu.

*Rung 3, files only.* Tell the user the path of each HTML mockup in
`<work-dir>` so they can open it in any browser. Record nothing visual in the
assembled section; it carries descriptions and annotations only.

**D.3 Gather feedback and iterate.** Ask what to change. Edit the HTML,
re-render, and re-open (rung 1), or edit the artboard file and publish again to
the same canvas `url` (rung 2): the link stays the same and each publish is a
new version. Repeat until the user confirms the screen looks right.
Treat this as the main value of the procedure: keep the loop fast and the
changes small and visible.

**D.4 Draft the screen annotations.** Once approved, write a short description
of the screen for a business reader, plus a numbered list of annotations that
call out each key element and any state-specific behaviour. These become the
durable record, because an image cannot be embedded automatically and a link
may go stale or never be shared.

Move to the next screen and repeat D.1 to D.4.

## Step E: Assemble the section

Build the complete `User Interface Mockups` section using
[`../templates/mockup-section.md`](../templates/mockup-section.md). For each
screen include its name, primary persona, purpose, business-reader
description, numbered annotations, relevant states, and the closing line for
the rung used (an `_Attach:_` line naming the PNG, a `_Mockup:_` line with
`<design-url>`, or the no-image line), as the template describes.

Hand the assembled section back to the calling skill, together with the
visual evidence: the `<work-dir>` and the PNG list, the `<design-url>`, or
neither. Do not write anything to Jira here; the caller owns that.
