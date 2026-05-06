# Playable Org

Represent an organization as a navigable graph of cited markdown files, then run analytical playbooks on top of it. Connects to Claude Desktop via the bundled mcp server. Everything local, no cloud, no database.

## What you install

- `Org/` — your structure, as a folder of markdown files. One file per organizational unit, person, role, activity, stakeholder, commitment, financial summary. Each file is short. Each claim cites its source.
- `mcp-server/` — a TypeScript stdio mcp server that exposes 12 tools to Claude Desktop. Read tools (read, search, list, neighbors). Write tools (write_node, save_source, log_append). Meta tools (skills_list, skill_read, lint_run, play_run, open).
- `skills/` — workflow recipes and analytical playbooks, plus the productizable design system. Two operational skills (`ingest`, `lint`), four analytical playbooks (`ai-exposure`, `value-map`, `reshuffle`, `world-model`), one bulk-ingest skill (`seed`), one meta-skill (`new-play`).
- `install.command` / `install.bat` — clickable installers. They build the mcp server and register it in Claude Desktop's config. No admin privileges required.

After install, you chat with Claude in plain language. *Show me the structure of marketing.* *Where is the legacy pipeline going on the evolution curve?* *Run the world-model on the customer-facing division.* The artefacts land on your disk and open in your default browser.

## Why it exists

LLMs change what kind of "data" a system can manage. Before, structured data was needed because the only thing reading it was code. Now an LLM can read prose. That means a knowledge representation can be: a folder of markdown files, with a thin schema in YAML frontmatter, and citations everywhere. Persistence is the filesystem. Schema validation is a lint pass. Query is the agent reading the relevant files. Audit is an append-only log.

This pattern was articulated by Andrej Karpathy in May 2026 as the "LLM Wiki" idea. Playable Org is one application of the pattern: a representation of an organization, with analytical playbooks on top.

## Who it is for

Three readers benefit.

A consultant who works with organizations and wants a substrate to ground analysis in cited facts, instead of slide decks that go stale.

An in-house operations or strategy lead who wants to think about their own organization as a system: where the work happens, where commitments are load-bearing, where AI changes structure rather than speed.

A developer building knowledge tools who wants a reference implementation of the markdown-corpus pattern with mcp integration and analytical layers.

## What's in the box

Twelve mcp tools, accessible from Claude Desktop:

- **Read**: `org_read`, `org_search`, `org_list`, `org_neighbors` — query the graph.
- **Write**: `org_write_node`, `org_save_source`, `org_log_append` — modify the graph (with safeguards).
- **Meta**: `org_skills_list`, `org_skill_read` — discover what skills are available and read their recipes.
- **Executors**: `org_lint_run`, `org_play_run`, `org_open` — run lint, run playbooks, open artefacts in the OS default app.

Seven skills:

- `seed` — one-time bulk ingest of source documents, populating the graph from scratch.
- `ingest` — default after seed: ingest one new source at a time with human confirmation.
- `lint` — quality control on the graph (broken links, missing frontmatter, citations to non-existent sources).
- `ai-exposure` — for each activity, classify AI exposure using the Anthropic Economic Index dataset.
- `value-map` — position the components of a slice on the evolution × visibility plane, with AI overlay.
- `reshuffle` — diagnose which constraints hold a process bundle together; classify AI uses as tool or engine.
- `world-model` — re-read the organization as a platform of capabilities + world model + intelligence layer + interfaces. Surface failure signals as roadmap.
- `new-play` — meta-skill: scaffold a new playbook from a five-question interview.

Each playbook produces a self-contained interactive HTML report. The design system uses Inter Variable, sober typography, hairline rules, monochrome palette with state accents only.

## What it is not

This is not a database replacement for production applications. The pattern works for knowledge that fits in thousands of markdown files (one organization, one knowledge base, one personal data vault), single-user or small-team. It does not replace Postgres for a high-write-rate transactional system.

This is not Notion. There is no rich-text editor. No real-time collaboration. No web app. The graph is a folder. You edit it through the agent, or by opening files in any text editor.

This is not an org chart tool. The structure of `Org/` is richer than a tree of boxes: it has stakeholders, commitments, activities, language terms. The org chart is a thin slice of what's modelled.

## Theoretical lineage

The four playbooks have explicit roots. They are compositions of patterns from other authors, applied through the LLM substrate.

- `ai-exposure` — *Anthropic Economic Index*, March 2026 release. Empirical signal of AI usage in occupational tasks.
- `value-map` — Simon Wardley. Mapping process components on the evolution × visibility plane.
- `reshuffle` — Sangeet Paul Choudary, *Reshuffle* (2024). Tool vs engine, three constraint types, autonomy-coordination tradeoff.
- `world-model` — Jack Dorsey + Roelof Botha, *From Hierarchy to Intelligence* (Block, March 2026). Capability + world model + intelligence layer + interfaces.

The substrate pattern itself is from Andrej Karpathy, *Building an LLM Wiki* (gist, May 2026). The term "structure" for the cited-graph layer is borrowed from Simone Cicero on platform design.

## Quick start

1. Clone or download this repo. Open the folder.
2. Make sure Claude Desktop is installed (https://claude.ai/download) and Node.js is on your PATH.
3. Double-click `install.command` (macOS) or `install.bat` (Windows). The installer builds the mcp server and registers it in Claude Desktop.
4. Restart Claude Desktop.
5. Drop founding documents (charter, organizational charts, role-descriptions, annual report) into `Org/sources/`.
6. In Claude Desktop, in a new chat: *seed the structure from sources/*.
7. After ~30–60 minutes you have a populated graph. From there, ask questions, ingest new documents as they arrive, run playbooks.

Detailed instructions: [`SETUP.md`](SETUP.md). Architecture: [`docs/architecture.md`](docs/architecture.md). Playbook reference: [`docs/playbooks.md`](docs/playbooks.md). Extending: [`docs/extending.md`](docs/extending.md).

## License

MIT. See [`LICENSE`](LICENSE).

The bundled Inter Variable font is licensed under the SIL Open Font License (Rasmus Andersson). The Anthropic Economic Index dataset shipped with `ai-exposure` is licensed under CC BY 4.0 (Anthropic).
