# Installer for Claude Desktop (Windows).
#
# Run once after extracting / cloning the repo. Either:
#   - Double-click install.bat (recommended for non-developers)
#   - Or run from PowerShell:  .\install.ps1
#
# What it does:
#   1. Verifies Node.js (>=18). If missing, prints how to install it.
#   2. npm install + npm run build inside mcp-server\.
#   3. Adds the "playable-org" entry to the Claude Desktop config (with backup).
#   4. Prints verification instructions.
#
# No admin privileges required.

$ErrorActionPreference = "Stop"

function Write-Ok    { param($msg); Write-Host "OK   " -ForegroundColor Green -NoNewline; Write-Host $msg }
function Write-Warn  { param($msg); Write-Host "WARN " -ForegroundColor Yellow -NoNewline; Write-Host $msg }
function Write-Fail  { param($msg); Write-Host "FAIL " -ForegroundColor Red -NoNewline; Write-Host $msg; exit 1 }
function Write-Bold  { param($msg); Write-Host $msg -ForegroundColor White }

$RepoRoot   = $PSScriptRoot
$OrgDir     = Join-Path $RepoRoot "org"
$McpDir     = Join-Path $RepoRoot "mcp-server"
$ConfigDir  = Join-Path $env:APPDATA "Claude"
$ConfigFile = Join-Path $ConfigDir "claude_desktop_config.json"

Write-Bold "Playable Org installer"
Write-Host "Repo root: $RepoRoot"
Write-Host ""

# 1. Verify Node.js -----------------------------------------------------------

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host @"
Node.js not installed.

To install:
  1. Open https://nodejs.org/it (or https://nodejs.org/en)
  2. Download the LTS version ('Recommended for most users')
  3. Run the .msi installer, accept the defaults
  4. Close this window, reopen install.bat

"@ -ForegroundColor Red
    exit 1
}

$nodeVersion = (& node --version) -replace '^v',''
$nodeMajor   = [int]($nodeVersion.Split('.')[0])
if ($nodeMajor -lt 18) {
    Write-Fail "Node.js v18+ required. Found v$nodeVersion. Update from nodejs.org."
}
$nodeBin = $nodeCmd.Source
Write-Ok "Node.js v$nodeVersion found at $nodeBin"

# 2. Build mcp-server ---------------------------------------------------------

if (-not (Test-Path $McpDir)) {
    Write-Fail "mcp-server\ folder not found at $RepoRoot. Incomplete repo?"
}

Push-Location $McpDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing npm dependencies..."
        npm install --silent 2>&1 | Select-Object -Last 5
    }
    Write-Ok "npm dependencies ready"

    Write-Host "Building TypeScript..."
    npm run build --silent | Out-Null
    if (-not (Test-Path (Join-Path $McpDir "dist\index.js"))) {
        Write-Fail "Build failed (dist\index.js missing)."
    }
    Write-Ok "Build OK ($McpDir\dist\)"
}
finally {
    Pop-Location
}

# 3. Verify org/ --------------------------------------------------------------

if (-not (Test-Path $OrgDir)) {
    Write-Fail "org\ folder not found at $RepoRoot. Incomplete repo?"
}
Write-Ok "org\ present"

# 4. Configure Claude Desktop -------------------------------------------------

if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir | Out-Null
}

if (Test-Path $ConfigFile) {
    $ts = Get-Date -Format "yyyy-MM-dd-HHmmss"
    $backup = "$ConfigFile.bak-$ts"
    Copy-Item $ConfigFile $backup
    Write-Ok "Existing config backed up -> $(Split-Path $backup -Leaf)"
}

# JSON merge: preserve already-configured mcpServers, add 'playable-org'.
$config = @{}
if (Test-Path $ConfigFile) {
    try {
        $config = Get-Content $ConfigFile -Raw | ConvertFrom-Json -ErrorAction Stop -AsHashtable
    }
    catch {
        $config = @{}
    }
    if (-not ($config -is [hashtable])) {
        $config = @{}
    }
}

if (-not $config.ContainsKey("mcpServers")) {
    $config["mcpServers"] = @{}
}

$config["mcpServers"]["playable-org"] = @{
    command = $nodeBin
    args    = @(
        (Join-Path $McpDir "dist\index.js"),
        "--data-dir",
        $OrgDir
    )
}

$config | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigFile -Encoding UTF8
Write-Ok "Entry 'playable-org' added to $ConfigFile"

# 5. Smoke-test ---------------------------------------------------------------

Write-Host ""
Write-Host "Smoke-testing the server (1 second)..."

$indexPath = Join-Path $McpDir "dist\index.js"
$request = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
try {
    $response = $request | & node $indexPath --data-dir $OrgDir 2>$null
    $parsed   = $response | ConvertFrom-Json
    $toolCount = ($parsed.result.tools | Measure-Object).Count
    if ($toolCount -ge 8) {
        Write-Ok "Smoke-test OK ($toolCount tools registered)"
    }
    else {
        Write-Warn "Smoke-test inconclusive. Server started but response unexpected."
    }
}
catch {
    Write-Warn "Smoke-test could not parse server response. Continuing — verify in Claude Desktop."
}

# 6. Done ---------------------------------------------------------------------

Write-Host ""
Write-Bold "Installation complete."
Write-Host @"

Next steps:
  1. Quit Claude Desktop completely (Alt+F4 or right-click tray icon -> Quit).
  2. Reopen Claude Desktop.
  3. In a new chat, ask:
       "What tools do you have available?"
     Expected: a list of 8 tools starting with "org_".

  4. Try:
       "Show me the organization chart."
     Expected: the agent reads from the bundled org\ via mcp.

If something doesn't work, see SETUP.md (or ask the maintainer).
"@
