# restart_mcp.ps1
# Remove + re-add the openproject-fastmcp MCP server in one shot.
# Reads OPENPROJECT_URL / OPENPROJECT_API_KEY from the project .env (no secrets hardcoded).
# Usage:  pwsh scripts/restart_mcp.ps1   (or right-click -> Run with PowerShell)

$ErrorActionPreference = "Stop"

$Name        = "openproject-fastmcp"
$ProjectRoot = Split-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) -Parent
$VenvPython  = "$ProjectRoot\.venv\Scripts\python.exe"
$Entry       = "$ProjectRoot\openproject-mcp-fastmcp.py"
$EnvFile     = "$ProjectRoot\.env"

# --- sanity ---
if (-not (Test-Path $VenvPython)) { Write-Error "python not found in .venv: $VenvPython. Run 'uv sync' first." }
if (-not (Test-Path $Entry))      { Write-Error "entry script not found: $Entry" }
if (-not (Test-Path $EnvFile))    { Write-Error ".env not found: $EnvFile" }

# --- parse .env (KEY=VALUE, skip comments/blanks) ---
$cfg = @{}
foreach ($line in Get-Content $EnvFile) {
    $t = $line.Trim()
    if ($t -eq "" -or $t.StartsWith("#")) { continue }
    $i = $t.IndexOf("=")
    if ($i -lt 1) { continue }
    $cfg[$t.Substring(0, $i).Trim()] = $t.Substring($i + 1).Trim()
}

$Url = $cfg["OPENPROJECT_URL"]
$Key = $cfg["OPENPROJECT_API_KEY"]
if ([string]::IsNullOrWhiteSpace($Url)) { Write-Error "OPENPROJECT_URL missing in .env" }
if ([string]::IsNullOrWhiteSpace($Key)) { Write-Error "OPENPROJECT_API_KEY missing in .env" }

# --- kill (ignore if not registered) ---
Write-Host ">>> removing $Name ..." -ForegroundColor Cyan
try { claude mcp remove $Name --scope user } catch { Write-Host "   (not registered, skipping)" -ForegroundColor DarkGray }

# --- re-add ---
Write-Host ">>> adding $Name ..." -ForegroundColor Cyan
claude mcp add $Name --scope user $VenvPython $Entry `
    -e "PYTHONPATH=$ProjectRoot" `
    -e "OPENPROJECT_URL=$Url" `
    -e "OPENPROJECT_API_KEY=$Key"

Write-Host "`n>>> current MCP list:" -ForegroundColor Cyan
claude mcp list

Write-Host "`nDone. Restart the Claude client to pick up the reloaded server." -ForegroundColor Green
