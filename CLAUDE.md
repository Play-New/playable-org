# Playable Org

Public template for representing an organization as a structured, agent-maintained graph. Markdown files with YAML frontmatter, plus analytical playbooks on top. The bundled mcp server connects the graph to Claude Desktop.

This `CLAUDE.md` is working memory for whoever maintains the template (me, future contributors). It is not shipped to end users — the customer-facing docs are `README.md`, `SETUP.md`, `CONTRIBUTING.md`, `docs/`.

## Where things live

- `org/` — the organization instance bundle. Empty in the public template (3 identity stubs only). Forks populate it.
- `org/AGENTS.md` — operational contract for `org/`. **Read this before any write to `org/`.**
- `org/README.md` — entry point for whoever opens `org/`.
- `org/log.md` — prepend-only audit. Most-recent on top.
- `org/index.md` — content-oriented catalog (link + one-line summary). Updated by the agent on every ingest.
- `mcp-server/` — TypeScript stdio mcp server. 12 tools (4 read + 3 write + 1 meta + 4 executors), full e2e test suite at `mcp-server/test-e2e.py` against fixture in `mcp-server/test-fixtures/sample-org/`.
- `skills/` — agent workflows + analytical playbooks + design system. Three operational skills (`init`, `ingest`, `lint`), four analytical playbooks (`ai-exposure`, `value-map`, `reshuffle`, `world-model`), one meta-skill (`new-play`). Cross-cutting docs: `CAPABILITIES.md` (the four-property frame), `STYLE.md` (anti-rhetoric charter), `ROADMAP.md` (the playbook order), `design.py` (single source of truth for the visual language), `_assets/fonts/inter-variable.woff2` (embedded font).
- `docs/` — public-facing architecture, playbooks reference, extension guide.
- `CLAUDE.md` (this file) — working memory. Not exposed to customers.

## Locked vocabulary

- **Node** — an entity (unit, person, role, activity, stakeholder, financial-summary), under `org/nodes/` or `org/financials/`.
- **Commitment** — relation between nodes. 5 levels × 3 state dimensions.
- **Source** — immutable raw document, under `sources/`.
- **Playbook** — analytical procedure (template, named, reusable). In `skills/playbooks/`.
- **Play** — point-in-time execution of a playbook on a slice of `org/`. In `org/plays/`. Frozen at creation.
- **Structure** — the cited-graph layer in `org/`, distinct from interpretations in `plays/`. Term from Simone Cicero, *[What is an organization today?](https://through-the-boundary.simonecicero.com/p/ttb-1-what-is-an-organization-today)* (Through The Boundary, April 2026): the *structure* (topology, taxonomy, shared context, promise chains) is what AI makes more necessary; the *superstructure* (hierarchies, bureaucracy) is what AI eliminates.

Forbidden words in any context: *wiki*, *lens / lente / lenti*, *diagnosis / diagnosi*, *frame*, *view*, *lettura*, *datato/datata/datati/datate*, *substrate / substrato* (renamed to *structure* throughout — including the JSON schema keys, formerly `_substrate_id` / `_substrate_evidence` / `_substrate`, now `_structure_id` / `_structure_evidence` / `_structure`). Author names of analytical-framework authors (Wardley, Sangeet, Cicero, Burgess, Dorsey, Botha, Karpathy, ...) never appear in any content under `org/`. They may appear in `skills/` documentation, in `docs/`, in `README.md`, in `CONTRIBUTING.md`, in `CLAUDE.md`.

When prose is in a language other than English, prefer the local equivalent over an English loan where natural (parafrasare not paraphrase, alla lettera not verbatim, verifica di pertinenza not scope check). Technical / code terms can stay English (markdown, YAML, frontmatter, kebab-case, mcp, tool, log).

## Locked decisions

- **Structure vs interpretation.** `org/` contains only observable, cited facts. Interpretations live in `plays/`, frozen at creation.
- **Capability is not structure.** It's an interpretive grouping of activities. Structure has `nodes/activities/`; capability decompositions are plays of kind `world-model` or `value-map`.
- **As-is only.** No `state: proposed` on structure nodes. To-be lives in plays.
- **English schema, content in the org's working language.** Folder names and YAML keys in English (productizable). Free-text values in whatever language the organization actually uses.
- **Cross-references**: standard markdown links `[text](../path/to/node.md)` in body for nodes; frontmatter id arrays for structured relations; `(source-id)` for source citations. No wikilinks.
- **No inbox.** Sources arrive via chat upload (one at a time after init) or via Finder drop into `org/sources/` (bulk during init).
- **Tools vs workflows.** Tools = mcp primitives (server). Workflows = recipes that compose tools, defined in `skills/<name>/SKILL.md`. `org/AGENTS.md` describes workflow shape; details live in skills.
- **No length budgets** on nodes. Anti-bloat is qualitative ("cut what you can"), not numeric.
- **Anti-hallucination discipline**: every play must pass `audit.py` (deterministic numerical + citation gate) before commit. Computed content is generated by scripts; agent narrative is clearly demarcated as interpretation.
- **Log convention**: prepend-only (most recent on top). Equivalent stability guarantee to append-only, better readability.
- **Single design system in `skills/design.py`.** All viewers compose primitives from there. No bespoke `<style>` blocks beyond a slim playbook-specific extension that uses design tokens.
- **Inter Variable as single font family** (Rasmus Andersson, SIL OFL). `opsz` axis used for automatic display vs text optical sizing.

## Public template state

- 12 mcp tools.
- 3 operational skills: `init`, `ingest`, `lint`.
- 4 analytical playbooks: `ai-exposure`, `value-map`, `reshuffle`, `world-model`. All four use `design.py` primitives via inheritance through their viewer.py modules. Each ships with build.py + audit.py + viewer.py.
- 1 meta-skill: `new-play`. Five-question interview that scaffolds a new playbook.
- `org/` empty: 3 identity stubs (`# REPLACE ME`), zero other content. Lint Tier 1 reports 3 expected warnings on the stubs (empty `sources` arrays); these go to 0 after init.
- mcp-server e2e: 84/84 PASS against `mcp-server/test-fixtures/sample-org/` (a tiny generic Acme fixture: 1 mission, 2 units, 1 person, 1 stakeholder, 1 commitment, 1 source).
- TypeScript build: clean.

## Maintenance

When adding a new mcp tool:
1. Create `mcp-server/src/tools/<name>.ts`.
2. Register in `mcp-server/src/server.ts`.
3. Add a test in `mcp-server/test-e2e.py`.
4. Document in `docs/architecture.md` if the addition changes the surface area.

When adding a new playbook:
1. Create `skills/playbooks/<name>/{SKILL.md, build.py, audit.py, viewer.py}`.
2. Use `design.py` primitives in viewer.py — no bespoke `<style>` blocks.
3. Declare theoretical lineage explicitly in SKILL.md frontmatter and body.
4. Add an entry to `skills/ROADMAP.md`.
5. Document in `docs/playbooks.md`.

When changing the design system:
1. Update `skills/design.py` only. Never edit the CSS in viewer.py files.
2. If the change requires migration of existing viewers (renamed token, removed primitive), update all four base viewer.py files in the same commit.
3. Bump the visual-version comment at the top of `design.py` so downstream viewers can detect.

When the public template gets new features that downstream forks should pull in:
1. Commit on `main` of `playable-org`.
2. Forks (instance repos) merge `upstream/main`. The public template never modifies `org/` content beyond the 3 identity stubs, so merge conflicts are minimal.

## Lineage

Direct: Andrej Karpathy's *Building an LLM Wiki* gist (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f, May 2026). The pattern: dense markdown corpus maintained by an LLM agent that follows a `CLAUDE.md`/`AGENTS.md` contract, with `index.md` (catalog) and `log.md` (append-only) as special root files.

The four base playbooks are explicit compositions of established frames: Anthropic Economic Index (ai-exposure), Wardley (value-map), Choudary (reshuffle), Dorsey + Botha (world-model). The term "structure" instead of "substrate" follows Simone Cicero, *What is an organization today?* (Through The Boundary, April 2026) — see the vocabulary entry above for the URL.

We borrow the pattern; we call our artefact `org/`, not a wiki.
