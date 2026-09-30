<!-- Part E of the bundled SDD authoring guide. The conventions every Part relies on (ID registry, vocabularies, omission rule, evidence, diagrams, checklist) are in 00-conventions.md. -->

## Contents of this Part

- §22 Cross-cutting policy
- §23 Security & identity
- §24 Compliance & data protection
- §25 Responsible AI
- §26 Model & platform lifecycle
- §27 Accessibility

---

# Part E — Cross-cutting concerns

## 22. Cross-cutting policy — `REQUIRED`

**Purpose.** The policies that apply across the whole system rather than to one component.

**How to write it.** Start from the table below — it is the minimum concern set, not a menu. Fill every row. **Promote a row to its own prose subsection** whenever it carries an open caveat, an unresolved recommendation, more than one mechanism, or more than two or three sentences of genuine nuance. A caveat compressed into a table cell until it disappears is a silent regression, and the whole point of promotion is to stop that happening.

**Example**

| Concern | Policy |
| --- | --- |
| Authentication | End users authenticate via Entra ID OAuth2 bearer tokens. Service-to-service calls use managed identity. Ingestion uses a certificate-backed service principal — see the promoted subsection below. |
| Authorisation | Role-based; see the access matrix in §23. |
| Secrets management | All secrets in Azure Key Vault, referenced rather than copied. No secrets in configuration files, container images, or source control. Managed identity access only; no access policies. |
| Data & retention | Per the retention column in §17. A formal retention policy is agreed with Acme and reviewed annually. |
| Encryption | TLS 1.2+ in transit on every hop; platform-managed encryption at rest on all stores. |
| Observability | Application Insights on all services with distributed tracing; alert rules per §31. |
| Networking | All services inside a private VNet peered as a Spoke to Acme's Hub. Every PaaS dependency reached through a Private Endpoint with a Private DNS Zone. No service is publicly addressable. |
| Scaling & cost | See §32. |
| Supply chain | Dependencies scanned for vulnerabilities and licence compliance in CI; builds fail on a forbidden licence or a high-severity advisory without a recorded exception. |
| Business continuity | See §31. |

### Authentication & authorisation _(promoted — two mechanisms plus an unresolved item)_

Two mechanisms exist: the primary Entra ID bearer-token flow for end users, and a certificate-backed service principal used by the ingestion service for Graph and SharePoint calls. The certificate is held in Key Vault and rotates annually; **no automated alert currently fires on a failed certificate acquisition — see R-08.** Administrative authorisation is defined in §23 but **is not yet enforced at the API layer — see R-04, the highest-severity open item in this document.**

---

## 23. Security & identity — `REQUIRED`

**Purpose.** Who can do what, and what has been done to establish that the design is sound.

**How to write it.** Two parts. **(a) An access matrix** — roles against capabilities, with the enforcement point named for each. Filling this in is frequently the moment an unenforced authorisation boundary becomes visible; that is the section working correctly. **(b) A threat-model reference** — link the assessment, name the method, and state the date. If no threat model has been performed, say so plainly and raise a risk; do not leave the reader to infer it.

**Example**

**Access matrix**

| Capability | Handler | Administrator | Service identity | Enforcement point |
| --- | --- | --- | --- | --- |
| Ask a question | Yes | Yes | No | Bearer token validation, API middleware |
| Retrieve a document's content | Only where SharePoint grants access | Only where SharePoint grants access | No | Query-time security filter on the search index |
| Download a source document | Only where SharePoint grants access | Same | No | Server-side token validation on the download route |
| Upload or delete a document | No | Yes | No | **Intended: Entra group check. Not currently enforced — R-04** |
| Run an evaluation | No | Yes | No | **Intended: Entra group check. Not currently enforced — R-04** |
| View usage reporting | No | Yes | No | **Intended: Entra group check. Not currently enforced — R-04** |
| Read SharePoint ACLs | No | No | Yes | Certificate-backed service principal, scoped via `Sites.Selected` |
| Write to the search index | No | No | Yes | Managed identity, index contributor role |

**Threat model.** STRIDE assessment performed 2026-06-18, covering the ingestion path, the retrieval path, and the administrative surface (REF-08). Six findings raised; four closed, two carried as R-04 and R-09. Reassessment is due on any change to the authentication model or the addition of an externally-reachable surface.

**Least privilege note.** Service principal permissions are reviewed at each release. Where a shared credential serves more than one feature, the union of its permissions is recorded and justified — an over-broad shared credential is a finding, not a convenience.

---

## 24. Compliance & data protection — `CONDITIONAL`

**Trigger.** Required whenever the solution processes personal data, regulated data, or client-confidential content — which is most customer projects.

**How to write it.** State the regulatory position that applies to your jurisdiction and sector (for example GDPR or HIPAA), the legal basis for processing if personal data is processed, the data classification, residency commitments, and the status of any required assessment (for example a data protection impact assessment, a security review, or a penetration test). Name the accountable party on the client side. Where an assessment has not been done, that is a finding with an owner and a date, not a blank.

**Example**

* **Data classification.** Policy wordings and claim notes are Acme Confidential. Claim notes contain personal data relating to policyholders and third parties.
* **Lawful basis.** Acme is the data controller; Northwind acts as processor under the data processing agreement executed 2026-03-30. Processing is on the basis of Acme's legitimate interest in claims handling.
* **Residency.** All storage, compute, and model inference occurs in UK South (NFR-09). No data leaves the region, including for model inference.
* **Sub-processors.** Microsoft Azure is the only sub-processor. Azure OpenAI operates without human review of prompts and with abuse-monitoring data retention disabled for this deployment; confirmed with Microsoft on 2026-05-02.
* **DPIA.** Required by Acme's privacy office given the presence of personal data in claim notes. **Not yet complete — owner Acme Privacy, target 2026-09-15. See OQ-02.**
* **Penetration test.** Scheduled for 2026-09-22 against the pre-production environment; go-live is gated on a clean report with no unresolved High findings.
* **Right to erasure.** Handler conversation data is purged on a 90-day rolling basis and can be purged on demand by session or user identifier. Indexed content is derived from Acme's own systems; erasure of source content propagates on the next sync.

---

## 25. Responsible AI — `CONDITIONAL`

**Trigger.** Required whenever the solution uses generative AI or automated decision-making.

**How to write it.** Cover what the model is and is not permitted to do, content filtering at both platform and application layer, grounding and hallucination controls, human oversight, evaluation approach, and known limitations stated honestly. Where the application performs its own screening, list the exact categories — an undocumented refusal category will eventually refuse something legitimate, and nobody will know why. State plainly what the system must never be used for.

**Example**

* **Permitted use.** The assistant retrieves and summarises existing content with citations. It is a research aid for handlers.
* **Prohibited use.** It does not make or recommend claims decisions, set reserves, or produce customer-facing correspondence. Every answer surfaces its sources so the handler remains the decision-maker. This boundary is stated in the interface and in onboarding material.
* **Platform content filtering.** An Azure content-filtering policy is provisioned in Infrastructure-as-Code at the default severity thresholds for hate, sexual, violence, and self-harm categories, applied to both prompt and completion. Verified against the live resource on 2026-08-01.
* **Application screening.** Queries are screened for three categories before retrieval: `OUT_OF_DOMAIN`, `PERSONAL_DATA_REQUEST`, and `DECISION_REQUEST` (asking the system to decide a claim). Screened queries return a refusal explaining which category applied. These map to the `ScreeningOutcome` enumeration in §20.
* **Grounding.** Answers are generated only from retrieved content. Where retrieval returns nothing above the relevance threshold, the system states that it has no supporting content rather than answering from model recall.
* **Human oversight.** Every answer is attributable to its sources and every interaction is logged. Handlers may flag an answer, and flagged answers feed the evaluation set.
* **Evaluation.** Answer quality is measured against a Ground Truth set curated by Acme Claims Ops, on the thresholds in NFR-08. Scores are comparable only within the same model generation; a model change invalidates the baseline and requires re-baselining before any quality claim is made.
* **Known limitations.** The system does not interpret diagrams or scanned tables beyond OCR text. It cannot reason across documents a handler cannot see, which means two handlers may correctly receive different answers to the same question.

---

## 26. Model & platform lifecycle — `CONDITIONAL`

**Trigger.** Required whenever the solution depends on a vendor-versioned model or a service with a published retirement schedule.

**How to write it.** This is a standing operational obligation, not a one-time fact. Record current versions, their published retirement dates, who tracks them, and what a migration requires. State explicitly whether a version change invalidates anything downstream — an embedding model change usually means re-indexing the entire corpus, which is a project, not a patch.

**Example**

| Component | Current version | Retirement | Tracked by | Migration impact |
| --- | --- | --- | --- | --- |
| Generation model | `gpt-5-mini` | Per Microsoft's published schedule; reviewed monthly | Northwind Tech Lead | Prompt revalidation and a fresh evaluation baseline required; no re-indexing |
| Embedding model | `text-embedding-3-large` | Per Microsoft's published schedule | Northwind Tech Lead | **Full corpus re-embedding and index rebuild** — treat as a scheduled project, not a patch |
| Document Intelligence | `2024-11-30` GA API | Per Microsoft's published schedule | Northwind Tech Lead | Extraction output may shift; spot-check a sample corpus before cutover |

**Standing obligation.** Model retirement dates are reviewed at each monthly service review and recorded in the review minutes. A retirement inside 90 days is raised as a risk with a migration plan.

---

## 27. Accessibility — `CONDITIONAL`

**Trigger.** Required whenever the solution has a human-facing interface.

**How to write it.** State the conformance target, the audit status, and any known non-conformance. An unaudited interface is not the same as a conformant one — say which you mean. Include language and localisation, which is a conformance matter, not a nicety, when the content and the interface are in different languages.

**Example**

Target: WCAG 2.2 Level AA (NFR-11). **No formal audit has been performed — see R-11.**

Implemented: semantic landmark structure, keyboard navigation through the full chat and administrative flows, visible focus indicators, and a 4.5:1 minimum contrast ratio in both themes. Streaming answers are announced through an ARIA live region.

Known non-conformance: source-citation tooltips are not reachable by keyboard alone (SC 2.1.1). Remediation scheduled for the next release.

Localisation: interface and content are both English, so SC 3.1.1 is met. If Acme extends the corpus to non-English content, a localisation framework becomes a conformance requirement rather than an enhancement.
