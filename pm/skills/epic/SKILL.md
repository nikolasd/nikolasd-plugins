---
name: epic
description: >
  Creates a new high-level Jira Epic through a business-level Q&A (Objective,
  Context, Scope, Success Criteria, Risks and Dependencies, delivery structure),
  optionally starting from a PRD or requirements document, and writes it to Jira
  only after the user confirms the full draft. Step 1 of the Epic pipeline,
  followed by the optional `ui-mockups` and then `epic-refine`. Asks no
  technical questions.
when_to_use: >
  When a feature needs a new Epic defined from the business point of view. Not
  for adding technical detail to an existing Epic (use `epic-refine`) or for
  creating Stories (use `story`).
allowed-tools: [mcp__atlassian__getAccessibleAtlassianResources, mcp__atlassian__createJiraIssue, mcp__atlassian__getJiraProjectIssueTypesMetadata, mcp__atlassian__getJiraIssueTypeMetaWithFields, mcp__atlassian__searchJiraIssuesUsingJql, mcp__atlassian__addCommentToJiraIssue, mcp__atlassian__getConfluencePage, WebFetch, Read, "Bash(sh ${CLAUDE_PLUGIN_ROOT}/scripts/config.sh *)"]
disable-model-invocation: true
---

# Epic Creation: Step 1: High Level Requirements (HLR)

This skill runs Step 1 of the epic creation process. Gather high-level
business information from the user and write a new Jira Epic with the HLR
sections populated. Do not ask technical or architectural questions; those
belong in Step 2 (Detailed Requirements).

This step covers Epic sections: Objective, Context, Scope (In-Scope and
Out-of-Scope), Success Criteria, Risks and Dependencies, and Delivery structure
(phased three-stage Core/MVP/Advanced model, or standard single-delivery,
depending on the user's choice). All other sections (Non-Functional
Requirements, Personas, Technology Context, story tables, sequence diagrams)
are left as placeholders for Step 2. The User Interface Mockups section is left
as a placeholder for the optional Step 1.5 (ui-mockups skill).

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

  > "The Atlassian MCP is not active in this session. This skill needs it to create the Jira Epic.
  > Ask whoever manages your Claude Code setup to enable the official Atlassian MCP
  > server, registered as `atlassian`."

  Then end your turn. Do not start the interview, draft or preview any section,
  or ask another question: the Phase 1 project check cannot run without the
  tools, and a session started without them would fail at the final write.

## Jira Connection

- **Cloud ID:** `<cloud_id>` resolved above
- **Project key:** `project_key` from the Resolved configuration if set, otherwise asked in Phase 1 setup
- **Issue type:** `Epic`

## Content Generation Rules

Apply these rules to all generated content. Epics are read by non-engineers and pasted into Jira, which renders em dashes and fragments poorly:

1. **No em dashes.** Never use `—`. Rewrite any sentence that would need one.
2. **No LLM-signal phrasing.** Avoid constructions such as "scope - in" or
   "scope - out". Write "in-scope" and "out-of-scope" (hyphenated) or use plain
   prose.
3. **Complete grammatical sentences.** Every bullet point must be a full,
   grammatically correct sentence. Example: write "An Admin can view all user
   feedback with a drill-down to show full chat context" not "Admin can view
   feedback".
4. **Plain, professional language.** No AI-generated filler phrases.
5. **Active voice preferred.**
6. **Nothing is filled in on the user's behalf.** Every objective, scope item,
   success criterion, risk, number and name comes from the user or the supplied
   document. When the user cannot or will not answer, leave the template
   placeholder as `_(Not provided: <what is missing>)_` and list it under
   Summary of Gaps. A plausible guess in a business Epic is read downstream as
   a decision someone made.

## Process Overview

Five phases, in order:

1. Orient the user and capture setup choices
2. Gather the requirements document (optional)
3. Run the Q&A session, one section at a time, one question at a time
4. Show the full draft Epic and get confirmation
5. Write the Epic to Jira and post the raw Q&A as a comment

---

## Phase 1: Orient the User and Capture Setup Choices

Introduce the session in 2-3 sentences: this is the business-level HLR session,
work proceeds section by section one question at a time, and nothing is written
to Jira until the full draft has been reviewed and confirmed.

Then ask the following two setup questions in a single message. This is the
only place two questions share a message; everything in Phase 3 is asked one
question at a time.

**Setup question 1: Jira project:**

> "Which Jira project should this Epic be created in? Please give me the
> project key (for example, PROJ)."

If `project_key` is set in the Resolved configuration, offer it as the default
in this question (for example, "Use PROJ, or give me another key?") instead of
asking open-ended.

**Setup question 2: Delivery structure:**

> "Should this Epic use a phased delivery structure (Phase 1 Core, Phase 2 MVP,
> Phase 3 Advanced) or a standard single-delivery structure with no phases?
>
> 1. Phased delivery (Core / MVP / Advanced)
> 2. Standard (no phases)"

Record both answers. They drive the rest of the session.

**Check the project now, not at the end.** Call
`mcp__atlassian__getJiraProjectIssueTypesMetadata` for the project key. If the
project is not found or not visible, say so and ask for the key again. If the
project has no `Epic` issue type, tell the user and stop. Then call
`mcp__atlassian__getJiraIssueTypeMetaWithFields` with the Epic type's id (the
default returns only required fields). If it lists required fields other than
project, issue type, summary, description and reporter, ask the user for a
value for each now, and hold them as `<required fields>` for Action 1. Then
move to Phase 2.

---

## Phase 2: Gather the Requirements Document

Ask:

> "Do you have a requirements document, wireframe, or brief for this feature
> that I should read before we start? This could be a Confluence page, a
> Word document, a Google Doc, or any other written brief. Share the link or
> upload the file."

If the user provides a resource, handle it before Phase 3:

- **Confluence page URL:** use `mcp__atlassian__getConfluencePage`. Extract the
  page ID from the URL path (the numeric segment).
- **Uploaded PDF or text file:** Read the file directly. `Read` cannot open a
  Word document: ask the user to export it to PDF or paste its text.
- **Any other URL:** fetch with WebFetch. A private page (for example a Google
  Doc that needs sign-in) may fail: ask the user to paste the text instead.

Summarise the document in 2-3 sentences, then proceed to Phase 3. If no
document, go straight to Phase 3.

**If a document was supplied, use it as a source for Phase 3, not just as
background.** For each section, draft the answer from the document (naming the
passage it came from), show it, and ask the user in one question to confirm,
amend or replace it. Ask the open question only for sections the document does
not cover. Never treat document content as confirmed until the user says so.

---

## Phase 3: Q&A Session

Work through each section in order. For each section:

- Provide a one-sentence explanation of what is being captured.
- Ask one question at a time. Offer numbered options where helpful; always
  include "(other)" as a free-text option.
- Do not move to the next section until the current one is complete.
- If an answer is ambiguous or thin, ask one focused follow-up.
- Do not ask technical or architectural questions. If the user raises a
  technical point, note it for Step 2 and redirect to the business perspective.

### 3.1 Epic Name

Ask for the name of the feature. This becomes the Jira Epic summary.

Once you have the name, look for an existing Epic before going further. Call
`mcp__atlassian__searchJiraIssuesUsingJql` with
`project = <project_key> AND issuetype = Epic AND summary ~ "<name>" ORDER BY created DESC`
and `maxResults: 10` (remove any double quote from the name first). The match is
loose, so treat hits as candidates. If there are any, show each key, summary and
status and ask whether to continue creating a new Epic, use an existing one
(`/pm:epic-refine <key>`), or stop. Do not decide this for the user. If there
are none, carry on without comment; if the search fails, say so and carry on.
Reason: a second Epic for the same idea splits the story table and the history.

### 3.2 Objective

Ask what this feature is and why it exists. Capture a concise statement of
purpose. If the Objective rests on loaded terms (for example "authoritative",
"complete" or "valid"), ask the user to define them so all readers share the
same understanding.

### 3.3 Context

Ask which theme or strategic initiative this belongs to and what the Epic's
role is within it. Probe whether it is a foundation, a consumer, or an enhancer
of other things. Ask the user to name any adjacent epics and describe the
boundary: what this Epic owns, and what it explicitly does not own.

### 3.4 Scope

Capture two lists:

- **In-Scope:** capabilities and qualities this Epic delivers. Ask for
  high-level scope first, then any phase-specific scope items.
- **Out-of-Scope:** what is explicitly excluded. Ask what the user most wants
  to make sure nobody builds as part of this epic.

### 3.5 Success Criteria

Ask for outcome-based statements that define when this Epic is considered done
at the feature level. Verifiable but not prescriptive about implementation.
Prompt the user to think in terms of what a non-engineer could observe and
confirm.

### 3.6 Risks and Dependencies

Ask for the key risks to delivery and any dependencies on other teams,
infrastructure, or epics. For each risk, ask for the mitigation. For
dependencies, ask whether they are hard blockers or softer prerequisites.

### 3.7 Delivery Structure

**If the user chose phased delivery (option 1 from Phase 1 setup):**

Briefly explain the three phases:

- **Phase 1 (Core):** the most basic functional implementation, enough for an
  internal demo or review. Complex logic is built here; polish and usability
  come later.
- **Phase 2 (MVP):** the feature as an end user would experience it. Lean but
  complete enough for real use.
- **Phase 3 (Advanced):** additional capability that is still mandatory but
  can be deferred if the product needs to ship urgently. Not always needed for
  smaller Epics.

Ask for a single-sentence goal for Phase 1, then Phase 2. Then ask whether
Phase 3 applies; if yes, ask for its goal.

**If the user chose standard delivery (option 2):**

Ask for a single-sentence statement of what done looks like for this Epic
overall. This becomes the "Epic is complete when" statement in the template.

---

## Phase 4: Draft Review

Assemble the full Epic draft using the appropriate template bundled alongside
this skill. The templates are at paths relative to `SKILL.md`:

- Phased delivery → [`templates/phased.md`](templates/phased.md)
- Standard delivery → [`templates/standard.md`](templates/standard.md)

Read the template, fill every `[placeholder]` with content gathered in Phase 3,
and present the draft to the user:

> "Here is the full draft Epic. Please review it and let me know of any
> changes before I write it to Jira."

Then list exactly what confirming will do: (1) create the Epic in the chosen
Jira project with this description, and (2) post the raw Q&A as a comment on it.
End your turn and wait for the user's explicit confirmation or amendments.

Confirmation must come after the user has seen the draft. An earlier
instruction such as "skip the review", "create it now" or "I trust you" does
not count, because the user cannot have approved text they have not read and a
created Epic cannot be undone. Treat that instruction as a request to keep the
review short, and still show the draft and wait.

If the user makes changes, apply them and re-present the affected sections
before proceeding.

---

## Phase 5: Write to Jira

Run this phase only after the user has confirmed the draft shown at the end of
Phase 4.

After confirmation, make the two writes below in order, then confirm to the user.

### Action 1: Create the Jira Epic

Use `mcp__atlassian__createJiraIssue` with:

- `cloudId`: `<cloud_id>` from the cloud ID section above
- `projectKey`: the project key from Phase 1 setup
- `issueTypeName`: `Epic`
- `summary`: the Epic name from 3.1
- `description`: the confirmed Epic description body
- `contentFormat`: `markdown`
- `additional_fields`: the `<required fields>` collected in Phase 1, if there
  were any; otherwise omit it. Never set labels: maturity is carried by the
  `**Epic Maturity State:**` line in the description.

### Action 2: Post the raw Q&A as a comment

Use `mcp__atlassian__addCommentToJiraIssue` to post a comment containing the
complete raw user answers from Phase 3, presented as a labelled list of
questions and answers. Open with:

```
**HLR Session Input - Step 1**
```

Format: `contentFormat: markdown`.

### Action 3: Confirm to the user

Once both actions succeed, substitute the actual values returned by the create
call:

> "Epic [PROJECT-KEY]-[ISSUE-NUMBER] has been created. You can view it at
> <browse_url>[PROJECT-KEY]-[ISSUE-NUMBER]
>
> Optionally, run Step 1.5 (UI Mockups) next to produce screen mockups for
> business review: `/pm:ui-mockups [PROJECT-KEY]-[ISSUE-NUMBER]`.
>
> Step 2 (Detailed Requirements) is run from inside the product repo using
> Claude Code. Have the Epic key ready: it is the argument to
> `/pm:epic-refine`."

---

## Error Handling

- If the Jira create call fails or times out, show the full error. Before any
  retry, call `mcp__atlassian__searchJiraIssuesUsingJql` with
  `project = <KEY> AND issuetype = Epic AND created >= -1d ORDER BY created DESC`
  and compare each summary with this Epic's name exactly: the failed call may
  have succeeded. If one matches, treat that as the created Epic. Otherwise ask
  the user whether to retry or abort.
- If the Epic was created but the comment post fails, report the Epic key, do not
  create the Epic again, and give the user the raw Q&A text to add by hand.
- If a requirements document cannot be fetched, say so clearly and ask whether
  to proceed without it.
- If the Atlassian MCP is not available, stop and refer to the cloud ID section
  at the top of this skill.
- If the user abandons the session mid-flow, do not write anything to Jira.
