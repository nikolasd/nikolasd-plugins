#!/usr/bin/env bash
# The order-service fixture plus a valid specs document (S-01 Ready, S-02 Needs decision, S-03 Withdrawn).
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
write_specs_doc
