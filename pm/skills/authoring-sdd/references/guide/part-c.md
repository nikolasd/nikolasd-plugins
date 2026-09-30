<!-- Part C of the bundled SDD authoring guide. The conventions every Part relies on (ID registry, vocabularies, omission rule, evidence, diagrams, checklist) are in 00-conventions.md. -->

## Contents of this Part

- §8 Functional requirements
- §9 Non-functional requirements
- §10 Traceability

---

# Part C — Requirements

## 8. Functional requirements — `REQUIRED`

**Purpose.** What the system does, expressed so it can be built, tested, and signed off.

**How to write it.** One row per requirement. Acceptance criteria in given/when/then form — a requirement without a testable acceptance criterion is a wish. Priority uses MoSCoW exactly (§0.4); status uses the requirement status vocabulary exactly. **Status lives in the Status column** — never in Priority and never in Stakeholders. An unmet `Must` carries its risk reference in the Status cell. Reserve the ID range up front.

**Example**

| ID | Category | Requirement | Acceptance criteria | Priority | Stakeholders | Status |
| --- | --- | --- | --- | --- | --- | --- |
| FR-01 | Retrieval | Handlers submit natural-language questions and receive grounded, source-cited answers | Given a question about indexed content, when submitted via the chat interface, then the response cites at least one retrieved source document | Must | Acme handlers | Met |
| FR-02 | Permissions | Retrieval respects the querying handler's document-level access | Given a handler without access to a policy wording, when they ask a related question, then that document is excluded from retrieved context and from citations | Must | Acme handlers, Acme Security | Met |
| FR-03 | Document management | Administrators upload, list, search, and delete documents | Given an administrator session, when a PDF or Word file is uploaded, then it is queued for indexing and appears in the document list with an indexing status | Must | Acme administrators | Met |
| FR-04 | Access control | Administrative functions are restricted to a designated Entra ID group | Given a user outside the administrative group, when they call an administrative endpoint, then the request is rejected with 403 | Must | Acme Security | **Not met — see R-04** |
| FR-05 | Evaluation | Administrators run on-demand evaluations against the Ground Truth set and view per-question and summary scores | Given an evaluation run request, when executed, then per-question Groundedness, Relevance, and Similarity scores are recorded and retrievable | Must | Acme Claims Ops | In build |
| FR-06 | Feedback | Handlers rate individual answers with an optional comment | Given an answer, when a handler submits feedback, then it is recorded against that specific interaction and surfaces in reporting | Should | Acme handlers | Met |
| FR-07 | Reporting | Administrators view usage, adoption, and feedback trends | Given an administrator session, when the reporting view is opened, then query volume, active users, and feedback sentiment are displayed for a selectable range | Should | Acme Claims Ops | In build |
| FR-08 | Ingestion | SharePoint content changes are detected and indexed without manual intervention | Given a document added, updated, or deleted in a monitored library, when the change notification is received, then the index reflects it within 15 minutes | Must | Acme handlers | Met |
| FR-09 | Ingestion | ClaimCore claim notes are ingested on a defined schedule | Given a scheduled ingestion run, when new or changed notes are found, then they enter the same indexing pipeline as SharePoint content | Must | Acme handlers | In build |
| FR-10 | Administration | Optional features are enabled and disabled without a code deployment | Given a feature-flag change, when applied, then the corresponding functionality changes availability without a service restart | Should | Acme administrators | Met |
| FR-11 | _Reserved_ | _(reserved — pending resolution of OQ-03, multi-channel interface)_ |  |  |  | Reserved |
| FR-12 | _Reserved_ | _(reserved)_ |  |  |  | Reserved |

---

## 9. Non-functional requirements — `REQUIRED`

**Purpose.** The qualities the system must hold, with numbers. An NFR without a threshold is not a requirement.

**How to write it.** Work through the category checklist below and consciously decide each one — record "Not applicable — reason" rather than silently dropping a category. Where a threshold has not yet been agreed with the client, state the proposed value, mark it unagreed, and raise an `OQ-xx`. Never encode that state in the Priority column.

**Category checklist.** Cover or explicitly dismiss each: Performance · Capacity & throughput · Availability · Recoverability (RTO/RPO) · Scalability · Security · Privacy & data protection · Data residency · Interoperability · Maintainability · Observability · Accessibility · Portability · Compliance · Localisation.

**Example**

| ID | Category | Requirement | Acceptance criteria / threshold | Priority | Stakeholders | Status |
| --- | --- | --- | --- | --- | --- | --- |
| NFR-01 | Performance | End-to-end answer latency | p95 < 12s for a standard query, measured at the API boundary over a rolling 7 days | Must | Acme, Northwind | Agreed |
| NFR-02 | Performance | Retrieval depth | 10 retrieved chunks per query by default, with a second retrieval pass when relevance scoring falls below 0.6 | Must | Northwind | Agreed |
| NFR-03 | Capacity | Concurrent users | 120 concurrent handlers sustained without latency breach of NFR-01 | Must | Acme | **Proposed — not yet load-tested, see R-02** |
| NFR-04 | Capacity | Upload size | 25MB per manually uploaded document, enforced server-side | Must | Acme administrators | Met |
| NFR-05 | Availability | Service availability | 99.5% monthly, business hours 07:00–19:00 UK, excluding agreed maintenance windows | Must | Acme | Agreed |
| NFR-06 | Recoverability | RTO / RPO | RTO 4 hours; RPO 24 hours for the index (rebuildable from source), 1 hour for conversation and feedback data | Must | Acme | Agreed |
| NFR-07 | Security | Authentication | All end-user access requires a valid Entra ID token; no anonymous surface exists in any environment | Must | Acme Security | Met |
| NFR-08 | Quality | Evaluation thresholds | Groundedness ≥ 0.85, Relevance ≥ 0.80, Similarity ≥ 0.75 against the Ground Truth set | Must | Acme, Northwind | **Not met — no baseline recorded on current models, see R-06** |
| NFR-09 | Data residency | Processing location | All storage, compute, and model inference occurs within the UK South region | Must | Acme | Agreed |
| NFR-10 | Observability | Traceability | Every served answer is reconstructable from telemetry: query, retrieved source IDs, model, latency, and outcome | Must | Northwind | In build |
| NFR-11 | Accessibility | Conformance | WCAG 2.2 Level AA for the handler-facing interface | Should | Acme | **Proposed — no audit performed, see R-11** |
| NFR-12 | Maintainability | Test coverage | ≥ 80% line coverage on application components; ≥ 60% on infrastructure automation | Should | Northwind | In build |

---

## 10. Traceability — `REQUIRED`

**Purpose.** Closes the loop from requirement to design to test to acceptance. This is what a client audit asks for and what a delivery team quietly needs.

**How to write it.** If traceability is maintained in a tracker, say so and link it — do not duplicate a live tracker into a static page. Otherwise, keep a compact matrix here. Either way, every `Must` requirement must appear.

**Example**

Traceability is maintained in Jira; the authoritative view is the `Acme Claims Assistant / Requirements` filter (REF-07). Summary at last issue:

| Requirement | Design reference | Verified by | Status |
| --- | --- | --- | --- |
| FR-01 | §14 L2, §16 User Query pipeline | `TEST-QA-01`…`TEST-QA-06`, UAT-01 | Met |
| FR-02 | §16 Ingestion pipeline, §23 Access matrix | `TEST-SEC-04`, UAT-07 | Met |
| FR-04 | §23 Access matrix | `TEST-SEC-11` | **Failing — R-04** |
| NFR-01 | §18 Technology stack | Load profile `LOAD-STD-01` | Agreed, not yet executed |
| NFR-06 | §31 Operations & support | DR rehearsal `DR-01`, scheduled 2026-09-12 | Not started |
