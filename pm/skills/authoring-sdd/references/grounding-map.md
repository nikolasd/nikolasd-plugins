# Phase 2: what to ground, and where

Read this at the start of Phase 2. The section numbers are the bundled template's; with a custom template, map them by section name.

For each of the following, capture the fact together with `file:line`
evidence. These map onto the sections in `section-tiers.md`:

- **Tech stack and dependencies** (§18): package manifests, lockfiles,
  Dockerfiles.
- **Services, entry points, deployment topology** (§13–15): what talks to
  what, and across which trust boundary.
- **Data stores and models** (§17, §20): ORM models, migrations, schema
  files.
- **API routes and interfaces** (§19): route definitions, an OpenAPI spec if
  one exists.
- **External integrations** (§21): SDK usage, environment variables that name
  an external service.
- **IaC and CI/CD configs** (§28–29): environments defined, deploy
  pipelines, any scripted rollback step.
- **Existing tests** (§30): test directories, coverage configuration.
- **Existing ADRs** under `docs/adr/*.md`, if the repository has them: mine
  these directly for §33 (Key decisions) and §34 (the ADR table), preserving
  their existing IDs and dates exactly rather than re-deriving them.
- **Auth/authz code**: partial grounding for §22 (cross-cutting policy) and
  §23 (security & identity). The threat-model conclusion and the
  least-privilege justification stay interview items regardless of what the
  code shows.
- **Accessibility signals** in UI code (ARIA attributes, an a11y tooling
  config): partial grounding for §27, only when the repository has a
  human-facing UI.
