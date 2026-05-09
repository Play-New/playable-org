# Playable Org

Public template for representing an organization as a structured, agent-maintained graph. Markdown files with YAML frontmatter, plus analytical playbooks on top. The bundled mcp server connects the graph to Claude Desktop.

This `CLAUDE.md` is working memory for whoever maintains the template (me, future contributors). It is not shipped to end users — the customer-facing docs are `README.md`, `SETUP.md`, `CONTRIBUTING.md`, `docs/`.

## Where things live

- `org/` — the organization instance bundle. Empty in the public template (3 identity stubs only). Forks populate it.
- `org/AGENTS.md` — operational contract for `org/`. **Read this before any write to `org/`.**
- `org/README.md` — entry point for whoever opens `org/`.
- `org/log.md` — prepend-only audit. Most-recent on top.
- `org/index.md` — content-oriented catalog (link + one-line summary). Updated by the agent on every ingest.
- `mcp-server/` — TypeScript stdio mcp server. 13 tools (4 read + 3 write + 1 meta + 5 executors), full e2e test suite at `mcp-server/test-e2e.py` against fixture in `mcp-server/test-fixtures/sample-org/`.
- `skills/` — agent workflows + analytical playbooks + design system. Three operational skills (`init`, `ingest`, `lint`), five analytical playbooks (`graph`, `ai-exposure`, `value-map`, `reshuffle`, `world-model`), two deployment skills (`compile-agent`, `interview-activity`), one meta-skill (`new-playbook`). Cross-cutting docs: `CAPABILITIES.md` (the four-property frame), `STYLE.md` (anti-rhetoric charter), `ROADMAP.md` (the playbook order), `design.py` (single source of truth for the visual language), `_assets/fonts/inter-variable.woff2` (embedded font; instances swap in their brand font at the same path).
- `docs/` — public-facing architecture, playbooks reference, extension guide, design direction (Lupi / Accurat / Fragapane references), `screenshots/` (rendered hero PNGs of every viewer, embedded in README; regenerate with `tools/screenshot-viewers.py`).
- `tools/` — utility scripts that don't fit anywhere else (`screenshot-viewers.py` for README hero PNGs).
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
- **Single design system in `skills/design.py`** (currently visual version 4). All viewers compose primitives from there. No bespoke `<style>` blocks beyond a slim playbook-specific extension that uses design tokens. v4 adds editorial chrome (Italianate masthead via `masthead()`, magazine colophon via `colophon()`, numbered-section headers via `section_head()`, marginalia via `marginalia()`), 5-stop colour scales per data-viz hue (`--ds-X-50/200/400/600/900` + `--ds-X-glow`), surface tokens (`--surf-paper / --surf-inset-dark / --surf-raised-shadow`), motion tokens (`--anim-entry / --anim-hover / --anim-stagger`). The design direction (Lupi, Accurat, Fragapane, Posavec, Bremer, Density Design, NYT Graphics) is documented in `docs/design-direction.md`.
- **Inter Variable as single font family in the public template** (Rasmus Andersson, SIL OFL — freely redistributable). One family for display, body, and the historical "mono" role, per Play New convention. Instance forks (e.g. AIRC-Org, Cosmico-internal) swap in their own brand font by replacing the woff2 at `_assets/fonts/inter-variable.woff2` and updating the family name in `design.py`. Mirage was tried (visual v2) but rolled back: Klim Type Foundry's standard license does not permit public redistribution of the font file.
- **Pastel data-viz palette as secondary**. Brand surfaces stay monochrome; `--ds-sage / --ds-lilac / --ds-slate / --ds-sand / --ds-coral` (in `design.py`) are used only inside viewer EXTRA_CSS for heatmap squares, stage bands, category swatches, and any element that needs category differentiation. State semantics (`--warn / --success / --info`) re-point to the same palette so brand and viz stay in sync.

## Public template state

- 13 mcp tools.
- 3 operational skills: `init`, `ingest`, `lint`.
- 5 analytical playbooks: `graph`, `ai-exposure`, `value-map`, `reshuffle`, `world-model`. All five use `design.py` primitives via inheritance through their viewer.py modules. Each ships with build.py + audit.py + viewer.py + autoresearch.py.
- 2 deployment skills: `compile-agent` (Level 1, scope-limited Claude Code agents), `interview-activity` (Level 2, fills the activity density layer).
- 1 meta-skill: `new-playbook`. Five-question interview that scaffolds a new playbook.
- 1 utility: `tools/screenshot-viewers.py` — Playwright-based screenshot capture for README hero PNGs.
- `design.py` at v4 — editorial direction (Lupi/Accurat/Fragapane). Masthead, colophon, numbered-section headers, marginalia, 5-stop colour scales, surface tokens, motion tokens. Backward-compatible with v3.
- 5 hero PNGs under `docs/screenshots/` — one per viewer, embedded in README.
- 1 design-direction doc: `docs/design-direction.md`.
- 1 architecture-philosophy doc: `docs/skills-as-capabilities.md`.
- `org/` empty: 3 identity stubs (`# REPLACE ME`), zero other content. Lint Tier 1 reports 3 expected warnings on the stubs (empty `sources` arrays); these go to 0 after init.
- mcp-server e2e: 88/88 PASS against `mcp-server/test-fixtures/sample-org/` (the Outline & Co. fake creative studio: 5 units, 14 activities, 5 people, 4 stakeholders, 4 commitments, 3 sources, plus the five canonical playbook artefacts under `plays/data/` — including the graph play with 41 nodes / 165 typed relations).
- TypeScript build: clean.

## Maintenance

When adding a new mcp tool:
1. Create `mcp-server/src/tools/<name>.ts`.
2. Register in `mcp-server/src/server.ts`.
3. Add a test in `mcp-server/test-e2e.py`.
4. Document in `docs/architecture.md` if the addition changes the surface area.

When adding a new playbook:
1. Create `skills/playbooks/<name>/{SKILL.md, build.py, audit.py, viewer.py, autoresearch.py}`.
2. Use `design.py` primitives in viewer.py — no bespoke `<style>` blocks. The viewer must open with `masthead()` and close with `colophon()`; both come from `design.py`. The build script must stamp `_dated: <YYYY-MM-DD>` in the JSON skeleton (use `date.today().isoformat()`).
3. Declare theoretical lineage explicitly in SKILL.md frontmatter and body. (For sourceless playbooks like `graph`, say so explicitly in the body — the absence of a source is itself a deliberate choice.)
4. Wire in `mcp-server/src/tools/org-play-run.ts`: add to the playbook enum, branch the build args if needed.
5. Add an entry to `skills/ROADMAP.md` and a section in `docs/playbooks.md`.
6. Add a build-mode test to `mcp-server/test-e2e.py`; bump the skill-list count assertion.
7. Run `python3 tools/screenshot-viewers.py` to add a hero PNG under `docs/screenshots/<name>.png` and embed it in README.md.

When changing the design system:
1. Update `skills/design.py` only. Never edit the CSS in viewer.py files.
2. If the change requires migration of existing viewers (renamed token, removed primitive), update all five base viewer.py files in the same commit.
3. Bump the visual-version comment at the top of `design.py` so downstream viewers can detect.
4. Re-render every sample-org artefact and regenerate `docs/screenshots/*.png` so the README stays in sync.
5. Update `docs/design-direction.md` if the change introduces a new editorial primitive (masthead variant, marginalia style, colour scale, motion token).

When the public template gets new features that downstream forks should pull in:
1. Commit on `main` of `playable-org`.
2. Forks (instance repos) merge `upstream/main`. The public template never modifies `org/` content beyond the 3 identity stubs, so merge conflicts are minimal.

## Lineage

Direct: Andrej Karpathy's *Building an LLM Wiki* gist (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f, May 2026). The pattern: dense markdown corpus maintained by an LLM agent that follows a `CLAUDE.md`/`AGENTS.md` contract, with `index.md` (catalog) and `log.md` (append-only) as special root files.

Of the five base playbooks, four are explicit compositions of established frames: Anthropic Economic Index (ai-exposure), Wardley (value-map), Choudary (reshuffle), Dorsey + Botha (world-model). The fifth (graph) is sourceless — it renders the structure as the structure declares itself, with no interpretive frame in between. The term "structure" instead of "substrate" follows Simone Cicero, *What is an organization today?* (Through The Boundary, April 2026) — see the vocabulary entry above for the URL.

We borrow the pattern; we call our artefact `org/`, not a wiki.
