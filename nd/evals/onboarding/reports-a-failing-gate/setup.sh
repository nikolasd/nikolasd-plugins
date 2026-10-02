#!/usr/bin/env bash
set -euo pipefail
git init --quiet
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
mkdir -p src docs/onboarding/c4
echo 'def main(): pass' > src/app.py
cat > docs/onboarding/c4/01-context.md <<'MD'
# c4/01-context.md

This document cites a file that does not exist: `src/ghost.py`.

```mermaid
graph TD
  A-->B
```
MD
cat > docs/onboarding/c4/02-containers.md <<'MD'
# c4/02-containers.md

This document cites a file that does not exist: `src/ghost.py`.

```mermaid
graph TD
  A-->B
```
MD
cat > docs/onboarding/c4/03-components.md <<'MD'
# c4/03-components.md

This document cites a file that does not exist: `src/ghost.py`.

```mermaid
graph TD
  A-->B
```
MD
cat > docs/onboarding/engineering.md <<'MD'
# engineering.md

This document cites a file that does not exist: `src/ghost.py`.

```mermaid
graph TD
  A-->B
```
MD
cat > docs/onboarding/ai-design.md <<'MD'
# ai-design.md

This document cites a file that does not exist: `src/ghost.py`.

```mermaid
graph TD
  A-->B
```
MD
cat > docs/onboarding/infrastructure.md <<'MD'
# infrastructure.md

This document cites a file that does not exist: `src/ghost.py`.

```mermaid
graph TD
  A-->B
```
MD
cat > docs/onboarding/deployment.md <<'MD'
# deployment.md

This document cites a file that does not exist: `src/ghost.py`.

```mermaid
graph TD
  A-->B
```
MD
cat > docs/onboarding/ONBOARDING.md <<'MD'
# ONBOARDING.md

This document cites a file that does not exist: `src/ghost.py`.

```mermaid
graph TD
  A-->B
```
MD
git add -A
git commit --quiet -m "Docs with a dangling citation"
