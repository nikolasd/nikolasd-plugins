#!/usr/bin/env bash
# The eval harness seeds an empty (commit-less) git repo by default, which
# makes `git rev-parse --git-dir` succeed rather than fail — the opposite of
# what this case is meant to test. `rm -rf .git` isn't reliable here: the
# seeded repo's root doesn't necessarily match this script's own cwd (git
# searches upward), so a plain `.git` removal can silently miss it and
# leave a real, discoverable, commit-less repo in place. Ask git itself
# where the repo actually is and remove exactly that, looped in case of
# nesting, until git-dir genuinely fails.
#
# Also plants real files matching the prompt's narrative so a model that
# checks for corroborating evidence finds it, not nothing.
set -euo pipefail

for _ in 1 2 3; do
  git_dir=$(git rev-parse --git-dir 2>/dev/null) || break
  rm -rf "$git_dir"
done

if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "setup.sh: a git repo is still discoverable after cleanup — scaffold cannot guarantee a non-git workspace" >&2
  exit 1
fi

mkdir -p payments

cat > payments/client.py <<'PY'
import time


GATEWAY_TIMEOUT_SECS = 10
MAX_RETRY_ATTEMPTS = 3


def _is_retryable(response):
    """The upstream API returns 200 with an error body instead of a 4xx,
    so the retry predicate has to inspect the body, not the status code."""
    if response.status_code >= 500:
        return True
    if response.status_code == 200 and response.json().get("error"):
        return True
    return False


def call_with_backoff(send_request):
    attempt = 0
    while attempt < MAX_RETRY_ATTEMPTS:
        response = send_request(timeout=GATEWAY_TIMEOUT_SECS)
        if not _is_retryable(response):
            return response
        attempt += 1
        time.sleep(2 ** attempt)
    return response
PY
