#!/usr/bin/env bash
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
cat > prd/exports.md <<'MD'
# Order exports PRD

Customers need to take their order history out of the product.

## Requirements

1. A customer can export their order history as a file from the account page.
2. Exports are kept for a retention period and then deleted.
MD
