#!/bin/sh
# Renders one self-contained HTML mockup to a PNG with a headless
# Chromium-family browser (Chrome, Edge, Chromium or Brave) on macOS, Linux, or
# Windows under Git Bash. No installation is needed beyond a browser.
#
# Usage: render.sh [--open] <html> [png] [width] [height]
#   png     output path; defaults to the HTML path with a .png extension
#   width   viewport width in CSS pixels  (default 1440)
#   height  viewport height in CSS pixels (default 1024)
#   --open  open the PNG in the default viewer afterwards
#
# Browser selection: $PM_BROWSER (a path or a command name) wins if set and is
# never silently overridden. Otherwise the first browser found among the
# standard macOS application bundles, the usual Linux command names, and the
# standard Windows install folders.
#
# Exit codes: 0 rendered; 1 bad arguments or missing HTML; 2 no browser found
# (the HTML path is printed so the caller can fall back); 3 a browser ran but
# produced no PNG. Prints "Rendered: <png>" on success.
#
# POSIX sh only (no bashisms).

OPEN=0
if [ "$1" = "--open" ]; then OPEN=1; shift; fi

HTML=$1
PNG=$2
W=${3:-1440}
H=${4:-1024}

if [ -z "$HTML" ] || [ ! -f "$HTML" ]; then
  echo "HTML file not found: ${HTML:-(none given)}" >&2
  exit 1
fi

abspath() {
  d=$(cd "$(dirname "$1")" 2>/dev/null && pwd) || return 1
  printf '%s/%s' "$d" "$(basename "$1")"
}

HTML_ABS=$(abspath "$HTML") || { echo "Cannot resolve: $HTML" >&2; exit 1; }
[ -n "$PNG" ] || PNG="${HTML_ABS%.*}.png"
mkdir -p "$(dirname "$PNG")" 2>/dev/null
PNG_ABS=$(abspath "$PNG") || { echo "Cannot resolve output: $PNG" >&2; exit 1; }

# Native Windows browsers need Windows-style paths; Git Bash ships cygpath.
if command -v cygpath >/dev/null 2>&1; then
  HTML_ABS=$(cygpath -m "$HTML_ABS")
  PNG_ABS=$(cygpath -m "$PNG_ABS")
fi

find_browser() {
  if [ -n "${PM_BROWSER:-}" ]; then
    if [ -x "$PM_BROWSER" ]; then printf '%s' "$PM_BROWSER"; return 0; fi
    p=$(command -v "$PM_BROWSER" 2>/dev/null) && [ -n "$p" ] && { printf '%s' "$p"; return 0; }
    return 1
  fi
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"; do
    [ -x "$c" ] && { printf '%s' "$c"; return 0; }
  done
  for c in google-chrome google-chrome-stable chromium chromium-browser \
           microsoft-edge microsoft-edge-stable brave-browser msedge; do
    p=$(command -v "$c" 2>/dev/null) && [ -n "$p" ] && { printf '%s' "$p"; return 0; }
  done
  for base in "${PROGRAMFILES:-}" "$(printenv 'PROGRAMFILES(X86)' 2>/dev/null)" "${LOCALAPPDATA:-}"; do
    [ -n "$base" ] || continue
    if command -v cygpath >/dev/null 2>&1; then base=$(cygpath -u "$base"); fi
    for rel in "Google/Chrome/Application/chrome.exe" \
               "Microsoft/Edge/Application/msedge.exe" \
               "BraveSoftware/Brave-Browser/Application/brave.exe"; do
      [ -x "$base/$rel" ] && { printf '%s' "$base/$rel"; return 0; }
    done
  done
  return 1
}

BROWSER=$(find_browser)
if [ -z "$BROWSER" ]; then
  echo "No Chromium-family browser found (looked for Chrome, Edge, Chromium, Brave; PM_BROWSER=${PM_BROWSER:-unset})." >&2
  echo "HTML: $HTML_ABS" >&2
  exit 2
fi

# A throwaway profile stops headless mode attaching to an already-running
# browser (which would produce no screenshot).
PROFILE=$(mktemp -d 2>/dev/null) || PROFILE="${TMPDIR:-/tmp}/pm-render-profile-$$"
pid=""
trap 'rm -rf "$PROFILE"' EXIT
trap 'kill "$pid" 2>/dev/null; exit 130' INT TERM
if command -v cygpath >/dev/null 2>&1; then PROFILE_ARG=$(cygpath -m "$PROFILE"); else PROFILE_ARG=$PROFILE; fi

# Some browser builds write the screenshot and then never exit, so the browser
# runs in the background: wait until the PNG exists and has stopped growing (or
# the browser exits on its own, or ~25 seconds pass), then stop it.
attempt() {
  # $1 = headless flag, $2 = extra flag (may be empty)
  rm -f "$PNG_ABS" 2>/dev/null
  "$BROWSER" "$1" --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --user-data-dir="$PROFILE_ARG" ${2:+"$2"} \
    --window-size="$W,$H" --screenshot="$PNG_ABS" "$HTML_ABS" >/dev/null 2>&1 &
  pid=$!
  ticks=0
  last=-1
  while [ "$ticks" -lt 100 ]; do
    if [ -s "$PNG_ABS" ]; then
      size=$(wc -c < "$PNG_ABS" | tr -d ' ')
      [ "$size" = "$last" ] && break
      last=$size
    fi
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.25 2>/dev/null || sleep 1
    ticks=$((ticks + 1))
  done
  pkill -P "$pid" 2>/dev/null
  kill "$pid" 2>/dev/null
  wait "$pid" 2>/dev/null
  [ -s "$PNG_ABS" ]
}

# Current headless first, then the legacy headless mode of older browsers. The
# sandbox is switched off only when running as root, where browsers refuse to
# start with it (typical of containers).
NOSANDBOX=""
[ "$(id -u 2>/dev/null)" = 0 ] && NOSANDBOX="--no-sandbox"
if attempt --headless=new "$NOSANDBOX" || attempt --headless "$NOSANDBOX"; then
  echo "Rendered: $PNG_ABS"
else
  echo "The browser ran but produced no PNG at: $PNG_ABS" >&2
  echo "Browser: $BROWSER" >&2
  exit 3
fi

if [ "$OPEN" = 1 ]; then
  if command -v open >/dev/null 2>&1; then open "$PNG_ABS"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$PNG_ABS" >/dev/null 2>&1
  elif command -v cmd.exe >/dev/null 2>&1; then cmd.exe /c start "" "$PNG_ABS"
  fi
fi
exit 0
