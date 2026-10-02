# Phase 4 (steps 4.1 to 4.3): breakdown, dependencies and Epic attachment

Read this at the start of Phase 4, before you draft the ticket set. The review
gate itself (4.4) is in `SKILL.md`.

## Contents

- [4.1 Decide the breakdown](#41-decide-the-breakdown)
- [4.2 Map dependencies](#42-map-dependencies)
- [4.3 Offer Epic attachment](#43-offer-epic-attachment)

## 4.1 Decide the breakdown

Decide whether the work is one Story with sub-tasks, and what each sub-task is.
Split by repository and by reviewable unit of work so that each sub-task can own
its own pull request.

Do not create sub-tasks for their own sake. If all the work lives in one
repository and can be reviewed in a single pull request, the Story has no
sub-tasks: put the implementation detail directly in the Story's Technical
Notes section instead. A story with a single sub-task adds no value and only
prompts the reviewer to ask why it is there. Reach for sub-tasks only when the
work genuinely splits across repositories or into separately reviewable units.

Use the section definitions in `../templates/story-structure.md` for the Story and
`../templates/subtask-structure.md` for each sub-task (both read in Phase 3). Every sub-task gets a human-readable preamble followed by a
`### Claude Planning Hints` block.

**Promote mode:** the review must show the sub-tasks and links that already
exist (captured in the promote-mode read). Mark each planned sub-task as `new`
or `already exists (skip)`, matching on summary, and do the same for each link.
Plan to create only what is new.

## 4.2 Map dependencies

Express the order of work as Blocks links and draw a short gantt-like diagram
showing what runs in parallel and what waits. Dependencies include cross-repo
sequencing (for example, publish a library version before the repos that consume
it can bump to it), internal ordering between sub-tasks, and external
prerequisite tickets the user names (link the Story or the relevant sub-task as
"is blocked by" the prerequisite). For a genuinely unknown precondition
identified in Phase 2, propose a spike sub-task with a tight exit criterion
rather than burying the risk in an implementation ticket.

## 4.3 Offer Epic attachment

Ask whether this Story should belong to an existing Epic. Make the offer
according to the mode:

- **Create mode:** always ask.

  > "Should this Story belong to an existing Epic? If so, give me the Epic key
  > and I will set it as the parent. This only sets the parent link; it does not
  > add a row to the Epic's story table or change the Epic's maturity."

- **Promote mode:** ask only if the story has **no** parent Epic (checked in the
  promote-mode read). If it already has one, skip the offer and leave the parent
  as it is.

If the user names an Epic, validate it before accepting it: fetch it with
`mcp__atlassian__getJiraIssue` and confirm its issue type is `Epic`. If the key
is missing or is not an Epic, say so and ask again rather than guessing; do not
guess a key and do not fall back to leaving the story unparented without telling
the user. Hold the validated key as `<epic_key>` for Phase 5. The constraint is
firm and deliberate: attachment sets only the parent link. Do **not** add a row
to the Epic's story table and do **not** change the Epic's maturity state or
labels. That Epic-table-and-maturity behaviour belongs to `story`, not here; do
not "helpfully" wire it in.
