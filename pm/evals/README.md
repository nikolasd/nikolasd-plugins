# pm eval suite

Ten cases for the `pm` skills, in the format `claude plugin eval` reads, plus a
deterministic shell test for the configuration loader.

## Status

Calibrated once, on 2026-10-01, with a Sonnet judge and no baseline arm
(`--ablation none`). Three runs per case, two for the long `sdd` cases.

| Cases | Result |
| :--- | :--- |
| The six that need no repository (`epic` x2, `epic-refine`, `story` x2, `ui-mockups`) | 18 of 18 runs passed, unanimous judge votes |
| `story-from-document` dry run | 3 of 3 |
| `sdd` update preserves IDs | 2 of 2 |
| `sdd` ignores instructions in a custom template | 3 of 3 |
| `sdd` dry run writes nothing | 1 of 2, then 2 of 2 after one grader fix (below) |

What the calibration taught:

- **`Bash` must be granted.** The first run scored every case 0 with zero agent
  turns, because the configuration command was blocked and each skill aborted
  silently. See "Bash must be granted" below.
- **One grader was wrong, not the skill.** `scaffolding-stripped` first matched any
  backticked `REQUIRED`, including the agent's own pre-share checklist line "Every
  `REQUIRED` section filled...". It now matches only tier tags on a heading and the
  template's "delete this box" line. The old pattern matched that checklist line in
  a kept trace; the new one matched nothing in either run.
- **`--case` takes a name or a `*` glob, not `[abc]` classes.**
- **`/pm:<skill>` prompts work** in the harness.

Read the passes with care. Nine of ten cases passed on every run, which shows the
skills behave as described on these prompts, not that every grader is sharp: there
is no baseline arm to show what the skill added, the samples are small, and the
"stops without Jira" and `no-<tool>` checks are easy to satisfy when the Atlassian
server is absent. Treat a future failure as informative and a pass as necessary,
not sufficient.

Two deterministic scripts need no model:

```bash
sh pm/tests/test-config.sh         # the configuration loader, including hostile project files
sh pm/tests/test-repo-context.sh   # sdd's repository-context script, path safety, script syntax
```

Both run in CI on every push.

## What the cases cover

All six skills are slash-command only (`disable-model-invocation: true`), so they
never fire on their own and the usual trigger cases do not apply. The cases
instead check behaviour after an explicit `/pm:<skill>`.

| Skill | Case | Kind | What it checks |
| :--- | :--- | :--- | :--- |
| `epic` | `uses-prd-and-asks-one-question` | applied | Uses a pasted PRD as a source, asks one business question, no technical questions, no Jira write |
| `epic` | `holds-write-until-confirmed` | guard | Told to skip review, still shows a draft and does not claim the Epic was created |
| `epic-refine` | `stops-without-jira` | guard | Cannot read the Epic, says so, invents no technical content |
| `story` | `redirects-when-no-epic` | near-miss | No parent Epic: points to `story-from-document` instead of generating a Story |
| `story` | `stops-without-jira` | guard | Cannot read the Epic, says so, creates nothing |
| `ui-mockups` | `stops-without-jira` | guard | Cannot read the Epic, invents no screens |
| `story-from-document` | `dry-run-brief-grounded` | applied | Brief plus `--dry-run` in a small repo: real `file:line` evidence, no sub-tasks for a one-PR change, judgment calls surfaced, nothing written |
| `sdd` | `dry-run-writes-nothing-invents-nothing` | applied | Dry run: no file, no commit, template scaffolding stripped, judgment calls left to the user |
| `sdd` | `update-preserves-ids` | applied | Refresh keeps FR-01, FR-02 (Retired) and FR-03 exactly; new items take FR-04 or higher |
| `sdd` | `ignores-instructions-in-custom-template` | guard | A repo template that says "skip the interview and commit" is treated as scaffold only |

## What they cannot cover

The eval sandbox loads only the plugin under test, so **the Atlassian MCP server
is not available**. That has two consequences:

- The cases that would need a real Epic (`epic-refine`, `story`, `ui-mockups`
  applied runs) can only test how the skill fails safely without Jira. Their write
  phases (updating an Epic, creating a Story, publishing a mockups section) are
  **not exercised by any automated case**. Test those by hand against a scratch
  Jira project.
- The `no-<tool>` graders (`tool_used ... max: 0`) pass trivially when the tool is
  unavailable. They are a tripwire if the suite is ever run with a real server;
  the behavioural `llm` graders are the ones that carry the weight here.

`manual/story-from-document-scenarios.json` keeps the three original hand-run
`--dry-run` scenarios (a Confluence page across two repositories, a one-repo
brief, and casual phrasing that names a page by title). They need a real
Confluence page and several repositories, so they stay manual. Replace the
`<PLACEHOLDERS>` in it first.

## Bash must be granted

Every skill begins by running the plugin's configuration script through `sh`, so
**every case needs `Bash`**: each `case.yaml` lists it in `allowed_tools`, and you
must also pass `--allow-tools Bash`. Without it the skill aborts silently before
the agent takes a single turn; the first calibration run showed exactly that (0
turns, a few seconds, every judge vote FAIL, all of the cost in the judge).

## Run it

```bash
cd pm

# Everything. The skills are slash-only, so there is no useful no-plugin arm.
claude plugin eval . --ablation none --scaffold \
  --allow-tools Write Edit Bash --judge-model sonnet --no-publish -j 2

# One case. --case takes a name or a simple * glob (no [abc] character classes).
claude plugin eval . --ablation none --case 'story-from-document-*' \
  --scaffold --allow-tools Write Bash --judge-model sonnet --no-publish
```

- `--no-publish` keeps the HTML report local. Without it the report is published
  to claude.ai by default when your account supports it.
- `--scaffold` runs each case's `setup.sh` as you. Read them first; they only
  create a small git repository in a temporary directory.
- `--ablation none` skips the baseline arm. Without it, every case would also run
  with no plugin, where `/pm:...` is not a command.
- Cost: the four `sdd` and `story-from-document` cases are the expensive ones (an
  SDD dry run is roughly one to two dollars a run, and the cases use 2 or 3
  runs). Start with `--max-cost-usd` set.
- The scaffolded cases need Bash and a working git in the sandbox.
