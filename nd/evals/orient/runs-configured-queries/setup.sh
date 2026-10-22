#!/usr/bin/env bash
# Seeds the project settings the skill reads: a primary project plus one
# orientQueries entry for a note type Basic Memory's own orientation never searches.
set -euo pipefail

# Some ordinary code, so the settings file is not the only thing in the workspace.
cat > README.md <<'MD'
# Tasklist

A small task tracker that stores tasks in SQLite.
MD
cat > app.py <<'PY'
import sqlite3


def list_tasks(db_path):
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT id, title FROM tasks").fetchall()
PY

mkdir -p .claude
cat > .claude/settings.local.json <<'JSON'
{
  "basicMemory": {
    "primaryProject": "eval-notes",
    "recallTimeframe": "3d",
    "sessionProfile": "general",
    "orientQueries": [
      {
        "label": "Open ticket journals",
        "type": "ticket_journal",
        "status": ["design", "in_progress"],
        "query": "journal"
      }
    ]
  }
}
JSON
