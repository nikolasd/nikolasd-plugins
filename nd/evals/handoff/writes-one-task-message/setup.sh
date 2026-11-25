#!/usr/bin/env bash
set -euo pipefail
git init --quiet
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
cat > RELEASE_NOTES.md <<'MD'
# Release notes

Version 2.4 (beta) ships on 2026-12-01.

- Faster sync for large folders.
- New sharing dialog.
MD
git add RELEASE_NOTES.md
git commit --quiet -m "Draft release notes for 2.4"
