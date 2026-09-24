#!/usr/bin/env bash
# Without this, the sandbox is an empty directory with no signup form to edit,
# so a model correctly asks where the code lives instead of implementing —
# same shape as handoff-guards-non-git's original bug (see nd/evals/README.md).
# That's not the near-miss behaviour this case means to test, so plant a
# minimal target matching the prompt's narrative.
set -euo pipefail

mkdir -p signup

cat > signup/handler.py <<'PY'
def create_account(email: str, password: str) -> dict:
    """Handles a signup form submission. No email validation yet — an empty
    or malformed address reaches the database as-is."""
    return {"email": email, "password_hash": hash(password)}
PY
