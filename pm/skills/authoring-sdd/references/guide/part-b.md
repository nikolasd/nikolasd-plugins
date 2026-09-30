<!-- Part B of the bundled SDD authoring guide. The conventions every Part relies on (ID registry, vocabularies, omission rule, evidence, diagrams, checklist) are in 00-conventions.md. -->

## Contents of this Part

- §3 At a glance
- §4 Business problem & goals
- §5 Glossary & ubiquitous language
- §6 Scope & assumptions
- §7 Success criteria

---

# Part B — Context and scope

## 3. At a glance — `REQUIRED`

**Purpose.** One paragraph a busy executive or a new joiner can read in thirty seconds and be broadly correct about the system.

**How to write it.** Three to five sentences. Who uses it, what it does, what it runs on, why it matters. No acronyms that §5 has not defined. **Write this section last** — it is a summary of the finished document, not an opening guess.

**Example**

> Acme Claims Assistant lets claims handlers query policy wordings, regulatory guidance, and historical claim notes in natural language and receive accurate, source-cited answers grounded in retrieved content. Content is drawn from Acme's SharePoint Online libraries and the ClaimCore claims system, indexed continuously, and served through a retrieval-augmented generation pipeline deployed inside a private Azure network peered to Acme's environment. An administrative portal supports document management, answer-quality evaluation, and usage reporting. The solution enforces document-level access control so a handler only ever sees content their existing permissions already allow.

---

## 4. Business problem & goals — `REQUIRED`

**Purpose.** Anchors every later technical decision to a business reason. If a component cannot be traced back to a line in this section, ask why it is being built.

**How to write it.** State the problem as it exists today, without reference to the solution. Then the goal, then what measurable change counts as success. Keep it short — three to six bullets. Detail belongs in §6.

**Example**

* Claims handlers spend a material share of each case searching policy wordings and regulatory guidance spread across SharePoint libraries and the ClaimCore notes field; answers are inconsistent between handlers and hard to evidence at audit.
* **Goal:** answers that are accurate, source-cited, and strictly scoped to what the querying handler is already permitted to see.
* **Success looks like:** handlers reach a correct, attributable answer faster than by manual search, with answer quality measured against an agreed evaluation baseline rather than asserted.

---

## 5. Glossary & ubiquitous language — `REQUIRED`

**Purpose.** One shared vocabulary. This is the section that stops the client and the delivery team meaning different things by the same word for six months.

**How to write it.** Every domain term, product term, and abbreviation used anywhere in the document. Client-side business terms matter more than technology acronyms — define "reserve", not "HTTP". Where the client's word and the system's word differ, record both and pick one for the rest of the document.

**Example**

| Term | Meaning |
| --- | --- |
| Claim note | A free-text case record entered in ClaimCore by a handler. The system indexes these; it never writes them. |
| Handler | An Acme claims employee. The primary end user. Called "adjuster" in some Acme documents; this document uses "handler" throughout. |
| Policy wording | The contractual document defining cover. Held in SharePoint, version-controlled by Acme Legal. |
| Grounding | The property of an answer being supported by retrieved source content rather than model recall. |
| RAG | Retrieval-augmented generation — retrieving relevant content and supplying it to a language model as context. |
| Ground Truth set | The curated question/answer pairs used to score answer quality. |
| ACL | Access control list — the per-document permission set the system replicates from SharePoint into the search index. |

---

## 6. Scope & assumptions — `REQUIRED`

**Purpose.** The boundary of the engagement, and everything being taken on trust. This section prevents more disputes than any other.

**How to write it.** Four blocks. **In scope** and **Out of scope** are plain bullets — be blunt in Out of scope, including the near-misses a client might reasonably assume are included. **Assumptions** carry `A-xx` IDs; group them under sub-headings once they pass about six. **Dependencies** carry `D-xx` IDs plus a named owner and impact-if-blocked; a dependency with no named owner is not a dependency, it is a hope.

**Example**

**In scope**

* Natural-language Q&A over SharePoint policy wordings and ClaimCore claim notes, with source citation on every answer.
* Permission-aware retrieval via SharePoint ACL propagation into the search index.
* Administrative portal: document upload, deletion, indexing status, and search.
* On-demand answer-quality evaluation against a Ground Truth set.
* Usage and adoption reporting via administrative endpoints.
* Deployment automation via Infrastructure-as-Code, with environment separation.

**Out of scope**

* Write-back of any kind into ClaimCore. The integration is read-only.
* Automated claims decisioning, reserve setting, or any recommendation that constitutes a claims decision.
* Interpretation of images or scanned diagrams beyond OCR text extraction.
* Zero-downtime deployment infrastructure. Verified rollback of a prior release **is** in scope; blue-green hot-swap is not.
* Mobile applications; the interface is browser-based only.

**Assumptions**

_Environment & access_

| ID | Assumption |
| --- | --- |
| A-01 | SharePoint Online is the authoritative store for policy wordings; Acme maintains its folder structure and file-level permissions, and the system treats them as the source of truth for access control. |
| A-02 | Microsoft Entra ID is the identity provider for all end users. |
| A-03 | All application services run inside a private Azure virtual network, peered as a Spoke to Acme's Hub; on-premises connectivity is available via ExpressRoute. |
| A-04 | Northwind engineer access to Acme's tenant is Privileged Identity Management eligible-only, activated per session, not standing. |

_Ingestion & processing_

| ID | Assumption |
| --- | --- |
| A-05 | Document changes are delivered via Microsoft Graph webhook for near-real-time content sync. Permission changes are **not** delivered by webhook and are reconciled by a scheduled batch job. |
| A-06 | Re-indexing is rollback-safe: the prior version of a document stays retrievable until its replacement is fully indexed. |
| A-07 | Source documents are predominantly English; no translation layer is required in this phase. |

**Dependencies**

| ID | Dependency | Owner | Impact if blocked |
| --- | --- | --- | --- |
| D-01 | Azure subscription and resource-group provisioning | Acme IT | No environment can be stood up; all delivery stalls. |
| D-02 | VNet peering, DNS delegation, on-premises routing | Acme Networking | The solution cannot reach ClaimCore or resolve hub resources. |
| D-03 | Entra ID group provisioning for administrative access control | Acme Identity | Administrative access control cannot be enforced — see R-04. |
| D-04 | ClaimCore read API credentials and rate-limit agreement | Acme Claims Platform | No claim-note content is ingested; scope reduces to policy wordings only. |
| D-05 | Ground Truth question set authored by Acme subject-matter experts | Acme Claims Ops | Answer quality cannot be measured; NFR-08 cannot be evidenced. |

---

## 7. Success criteria — `REQUIRED`

**Purpose.** The checkable list of what "shipped correctly" means. Distinct from §4 Goals, which are directional, and from §36 Outcomes, which is a status tracker.

**How to write it.** Numbered, measurable, and verifiable — each one must be something a person could test and get a yes or no. Where a criterion is qualified or not yet baselined, say so in the criterion itself and reference the risk. Six to eight is a healthy number.

**Example**

1. **Answer grounding** — every answer cites at least one retrieved source document, and cited content is retrievable by the reader.
2. **Permission enforcement** — retrieval is strictly limited to documents the querying handler can already access in SharePoint, with revoked access reflected within 24 hours. _(This governs newly-retrieved content; see R-09 for the cached-answer caveat.)_
3. **Answer quality thresholds** — Groundedness, Relevance, and Similarity scores meet the thresholds agreed in NFR-08 against the Ground Truth set. **No baseline exists on the currently-deployed models — see R-06.**
4. **Sync reliability** — SharePoint content changes are reflected in the index within 15 minutes; permission changes within 24 hours.
5. **Administrative operability** — administrators manage documents, run evaluations, and view reporting without Northwind engineering involvement.
6. **Auditability** — every answer served is reconstructable from logs: query, retrieved sources, and response, retained per the policy in §24.
