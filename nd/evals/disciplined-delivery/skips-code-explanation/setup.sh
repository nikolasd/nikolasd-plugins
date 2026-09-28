#!/usr/bin/env bash
# Plants the code the prompt asks about, so the case tests whether the skill
# fires rather than whether the model can find missing code.
set -euo pipefail

cat > utils.py <<'PY'
def fmt(cents: int) -> str:
    return f"${cents / 100:.2f}"


def receipt_line(name: str, cents: int) -> str:
    return f"{name}: {fmt(cents)}"
PY
