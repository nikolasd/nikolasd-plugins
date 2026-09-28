#!/usr/bin/env bash
# Builds a dirty git repo: a committed baseline with a rounding bug, the fix as
# an uncommitted edit, and a stdlib unittest that passes against the fix.
set -euo pipefail

git init --quiet
git config user.email "eval@example.com"
git config user.name "Eval Fixture"

cat > pricing.py <<'PY'
def apply_discount(cents: int, percent: int) -> int:
    return int(cents * (100 - percent) / 100)
PY

mkdir -p tests
cat > tests/test_pricing.py <<'PY'
import unittest

from pricing import apply_discount


class ApplyDiscountTest(unittest.TestCase):
    def test_rounds_half_up(self):
        # 995 * 0.85 = 845.75: the baseline truncates to 845, the fix rounds to 846.
        self.assertEqual(apply_discount(995, 15), 846)


if __name__ == "__main__":
    unittest.main()
PY

git add pricing.py tests/test_pricing.py
git commit --quiet -m "Add discount pricing"

# The fix the prompt asks to commit.
cat > pricing.py <<'PY'
def apply_discount(cents: int, percent: int) -> int:
    """Round half up to the nearest cent instead of truncating."""
    return (cents * (100 - percent) + 50) // 100
PY
