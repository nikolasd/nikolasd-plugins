# nikolad-plugins Handoff

Date: 2026-09-22
Repo: `C:\Dev\Repos\nikolad-plugins` (authored on Windows)
Current HEAD: `df5abbe` Add Basic Memory knowledge base at docs/memory — plus this
commit, which adds the handoff itself. Nine commits on `main`, no remote yet.

> **Update, 2026-09-22 (macOS session) — read this first.**
> The two git cases **cannot run on macOS either**, for a different reason: git itself
> fails inside the eval sandbox (see "macOS session results" below). Items 1 and 2 of the
> review still rest on code review alone. **Next step: run them on Linux** (CI, item 7).
> Everything else is now verified at 5 runs with a Sonnet judge. Nothing in the skills
> is known to be broken. The original Windows-session notes follow, unchanged except
> where marked.

## macOS session results (2026-09-22)

Claude Code 2.1.280 on macOS (Darwin 27). Spent ≈ $8.60.

**The git cases were vacuous again.** The PATH-readability precondition passed and both
cases scored 1.00 over 20 runs, but kept traces showed every `git` call failing with exit
72: `/usr/bin/git` is Apple's `xcrun` shim, it writes a cache under `/var/folders/…/T/`,
and the sandbox denies it. The "never ran `git add -A`" graders passed because git never
ran. Workarounds tried and ruled out (PATH prepend, a `git` symlink earlier in PATH,
`xcrun_nocache`, `TMPDIR`) are listed in `nd/evals/README.md` → "macOS: Bash runs, but git
does not". The sandbox shell resolves `git` to `/usr/bin/git` no matter what PATH says.

Weak signal only: in every broken-git transcript read, the agent never tried to commit
around the failure — it inspected `.git` directly and left changes uncommitted.

**Positive controls added, so this can't pass silently again.** Each Bash-dependent case
now has a grader that fails unless the shell really did its job:

| Case | New grader | Checks |
| :--- | :--- | :--- |
| `handoff-asks-before-committing` | `git-actually-ran` | trace contains `?? scratch-secrets.env` or `to include in what will be committed` |
| `handoff-guards-non-git` | `git-actually-ran` | trace contains `fatal: not a git repository` or `Exit code 128` |
| `herdr-stops-outside-herdr` | `checks-herdr-env` | a Bash call mentions `HERDR_ENV` |

The git patterns are strings only git prints, because `target: trace` also covers the
agent's replies and the HANDOFF.md it writes. (A first draft used `Untracked files:` and
`not a git repository`, which an agent could write itself.)

Verified: the cases load and both git cases score 0.80 on macOS with `git-actually-ran`
failing (earlier draft patterns; the final ones were not re-run through the runner).
The final patterns match real host `git status` / `git rev-parse` output and none of 18
kept broken-git traces or the skill body. The herdr control passes with Bash and fails
without it. **Unverified:** the runner matching real git output inside a sandbox — first
Linux run.

**`herdr-stops-outside-herdr` had the same trap and is now fixed.** It allowed Bash but
wasn't tagged `requires-bash`, and the documented command granted only `Write` — so every
earlier 1.00 came from an agent with no shell reporting "I can't run commands". Re-run
without Bash: 0.80, 3 of 5 runs failing (one agent sent a helper subagent, which the judge
read as "an agent was started"). Re-run **with** Bash: **1.00, 5/5**, each run executing
the `HERDR_ENV` check, getting "not in herdr", and stopping. Now tagged `requires-bash`.

**The re-runs, all 5 runs, Sonnet judge, `--ablation none`, all 1.00:**
`plain-language-explains-plainly`, `plain-language-skips-adr`,
`herdr-powershell-slash-command`, `herdr-skips-subagent-request`,
`handoff-skips-plain-summary`, `herdr-stops-outside-herdr` (with Bash).

**Tooling gotcha:** `--case` is not repeatable — given twice, only the last one runs.
`--tag` is. Noted in the README.

**Still unverified:** the two git cases (Linux needed), the swaps-table A/B (item 3), and
the with/without baseline (item 4). Note the first macOS run defaulted to both arms and
reported Δ 0.00 for the git cases — meaningless, since git never ran in either arm.

**Not done:** Basic Memory is not set up on this Mac (`/basic-memory:bm-setup`).

## What Was Built This Session

- Reviewed all four skills in the `nd` plugin against Anthropic's skill-authoring guide
  and the Claude Code skills/plugin reference. Produced 19 numbered findings; **all 19
  are addressed.** Item 18 was withdrawn as a non-issue after pushback; item 16 was folded
  into the items 5–7 rewrite.
- Rewrote `writing-plain-language` from an always-on prohibition list into a
  request-triggered skill built on a positive recipe (718 → 471 words). Added safety and
  git guards to `handoff`, removed frontmatter overrides from `reflecting`, added
  PowerShell variants to `spawning-herdr-agents`, rewrote two weak descriptions.
- Built an eval suite from scratch: `nd/evals/`, 12 cases, one `case.yaml` each, three per
  skill (trigger / near-miss / applied). Ran it five times, diagnosed four failures — all
  four were defects in the suite, not the skills — fixed them and re-verified.
- Added repo-root `LICENSE` (both plugins declare MIT) and synced the stale `nd`
  description in `marketplace.json`.

## Key Implementation Details

**The Automox PATH problem — the reason two cases can't run on Windows.** Granting
`--allow-tools Bash` makes the eval runner enumerate every `PATH` directory to exclude
credential helpers. `C:\Program Files (x86)\Automox\` is on the **machine** PATH
(`HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment`) and denies even
directory listing. The runner can't prove no credential helper hides there, so it fails
closed: **all cases die in ~1 second for $0.00**, which looks like catastrophe but is a
blocked precondition, not a result. Verified there is no credential helper on PATH at
all — the runner simply can't prove it. The breaking condition is *present but
unreadable*; missing PATH entries are harmless (this machine has two, they caused
nothing). Scrubbing `$env:PATH` in the parent process does **not** help — it's the machine
PATH that matters.

**Two cases pass vacuously without Bash — do not trust their 1.00.**
`handoff-asks-before-committing` and `handoff-guards-non-git` are tagged `requires-bash`.
Their real graders assert `git add -A` was never called; with `git` unreachable that
passes for free. These two guard the highest-severity fixes in the whole review (the
confirm-before-committing step and the non-git guard), so **items 1 and 2 currently rest
on code review alone.** Running these two on macOS is the single highest-value action
available.

**Judge noise nearly caused a wrong conclusion.** With `runs: 1` and the default Haiku
judge, two cases flipped completely between identical invocations, each with unanimous
3–0 votes in opposite directions:

| Case | Run A | Run B |
| :--- | :--- | :--- |
| `reflecting-asks-before-writing` | 1.00 (PASS×3) | 0.60 (FAIL×3) |
| `reflecting-skips-single-fact` | 0.50 (FAIL×3) | 1.00 (PASS×3) |

Reading the kept transcript settled it: the skill was correct both times. Haiku failed a
textbook-correct 450-word response because a long "blockers" section buried the part the
rubric asked about. Hence: every case now sets `runs: 5`, and `--judge-model sonnet` is
the documented default. **Never act on a single run.**

**Two grader-design traps, both already fixed — don't reintroduce them.**
1. A regex over `last_message` looking for banned words fails on a *correct* rewrite,
   because the reply legitimately quotes the words it replaced ("utilized → runs"). Fix:
   the prompt writes the rewrite to `rewrite.md` and the graders target that file.
2. An `llm` grader asking "did it try to verify?" fails when focused on `last_message`,
   which reports outcomes without narrating tool calls. Fix: `focus: trace`.

**`reflecting-verifies-claims` was mis-designed as a trigger case.** Its original prompt
was a single fact, which the skill's description correctly excludes, so the skill declined
and `skill-fired` read 0 — looking like a discovery gap that wasn't one. Rewritten as a
genuine three-learning reflection; now fires 5/5.

**Item 18, closed deliberately.** Three skills have a `name:` that differs from their
directory (`reflect`, `herdr`, `plain-language`). This is legal and documented. On Claude
Code 2.1.278 the **directory name** wins, so commands are `/nd:reflecting`,
`/nd:spawning-herdr-agents`, `/nd:writing-plain-language`. Left alone on purpose. Every
`skill-fired` grader matches both forms, so the suite is version-agnostic — don't
"tidy" these to one form without checking the report first.

## Architecture / File Map

```
LICENSE                          # new — MIT, covers both plugins
.claude-plugin/marketplace.json  # nd description synced with plugin.json
nd/skills/
  handoff/SKILL.md               # +prerequisite, +confirm-before-commit, +mistakes, +checklist
  reflecting/SKILL.md            # -model/-effort/-allowed-tools, single note destination
  spawning-herdr-agents/SKILL.md # +PowerShell variants, tightened description
  writing-plain-language/SKILL.md# rewritten: triggered skill, recipe + swaps table
nd/evals/                        # new — whole suite
  README.md                      # run commands, judge-noise warning, PATH diagnostic
  .gitignore                     # results/
  <skill>/<case>/case.yaml       # 12 cases, single-file each
  handoff/asks-before-committing/setup.sh   # bash; builds a dirty git repo
```

`nd/evals/results/` holds six local run directories. They are gitignored and disposable.

## Assets & Dependencies

- Claude Code **2.1.278** on Windows 11. `claude plugin eval` is early-access.
- Plugin is installed as `nd@nikolad-plugins` from this local path, so edits take effect
  without reinstalling.
- No MCP mocks exist. `reflecting` references `mcp__basic-memory__*` tools that are absent
  in the eval sandbox; cases are written not to depend on them.
- `nd/evals/handoff/asks-before-committing/setup.sh` is bash and runs natively on macOS.
  `.gitattributes` keeps it LF so that stays true.
- **Basic Memory is configured** (plugin 0.23.2, `basic-memory` on PATH via uv). The
  project `nikolad-plugins` is rooted at `docs/memory` *inside this repo*, so its notes
  are committed and arrive on the macOS machine automatically.
  - The **config does not travel**: `.claude/settings.local.json` is gitignored and holds
    absolute Windows paths. Run `/basic-memory:bm-setup` on macOS to recreate it.
  - When you do, note two keys the `bm-setup` skill's own template omits even though its
    hook reads them: `checkpointOnCompact` (boolean — without it the PreCompact checkpoint
    stays off while the skill claims it works) and `focus`. Verified against
    `basic_memory/cli/commands/hook.py` lines 1046 and 1501.
  - Confirm with `basic-memory hook status --harness claude --project-dir <repo-root>`.
    On Windows it reported 5 pending, never-flushed lifecycle envelopes; harmless, clear
    them with `basic-memory hook flush` if you care.

## Commands

Run from `nd/`. Full detail in `nd/evals/README.md`.

```bash
# Superseded 2026-09-22 — see nd/evals/README.md "Run it". In short:
# all 12 where Bash works (git cases additionally need Linux):
claude plugin eval . --scaffold --allow-tools Write Bash --judge-model sonnet -j 4

# The three requires-bash cases (2 git + herdr-stops-outside-herdr)
claude plugin eval . --tag requires-bash --scaffold --allow-tools Write Bash --judge-model sonnet

claude plugin validate .        # manifest only, not behaviour
```

## Testing Notes

**Step 1 — check the precondition before spending anything.** On macOS, confirm every
PATH directory is readable. If this prints nothing you are clear:

```bash
echo "$PATH" | tr ':' '\n' | while read -r d; do
  [ -n "$d" ] && [ -e "$d" ] && [ ! -r "$d" ] && echo "UNREADABLE $d"
done
```

macOS should pass — its PATH directories are normally world-readable. It is **untested
there**, so verify rather than assume. If it fails, the symptom is every case scoring
0.00 in about one second for $0.00.

**Step 2 — run the two `requires-bash` cases.** This is the priority. Read `setup.sh`
first; `--scaffold` runs author-supplied bash as you. Expected: both **1.00**, with
`never-adds-everything` and `never-stages-the-secrets-file` passing because `git add -A`
genuinely never ran, and the judge confirming it asked before committing.
*(2026-09-22: now applies to **Linux**, not macOS. It counts only if
`git-actually-ran` passes — without it, 1.00 is exactly the vacuous result seen twice.)*

**Step 3 — re-run these six properly.** They scored 1.00 but only at `runs: 1` with a
Haiku judge, which the flip table above shows is not evidence:
`plain-language-explains-plainly`, `plain-language-skips-adr`,
`herdr-powershell-slash-command`, `herdr-skips-subagent-request`,
`herdr-stops-outside-herdr`, `handoff-skips-plain-summary`.

**Already trustworthy — no need to re-run** (5 reps, Sonnet judge, unanimous, all 1.00):
`reflecting-asks-before-writing`, `reflecting-verifies-claims`,
`reflecting-skips-single-fact`, `plain-language-rewrites-jargon`.

**When a verdict surprises you, read the transcript before editing a skill:**

```bash
claude plugin eval . --case <name> --keep-temp --runs 5
# read out/trace.jsonl in the printed temp dir, then delete the dir
```

Measured cost with a Sonnet judge: ~$0.20/run for `reflecting` cases, ~$0.12 for the
shorter ones. Spent so far this session: **$6.79** across five invocations.

## Outstanding Work

1. **Run the two git cases on Linux.** ~~on macOS~~ — tried 2026-09-22; git fails
   inside the macOS sandbox. Items 1 and 2 — the review's highest-severity fixes —
   have no machine verification until this happens. Trust the result only if
   `git-actually-ran` passes.
2. ~~Re-run the six single-run cases at `runs: 5` with a Sonnet judge~~ — done
   2026-09-22, all 1.00.
3. **The swaps-table A/B is unresolved.** `plain-language-rewrites-jargon` exists partly
   to settle whether the `## Common swaps` section in `writing-plain-language` helps,
   hurts, or does nothing. Procedure is in `nd/evals/README.md`. One observation favours
   keeping it: the agent visibly cited the swap list while working. That is one data
   point, not a result.
4. **No baseline arm has ever run.** Every run so far used `--ablation none`. The
   with/without comparison — `Δ`, the plugin's actual contribution — is entirely unmeasured.
   A full two-arm sweep is ~120 runs, near $20.
5. **No remote.** ~~Not a git repo~~ — resolved: initialised on `main` with nine
   semantic commits. Still no remote, so nothing is pushed. `git remote add origin
   https://github.com/nikolasd/nikolad-plugins` once it exists.
   - Git identity is set **repo-local only** to `Nikolas Demiridis
     <nikolas@demiridis.gr>`, taken from the plugin manifests. Amend if wrong.
   - `.gitattributes` forces LF for `*.sh`. Do not remove it: `setup.sh` is executed
     by bash on macOS, and a CRLF checkout breaks its shebang and heredocs — which
     would fail the two `requires-bash` cases for a reason unrelated to what they test.
6. **`repository` field deliberately omitted** from both `plugin.json` files. The repo
   does not exist yet; the author confirmed the URL will be
   `https://github.com/nikolasd/nikolad-plugins`. Add it to `nd/` and `ty-lsp/` when real.
7. **A Linux CI workflow was offered but not written.** Now the only known route to
   items 1 and 2. It would also make item 4 routine instead of machine-dependent. `--trust-plugin` exists for unattended runs.
8. **`ty-lsp` was never reviewed** — out of scope. It declares MIT and has a valid
   manifest; nothing further checked.
9. **Minor gap found in `reflecting` but not fixed:** the skill says nothing about what to
   do when `MEMORY.md` is unreadable. An eval transcript showed the agent improvising
   sensibly (asking rather than clobbering the index), so this is a documentation gap, not
   a defect.

## Suggested Skills for Next Session

- `superpowers:verification-before-completion` — the recurring failure mode here was
  citing a score as evidence before checking whether the score meant anything. Two
  retractions this session came from exactly that.
- `superpowers:writing-skills` — if any skill body changes, its "Match the Form to the
  Failure" table is what drove the `writing-plain-language` restructure.
- `nd:reflecting` — to consolidate what the macOS runs establish.
- Not `nd:handoff` again unless the session ends mid-task.
