# Promote mode: read the existing story and fill gaps

Read this when `SKILL.md` Phase 0 settled on **promote** mode. It replaces
Phase 1 (create). The existing story body plays the role the source plays in
create mode: it is the input to verify, not ground truth.

## Contents

- [1P.1 Read the existing story](#1p1-read-the-existing-story)
- [Issue-type rules](#issue-type-rules)
- [1P.2 Ask targeted questions to fill gaps](#1p2-ask-targeted-questions-to-fill-gaps)

## 1P.1 Read the existing story

Call `mcp__atlassian__getJiraIssue` for the story key with
`responseContentFormat: markdown` and `fields: ["*all"]`. The default field set
omits sub-tasks, issue links and custom fields, and this step needs all of them.
Capture and hold:

- The current body and summary.
- The issue type (see the rules below).
- The **parent**. Record whether the story already belongs to an Epic, because
  this decides whether you offer Epic attachment later (Phase 4). If it already
  has a parent Epic, do not offer to attach it to another.
- The target **project key**, parsed from the story key (for example `PROJ`
  from `PROJ-1234`). Hold it as `<project_key>` for Phase 5; you do not need to
  re-derive it from the repos.
- The **existing sub-tasks** (key, summary, status) and **existing issue links**
  (type, direction, other key). Phase 4 shows them, and Phase 5 must not create a
  sub-task or link that is already there.

Treat the existing body, however thin, as the initial "source" text for the
extraction step: pull out the problem it states, any changes it proposes, every
concrete claim it makes about the code, and any decisions it records as made.

## Issue-type rules

`Story` is the expected type. In many Jira projects `Task` is used
interchangeably with `Story`, so do not hard-stop on it: if the issue is a
`Task` (or a `Bug`), state the mismatch, note that any sub-tasks will be
parented to that issue rather than a Story, and ask whether to proceed.

Hard-stop only for types that are structurally incompatible: a `Sub-task`
cannot own sub-tasks, and an `Epic` is the wrong altitude for this skill (use
the `epic` and `epic-refine` skills for an Epic). If the story key is not found,
stop and tell the user.

## 1P.2 Ask targeted questions to fill gaps

A placeholder story usually omits most of what a full story needs. Ask the user
a focused set of questions to fill the gaps, not an open-ended interview. Cover
at least:

- The problem the story addresses and why it matters now.
- The outcome the user wants, in plain terms: what should be true once this is
  done. Not how to achieve it.
- Which repositories the work touches, and which is primary. This answer settles 2.1;
  do not ask it again there.
- What "done" looks like (the acceptance expectations).
- Any decisions already made that implementers must not reopen.

Do not ask how to fix the problem at this point: not what to replace, not
whether to delete versus mask, not which mechanism to use. No code has been
read yet, so the honest answer is almost always "investigate and recommend".
You settle the technical approach in Phase 2.4, after the code evidence is in
hand. Keep this interview about the problem and the desired outcome.

Keep it tight. Anything the user cannot answer becomes a `[GAP: ...]` in the
draft, to be resolved at the Phase 4 review rather than guessed.

Once you have the gathered answers, continue into Phase 2 with the existing
body plus the answers as the combined claim set to verify. The rest of the flow
(investigation, summary, optional mockups, breakdown) is identical to create
mode; only the Phase 5 write differs (edit in place rather than create).
