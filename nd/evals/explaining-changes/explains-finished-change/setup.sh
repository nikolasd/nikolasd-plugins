#!/usr/bin/env bash
# Builds a small Python repo with a finished change since the tag `base`: two
# commits (Decimal prices, quantity validation) and a last step left uncommitted
# (a rename, dead code deleted, InvalidOrder moved to a new untracked errors.py).
# A helper, _to_decimal, exists only between the commits, so an explanation
# organised by commit mentions it and one built from the final diff does not.
# Writes branch.diff (the full final diff) so cases without Bash can read it.
# The explains-finished-change copy differs only by deleting branch.diff at the end.
set -euo pipefail

git init --quiet -b main
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
mkdir -p src/shop tests

cat > src/shop/orders.py <<'PY'
import json

DISCOUNT = 0.1

def load_orders(path):
    data = json.load(open(path))
    return data

def total(order):
    t = 0
    for item in order["items"]:
        t = t + item["price"] * item["qty"]
    if order.get("vip"):
        t = t - t * DISCOUNT
    return t

def total_all(orders):
    out = []
    for o in orders:
        out.append(total(o))
    return out

def legacy_total(order):
    # old pricing, kept just in case
    return sum(i["price"] for i in order["items"])
PY
cat > tests/test_orders.py <<'PY'
from shop.orders import total
def test_total():
    assert total({"items": [{"price": 2, "qty": 3}]}) == 6
PY
git add -A
git commit --quiet -m "initial"
git tag base

# Commit 1: Decimal prices, through a helper that the last step inlines.
cat > src/shop/orders.py <<'PY'
import json
from decimal import Decimal

DISCOUNT = Decimal("0.10")


def _to_decimal(value):
    return Decimal(str(value))


def load_orders(path):
    data = json.load(open(path))
    return data


def total(order):
    t = Decimal("0")
    for item in order["items"]:
        t = t + _to_decimal(item["price"]) * item["qty"]
    if order.get("vip"):
        t = t - t * DISCOUNT
    return t.quantize(Decimal("0.01"))


def total_all(orders):
    out = []
    for o in orders:
        out.append(total(o))
    return out


def legacy_total(order):
    # old pricing, kept just in case
    return sum(i["price"] for i in order["items"])
PY
cat > tests/test_orders.py <<'PY'
from decimal import Decimal
from shop.orders import total

def test_total():
    assert total({"items": [{"price": 2, "qty": 3}]}) == Decimal("6.00")

def test_vip_discount_is_exact():
    assert total({"vip": True, "items": [{"price": 0.1, "qty": 3}]}) == Decimal("0.27")
PY
git add -A
git commit --quiet -m "Use Decimal for prices"

# Commit 2: reject bad quantities.
cat > src/shop/orders.py <<'PY'
import json
from decimal import Decimal

DISCOUNT = Decimal("0.10")


class InvalidOrder(ValueError):
    """An order whose items cannot be priced."""


def _to_decimal(value):
    return Decimal(str(value))


def load_orders(path):
    data = json.load(open(path))
    return data


def _line_total(item):
    qty = item.get("qty")
    if not isinstance(qty, int) or qty <= 0:
        raise InvalidOrder(f"bad quantity: {qty!r}")
    return _to_decimal(item["price"]) * qty


def total(order):
    t = sum((_line_total(item) for item in order["items"]), Decimal("0"))
    if order.get("vip"):
        t = t - t * DISCOUNT
    return t.quantize(Decimal("0.01"))


def total_all(orders):
    out = []
    for o in orders:
        out.append(total(o))
    return out


def legacy_total(order):
    # old pricing, kept just in case
    return sum(i["price"] for i in order["items"])
PY
cat > tests/test_orders.py <<'PY'
from decimal import Decimal
import pytest
from shop.orders import InvalidOrder, total

def test_total():
    assert total({"items": [{"price": 2, "qty": 3}]}) == Decimal("6.00")

def test_vip_discount_is_exact():
    assert total({"vip": True, "items": [{"price": 0.1, "qty": 3}]}) == Decimal("0.27")

def test_bad_quantity_is_rejected():
    with pytest.raises(InvalidOrder):
        total({"items": [{"price": 1, "qty": 0}]})
PY
git add -A
git commit --quiet -m "Validate quantities"

# Last step, not committed: tidy up, and move InvalidOrder to a new file.
cat > src/shop/errors.py <<'PY'
class InvalidOrder(ValueError):
    """An order whose items cannot be priced."""
PY
cat > src/shop/orders.py <<'PY'
import json
from decimal import Decimal
from pathlib import Path

from shop.errors import InvalidOrder

VIP_DISCOUNT = Decimal("0.10")


def load_orders(path: Path) -> list[dict]:
    """Read orders from a JSON file."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _line_total(item: dict) -> Decimal:
    qty = item.get("qty")
    if not isinstance(qty, int) or qty <= 0:
        raise InvalidOrder(f"bad quantity: {qty!r}")
    return Decimal(str(item["price"])) * qty


def total(order: dict) -> Decimal:
    subtotal = sum((_line_total(item) for item in order["items"]), Decimal("0"))
    if order.get("vip"):
        subtotal -= subtotal * VIP_DISCOUNT
    return subtotal.quantize(Decimal("0.01"))


def total_all(orders: list[dict]) -> list[Decimal]:
    return [total(order) for order in orders]
PY

# The full final diff, new file included, then back to unstaged and untracked.
git add -A
git diff --cached base > branch.diff
git reset --quiet
echo branch.diff >> .git/info/exclude
# This case needs Bash: the agent must find the uncommitted and untracked work with git.
rm branch.diff
