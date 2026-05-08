# Playable Org

A graph of cited claims about an organization, maintained by an agent, with read-models layered on top.

The graph lives as markdown files. Each file has frontmatter (a typed shape) and a body (prose). Every claim cites the source it came from. The agent reads the org's actual documents — charter, role descriptions, meeting notes, contracts — and proposes diffs against the graph, which a human confirms. Once the graph is populated, **read-models** (we call them *playbooks*) compose specific lenses on top of it: the whole org as one connected force-directed picture, where AI presses on each activity, how the value chain looks under evolution pressure, how AI changes the bundle structure, what the org looks like as a platform of capabilities. Each read-model is a frozen artefact (HTML + JSON), reproducible from the graph at any later time by re-running the playbook.

The artefact is not a wiki, not an RDF knowledge graph, not a BPM tool, not a Notion replacement. See *Where it sits* below.

## The four layers

```
       ┌─────────────────────────────────────────────────┐
LAYER 4 │ agent  (Claude Code / Claude Desktop)            │
       │   reads + writes the graph via the mcp surface   │
       └─────────────────────────────────────────────────┘
                          ▲ ▼
       ┌─────────────────────────────────────────────────┐
LAYER 3 │ mcp-server/  — 13 typed primitives               │
       │   read   (read, search, list, neighbors)         │
       │   write  (write_node, save_source, log_append)   │
       │   meta   (skills_list, skill_read)               │
       │   exec   (lint_run, play_run, autoresearch_run,  │
       │           open)                                  │
       └─────────────────────────────────────────────────┘
                          ▲ ▼
       ┌──────────────────────┬──────────────────────────┐
LAYER 2 │ skills/              │ org/plays/                │
       │ recipes the agent    │ frozen read-models        │
       │ follows (SKILL.md +  │ produced by skills on a   │
       │ optional py: build,  │ slice of the structure;   │
       │ audit, viewer)       │ HTML + JSON, citable      │
       └──────────────────────┴──────────────────────────┘
                          │ ▲
                          ▼ │  cite
       ┌─────────────────────────────────────────────────┐
LAYER 1 │ org/  — cited structure                          │
       │   units / activities / people / commitments      │
       │   stakeholders / sources                         │
       │   each markdown file: frontmatter (typed)        │
       │   + body (prose). Every claim cites a source.    │
       └─────────────────────────────────────────────────┘
```

Two invariants hold across all layers:

- **Every claim in `org/` cites a source under `sources/`.** No exceptions. The lint script refuses commits that violate this.
- **Plays are frozen at creation.** A play asserts the world at time T. Re-running the same playbook at T+N produces a new play; the old one stays as the historical reading. No mutation in place.

Where Cicero (*[Through The Boundary, May 2026](https://through-the-boundary.simonecicero.com/)*) frames a context bundle as **data model + business logic + UX**: layer 1 is the data model; layer 2's playbooks are the business-logic-as-read-models; the agent is the UX. The bridge to deployable agents — exporting a `CLAUDE.md` per scope (`compile-agent`), filling Gherkin-equivalent density per activity (`interview-activity`) — is built and shipped; the formal context-bundle export (Gherkin scenarios, RDF triplets) is on the roadmap.

## Where it sits

| Compared to | Playable Org is | Playable Org is not |
|---|---|---|
| Wiki (Confluence, Notion) | agent-maintained markdown under an `AGENTS.md` contract | not human-editable in a UI; the agent is the editor, with diffs confirmed by a human |
| Knowledge graph (RDF / Neo4j) | typed YAML frontmatter on every node, structured cross-references | not triples; markdown is the storage, the agent + lint script are the query engine; humans read the graph as prose |
| BPM tool (Camunda, BPMN) | activities have performers, inputs, outputs, frequency, and (optional) trigger / quality_gates / decision_criteria / output_format / fallback / handoff | not executable; the structure documents the work; the agent runs it via composed `skills/` |
| LLM-wrapper / RAG over docs | the agent reads `org/` to answer | not raw RAG; the cited structure is the moat. Without `(source-id)` citations on every claim, agents hallucinate; with them, every answer points back to a real document |
| Org chart | five node types (unit, person, role, activity, stakeholder) plus commitments | not a hierarchy; commitments are richer than reporting lines (level × direction × explicit × state × fallback) |

The thing the artefact aims to be is a **substrate**: enough cited structure for an agent to act on, minus the bureaucracy of formal ontologies, plus the editorial discipline that keeps the prose readable.

## The five read-models (playbooks)

Each playbook produces an HTML + JSON pair under `org/plays/data/`. Same chrome across all five (one container width, popover on click, "How to read this map" decisions section). Different lenses on the same `org/`.

| Playbook | Question it answers | Source theory |
|---|---|---|
| **graph** | What does the whole organization look like as one connected graph? Which nodes are load-bearing? Where has the structure not been written down yet? | None — mechanical render of the corpus as the structure declares itself. |
| **ai-exposure** | For each activity, how is AI used today on the closest matched task in a public sample? Which org activities are most exposed, and how? | Anthropic Economic Index (March 2026) — observed-usage signal across O\*NET tasks |
| **value-map** | Where does each piece of the work sit on evolution × visibility, where is AI pushing it, and what new pieces are emerging that don't exist yet? | Simon Wardley — value-mapping with evolution stages |
| **reshuffle** | For a process slice, what holds each activity in place (rare resource / cost-of-being-wrong / cost-of-keeping-aligned)? Which AI uses change structure (engine) vs just speed (tool)? Which rebundle moves does the analysis suggest? | Sangeet Paul Choudary, *Reshuffle* (2024) |
| **world-model** | The org as platform: capabilities + world model + intelligence layer + interfaces. What's differentiated vs standard? What pieces of the chain don't exist yet that the demand already implies? | Jack Dorsey + Roelof Botha, *From Hierarchy to Intelligence* (Block, March 2026) |

The playbooks compose: graph first (the lightest, after the first ingest, no AEI dependency, no interpretive frame), then ai-exposure (broadest analytical survey), then value-map (each activity placed on the curve), then reshuffle (constraint analysis on a slice), then world-model (capability-level overlay). The composition is documented in `skills/ROADMAP.md`.

Each playbook ships its own audit gate (anti-hallucination, deterministic) plus an autoresearch gate (five dimensions: recognizability, plain-language, decision-anchoring, audit-grounded, plus an opt-in LLM judge). The judge can run in **subscription mode** (the agent in the user's session applies the rubric in-context, no API key) or **API mode** (`autoresearch.py --llm`, calls Claude Sonnet 4.6 via SDK, for CI). The rubric is in `skills/playbooks/AUTORESEARCH-JUDGE-RUBRIC.md`.

## Opinionated choices

Each is a non-default decision; each has a rationale.

- **Markdown corpus, not RDF triples.** Humans read the graph as prose; agents read both the prose and the typed frontmatter; git tracks revisions. Cost: less query-able than a triplestore. Mitigation: the YAML frontmatter is structured, and the agent is the query engine — through `org_search` / `org_neighbors` / `org_list`.

- **Agent-maintained, not human-edited.** The org's documents change; the agent re-walks them and proposes diffs; humans confirm. Cost: agent reliability is now load-bearing. Mitigation: three deterministic gates (lint Tier 1 + Tier 2; per-playbook `audit.py`; per-playbook `autoresearch.py`) plus the citation invariant. No claim ships without a source.

- **Plays are frozen at creation; structure is immutable-by-convention.** An analysis at time T must be reproducible at time T+N. Without freezing, plays drift and "what did we conclude in May" loses meaning. Cost: a play goes stale within months. Mitigation: re-running is one `org_play_run` call; the historical play stays as the past reading.

- **Conditional voice on emerging items.** Anything in `org/` or in a play that names a thing *that doesn't exist today* (a new component, a new stakeholder type, a candidate role, a piece-to-build) is written with `if / would / could / depends on`, never `when / will / makes`. Cost: prose feels less assertive. Gain: the artefact reads as an analysis, the org keeps agency. The map suggests preconditions are approaching; whether to build the thing stays the org's call. Documented in `skills/STYLE.md`.

- **Plain-language jargon discipline in user-facing prose.** Framework primitive names are fine as labels (Stakeholders, Capabilities, Genesis/Custom/Product/Commodity); paraphrased into running prose they become jargon and the leader stops on them. Avoid-list (lives in `STYLE.md`): *moat*, *commodity* in body, *commoditize*, *judgment density*, *capability stack*, *coordination tax*, *failure-signal*, *thin* (metaphor), *see-saw*, *flywheel*, *engine candidate*, *rebundle*, *production-tier*, *rich subset*, *O\*NET*, *AEI*, *embedding*, *cosine similarity*, *top-K*, *p25*/*p75*, JSON field names. The autoresearch jargon dimension catches deterministic violations; the editorial pass catches paraphrased ones.

- **Prepend-only `log.md`.** Most-recent-on-top is faster to scan during audit. Semantically still append-only (no edits, no deletions). Trades a UNIX convention for ergonomics; we think the trade is worth it.

- **Activity density layer is opt-in per activity.** A first-install activity has the structural floor (description, performer, unit, inputs/outputs, frequency, sources). The density ceiling — `trigger` / `quality_gates` / `decision_criteria` / `output_format` / `fallback` / `handoff` — gets filled only when the org wants to compile that activity into a Claude skill. Cost: two registers in the same schema. Gain: the floor stays low (every activity has structural facts); the ceiling opens for the activities that need to become agent-runnable. Documented in `org/AGENTS.md`.

## What ships in the public template

- **mcp-server**: 13 tools, TypeScript stdio, 84/84 e2e tests, ~30KB compiled.
- **skills**: 11 skills total. Three operational (`init`, `ingest`, `lint`); five playbooks (`graph`, `ai-exposure`, `value-map`, `reshuffle`, `world-model`); two deployment skills (`compile-agent` for scope-limited agents, `interview-activity` for filling the activity density layer); one meta-skill (`new-playbook`).
- **sample-org**: a fully populated test fixture under `mcp-server/test-fixtures/sample-org/`. The Outline & Co. fake studio: 5 units, 14 activities, 5 people, 4 stakeholders, 4 commitments, 3 sources, plus the five canonical playbook artefacts (HTML + JSON + judge verdicts where applicable) and two activities with the density layer filled (brand-positioning, kickoff-workshop). Open `plays/data/*.html` to see exactly what each playbook produces.
- **install.command / install.bat**: clickable installers (no admin required). Build the mcp server, register it in Claude Desktop's config.
- **design system**: `skills/design.py` — single source of truth for the visual language (Inter Variable + opacity-layered grayscale + small pastel data-viz palette). Forks override the brand font by replacing `_assets/fonts/inter-variable.woff2`.

The public template's `org/` is empty (3 identity stubs marked `# REPLACE ME`). Forks populate it from real org documents.

## Frontier

Built and shipped:

- The five playbooks with the unified chrome (1240px container, 820px editorial column for editorial bookends; the graph viewer extends its canvas to 1160px because the topology genuinely needs the width). Popover on click, "How to read this map" decisions section, conditional-voice rule on emerging items.
- The five-dimension autoresearch loop, with subscription-mode (agent-as-judge in-context) as the default and API-mode as the CI fallback. Verdicts produced for all four interpretive sample-org plays (ai-exposure, value-map, reshuffle, world-model); graph runs the four deterministic dimensions (the LLM-judge dimension is opt-in there too).
- `compile-agent` skill — given a scope (`org` / `unit:<id>` / `person:<id>` / `commitment:<id>`), emit a `CLAUDE.md` that turns a Claude Code session into an agent that knows that scope. Currently a recipe-an-agent-follows-by-hand via the existing read tools; the mechanised compiler is the next iteration.
- `interview-activity` skill — the eight-question Q&A flow that fills the density layer for one activity (interviewing the performer, saving the transcript verbatim as a source, structure-extracting the six fields). Demonstrated on two sample-org activities.

On the roadmap, with explicit composition with adjacent work:

- **`compile-agent --with-skills`** — once an activity has the density layer filled, export it as a Claude slash-command skill. Bridge from Level 1 (scoped CLAUDE.md) to Level 2 (invocable skills). The mechanism is sketched in `skills/compile-agent/SKILL.md`; the implementation lands when 3-5 activities have been density-filled in a real fork.

- **`context-bundle` playbook** — formal export of the structure as Cicero's three-layer context bundle: data model (RDF triples derived from the YAML frontmatter), business logic (capability×role matrix + Gherkin scenarios derived from the activity density layer), UX (User Postures derived from the stakeholder side of `world-model`). Composes with [Cicero's context-bundling thread](https://through-the-boundary.simonecicero.com/) directly.

- **`autoresearch` as wiki feature** — the `org_autoresearch_run` mcp tool ships today; the next iteration makes autoresearch a *property* of every play (and, eventually, every node), not an external command.

## Quick start

1. Clone or download. Open the folder.
2. Make sure Claude Desktop is installed and Node.js is on your PATH.
3. Double-click `install.command` (macOS) or `install.bat` (Windows). Restart Claude Desktop.
4. **Either** drop founding documents (charter, role-descriptions, contracts) into `org/sources/` (Path A — documents-first), **or** open Claude Desktop and ask it to *initialize the structure* with no documents (Path B — interview-first; the ten-question interview transcript becomes the founding source).
5. After 30-60 minutes you have a populated `org/`. From there: ask questions, ingest new documents as they arrive, run playbooks (`run the value-map on the customer-facing unit` / `run ai-exposure across the whole org` / etc.), open the rendered HTML in your browser.

Detailed: [`SETUP.md`](SETUP.md). Architecture: [`docs/architecture.md`](docs/architecture.md). Playbook reference: [`docs/playbooks.md`](docs/playbooks.md). Extension: [`docs/extending.md`](docs/extending.md).

## Lineage

The pattern — an LLM-maintained markdown corpus governed by an `AGENTS.md` contract, with `index.md` as catalog and `log.md` as audit — is from Andrej Karpathy, [*Building an LLM Wiki*](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (gist, May 2026). We keep the pattern and call our artefact `org/`, not a wiki. The term **structure** for the cited-graph layer comes from Simone Cicero, *[What is an organization today?](https://through-the-boundary.simonecicero.com/p/ttb-1-what-is-an-organization-today)* (Through The Boundary, April 2026), which contrasts the *structure* of an organization (topology, taxonomy, shared context, promise chains) — what AI makes more necessary — with the *superstructure* (hierarchical management, bureaucracy) — what AI eliminates.

Of the five playbooks, four are explicit compositions of established frames: Anthropic Economic Index (`ai-exposure`), Wardley (`value-map`), Choudary (`reshuffle`), Dorsey + Botha (`world-model`). The fifth (`graph`) has no external source — it is the structure rendered as the structure declares itself.

Author surnames appear in this README and in `skills/` documentation for credibility and reproducibility. They never appear inside `org/` artefacts (structure or plays) — those are written for the leader of the org being mapped, not for someone tracing the playbook's intellectual ancestry.

## License

MIT. See [`LICENSE`](LICENSE).

The bundled Inter Variable font is licensed under the SIL Open Font License (Rasmus Andersson). Forks that ship a different brand font replace `_assets/fonts/inter-variable.woff2` with their own woff2 at the same path. The Anthropic Economic Index dataset shipped with `ai-exposure` is licensed under CC BY 4.0 (Anthropic).
