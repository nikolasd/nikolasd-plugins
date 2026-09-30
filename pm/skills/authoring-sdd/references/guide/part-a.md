<!-- Part A of the bundled SDD authoring guide. The conventions every Part relies on (ID registry, vocabularies, omission rule, evidence, diagrams, checklist) are in 00-conventions.md. -->

## Contents of this Part

- §1 Document control
- §2 References & related documents

---

# Part A — Document control

## 1. Document control — `REQUIRED`

**Purpose.** Establishes who owns the document, who has approved it, and what changed since the last version. This is what makes the SDD a deliverable rather than a working note.

**How to write it.** Three blocks: metadata, revision history, approvals. Revision history is append-only. The approvals table is signed at each formal issue — an unsigned approvals table is itself a finding. Classification drives what may appear in the document, per §0.7.

**Example**

**Metadata**

|  |  |
| --- | --- |
| **Project** | Acme Claims Assistant |
| **Client** | Acme Insurance |
| **Document status** | Issued for review |
| **Version** | 1.2 |
| **Classification** | Confidential — Acme Insurance and Northwind Consulting only |
| **Owner** | A. Architect, Tech Lead, Northwind Consulting |
| **Contributors** | B. Engineer (backend), C. Engineer (platform) |
| **Audience** | Acme solution architects, Acme security review, Acme business sponsor, Northwind delivery team |
| **Last reviewed** | 2026-08-05 |
| **Next review** | 2026-09-30 or at the next release, whichever is sooner |

**Revision history**

| Version | Date | Author | Summary of change |
| --- | --- | --- | --- |
| 1.0 | 2026-05-14 | A. Architect | Initial issue for design review. |
| 1.1 | 2026-06-27 | A. Architect | Added ADR-0004; NFR-02 threshold agreed with Acme. |
| 1.2 | 2026-08-05 | A. Architect | Full codebase verification pass; R-06…R-12 added; §17 Data design added. |

**Approvals**

| Role | Name | Organisation | Date | Outcome |
| --- | --- | --- | --- | --- |
| Solution Architect | A. Architect | Northwind | 2026-08-05 | Approved |
| Engineering Manager | D. Manager | Northwind | 2026-08-05 | Approved |
| Client Technical Sponsor | E. Sponsor | Acme |  | Pending |
| Client Security | F. Security | Acme |  | Pending — review scheduled 2026-08-19 |

---

## 2. References & related documents — `REQUIRED`

**Purpose.** Tells the reader where the rest of the truth lives. An SDD is one document in a set; unlinked companions are effectively lost.

**How to write it.** Link every companion artefact, and state what each is authoritative for. Where a live system is the authority — an OpenAPI specification, an infrastructure repository — say so explicitly. This is what stops the SDD from drifting into a stale second source of truth.

**Example**

| Ref | Document | Authoritative for | Location |
| --- | --- | --- | --- |
| REF-01 | Acme Claims Assistant — Low-Level Design | Component internals, class-level detail | Confluence, project space |
| REF-02 | Live OpenAPI specification (`/docs`) | Field-level API contract | Running service — **authoritative over §19 of this document** |
| REF-03 | Infrastructure repository (`infra/`) | Deployed Azure resource definitions | Git |
| REF-04 | Acme Information Security Policy v4 | Client security requirements | Supplied by Acme, 2026-04-02 |
| REF-05 | Acme Claims Assistant — Test Strategy | Test scope and coverage targets | Confluence, project space |
| REF-06 | Statement of Work, signed 2026-03-30 | Commercial scope | Contract repository |
