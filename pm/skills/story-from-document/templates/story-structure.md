# Story Structure Template

## Contents

- Summary (issue title)
- User Story
- Context
- Source of analysis
- Source document notes
- Scope
- Requirements
- Implementation Specification
- Acceptance Criteria
- Test Requirements
- Technical Notes
- Sub-tasks and dependencies
- Decisions carried from the source (do not re-litigate)
- Out of scope
- Gaps

Use these section definitions when generating the standalone Story body in
Phase 4 of [`../SKILL.md`](../SKILL.md). The same template serves both modes:
**create** (a new Story from a source artifact) and **promote** (an existing
Story fleshed out in place). Apply the
[content rules](../SKILL.md#content-rules) to every section: human-facing prose
in full sentences, no em dashes, claims about code carry `file:line` evidence.
Produce the sections in the order below.

This is a merged section set. It keeps the investigation sections that are
specific to this skill (Source of analysis, the conditional Source document
notes, Scope, Sub-tasks and dependencies, Decisions carried from the source,
Out of scope) and adds the richer
story-shaped sections (User Story, Requirements, Implementation Specification,
Acceptance Criteria, Test Requirements, Technical Notes). The crucial
difference from the Step-3 `story` skill: here those story-shaped
sections are **populated from the Q&A and the code investigation**, not copied
from an Epic. Anything that cannot be derived from the source, the user's
answers, or the verified code is marked `[GAP: ...]` and resolved at the Phase 4
review (see the Gaps section).

---

**Summary (issue title)**

One line naming the outcome, not the activity. Prefer the change in plain
terms over the mechanism. Example: `Access control: resolve group
membership at read time instead of write time`. In promote mode,
keep the existing summary unless it misnames the work; if you change it, say so
at the review.

---

**User Story**

One sentence in the form `As a [persona], I want [capability] so that
[benefit].` Derive the persona from the source or the user's answers, not from
an Epic Personas table (there may be no Epic). If the persona is genuinely
unclear, mark it `[GAP: persona not established]` rather than inventing one.

---

**Context**

Flowing prose, several short paragraphs. Cover, in order:

- Why the change is needed: the problem the source (or the existing story, in
  promote mode) describes, stated plainly.
- What the investigation found: the verified picture from Phase 2, including
  any place the input's claims turned out to be wrong, stale, or only
  partially true. This is the part a reviewer most needs, because it is the
  difference between the proposal and reality.
- The shape of the fix and the outcome it produces.

Write this so a reviewer who has never seen the source can follow it. Do not
compress it into note form.

---

**Source of analysis**

Name the source artifact (Confluence page title and ID, file path, or "written
brief"), or in promote mode the existing story key and that its body was the
starting point. Give the date the investigation was run and any correction to
the source's framing that the reader should carry into the rest of the story.

---

**Source document notes**

Include this section only when the source is a written document (a Confluence
page or a file) and the Phase 2 investigation found it inaccurate against the
current code. List each inaccuracy as a pair: what the document says, and what
the code actually shows, with a `file:line` anchor (wrong log levels, drifted
line numbers, claims that no longer hold, findings the document missed). This
makes the drift visible to the reader and feeds the Out of scope note about
correcting the document. Omit the section entirely when the source is a brief,
a promoted story body, or a document that checked out clean.

---

**Scope**

State which repositories are in **enhancement scope** (code will change) and
which are **verify-only** (confirmed correct, no change). If the work depends
on a published library version, note the publish-then-consume ordering here.

---

**Requirements**

A specific list of what the story must deliver, derived from the source, the
user's answers, and the verified investigation. Not a restatement of the
summary sentence. Mark anything still open as `[GAP: ...]`.

---

**Implementation Specification**

Determine which subsections apply from the verified investigation and the
agreed shape of the work. Include only the relevant ones and omit the rest.
Every claim about existing code carries a `file:line` anchor from Phase 2.

- **API Endpoint(s):** method, path, auth, request/response shape, and error
  cases, anchored to the real handlers found in the investigation.
- **Data Model:** include only if the story introduces or changes a model;
  describe it against the storage code that exists.
- **Frontend Component:** include only if there is a frontend deliverable;
  name the component, its location, states, and the pattern it follows in the
  existing code.
- **Infrastructure / Configuration:** include only if the story changes
  infrastructure or deployment.

Where the right design cannot be settled from the code or the user's answers,
mark it `[GAP: ...]` rather than guessing.

---

**Acceptance Criteria**

- **Functional:** 3 to 6 specific, testable sentences derived from the
  requirements and the agreed change. Each must be verifiable by a
  non-engineer.
- **Non-Functional:** include only the thresholds that genuinely apply, stated
  inline with the number, not "see somewhere else". Omit if none apply.
- **Regression:** always include an AC that existing behaviour in the affected
  areas continues to work.

---

**Test Requirements**

State the specific unit, integration, end-to-end, and edge cases the change
needs, derived from the ACs and the implementation specification. Name concrete
cases, not generic instructions. Omit end-to-end if the story has no
user-facing behaviour.

---

**Technical Notes**

The technical detail an implementer needs that does not fit the sections above:
the relevant module names and patterns confirmed in the investigation, key
dependencies, the auth approach, and any ordering or migration concern. Anchor
claims with `file:line`. Unlike `story`, this is assembled from the
verified investigation, not copied from an Epic's Technology Context.

When the story has no sub-tasks (all the work fits one repository and one pull
request), this section carries the full implementation detail that would
otherwise have gone into sub-task `### Claude Planning Hints` blocks: the
verified file anchors, the change shape, and the definition of done.

---

**Sub-tasks and dependencies**

Include this section only when the work is actually split into sub-tasks. If all
the work lives in one repository and is reviewable in a single pull request,
there are no sub-tasks: omit this section and put the implementation detail in
Technical Notes instead. Do not manufacture a single sub-task. When there are
sub-tasks, give a short list naming each one and a gantt-like diagram showing
order and parallelism. Mark the critical path and anything that can start immediately.
Name external prerequisite tickets and how they block the work. If a dependency
is conditional (for example, a downstream task is only blocked when the team
actually cuts a new library release), state it in prose alongside the firm
Blocks edges rather than forcing it into a hard link. Example shape:

```
EXT  PREREQ-123 merged            ████ (upstream prereq)
ST1  library change + publish     ██████░░          (parallel to EXT)
ST2  spike                            ███  <- EXT
ST3  consume new library version          ███   <- ST1
ST4  read-side change                        █████ <- ST3 + ST2 + EXT
```

---

**Decisions carried from the source (do not re-litigate)**

Copy verbatim any decision the source (or the existing story body, in promote
mode) records as already settled, so implementers do not reopen it. State each
with its rationale and any mitigation attached to it.

---

**Out of scope**

List what this story explicitly does not cover, including verify-only repos and
any deferred follow-ups. If the investigation recorded Source document notes,
add an entry here stating that correcting the source document is not part of
this story and should happen once anything blocking it is resolved (for example
an unmerged branch).

---

**Gaps**

If any section cannot be fully derived from the source, the user's answers, or
the verified code, mark the spot inline with `[GAP: description of what is
missing]` rather than guessing, and list every gap together at the end under a
`Gaps` heading. Gaps must be resolved by the user during the Phase 4 review
before the Story is created or, in promote mode, written back.
