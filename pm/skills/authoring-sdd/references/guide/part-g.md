<!-- Part G of the bundled SDD authoring guide. The conventions every Part relies on (ID registry, vocabularies, omission rule, evidence, diagrams, checklist) are in 00-conventions.md. -->

## Contents of this Part

- §33 Key decisions
- §34 Architecture Decision Records
- §35 Risks, dependencies & constraints
- §36 Outcomes & deliverables
- §37 Open questions

---

# Part G — Decisions, risks and open items

## 33. Key decisions — `REQUIRED`

**Purpose.** A one-screen index of the decisions that shaped the solution, each pointing to its full record.

**How to write it.** One bullet per decision: what was decided and the single-sentence reason, then a reference to its ADR. This section is the index; §34 is the record. Using both is correct — a reader who wants the shape of the design reads this, and a reader who wants to know what alternatives were rejected reads the ADR. **Only reference an ADR that exists.** If a significant change was made without an ADR, either write the ADR or describe the change without a reference — never point at an unrelated ADR ID because the number came to mind.

**Example**

* **Embedding model** — `text-embedding-3-large` selected over smaller alternatives for retrieval precision on long-form policy language. See ADR-0001.
* **Chunking strategy** — section-boundary chunking over document layout rather than fixed-size windows, to keep policy clauses intact. See ADR-0002.
* **ClaimCore integration** — scheduled read-only pull rather than event subscription, because ClaimCore exposes no change feed. See ADR-0003.
* **Permission model** — ACLs replicated into the index as a query-time security filter rather than post-filtering results, to avoid leaking existence through result counts. See ADR-0004.
* **Rollback approach** — image redeploy with index aliasing, rather than blue-green infrastructure, given the agreed availability window. See ADR-0005.

---

## 34. Architecture Decision Records — `REQUIRED`

**Purpose.** The durable record of what was decided, what was rejected, and what it cost.

**How to write it.** The inline table below is sufficient for most projects and scales further than people expect. For a large or long-lived programme, use dedicated ADR pages linked from §33 instead — but pick one route and say which. **Every ADR has a unique ID that means one thing forever** (§0.3). An ID used for two decisions is a defect, and it is a common one: it happens when a later change is casually cross-referenced to whichever ADR number was nearest to hand. The Consequences column is the one that earns its keep — record what got worse as well as what got better, because an ADR with no downside was not a decision.

**Example**

| ID | Date | Status | Decision | Alternatives rejected | Consequences |
| --- | --- | --- | --- | --- | --- |
| ADR-0001 | 2026-05-08 | Accepted | `text-embedding-3-large` for embeddings | `text-embedding-3-small`; a third-party multilingual model | Higher retrieval precision on long clauses; roughly 3× embedding cost, immaterial at current corpus size; index dimensionality is now fixed to this model — a change means a full rebuild |
| ADR-0002 | 2026-05-08 | Accepted | Section-boundary chunking over document layout | Fixed-size token windows with overlap | Retrieval units align to policy clauses, improving citation precision; variable chunk sizes make token-cost forecasting less predictable |
| ADR-0003 | 2026-05-21 | Accepted | Scheduled read-only pull from ClaimCore | Event subscription; direct database read | No dependency on a ClaimCore change; up to 30 minutes' staleness on claim notes, accepted by Acme Claims Ops |
| ADR-0004 | 2026-06-02 | Accepted | ACLs replicated into the index as a query-time filter | Post-filtering retrieved results | No existence leakage through result counts; permission changes now require a reconciliation job (Pipeline 2) rather than taking effect instantly |
| ADR-0005 | 2026-06-19 | Accepted | Image redeploy with index aliasing for rollback | Blue-green slots; deployment slots | Materially lower cost and complexity; a short restart at each deployment, acceptable within NFR-05's window |
| ADR-0006 | 2026-07-30 | Superseded by ADR-0007 | Single shared service principal for all Graph access | — | Simpler credential management; superseded after review found the union of permissions was over-broad |
| ADR-0007 | 2026-08-04 | Accepted | Per-feature service principals, SharePoint access scoped via `Sites.Selected` | Retaining the shared principal | Blast radius of a credential compromise reduced to one feature and named sites; three credentials to rotate instead of one |

---

## 35. Risks, dependencies & constraints — `REQUIRED`

**Purpose.** The honest ledger. This is the section a client security reviewer reads first and the one that most determines whether the document is trusted.

**How to write it.** Mandatory on every project regardless of size — two rows is fine, absent is not. **Include every known risk, not a representative sample**; an incomplete ledger is worse than a long one, because it teaches the reader that the ledger cannot be relied on. Severity and status use the vocabularies in §0.4. Every `Critical` and `High` risk carries a named owner and either a date or an explicit decision. Where a risk exists because a decision is owed by the client, say so and link the open question. Review severities at every phase change.

**Example**

_Risk IDs are stable and never renumbered. R-01 through R-05 carry forward from the design review of 2026-06-27; R-06 onward were added by the verification pass of 2026-08-01. Every entry reflects a confirmed condition._

| ID | Risk / constraint | Severity | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| R-01 | Claim notes may contain personal data relating to third parties, which retrieval could surface to a handler working an unrelated claim | High | Claim-note retrieval is scoped by claim reference; retrieval outside the handler's assigned claims is blocked at the security filter. Verified by `TEST-SEC-04` | Northwind | Control in place |
| R-02 | Web client and API share one App Service Plan with autoscale at plan level; NFR-03 has not been load-tested | High | Execute `LOAD-STD-01` before go-live; separate the plans if the test shows contention | Northwind | Open — target 2026-09-05 |
| R-03 | ClaimCore imposes an undocumented rate limit; a full historical backfill may breach it | Medium | Backfill throttled to 2 requests/second with backoff; confirm the limit with Acme Claims Platform | Northwind + Acme | Mitigating |
| R-04 | **Administrative authorisation is not enforced at the API layer. Every authenticated user currently has administrator-equivalent access, including document deletion.** | **Critical** | Implement and verify server-side group checks on every administrative endpoint. Blocks UAT entry | Northwind | Open — **highest priority; target 2026-08-20** |
| R-05 | Only the Development environment is provisioned; Pre-production and Production do not exist, and rollback has not been rehearsed outside Development | High | Provision both environments before UAT entry; rehearse rollback in Pre-production | Northwind + Acme | Open — depends on D-01 |
| R-06 | No answer-quality baseline exists on the currently-deployed models; historical scores were produced against a retired model pair | High | Run a full Ground Truth evaluation and record it as the baseline before citing any quality figure to Acme | Northwind | Open — blocks NFR-08 sign-off |
| R-07 | Model deployments and the administrative Entra group are created outside Infrastructure-as-Code, so the templates do not fully describe the live environment | Medium | Bring both under IaC, or document them as intentionally out-of-band with a named owner | Northwind | Open |
| R-08 | A failure to acquire the ingestion certificate is logged but not alerted, so an expired certificate could degrade ACL sync silently | Medium | Add explicit alerting on certificate-acquisition failure and a scheduled validity check | Northwind | Open |
| R-09 | Cached answers within a session re-cite prior sources without re-checking current permissions. Confined to a single user's own session; not a cross-user exposure | Medium | Treat a permission change as a cache miss, or filter cached citations against current permissions before serving | Northwind | Open |
| R-10 | Configuration values in this document can drift from the live deployment between reviews | Medium | Values are re-verified against the live environment at each release review rather than carried forward; last verified 2026-08-01 | Northwind | Control in place |
| R-11 | No WCAG audit has been performed against NFR-11, and one known keyboard-access non-conformance exists | Medium | Commission an audit before go-live; remediate the citation-tooltip defect in the next release | Northwind + Acme | Open |
| R-12 | The disaster recovery procedure has not been rehearsed against the RTO in NFR-06 | Medium | Rehearse in Pre-production once provisioned; scheduled 2026-09-12 | Northwind | Open — depends on R-05 |

_Ownership note. Ten of the twelve risks above are owned solely by Northwind; R-03 and R-11 are joint because they depend on an Acme decision. Risk ownership is revisited at each review so it reflects dependency ownership where appropriate._

---

## 36. Outcomes & deliverables — `OPTIONAL`

**Purpose.** A status tracker for a project delivered and reviewed across multiple cycles. Distinct from §37 Open questions, which is about unresolved decisions rather than progress.

**How to write it.** Include for in-flight work reviewed release over release; omit for a single-issue design document. Status uses the deliverable vocabulary in §0.4. **Keep the Note column** — a bare status pill loses the "why", and the why is the only part worth reading.

**Example**

| Deliverable | Status | Note |
| --- | --- | --- |
| Deployed instance in private VNet (Development) | Done |  |
| SharePoint near-real-time sync with ACL propagation | Done |  |
| Daily ACL reconciliation | Done | Alerting gap open — see R-08 |
| ClaimCore scheduled ingestion | In progress | Rate limit unconfirmed — see R-03 |
| Chat interface with cited answers | Done |  |
| Administrative portal | Done |  |
| Administrative access control enforcement | **Not started** | **Not enforced at the API layer — see R-04** |
| Evaluation framework | In progress | Framework functional; no baseline recorded — see R-06 |
| Pre-production environment | Not started | Blocked on D-01 |
| Load test to NFR-03 | Not started | Blocked on Pre-production |
| WCAG audit | Not started | See R-11 |
| DR rehearsal | Not started | Scheduled 2026-09-12 |
| Runbooks | In progress | Six of nine written |
| End-user onboarding material | Backlog |  |

---

## 37. Open questions — `REQUIRED`

**Purpose.** Every unresolved decision, with an owner. An SDD with no open questions is either finished or dishonest.

**How to write it.** One row per question with an `OQ-xx` ID, a named owner, and a needed-by date — a question with no owner will not be answered. **Keep resolved questions in the table** with their resolution and date; a reader six months later needs to know the question was asked and how it landed. Where a resolution created a new risk, link it.

**Example**

| ID | Question | Owner | Needed by | Status / resolution |
| --- | --- | --- | --- | --- |
| OQ-01 | Should ACL reconciliation run more frequently than daily? | Acme Security + Northwind | 2026-09-01 | Open |
| OQ-02 | Is a DPIA required before go-live, and who signs it? | Acme Privacy | 2026-09-15 | Open — see §24 |
| OQ-03 | Is a Microsoft Teams interface in scope for a future phase? | Acme business sponsor | 2026-10-01 | Open — FR-11 reserved against it |
| OQ-04 | What is ClaimCore's actual API rate limit? | Acme Claims Platform | 2026-08-25 | Open — see R-03 |
| OQ-05 | Does Acme require a dedicated Ground Truth curation role, or does Claims Ops absorb it? | Acme Claims Ops | 2026-09-05 | Open — D-05 depends on this |
| OQ-06 | Is the 90-day conversation retention period acceptable to Acme Privacy? | Acme Privacy | 2026-08-30 | **Resolved 2026-08-04** — confirmed acceptable; recorded in §17 and §24 |
| OQ-07 | Can model abuse-monitoring retention be disabled for this deployment? | Northwind | 2026-05-15 | **Resolved 2026-05-02** — confirmed disabled with Microsoft; recorded in §24 |
| OQ-08 | Should the shared Graph service principal be split per feature? | Northwind | 2026-08-01 | **Resolved 2026-08-04** — split, see ADR-0007, superseding ADR-0006 |
