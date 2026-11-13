#!/usr/bin/env bash
# Marks the session as running in a Herdr desktop app terminal (HC_TERMINAL_ID set, HERDR_ENV unset)
# and puts stub `herdr` and `herdr-app` on PATH. Each stub logs its calls, so the case can
# check that the standalone CLI route was not used and the app's commands were.
set -euo pipefail

D="$PWD"
mkdir -p bin app-home
: > herdr-calls.log
: > herdr-app-calls.log

cat > app-home/AGENTS.md <<'DOC'
# Herdr app

Start an agent in a new tab, with its first message:

    herdr-app do tab.new --name "<name>" --argv '["codex"]' --task "<first message>"

`herdr-app do` prints `{ "space", "tab", "terminal" }`. Then use `hc read <terminal>`,
`hc send <terminal> "<text>"` and `hc wait <terminal>`. `herdr-app commands` lists every command.
DOC

cat > bin/herdr <<'STUB'
#!/bin/sh
D=$(cd "$(dirname "$0")/.." && pwd)
echo "$*" >> "$D/herdr-calls.log"
echo '{"error":{"code":"not_in_herdr","message":"not inside a Herdr pane"}}' >&2
exit 1
STUB

cat > bin/herdr-app <<'STUB'
#!/bin/sh
D=$(cd "$(dirname "$0")/.." && pwd)
echo "$*" >> "$D/herdr-app-calls.log"
case "$1" in
  do) echo '{"space":"s1","tab":"s1/2","terminal":"t4"}' ;;
  --skill) cat "$D/app-home/AGENTS.md" ;;
  commands) echo '[{"name":"tab.new","args":[{"name":"name"},{"name":"argv"},{"name":"task"}]},{"name":"pane.split","args":[{"name":"direction"},{"name":"argv"}]}]' ;;
  *) echo '{}' ;;
esac
STUB

cat > bin/hc <<'STUB'
#!/bin/sh
D=$(cd "$(dirname "$0")/.." && pwd)
echo "hc $*" >> "$D/herdr-app-calls.log"
case "$1" in
  read) printf '> Review this branch\n(working...)\n' ;;
  *) echo '{}' ;;
esac
STUB
chmod +x bin/herdr bin/herdr-app bin/hc

# Mark the session as in the app through the sandbox shell's startup files. HOME is the
# eval's own temporary home; refuse to touch anything else.
case "$HOME" in
  /private/tmp/e-*|/tmp/e-*|/tmp/claude-eval-*/home) ;;
  *) echo "refusing to write shell startup files outside the eval sandbox: $HOME" >&2; exit 1 ;;
esac
for f in .zshenv .zshrc .bashrc .bash_profile; do
  cat > "$HOME/$f" <<ENV
unset HERDR_ENV
export HERDR_APP_HOME="$D/app-home" HC_TERMINAL_ID=t1
export PATH="$D/bin:\$PATH"
ENV
done
