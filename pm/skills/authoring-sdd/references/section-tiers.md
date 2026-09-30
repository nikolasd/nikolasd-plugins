# The Template's 37 sections, by Part and tier

Hold this table through the whole run; it is stable for the bundled Template
v2.0 and saves re-deriving Part groupings from the fetched markdown each time.
It applies only to the bundled template: when `sdd_template` is configured,
derive the sections, Parts and tiers from that template instead.

| # | Section | Part | Tier |
|---|---|---|---|
| 1 | Document control | A — Document control | REQUIRED |
| 2 | References & related documents | A — Document control | REQUIRED |
| 3 | At a glance | B — Context and scope | REQUIRED |
| 4 | Business problem & goals | B — Context and scope | REQUIRED |
| 5 | Glossary & ubiquitous language | B — Context and scope | REQUIRED |
| 6 | Scope & assumptions | B — Context and scope | REQUIRED |
| 7 | Success criteria | B — Context and scope | REQUIRED |
| 8 | Functional requirements | C — Requirements | REQUIRED |
| 9 | Non-functional requirements | C — Requirements | REQUIRED |
| 10 | Traceability | C — Requirements | REQUIRED |
| 11 | Solution overview | D — Solution architecture | REQUIRED |
| 12 | Domain overview | D — Solution architecture | OPTIONAL |
| 13 | Architecture — C4 L1: System Context | D — Solution architecture | REQUIRED |
| 14 | Architecture — C4 L2: Container | D — Solution architecture | REQUIRED |
| 15 | Architecture — C4 L3: Component | D — Solution architecture | CONDITIONAL |
| 16 | Process pipelines & sequence diagrams | D — Solution architecture | CONDITIONAL |
| 17 | Data design | D — Solution architecture | CONDITIONAL |
| 18 | Technology stack & rationale | D — Solution architecture | REQUIRED |
| 19 | Interfaces & endpoints | D — Solution architecture | CONDITIONAL |
| 20 | Models & schemas | D — Solution architecture | CONDITIONAL |
| 21 | Integrations & external dependencies | D — Solution architecture | REQUIRED |
| 22 | Cross-cutting policy | E — Cross-cutting concerns | REQUIRED |
| 23 | Security & identity | E — Cross-cutting concerns | REQUIRED |
| 24 | Compliance & data protection | E — Cross-cutting concerns | CONDITIONAL |
| 25 | Responsible AI | E — Cross-cutting concerns | CONDITIONAL |
| 26 | Model & platform lifecycle | E — Cross-cutting concerns | CONDITIONAL |
| 27 | Accessibility | E — Cross-cutting concerns | CONDITIONAL |
| 28 | Environments | F — Delivery and operations | REQUIRED |
| 29 | Release, cutover & rollback | F — Delivery and operations | REQUIRED |
| 30 | Testing & acceptance | F — Delivery and operations | REQUIRED |
| 31 | Operations & support | F — Delivery and operations | REQUIRED |
| 32 | Sizing & cost | F — Delivery and operations | REQUIRED |
| 33 | Key decisions | G — Decisions, risks and open items | REQUIRED |
| 34 | Architecture Decision Records | G — Decisions, risks and open items | REQUIRED |
| 35 | Risks, dependencies & constraints | G — Decisions, risks and open items | REQUIRED |
| 36 | Outcomes & deliverables | G — Decisions, risks and open items | OPTIONAL |
| 37 | Open questions | G — Decisions, risks and open items | REQUIRED |

`CONDITIONAL` triggers are stated in the Template next to each section (for
example, §17 Data design triggers on "the solution persists data"); read the
fetched Template for the exact trigger wording each run rather than
memorizing it, since triggers are the one thing worth re-reading verbatim.
