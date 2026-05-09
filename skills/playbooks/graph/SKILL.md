---
name: graph
description: "Render the whole organization as one graph: every node (unit, activity, person, stakeholder, commitment, source, identity, financial-summary) and every relation declared in the structure between them. Output: an interactive force-directed visualization plus a leader-facing reading of the topology — which nodes are load-bearing, which regions are thin, where the structure has been written down and where it has not."
---

# Playbook: graph

## How this playbook is run (read this first)

This playbook **must** produce a persistent file artefact under `org/plays/data/`, not an in-chat widget.

**Required tooling**: `org_play_run` (mcp tool). Two calls per run:

1. `org_play_run(playbook="graph", mode="build")` → walks every node under `org/`, collects every typed relation declared in frontmatter and every body markdown link / source citation, and returns the graph JSON inline (`nodes[]` + `edges[]` + `_topology` summary). Read `org_skill_read("STYLE")` before drafting decisions.
2. `org_play_run(playbook="graph", mode="render", json_content=<graph + decisions>)` → writes JSON, runs `audit.py`, runs `viewer.py`, returns artefact paths and audit summary.

**Do not** use Claude Desktop's inline widget / artifact features. The HTML returned by `org_play_run` mode=render is the canonical visualization.

**Do not** hand-write a markdown play file under `plays/`. The JSON + HTML pair under `plays/data/` is the play.

If `org_play_run` errors, report verbatim and stop. Do not fall back to an in-chat widget.

**How to present the result — strict protocol**:

1. As soon as render returns `status: "ok"`, call `org_open` immediately with `artefacts.html` (relative path). Opens in the default browser.
2. Paste the response `presentation_markdown` field **verbatim**. It is already a `[text](file://...)` Markdown link; do not wrap, quote, or rephrase.
3. Add one short sentence of context (e.g. "41 nodi, 165 relazioni, 0 isolati; 3 nodi più connessi: outline-roles-2025, outline-charter-2024, design").
4. Do NOT inline-render any custom widget.

## Output style

All consumer-facing text produced by this skill (decisions, viewer copy, popover labels) follows the project style charter in [skills/STYLE.md](../../STYLE.md). The graph is the most plumbing-flavoured of the playbooks; the discipline matters more, not less. No graph-theory jargon (degree centrality, betweenness, clustering coefficient) leaks into the leader-facing prose. The autoresearch gate enforces this.

The deliverable is a frozen `play` written as a JSON + HTML pair in `org/plays/data/graph-<scope>-<date>.{json,html}` — there is no markdown play file under `plays/` for this skill, the artefact lives entirely under `plays/data/`.

## What this skill does that's different

This skill differs from the previous four:

- **ai-exposure** maps activities to AEI tasks. Activity-grain.
- **value-map** maps a value chain on the evolution-visibility plane. Component-grain.
- **reshuffle** diagnoses how AI changes the bundle structure of a slice. Bundle-grain.
- **world-model** redescribes the organization as a five-layer stack with capabilities at the bottom and stakeholders at the top. Organization-grain, structural.
- **graph** reads the structure as itself: every node and every relation it declares, with no interpretive layer in between. Topology-grain.

The first four read the structure through a frame. This one reads the structure as the structure is written. It is the simplest of the five and the one that shows the leader where the writing is dense and where it is thin without committing to any interpretive vocabulary.

## Pre-conditions

- Structure `org/` has at least the minimum viable shape: identity (mission), at least one unit, at least one activity, at least one stakeholder, at least one commitment, at least one source. The audit refuses to render a graph with empty kinds.
- Lint Tier 1 should pass — broken citations and dangling ids show up as missing edges in the graph but the audit there is run by `lint.py`, not this skill.

## Workflow

### 0. Canonical invocation via mcp

When the bundled mcp server is available, launch this playbook via `org_play_run`:

1. `org_play_run(playbook="graph", mode="build")` → returns the graph JSON (nodes + edges + topology summary).
2. Read `_topology.top_connected` (the load-bearing nodes) and `_topology.isolated` (the unconnected ones). These are the two anchors for the decisions you'll write.
3. Open the rendered viewer (mode=render then `org_open`) and look at the layout — the force simulation surfaces clusters and bridges that the topology summary doesn't.
4. Author 3 to 5 decisions per the rules in §3 below.
5. `org_play_run(playbook="graph", mode="render", json_content=<graph JSON with decisions[] filled>)` → produces artefact + audit + viewer.
6. Append a log line via `org_log_append`.

If `org_play_run` is not available (older mcp build), fall back to the manual steps below.

### 1. Build the graph

```bash
python3 skills/playbooks/graph/build.py \
  --org-dir org \
  --out org/plays/data/graph-<scope>-<date>.json
```

Build walks `org/` and emits:

- **Nodes**: every file under `nodes/units`, `nodes/activities`, `nodes/people`, `nodes/roles`, `nodes/stakeholders`, `commitments`, `sources`, `identity`, `language`, `financials` becomes a node with id, kind, label, description, state, and relative path. Ten kinds total, mirroring the schema in `org/AGENTS.md`.
- **Edges** (typed): `parent` (unit → unit), `unit` (person/activity/role → unit), `performer` (activity → person), `head_role` (unit → role), `holds_role` (person → role), `covers` (role → activity), `party_committing` / `party_benefiting` (commitment → unit/stakeholder/person), `touches` (activity → stakeholder), `cite` (any → source), `link` (any → any node, when a body markdown link resolves to another node file).
- **`_topology` summary**: nodes_total, edges_total, by_node_kind, by_edge_kind, top_connected (eight nodes by degree on the full graph), isolated.

Build does not interpret. Decisions are not written here.

### 2. Read the graph in the viewer

```bash
python3 skills/playbooks/graph/viewer.py \
  --map org/plays/data/graph-<scope>-<date>.json \
  --html org/plays/data/graph-<scope>-<date>.html
```

The HTML is the **primary consumer artefact**. **This shape is frozen**; the canonical Outline & Co. play under `mcp-server/test-fixtures/sample-org/plays/data/graph-outline-2026-05-08.html` is the reference render. Page structure, in order:

1. **Header** (820px centered): eyebrow `graph` + h1 title + one-paragraph lead.
2. **Intro** (820px centered): two paragraphs explaining what the page is and how to read it (size = number of mentions; clusters = parts of the org that talk to each other in writing), plus a pull-quote on what the topology says.
3. **Stats strip** (820px centered): four numbers — nodes, relations, kinds, isolates.
4. **Legend** (1160px centered): row of clickable kind swatches (click to dim a kind) + the hint "click a kind to dim it · click a node to inspect".
5. **Graph canvas** (1160px centered, 640px tall): force-directed SVG. Vanilla JS, ~80 lines of simulation code. Circles sized by degree, coloured by kind. Edges hairline, dashed for `cite`, lighter for `link`, solid+dark for `parent`.
6. **Decisions section** (820px centered): "How to read this graph" — the leader-facing reading.

**Visual code (frozen)**:

- **Shape = circle for every node**. Graphs read shape unreliably; the differentiator is colour and size.
- **Colour = node kind**. Pulled from the project's data-viz palette (`--ds-sage / --ds-lilac / --ds-slate / --ds-sand / --ds-coral`) so the graph viewer and the other four viewers stay coherent.
- **Size = log of degree** computed against the *currently visible* subgraph (not the full graph). Toggling kinds on/off recomputes degrees so the "what's load-bearing right now" reading stays accurate.
- **Edges hairline (0.5–1.2px, opacity 0.6 in focus / 0.06 out of focus)**. Parent edges solid+dark; structural edges medium; bibliographic edges thin and dashed. The graph reads as topology, not as a wiring diagram.
- **Labels appear only for nodes with degree ≥ 4** in the current visible subgraph, plus the focused node and its first-degree neighbours. Avoids canvas clutter at AIRC scale (hundreds of nodes).

**Default visibility (frozen)**:

- **Visible by default**: `unit`, `activity`, `person`, `stakeholder`, `commitment`. The five operational kinds — what shows where the org's weight insists.
- **Hidden by default**: `identity`, `language-term`, `role`, `financial-summary`, `source`. Declarative / taxonomic / corpus metadata that either distorts the spatial picture (cited-source hubs) or duplicates what the operational kinds already say.
- **Visible edges by default**: the structural relations (`parent`, `unit`, `performer`, `head_role`, `holds_role`, `covers`, `party_committing`, `party_benefiting`, `touches`).
- **Hidden edges by default**: `cite`, `link` (bibliographic).

The legend is the live filter. Toggling a kind removes those nodes (or those edges) from the simulation entirely so the rest of the graph repacks the freed space — not a dim, an actual filter. The simulation reheats on every toggle and settles to a new layout.

**Click-to-focus (frozen)**. Clicking a circle:
1. Opens a popover below it (centred horizontally, flipping above when there's no room — same pattern as the other four playbooks).
2. **Dims everything that isn't the clicked node or its first-degree neighbours.** This is the affordance that makes the graph navigable at AIRC scale.
3. Highlights the focused node's circle with a heavier stroke.

Click empty space (or Esc) clears focus.

**Popover contents**:

- Eyebrow with the kind (`unit`, `activity`, `person`, `role`, `stakeholder`, `commitment`, `financial-summary`, `identity`, `language-term`, `source`).
- The full label as h3.
- Description paragraph (from the node's frontmatter `description`).
- Outgoing relations list (relation label + target name; first 10, "+ N more" beyond). Filter-aware — only relations through currently-visible edge kinds appear.
- Incoming relations list (same shape, with reversed relation labels: `cited by`, `hosts`, `performs`, etc.).
- Footer citation: the relative path of the node's source markdown file.

**Viewport interactions (frozen)**:

- Wheel zoom (0.3× to 4×, anchored on the cursor).
- Drag to pan.
- "reset view" button restores the default 1× translate(0,0).
- "re-shake" button nudges every visible node by a small random vector and reheats the simulation, useful when the layout settles into a local minimum.

**Plain-language discipline (frozen)**. The relation labels are written in plain English: `is part of`, `sits in`, `performed by`, `led by`, `holds role`, `covers`, `commits`, `benefits`, `touches`, `cites`, `mentions` — never `parties_committing`, never `degree`, never `edge`. Inside the prose and the decisions, no graph-theory vocabulary leaks. Words to never use in user-visible strings:

- `node degree` → "how many things connect to it" / "how connected"
- `degree centrality`, `betweenness`, `clustering coefficient` → never
- `hub`, `subgraph` → "load-bearing node", "region of the structure"
- `sparse / dense` is acceptable when used about regions of the structure; not as graph-theory shorthand.

Decisions are reviewed by `autoresearch.py` against the deterministic jargon list.

**`--decisions <list.json>`** merges a JSON list of `{question, answer, source}` into the map's `decisions[]` field before rendering. **Required** for a shippable play — autoresearch fails without it.

### 3. Author the decisions

The decisions are the load-bearing interpretive surface of this playbook. Without them the graph is just a picture. Three rules for writing them:

1. **Anchor on what the graph shows, not on an abstract claim.** The form is: "the topology shows X (load-bearing node Y, sparse region Z); for the leader this means W". Each decision should pass the test: a reader who saw only the graph and not the structure could read the decision and recognize what they're looking at.
2. **Name nodes by name.** "Lena", "design area", "studio-mid-market-baseline", "outline-charter-2024" — the recognizability gate fails decisions that read as generic.
3. **Conditional voice for emerging items.** If a region of the structure is thin (few edges, few mentions), the decision says "the structure has not been written down here yet" or "the org would have to author X for the picture to fill in" — not "the org is missing X". Topology silence is not the same as organizational absence; the playbook reads the writing, not the org.

Author 3 to 5 decisions. Each:
- `question`: the leader-facing question the decision answers (e.g. "Where does the documentation actually live?", "Which nodes is the structure most reliant on?", "Where is the structure written most thinly?").
- `answer`: the answer, ≥ 60 chars, named anchors.
- `source`: a node id or a path under `org/`, citing the part of the structure the answer anchors on.
- `node_ids` (optional): list of node ids referenced; if provided, the audit-grounded gate verifies they all resolve.

### 4. Audit

```bash
python3 skills/playbooks/graph/audit.py \
  --map <graph.json> \
  --org-dir org
```

The audit verifies:
1. Every node has id, kind, label.
2. No duplicate node ids.
3. The graph has at least one node of each required kind (unit, activity, person, stakeholder, commitment, source).
4. Every edge endpoint resolves to a node; every edge kind is in the allowed set; no duplicate (from, to, kind) tuples.
5. ≥ 3 decisions, each with question + answer ≥ 60 chars + source.

### 5. Autoresearch

```bash
python3 skills/playbooks/graph/autoresearch.py \
  --map <graph.json> \
  [--llm]
```

Five dimensions, four deterministic + one opt-in:

| Dimension | What it checks |
|---|---|
| **Recognizability** | Decisions mention specific units / activities / people / stakeholders / sources of the org by name (≥ 3 distinct names). |
| **Plain language** | No graph-theory jargon (degree centrality, betweenness, clustering coefficient, hub node, subgraph) and no leakage of other-playbook framework names (capability stack, world model, value chain, bundle, moat). |
| **Decision anchoring** | ≥ 3 items in `decisions[]`, each ≥ 60 chars in `answer`, each citing a non-empty `source`. |
| **Audit grounded** | Every node id named in a decision's `node_ids` field resolves to a real node in the graph. |
| **LLM judge** *(opt-in: `--llm`)* | Claude Sonnet 4.6 scores each decision on `actionable` (yes/no), `distinctive` (high/medium/low), `readable` (yes/no). Skipped when `ANTHROPIC_API_KEY` is not set. |

### 6. Lint + log

`python3 lint.py` should pass (the graph play does not write to structure files, but the audit gate above is the substantive one). `org_log_append` with a one-line summary including node and edge counts.

## Method limits

- **The graph reads the writing, not the org.** Nodes and relations come from what the structure declares. A relation that exists in the world but has not been written down does not appear in the graph. The play's job is to surface this — a sparse region is an invitation to write, not a verdict that something is absent.
- **Force-directed layouts are not unique.** Two runs of the simulation against the same graph produce slightly different positions; clusters and bridges are stable but exact angles drift. The decisions should anchor on relations, not on geometry.
- **Citation edges dominate at typical sizes.** Source documents are referenced from many nodes, so source nodes naturally read as load-bearing. The leader should read this as "the documents that anchor the structure are the documents most cited" — informative, not surprising.
- **The playbook does not score the org.** It surfaces what is connected to what. Whether a region of the structure being thin is a problem or a deliberate choice is a question the leader answers; the play poses it.

## Anti-hallucination discipline

Three structural rules:

1. The graph is mechanically built from the structure. The build script does not invent nodes or edges; the audit refuses unresolved endpoints. If a decision claims a node, that node must exist.
2. Decisions cite a `source` (node id or `org/` path). The autoresearch gate refuses empty sources.
3. Conditional voice on thin regions. If the structure has no writing on something, the decision says so explicitly — never "the org doesn't do X", always "the structure has not been written down here yet" or "the org would have to author X to make this part of the picture legible".

## When to run this skill

The graph is the lightest of the five and the one that is most useful early. Run it after the first ingest (when the structure has at least 10 nodes and a handful of citations) to give the agent and the leader a single picture of what is in the corpus. Re-run after any major ingest pass — the topology change between runs is itself informative.

It can be run alongside any of the other four playbooks; the graph view of the structure does not depend on a prior interpretive read.

## Reference example

The canonical artefact for this skill is the Outline & Co. sample-org play:

- `mcp-server/test-fixtures/sample-org/plays/data/graph-outline-2026-05-09.json` — the source JSON with the full graph (41 nodes, 165 typed relations) + 3 decisions
- `mcp-server/test-fixtures/sample-org/plays/data/graph-outline-2026-05-09.html` — the rendered viewer

Open the HTML in a browser to see exactly what this skill produces. The default view shows 32 nodes and 75 edges — the operational core: 5 units, 14 activities, 5 people, 4 stakeholders, 4 commitments. The two stakeholder types (enterprise-clients, mid-market-clients) come out as the most-connected nodes (degree 13 each); the four client-facing units cluster at near-equal weight (6–7); operations sits visibly below at 6. The three decisions name the operational quadrant (where the org's weight insists), the load-bearing commitment, and the regions written most thinly (strategic-partners, studio-vendors, quarterly-finance-review). Toggle `source` and `cite` from the legend to see the full bibliographic picture.
