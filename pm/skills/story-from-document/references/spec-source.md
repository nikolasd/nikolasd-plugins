# Source is a spec: `path#S-nn`

Read this in Phase 1 (create) when the argument is a file path followed by `#S-` and
digits, for example `docs/specs/exports.md#S-03`. The file is a specs document written by
`specs-from-prd`. It holds many specs; this run builds a Story from exactly one.

## Contents

- 1. Locate the spec
- 2. Check its status
- 3. Check whether a Story already exists
- 4. Context and scope
- 5. What to verify
- 6. After the Story is created

## 1. Locate the spec

Split the argument at the last `#`. The left part is the path, the right part is the spec
ID (`S-` and digits). `Read` the whole document. Find the heading that starts with the ID,
for example `### S-03 Customers can export as CSV`. Match the heading text, never a
Markdown anchor slug. If no heading starts with that ID, stop and list the spec IDs you
did find.

## 2. Check its status

Read the spec's `Status` line. If it is missing or holds a value other than `Ready`,
`Needs decision` or `Withdrawn`, say the document does not pass the specs-from-prd format,
name `scripts/check_specs.py` in that skill as the way to find out why, and stop.

- **Withdrawn:** stop. Say that the spec is withdrawn in the document, so there is nothing
  to build, and ask whether the user meant another spec. Build nothing.
- **Needs decision:** the spec holds open gaps. List each `[GAP: ...]` and ask the user,
  one at a time, to decide it, with options and a recommendation. A gap the user cannot
  decide stays `[GAP: ...]` in the Story. Ask product gaps (a time zone, who may see it)
  now; carry technical gaps (which library, which scheduler) into 2.4, where code
  evidence can support a recommendation.
- **Ready:** continue.

## 3. Check whether a Story already exists

If the spec's `Story:` line holds a Jira key, say so and ask whether to update that Story
(promote mode with that key), create a new one anyway, or stop. Do not decide this for the
user. If the answer is to update it, the spec stays part of the claim set next to the
existing Story body.

## 4. Context and scope

Read the whole document as context: the feature design, the decisions (`D-nn`) and the
dependency diagram, and the header's `Audience and success signal`, which feeds the
Story's User Story and Context. Treat the decisions as already made: do not re-ask them. The scope of
the Story is the selected spec only. Do not pull another spec's scope, acceptance
criteria or technical approach into this Story, even when it sits next to this one in the
document.

If the spec's `Depends on` names other specs, record them under Scope as `Depends on S-nn`
(that section is always present; "Sub-tasks and dependencies" is omitted when there are no
sub-tasks). If a depended-on spec's `Story:` line holds a key, plan a Blocks link to it in
4.2 as an external prerequisite: the depended-on Story is the blocker (`inwardIssue`) and
this Story is the blocked issue (`outwardIssue`).

## 5. What to verify

The spec's technical approach and its `file:line` evidence are the claims to check in
Phase 2. Re-read each cited line yourself. If the code has moved since the spec was
written, report the drift as a finding and use the current lines. The spec's `Repo` is the
root folder name of a repository, not a path. The primary repository for Phase 2.1 is the
one whose folder name matches it: compare it with `basename $(git rev-parse --show-toplevel)`
for the current repository, and if they differ ask the user for its path before reading it.

The "Source of analysis" section names `<path>#S-nn`. The `Source check:` line in
`SKILL.md` applies to the document as it does to any source.

## 6. After the Story is created

This skill never edits the specs document. When Phase 5 confirms the new key, add:

> "Set the `Story:` line of S-nn in `<path>` to `<KEY>` so the spec is locked against
> accidental rewrites. I have not edited the document."
