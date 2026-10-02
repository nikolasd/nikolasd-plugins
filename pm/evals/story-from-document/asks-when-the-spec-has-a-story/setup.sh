#!/usr/bin/env bash
# The same fixture, but S-01 already records a Jira Story, which locks it.
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
write_specs_doc DEMO-12
