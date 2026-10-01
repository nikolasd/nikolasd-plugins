# pm

## Description

Claude Code skills for project management — turning a business idea into fully-detailed, code-verified Jira Epics and Stories, and maintaining a per-repository Solution Design Document grounded in the actual code.

Aimed at product managers, tech leads, and engineers who need well-structured, consistently-formatted Jira/Confluence artifacts — grounded in real evidence from the codebase rather than written from memory — without doing all of the drafting and cross-checking by hand.

## Installation

Requires [Claude Code](https://docs.anthropic.com/claude-code) (latest) and git configured for GitHub access (an SSH key in `ssh-agent`, or `gh auth login` for HTTPS). This is a Claude Code plugin, installed and updated entirely through the Claude Code CLI — **no local clone of this repo is required**; Claude Code fetches directly from GitHub into its own plugin cache.

**Install:**

```bash
claude plugin marketplace add nikolasd/nikolasd-plugins
claude plugin install pm@nikolasd-plugins --scope user
```

Or, from inside a Claude Code session:

```
/plugin marketplace add nikolasd/nikolasd-plugins
/plugin install pm@nikolasd-plugins --scope user
```

`--scope user` (the CLI default if `--scope` is omitted) is recommended here: this plugin has no scope-sensitive hooks, so installing once at user scope makes it available in every repo without a per-project install or commit.

Confirm it loaded:

```bash
claude plugin list
```

You should see `pm` in the output.

**Update:** Claude Code caches installed plugins by the version in `plugin.json` — refresh the marketplace catalog, then update the plugin. You only receive an update when that version has actually changed:

```bash
claude plugin marketplace update nikolasd-plugins
claude plugin update pm --scope user
```

**Uninstall:**

```bash
claude plugin uninstall pm --scope user
```

## Skills

| Skill | Invoke | Description |
|-------|--------|-------------|
| epic | `/pm:epic` | Step 1: business-level Q&A, optionally starting from a PRD or requirements document, that creates a new Jira Epic with High Level Requirements sections populated |
| ui-mockups | `/pm:ui-mockups EPIC-123` | Step 1.5 (optional): generates high-fidelity screen mockups (PNG images, or a private Claude Design canvas when no browser is available) for iterative business review, then writes a User Interface Mockups section into the Epic |
| epic-refine | `/pm:epic-refine EPIC-123` | Step 2: technical Q&A that reads the codebase and populates NFRs, Personas, Technology Context, story tables, and sequence diagrams |
| story | `/pm:story EPIC-123` | Step 3: generates one Jira Story at a time from the Epic's story table, populating all sections from the Epic content and codebase, and updates the Epic story table and maturity state |
| story-from-document | `/pm:story-from-document <source OR story key>` | Standalone (not part of the epic pipeline). Two modes: **create** a new verified Jira Story from a source artifact (a Confluence page, a local document, or a written brief), or **promote** an existing Story (often a placeholder) by fleshing it out in place. Either mode can optionally attach the Story to an existing Epic as a child (parent link only, no Epic story-table or maturity change). Investigates claims against the relevant repos with `file:line` evidence; sub-tasks and Blocks links; optional UI mockups via the shared mockup core. Supports `--dry-run` |
| sdd | `/pm:sdd [--dry-run]` | Standalone, scoped to the repo it runs in (no Jira key). Creates or refreshes one living Solution Design Document against a Solution Design Document template (the bundled Template v2.0, or one you supply as a file or Confluence page), grounding every section it can in the codebase with `file:line` evidence and interviewing the user, batched by document Part, for anything that is a judgment call rather than a fact. Writes a local markdown copy (Zensical-aware path if `docs/zensical.toml` exists) and a Confluence page, kept in sync; the first run creates, every later run updates in place, preserving every existing requirement/risk/decision ID. Supports `--dry-run` |

All six skills run only when you invoke them (`/pm:<name>`); none fires on its own,
because each one can write to Jira, Confluence or git. Each asks for explicit
confirmation of a full draft before it writes anything.

## Requirements

- The official Atlassian MCP server, active in your Claude Code session and registered
  under the name `atlassian`: the skills call its tools as `mcp__atlassian__*`. A server
  registered under a different name, or a third-party Atlassian MCP with different tool
  names, is not supported.
- For `sdd`: a git identity (`user.name` and `user.email`), because it commits.
- A POSIX `sh` on your PATH (macOS, Linux, or Git Bash on Windows). The plugin's
  configuration loader and mockup renderer are short shell scripts; they need no
  `jq` or `python3`.
- Optional, for `ui-mockups` images: Chrome, Edge, Chromium or Brave. Without one,
  the skill falls back to a private Claude Design canvas.

The skills read local code, so run Steps 1.5 to 3, `story-from-document`, and `sdd` from
inside the relevant repository. `sdd` is scoped to exactly one repository per run and
needs no Jira access.

## Configuration

Nothing is required up front: a skill asks for any value it needs and offers to save
the answer. To set values in advance, use either layer below. When the same key is set
in more than one place, the project file wins over the plugin option, which wins over
the built-in default.

**Plugin options** (one set per user, asked when the plugin is enabled, changed with
`claude plugin configure pm@nikolasd-plugins`):

| Option | Meaning | Default |
|---|---|---|
| `site` | Your Atlassian site hostname, for example `acme.atlassian.net`. Picks the right site when several are accessible and builds issue links. | asked when needed |

Claude Code keeps one value per option per user, even for a project-scope install. For
anything that differs between projects, use the project file.

**Project file** `.claude/pm.json` in the repository root: a flat JSON object of string
values, safe to commit. Every key is optional.

```json
{
  "site": "acme.atlassian.net",
  "project_key": "PROJ",
  "repos_root": "/work/repos",
  "sdd_space": "DOCS",
  "sdd_parent_id": "1234567891"
}
```

| Key | Used by | Meaning |
|---|---|---|
| `site` | all skills | Overrides the plugin option for this project. |
| `project_key` | `epic`, `story-from-document` | Default Jira project key, offered instead of asking. |
| `repos_root` | `story-from-document` | Directory holding the repositories to investigate, when they are not siblings of the current one. The skill tells you the path and asks once before reading outside the current repository. |
| `sdd_template`, `sdd_guide` | `sdd` | The template and authoring guide to use instead of the bundled ones: a local file path relative to the repo root, or a Confluence page ID. Absolute paths and `..` are refused, so a cloned repository cannot point the skill at files elsewhere on your machine. |
| `sdd_space`, `sdd_parent_id` | `sdd` | Default Confluence space key and parent page for a new document. |

Values cannot contain double quotes or nested objects, when a key appears twice the first one wins, and a value may not end in a backslash. Because the file can come from a
repository you did not write, each value is checked against a strict format (`site` a
hostname, `project_key` letters, digits and underscores, `sdd_space` and `sdd_parent_id`
letters, digits, `_`, `-` and `/`, paths plain path characters) and anything else is ignored
with a note. The configuration is loaded
through Claude Code's shell injection, so it is available in Claude Code only: on
claude.ai every value is treated as unset and asked for.

---

## Authoring pipeline — how to use

Step 1 works from any directory. Steps 1.5, 2, and 3 read the codebase from the
current working directory — run them from inside the product repo for best
results.

### Step 1 — High Level Requirements

```
/pm:epic
```

Creates a new Jira Epic. Business-level Q&A only — no technical questions.

### Step 1.5 — UI Mockups (optional)

```
/pm:ui-mockups EPIC-123
```

Optional step between Steps 1 and 2. Generates high-fidelity screen mockups that
you review and iterate on, then writes a User Interface Mockups section into the
Epic and advances maturity to "UI Mockups Created". Each screen is shown by the
first of these that works:

1. **A PNG image**, rendered headless by Chrome, Edge, Chromium or Brave on
   macOS, Linux, or Windows (Git Bash), into a temp folder; nothing is installed
   and the images are not committed to the repo. You attach the agreed PNGs to
   the Epic manually. Set the `PM_BROWSER` environment variable to a browser path
   or command to choose a specific browser.
2. **A private Claude Design canvas**, when no browser is found or rendering
   fails, after you agree to it. It is published to claude.ai and only you can
   open it until you share it from its Share menu; the Epic carries the link.
3. **The HTML files only**, if neither is possible. The screen descriptions in
   the Epic are then the whole record.

Run from inside the product repo so the mockups match the existing design
language.

### Step 2 — Detailed Requirements

```
/pm:epic-refine EPIC-123
```

Updates an existing Epic created by Step 1. Technical Q&A — run from inside
the product repo so Claude can read the codebase.

### Step 3 — Story Generation

```
/pm:story EPIC-123
```

Generates one Jira Story at a time from the Epic created by Steps 1 and 2.
Run from inside the product repo so Claude can read the codebase. Re-run the
command to generate the next story; the Epic story table and maturity state
update on each invocation.

### Story from a document (independent of the epic pipeline)

```
/pm:story-from-document <source OR existing story key e.g. PROJ-1234>
```

Builds a fully detailed Jira Story, with sub-tasks and dependency links, without
needing a parent Epic. The skill asks up front which of two modes to run:

- **Create** turns a source artifact (a Confluence page, a local document, or a
  written brief) into a brand-new Story.
- **Promote** takes an existing Story key, including a quick placeholder, and
  fleshes it out to the same level of detail in place, keeping its key.

Either way it investigates the relevant claims against the local repositories
and verifies them against real code with `file:line` evidence, drafts a
high-level summary plus low-level planning detail, and on approval creates the
sub-tasks and their Blocks links (including cross-repo sequencing and external
prerequisites). Create mode creates the Story; promote mode updates the existing
one in place with `editJiraIssue`.

Both modes can optionally attach the Story to an existing Epic as a child. This
sets only the parent link: it deliberately does **not** add a row to the Epic's
story table or change the Epic's maturity (that synchronisation is the job of
the Step-3 `story` skill). In promote mode the Epic offer is made only
when the story has no parent already.

Pass `--dry-run` to produce the full draft (in promote mode, the full updated
body) without writing anything: nothing to Jira, Confluence or claude.ai (mockups
are rendered locally or left as files, never published). To write it afterwards,
say so in the same conversation. Optional UI mockups are generated
through the same shared core the `ui-mockups` skill uses
(`ui-mockups/references/mockup-core.md`). Run from inside or alongside the
product repos so the investigation can read them.

### Epic maturity model

The Epic's maturity is the `**Epic Maturity State:**` line in its description. The
skills never set Jira labels or story points.

| State | Set by |
|-------|--------|
| High Level Requirements Created | Step 1 |
| UI Mockups Created | Step 1.5 (optional) |
| Detailed Level Requirements Created | Step 2 |
| Story Creation In Progress | Step 3 |
| All Stories Created | Step 3 |

The state only moves forward: running `ui-mockups` on an Epic that has already been
refined leaves the state where it is.

### Full process

| Step | Tool | Skill |
|------|------|-------|
| 1 - High Level Requirements | Claude Code or claude.ai | `/pm:epic` |
| 1.5 - UI Mockups (optional) | Claude Code (from inside repo) | `/pm:ui-mockups` |
| 2 - Detailed Requirements | Claude Code (from inside repo) | `/pm:epic-refine` |
| 3 - Story Generation | Claude Code (from inside repo) | `/pm:story` |

---

## Solution Design authoring — how to use

```
/pm:sdd
```

Run from inside the repository the document should describe. The first run
creates `docs/solution-design.md` (or `docs/<docs_dir>/solution-design.md`
when the repo has a `docs/zensical.toml`) and, once you confirm, a matching
Confluence page in a space you choose. Every later run in the same repo
refreshes that same document in place: it re-grounds the technical sections
against the current code, shows you what changed, and asks only about what
drifted or is still open — not the whole document again. Every judgment call
(priority, risk severity, cost, ownership, an ADR's status) is always put to
you; the skill never invents one.

What it changes, and only after one confirmation that lists all of it: it writes
the document and `docs/.solution-design.state.json`, adds a `nav` entry to
`docs/zensical.toml` when that file already has a `nav` array, creates or updates
the Confluence page, and commits exactly those paths on the current branch
(nothing else you had staged). Updating a Confluence page replaces its whole body
with the markdown, so macros, inline comments and manual layout on that page are
not preserved. The state file records the Confluence page and its version
so a later run can tell whether either side was edited by hand. If you already
have a hand-written page with the standard title, the skill offers to adopt it
instead of creating a second one. Pass `--dry-run` to see the full draft without
writing or committing anything.

## Troubleshooting

**A skill does nothing, or stops before asking anything, in a headless or CI run.**
Every skill starts by running the plugin's configuration script through `sh`. A
permission setup that blocks shell commands stops the skill silently, because the
skill never reaches the model. Allow `Bash(sh *)` (or `Bash`) for that run. In an
interactive session you are asked instead.

**A skill keeps asking for the Atlassian site.** Set the `site` plugin option
(`claude plugin configure pm@nikolasd-plugins`) or add `"site"` to `.claude/pm.json`.

**A skill stops with a shell error right at the start.** The `site` plugin option
was typed with a quote character in it. It must be a plain hostname such as
`acme.atlassian.net`; fix it with `claude plugin configure pm@nikolasd-plugins`.

## What the skills never touch

The Epic and Story skills never set or change Jira **labels** or **story points**
(the points field is left untouched on every Story they create or promote, and the
Epic story table has no points column). Epic maturity is kept in the description only.

## Authors & Contributing

Originally created by Mark Ransome. Adapted into `pm` and maintained by Nikolas
Demiridis.

Contribution conventions are in [CONTRIBUTING.md](../CONTRIBUTING.md); changes are
recorded in [CHANGELOG.md](../CHANGELOG.md). Licensed under [MIT](../LICENSE).
