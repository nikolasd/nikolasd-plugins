#!/usr/bin/env bash
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
cat > prd/exports.md <<'MD'
# Order exports PRD

Customers need to take their order history out of the product.

## Requirements

1. Customers can export their orders as CSV or PDF, schedule a weekly export that is emailed to them, and an admin can see an audit log of every export.
MD
