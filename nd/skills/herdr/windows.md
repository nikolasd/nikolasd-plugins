# Herdr on Windows

Read this when you run herdr from Git Bash or PowerShell on Windows.

## Slash commands from Git Bash

If a prompt's text starts with `/` (a slash command like `/model opus`, `/clear`, `/help`), Git Bash silently rewrites the leading `/` into a real filesystem path before `herdr.exe` sees it (for example `/model opus` becomes `C:/Users/.../git/2.55.0.5/model opus`, sent to the agent as garbage, with no error anywhere). Two fixes:

```bash
# Bash: the prefix suppresses the path rewrite
MSYS_NO_PATHCONV=1 herdr agent prompt <name> "/model opus" --wait --timeout 30000
```

```powershell
# PowerShell: no rewrite happens here, so no prefix is needed
herdr agent prompt <name> "/model opus" --wait --timeout 30000
```

Use the prefix on every slash-command prompt from Git Bash, including the `/model` and `/nd:<name>` prompts in the "Spawn a Claude peer" recipe.

## Environment variables in PowerShell

Read the exported context as `$env:HERDR_PANE_ID`, `$env:HERDR_TAB_ID` and `$env:HERDR_WORKSPACE_ID`, not `$HERDR_WORKSPACE_ID`. `"$PWD"` needs no change; it resolves in both shells.
