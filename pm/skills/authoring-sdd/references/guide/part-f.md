<!-- Part F of the bundled SDD authoring guide. The conventions every Part relies on (ID registry, vocabularies, omission rule, evidence, diagrams, checklist) are in 00-conventions.md. -->

## Contents of this Part

- §28 Environments
- §29 Release, cutover & rollback
- §30 Testing & acceptance
- §31 Operations & support
- §32 Sizing & cost

---

# Part F — Delivery and operations

## 28. Environments — `REQUIRED`

**Purpose.** What exists, where, and what each is for.

**How to write it.** One column per environment, including ones not yet built — an environment that is planned but absent is a finding worth surfacing here rather than discovering at go-live. State the purpose and data policy of each: whether it holds production data matters more than its resource names. **Do not publish tenant, subscription or account IDs, or resource GUIDs, in a client-shared document** (§0.7); reference the internal deployed-resources page instead.

**Example**

| Attribute | Development | Pre-production | Production |
| --- | --- | --- | --- |
| Purpose | Engineering and integration | UAT, performance, security testing | Live service |
| Owner | Northwind | Acme, operated by Northwind | Acme, operated by Northwind |
| Tenant | Northwind tenant | Acme tenant | Acme tenant |
| Region | UK South | UK South | UK South |
| Data | Synthetic only; no Acme data | Anonymised subset, refreshed quarterly | Live |
| Access | Northwind engineering | Northwind engineering (PIM), Acme UAT users | PIM-eligible only, activated per session, audited |
| Deployment | On merge to `main` | On release tag, automated | On release tag, manual approval gate |
| Status | Provisioned | **Not yet provisioned — see R-05** | **Not yet provisioned** |

Resource-level identifiers are maintained in the internal deployed-resources register (REF-09), not in this document.

---

## 29. Release, cutover & rollback — `REQUIRED`

**Purpose.** How change reaches production, and how it is undone.

**How to write it.** Branching and release model, the promotion path, the approval gates, and — the part most often missing — the **verified** rollback procedure. "Redeploy the previous image" is only a rollback plan if someone has actually done it and timed it. State when it was last rehearsed. Include data migration and cutover if there is a system being replaced.

**Example**

* **Branching.** Trunk-based on `main`, short-lived feature branches, squash merge. Release tags are cut from `main`.
* **Promotion.** Merge to `main` deploys to Development automatically. A release tag deploys to Pre-production automatically and to Production behind a manual approval gate held by the Northwind Tech Lead and the Acme technical sponsor.
* **Deployment method.** Container images built in CI, pushed to the private registry, deployed by Infrastructure-as-Code. Infrastructure and application deploy through the same pipeline.
* **Downtime.** Deployment causes a brief restart, typically under 60 seconds. Blue-green is out of scope (§6); deployments are scheduled outside the availability window in NFR-05.
* **Rollback.** Redeploy the previously tagged image via the pipeline's rollback job. Measured at 6 minutes end to end. **Last rehearsed 2026-07-24 against Development; a Pre-production rehearsal is scheduled once that environment exists — see R-05.**
* **Data.** The search index is rebuildable from source and is not rolled back with the application; a schema-affecting index change is deployed as a side-by-side index with an alias flip, so rollback is an alias change.
* **Post-deployment verification.** A smoke suite runs automatically after every deployment: health, authenticated query returning a citation, indexing trigger, and an administrative endpoint returning 403 to a non-administrator. A failure triggers automatic rollback.

---

## 30. Testing & acceptance — `REQUIRED`

**Purpose.** How the solution is shown to meet §8 and §9, and how the client formally accepts it.

**How to write it.** Test levels and what each covers, coverage targets, the non-functional test approach, and the UAT process including entry and exit criteria. **Entry and exit criteria are the point** — UAT without agreed exit criteria never ends. Name the defect triage process and who arbitrates severity.

**Example**

| Level | Scope | Owner | Target |
| --- | --- | --- | --- |
| Unit | Application components, in isolation | Northwind | ≥ 80% line coverage (NFR-12) |
| Integration | Component to Azure dependency, against real services in Development | Northwind | All ingestion and retrieval paths |
| End-to-end | Browser-driven journeys covering every `Must` requirement | Northwind | 100% of `Must` requirements |
| Answer quality | Ground Truth evaluation against NFR-08 thresholds | Northwind, set curated by Acme | Every release |
| Performance | Load profile `LOAD-STD-01` to NFR-01 and NFR-03 | Northwind | Before Production go-live |
| Security | STRIDE review plus third-party penetration test | Northwind, third party | Before Production go-live |
| Accessibility | WCAG 2.2 AA audit | Third party | Before Production go-live |
| UAT | Business-scenario validation by Acme handlers | Acme Claims Ops | Per exit criteria below |

**UAT entry criteria.** Pre-production environment provisioned with an anonymised data subset; all `Must` requirements at status `Met`; smoke suite passing; UAT scenarios and test accounts agreed; defect triage process in place.

**UAT exit criteria.** Every agreed scenario executed; zero open Critical or High defects; Medium defects either fixed or accepted in writing by the Acme sponsor with an agreed remediation date; the answer-quality baseline recorded against NFR-08; sign-off recorded in §1.

**Defect management.** Defects are raised in the shared tracker with a severity proposed by the raiser. Severity disputes are arbitrated jointly by the Northwind Tech Lead and the Acme technical sponsor. Critical and High defects block the exit criteria; they are not negotiable at the point of sign-off.

---

## 31. Operations & support — `REQUIRED`

**Purpose.** How the solution is run once it is live, and by whom. This section is the difference between delivering a system and delivering a service.

**How to write it.** Cover monitoring and alerting with actual thresholds, backup and restore with a rehearsal date, disaster recovery against the RTO/RPO in §9, the support model with response targets, and where runbooks live. **An untested restore is not a backup, and an unrehearsed DR plan is not a plan** — state the rehearsal dates honestly.

**Example**

**Monitoring & alerting**

| Signal | Threshold | Action |
| --- | --- | --- |
| API availability | < 99.5% over 1 hour | Page on-call |
| Answer latency p95 | 12s over 15 minutes (NFR-01) | Alert engineering channel |
| Indexing failure rate | 5% over 1 hour | Alert engineering channel |
| ACL reconciliation job | No successful run in 26 hours | Page on-call — this backs Success Criterion 2 |
| Model throttling (429) | Any sustained occurrence over 5 minutes | Alert engineering channel |
| Certificate expiry | 30 days before expiry | Ticket raised automatically |
| Monthly cost | 110% of forecast | Alert Tech Lead and Acme sponsor |

**Backup & restore.** Cosmos DB continuous backup with 7-day point-in-time restore. Azure SQL automated backup, 14-day retention. Blob Storage soft-delete at 30 days with versioning. The search index is not backed up — it is rebuildable from source in approximately 3 hours, which is what makes the NFR-06 index RPO acceptable. **Restore rehearsed 2026-07-30 for Cosmos DB and Azure SQL; both met RTO.**

**Disaster recovery.** Regional failure recovery is a redeploy from Infrastructure-as-Code into the paired region plus a restore from backup, against RTO 4 hours (NFR-06). **Not yet rehearsed — scheduled 2026-09-12, see R-12.**

**Support model**

| Tier | Responsibility | Hours | Response target |
| --- | --- | --- | --- |
| Tier 1 | Acme service desk — user access, usage questions | Acme business hours | Per Acme's internal SLA |
| Tier 2 | Northwind engineering — application defects, indexing failures | 08:00–18:00 UK, business days | 4 business hours |
| Tier 3 | Northwind engineering on-call — Critical incidents | 24×7 for Critical only | 1 hour |

**Runbooks.** Held alongside the source repository and linked from REF-10. Runbooks exist for: failed indexing, ACL reconciliation failure, model throttling and failover, certificate rotation, index rebuild, and rollback.

---

## 32. Sizing & cost — `REQUIRED`

**Purpose.** What the solution costs to run and what drives that cost up.

**How to write it.** Current sizing per component, the monthly run-rate estimate, the variable cost drivers, and what bounds spend. **Date the estimate and state its assumptions** — pricing and volume assumptions change, and an undated estimate is quoted back at you a year later. Where an estimate has been invalidated by a change, say it is superseded rather than leaving the old figure standing.

**Example**

**Fixed monthly cost — estimate dated 2026-08-01, at current list pricing**

| Component | Sizing | Indicative monthly |
| --- | --- | --- |
| App Service Plan | `P1v3`, 2 instances, autoscale to 4 | \[value\] |
| Azure AI Search | `Standard S1`, 2 replicas, 1 partition | \[value\] |
| Cosmos DB | Autoscale 4000 RU/s | \[value\] |
| Azure SQL | General Purpose, 2 vCore | \[value\] |
| Functions | Elastic Premium `EP1` | \[value\] |
| Storage, Key Vault, networking | — | \[value\] |

**Variable cost drivers.** Model generation and embedding tokens (scales with query volume and retrieval depth), Document Intelligence pages (scales with corpus growth and re-indexing), and Cosmos RU consumption (scales with concurrent sessions).

**Assumptions behind the estimate.** 120 active handlers, 25 queries per handler per week, a 40,000-document corpus growing 3% monthly, and retrieval depth per NFR-02. A change in retrieval depth or a second-pass rate above 20% materially changes the generation cost.

**Cost controls.** A budget alert fires at 110% of forecast (§31). Retrieval depth and the reranking pass are configurable without deployment, giving a direct cost lever. **A model change invalidates this estimate; reissue it rather than adjusting it.**
