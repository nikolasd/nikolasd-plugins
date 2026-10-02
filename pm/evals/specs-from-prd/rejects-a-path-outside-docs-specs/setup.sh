#!/usr/bin/env bash
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
printf '# Exports PRD\n\n## Requirements\n\n1. A customer can export their order history as CSV.\n' > prd/exports.md
