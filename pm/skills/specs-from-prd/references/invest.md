# Phase 5 and 6: INVEST and splitting

Read this at the start of Phase 5. Every live spec carries six results, one per
criterion, each `Pass` or `Fail` with a one-line reason. A `Fail` is never left in the
document: fix the spec first.

## Contents

- The six criteria
- Splitting
- When a spec fails

## The six criteria

| Criterion | Ask | Pass looks like |
|---|---|---|
| Independent | Can this be built and released without another spec? | No dependency, or the dependency is declared in `Depends on` and cannot be removed by reordering. |
| Negotiable | Does it state the outcome and leave the implementation open? | The acceptance criteria describe behaviour a user can see, not a mandated class or table. |
| Valuable | Can a user or the business observe the benefit on its own? | A person could say what is now possible that was not before. |
| Estimable | Is it clear enough that a team could estimate it? | No open `[GAP: ...]` hides the size of the work. Give no number. |
| Small | One repository and one reviewable change? | It fits one pull request. More than about seven acceptance criteria usually means two specs. |
| Testable | Can every acceptance criterion be verified? | Each is a complete sentence with an observable result. |

A recorded gap keeps Estimable at `Pass`, with the reason "gap recorded": list the gap and
set the status to `Needs decision`. A spec whose size is unknowable even with the gap
recorded is split or merged until it is not, because a `Fail` never stays in the document.

## Splitting

Split by what a user can do, in thin slices that each work end to end, such as one
format, one trigger or one role. Do not split by layer (a "database spec" and an "API
spec"): neither is valuable alone, and the pair is not independent. Split by repository
whenever one capability needs changes in two, so each spec has exactly one `Repo`, and
declare the order in `Depends on`.

One spec per capability the PRD asks for. When the PRD lists several formats, triggers or
roles, each is its own spec. A capability the code already provides needs no spec of its
own (say so under Scope) and is never bundled with a new one: a story for "CSV or PDF"
where CSV already exists is really the PDF story, so write it as that. State a
cross-cutting behaviour such as an audit log once, in the spec that owns it, and let the
others declare `Depends on`; give another spec a criterion about it only when that spec
has an outcome of its own to verify.

Example (an illustration of the shape, not a template). Before: "Customers can export their
orders as CSV or PDF, schedule a weekly emailed export, and an admin can see an audit log of
every export." One spec fails Small and Independent. After: `S-01` Customers download their
orders as PDF (CSV already exists, so it gets no spec; say so under Scope); `S-02` Admins view
an audit log of exports; `S-03` Customers receive a weekly emailed export, which depends on
`S-02` so that scheduled exports are logged.

## When a spec fails

- **Too big (Small):** split it into slices, each with its own acceptance criteria.
- **Not independent:** reorder or re-slice so the dependency disappears; if it cannot,
  declare it in `Depends on` and keep the result honest.
- **Not valuable:** merge it into the spec whose benefit it enables.
- **Not testable:** rewrite the criterion until a person could verify it, or record a
  `[GAP: ...]` for the missing observable meaning.

List every split and merge with its reason at the top of the review gate, where the user
approves them with the rest of the draft. Ask earlier only when one touches a locked spec or
a recorded decision.
