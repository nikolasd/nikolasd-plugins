#!/usr/bin/env bash
# Builds a tiny membership-service repo: one committed baseline the skill can investigate.
set -euo pipefail

git init --quiet
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
mkdir -p app tests .claude

cat > app/settings.py <<'PY'
"""Runtime settings for the membership service."""
import os

SERVICE_NAME = "membership"
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///membership.db")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
PY

cat > app/cache.py <<'PY'
"""Group membership cache.

Membership lookups are expensive, so results are cached per user and expire
at the next local midnight.
"""
import datetime

_CACHE: dict[str, tuple[datetime.datetime, list[str]]] = {}


def _next_midnight(now: datetime.datetime) -> datetime.datetime:
    tomorrow = now.date() + datetime.timedelta(days=1)
    return datetime.datetime.combine(tomorrow, datetime.time.min)


def get_groups(user_id: str, loader) -> list[str]:
    """Return the user's groups, loading and caching them on a miss."""
    now = datetime.datetime.now()
    hit = _CACHE.get(user_id)
    if hit and now < hit[0]:
        return hit[1]
    groups = loader(user_id)
    _CACHE[user_id] = (_next_midnight(now), groups)
    return groups
PY

cat > app/api.py <<'PY'
"""HTTP handlers."""
from app import cache


def list_user_groups(user_id: str, loader):
    return {"user": user_id, "groups": cache.get_groups(user_id, loader)}
PY

cat > tests/test_cache.py <<'PY'
from app import cache


def test_cache_returns_loaded_groups():
    assert cache.get_groups("u1", lambda _: ["a", "b"]) == ["a", "b"]
PY

printf 'Membership service. Run tests with `pytest`.\n' > README.md
echo '{"project_key":"DEMO"}' > .claude/pm.json
git add -A
git commit --quiet -m "Membership service baseline"

# An existing SDD: FR-01 met, FR-02 retired, FR-03 in build. Never renumber them.
mkdir -p docs
cat > docs/solution-design.md <<'MD'
# Membership Service: Solution Design Document

## 1. Document control

| Version | 1.0 |
| --- | --- |

## 8. Functional requirements

| ID | Category | Requirement | Acceptance criteria | Priority | Stakeholders | Status |
| --- | --- | --- | --- | --- | --- | --- |
| FR-01 | Retrieval | Return a user's groups | Given a user, when requested, then groups are returned | Must | Support | Met |
| FR-02 | Retrieval | Return groups in alphabetical order | Given groups, when returned, then sorted | Should | Support | Descoped |
| FR-03 | Caching | Cache group lookups per user | Given a repeat lookup, then the loader is not called again | Must | Support | In build |
MD
cat > docs/.solution-design.state.json <<'JSON'
{
  "confluence_page_id": null,
  "confluence_space": "DOCS",
  "confluence_parent_id": null,
  "confluence_version": null,
  "local_path": "docs/solution-design.md",
  "last_run_version": "1.0",
  "last_run_date": "2026-09-01"
}
JSON
git add -A
git commit --quiet -m "Add SDD"
