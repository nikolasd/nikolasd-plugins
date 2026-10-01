<!-- Bundled SDD authoring guide, part 0: introduction and conventions (§0). Read this first; the Part files hold the per-section guidance. -->

| **Document type** | Authoring guide — companion to the template |
| --- | --- |
| **Guide version** | v2.0 |
| **Owner** | Engineering |
| **Applies to** | Solution Design Documents for customer projects and internal projects |
| **Last reviewed** | 2026-08-06 |

> **This page is the guide, not the template.**  
> To start a new project document, copy **Solution Design Document — Template v2.0** — the blank, copy-and-fill page. Come back here for what each section is for, how to write it, and a worked example.

The SDD is a **client-facing deliverable**. It is the document a customer architect, a customer security reviewer, and an engineer joining in month six all read to understand what was built, why, and what is still open. It is not a status report and not a low-level design — it states the solution, the reasoning, and the honest position on every open item.

Every section below matches the template one-for-one, by number and by name. Each carries three blocks: **Purpose** (what the section is for), **How to write it** (the rules), and **Example** (a worked illustration drawn from a fictional reference project, Acme Claims Assistant, used consistently throughout).

Acme (the client) and Northwind Consulting (the supplier) are fictional, and the example is deliberately specific: an Azure retrieval-augmented generation stack, Microsoft identity, a UK region and UK business hours. None of that is a recommendation. Substitute your own stack, region, hours, organisations and figures. For an internal project, read *client* as the business sponsor and *supplier* as the delivery team.

---

# §0 — Conventions

These conventions govern the whole document. They are defined once here and referenced from every section — they are not per-section advice.

## Contents

- 0.1 Working method
- 0.2 Section tiers
- 0.3 ID registry
- 0.4 Controlled vocabularies
- 0.5 The omission rule
- 0.6 Evidence and verification
- 0.7 Diagrams and confidentiality
- 0.8 Pre-share review checklist

## 0.1 Working method

1. Copy **Solution Design Document — Template v2.0** into the project's documentation space (for example a Confluence space) and rename it `[Project] — Solution Design Document`.
2. Fill in every section in order, except **At a glance**, which you write last.
3. Work with this guide open alongside the template. Delete the tier tags from the template's headings as you complete each section.
4. Never delete a section — see the omission rule in §0.5.
5. Run the review checklist in §0.8 before sharing the document with a client.

## 0.2 Section tiers

Every section is tagged in the template. The tag is not a suggestion.

| Tag | Meaning |
| --- | --- |
| `REQUIRED` | Present and filled in on every customer project, without exception. |
| `CONDITIONAL` | Required whenever its stated trigger is true. If the trigger is false, apply the omission rule (§0.5). |
| `OPTIONAL` | Include on judgement. If you exclude it, no note is needed. |

## 0.3 ID registry

Identifiers are what make the document reviewable, testable, and auditable. They are referenced by delivery stories, test cases, the UAT report, and the client's own security review.

| Prefix | Applies to | Format | Example |
| --- | --- | --- | --- |
| `FR-` | Functional requirement | two digits | `FR-07` |
| `NFR-` | Non-functional requirement | two digits | `NFR-03` |
| `A-` | Assumption | two digits | `A-12` |
| `D-` | Dependency | two digits | `D-04` |
| `R-` | Risk or constraint | two digits | `R-19` |
| `ADR-` | Architecture Decision Record | four digits | `ADR-0005` |
| `OQ-` | Open question | two digits | `OQ-11` |

**Rules — these are absolute:**

* An ID is assigned **once** and is **never renumbered, never reused, and never recycled** after retirement.
* An ID means **exactly one thing** for the life of the document. If you find one ID used for two items, that is a defect — fix it before the next review, keeping the earlier meaning on the original ID.
* **Reserve the full range up front** (e.g. `FR-01`…`FR-15`) even when some rows are still `Reserved`. Never compress the range as you draft.
* A retired item **keeps its ID** and its row, with status `Descoped` and a one-line reason. Deleting the row breaks every outbound reference.

## 0.4 Controlled vocabularies

Use these values exactly. Do not qualify them inline — `Must (target TBD)` is not a value.

**Requirement priority — MoSCoW**

| Value | Meaning |
| --- | --- |
| `Must` | The solution fails its purpose without this. |
| `Should` | Important; a defined workaround exists if it slips. |
| `Could` | Desirable; first to be traded away. |
| `Won't` | Explicitly excluded from this phase. Record it so it stays excluded. |

**Requirement status**

`Proposed` · `Agreed` · `In build` · `Met` · `Not met` · `Reserved` · `Descoped`

`Not met` on a `Must` requirement must carry a risk reference in the same row.

**Risk severity**

| Value | Meaning |
| --- | --- |
| `Critical` | Active exposure, or certain failure of a `Must` requirement. Blocks go-live. Needs a named owner and a date now. |
| `High` | Likely to block go-live or breach an agreed NFR. Mitigation must be scheduled, not merely noted. |
| `Medium` | Degrades quality, cost, or operability. Mitigation planned. |
| `Low` | Contained or cosmetic. Accept, or fix opportunistically. |

**Risk status**

`Open` · `Mitigating` · `Control in place` · `Accepted` · `Closed`

`Accepted` means a named party has consciously accepted the risk — record who, in the Owner column.

**Deliverable status**

`Not started` · `In progress` · `Blocked` · `Done` · `Backlog`

## 0.5 The omission rule

**Never delete a section.** If a section does not apply, keep the heading and replace its body with:

> _Not applicable — \[one-line reason\]._

A reviewer must be able to tell a deliberate exclusion from an oversight. This applies uniformly — to `CONDITIONAL` sections, to C4 levels, to interfaces, to everything.

## 0.6 Evidence and verification

An SDD that describes intent as though it were fact is worse than no SDD.

* Any claim about a **deployed** environment carries the date and source of verification — for example, "verified against the live environment on 2026-07-31".
* A configuration value read only from source control is **not** a claim about the deployment. Say so.
* **Bold every known gap, unmet requirement, and open exposure.** Brevity in a table cell must never erase a caveat. A caveat flattened out of existence is a silent regression, and the next reader will act on the wrong picture.
* Where a claim is unverified, mark it unverified rather than omitting it.

## 0.7 Diagrams and confidentiality

**Diagrams — publish the source, and a rendered image wherever the destination cannot render Mermaid.** Author in Mermaid. Where the destination renders a fenced `mermaid` block natively (GitHub, GitLab and most documentation sites), the source alone is enough. Where it does not, publish two things, in this order. Confluence is the usual case: it renders a fenced `mermaid` block as **source code, not as a diagram**, so source alone leaves a client-facing document with no visible architecture.

1. **A rendered image** — paste the Mermaid source into a renderer such as `mermaid.live`, export PNG or SVG, and place it at the top of the section. This is what a reader sees.
2. **The Mermaid source immediately beneath it**, in a fenced `mermaid` block. This is what the next author edits and what a reviewer diffs.

Keeping both means the diagram is legible to the reader and maintainable by the team; keeping only one fails one of those two audiences. When you change a diagram, **re-export the image at the same time as the source edit** — a stale image over fresh source is worse than either alone.

C4 colour convention: system under design `#1168bd`, human actors `#08427b`, external systems `#999999`. Colour a component red or amber when it carries a known risk, and name the risk in the node label so the caveat travels with the picture.

Never let a missing diagram block the rest of the document — ship a placeholder and note it.

**Confidentiality.** State the document's classification in §1. In a client-shared document, do **not** publish tenant, subscription or account IDs, resource GUIDs, connection strings, certificate thumbprints, or private endpoint hostnames. Reference an internal deployed-resources page instead. If the client explicitly asks for them, record that they asked.

## 0.8 Pre-share review checklist

* Every `REQUIRED` section is filled in; every excluded section carries _Not applicable — reason_.
* No ID appears twice with two meanings; no ID range was compressed.
* Every `Must` requirement has an acceptance criterion and a status.
* Every `Critical` and `High` risk has a named owner and a date or a decision.
* Every unmet `Must` requirement is cross-referenced from a risk.
* Every claim about the live environment carries a verification date.
* No secrets, GUIDs, or private hostnames in a client-shared document.
* Revision history and approvals (§1) are current.
* Every diagram is published as Mermaid source, with a rendered image above it wherever the destination cannot render Mermaid, and any image matches the current source.

---

_This is the authoring guide. The blank document to copy is **Solution Design Document — Template v2.0**. Keep the two together, and maintain them as part of your delivery documentation standard._
