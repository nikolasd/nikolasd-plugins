#!/usr/bin/env bash
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
printf '# Exports\n\nMake exports better. Customers have complained.\n' > prd/exports.md
