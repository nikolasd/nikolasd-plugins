#!/usr/bin/env bash
# Shared fixture for the specs-from-prd and story-from-document spec cases: a tiny order
# service with an in-memory CSV export, plus a helper that writes a valid specs document.
# Sourced by each case's setup.sh. Every value is invented and matches no provider key format.
set -euo pipefail

build_exports_repo() {
  mkdir -p app tests prd docs/specs .claude

  cat > app/orders.py <<'PY'
"""Order storage."""

_ORDERS: dict[str, list[dict]] = {}


def list_orders(customer_id: str) -> list[dict]:
    return list(_ORDERS.get(customer_id, []))


def add_order(customer_id: str, order: dict) -> None:
    _ORDERS.setdefault(customer_id, []).append(order)
PY

  cat > app/exports.py <<'PY'
"""Order export helpers."""
from app import orders


def export_orders_csv(customer_id: str) -> str:
    """Return every order for the customer as one CSV string.

    The whole result is built in memory, so a long history is slow and heavy.
    """
    rows = ["id,total,placed_at"]
    for order in orders.list_orders(customer_id):
        rows.append(f"{order['id']},{order['total']},{order['placed_at']}")
    return "\n".join(rows)
PY

  cat > app/api.py <<'PY'
"""HTTP handlers."""
from app import exports


def get_export(customer_id: str):
    body = exports.export_orders_csv(customer_id)
    return {"status": 200, "body": body, "content_type": "text/csv"}
PY

  cat > tests/test_exports.py <<'PY'
from app import exports, orders


def test_export_has_a_header_row():
    orders.add_order("c1", {"id": "o1", "total": 10, "placed_at": "2026-01-01"})
    assert exports.export_orders_csv("c1").splitlines()[0] == "id,total,placed_at"
PY

  printf 'Order service. Run tests with `pytest`.\n' > README.md
  echo '{"project_key":"DEMO"}' > .claude/pm.json
}

# write_specs_doc [story-key]: a valid specs document. The optional argument fills the
# Story line of S-01, which locks that spec.
write_specs_doc() {
  local s01_story="${1:-}"
  cat > docs/specs/exports.md <<MD
# Order exports Specs

- **Source PRD:** prd/exports.md
- **Date:** 2026-10-02
- **Repositories:** orders-service
- **Audience and success signal:** Customers on the account page; fewer support tickets about missing order history.

## Open gaps

- S-02: [GAP: the time zone the weekly schedule runs in]

## Feature design

### Components touched

| Component | What changes | Evidence |
|---|---|---|
| Export function | Stays the source of the CSV | \`app/exports.py:5\` |
| HTTP handler | Serves the download | \`app/api.py:5\` |

### Data flow

\`\`\`mermaid
flowchart LR
  Page[Account page] --> API[app/api.py] --> Export[app/exports.py]
\`\`\`

### Decisions

#### D-01 Keep the export in the order service

- **Decision:** Exports are produced by the order service.
- **Decided by:** the user
- **Alternatives shown:** a separate export service

### Spec dependencies

\`\`\`mermaid
flowchart LR
  S01[S-01] --> S02[S-02]
\`\`\`

## Specs

### S-01 Customers download their orders as CSV

- **Status:** Ready
- **Story:** ${s01_story}
- **Repo:** orders-service
- **Depends on:** none

**User story:** As a customer, I want to download my order history as a CSV file, so that I can keep my own records.

**Scope:**

- In: a CSV download of the signed-in customer's orders from the account page.
- Out: scheduled exports and any other file format.

**Acceptance criteria:**

1. A signed-in customer can download a CSV file containing every one of their orders.
2. The first row of the file names the columns id, total and placed_at.

**Technical approach:** Reuse \`app/exports.py:5\` and expose it through the handler at \`app/api.py:5\`.

**INVEST:**

| Criterion | Verdict | Reason |
|---|---|---|
| Independent | Pass | The export function already exists. |
| Negotiable | Pass | It states the outcome, not the implementation. |
| Valuable | Pass | A customer can keep a record of their orders. |
| Estimable | Pass | The code to extend is small and clear. |
| Small | Pass | One repository and one reviewable change. |
| Testable | Pass | Both criteria can be checked by downloading the file. |

**Gaps:**

- None.

**PRD trace:** Requirement 1

### S-02 Customers schedule a weekly export by email

- **Status:** Needs decision
- **Story:**
- **Repo:** orders-service
- **Depends on:** S-01

**User story:** As a customer, I want a weekly export emailed to me, so that I do not have to remember to download it.

**Scope:**

- In: a weekly schedule that emails the CSV from S-01.
- Out: other schedules and other formats.

**Acceptance criteria:**

1. A customer can turn a weekly emailed export on and off.
2. The emailed file is the same CSV that S-01 produces.

**Technical approach:** Add a scheduled job that calls \`app/exports.py:5\`.

**INVEST:**

| Criterion | Verdict | Reason |
|---|---|---|
| Independent | Pass | It depends only on S-01, declared above. |
| Negotiable | Pass | It leaves the scheduler open. |
| Valuable | Pass | The customer receives data without asking. |
| Estimable | Pass | The open gap does not hide the size of the work. |
| Small | Pass | One repository and one reviewable change. |
| Testable | Pass | Each criterion can be checked with a test mailbox. |

**Gaps:**

- [GAP: the time zone the weekly schedule runs in]

**PRD trace:** Requirement 2

### S-03 Customers download their orders as PDF

- **Status:** Withdrawn
- **Story:**
- **Repo:** orders-service
- **Depends on:** none

Withdrawn on 2026-10-02: the PRD dropped PDF export.

## PRD findings

| Id | Claim or finding | Verdict | Evidence |
|---|---|---|---|
| F-01 | The existing export builds the whole result in memory. | TRUE | \`app/exports.py:5\` |

## Change log

| Date | Change | Specs affected |
|---|---|---|
| 2026-10-02 | Created from prd/exports.md. | S-01, S-02, S-03 |
MD
}
