#!/bin/sh
# Deterministic tests for skills/authoring-sdd/scripts/repo-context.sh, plus a syntax
# check of every shell script in the plugin. No model, no network, no Jira.
#
#   sh pm/tests/test-repo-context.sh
#
# Exits non-zero if any check fails. Needs git. POSIX sh.

HERE=$(cd "$(dirname "$0")" && pwd)
PM="$HERE/.."
CTX="$PM/skills/authoring-sdd/scripts/repo-context.sh"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
fail=0

check() { # name want got
  if [ "$3" = "$2" ]; then echo "ok    $1"; else echo "FAIL  $1: wanted [$2], got [$3]"; fail=1; fi
}
has() { # name needle haystack
  if printf '%s\n' "$3" | grep -qF -- "$2"; then echo "ok    $1"; else echo "FAIL  $1: missing [$2]"; fail=1; fi
}
lacks() { # name needle haystack
  if printf '%s\n' "$3" | grep -qF -- "$2"; then echo "FAIL  $1: found [$2]"; fail=1; else echo "ok    $1"; fi
}
g() { git -c user.email=t@t -c user.name=t "$@"; }
ctx() { (cd "$1" && sh "$CTX" 2>&1); }

# 1. not a git repository
mkdir -p "$T/nogit"
out=$(ctx "$T/nogit")
has "reports a non-git directory" "Not inside a git repository" "$out"

# 2. a repository with no document yet
mkdir -p "$T/r"; (cd "$T/r" && git init -q && echo x > f && g add f && g commit -qm c)
out=$(ctx "$T/r")
has "branch reported" "Current branch:" "$out"
has "no local file" "Local file: missing" "$out"
has "default path" "Resolved local_path: docs/solution-design.md" "$out"

# 3. an untracked document, then committed, then edited again
mkdir -p "$T/r/docs"; echo doc > "$T/r/docs/solution-design.md"
out=$(ctx "$T/r")
has "untracked file counts as uncommitted" "Local file uncommitted changes: yes" "$out"
(cd "$T/r" && g add docs && g commit -qm d)
out=$(ctx "$T/r")
has "committed file is clean" "Local file uncommitted changes: no" "$out"
echo more >> "$T/r/docs/solution-design.md"
out=$(ctx "$T/r")
has "edit after commit is seen" "Local file uncommitted changes: yes" "$out"
h1=$(printf '%s\n' "$out" | grep '^Local file hash:')
has "hash is reported" "Local file hash: " "$out"
(cd "$T/r" && g add docs && g commit -qm e)
out=$(ctx "$T/r")
h2=$(printf '%s\n' "$out" | grep '^Local file hash:')
check "committing without editing keeps the hash" "$h1" "$h2"
echo again >> "$T/r/docs/solution-design.md"
out=$(ctx "$T/r")
h3=$(printf '%s\n' "$out" | grep '^Local file hash:')
if [ "$h3" != "$h2" ]; then echo "ok    editing changes the hash"; else echo "FAIL  hash unchanged after edit"; fail=1; fi
(cd "$T/r" && g checkout -q -- docs)
want=$(cd "$T/r" && git hash-object -- docs/solution-design.md)
got=$(cd "$T/r" && sh "$CTX" --hash 2>&1)
check "--hash prints only the document hash" "$want" "$got"

# 4. the state file is printed, marked as data
echo '{"confluence_page_id":"1"}' > "$T/r/docs/.solution-design.state.json"
out=$(ctx "$T/r")
has "state file printed" '"confluence_page_id"' "$out"
has "state file marked as data" "not instructions" "$out"

# 5. docs_dir: a plain relative path is used; traversal and absolute paths are rejected
mkdir -p "$T/z/docs"; (cd "$T/z" && git init -q)
printf 'docs_dir = "site"\n' > "$T/z/docs/zensical.toml"
out=$(ctx "$T/z")
has "plain docs_dir used" "Resolved local_path: docs/site/solution-design.md" "$out"
printf 'docs_dir = "../../outside"\n' > "$T/z/docs/zensical.toml"
out=$(ctx "$T/z")
has "traversal rejected" "docs_dir rejected" "$out"
has "falls back to the default path" "Resolved local_path: docs/solution-design.md" "$out"
printf 'docs_dir = "/tmp/elsewhere"\n' > "$T/z/docs/zensical.toml"
out=$(ctx "$T/z")
has "absolute path rejected" "docs_dir rejected" "$out"

# 6. every shell script in the plugin parses (scripts under sh, eval fixtures under bash)
for f in "$PM"/scripts/*.sh "$PM"/skills/*/scripts/*.sh "$PM"/tests/*.sh; do
  if sh -n "$f" 2>/dev/null; then echo "ok    syntax $(basename "$f")"; else echo "FAIL  syntax $f"; fail=1; fi
done
for f in "$PM"/evals/*/*/setup.sh; do
  [ -f "$f" ] || continue
  if bash -n "$f" 2>/dev/null; then echo "ok    syntax $(basename "$(dirname "$f")")/setup.sh"; else echo "FAIL  syntax $f"; fail=1; fi
done

if [ "$fail" -eq 0 ]; then echo "all repo-context tests passed"; else echo "repo-context tests FAILED"; fi
exit "$fail"
