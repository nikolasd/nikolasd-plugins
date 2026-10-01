# Story Section Templates

Use these section definitions when generating story content in Phase 3 of
[`../SKILL.md`](../SKILL.md). Apply the [content rules](../SKILL.md#content-rules)
to every section. Produce sections in the order listed below.

**Sections, in order:** User Story, Context, Requirements, Implementation Specification, Acceptance Criteria, Test Requirements, Technical Notes, Sub-tasks, Other Information, Gaps.

---

**User Story**

Construct from the persona most relevant to the story summary and the story
summary from the Epic table. If the persona is ambiguous, propose the most likely
one and list it in the Phase 4 review as a choice for the user. Format: `As a [Persona], I want [capability]
so that [benefit].`

---

**Context**

State which phase this story belongs to, what the phase goal is (copied from
Epic), and how this story contributes to it. Note any stories in the same
phase whose Id column is still empty and that this story may depend on.

---

**Requirements**

Derive from the story summary plus the relevant phase scope from the Epic.
Write as a specific list, not a restatement of the summary sentence.

---

**Implementation Specification**

Determine which subsections apply based on the story summary and Technology
Context. Include only relevant subsections. Omit any that do not apply. Every
item must rest on code you have read: cite `path/to/file.py:120` for the
existing route, model, component or configuration it extends, and say plainly
what is new. If you cannot confirm an existing pattern, mark it
`[GAP: ...]`; never invent a path, endpoint or schema.

- **API Endpoint(s):** Derive method, path, auth, request/response schema,
  and error cases from the story summary, Technology Context, and sequence
  diagrams. Use the naming conventions and module patterns from the Epic.
- **Data Model:** Include only if the story introduces or modifies a data
  model. Derive from Technology Context storage section and sequence
  diagrams.
- **Frontend Component:** Include only if the story has a frontend
  deliverable. Derive component name, location, states, interactions, and
  pattern from Technology Context frontend section and existing code
  structure.
- **Infrastructure / Configuration:** Include only if the story involves
  infrastructure or deployment changes.

---

**Acceptance Criteria**

- **Functional:** Derive from the story summary and requirements. Write 3-6
  specific, testable criteria.
- **Non-Functional:** Copy the applicable NFR thresholds from the Epic
  verbatim. Include only those relevant to this story. If none apply, omit
  the section.
- **Regression:** Always include this criterion, filled in for the story: "All
  existing automated tests for [affected component(s)] pass, and [the named
  existing behaviour closest to this change] is unchanged." Name the real
  component and one concrete existing behaviour from the code you read. If none
  can be identified, mark it `[GAP: ...]`. This is non-negotiable per the content
  rules.

---

**Test Requirements**

Derive unit, integration, E2E, and edge case requirements from the ACs and
implementation specification. State specific cases, not generic
instructions. Omit E2E if the story has no user-facing behaviour.

---

**Technical Notes**

Copy the following directly from the Epic. Do not summarise or link:

- The sequence diagram(s) for the relevant phase that cover this story's
  interactions (full Mermaid text)
- The phase technical constraints for this story's phase
- The Technology Context slice relevant to this story (module names,
  patterns, key dependencies, auth approach)

---

**Sub-tasks**

Include sub-tasks only when the work has two or more clearly separable work
streams, and put the split to the user as a Phase 4 choice. If sub-tasks apply,
list each with description and effort, where effort is what the user gave you or
`[GAP: effort]`. If not, omit the section entirely.

---

**Other Information**

- **Links:** Omit unless a specific design doc or ADR is referenced in the
  Epic.
- **Dependencies:** List story names (not yet IDs) of any uncreated stories
  in the same phase this story likely depends on.
- **Notes:** Any implementation decisions flagged as uncertain or requiring
  pre-work agreement.

---

**Gaps**

If any section cannot be fully derived from available information, mark it
with `[GAP: description of what is missing]` rather than guessing. List all
gaps at the end of the draft under a "Gaps" heading. Gaps must be resolved
by the user during Phase 4 review before the story is created in Jira.
