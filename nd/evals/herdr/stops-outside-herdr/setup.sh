#!/usr/bin/env bash
# Makes sure the sandbox shell is in neither kind of Herdr: no standalone pane (HERDR_ENV) and
# no desktop app terminal (HC_TERMINAL_ID), even when the suite is run from inside the app.
set -euo pipefail

# HOME is the eval's own temporary home; refuse to touch anything else.
case "$HOME" in
  /private/tmp/e-*|/tmp/e-*|/tmp/claude-eval-*/home) ;;
  *) echo "refusing to write shell startup files outside the eval sandbox: $HOME" >&2; exit 1 ;;
esac
for f in .zshenv .zshrc .bashrc .bash_profile; do
  echo 'unset HERDR_ENV HC_TERMINAL_ID' > "$HOME/$f"
done
