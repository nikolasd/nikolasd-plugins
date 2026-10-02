#!/usr/bin/env bash
# The order-service fixture, whose .claude/pm.json names the project DEMO, plus a brief.
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
cat > brief.md <<'MD'
# Export size limit

The order export in app/exports.py builds the whole CSV in memory, so a customer with a long
history makes the service slow. Make the maximum number of exported orders configurable.
MD
