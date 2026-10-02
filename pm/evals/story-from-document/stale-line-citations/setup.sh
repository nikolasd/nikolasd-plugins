#!/usr/bin/env bash
set -euo pipefail
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/exports-repo.sh"
build_exports_repo
write_specs_doc
python3 - <<'PY'
from pathlib import Path
p = Path("app/exports.py")
p.write_text('# moved down by a refactor' + '\n' * 10 + p.read_text().split('\n', 1)[1])
PY
