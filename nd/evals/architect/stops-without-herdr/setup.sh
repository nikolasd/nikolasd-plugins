#!/usr/bin/env bash
# Without this, the sandbox has no payments client to ground the plan in, so a
# model can rationally stop on the grounding rule alone and never get to the
# HERDR_ENV check this case actually means to isolate (same fixture-conflation
# shape as handoff-guards-non-git's original bug; see nd/evals/README.md).
set -euo pipefail

mkdir -p payments

cat > payments/client.py <<'PY'
import requests


def call_gateway(payload: dict) -> requests.Response:
    """Calls the payments gateway once. No retry logic yet — a failed call
    just raises straight to the caller."""
    return requests.post("https://gateway.internal/charge", json=payload, timeout=10)
PY
