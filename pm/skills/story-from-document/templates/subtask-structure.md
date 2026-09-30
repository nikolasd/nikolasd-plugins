# Sub-task Structure Template

Use this for every sub-task body generated in Phase 4 of
[`../SKILL.md`](../SKILL.md). The shape is deliberate and has two layers,
because each sub-task is read by two audiences: a human reviewing the plan, and
the implementing agent or engineer who will do the work. Apply the
[content rules](../SKILL.md#content-rules).

Each sub-task has a one-line metadata header, a human-readable preamble in
prose, and then a `### Claude Planning Hints` block with the verified technical
detail. Keeping the human preamble and the machine-facing detail separate is
the lesson that makes these tickets usable: a reviewer should understand the
sub-task from the preamble alone, without reading the file-and-line anchors.

---

**Summary (issue title)**

Tag the repository or component in brackets, then the outcome. Examples:
`[library] Add a configurable retry limit`,
`[api] Enforce the retry limit on the read path`.

---

**Metadata header (one line)**

`**Repo:** <repo> · **Owner:** <agent or role> · **Depends on:** <tickets or "nothing — can start now">`

---

**Preamble (human-readable, prose)**

One to three short paragraphs in full sentences explaining what this sub-task
does and why, in terms a reviewer can follow without the technical anchors.
State what changes, what stays the same, and any ordering or safety constraint
that matters (for example, why it must wait for another sub-task, or why a
check must fail closed). Do not start the body with file paths.

---

**### Claude Planning Hints**

Everything an implementing agent needs, under this exact H3 heading so it is
clearly the machine-facing layer. Include the relevant subsections:

- **Files (verified):** the exact paths and `file:line` anchors from the
  Phase 2 investigation, each with a one-line note of what is there.
- **Change shape:** the specific edits, described by function or symbol, not as
  a diff. Note anything that becomes dead code, and anything that must stay.
- **Sequencing / preconditions:** what must be true or deployed first, and any
  ordering hazard (state it plainly, including the safe-but-degraded case).
- **Definition of done:** verifiable outcomes. For code repos, name the check
  to run (for example the repo's own test or lint command, such as a `make` target
  or `npm test`). For a spike,
  the exit artifact (a decision record naming the chosen option and its
  evidence), with no production code.

---

## Spike sub-tasks

When Phase 2 surfaced a genuine unknown that reading code cannot settle, the
sub-task is a spike. Keep the same two-layer shape, but the preamble explains
why the unknown exists and why it must be settled before the dependent
implementation sub-task, and the Claude Planning Hints give the investigation
targets and a tight exit criterion. A spike produces a decision, not code.
