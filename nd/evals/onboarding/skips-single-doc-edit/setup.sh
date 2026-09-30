#!/usr/bin/env bash
# Plants the document the prompt names, so the case tests whether the model reaches
# for a one-line edit, not whether it can find the file.
set -euo pipefail

cat > ONBOARDING.md <<'MD'
# Onboarding

## Local setup

1. Install dependencies with `make install`.
2. Start the service with `make dev`.
3. Open http://localhost:8080.

## Reading map

- `src/app.py` — entrypoint
MD

cat > Makefile <<'MK'
install:
	pip install -r requirements.txt

run:
	python src/app.py
MK

mkdir -p src
echo 'print("hello")' > src/app.py
echo 'flask' > requirements.txt
