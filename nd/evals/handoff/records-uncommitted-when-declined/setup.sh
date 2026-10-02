#!/usr/bin/env bash
set -euo pipefail
git init --quiet
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
cat > limiter.py <<'PY'
class RateLimiter:
    def allow(self, key):
        return True
PY
git add -A
git commit --quiet -m "Baseline"
cat > limiter.py <<'PY'
class RateLimiter:
    def allow(self, key):
        return key != "blocked"
PY

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
