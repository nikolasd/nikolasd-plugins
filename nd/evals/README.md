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

# All 12 cases, where Bash is available. Sonnet judge — see "Judge noise" below.
claude plugin eval . --scaffold --allow-tools Write Bash --judge-model sonnet -j 4

# Only the three cases that need a shell (see "Bash is blocked on some machines").
claude plugin eval . --tag requires-bash --scaffold --allow-tools Write Bash --judge-model sonnet

# One case, or one glob.
claude plugin eval . --case 'plain-language-*'
```

`--tag` is repeatable; `--case` is not — given twice, only the last one runs. Loop over
names, or use a glob.

Three cases are tagged `requires-bash`: the two `handoff` git cases and
`herdr-stops-outside-herdr`. Each has a positive-control grader (`git-actually-ran`,
`checks-herdr-env`) that **fails** when run without Bash, or when git cannot run inside
the sandbox. On a machine where Bash is blocked, run the other nine with
`--allow-tools Write` and expect those three to fail for that reason alone.

Where it matters today (Claude Code 2.1.280): `herdr-stops-outside-herdr` runs
correctly on macOS; the two git cases need Linux (see "macOS: Bash runs, but git does not").

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

## Cost

12 cases × 5 runs × 2 arms = 120 agent runs, each a full `claude` child on your own
credential and rate limit. Measured rates from real runs, with `--judge-model sonnet`:
roughly **$0.20 per run** for the `reflecting` cases and **$0.12** for the shorter ones,
so a full two-arm sweep lands near **$20**. The 10 local cases in one arm at 5 reps cost
about **$8**.

Drop to `--runs 1 --ablation none` while iterating on graders, and use `--max-cost-usd`
for a hard ceiling. `results/` is gitignored.
