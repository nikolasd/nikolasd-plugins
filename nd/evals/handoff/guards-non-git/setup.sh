#!/usr/bin/env bash
# The eval harness seeds an empty (commit-less) git repo by default, which
# makes `git rev-parse --git-dir` succeed rather than fail — the opposite of
# what this case is meant to test. Remove it so the workspace is genuinely
# not a git repository, and plant real files matching the prompt's narrative
# so a model that checks for corroborating evidence finds it, not nothing.
set -euo pipefail

rm -rf .git

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
