#!/usr/bin/env bash
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
cat > prd/exports.md <<'MD'
# Order exports PRD

Customers need to take their order history out of the product.

## Requirements

1. A customer can export their order history as CSV from the account page.
2. A customer can schedule a weekly export that is emailed to them.
3. An admin can see an audit log of every export.

## Notes

The existing export endpoint already streams large histories.
MD
