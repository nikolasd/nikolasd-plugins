# Re-runs: updating an existing specs document

Read this in Phase 1 when a document already exists at the specs path. The document is
living: the PRD changes, and Stories may already exist for some specs.

## Rules

1. **IDs are stable.** Never renumber a spec or a decision. Never reuse an ID, including
   the ID of a withdrawn spec. New specs take the next number after the highest ID in the
   document, withdrawn ones included.
2. **A spec with a `Story:` value is locked.** A PRD change that touches it is not
   written into the spec. Show it as a proposed amendment in the review gate and let the
   user decide: amend the spec, or leave it and cover the change with a new spec. The one
   exception is a gap the user has now resolved: that edits only the gap line and the
   status of the locked spec, and is shown as a proposed amendment like any other.
3. **A spec that no longer fits becomes `Withdrawn`.** Keep its block, keep its ID, set
   the status, and say why in the change log. Never delete it. Live specs must not depend
   on it: re-point or remove those dependencies and tell the user.
4. **Keep what the user decided.** Existing decisions stay, with their IDs. A new answer
   that conflicts with one is recorded as a new decision that supersedes it, and the
   change log says so.
5. **Gaps move forward.** A `[GAP: ...]` that the new answers resolve is removed, and its
   spec moves from `Needs decision` to `Ready`. A gap that is still open stays.
6. **Keep the audience and success signal.** The header's `Audience and success signal`
   stays as it is unless the user changes it.

## What to show at the gate

Before the full draft, list: new specs, amended specs, withdrawn specs, locked specs with
a proposed amendment, resolved gaps, and any dependency you re-pointed. The change log
gets one row for this run.

## What not to do

- Do not rewrite a spec's text just to polish it.
- Do not change a spec's `Story:` value. The user owns that field.
- Do not renumber to close a gap in the numbering.
