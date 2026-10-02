#!/usr/bin/env bash
set -euo pipefail
git init --quiet
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
cat > client.py <<'PY'
def fetch(url):
    return {"status": 200, "body": ""}
PY
cat > HANDOFF.md <<'MD'
# Payments Handoff

Date: 2026-09-01
Repo: /old/path
HEAD of the work: abc1234 initial

## What Was Built This Session
- STALE-ITEM-ALREADY-DONE: wrote the initial client skeleton.

## Outstanding Work
- STALE-ITEM-ALREADY-DONE: add a client skeleton.
MD
git add -A
git commit --quiet -m "Payments client skeleton and handoff"

# Make `git` usable for the agent inside the eval sandbox on macOS (see the other scaffolds):
# the Xcode shim cannot write its cache there, so call the real binary. Only acts when that
# binary exists and HOME is the eval's own temporary home.
REAL_GIT=/Library/Developer/CommandLineTools/usr/bin/git
case "$HOME" in
  /private/tmp/e-*|/tmp/e-*)
    if [ -x "$REAL_GIT" ]; then
      mkdir -p "$HOME/.eval-bin"
      printf '#!/bin/sh\nexec "%s" "$@"\n' "$REAL_GIT" > "$HOME/.eval-bin/git"
      chmod +x "$HOME/.eval-bin/git"
      for f in .zshenv .zshrc .bashrc .bash_profile; do
        printf 'export PATH="%s:$PATH"\n' "$HOME/.eval-bin" > "$HOME/$f"
      done
    fi
    ;;
esac
