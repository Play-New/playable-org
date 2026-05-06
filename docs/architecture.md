# Architecture

This document explains why Playable Org is built the way it is. Read it after `README.md` if you want the reasoning behind the choices.

## The pattern

A folder of markdown files representing one organization. Each entity is one file. Each claim cites a source. The agent is the maintainer, not the author. The folder structure is the schema.

The pattern was articulated by Andrej Karpathy in May 2026 ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). Three properties make it work in practice:

1. **Files are the storage.** Markdown is human-readable. Diffs are line-level. Everything ports across editors, IDEs, GitHub, Obsidian. The file system is the database.
2. **Citations are mandatory.** Every assertion carries an inline `(source-id)`. The lint refuses citations to non-existent sources. The agent cannot invent without breaking the rule mechanically.
3. **The agent maintains, the human curates.** Writes are proposed, the human confirms. The audit log is prepend-only. There is no "automatic update" path that bypasses confirmation.

## Why files instead of a database

Three practical reasons.

**Readability.** A markdown file opens in any editor. Grep works. Git diff works. The structure can be inspected without launching an application or hitting an API.

**Portability.** No vendor lock-in. No proprietary format. The folder zips, syncs to Dropbox, versions with git. If Playable Org is abandoned tomorrow, the data remains usable.

**Diff visibility.** Modifications to a node are line-level diffs in plain text. Code review works. Conflict resolution works. Audit works.

The trade-off: performance and scale. The pattern works for tens of thousands of files (one organization, one knowledge base). It does not replace Postgres for transactional systems with high write rates. Most internal organizational knowledge lives in the first category but is built as if it lived in the second. That mismatch is the opportunity Playable Org targets.

## Why citations are mandatory

LLMs are excellent at producing plausible content. Without an obligation to cite, the graph fills with confident-sounding facts whose origin cannot be traced. This is not a hypothetical risk — it's the default behaviour of any LLM-mediated knowledge system that doesn't enforce the rule mechanically.

The rule: every node body has at least one inline `(source-id)` reference. The lint script verifies that every cited `source-id` corresponds to a real file in `sources/`. Citations to non-existent sources are rejected outright, no exceptions.

This forces a discipline: when the agent doesn't have a source, it cannot write. When the user wants to add a fact, they must point at a document. When two sources disagree, the discrepancy is documented as a discrepancy, not silently resolved.

## Why `sources/` is immutable

Sources are the ground truth. The structure is paraphrase. If a source changes (a charter is amended, a new annual report comes out), the new version is added as a new file with a new id. The old version stays. The structure citing the old version remains valid for what it represented at the time.

This means:
- Re-compilation is possible. Given `sources/` alone, you could rebuild the rest.
- Citations are stable. A `(charter-2024)` citation always points to the same content.
- History is preserved. The 2025 charter and the 2024 charter coexist; their differences are documented in the structure.

## Why content in the working language and schema in English

The schema (folder names, YAML keys, internal identifiers like `level: division | area | team`) is English. The content (descriptions, narratives, role definitions) is in whatever language the organization actually uses.

Reason: the schema is productizable across organizations and languages. The content is specific to one organization. Keeping them in different languages makes the boundary explicit and prevents the productizable layer from accreting language-specific assumptions.

## Why facts in `org/`, interpretations in `plays/`

The structure of facts is reusable across many analyses. An interpretation is one analyst's reading at one point in time. Mixing them produces a graph that drifts: every interpretation that "becomes true" overwrites the underlying facts, and the structure ceases to be a stable reference.

The discipline: `org/` answers *what is*. `plays/` answers *what does this mean, given that*. A play in `plays/` is frozen at creation date. To revise, write a new play. The old plays are not deleted — they are history.

## Why the log is prepend-only

Each write to `org/` appends one line to `log.md`. The line goes at the top, not the bottom. Most-recent first.

Two reasons:
- **Audit**: when something goes wrong, the recent context is what you need. Reading the top is faster than scrolling.
- **Stability**: appending at the top is mechanically equivalent to appending at the bottom. The log file is still append-only in spirit (no edits, no deletions), the order is reversed for readability.

## The mcp server

The bridge from Claude Desktop to the graph. TypeScript, stdio-based, exposes 12 tools. Read tools (read, search, list, neighbors). Write tools (write_node, save_source, log_append). Meta tools (skills_list, skill_read). Executors (lint_run, play_run, open).

The server is intentionally thin. It does not know about playbooks. It does not know about specific analytical methods. It exposes primitives. The agent (Claude) composes them by following recipes in `skills/`.

This separation has two consequences:
- **Adding a new analytical method = adding a SKILL.md.** No mcp server change required if the method composes existing primitives. (If a new primitive is needed, then the server is updated and a new tool is exposed.)
- **The mcp server is generic.** Other projects could use it as the bridge to their own structure. The server makes no assumption about what the markdown files mean.

## The skills layer

`skills/` contains seven recipes (`init`, `ingest`, `lint`, four playbooks, plus the meta-skill `new-playbook`) and three cross-cutting docs (`CAPABILITIES.md`, `STYLE.md`, `ROADMAP.md`) plus `design.py`.

Each skill is a `SKILL.md` recipe the agent reads via `org_skill_read`. Some skills (the playbooks) ship with Python scripts (build/audit/viewer). The recipe tells the agent how to compose the scripts via `org_play_run`.

The four base playbooks all use `design.py` for visual identity. Adding a new playbook via `new-playbook` inherits the same design system automatically.

## What this is not

- Not a database replacement for production transactional systems.
- Not Notion. No web app, no real-time collaboration.
- Not an org chart tool. The structure of `org/` is richer than a tree of boxes.
- Not a CMS. The agent is the maintainer, not a publishing pipeline.

## See also

- [`README.md`](../README.md) — public-facing pitch.
- [`SETUP.md`](../SETUP.md) — installation guide.
- [`docs/playbooks.md`](playbooks.md) — reference for the four base playbooks.
- [`docs/extending.md`](extending.md) — how to add a new playbook or new mcp tool.
- [`org/AGENTS.md`](../org/AGENTS.md) — operational contract for `org/`.
