# Restarting the MCP server (Windows / PowerShell)

A helper to **re-register** the `openproject-fastmcp` server with the Claude CLI in
one step, plus an optional global shortcut you can run from any terminal.

The script does: `claude mcp remove` → `claude mcp add` → `claude mcp list`.
It reads `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` from your `.env` — **no secrets
are hardcoded** in the script.

> Re-registering does not by itself restart the running Python process. The Claude
> client spawns the server on demand. After running the script, **restart your Claude
> client** (VS Code / Desktop) to pick up code or env changes.

---

## Prerequisites

- The [Claude CLI](https://docs.claude.com/claude-code) installed and on `PATH`
  (`claude --version` works).
- Repo set up: `uv sync` done and a `.env` file created (`cp env_example.txt .env`,
  then fill `OPENPROJECT_URL` and `OPENPROJECT_API_KEY`).

The script auto-detects the repo location, so it works regardless of where you cloned it.

---

## Option A — run the script directly

From the repo root:

```powershell
pwsh scripts/restart_mcp.ps1
```

Only Windows PowerShell 5.1 installed (no `pwsh`)? Use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/restart_mcp.ps1
```

Expected tail:

```
openproject-fastmcp: ...python.exe ...openproject-mcp-fastmcp.py - √ Connected
```

---

## Option B — global shortcut `opmcp`

Add a function to your PowerShell profile so you can type `opmcp` from anywhere.

**1. Find your profile path** (run in the PowerShell version you actually use):

```powershell
$PROFILE
```

- PowerShell 7 (`pwsh`): `...\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
- Windows PowerShell 5.1: `...\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

**2. Append the function**, pointing at *your* clone path:

```powershell
# create the profile if missing, then add the function
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
Add-Content -Path $PROFILE -Encoding UTF8 -Value @'

# --- OpenProject MCP restart ---
function opmcp { & "C:\path\to\your\clone\scripts\restart_mcp.ps1" }
'@
```

Replace `C:\path\to\your\clone` with your actual repo path.

**3. Reload and use:**

```powershell
. $PROFILE   # or just open a new terminal
opmcp
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `opmcp` / script blocked, "running scripts is disabled" | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `claude: command not found` | Install the Claude CLI and ensure it's on `PATH`. |
| `python not found in .venv` | Run `uv sync` in the repo root first. |
| `.env not found` | `cp env_example.txt .env` and fill in your values. |
| `OPENPROJECT_URL missing` | Check `.env` has `OPENPROJECT_URL=` and `OPENPROJECT_API_KEY=` set. |
| Server shows `Needs authentication` / not `Connected` | Verify the API key in `.env` is valid, then re-run. |

---

## What the script registers

Equivalent to running manually:

```powershell
claude mcp remove openproject-fastmcp --scope user
claude mcp add openproject-fastmcp --scope user `
    "<repo>\.venv\Scripts\python.exe" `
    "<repo>\openproject-mcp-fastmcp.py" `
    -e "PYTHONPATH=<repo>" `
    -e "OPENPROJECT_URL=<from .env>" `
    -e "OPENPROJECT_API_KEY=<from .env>"
```
