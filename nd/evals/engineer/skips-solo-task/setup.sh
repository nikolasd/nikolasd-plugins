#!/usr/bin/env bash
# Without this, the sandbox is an empty directory with no search endpoint to
# edit, so a model correctly asks where the code lives instead of implementing
# — same shape as handoff-guards-non-git's original bug (see nd/evals/README.md).
# That's not the near-miss behaviour this case means to test, so plant a
# minimal target matching the prompt's narrative.
set -euo pipefail

mkdir -p search

cat > search/handler.py <<'PY'
def search(query: str) -> list[dict]:
    """Handles a search-results request. Hits the index on every call — no
    caching layer yet."""
    return _query_index(query)
PY
