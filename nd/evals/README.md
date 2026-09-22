# nd eval suite

12 cases across the four skills, run with [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals).
Each skill gets three kinds of case:

- **trigger** — natural phrasing that should fire the skill
- **near-miss** — adjacent phrasing that should *not* fire it, guarding against an over-broad `description`
- **applied** — the skill actually doing its job, with the behaviour we care about asserted

Every case runs in two arms by default: with the plugin and without it. `Δ` is what
the plugin contributes. A `Δ` near zero with `skill-fired` failing means the
`description` isn't matching the prompt's phrasing — fix the description, not the body.

## Run it

```bash
cd nd

# The 10 cases that run anywhere. Sonnet judge — see "Judge noise" below.
claude plugin eval . --allow-tools Write --judge-model sonnet -j 4 --tag handoff \
  --tag reflecting --tag herdr --tag plain-language

# The two git cases, where Bash is available (see "Bash is blocked on some machines").
claude plugin eval . --tag requires-bash --scaffold --allow-tools Write Bash

# One case.
claude plugin eval . --case 'plain-language-*'
```

Read `handoff/asks-before-committing/setup.sh` before passing `--scaffold` — the flag
runs author-supplied bash as you.

## Judge noise is the first thing to rule out

**Never draw a conclusion from a single run.** Two cases in the first smoke run flipped
completely between identical invocations, both times with unanimous 3–0 judge votes in
opposite directions:

| Case | Run A | Run B |
| :--- | :--- | :--- |
| `reflecting-asks-before-writing` | 1.00 (PASS×3) | 0.60 (FAIL×3) |
| `reflecting-skips-single-fact`   | 0.50 (FAIL×3) | 1.00 (PASS×3) |

Reading the kept transcript showed the skill behaved correctly in both. The judge was
wrong, not the plugin. So:

- Run at least 5 reps on any case whose verdict you intend to act on. Every case here
  sets `runs: 5` for that reason; drop to `--runs 1` only while iterating on graders,
  and never read the result as a finding.
- Use `--judge-model sonnet`. Haiku failed a textbook-correct 450-word response because
  a long blockers section buried the part the rubric asked about.
- When a verdict surprises you, read the transcript before editing a skill:

```bash
claude plugin eval . --case <name> --keep-temp --runs 5
# then read out/trace.jsonl in the printed temp dir, and delete the dir afterwards
```

Rubrics here are written to be decidable from one or two structural conditions, with an
explicit instruction to ignore length and extra sections. Keep new ones that way.

## Bash is blocked on some machines

Granting `Bash` makes the runner enumerate every PATH directory to exclude credential
helpers. If any entry is unreadable it refuses outright, and **every case fails in about
one second for $0.00** with:

> a PATH directory could not be examined for keychain credential helpers (EPERM), so the
> Bash sandbox cannot exclude them — a Bash-granting evaluation cannot run in this
> environment

That is not a finding about the plugin. On the author's machine the culprit is
`C:\Program Files (x86)\Automox\`, which is endpoint-management software and unreadable
by design. Stripping it from the child process's PATH does *not* help — the runner reads
machine PATH directly. Find your own culprit with:

```powershell
$env:PATH -split ';' | Where-Object { $_ } | ForEach-Object {
  try { Get-ChildItem -LiteralPath $_ -Force -ErrorAction Stop | Out-Null }
  catch { "UNREADABLE $_" } }
```

The two `requires-bash` cases guard the highest-severity fixes in `handoff` — the
confirm-before-committing step and the non-git guard. **Do not run them without Bash.**
They score 1.00 vacuously: their `tool_used` graders assert `git add -A` was never
called, which passes for free when `git` was never reachable. Run them in CI on Linux,
or on a machine with a clean PATH. Until then those two fixes rest on code review alone.

## Skill names are matched permissively

Each `skill-fired` grader accepts both the `name:` in `SKILL.md` and the directory
name, because which one resolves to the command has differed between Claude Code
versions:

```yaml
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?(?:reflect|reflecting)"'
```

A useful side effect: the trace in the HTML report shows which form actually fired,
which answers the question directly. If it's stable across versions you care about,
tighten these to the one real form.

## The pending A/B: does the Common swaps table help?

`plain-language-rewrites-jargon` exists to settle a specific open question. The
skill was rewritten from a prohibition list into a positive recipe, on the grounds
that prohibitions backfire on output-shaping problems. A "Common swaps" table was
then added back. Whether that table helps, does nothing, or hurts is untested — the
guidance it came from says to micro-test rather than assume.

Early evidence favours keeping it. In the first run the agent's reply cited the swap
list explicitly — "utilized → runs, leverage → turn on, in order to facilitate → for
you" — which is the table doing visible work. That is one observation, not a result.

Procedure:

1. `claude plugin eval . --case plain-language-rewrites-jargon --ablation none --runs 5 --allow-tools Write --judge-model sonnet`
   and record the score.
2. Delete the `## Common swaps` section from `skills/writing-plain-language/SKILL.md`.
3. Run the same command again and record the score.
4. Restore the section. Keep it only if arm 1 scored higher.

Five runs per arm, not three, because the effect is expected to be small.

The `planted-words-removed` grader targets `rewrite.md`, not the reply, for a reason: it
failed on a correct rewrite when it read the reply, because the reply legitimately quotes
the words it replaced. If you retarget it, expect false failures.

## Cost

12 cases × 5 runs × 2 arms = 120 agent runs, each a full `claude` child on your own
credential and rate limit. Measured rates from real runs, with `--judge-model sonnet`:
roughly **$0.20 per run** for the `reflecting` cases and **$0.12** for the shorter ones,
so a full two-arm sweep lands near **$20**. The 10 local cases in one arm at 5 reps cost
about **$8**.

Drop to `--runs 1 --ablation none` while iterating on graders, and use `--max-cost-usd`
for a hard ceiling. `results/` is gitignored.
