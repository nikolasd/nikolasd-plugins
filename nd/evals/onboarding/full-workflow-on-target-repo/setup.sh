#!/usr/bin/env bash
# Copies the tracked files at HEAD of a real repository into the empty workspace, so
# the case runs the whole onboarding workflow against real code. Tracked files only:
# untracked and ignored files (.env.local, node_modules, build output) never enter the
# sandbox.
#
# Which repository: set EVAL_TARGET_REPO to its absolute path, or put the path on one
# line in target-repo.path next to this script (gitignored, so it stays per-machine).
set -euo pipefail

repo="${EVAL_TARGET_REPO:-}"
if [ -z "$repo" ]; then
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  [ -f "$here/target-repo.path" ] && repo="$(head -n 1 "$here/target-repo.path" | tr -d '\r')"
fi
if [ -z "$repo" ] || ! git -C "$repo" rev-parse --git-dir >/dev/null 2>&1; then
  echo "set EVAL_TARGET_REPO (or target-repo.path) to a git repository; got: '${repo}'" >&2
  exit 1
fi

# The target's own agent config (.claude/, .agents/, CLAUDE.md, AGENTS.md) is left out:
# Claude Code would load it as project skills and instructions and change what this
# case measures, which is the onboard skill alone.
git -C "$repo" archive HEAD | tar -x --exclude=.claude --exclude=.agents --exclude=CLAUDE.md --exclude=AGENTS.md
echo "copied $(git -C "$repo" ls-files | wc -l) tracked files from $repo at $(git -C "$repo" rev-parse --short HEAD)"
