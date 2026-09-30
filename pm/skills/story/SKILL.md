---
name: story
description: >
  Creates one Jira Story per run from an Epic's story table, as a child of that
  Epic, filling every Story section from the Epic content and from code it has
  read, then updates the Epic's story table and maturity. Step 3 of the Epic
  pipeline, after `epic` and `epic-refine`. Use `story-from-document` instead
  for a one-off Story with no parent Epic or story table. Triggers: "create
  story", "next story", "generate stories", "epic step 3", or an Epic key
  argument.
when_to_use: >
  Only after `epic-refine` has completed the Epic: maturity "Detailed Level
  Requirements Created", or "Story Creation In Progress" while working through
  the table. Not for an Epic that has not been refined, because the story
  content would be incomplete. One Story per invocation; run it repeatedly.
allowed-tools: [Read, Write, Glob, Grep, Agent, mcp__atlassian__getAccessibleAtlassianResources, mcp__atlassian__getJiraIssue, mcp__atlassian__createJiraIssue, mcp__atlassian__getJiraProjectIssueTypesMetadata, mcp__atlassian__getJiraIssueTypeMetaWithFields, mcp__atlassian__searchJiraIssuesUsingJql, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, "Bash(sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh *)"]
model: sonnet
effort: high
disable-model-invocation: true
argument-hint: "<EPIC-KEY e.g. PROJ-1260>"
arguments: epic-key
---

Generate one Jira Story from the Epic's story table, derive all story content
from the Epic and codebase, present for review, create in Jira, and update the
Epic story table and maturity state.

**Before starting, confirm this is the right skill.** `story` is Step 3 of the
Epic pipeline and works from an existing Epic's story table. If
there is no parent Epic and you need a one-off Story built and verified from a
source document (a Confluence page, a local document, or a written brief), use
the `story-from-document` skill instead.

## Configuration

!`sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh '${user_config.site}' '${user_config.points_scale}'`

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

  > "The Atlassian MCP is not active in this session. This skill needs it to read and update the Jira Epic and create the Story.
  > Ask whoever manages your Claude Code setup to enable the official Atlassian MCP
  > server, registered as `atlassian`."

## Jira connection

- **Cloud ID:** `<cloud_id>` resolved above
- **Browse URL:** `<browse_url>` resolved above

## Content rules

Apply to all generated content without exception:

1. No em dashes. Rewrite any sentence that would need one.
2. No LLM-signal phrasing. Plain, professional language. Active voice.
3. Every bullet point and AC is a complete grammatical sentence.
4. Story points use the `points_scale` from the Resolved configuration
   (default: 1, 2, 3, 5, 8, 13).
5. Sub-task effort estimates, when sub-tasks apply, are in days for a mid-level
   developer, to one decimal place. The Epic story table has no effort column,
   so never invent a Story-level effort.
6. ACs must be testable and independently verifiable by a non-engineer.
7. NFR ACs must state the specific threshold inline (not "see Epic NFR").
8. Every story ends its Acceptance Criteria with the regression AC defined in
   [`templates/story-sections.md`](templates/story-sections.md), filled in for
   this story.
9. The story must be self-contained. Copy these Epic items verbatim, never
   paraphrased, summarised or linked: the phase goal, the phase's technical
   constraints, the NFR thresholds that apply, the phase's sequence diagram(s),
   and the slice of Technology Context the story touches. Derive everything
   else from them and from code you have read.
10. Every claim about existing code carries `path/to/file.py:120` evidence from
    a file you have read in this session. Never invent a path, endpoint or
    schema: mark it `[GAP: ...]` instead.

## Phase 1: Load context

Execute all three steps before presenting anything to the user.

**1.1 Fetch the Epic.** Take the Epic key from the `epic-key` argument; ask for
it if it was not given. Use `mcp__atlassian__getJiraIssue` with
`responseContentFormat: markdown`. Extract and hold:
- Epic summary and key, and its current labels (Phase 5 rewrites them)
- All story table rows for every phase (or the single Delivery table for
  standard Epics): Id, Story, Summary, Status, Story Points
- Delivery structure (phased or standard)
- Personas table and NFRs
- Technology Context (full)
- Per-phase sequence diagrams, phase goals, and technical constraints
- Epic maturity state: the `**Epic Maturity State:**` line, or the
  `epic-maturity-*` label if the line is missing. If they disagree, tell the
  user and ask which to trust. State line and label pairs: High Level Requirements Created (`epic-maturity-hlr-created`), UI Mockups Created (`epic-maturity-mockups-created`), Detailed Level Requirements Created (`epic-maturity-detailed-created`), Story Creation In Progress (`epic-maturity-stories-in-progress`), All Stories Created (`epic-maturity-all-stories-created`).

**1.2 Check maturity.**
- "Detailed Level Requirements Created" (first Story) or "Story Creation In
  Progress" (a later Story): proceed.
- "All Stories Created": stop and tell the user there is nothing left to do.
- Any other state: warn that the Epic has not been refined, and ask whether to
  proceed anyway.

**1.3 Identify uncreated stories.** A story is uncreated if its Id column is
empty. Ignore rows that still hold placeholder text such as "to be completed in
Step 2": if only placeholder rows exist, stop and tell the user to run
`/pm:epic-refine` first. Story names must be unique, because Phase 5 matches the
table row by name: if two rows share a name, stop and ask the user to rename one
in the Epic. If every story already has an Id, stop and confirm the Epic is
complete. Build the list of uncreated stories across all phases.

---

## Phase 2: Select story

Present the list of uncreated stories to the user, grouped by phase if phased,
with their story points. Ask which story to generate.

If `epic-key` was provided as an argument but no story was specified, default
to the first uncreated story in Phase 1. State which story you are defaulting
to and ask the user to confirm or select a different one.

---

## Phase 3: Ground and generate the story

**3.1 Find the code.** Only now, with one story selected, look at the code. If
the current directory does not look like the product repo for this Epic, ask the
user for its path first. Dispatch the `Explore` sub-agent via the `Agent` tool to
locate candidate files, not to summarise:

> "Read-only. For the story below, list the files, modules, routes, data models
> and frontend components in this repository it will touch or extend, as paths
> with one line each. Do not modify anything.
>
> Story: [name and summary from the Epic table]
> Technology Context: [the slice relevant to this story]"

If sub-agents are not available, use `Grep`, `Glob` and `Read` directly.

**3.2 Verify the code.** `Read` every file you will cite. For each item in the
Implementation Specification and Technical Notes (route, model, component,
configuration), record `path/to/file.py:120` for the existing code it extends,
and say plainly what is new. Anything you cannot find or confirm becomes
`[GAP: ...]`.

**3.3 Generate.** Use the section definitions in
[`templates/story-sections.md`](templates/story-sections.md) to produce each
section in order: User Story, Context, Requirements, Implementation
Specification, Acceptance Criteria, Test Requirements, Technical Notes,
Sub-tasks, Other Information, and Gaps. Derive from the Epic and the verified
code; do not interrupt the user while drafting. Decisions that belong to the
user are not derived silently: the persona, any API or data-model design choice,
and the sub-task split. Put each into the Phase 4 review as an explicit choice,
with your recommendation.

List every `[GAP: ...]` at the end of the draft under a "Gaps" heading.

---

## Phase 4: Draft review

Present the complete story draft and the list of choices to the user. Say:

> "Here is the draft for [Story Name]. Please review it, decide the choices
> listed, and confirm or amend before I create it in Jira. Any [GAP: ...] items
> need your input before I can proceed."

Wait for explicit confirmation. Resolve all gaps and choices before proceeding.
Apply amendments and re-present the affected sections.

---

## Phase 5: Create in Jira

Execute the following actions in order after confirmation.

**Duplicate check.** Call `mcp__atlassian__searchJiraIssuesUsingJql` with
`jql: parent = <EPIC-KEY> ORDER BY created DESC` and `maxResults: 100`, and
compare each child's summary with this story's name exactly (ignoring case and
surrounding spaces); do not search by text, which matches loosely. If one
matches, show it and ask whether it is this same Story from an earlier,
interrupted run. If yes, skip Action 1 and continue with Action 2 using that
key; in Action 3, create only the sub-tasks it does not already have (list its
children with `parent = <STORY-KEY>` first). If no, continue normally.

**Action 1: Create the Jira Story**

**Resolve the issue types and the story points field first.** Call
`mcp__atlassian__getJiraProjectIssueTypesMetadata` for the target project and record
the exact names and ids of the Story type and the sub-task type (the type the response
flags as a sub-task; commonly `Sub-task` or `Subtask`). If the project has no
Story type, use its closest equivalent (for example Task) and tell the user. Then call
`mcp__atlassian__getJiraIssueTypeMetaWithFields` with the Story type's id and
`requiredFieldsOnly: false` (story points is optional, so the default would omit it) and
find this instance's story points field. Do not assume `customfield_10016`: it is not
universal and will fail in some Jira configurations. If you cannot identify the field, or
the set later fails, leave the points unset, report it, and tell the user to set the
points manually rather than surfacing a raw API error.

Use `mcp__atlassian__createJiraIssue`:
- `cloudId`: `<cloud_id>` from the cloud ID section above
- `projectKey`: same project as the Epic (parse from Epic key)
- `issueTypeName`: the Story type name resolved above
- `summary`: the story name from the Epic table
- `description`: the full confirmed story body
- `contentFormat`: `markdown`
- `parent`: the Epic key
- `additional_fields`:
  ```json
  {
    "<resolved story points field>": <story_points_number>
  }
  ```

**Action 2: Update the Epic in one write**

Re-fetch the Epic right before writing, because the description was read before
a long session and may have changed. Decide the new state: if every story table
row now has an Id, the state is "All Stories Created" with label
`epic-maturity-all-stories-created`; otherwise "Story Creation In Progress" with
label `epic-maturity-stories-in-progress`.

Make a single `mcp__atlassian__editJiraIssue` call with `contentFormat: markdown`
and these `fields`:

```json
{
  "description": "<the fresh description with this story's row updated and the state line replaced>",
  "labels": ["<every existing label except epic-maturity-*>", "<the new maturity label>"]
}
```

In the table row, set the Id column to a Jira link to the new story,
`[PROJECT-XXXX](<browse_url>PROJECT-XXXX)`, and the Status column to `Created`.
Replace the state line with `**Epic Maturity State:** <state>`. Change nothing
else in the description.

**Action 3: Create sub-tasks (if applicable)**

If the story has sub-tasks, create each one using `mcp__atlassian__createJiraIssue`
(when resuming, only those the Story does not already have):
- `cloudId`: `<cloud_id>` from the cloud ID section above
- `issueTypeName`: the sub-task type name resolved above
- `parent`: the newly created Story key
- `summary`: the sub-task name
- `description`: the sub-task description from the story
- `contentFormat`: `markdown`

**Action 4: Confirm to the user**

> "Story [KEY] has been created.
> <browse_url>[KEY]
>
> Epic [EPIC-KEY] updated: [N] of [TOTAL] stories created.
> [All stories created / X stories remaining.]
>
> Run /pm:story [EPIC-KEY] from the product repo to generate the next story."

---

## Error handling

- If the Jira Story create call fails, stop and show the error. Do not
  attempt the Epic update.
- If the Epic update fails after the story was created, report the story key
  and tell the user to set the Id and Status in the story table, the state line
  and the maturity label by hand. The duplicate check will recognise the Story
  on the next run.
- If a sub-task create call fails, report which sub-task failed and continue
  with the remaining ones rather than aborting.
- If the Epic description no longer has a row matching this story's name,
  stop before writing and ask the user how to proceed.

---

## Completion checklist

- [ ] Atlassian MCP available and `<cloud_id>` resolved
- [ ] Epic fetched, story table parsed, maturity checked
- [ ] Uncreated stories identified, names unique
- [ ] Story selected and confirmed by user
- [ ] Code for the selected story located and every cited file read
- [ ] All story sections derived from the Epic and verified code, with `file:line` evidence
- [ ] Gaps and judgment-call choices put to the user (no guessing)
- [ ] Draft reviewed and all gaps resolved
- [ ] Duplicate check run; Jira Story created as a child of the Epic
- [ ] Epic updated in one write: story row, state line and labels
- [ ] Sub-tasks created if applicable
- [ ] User confirmed with story key, link, and remaining count
