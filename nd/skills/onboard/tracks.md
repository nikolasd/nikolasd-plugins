# Tracks and layouts

Read this before step 2 of the workflow.

## What a track is

A *track* is a component with its own registration/entrypoint seam **and** its own runtime process or deploy target: a separate app module, worker, Dockerfile or compose service, or startup-script mode. Shared libraries are never tracks.

Find them by grepping for the seams: domain registries, app factories, mount functions, worker entrypoints, startup-script modes.

## Choosing the layout

| Tracks found | Layout | Checker flag | Docs |
|---|---|---|---|
| 0 or 1 | single | `--layout single` | `c4/01-context.md`, `c4/02-containers.md`, `c4/03-components.md`, `engineering.md`, `ai-design.md`, `infrastructure.md`, `deployment.md`, `ONBOARDING.md` |
| 2 or more | tracked | `--layout tracked` | the same set under `common/` (domain-neutral platform), plus per track a dir `<track>/` holding `README.md`, `components.md`, `agents.md`, plus `OWNERSHIP.md` and a fork-style `ONBOARDING.md` |

## Deciding who owns a file

- A file imported by two or more tracks is `common`: describe it in `common/`, list it under "Cross-track touch points" in `OWNERSHIP.md`. Each track doc may cite it for its own use.
- Decide every ambiguous file by its importers, never by its directory or name. Record the decision and the reason in `OWNERSHIP.md`.

## Repos with no LLM agents

Rename `ai-design.md` to `runtime-design.md` and `agents.md` to `workloads.md` (long-running processes, jobs, pipelines). The rules stay the same. Pass `--ai-doc runtime-design.md --agents-doc workloads.md` to the checker, or it reports the originals as MISSING.

The rename is all-or-nothing for the repo, because the checker takes one name for the set. In a **mixed** repo (some tracks have agents, some do not), keep `agents.md` everywhere. `agents.md` covers agents *and* workloads: a track with no LLM agents documents its workloads there instead. A track is defined by having its own runtime process, so it always has at least one workload to document, and the usual citation minimum is reachable. If a track is genuinely too thin for it, the only lever is a lower `--min-cites` for the whole set, which you must say in the final report.

## Track regexes for the checker

`--track NAME:REGEX`. `NAME` must equal the track's directory name. `REGEX` matches that track's own package roots and distinctive module prefixes, derived from the seams above. Never include shared libraries. The checker fails a track doc that matches another track's regex, and fails a `common/` doc that matches any track's regex outside a heading containing "Domain extension points".
