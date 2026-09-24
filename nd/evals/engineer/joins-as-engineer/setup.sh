#!/usr/bin/env bash
# Without this, the sandbox is an empty directory with no /signup endpoint to
# edit, so a model correctly asks where the code lives (and what stack to use)
# instead of following TDD against real code — same fixture-conflation shape
# as handoff-guards-non-git's original bug (see nd/evals/README.md).
set -euo pipefail

mkdir -p signup

cat > signup/handler.py <<'PY'
def create_account(email: str, password: str) -> dict:
    """Handles a POST /signup submission. No email validation yet — an empty
    or malformed address reaches the database as-is."""
    return {"email": email, "password_hash": hash(password)}
PY
