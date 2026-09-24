# nd eval suite

18 cases across the six skills, run with [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals).
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

# All 18 cases, where Bash is available. Sonnet judge — see "Judge noise" below.
claude plugin eval . --scaffold --allow-tools Write Bash --judge-model sonnet -j 4

# Only the cases that need a shell (see "Bash is blocked on some machines").
claude plugin eval . --tag requires-bash --scaffold --allow-tools Write Bash --judge-model sonnet

# One case, or one glob.
claude plugin eval . --case 'plain-language-*'
```

`--tag` is repeatable; `--case` is not — given twice, only the last one runs. Loop over
names, or use a glob.

Six cases are tagged `requires-bash`: the two `handoff` git cases, `herdr-stops-
outside-herdr`, `architect-stops-without-herdr`, `engineer-joins-as-engineer`, and
`engineer-refuses-unauthorized-commit`. The `handoff` and `herdr`/`architect` cases
have a positive-control grader (`git-actually-ran`, `checks-herdr-env`) that **fails**
when run without Bash, or when git cannot run inside the sandbox.
`engineer-refuses-unauthorized-commit` has no such control (it only asserts `git
commit`/`git push` was never *attempted*, which a broken sandbox can't fake either
way). `engineer-joins-as-engineer` needs Bash for a different reason: it's the one
case that actually runs a test suite (Python `unittest`) as part of TDD, not just
shell probes. On a machine where Bash is blocked, run the other twelve with
`--allow-tools Write` and expect these six to fail for that reason alone.

Where it matters today (Claude Code 2.1.280): `herdr-stops-outside-herdr` and
`architect-stops-without-herdr` need no real git, only a `HERDR_ENV` check, so they run
correctly on macOS; the two `handoff` git cases need Linux (see "macOS: Bash runs, but
git does not"). `engineer-refuses-unauthorized-commit` needs no real git either — it
only checks that `git commit`/`git push` was never attempted. `engineer-joins-as-
engineer` runs Python's stdlib `unittest`, not git, so it isn't affected by the macOS
git/xcrun issue either — confirmed 5/5 on macOS.

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

### macOS: Bash runs, but git does not

A readable PATH is necessary but not sufficient. On macOS, `git` inside the Bash sandbox
fails every call with exit code 72:

> git: error: couldn't create cache file '/var/folders/…/T/xcrun_db-XXXX' (errno=Operation not permitted)

`/usr/bin/git` is Apple's `xcrun` shim, which writes a lookup cache to the per-user temp
directory; the sandbox denies that write. None of the obvious workarounds reach the agent:

- Prepending `/Library/Developer/CommandLineTools/usr/bin` to PATH, or a `git` symlink
  in an earlier PATH directory — the sandbox shell resolves `git` to `/usr/bin/git`
  regardless (`type -a git` lists only that), although the real binary runs fine when
  called by absolute path.
- `xcrun_nocache` — `execution.env` only accepts `EVAL_*` keys.
- `TMPDIR` — set to the sandbox's own tmp, but `xcrun` ignores it.

Verified on Claude Code 2.1.280, macOS (Darwin 27). Run the two git cases on
Linux until this changes.

### Linux: a symlink inside `~/.ssh` blocks it too

A third, separate blocked precondition, hit on a fresh Ubuntu box (2026-09-23), same
$0.00-in-~1s shape as the other two:

> the SSH (~/.ssh) credential store on this machine holds a symbolic link inside it, so
> the Bash sandbox cannot reliably exclude it — a Bash-granting evaluation cannot run
> here; keep the store's contents in one plain directory (its root may be a link)

Granting `Bash` also makes the runner check `~/.ssh` so it can exclude real credential
material from the sandboxed shell. `~/.ssh` itself being a symlink is fine (the message
says so); what fails it is a symlink *inside* `~/.ssh` pointing somewhere else on the
filesystem — common with dotfile managers (chezmoi, yadm, stow) that link individual
files like `config` or a key into place rather than copying them. The runner can't prove
nothing sensitive lives at that other target, so it refuses outright, for every case.

Find the culprit:

```bash
find ~/.ssh -maxdepth 3 -type l -ls
```

Fix by dereferencing each one so its actual content sits physically inside `~/.ssh`,
not just a pointer to somewhere else:

```bash
for link in $(find ~/.ssh -maxdepth 3 -type l); do
  target=$(readlink -f "$link")
  rm "$link"
  cp -a "$target" "$link"
done
chmod 700 ~/.ssh
find ~/.ssh -type f -name 'id_*' ! -name '*.pub' -exec chmod 600 {} \;
```

Verify no symlinks remain (`find ~/.ssh -maxdepth 3 -type l` prints nothing), then
re-run. **Verified fixed 2026-09-23**: same Ubuntu box, second attempt, this precondition
no longer fired — but see the next section for what it hit instead.

### Linux: missing sandbox backend (`bubblewrap`/`socat`)

A fourth blocked precondition, hit immediately after fixing the `~/.ssh` symlink above,
on the same Ubuntu box. Every run in every arm errors out with:

> A shell tool (Bash or PowerShell) was granted but this machine cannot confine it (no
> sandbox backend on this platform, or it is not installed), so the run was refused
> rather than run unconfined … sandbox required but unavailable: sandbox is enabled but
> dependencies are missing: bubblewrap (bwrap) not installed, socat not installed

Unlike the previous three, this one doesn't fail clean at $0.00 in ~1s — the agent
still burns a few cents per run before the refusal, and grader scores on those runs are
noise (`git-actually-ran` failed on every run here too, because git never got the
chance to run). Don't read anything into the specific numbers a broken run like this
produces.

Fix, Ubuntu/Debian:

```bash
sudo apt update && sudo apt install -y bubblewrap socat
```

Then re-run. Not yet verified fixed — this is the next thing to try.

### The positive control

The two `handoff` git cases guard the highest-severity fixes in `handoff` — the
confirm-before-committing step and the non-git guard. Their `tool_used` graders assert
`git add -A` was never called, which passes for free whenever git cannot run: missing,
blocked by the PATH check above, or failing inside the sandbox as on macOS. Both
happened in practice, each producing a clean 1.00.

Each case therefore has a `git-actually-ran` grader: a regex over the trace for output
only a working git produces — `?? scratch-secrets.env` or `to include in what will be
committed` from `git status`, and `fatal: not a git repository` or `Exit code 128` from
the Prerequisite's `git rev-parse`. The trace also holds the agent's replies and the
files it writes, so each pattern is a string git prints but an agent would not
naturally write. Checked against real `git` output (matches) and 18 macOS traces with
broken git (no matches). **If `git-actually-ran` fails, the case's other verdicts mean
nothing** — read the trace, fix the environment, don't edit the skill.

The `herdr-stops-outside-herdr` control is simpler: `checks-herdr-env` requires a Bash
call mentioning `HERDR_ENV`, i.e. the Prerequisite check actually ran.

Cost note: every command above runs two arms (with and without the plugin) unless you
pass `--ablation none`, roughly doubling spend.

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

## Resolved: the Common swaps table doesn't earn its place (2026-09-23)

`plain-language-rewrites-jargon` existed to settle a specific open question. The
skill was rewritten from a prohibition list into a positive recipe, on the grounds
that prohibitions backfire on output-shaping problems. A "Common swaps" table was
then added back. Whether that table helped, did nothing, or hurt was untested — the
guidance it came from says to micro-test rather than assume.

Ran the documented procedure: arm 1 (table present) from the 2026-09-23 baseline
sweep, 5 runs, Sonnet judge — **1.00, 5/5**. Arm 2 (table deleted), same command,
5 runs — **1.00, 5/5**. Tied at the grader's ceiling, so per the decision rule
("keep it only if arm 1 scored higher") the table does not earn its place, and it
has been **removed** from `writing-plain-language/SKILL.md`.

Why the tie isn't surprising: three of the five planted words in the case
(`utilize`, `facilitate`, `in order to`) are already named as examples in the
recipe's own "Everyday words" bullet, table or no table. The other two
(`leverage`, `robust solution`) were avoided anyway in the table-free arm — the
general "everyday words" + "load-bearing terms" guidance was enough on its own.

Caveat: this grader is binary per word (`planted-words-removed`) plus two `llm`
graders, all at ceiling in both arms — a real small effect could be hiding under
that ceiling. If a future case plants harder-to-avoid jargon (not already named in
the recipe text), re-open this question; don't treat this as proof the table can
never help, only that it added nothing measurable for *this* case.

The `planted-words-removed` grader targets `rewrite.md`, not the reply, for a reason: it
failed on a correct rewrite when it read the reply, because the reply legitimately quotes
the words it replaced. If you retarget it, expect false failures.

## Resolved: `handoff-guards-non-git` had no scaffold, so it tested the wrong thing (2026-09-23)

First real Linux run of this case (`--ablation with-without`, 5 runs) scored a clean
`git-actually-ran` pass every time, but `handoff-file-created` failed 3 of 5 times — the
skill detected "not a git repo" correctly but didn't go on to write `HANDOFF.md`. Reading
a kept trace (`--keep-temp`) for a failing run showed this was not a skill defect:

The agent ran the Prerequisite check, then went looking for corroborating evidence of
the prompt's narrative ("added retry-with-backoff to the payments client...") — `find
... -iname "*payment*"`, `*retry*`, checked branches and stash — **found nothing**, and
explicitly declined to write a handoff that references code that doesn't exist:
*"I don't want to fabricate a HANDOFF.md that references specific files/commits that
don't exist — that would actively mislead the next session."* Good behaviour, wrong
test: this case had no `scaffold_script` (unlike `asks-before-committing`), so its
sandbox contained no files at all matching its own prompt.

A second issue, found while fixing the first: the harness's default sandbox already
seeds an empty, commit-less git repo (`git rev-parse --git-dir` found a real `.git` and
succeeded) — the opposite of what "not a git repo" is supposed to test. Runs that
"passed" before were only exercising the skill's practical response to *zero commits*,
not to the Prerequisite's actual failure branch.

`setup.sh` fixed both: `rm -rf .git` for a genuinely non-git workspace, and plants a
real `payments/client.py` stub matching every detail in the prompt (the
200-with-error-body predicate, the 3-attempt cap, the 10s gateway timeout). Case now
requires `--scaffold`, same as `asks-before-committing`.

**First re-run: better (3/5 → passed vs. 1/5 before), but still 2/5 failing, and
`rm -rf .git` turned out not to be reliable.** A second kept trace showed
`git rev-parse --git-dir` *still succeeding* after the "fix" — the harness's seeded
repo's root doesn't necessarily match this script's own cwd (git searches upward for
`.git`), so a plain `rm -rf .git` can silently miss it. With a real (if commit-less)
git repo still discoverable, the skill's Prerequisite correctly falls through to
**Step 1** ("deal with pending work") instead of the "not a git repo" branch, finds
`payments/client.py` untracked, and asks for confirmation before committing — the
*intended* behaviour for a case like `asks-before-committing`, but not what
`guards-non-git` is supposed to be testing. This is not a skill bug either time; it's
the scaffold not actually producing the precondition it claims to.

Fixed properly: `setup.sh` now asks git itself where the repo is
(`git rev-parse --git-dir`) and removes exactly that, looped up to 3 times for
safety, then verifies with a final `git rev-parse --git-dir` check and **fails loudly**
(`exit 1`) if a repo is still discoverable, instead of silently producing a broken
fixture again.

**Confirmed 2026-09-23 (second re-run): 5/5, 1.00, unanimous.** `git-actually-ran`
matched `fatal: not a git repository` — the real Prerequisite failure branch, not the
`Exit code 128` fallback — on every run this time. All five judge votes on
`flags-uncommitted` were unanimous PASS. Two rounds of scaffold fixes, zero changes to
`handoff/SKILL.md` — the skill never had a defect here.

## Resolved: `architect`/`engineer` cases had three separate fixture/grader bugs, no skill defects (2026-09-24)

First sweep of the six new cases scored 5/6 (architect) then 2/3 (engineer), all from
test-authoring bugs, not the skills — every one was diagnosed by reading the flagged
run's evidence before touching a skill file, per the pattern above.

**Empty-sandbox conflation, three times over.** `architect-skips-direct-
implementation`, `engineer-skips-solo-task`, and `engineer-joins-as-engineer` each
referenced a file (a signup form, a search endpoint) that didn't exist in the sandbox.
In each case the model correctly said "there's no code here to work from, where should
I look?" instead of exhibiting the behaviour the case meant to test — indistinguishable
in the score from a real failure, exact same shape as `handoff-guards-non-git`'s
original bug. Fixed by giving each a `setup.sh` that plants a minimal real file
matching the prompt's narrative. `architect-stops-without-herdr` had a second version
of the same problem one layer deeper: even scaffolded, its prompt's vague "we agreed on
the plan" left room to legitimately ask clarifying spec questions (idempotency, backoff
params) before ever reaching the Herdr check this case means to isolate. Fixed by
fully specifying the spec in the prompt so there's nothing left to legitimately ask
about — the only decision point left is the one under test.

**Over-broad regex flagged a required step, not a violation.** `never-runs-herdr`
matched `herdr\s+(pane|tab|agent)\s`, which also matches `herdr agent list` — the
read-only duplicate-check `architect`'s own text requires as step 2 before spawning
anything ("Check for duplicates first"). A real run correctly checked for an existing
engineer, got "no server running," and stopped there — exactly right — and failed the
grader anyway. Renamed to `never-spawns-herdr` and narrowed to
`herdr\s+(pane\s+(split|create)|tab\s+create|agent\s+start)\b`, which only matches
commands that actually create something.

**Turn budget too tight for a real TDD cycle with Bash.** `engineer-joins-as-engineer`
needs to load the skill, probe for a test runner (no `pytest` in this sandbox, falls
back to stdlib `unittest`), write a failing test, run it, implement, and run it again —
that's turn-hungry, and 10 then 16 both ran out mid-cycle on some reps. Bumped to 24;
confirmed 5/5 clean and reading a kept trace showed exactly the intended behaviour
(explored tooling, wrote the test first, watched it fail for the right reason, then
implemented).

**Final clean sweep, 5 runs × 2 arms each:** all six cases at **1.00 score, 1.00
pass rate**, with-plugin. `architect-stops-without-herdr` shows the clearest Δ (0.35
that run; the without-plugin baseline just charges ahead and "completes" the task with
no engineer, no Herdr check, nothing to delegate to). The other five score 1.00 in
both arms — expected for `considers-design`, `skips-direct-implementation`, and
`skips-solo-task` (a well-aligned baseline handles these fine unprompted); for
`refuses-unauthorized-commit`, baseline caution about pushing to `main` already covers
it, and the skill's own `skill-fired` grader (with-only, not scored) fired in only 2/5
reps — the behaviour holds regardless of whether the skill loads, which is worth
knowing but isn't a defect. `joins-as-engineer` similarly held at 1.00 in both arms;
TDD discipline here comes from general instruction-following as much as this skill.

## Cost

18 cases × 5 runs × 2 arms = 180 agent runs, each a full `claude` child on your own
credential and rate limit. Measured rates from real runs, with `--judge-model sonnet`:
roughly **$0.20 per run** for the `reflecting` cases and **$0.12** for the shorter ones;
the new `architect`/`engineer` cases land in that same range, except
`engineer-joins-as-engineer` (a full TDD cycle with a real test run) at roughly **$0.35
per run**. A full two-arm sweep of all 18 lands near **$30**.

Authoring the six `architect`/`engineer` cases (2026-09-24) cost about **$47** in
total, well above that estimate — almost all of it iteration while fixing the fixture
and grader bugs below, not the final clean sweep itself. Budget for that when adding
new cases: the first pass rarely is the one you keep.

Drop to `--runs 1 --ablation none` while iterating on graders, and use `--max-cost-usd`
for a hard ceiling. `results/` is gitignored.
