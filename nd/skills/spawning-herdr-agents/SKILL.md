---
name: herdr
description: Use when asked to spawn, run, or control another coding-agent session via Herdr — panes, tabs, and agent sessions.
when_to_use: |
  Trigger phrases: "spawn an agent", "open a new pane", "start Claude in another tab", "send that agent a prompt", "what is the other agent doing", "close that pane", any mention of `herdr`.

  Requires being inside a Herdr-managed pane (`HERDR_ENV=1`). For anything beyond spawning and driving a single agent — multi-machine control, worktrees, workspace management, layout inspection — run `herdr --skill` for the full reference instead.
---

# Spawning and Controlling Herdr Agents

## Prerequisite

Confirm you're inside a Herdr-managed pane before doing anything. If false, say so and stop.

- Bash: `test "${HERDR_ENV:-}" = 1`
- PowerShell: `$env:HERDR_ENV -eq '1'`

## Spawn the agent

1. Your context is already exported: `HERDR_PANE_ID`, `HERDR_TAB_ID`, `HERDR_WORKSPACE_ID`. Commands below are written for Bash — in PowerShell, read these as `$env:HERDR_WORKSPACE_ID` rather than `$HERDR_WORKSPACE_ID`. (`"$PWD"` needs no change; it resolves in both shells.)
2. Pick pane vs tab, defaulting to a sibling pane in the current tab unless the user asks for a new tab or a different directory:
   - **New pane, same tab**: `herdr pane split --current --direction right|down --cwd "$PWD" --no-focus`. Split a wide pane right, a narrow/tall pane down. Read `.result.pane.pane_id`.
   - **New tab**: `herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$PWD"`. Read `.result.root_pane.pane_id`.
3. Start the agent: `herdr agent start <name> --kind claude --pane <pane_id>`. `<name>` must match `[a-z][a-z0-9_-]{0,31}` (lowercase, starts with a letter) — lowercase whatever name the user gives you. Returns once idle/ready (30s default timeout).

## Send it work

- `herdr agent prompt <name> "text" --wait --timeout 120000` — `--wait` blocks until the agent settles to idle/done/blocked.
- **Windows gotcha:** if the text starts with `/` (a slash command like `/model opus`, `/clear`, `/help`), Git Bash silently rewrites the leading `/` into a real filesystem path before `herdr.exe` sees it (e.g. `/model opus` → `C:/Users/.../git/2.55.0.5/model opus`, sent to the agent as garbage — no error anywhere). Two fixes:
  ```bash
  # Bash — the prefix suppresses the path rewrite
  MSYS_NO_PATHCONV=1 herdr agent prompt <name> "/model opus" --wait --timeout 30000
  ```
  ```powershell
  # PowerShell — no rewrite happens here, so no prefix is needed
  herdr agent prompt <name> "/model opus" --wait --timeout 30000
  ```
- Never trust `agent_prompted` or a changed `terminal_title` alone as proof the command was understood — both only confirm text was written. Always follow with a read and check the *echoed input line*, not just the reply.

## Handle confirmation dialogs

Some commands (e.g. Claude's `/model`) open a blocked prompt ("Switch model? 1. Yes / 2. No") instead of applying immediately. `--wait` returns as soon as that dialog appears — that isn't completion. Inspect, then answer:

```bash
herdr agent read <name> --source recent-unwrapped --lines 20   # see the dialog
herdr agent send-keys <name> enter                              # accept the default option
herdr agent read <name> --source recent-unwrapped --lines 20   # verify the real result
```

Sending another prompt while blocked fails with `agent_blocked` — resolve it first. Don't answer a blocked approval/question without checking with the user, unless it's a routine dialog you triggered yourself.

## Read its output

```bash
herdr agent read <name> --source recent-unwrapped --lines 40
```

`recent-unwrapped` for transcripts/logs, `visible` for the current viewport, `detection` for the plain-text snapshot used for agent detection.

## Close it down

- Pane only (agent dies with it): `herdr pane close <pane_id>`
- Whole tab: `herdr tab close <tab_id>`

Only close panes/tabs/sessions you created, unless the user explicitly asks otherwise.

## Quick reference

| Task | Command |
|---|---|
| Split pane | `herdr pane split --current --direction right\|down --cwd "$PWD" --no-focus` |
| New tab | `herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$PWD"` |
| Start agent | `herdr agent start <name> --kind claude --pane <pane_id>` |
| Prompt (plain) | `herdr agent prompt <name> "text" --wait --timeout 120000` |
| Prompt (slash cmd, Bash on Windows) | `MSYS_NO_PATHCONV=1 herdr agent prompt <name> "/cmd" --wait` |
| Prompt (slash cmd, PowerShell) | `herdr agent prompt <name> "/cmd" --wait` |
| Confirm dialog | `herdr agent send-keys <name> enter` |
| Read transcript | `herdr agent read <name> --source recent-unwrapped --lines 40` |
| Close pane / tab | `herdr pane close <pane_id>` / `herdr tab close <tab_id>` |

## Common mistakes

| Mistake | Fix |
|---|---|
| Running herdr commands without checking `HERDR_ENV=1` | Check first; stop if not inside Herdr |
| Sending `/anything` via Bash on Windows without `MSYS_NO_PATHCONV=1` | Always set it for leading-`/` payloads, or use PowerShell (no prefix needed there) |
| Using `$HERDR_WORKSPACE_ID` in PowerShell | Environment variables need the `$env:` prefix there |
| Treating `agent_prompted` or a title change as proof it worked | Read the transcript; check the echoed line and the real resulting state |
| Assuming a slash command applied instantly | Check for a blocked confirmation dialog, answer with `send-keys` |
| Invalid agent name (uppercase, starts with a digit) | Must match `[a-z][a-z0-9_-]{0,31}` |
| Closing panes/tabs you didn't create | Only close your own, unless asked |

For anything beyond this task (multi-machine control, worktrees, workspace management, key vocabulary, layout inspection), run `herdr --skill` for the full reference.
