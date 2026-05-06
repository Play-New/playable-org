#!/usr/bin/env bash
#
# Installer for Claude Desktop (macOS).
#
# Run once after cloning the repo:
#   cd <repo> && ./install.sh
#
# What it does:
#   1. Verifies Node.js (≥18). If missing, prints how to install it.
#   2. npm install + npm run build inside mcp-server/.
#   3. Adds the "playable-org" entry to the Claude Desktop config (with backup).
#   4. Prints verification instructions.
#
# No admin privileges required.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
ORG_DIR="$REPO_ROOT/Org"
MCP_DIR="$REPO_ROOT/mcp-server"
CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "\033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "\033[33m!\033[0m %s\n" "$1"; }
fail() { printf "\033[31m✗\033[0m %s\n" "$1"; exit 1; }

bold "Playable Org installer"
echo "Repo root: $REPO_ROOT"
echo

# ----------------------------------------------------------------------------
# 1. Verify Node.js
# ----------------------------------------------------------------------------

if ! command -v node >/dev/null 2>&1; then
  cat <<EOF
✗ Node.js not installed.

To install:
  - Download the installer from https://nodejs.org (LTS version, "Recommended")
  - Open the .pkg, follow the installer
  - Reopen Terminal and re-run this script

EOF
  exit 1
fi

NODE_VERSION="$(node --version | sed 's/^v//' | cut -d. -f1)"
if [[ "$NODE_VERSION" -lt 18 ]]; then
  fail "Node.js v18+ required. Found v$(node --version). Update from nodejs.org."
fi

NODE_BIN="$(command -v node)"
ok "Node.js v$(node --version | sed 's/v//') found at $NODE_BIN"

# ----------------------------------------------------------------------------
# 2. Build mcp-server
# ----------------------------------------------------------------------------

if [[ ! -d "$MCP_DIR" ]]; then
  fail "mcp-server/ folder not found at $REPO_ROOT. Incomplete repo?"
fi

cd "$MCP_DIR"
if [[ ! -d node_modules ]]; then
  echo "Installing npm dependencies..."
  npm install --silent 2>&1 | tail -5
fi
ok "npm dependencies ready"

echo "Building TypeScript..."
npm run build --silent
[[ -f "$MCP_DIR/dist/index.js" ]] || fail "Build failed (dist/index.js missing)."
ok "Build OK ($MCP_DIR/dist/)"

cd "$REPO_ROOT"

# ----------------------------------------------------------------------------
# 3. Verify Org/
# ----------------------------------------------------------------------------

if [[ ! -d "$ORG_DIR" ]]; then
  fail "Org/ folder not found at $REPO_ROOT. Incomplete repo?"
fi
ok "Org/ present"

# ----------------------------------------------------------------------------
# 4. Configure Claude Desktop
# ----------------------------------------------------------------------------

mkdir -p "$CONFIG_DIR"

if [[ -f "$CONFIG_FILE" ]]; then
  TS="$(date +%Y-%m-%d-%H%M%S)"
  cp "$CONFIG_FILE" "$CONFIG_FILE.bak-$TS"
  ok "Existing config backed up → $(basename "$CONFIG_FILE.bak-$TS")"
fi

# Use Python for safe JSON merge (preserves other already-configured servers)
python3 <<PYEOF
import json
from pathlib import Path

cfg = Path("$CONFIG_FILE")
data = {}
if cfg.exists():
    try:
        data = json.loads(cfg.read_text())
    except json.JSONDecodeError:
        data = {}

data.setdefault("mcpServers", {})["playable-org"] = {
    "command": "$NODE_BIN",
    "args": [
        "$MCP_DIR/dist/index.js",
        "--data-dir",
        "$ORG_DIR"
    ]
}

cfg.write_text(json.dumps(data, indent=2))
print("Updated", cfg)
PYEOF

ok "Entry 'playable-org' added to $CONFIG_FILE"

# ----------------------------------------------------------------------------
# 5. Smoke-test
# ----------------------------------------------------------------------------

echo
echo "Smoke-testing the server (1 second)..."
RESULT="$(echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | "$NODE_BIN" "$MCP_DIR/dist/index.js" --data-dir "$ORG_DIR" 2>/dev/null \
  | python3 -c 'import json,sys; r=json.loads(sys.stdin.read()); print(len(r["result"]["tools"]))' || echo 0)"

if [[ "$RESULT" -ge 8 ]]; then
  ok "Smoke-test OK ($RESULT tools registered)"
else
  warn "Smoke-test inconclusive. Server started but response unexpected."
fi

# ----------------------------------------------------------------------------
# 6. Done
# ----------------------------------------------------------------------------

echo
bold "Installation complete."
cat <<'EOF'

Next steps:
  1. Quit Claude Desktop completely (Cmd+Q).
  2. Reopen Claude Desktop.
  3. In a new chat, ask:
       "What tools do you have available?"
     Expected: a list of 8 tools starting with "org_".

  4. Try:
       "Show me the organization chart."
     Expected: the agent reads from the bundled Org/ via mcp.

If something doesn't work, see SETUP.md (or ask the maintainer).
EOF
