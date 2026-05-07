# Playable Org

Represent an organization as a navigable graph of cited markdown files, then run analytical playbooks on top of it. Connects to Claude Desktop via the bundled mcp server. Everything local, no cloud, no database.

## What you install

- `org/` — your structure, as a folder of markdown files. One file per organizational unit, person, role, activity, stakeholder, commitment, financial summary. Each file is short. Each claim cites its source.
- `mcp-server/` — a TypeScript stdio mcp server that exposes 12 tools to Claude Desktop. Read tools (read, search, list, neighbors). Write tools (write_node, save_source, log_append). Meta tools (skills_list, skill_read, lint_run, play_run, open).
- `skills/` — workflow recipes and analytical playbooks, plus the productizable design system. Three operational skills (`init`, `ingest`, `lint`), four analytical playbooks (`ai-exposure`, `value-map`, `reshuffle`, `world-model`), one meta-skill (`new-playbook`).
- `install.command` / `install.bat` — clickable installers. They build the mcp server and register it in Claude Desktop's config. No admin privileges required.

After install, you chat with Claude in plain language. *Show me the structure of marketing.* *Where is the legacy pipeline going on the evolution curve?* *Run the world-model on the customer-facing division.* The artefacts land on your disk and open in your default browser.

## Why "Playable"

Organizations are opaque even to themselves. Who does what, who owes what to whom, where the load-bearing commitments are — most of this lives in people's heads, in role-description PDFs nobody reads twice, in org charts stale within days of a reorg. You can't play a game whose rules and pieces you can't see.

Playable Org is legibility first, then play.

**Legible**: a folder of cited markdown files, maintained by an LLM agent against the documents you already have. The graph re-renders as the documents change. You read it like prose, query it like a database, audit it like a ledger.

**Playable**: each analytical pass over the graph is a *play* — a what-if simulation of the organization under a specific hypothesis, grounded in cited facts. Run it. Freeze the result. Run a different hypothesis. Compare across time as the organization evolves.

You play with the graph the way you play with a board: pieces visible, rules explicit, moves recorded, positions reproducible.

Without legibility, the plays have no ground. Without the plays, the graph is a static reference.

## What's in the box

Twelve mcp tools, accessible from Claude Desktop:

- **Read**: `org_read`, `org_search`, `org_list`, `org_neighbors` — query the graph.
- **Write**: `org_write_node`, `org_save_source`, `org_log_append` — modify the graph (with safeguards).
- **Meta**: `org_skills_list`, `org_skill_read` — discover what skills are available and read their recipes.
- **Executors**: `org_lint_run`, `org_play_run`, `org_open` — run lint, run playbooks, open artefacts in the OS default app.

Seven skills:

- `init` — one-time bulk ingest at first install: populates the graph from a folder of source documents.
- `ingest` — default after init: ingest one new source at a time with human confirmation.
- `lint` — quality control on the graph (broken links, missing frontmatter, citations to non-existent sources).
- `ai-exposure` — for each activity, classify AI exposure using the Anthropic Economic Index dataset.
- `value-map` — position the components of a slice on the evolution × visibility plane, with AI overlay.
- `reshuffle` — diagnose which constraints hold a process bundle together; classify AI uses as tool or engine.
- `world-model` — re-read the organization as a platform of capabilities + world model + intelligence layer + interfaces. Surface failure signals as roadmap.
- `new-playbook` — meta-skill: scaffold a new playbook from a five-question interview.

Each playbook produces a self-contained interactive HTML report. The design system follows Play New: Mirage variable as the single font family, opacity-layered black on white, hairline rules, no chromatic colors. One brand, one accent.

## What it is not

This is not a database replacement for production applications. The pattern works for knowledge that fits in thousands of markdown files (one organization, one knowledge base, one personal data vault), single-user or small-team. It does not replace Postgres for a high-write-rate transactional system.

This is not Notion. There is no rich-text editor. No real-time collaboration. No web app. The graph is a folder. You edit it through the agent, or by opening files in any text editor.

This is not an org chart tool. The structure of `org/` is richer than a tree of boxes: it has stakeholders, commitments, activities, language terms. The org chart is a thin slice of what's modelled.

## Theoretical lineage

The four playbooks have explicit roots. They are compositions of patterns from other authors, applied to the LLM-maintained graph.

- `ai-exposure` — *Anthropic Economic Index*, March 2026 release. Empirical signal of AI usage in occupational tasks.
- `value-map` — Simon Wardley. Mapping process components on the evolution × visibility plane.
- `reshuffle` — Sangeet Paul Choudary, *Reshuffle* (2024). Tool vs engine, three constraint types, autonomy-coordination tradeoff.
- `world-model` — Jack Dorsey + Roelof Botha, *From Hierarchy to Intelligence* (Block, March 2026). Capability + world model + intelligence layer + interfaces.

The pattern itself — an LLM-maintained markdown corpus governed by an `AGENTS.md` contract, with `index.md` as catalog and `log.md` as audit — is from Andrej Karpathy, *Building an LLM Wiki* (gist, May 2026). We keep the pattern; we call our artefact `org/`, not a wiki. The term "structure" for the cited-graph layer is borrowed from Simone Cicero, *[What is an organization today?](https://through-the-boundary.simonecicero.com/p/ttb-1-what-is-an-organization-today)* (Through The Boundary, April 2026), which contrasts the foundational *structure* of an organization (topology, taxonomy, shared context, promise chains) with the *superstructure* — hierarchical management and bureaucracy — that AI eliminates.

## Quick start

1. Clone or download this repo. Open the folder.
2. Make sure Claude Desktop is installed (https://claude.ai/download) and Node.js is on your PATH.
3. Double-click `install.command` (macOS) or `install.bat` (Windows). The installer builds the mcp server and registers it in Claude Desktop.
4. Restart Claude Desktop.
5. Drop founding documents (charter, organizational charts, role-descriptions, annual report) into `org/sources/`.
6. In Claude Desktop, in a new chat: *initialize the structure from sources/*.
7. After ~30–60 minutes you have a populated graph. From there, ask questions, ingest new documents as they arrive, run playbooks.

Detailed instructions: [`SETUP.md`](SETUP.md). Architecture: [`docs/architecture.md`](docs/architecture.md). Playbook reference: [`docs/playbooks.md`](docs/playbooks.md). Extending: [`docs/extending.md`](docs/extending.md).

## License

MIT. See [`LICENSE`](LICENSE).

The bundled Mirage variable font is part of the Play New design system; license terms to be confirmed before public redistribution (forks that cannot include Mirage drop `_assets/fonts/mirage-variable.woff2` and inherit the system-ui fallback). The Anthropic Economic Index dataset shipped with `ai-exposure` is licensed under CC BY 4.0 (Anthropic).
