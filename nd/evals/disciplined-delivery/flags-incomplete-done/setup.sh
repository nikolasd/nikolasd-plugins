#!/usr/bin/env bash
# Plants a spec and an implementation that meets two of its three acceptance
# criteria. Without these on disk, a model correctly asks where the work is
# instead of checking it against the spec — the empty-sandbox bug described in
# nd/evals/README.md.
set -euo pipefail

cat > SPEC.md <<'MD'
# Orders list pagination

## Acceptance criteria
1. Default page size is 20.
2. Each response includes a `next_cursor` when more results exist.
3. A caller-supplied `page_size` above 100 is capped at 100.
MD

cat > orders.py <<'PY'
DEFAULT_PAGE_SIZE = 20


def list_orders(orders: list[dict], cursor: int = 0, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    page = orders[cursor:cursor + page_size]
    next_index = cursor + page_size
    result = {"items": page}
    if next_index < len(orders):
        result["next_cursor"] = next_index
    return result
PY
