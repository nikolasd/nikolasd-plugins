#!/usr/bin/env bash
# A docs-only change: one misspelled word in a README. No behaviour, no tests, no git action asked for.
set -euo pipefail
cat > README.md <<'MD'
# Tasklist

A small task tracker. It will recieve tasks over HTTP and store them in SQLite.
MD
