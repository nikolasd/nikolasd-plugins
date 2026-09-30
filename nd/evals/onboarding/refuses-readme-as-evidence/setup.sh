#!/usr/bin/env bash
# Plants a tiny repo whose README contradicts its code (Postgres + Redis claimed,
# SQLite used), so the case tests whether the docs follow the code, not whether the
# model can find a codebase to describe.
set -euo pipefail

cat > README.md <<'MD'
# Tasklist

A small task tracker. Tasks are stored in Postgres and list results are cached in
Redis. Run it with `make run`.
MD

cat > Makefile <<'MK'
run:
	python src/app.py
MK

echo 'flask' > requirements.txt

mkdir -p src tests
cat > src/db.py <<'PY'
import sqlite3

DB_PATH = "tasks.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT)")
    return conn


def add_task(title: str) -> int:
    with connect() as conn:
        return conn.execute("INSERT INTO tasks (title) VALUES (?)", (title,)).lastrowid


def list_tasks() -> list[tuple]:
    with connect() as conn:
        return conn.execute("SELECT id, title FROM tasks").fetchall()
PY

cat > src/app.py <<'PY'
from flask import Flask, jsonify, request

from db import add_task, list_tasks

app = Flask(__name__)


@app.get("/tasks")
def get_tasks():
    return jsonify(list_tasks())


@app.post("/tasks")
def post_task():
    return jsonify({"id": add_task(request.json["title"])}), 201


if __name__ == "__main__":
    app.run(port=8080)
PY

cat > tests/test_db.py <<'PY'
import unittest

import db


class DbTest(unittest.TestCase):
    def test_add_then_list(self):
        task_id = db.add_task("write docs")
        self.assertIn((task_id, "write docs"), db.list_tasks())
PY
