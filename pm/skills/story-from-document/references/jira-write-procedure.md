# Phase 5: Write to Jira

Read this only after the user has confirmed the review gate (4.4), and never
under `--dry-run`. Execute in order.

## Contents

- [5.0 Check for work already done](#50-check-for-work-already-done)
- [5.1 Resolve only what the approved plan needs](#51-resolve-only-what-the-approved-plan-needs)
- [5.2 Write the Story](#52-write-the-story)
- [5.3 Create each sub-task](#53-create-each-sub-task)
- [5.4 Create the dependency links](#54-create-the-dependency-links)
- [5.5 Confirm to the user](#55-confirm-to-the-user)
- [Error handling](#error-handling)

## 5.0 Check for work already done

An earlier run may have been interrupted after writing part of the plan.

- **Create mode:** call `mcp__atlassian__searchJiraIssuesUsingJql` with
  `jql: project = <project_key> AND created >= -2d ORDER BY created DESC` and
  `maxResults: 50`, and compare each summary with the story summary exactly
  (ignoring case and surrounding spaces); do not search by text, which matches
  loosely. If a recent issue has the same summary, show it and ask whether it is
  this Story from an interrupted run. If yes, use its key as the Story key, skip the create in 5.2, and treat
  its existing children and links as already done in 5.3 and 5.4.
- **Promote mode:** the existing sub-tasks and links were captured in the
  promote-mode read; use them the same way.

Never create a sub-task whose summary matches an existing child of the Story,
and never create a link that already exists.

## 5.1 Resolve only what the approved plan needs

This step prepares the Jira field and type information for the writes below.
Resolve only what the breakdown actually uses, and skip the rest. If the
approved plan has no sub-tasks, no dependency links, and no story points to set,
skip this step entirely.

- **Story points field:** if you are setting story points, first get the id of
  the target issue's type (the Story type in create mode, the existing issue's
  own type in promote mode) from `mcp__atlassian__getJiraProjectIssueTypesMetadata`
  for the target project, then call `mcp__atlassian__getJiraIssueTypeMetaWithFields`
  with that id and `requiredFieldsOnly: false` (story points is optional, so the
  default would omit it) and find this instance's story points field. Do not
  assume `customfield_10016`: it is not universal and will fail in some Jira
  configurations. If you cannot identify the field, or the set later fails, leave
  the points unset, report it, and tell the user to set the points manually
  rather than surfacing a raw API error. If the project has no Story type, use
  its closest equivalent (for example Task) and tell the user.
- **Issue type names and the Blocks link type:** needed only when you will create
  sub-tasks or dependency links. When the breakdown has sub-tasks, take the
  sub-task issue type name (the type the response flags as a sub-task; commonly
  `Sub-task` or `Subtask`) from that same metadata call, and use exactly that
  name below. When it has Blocks links, call `mcp__atlassian__getIssueLinkTypes`
  to confirm the Blocks type (`inward: "is blocked by"`, `outward: "blocks"`).

Make the metadata call once and reuse the result.

## 5.2 Write the Story

This step differs by mode.

**Create mode:** `mcp__atlassian__createJiraIssue` with:
- `cloudId`: `<cloud_id>`
- `projectKey`: `<project_key>` settled in Phase 2.1 (do not guess it here)
- `issueTypeName`: the Story type name from 5.1 (`Story` if 5.1 was skipped)
- `summary` and `description`: the confirmed summary and body
- `contentFormat`: `markdown`
- `parent`: `<epic_key>`, only when an Epic attachment was agreed in 4.3

Do not send the story points in this call: a rejected custom field would fail the
whole create. Capture the returned key as the Story key for the steps below, then
set the points separately (see "Story points" below).

**Promote mode:** `mcp__atlassian__editJiraIssue` on the **same** story key. This
tool takes `fields` (not `additional_fields`) and replaces the whole description.

First re-fetch the story with `mcp__atlassian__getJiraIssue`: the body you read
in the promote-mode step may be hours old. If its description differs from that
copy, show the user what changed and confirm again before overwriting.

Keep the original text: end the new body with an `## Original description`
section that holds the previous body, unless it was empty. If the current body
already ends with such a section (an earlier run enriched it), keep that section
as it is instead of adding a second one around the whole body. Send:
- `cloudId`: `<cloud_id>`
- `issueIdOrKey`: the existing story key
- `contentFormat`: `markdown`
- `fields`, including only the keys that change:
  ```json
  {
    "description": "<confirmed enriched body, ending with the Original description section>",
    "summary": "<new summary, only if it changed>",
    "parent": { "key": "<epic_key>" }
  }
  ```

Include `parent` only if an Epic attachment was agreed in 4.3 (possible only when
the story had no parent). The key stays the same: this is an update in place,
not a new issue. The Story key for the steps below is the existing key.

**Story points (both modes).** If story points are to be set, make a second,
separate `mcp__atlassian__editJiraIssue` call on the Story key with
`fields: { "<resolved story points field>": <story_points_number> }`. If it is
rejected, leave the points unset and report it (see Error handling); the Story
and its body are already written.

In both modes, attachment touches only the Story's parent link. Do not edit the
Epic: no story-table row, no maturity or label change.

## 5.3 Create each sub-task

`mcp__atlassian__createJiraIssue` with `issueTypeName` set to the sub-task type
name resolved in 5.1, `parent` set to the Story key (the new key in create mode,
the existing key in promote mode), the sub-task summary and body,
`contentFormat: markdown`. Skip any sub-task that already exists (see 5.0).
Capture every returned key. Send the sub-task create calls together where
possible.

## 5.4 Create the dependency links

For each Blocks relationship use `mcp__atlassian__createIssueLink` with
`type: Blocks`, `inwardIssue: <the blocker>`, `outwardIssue: <the blocked issue>`.
Link any external prerequisite tickets the user named, and the internal sub-task
ordering from Phase 4. Skip links that already exist.

## 5.5 Confirm to the user

Report the Story key and URL (noting that in promote mode it is the same key,
now enriched), the list of created sub-task keys, and the dependency links
created, and say which already existed and were left alone. If the Story was
attached to an Epic, name the parent Epic and state plainly that the Epic's story
table and maturity were left unchanged. Name which sub-task has no blockers and
can start first. If mockups were generated in Phase 3.5, give the PNG directory
path and list the files for the user to attach to the Story, since this skill
cannot attach images itself, or give the private Claude Design canvas link and
remind the user to share it with reviewers.

## Error handling

- If the story points field cannot be identified, or the separate points call
  rejects it, do not abort: complete the rest, then tell the user the points were
  not set and to set them manually. Do not surface a raw field-id API error as if
  the story failed.
- If the Story create call fails (create mode), stop and show the error before
  creating any sub-task.
- If the `editJiraIssue` update fails (promote mode), report the error and keep
  the existing story key; do not create sub-tasks against a story whose body did
  not update until the user decides how to proceed.
- If a sub-task create call fails, report which one failed and continue with the
  rest rather than aborting; create the dependency links only between issues
  that were actually created. A later run recognises the created ones (5.0).
- If a dependency link call fails, report it and continue; links are recoverable
  manually.
