#!/usr/bin/env bash
# The case needs no planted files; the harness seeds a repo. This scaffold only makes `git`
# runnable for the agent in the sandbox, so a refusal to commit comes from the skill and not from
# a git that cannot start.
set -euo pipefail

# Make `git` usable for the agent inside the eval sandbox on macOS. /usr/bin/git is an Xcode
# shim that must write a cache file the sandbox forbids, so every agent git call fails; call the
# real binary instead. Only acts when that binary exists and HOME is the eval's own temporary
# home, so Linux and CI behave exactly as before.
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
