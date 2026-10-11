#!/usr/bin/env bash
# A business PRD that names no system, a repository whose architecture document and a code
# comment name an external billing service that produces invoices.
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
mkdir -p docs
cat > docs/architecture.md <<'MD'
# Order service architecture

The order service stores orders and lets customers export them (`app/exports.py`).

Invoices are not stored here. The billing-api service owns them; the order service only
keeps the invoice number on each order.
MD
cat > app/invoices.py <<'PY'
"""Invoice numbers on orders.

The invoice documents themselves are produced and stored by the billing-api service,
which is a separate repository.
"""


def invoice_number(order: dict) -> str | None:
    return order.get("invoice_number")
PY
cat > prd/records.md <<'MD'
# Purchase records PRD

Customers keep asking for a copy of everything they bought, for their accounts.

## Requirements

1. A customer can download all of their purchases, however many they have.
2. The download includes the invoice for each purchase.
3. A customer is told when the download is ready.
MD
