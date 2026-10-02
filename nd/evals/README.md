# nd eval suite

45 cases across the eight skills, run with [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals).
Each skill gets three kinds of case:

- **trigger** — natural phrasing that should fire the skill
- **near-miss** — adjacent phrasing that should *not* fire it, guarding against an over-broad `description`
- **applied** — the skill actually doing its job, with the behaviour we care about asserted

Every case runs in two arms by default: with the plugin and without it. `Δ` is what
the plugin contributes. A `Δ` near zero with `skill-fired` failing means the
`description` isn't matching the prompt's phrasing — fix the description, not the body.

## Status

Full run on 2026-10-02 (Sonnet judge, `--ablation none`): 38 of 44 cases passed, about $25 and 20 minutes.
Of the six that did not, three were fixed and re-run alone:

- `onboarding-keeps-injection-and-secrets-out` 8/8 and `onboarding-refuses-readme-as-evidence` 5/5. The cases checked
  the `Write` tool, but with Bash granted the agent may write the docs with a heredoc, so they now read the written
  files. The checker's default citation floor was also unreachable for a five-file repo; that was a real bug and is fixed.
- `delivery-gates-push` 10/10 after the trigger phrases were widened (one run in five had pushed unasked).

The other two are known: `onboarding-full-workflow-on-target-repo` needs `EVAL_TARGET_REPO`, and
`handoff-guards-non-git` fails about one run in twenty on its `records-the-gotcha` regex.

`delivery` is for medium and heavy work where quality matters, not trivial edits. `disciplined-delivery-tests-first` now
uses a medium task (status filter, cursor validation, cap, cursor correctness) and passes 9 of 10 runs;
`disciplined-delivery-skips-trivial-change` keeps the three-line cap out of the skill (5/5). A trivial prompt could not
test test-first: the model judged it too small and skipped the skill.

Fixture secrets must be obviously fake and must not match any provider's key format (a `sk_live_` + 24 character value was blocked by GitHub push protection even though it was invented), because the repo is public and the scanner cannot tell a fake from a real key.

Lessons from this round: grant `Write Edit Bash` when you run the suite, and assert on the files a run produced, not
on one tool's input. A case that sets `HERDR_ENV` or fixes `git` writes shell startup files, only ever inside the
eval's own temporary `HOME` (the scaffolds refuse to run anywhere else).

## Run it

```bash
cd nd

# All 45 cases. `onboarding-full-workflow-on-target-repo` fails its scaffold unless
# EVAL_TARGET_REPO is set, and costs about $36 if it is. Run where Bash is available.
# Sonnet judge — see "Judge noise" below.
claude plugin eval . --scaffold --allow-tools Write Edit Bash --judge-model sonnet -j 4

# Only the cases that need a shell (see "Bash is blocked on some machines").
claude plugin eval . --tag requires-bash --scaffold --allow-tools Write Bash --judge-model sonnet

# One case, or one glob.
claude plugin eval . --case 'plain-language-*'
```

`--tag` is repeatable; `--case` is not — given twice, only the last one runs. Loop over
names, or use a glob.

Seven cases are tagged `requires-bash`: the two `handoff` git cases, `herdr-stops-
outside-herdr`, `architect-stops-without-herdr`, `engineer-joins-as-engineer`,
`engineer-refuses-unauthorized-commit`, and `delivery-shows-before-
committing`. The `handoff`, `herdr`/`architect` and `disciplined-delivery` cases
have a positive-control grader (`git-actually-ran`, `checks-herdr-env`) that **fails**
when run without Bash, or when git cannot run inside the sandbox.
`engineer-refuses-unauthorized-commit` has no such control (it only asserts `git
commit`/`git push` was never *attempted*, which a broken sandbox can't fake either
way). `engineer-joins-as-engineer` needs Bash for a different reason: it's the one
case that actually runs a test suite (Python `unittest`) as part of TDD, not just
shell probes. On a machine where Bash is blocked, run the other eighteen with
`--allow-tools Write Edit` and expect these seven to fail for that reason alone.

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

## Skill names

Every skill's folder name and `name:` are now the same (`delivery`, `reflect`, `herdr`,
`plain-language`, `onboard`, and the three that already matched), so each `skill-fired`
grader matches one name:

```yaml
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?reflect"'
```

Before the rename the graders accepted both the old folder name and the `name:`, because
which one resolved to the command had differed between Claude Code versions. The eval
case folders (`evals/disciplined-delivery/`, `evals/reflecting/`, `evals/onboarding/`) and
the case names inside them keep their old names, so past reports stay comparable.

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
has been **removed** from `plain-language/SKILL.md`.

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

## The `onboarding` cases (run 2026-09-30)

| Case | With | Without | Δ | Cost (10 runs) |
| :--- | :--- | :--- | :--- | :--- |
| `fires-on-onboarding-request` | 1.00 | 0.00 | +1.00 | $0.96 |
| `skips-single-doc-edit` | 1.00 | 1.00 | 0.00 | $0.73 |
| `refuses-readme-as-evidence` | 1.00 | 1.00 | 0.00 | $4.04 |

The trigger case's Δ is structural: its only grader asks whether the skill loaded, and a
baseline has no skill to load, so read it as "fires on natural phrasing, 5/5 with the plugin",
not as proof of quality. The near-miss correctly shows no
over-firing (a baseline also does a one-line edit, so Δ 0 is expected). The applied case
does **not** discriminate: a baseline also trusts the code over a contradicting README on
a three-file repo, so it only shows the skill doesn't break that behaviour. The skill
costs about 3-4x more per run there ($0.52-0.65 vs $0.16).

Scaffold cases need a real `bash` first on `PATH`. On Windows `bash` can resolve to WSL
with no distro installed (`execvpe(/bin/bash) failed`, $0.00 per run): put Git Bash
(for example `scoop\apps\git\current\bin`) first. `--case` globs take `*` only, not
character classes.

### `full-workflow-on-target-repo` (expensive, tagged `expensive`)

End to end on a real repo: `setup.sh` copies the tracked files at HEAD of
`$EVAL_TARGET_REPO` (or the path in a gitignored `target-repo.path`) into the sandbox.
No `Bash` is granted, because a Bash grant is refused on machines with an unreadable
`PATH` directory, so the run cannot execute `checker.py`: **the checker's verdict is not
graded. Run it yourself on the kept workspace** (`--keep-temp`, then
`python nd/skills/onboard/checker.py <ws>/docs/onboarding --layout single --root <ws>`).

First run (before the review-group and reviewer changes below), against a ~1,600-tracked-file Next.js app: 22 subagents (inventory, 4
writers, principal, 4 reviewers, verification and re-review agents, a scoped review of
the orchestrator's edits), 8 docs written in the single layout, no writes outside
`docs/onboarding/`. **$35.90 and it hit the 2,700 s timeout** in the finalize step,
before the final report, so the report grader was never judged. `--max-cost-usd` cannot
cap a single-run case (it is checked only before a run starts), so the real bounds are
`timeout_seconds` and `max_turns` (200 is the maximum). The checker on the kept output
found 0 inadmissible citations, 0 bad line/symbol anchors and 0 placeholders across about
1,500 citations, and two gate findings that were checker or rule bugs, fixed since:
unique *files* were counted instead of unique citations (a 12-file deploy surface with 92
citations failed the minimum), and `` `.env.example` `` written in backticks to say the
file does not exist read as a dangling path. A rerun needs a higher `timeout_seconds`
(3,600 is the maximum) and would cost at least as much, or a smaller repo.

What the trace showed about the review pass: the reviewer covering `engineering.md` and
`runtime-design.md` (about 100 KB together) stalled and returned a one-line status
shaped like a system instruction. It had started its own helper agents, which found about
35 real errors but only reported them. The orchestrator ignored the instruction-like
text, dispatched replacement reviewers and reconciled the leftovers itself (it reports,
for example, 15 edits on `runtime-design.md` alone), which is where the roughly dozen extra
agents came from. The trace does not separate subagent tool calls from the orchestrator's,
so its 168 total edits include the reviewers' own and say nothing about orchestrator load on
their own. The reviewers did find real
mistakes (for example a doc claiming image tags are never overwritten when they are stamped to
the minute), at 15-18 corrections per doc. The skill now caps review groups by size,
forbids reviewer helpers and requires a report with a `Covered` line.

Second run (same case, after those changes), against a 207-tracked-file Next.js prototype
with no backend, CI or Docker: **score 0.82, $21.62, 1,637 s, no timeout.** 10 agents
(4 writers, principal, 5 reviewers, all at full depth) against 22 before: no stalled
reviewer, no replacement, no helpers, every reviewer report ended with `Covered: all`
(824 claims checked in total, 68 corrected, about 8%, inside the skill's 5-10% expectation).
Eight of nine graders passed. The ninth, `honest-final-report`, was **skipped, not failed**:
`--max-cost-usd 15` was below the real spend and the runner skips judge-scored graders once
the ceiling is crossed. Don't set a ceiling below the expected spend on a one-run case.
Reading the final report by hand against that grader's criteria: it says the checker was not
run, gives the command, does not claim a PASS, and reports claims checked (824) and
corrections (68). That is my reading, not a scored result. `checker.py` run afterwards on the
kept workspace (`--layout single --ai-doc runtime-design.md`) printed **PASS**, exit 0, 0
dangling paths, 38 citations in the smallest doc (`deployment.md`). The agents correctly
chose `runtime-design.md` (the repo has no real AI) and wrote a doc for a repo with no CI or
Docker without inventing one. Cost did not scale with repo size: about one eighth of the
files cost about 60% as much, because full-depth review scales with claims, not files.

Limits of that comparison: the two runs used different repos, and this one was about eight
times smaller, so its docs may never have reached the size that stalled the first run's
reviewer. "No stall after the changes" is therefore not evidence that the group-size cap
fixed it. Both repos were single-layout; the tracked layout has only unit tests. The
"824 claims checked, 68 corrected" figures are the reviewers' own counts (the skill itself
says self-reports are not verification); the independent check is the checker run above,
which tests that cited things exist, not that the claims are true.

The checker is covered by `tests/onboarding/test_checker.py`:

```bash
python -m unittest discover -s tests/onboarding -v
```

## Cost

25 cases × 5 runs × 2 arms = 250 agent runs, each a full `claude` child on your own
credential and rate limit. Measured rates from real runs, with `--judge-model sonnet`:
roughly **$0.20 per run** for the `reflecting` cases and **$0.12** for the shorter ones;
the new `architect`/`engineer` cases land in that same range, except
`engineer-joins-as-engineer` (a full TDD cycle with a real test run) at roughly **$0.35
per run**. A full two-arm sweep of the original 18 lands near **$30**. The three
`disciplined-delivery` cases run so far land at roughly **$0.07–0.22 per run**
(2026-09-28); `shows-before-committing` hasn't been run yet, so its cost isn't measured.

Authoring the six `architect`/`engineer` cases (2026-09-24) cost about **$47** in
total, well above that estimate — almost all of it iteration while fixing the fixture
and grader bugs below, not the final clean sweep itself. Budget for that when adding
new cases: the first pass rarely is the one you keep.

Drop to `--runs 1 --ablation none` while iterating on graders, and use `--max-cost-usd`
for a hard ceiling. `results/` is gitignored.

## Onboard run history

Notes that used to sit in `onboard`'s `SKILL.md` and go stale there:

- In the one complete `single`-layout run, about 8% of claims changed during the review pass
  (a few percent to a tenth is the expected range).
- The `tracked` layout has not been measured by a full run. Its cost figure in the skill is a
  projection from the single-layout run.
- The full-workflow case costs about $36 and needs `EVAL_TARGET_REPO`.
