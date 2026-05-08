# Playbooks reference

Five base playbooks plus one meta-skill. Each answers one analytical question and produces a frozen artefact under `org/plays/data/`.

## ai-exposure

**Question.** For each activity in the structure, how exposed is it to AI? What kind of AI work do we observe today on similar tasks?

**Source theory.** Anthropic Economic Index, March 2026 release. Empirical signal of AI usage in occupational tasks. Claude conversations sampled and mapped to ~1,000 O*NET task labels, with autonomy + adoption metrics per task.

**What it does.**
1. Reads every `nodes/activity/*.md` in the structure.
2. Computes a multilingual sentence embedding per activity.
3. Maps each activity to its 5 nearest O*NET tasks by cosine similarity.
4. For each match, retrieves the AEI metrics (autonomy fraction, sample size, penetration).
5. Classifies the activity into one of five buckets: `strong`, `medium`, `mixed`, `zero`, `low-confidence`.
6. Renders an interactive HTML report grouped by area.

**Output.**
- `org/plays/data/all-org-matches-<date>.json` — raw matches with metrics.
- `org/plays/data/area-notes.json` — per-area qualitative notes.
- `org/plays/data/ai-exposure-<date>.html` — interactive viewer.

**Detail.** [`skills/playbooks/ai-exposure/SKILL.md`](../skills/playbooks/ai-exposure/SKILL.md).

## value-map

**Question.** Where does each component of a process sit on the evolution curve (genesis → custom-built → product → commodity), and where is AI pushing it?

**Source theory.** Simon Wardley, value-chain mapping (2005-). Components of a process are placed on a 2D grid: visibility (how directly the user sees this) on the y-axis, evolution (genesis → commodity) on the x-axis. The map exposes which components are differentiating, which are commoditizing, which need investment.

**What it does.**
1. Takes an anchor: a commitment, a unit, or a stakeholder slice.
2. Walks the structure to find components reachable from the anchor.
3. The agent positions each component on the evolution × visibility grid, with citations.
4. Optionally overlays AI effect per component, grounded in AEI matches from `ai-exposure`.
5. Marks components targeted to evolve (with `evolution_target`) or new components emerging (`is_new`).
6. Renders an interactive map (HTML) plus a static SVG fallback.

**Output.**
- `org/plays/data/value-map-<anchor>-<date>.json`
- `org/plays/data/value-map-<anchor>-<date>.html`
- `org/plays/data/value-map-<anchor>-<date>.svg`

**Detail.** [`skills/playbooks/value-map/SKILL.md`](../skills/playbooks/value-map/SKILL.md).

## reshuffle

**Question.** What constraints hold a process bundle together today? When AI matures, which uses are accelerators (don't change structure) and which are engines (force the bundle to reconfigure)?

**Source theory.** Sangeet Paul Choudary, *Reshuffle* (2024). A bundle of activities is held together by one of three constraint types: scarcity (rare expertise/resource), risk (cost of being wrong), coordination (cost of keeping teams aligned). AI either accelerates within the existing bundle (tool) or dissolves a constraint and forces a new bundle (engine). Only engines reconfigure organizations.

**What it does.**
1. Takes a slice (commitment, area, or division).
2. Inventories every activity in the slice.
3. The agent classifies each activity's primary constraint type with structure citations.
4. For each AI use case identified in the slice (typically grounded in AEI matches), the agent classifies it as `tool` or `engine`.
5. The agent surfaces rebundle candidates: alternative groupings of activities that emerge if specific engines dissolve specific constraints.
6. Renders an interactive viewer with constraint colour-coding, tool/engine badges, autonomy-coordination axis, coordination-paradox flag.

**Output.**
- `org/plays/data/reshuffle-<slice>-<date>.json`
- `org/plays/data/reshuffle-<slice>-<date>.html`

**Detail.** [`skills/playbooks/reshuffle/SKILL.md`](../skills/playbooks/reshuffle/SKILL.md).

## world-model

**Question.** Reading the organization as a platform: what are its capabilities? Which are uniquely hard to acquire (moat) vs commodity? Where does the organization fail to compose capabilities into solutions for stakeholders?

**Source theory.** Jack Dorsey + Roelof Botha, *From Hierarchy to Intelligence* (Block, March 2026). An organization has four layers. **Capabilities** are atomic invocable functions with a public contract (input, output, SLO, regulatory constraints). **World model** is the representation of operations and stakeholders. **Intelligence layer** composes capabilities into responses to stakeholder signals. **Interfaces** deliver. The roadmap emerges from failure signals: composition attempts that fail because a capability is missing.

**What it does.**
1. Inventories candidate capabilities by clustering activities.
2. Filters via the five-property test (invocable, structured output, atomic, hard to acquire, composable). See [`skills/CAPABILITIES.md`](../skills/CAPABILITIES.md).
3. The agent classifies each capability as `moat` or `commodity` with rationale.
4. For each stakeholder type the agent fills bidirectional fields: what they get from the org, what they contribute back, the most honest signal recorded, current maturity, fragmentation across teams.
5. The agent surfaces pieces to build (formerly "failure signals"): stakeholder requests that fail today because one needed piece of the chain isn't there yet.
6. Renders the layered stack with a floating popover on every clickable card.

**Output.**
- `org/plays/data/world-model-<scope>-<date>.json`
- `org/plays/data/world-model-<scope>-<date>.html`

**Detail.** [`skills/playbooks/world-model/SKILL.md`](../skills/playbooks/world-model/SKILL.md).

## graph

**Question.** What does the whole organization look like as one connected graph? Which nodes are load-bearing? Where is the structure dense, and where has it not been written down yet?

**Source theory.** None — this playbook is the only one without an external source. The structure is rendered as the structure declares itself, with no interpretive frame in between. It is the lightest of the playbooks and the one to run earliest, after the first ingest, before any of the framed reads.

**What it does.**
1. Walks every node in `org/`: identity, units, activities, people, stakeholders, commitments, financial summaries, sources.
2. Collects typed edges from frontmatter id arrays (parent, unit, performer, parties_committing, parties_benefiting, stakeholders_touched), from body markdown links that resolve to other nodes, and from the citation pattern `(source-id)` in the body.
3. Surfaces a topology summary: top-connected nodes by degree, isolates, edge counts by kind.
4. The agent reads the graph in the viewer, then authors 3–5 leader-facing decisions naming load-bearing nodes, sparse regions, and where the structure has not been written down.
5. Renders an interactive force-directed visualization (vanilla JS, no D3 dependency) with click-to-inspect popovers.

**Output.**
- `org/plays/data/graph-<scope>-<date>.json`
- `org/plays/data/graph-<scope>-<date>.html`

**Detail.** [`skills/playbooks/graph/SKILL.md`](../skills/playbooks/graph/SKILL.md).

## new-playbook (meta-skill)

**Question.** What's a new analytical question we want to ask repeatedly about this organization, and what's the smallest scaffold that lets us answer it?

**What it does.** Five-question interview that scaffolds a new playbook by forking the closest base playbook. The five questions:

1. What question does the playbook answer?
2. What is the anchor (full-org, commitment, unit, activity-set, stakeholder-set)?
3. What is the primitive (the unit of analysis), and what fields does it carry?
4. What proves a primitive's claim is grounded?
5. Which viewer pattern (tabular, 2D map, bundle bands, layered stack)?

The meta-skill validates the design (refuses one-shot questions, refuses ungrounded primitive fields), picks the closest base playbook, and scaffolds a new `skills/playbooks/<name>/` folder.

**Detail.** [`skills/playbooks/new-playbook/SKILL.md`](../skills/playbooks/new-playbook/SKILL.md).

## How to invoke

In Claude Desktop, after install:

> Run the value-map for [your anchor].
> What's the world-model of this organization?
> Which activities does AI affect most?
> Reshuffle the customer-onboarding pipeline.
> Show me the whole org as one graph.
> Create a new playbook that maps fragility in our commitments.

The agent reads the relevant `SKILL.md` via `org_skill_read`, walks the structure, calls `org_play_run` to execute the playbook scripts, and opens the resulting HTML in your browser.

## See also

- [`docs/architecture.md`](architecture.md) — why the system is built this way.
- [`docs/extending.md`](extending.md) — how to add a new playbook from scratch.
- [`skills/ROADMAP.md`](../skills/ROADMAP.md) — the order in which the five base playbooks compose.
- [`skills/CAPABILITIES.md`](../skills/CAPABILITIES.md) — the methodology behind world-model.
