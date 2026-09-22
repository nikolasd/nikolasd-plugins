---
title: Plain-language guidance is a request-triggered skill
type: decision
permalink: nikolad-plugins/decisions/plain-language-guidance-is-a-request-triggered-skill
status: accepted
decided: '2026-09-22'
project: nikolad-plugins
tags:
- skills
- writing-plain-language
- nd-plugin
---

# Plain-language guidance is a request-triggered skill

`nd/skills/writing-plain-language/SKILL.md` fires when the user asks for plain
language. It is deliberately **not** an always-on rule. The outcome is visible in the
file; this note records the alternatives and why they lost, so the question does not
get relitigated.

## Observations

- [decision] Keep plain-language guidance as a skill with a real trigger, rather than making it an always-on response register.
- [context] The original description read "Use when writing any response to the user, before choosing wording" — which is not a trigger but a synonym for *always*. A skill whose description matches every turn either never fires distinctively or fires constantly and burns context.
- [alternative] **Output style** (`output-styles/plain-language.md`, registered via `outputStyles` in `plugin.json`). Rejected: output styles are mutually exclusive, only one active at a time, and the basic-memory plugin ships its own. Adopting that style would silently switch plain-language off.
- [alternative] **CLAUDE.md rule.** Genuinely the most robust option — no exclusivity, composes with everything, and user instructions outrank skills by design. Rejected because it leaves the plugin, so it cannot ship through the marketplace.
- [alternative] **Both: always-on rule plus an on-demand skill.** Rejected as two surfaces holding one rule, which drift apart over time.
- [consequence] The skill no longer claims to apply to every response. Its out-of-scope list explicitly names technical docs, ADRs, architecture documents, code comments, commit messages, and PR descriptions.
- [consequence] Being request-triggered weakens the case for prohibition-shaped guidance. Prohibitions backfire under a *competing* incentive, and an explicit request removes that competition — which is why a compact "Common swaps" table was kept after being cut, rather than stripped entirely.
- [consequence] Content was restructured from a prohibition list into a positive recipe: 718 words down to 471.
- [rationale] A skill can only express "when", not "always". Choosing the trigger honestly is better than a description that pretends to a scope the mechanism cannot deliver.

## Open question

Whether the "Common swaps" table earns its place is **untested**. The eval case
`plain-language-rewrites-jargon` exists to settle it; the A/B procedure is in
`nd/evals/README.md`. One observation favours keeping it — an agent visibly cited the
swap list while rewriting — but that is a single data point, not a result.

## Relations

- affects [[nd plugin skill review]]