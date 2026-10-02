#!/usr/bin/env bash
# Plants the code the prompt names plus an existing test file, so the case tests
# whether a test for the change comes first, not whether the model can find the
# code or decide where tests live.
set -euo pipefail

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

mkdir -p tests
cat > tests/test_orders.py <<'PY'
import unittest

from orders import list_orders


class ListOrdersTest(unittest.TestCase):
    def test_default_page_size_is_20(self):
        orders = [{"id": i} for i in range(50)]
        self.assertEqual(len(list_orders(orders)["items"]), 20)


if __name__ == "__main__":
    unittest.main()
PY
