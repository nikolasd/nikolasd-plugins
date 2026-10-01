---
name: epic-refine
description: >
  Refines an existing Jira Epic with technical detail: runs a technical Q&A
  grounded in the codebase, then writes NFRs, personas, Technology Context,
  per-phase story tables, completion statements and sequence diagrams into the
  same Epic and advances its maturity to "Detailed Level Requirements Created".
  Step 2 after `epic` (and the optional `ui-mockups`).
when_to_use: >
  Only after `epic` has created the Epic ("High Level Requirements Created"),
  or after the optional `ui-mockups` step ("UI Mockups Created"). Not for
  creating an Epic (use `epic`) or for creating Stories (use `story`).
allowed-tools: [Read, Write, Glob, Grep, WebFetch, Agent, mcp__atlassian__getAccessibleAtlassianResources, mcp__atlassian__getJiraIssue, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getConfluencePage, "Bash(sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh *)"]
model: sonnet
effort: high
disable-model-invocation: true
argument-hint: "<EPIC-KEY>"
arguments: epic-key
---

Populate the Detailed Requirements sections of an existing Jira Epic by reading
the codebase and conducting a technical Q&A session, then update the Epic in
Jira with the completed content and advance its maturity state.

## Configuration

!`sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh '${user_config.site}'`

The block above holds this plugin's settings, resolved from the project file
`.claude/pm.json` first, then the plugin's own configuration, then built-in
defaults. A value shown as `(unset)` is not configured: ask the user for it at
the point it is first needed, then offer to save it to `.claude/pm.json` in the
project root (a flat JSON object of string values, for example
`{"site": "acme.atlassian.net", "project_key": "PROJ"}`) so later runs do not
ask again. If no block appears above, treat every value as unset.

## Resolve the Atlassian cloud ID

Before any other Atlassian call, call `mcp__atlassian__getAccessibleAtlassianResources`
once.

- If it returns one resource, use it. If it returns several, use the one whose
  `url` contains `site`; if `site` is `(unset)`, list them and ask the user
  which to use.
- Hold the chosen resource's `id` as `<cloud_id>`, and derive `<browse_url>` as
  its `url` followed by `/browse/`.
- If the call errors or is denied but `site` is set, use `site` as `<cloud_id>`
  (the Jira and Confluence tools accept the site hostname as `cloudId`) and
  `browse_url` from the block as `<browse_url>`. If `site` is also `(unset)`,
  ask the user for their Atlassian site hostname and use it the same way.
- Stop only if a later Atlassian call fails because the tools are missing, and
  tell the user:

  > "The Atlassian MCP is not active in this session. This skill needs it to read and update the Jira Epic.
  > Ask whoever manages your Claude Code setup to enable the official Atlassian MCP
  > server, registered as `atlassian`."

## Jira connection

- **Cloud ID:** `<cloud_id>` resolved above

## Content rules

Apply to all generated content without exception:

1. No em dashes. Rewrite any sentence that would need one.
2. No LLM-signal phrasing ("scope - in", "leveraging", etc.).
3. Every bullet point is a complete grammatical sentence.
4. Plain, professional language. Active voice preferred.
5. Story summaries must include functional requirements, non-functional
   requirements, and deliverables in a single coherent statement.
6. Never estimate story points and never add, change or remove Jira labels.
   Maturity lives in the `**Epic Maturity State:**` line only.
7. Claims about existing code carry `path/to/file.py:120` evidence from a file
   you have read in this session. Never state a framework, module, route or
   store as fact without it: ask the user, or mark it `[GAP: ...]`.

## Phase 1: Load context

Execute steps 1.1 and 1.2 before asking the user anything. Step 1.3 then asks
one question.

**1.1 Read the Jira Epic.** Fetch the Epic using the `epic-key` argument (or
ask for it if not provided). Use `mcp__atlassian__getJiraIssue` with
`responseContentFormat: markdown`. Extract and hold:
- The full description body
- The delivery structure (phased or standard: inferred from whether
  "Phased Delivery" or "## Delivery" heading exists in the description)
- All Step 1 content (Objective, Context, Scope, Success Criteria,
  Risks and Dependencies, Phase Goals if phased)
- The "User Interface Mockups" section if it has real content (added by the
  optional Step 1.5 `ui-mockups` skill). Use its screen descriptions to inform
  the frontend parts of Technology Context and the per-phase story tables.

Confirm to the user which Epic was loaded and its current maturity state
before continuing. Read the state from the `**Epic Maturity State:**` line; if
the line is missing, ask the user which state the Epic is in. The states, in
order, are: High Level Requirements Created, UI Mockups Created, Detailed Level
Requirements Created, Story Creation In Progress, All Stories Created. **Re-entry:** if any story table row already has an Id
(Stories were created), say so. Never overwrite or remove a row that has an Id;
only fill placeholder rows and add new rows.

**1.2 Scan the codebase.** Dispatch the `Explore` sub-agent via the `Agent` tool
with this prompt:

> "Read-only. Summarise this repo's languages and frameworks, top-level
> packages or services, and any existing architecture documentation at the repo
> root or in obvious docs directories, in about 200 words. Then list, as paths
> with one line each, the files that define its API routes, data models or
> storage, authentication, and frontend structure. Do not modify anything."

Use the summary to inform Phase 2 questions. Before you state anything from the
code as fact in Phase 2 (for example "you use FastAPI"), `Read` the file behind
it and cite `path/to/file.py:120`. If sub-agents are not available, use `Grep`,
`Glob` and `Read` directly.

**1.3 Ask for additional requirements documents.** Ask once:

> "Are there any Confluence pages, wireframes, or other documents I should
> read before we start the technical Q&A? Share any links now or reply
> 'none' to skip."

If provided, fetch each document using the appropriate tool (Atlassian MCP
for Confluence, WebFetch for URLs; ask the user to export a Word document to
PDF or paste its text). Summarise in 1-2 sentences per document.

---

## Phase 2: Technical Q&A

Work through each section below in order. For each section:

- State in one sentence what you are capturing and why it matters.
- Ask one question at a time. Offer numbered options where helpful; always
  include "(other)" as a free-text option.
- Do not proceed to the next section until the current one is complete.
- One focused follow-up question is allowed if an answer is thin or ambiguous.
- Technical and architectural questions are expected and appropriate here.
- Where codebase evidence informs a question, reference it explicitly with its
  `file:line` (e.g. "`app/main.py:12` shows FastAPI: should the new endpoints
  follow the existing `features/` module pattern?").

### 2.1 Non-Functional Requirements

Capture NFRs covering scale, performance, security, and data integrity as
relevant to this Epic. Each NFR must be specific enough to be testable:
include thresholds, limits, or SLAs where applicable.

Ask about each dimension in turn: scale first, then performance, security,
data integrity. Skip any dimension the user confirms is not applicable.

Write the result as a table with exactly these columns:
`| NFR | Category | Requirement and threshold |`.

### 2.2 Personas

Capture the personas who interact with this feature. For each persona collect:
name, type (Client or Internal Staff), a one-line role description, and their
primary actions with this feature.

Suggest personas based on the Epic Scope and any codebase evidence (e.g.
existing auth roles, user types visible in the code), then ask the user to
confirm, amend, or add.

Write the result as a table with exactly these columns:
`| Persona | Type | Role | Primary actions |`. `story` uses the first row as
its default persona, so order the rows by importance.

### 2.3 Technology Context

Capture enough technical orientation for Step 3 story generation. Work through
each field below. Where codebase evidence gives a confident answer, state it
with its `file:line` and ask the user to confirm rather than asking cold.

- **Platform / architecture pattern** (e.g. microservices, event-driven,
  medallion)
- **Key services / components**: names of the primary backend services,
  shared libraries, and frontend modules in scope
- **Storage**: data stores used and how they evolve across phases
- **Auth / identity**: authentication and authorisation mechanism; roles
  enforced; prerequisites
- **API style**: REST / GraphQL / etc.; versioning pattern; naming conventions
- **Frontend framework**: confirm if visible in codebase
- **Key external dependencies**: libraries, SDKs, or third-party services
  this Epic depends on

Write each field as a bold label followed by its value, for example
`**Storage:** PostgreSQL via SQLAlchemy (app/db.py:8)`, so `story` can copy the
slice a story touches.

### 2.4 Phased delivery details

**If the Epic uses phased delivery:**

For each phase present in the Epic (Phase 1 Core, Phase 2 MVP, and Phase 3
if included), collect the following in order. Complete one phase fully before
moving to the next.

**Per phase:**

a) **Personas primarily served**: which personas from 2.2 are the primary
   audience for this phase?

b) **Key technical constraints**: what must be true technically for this
   phase to be built safely? (e.g. "read-only, no auth enforcement yet",
   "depends on Phase 1 spike output", "requires library X to be updated first")

c) **Story table**: generate the stories for this phase based on the phase
   Goal, Scope, NFRs, and Technology Context. The table has exactly the columns
   `| Id | Story | Summary | Status |`. For each story produce:
   - Id: empty (`story` fills it when the Story is created)
   - Story: a short descriptive name (e.g. "Feedback list API"), **unique
     within the whole Epic**, because `story` matches rows by name
   - Summary: a single sentence covering functional requirements,
     non-functional requirements where applicable, and deliverables
   - Status: `Not created`

   There is no effort or story points column: do not add one. If an existing
   table already has a Story Points column, keep it and leave the cells of new
   rows empty. Present the story table to the
   user for review before proceeding. Apply any amendments before moving on. If
   the phase genuinely needs no stories, say so and ask the user how to proceed.

d) **Phase complete when**: a plain-language observable outcome statement
   written so a non-engineer can verify it.

e) **Sequence diagrams**: generate one or more Mermaid `sequenceDiagram`
   diagrams for this phase. Separate read paths and write paths where both
   exist. Each diagram must have a bold heading above it and sit in a fenced
   ```mermaid block, so the text survives the markdown round trip. Show actors,
   UI, API, storage, and auth components as relevant. Use the component names
   from Technology Context (2.3).

**If the Epic uses standard delivery (no phases):**

Collect the following for the single Delivery section:

a) **Story table**: same format as above, derived from the full Scope and
   Success Criteria.

b) **Epic complete when**: confirm or refine the statement set in Step 1.

c) **Sequence diagrams**: same format as above.

---

## Phase 3: Draft review

**Re-run.** If no Step 2 placeholder is left in the description (the Epic was
already refined), do not rebuild it. Show the user the existing Step 2 sections,
ask which to change, edit only those, leave every story row that has an Id
untouched, and skip check 6 below. Everything else in this phase is for a first
run.

Assemble the complete updated Epic description:

1. Start from the existing description body fetched in Phase 1.
2. Replace every Step 2 placeholder with the content gathered in Phase 2. The
   placeholders, exactly as the `epic` templates write them, are:
   Jira may re-escape these when it returns the page as markdown (extra
   backslashes, changed spacing in table cells), so match each one by its words,
   ignoring case, underscores, backslashes and spacing, and replace the whole
   enclosing line or table row.
   - `_(To be completed in Step 2 - Detailed Requirements.)_` under
     Non-Functional Requirements, Personas and Technology Context
   - `**Personas primarily served:** _(To be completed in Step 2.)_` and
     `**Key technical constraints for this phase:** _(To be completed in Step 2.)_`
     in each phase
   - the whole table row `| | | _(Story table to be completed in Step 2.)_ | |`
     in each story table (the row has an empty cell on each side of the
     placeholder, whatever the column count): replace the entire row with the
     generated rows
   - `**Phase N is complete when:** _(To be completed in Step 2.)_` in each
     phase (in standard delivery `epic` already wrote the Epic-complete-when
     statement: confirm or refine it, nothing to replace), and the
     sequence-diagram placeholder `_(To be completed in Step 2.)_` in each phase
     or in Delivery
3. Bring the rest of the Epic up to date: if the "User Interface Mockups"
   section still holds only its placeholder (the italic line that says to run
   the ui-mockups skill, matched by its words as above), replace that with `_No mockups were produced for this Epic._`;
   rewrite the "Summary of Gaps" section so it lists only gaps still open after
   this session.
4. Replace the maturity state line, whichever entry state it holds
   (`**Epic Maturity State:** High Level Requirements Created` or
   `**Epic Maturity State:** UI Mockups Created`), with
   `**Epic Maturity State:** Detailed Level Requirements Created`. On a re-run
   from "Detailed Level Requirements Created", "Story Creation In Progress" or
   "All Stories Created", leave the state line exactly as it is: the state only
   moves forward.
5. Preserve all other Step 1 content exactly: do not rephrase or restructure
   it, and leave a User Interface Mockups section with real content untouched.
6. Check: search the assembled text, ignoring case, for `to be completed in
   Step 2`. None may remain.

Present the full updated description to the user and say:

> "Here is the complete updated Epic. Please review it and confirm before
> I write it to Jira."

Wait for explicit confirmation. Apply any amendments and re-present the
affected sections before proceeding.

---

## Phase 4: Write to Jira

Execute the following actions in order after confirmation.

**Action 1: Update the Epic in one write**

Re-fetch the Epic with `mcp__atlassian__getJiraIssue` right before writing. If
its description differs from the one you assembled from in Phase 1, show the
user what changed, re-apply your edits to the fresh copy, and confirm again.

Then make a single `mcp__atlassian__editJiraIssue` call with:
- `cloudId`: `<cloud_id>` from the cloud ID section above
- `issueIdOrKey`: the Epic key
- `contentFormat`: `markdown`
- `fields`:
  ```json
  {
    "description": "<full updated description body>"
  }
  ```
  Send no `labels` field: this skill never changes labels.

**Action 2: Post raw Q&A as a comment**

Use `mcp__atlassian__addCommentToJiraIssue` to post a comment containing
the complete raw user answers from Phase 2, presented as a labelled list
of questions and answers. Open with:

```
**Detailed Requirements Session Input - Step 2**
```

Format: `contentFormat: markdown`.

**Action 3: Confirm to the user**

> "Epic [EPIC-KEY] has been updated with Detailed Requirements and is ready
> for Step 3 (Story Generation). Run /pm:story [EPIC-KEY] from the product repo.
> <browse_url>[EPIC-KEY]"

---

## Error handling

- If the Epic cannot be fetched, stop and report the error. Do not proceed.
- If the Epic maturity state is neither "High Level Requirements Created" nor
  "UI Mockups Created", warn the user and ask whether to proceed anyway. If it
  is already "Detailed Level Requirements Created" or later, this is a re-run:
  never overwrite a story row that has an Id, and never move the maturity back.
- If a requirements document cannot be fetched, note it and continue.
- If the Epic write fails, show the full error and ask to retry or abort. The
  whole description goes in one call, so the Epic is never left half-updated.
  If only the comment fails, report it and give the user the raw Q&A to post.

---

## Completion checklist

- [ ] Epic fetched and Step 1 content extracted
- [ ] Codebase scanned; every code claim backed by a file you read, with `file:line`
- [ ] Additional documents read if provided
- [ ] NFRs captured with testable thresholds, as a table
- [ ] Personas table complete
- [ ] Technology Context complete across all seven fields
- [ ] Per-phase: personas, constraints, story table (unique names, no effort
      column), completion statement, sequence diagrams (or equivalent for
      standard delivery)
- [ ] No Step 2 placeholder left; mockups placeholder and Summary of Gaps updated
- [ ] Full updated description reviewed and confirmed by user
- [ ] Epic re-fetched, then the description (with the state line) written in one call
- [ ] Raw Q&A posted as Jira comment
