# mcp-server

TypeScript stdio MCP server that exposes a Playable Org folder as tools to any MCP-compatible client (Claude Desktop, Claude Code, etc.).

## What it exposes

12 tools across four categories.

**Read**
- `org_read(id)` — read a node's frontmatter + body. Resolves bare ids by globbing `nodes/`, `identity/`, `language/`, `commitments/`, `financials/`, `plays/`, plus root-level Org docs (`log`, `index`, `AGENTS`, `README`, `open-questions`).
- `org_search(query, type?)` — text search across nodes, optional type filter.
- `org_list(type?, path?)` — list nodes by type or path prefix. Returns id, path, type, title.
- `org_neighbors(id, depth?)` — graph neighborhood via frontmatter id arrays (`parent`, `head_role`, `unit`, `performer`, `parties_committing`, `parties_benefiting`, `related`, `sources`, etc.) plus reverse edges.

**Write**
- `org_write_node(path, frontmatter, body, mode?)` — create / update / upsert a node. Refuses writes to `sources/` (immutable) and `identity/` (unless `force_identity=true`). Path-traversal containment via `safeResolve`.
- `org_save_source(filename, content?, content_base64?)` — register a new file in `sources/`. Refuses overwrite. Canonicalizes filename to kebab-case.
- `org_log_append(entry, date?)` — append a line to `log.md` (most recent on top).

**Meta**
- `org_skills_list()` — list skills available alongside `Org/`. Returns name + description for each. Resolves both top-level (`skills/<name>/SKILL.md`) and nested playbooks (`skills/playbooks/<name>/SKILL.md`).
- `org_skill_read(name)` — return the full body of a skill SKILL.md (or one of the cross-cutting docs `CAPABILITIES`, `STYLE`, `ROADMAP`).

**Executors**
- `org_lint_run(tier?)` — spawn `python3 lint.py` and `lint-semantic.py`. Returns parsed counts per check. Detects missing python3 and returns a friendly error.
- `org_play_run(playbook, mode, ...)` — execute a playbook pipeline. `mode=build` runs `build.py`, returns the JSON skeleton. `mode=render` takes a filled JSON in `json_content`, runs `audit.py` and `viewer.py`, returns artefact paths plus audit summary.
- `org_open(path)` — open a file from the bundled repo in the OS default app via `open` (macOS), `xdg-open` (Linux), or `start` (Windows). Path constrained to repo root.

## Install

```bash
cd mcp-server
npm install
npm run build
```

Verify:

```bash
node dist/index.js --data-dir ../Org
```

The process starts and waits on stdio. Kill it with Ctrl+C.

## Configure Claude Desktop manually

Normally the top-level `install.command` / `install.bat` does this for you. Manual edit if you want:

macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "playable-org": {
      "command": "node",
      "args": [
        "/path/to/playable-org/mcp-server/dist/index.js",
        "--data-dir",
        "/path/to/playable-org/Org"
      ]
    }
  }
}
```

Restart Claude Desktop. The 12 tools become available in any new conversation.

## Test

```bash
cd mcp-server
npm run build
cd ..
python3 mcp-server/test-e2e.py
```

84 tests across the 12 tools. Tests use the bundled fixture in `mcp-server/test-fixtures/sample-org/` (a tiny generic Acme example) for read-side assertions, plus tmp directories for write-side and root-level for tooling that resolves via repo root.

## Architecture

```
mcp-server/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts             entry point, stdio transport
│   ├── server.ts            MCP server setup, tool registration
│   ├── tools/               one file per tool
│   │   ├── org-read.ts
│   │   ├── org-search.ts
│   │   ├── org-list.ts
│   │   ├── org-neighbors.ts
│   │   ├── org-write-node.ts
│   │   ├── org-save-source.ts
│   │   ├── org-log-append.ts
│   │   ├── org-skills-list.ts
│   │   ├── org-skill-read.ts
│   │   ├── org-lint-run.ts
│   │   ├── org-play-run.ts
│   │   └── org-open.ts
│   └── lib/
│       ├── safe-path.ts     path-traversal containment
│       └── walk.ts          filesystem walking + frontmatter parsing
├── test-e2e.py              84-test end-to-end suite
├── test-fixtures/sample-org generic Acme fixture
└── dist/                    compiled output (gitignored)
```

## License

MIT. See [`../LICENSE`](../LICENSE).
