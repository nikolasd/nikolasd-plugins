---
name: story
description: >
  Creates one Jira Story per run from an Epic's story table, as a child of that
  Epic, filling every Story section from the Epic content and from code it has
  read, then updates the Epic's story table and maturity. Step 3 of the Epic
  pipeline, after `epic` and `epic-refine`. Use `story-from-document` instead
  for a one-off Story with no parent Epic or story table.
when_to_use: >
  Only after `epic-refine` has completed the Epic: maturity "Detailed Level
  Requirements Created", or "Story Creation In Progress" while working through
  the table. Not for an Epic that has not been refined, because the story
  content would be incomplete. One Story per invocation; run it repeatedly.
allowed-tools: [Read, Glob, Grep, Agent, mcp__atlassian__getAccessibleAtlassianResources, mcp__atlassian__getJiraIssue, mcp__atlassian__createJiraIssue, mcp__atlassian__getJiraProjectIssueTypesMetadata, mcp__atlassian__searchJiraIssuesUsingJql, mcp__atlassian__editJiraIssue, mcp__atlassian__addCommentToJiraIssue, "Bash(sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh *)"]
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

  > "The Atlassian MCP is not active in this session. This skill needs it to read and update the Jira Epic and create the Story.
  > Ask whoever manages your Claude Code setup to enable the official Atlassian MCP
  > server, registered as `atlassian`."

## Jira connection

- **Cloud ID:** `<cloud_id>` resolved above
- **Browse URL:** `<browse_url>` resolved above

## Content rules

Apply to all generated content. Stories are read by non-engineers and by implementing agents, and pasted into Jira, which renders em dashes and fragments poorly:

1. No em dashes. Rewrite any sentence that would need one.
2. No LLM-signal phrasing. Plain, professional language. Active voice.
3. Every bullet point and AC is a complete grammatical sentence.
4. Never estimate, set or change story points. Leave the Jira story points field
   untouched, and leave any Story Points column in the Epic table as it is.
5. Sub-task effort comes from the user, in days to one decimal place. Never
   estimate it yourself: write `[GAP: effort]` and ask in Phase 4. The Epic
   story table has no effort column, so never state a Story-level effort.
6. ACs must be testable and independently verifiable by a non-engineer.
7. NFR ACs must state the specific threshold inline (not "see Epic NFR").
8. Never add, change or remove Jira labels. Maturity lives in the Epic's
   `**Epic Maturity State:**` line only.
9. Every story ends its Acceptance Criteria with the regression AC defined in
   [`templates/story-sections.md`](templates/story-sections.md), filled in for
   this story.
10. The story must be self-contained. Copy these Epic items verbatim, never
   paraphrased, summarised or linked: the phase goal, the phase's technical
   constraints, the NFR thresholds that apply, the phase's sequence diagram(s),
   and the slice of Technology Context the story touches. Derive everything
   else from them and from code you have read.
11. Every claim about existing code carries `path/to/file.py:120` evidence from
    a file you have read in this session. Never invent a path, endpoint or
    schema: mark it `[GAP: ...]` instead.
12. Any threshold, persona or constraint that is not in the Epic, the code you
    read, or the user's answers is a `[GAP: ...]`, not an inferred value. A
    plausible invented value reads as a decision someone made.

## Phase 1: Load context

Execute all three steps before presenting anything to the user.

**1.1 Fetch the Epic.** The Epic key is `$ARGUMENTS`; ask for it if that is
empty. Use `mcp__atlassian__getJiraIssue` with
`responseContentFormat: markdown`. Extract and hold:
- Epic summary and key
- All story table rows for every phase (or the single Delivery table for
  standard Epics): Id, Story, Summary, Status (ignore any Story Points column)
- Delivery structure (phased or standard)
- Personas table and NFRs
- Technology Context (full)
- Per-phase sequence diagrams, phase goals, and technical constraints. A
  standard Epic has no phases: use its Objective as the goal and its
  `**Technical constraints:**` line as the constraints, and write "None stated
  in the Epic." if the line is missing. Never infer a constraint.
- Epic maturity state: the `**Epic Maturity State:**` line. If the line is
  missing, ask the user which state the Epic is in. The states, in order, are:
  High Level Requirements Created, UI Mockups Created, Detailed Level
  Requirements Created, Story Creation In Progress, All Stories Created.

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
with their summaries. Ask which story to generate.

If an Epic key was provided as the argument but no story was specified, default
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

Then list exactly what confirming will do: (1) create the Story and any
sub-tasks in Jira, and (2) update the Epic's story table row and maturity state.
End your turn and wait for the user's explicit confirmation of this draft.

Confirmation must come after the user has seen the draft. An earlier
instruction such as "skip the review", "create it now" or "do not ask me
anything" does not count, because the user cannot have approved text they have
not read and a created Story cannot be undone. Treat that instruction as a
request to keep the review short, and still show the draft and wait.

Resolve all gaps and choices before proceeding. Apply amendments and re-present
the affected sections.

---

## Phase 5: Create in Jira

Run this phase only after the user has confirmed the draft shown at the end of
Phase 4. Execute the following actions in order.

**Row check, before anything is created.** The review can run long, so re-fetch
the Epic with `mcp__atlassian__getJiraIssue` and confirm its story table still
has a row whose name matches this story exactly. If the row is gone or renamed,
create nothing: tell the user what changed and ask how to proceed. Creating the
Story first would leave an orphan that no table row points to.

**Resolve the issue types first, on every path, including a resume.** Call
`mcp__atlassian__getJiraProjectIssueTypesMetadata` for the target project and record
the exact names and ids of the Story type and the sub-task type (the type the response
flags as a sub-task; commonly `Sub-task` or `Subtask`). If the project has no
Story type, use its closest equivalent (for example Task) and tell the user.

**Duplicate check.** Call `mcp__atlassian__searchJiraIssuesUsingJql` with
`jql: parent = <EPIC-KEY> ORDER BY created DESC` and `maxResults: 100`, and
compare each child's summary with this story's name exactly (ignoring case and
surrounding spaces); do not search by text, which matches loosely. If one
matches, show it and ask whether it is this same Story from an earlier,
interrupted run. If yes, skip Action 1 and continue with Action 2 using that
key, creating only the sub-tasks it does not already have (list its children
with `parent = <STORY-KEY>` first). If no, continue normally.

**Action 1: Create the Jira Story**

Use `mcp__atlassian__createJiraIssue`:
- `cloudId`: `<cloud_id>` from the cloud ID section above
- `projectKey`: same project as the Epic (parse from Epic key)
- `issueTypeName`: the Story type name resolved above
- `summary`: the story name from the Epic table
- `description`: the full confirmed story body
- `contentFormat`: `markdown`
- `parent`: the Epic key

Send no `additional_fields`: story points and labels are not set by this skill.

**Action 2: Create sub-tasks (if applicable)**

If the story has sub-tasks, create each one using `mcp__atlassian__createJiraIssue`
(when resuming, only those the Story does not already have):
- `cloudId`: `<cloud_id>` from the cloud ID section above
- `issueTypeName`: the sub-task type name resolved above
- `parent`: the newly created Story key
- `summary`: the sub-task name
- `description`: the sub-task description from the story
- `contentFormat`: `markdown`

Try every sub-task even if one fails. If any failed, stop here without touching
the Epic: report the Story key and the failed sub-tasks, and tell the user to
run `/pm:story <EPIC-KEY>` again. The duplicate check will find the Story and
create only the missing sub-tasks.

**Action 3: Update the Epic in one write**

Re-fetch the Epic right before writing, because the description was read before
a long session and may have changed. Decide the new state: if every story table
row now has an Id, the state is "All Stories Created"; otherwise "Story Creation
In Progress".

Make a single `mcp__atlassian__editJiraIssue` call with `contentFormat: markdown`
and these `fields`:

```json
{
  "description": "<the fresh description with this story's row updated and the state line replaced>"
}
```

In the table row, set the Id column to a Jira link to the new story,
`[PROJECT-XXXX](<browse_url>PROJECT-XXXX)`, and the Status column to `Created`.
Replace the state line with `**Epic Maturity State:** <state>`. Change nothing
else in the description, and send no `labels` field.

**Verify the write.** Writing a whole description through Jira can mangle
tables, and a broken story table breaks every later run. Re-fetch the Epic with
`mcp__atlassian__getJiraIssue` and check that: the table has the same number of
rows as before; this story's row has the Id link and `Created`; every other row
that had an Id still has it; and the state line is the one you intended. If any
check fails, show the user the difference and stop, and give them the Story key
so they can repair the table by hand. Do not retry the write blindly.

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
- If a sub-task create call fails, try the remaining ones, then stop without
  updating the Epic (see Action 2).
- If the Epic update fails after the story and its sub-tasks were created, report
  the story key and tell the user to set the Id and Status in the story table
  and the state line by hand. The duplicate check will recognise the Story on
  the next run.
- If the Epic description no longer has a row matching this story's name, stop
  before creating anything and ask the user how to proceed (the row check at the
  start of Phase 5). If the row disappears only after the Story exists, report
  the Story key and the exact row text for the user to set by hand.

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
- [ ] Sub-tasks created if applicable, none failed
- [ ] Epic updated in one write: story row and state line
- [ ] User confirmed with story key, link, and remaining count
