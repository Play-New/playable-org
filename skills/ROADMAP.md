# skills/ — roadmap

Five base playbooks plus one meta-skill. This file outlines what each does, what it consumes, what it produces, and the order they compose in.

Author names appear here because `skills/` is the productizable layer. They never appear inside `org/` artifacts (structure or plays).

## Status

| # | Playbook       | Kind                                 | Source theory                                 | Status  |
|---|----------------|--------------------------------------|-----------------------------------------------|---------|
| 1 | ai-exposure    | analysis                             | Anthropic Economic Index (v1, 2026)           | done    |
| 2 | value-map      | process mapping & redesign           | Simon Wardley                                 | done    |
| 3 | reshuffle      | design                               | Sangeet Choudary                              | done    |
| 4 | world-model    | operating-model design               | Jack Dorsey + Roelof Botha (Block, 2026)      | done    |
| 5 | graph          | topology — read structure as itself  | (no source — mechanical render of the corpus) | done    |
| 6 | new-playbook   | meta — author your own skill         | (no source — composition of the other five)   | done    |

The first four read the structure through an analytical framework borrowed from outside (Anthropic AEI, Wardley, Choudary, Dorsey/Botha). The fifth (graph) reads the structure as the structure declares itself, with no analytical framework layered on top — it's the picture you can run earliest, after the first ingest, to see the shape of the corpus before any interpretation.

## Order of composition

**graph first (lightest).** Run after the first ingest. Walks every node and every relation declared in the structure and renders the whole org as one force-directed picture. No analytical framework, no AEI dependency. The output answers "what does the corpus look like as a connected thing" before anything reads it through a framework.

**ai-exposure next.** It's the broadest analytical survey: every activity scored against the Anthropic AEI dataset. Tells you which activities are AI-amenable in observed terms, before any normative interpretation.

**Then value-map.** Natural successor to ai-exposure. ai-exposure tells you which activities are AI-amenable; value-map tells you where each of those activities sits on the evolution curve (genesis / custom-built / product / commodity) and which climatic patterns will move them. Without that map, "redesign" lacks a structural footing.

**Then reshuffle.** Once you have a map and an exposure scoring, the unbundle / componentize / rebundle loop becomes operational rather than rhetorical. You can name the constraint that holds each bundle together (scarcity, risk, coordination) and propose what changes when AI dissolves one.

**Then world-model.** The capability framework overlays on top of activities once you've already done the work-decomposition implicit in reshuffle. Co-creator boundaries are a redesign of stakeholder commitments. The structure for that already exists in `commitments/`.

## 2 — value-map

**What it does.** Builds a value-chain map (evolution × visibility) for a chosen anchor (a stakeholder commitment, a Direzione, or a single area). Surfaces where each component sits on the evolution axis and what climatic patterns are likely to move it. Outputs a frozen map plus a doctrine gap-analysis.

**Inputs.**
- One anchor: pick a `commitments/<id>.md` (e.g., `example-pipeline`) or a `nodes/units/<id>.md`.
- The activities reachable from that anchor (via `requires` / `produces` / sub-team membership).
- Optional: the matching ai-exposure play, to overlay AI pressure on the map.

**Outputs.**
- `org/plays/value-map-<anchor>-<date>.md` — frozen play with:
  - User need at the top, value chain decomposed into components, each placed on the evolution axis.
  - Climatic-pattern checklist (everything-evolves-toward-commodity, co-evolution of practice, Peace/War/Wonder phase, punctuated equilibrium).
  - Doctrine gaps (which of the ~40 doctrines the org is missing or mis-applying for this anchor).
- `org/plays/data/value-map-<anchor>.svg` — the visible map.
- `org/plays/data/value-map-<anchor>.json` — structured map (components, positions, links) for re-rendering.

**Key concepts borrowed.**
- Five-factor model: purpose, landscape, climate, doctrine, leadership.
- Evolution stages: genesis / custom-built / product (+rental) / commodity (+utility).
- Climatic patterns as forces that move components rightward on the map.
- Doctrine as universal practices that don't depend on context.

**Anti-hallucination discipline.**
- Component placement must cite at least one observable signal: a source, an activity description, or an Anthropic AEI metric. No "feels like product".
- Climate predictions are flagged as predictions, not observations.
- Doctrine gaps cite the specific commitment or activity that violates the doctrine.

**Open question for tomorrow.**
- Manual placement (agent-aided) vs. assisted placement from a feature vector? Manual is honest; assisted risks the same confirmation-bias trap that pushed us off manual mapping in ai-exposure. Likely answer: manual, but with a checklist that forces evidence per component.

## 3 — reshuffle

**What it does.** Takes a slice of org and asks: which constraints hold this bundle together, which of those constraints AI dissolves, what the new bundle looks like. Outputs three artifacts: a constraint inventory, a reshuffle proposal, and a risk-of-reshuffle score.

**Inputs.**
- A slice of org: a Direzione, an area, or a value chain anchored on a commitment.
- The matching ai-exposure play (gives the AI pressure per activity).
- Optional: the matching value-map play (gives the evolution stage per component).

**Outputs.**
- `org/plays/reshuffle-<slice>-<date>.md` with:
  - Constraint inventory: each activity tagged with the constraint type that holds it inside the current bundle (scarcity-based, risk-based, coordination-based, regulatory).
  - Unbundle table: which activities AI separates from the bundle, and why (which constraint is dissolving).
  - Componentize table: which separated activities become reusable components (and at what evolution stage they'd land — links back to value-map).
  - Rebundle proposals: candidate new bundles, each named, each anchored to a remaining constraint.
- A "tool vs. engine" tag per AI use case in the slice (Choudary's distinction): tool = bundle stays the same, faster; engine = bundle reshuffles.

**Key concepts borrowed.**
- Unbundle / componentize / rebundle as the three moves (Choudary, "Reshuffle").
- Three constraint types: scarcity, risk, coordination — plus regulatory as a fourth often surfaced in nonprofit/healthcare context.
- AI as engine vs. AI as tool: only engines reshuffle.
- The autonomy-coordination trade-off (Bezos two-pizza): rebundles trade autonomy for coordination depending on which constraint is binding.

**Anti-hallucination discipline.**
- Every constraint claim cites a source or an activity body — not a generic claim about the sector.
- "AI dissolves this constraint" requires citing the specific Anthropic-AEI signal or a recent capability demonstration.
- Rebundle proposals are explicitly framed as proposals; the play does not overwrite structure.

**Good test cases for any organization.**
- A multi-division pipeline that touches finance, legal, and a customer-facing function (the bundle is held by coordination cost; AI typically changes that first).
- A matrix unit that has visibly reorganized in the recent past (reshuffle in progress, dynamics already exposed in past charts).

## 4 — world-model

**What it does.** Reads the organization through the loop in Dorsey/Botha's *From Hierarchy to Intelligence* (Block, March 2026). Today the org has interfaces, capabilities, and a world model. Interfaces deliver outputs but don't capture signal. Capabilities are crafts embedded in named people. The world model is implicit, fragmented across heads and files. The move is to insert intelligence (typically AI-mediated) that transforms the three: interfaces become signal collection points; capabilities become invocable systems with the person staying as DRI; the world model auto-updates from the signals. The skill maps where the org is along this move and surfaces the roadmap as the subset of captured signals that no current composition can fulfil.

**Inputs.**
- The full activity registry and unit registry.
- The stakeholder registry and the commitments connecting them.
- Optional: a reshuffle play (its componentized building blocks become a strong starting point for the capabilities layer).

**Outputs.**
- A frozen play in `org/plays/world-model-<scope>-<date>.md`.
- A JSON map in `org/plays/data/world-model-<scope>-<date>.json` with three layer sections: interfaces, capabilities, and world-model (which now includes operational picture, per-caller picture, and captured-signals log). Plus a roadmap section that holds the queryable subset of captured signals with no current composition.
- An interactive HTML viewer rendering the three layers + the runtime as a connective annotation + the loop as overlay. Click-to-detail on each card via popover. Editorial-column layout per [SKILL.md](playbooks/world-model/SKILL.md) §8.

**Key concepts borrowed (from the source).**
- Capabilities as atomic primitives that are hard to acquire (regulation, network effects, expertise) and have no UI of their own.
- World model split: company side (replaces information that flowed through layers of management) + customer side (per-caller, transaction-derived).
- Intelligence layer: composes capabilities into solutions for specific callers at specific moments. AI in this layer is the coordination mechanism that replaces middle-management information routing.
- The roadmap is what the intelligence layer fails to compose. Captured signal generates the backlog, not a PM hypothesis.
- Three roles emerge: ICs who build capabilities, DRIs who own outcomes, player-coaches who develop people. No permanent middle layer.

**Operational extensions (ours, not in source).** The five-property test, four-question pragmatic test, three-actors rule, users-and-contributors framing, seven-step transition sequence, and the five-criteria wrapper for making a capability invocable. Developed for this template to apply the source's frame to organizations that aren't Block. Marked as such in [CAPABILITIES.md](CAPABILITIES.md).

**Anti-hallucination discipline.**
- A "capability" must be reachable from at least three activities in different units OR be a regulated/credentialed primitive (notarial, legal, banking).
- The world-model section must cite where each piece of memory lives today (a structure file, a system, a person's head). No hand-wave "we have data".
- Intelligence-layer compositions are conditional: each cites the capabilities chained and the captured signal that would trigger composition.
- Each roadmap entry must name a missing capability in verb-object form and cite a concrete observation that says the request arises.

**Open question.**
- Calibration of the loop to a non-profit foundation. The source's framework leans on transactional density (Block has millions of transactions/day). For an organization with thinner signal, the captured-signals log is sparser; the customer-side world model has to be built from non-transactional honest signals (donation history, grant outcomes, testator pre-mortem behaviour). The skill adapts the layer to the signal density the structure already has.

## 5 — graph

**What it does.** Walks the whole `org/` corpus and renders it as a single force-directed picture: every node (units, activities, people, stakeholders, commitments, sources, identity, financial summaries) and every typed relation declared in frontmatter or in body links. The lightest of the playbooks — no AEI dependency, no interpretive theory, just the structure as the structure is written.

**Inputs.**
- The whole `org/` directory.
- (Optional, reserved for future) a `--scope <unit-id>` flag to slice to one Direzione's neighbourhood.

**Outputs.**
- `org/plays/data/graph-<scope>-<date>.json` — typed nodes + edges + topology summary (degree-sorted top connected, isolates, by-kind counts).
- `org/plays/data/graph-<scope>-<date>.html` — interactive force-directed viewer (App-pure: full-bleed canvas, floating dateline + Analysis CTA + kinds ribbon, no editorial column). Click a node → Inspect card slides in from the right with outgoing + incoming dependencies grouped by verb. The viewer renders the *operational* layer of the graph (six load-bearing kinds); corpus / declarative kinds and body-markdown link edges stay in the JSON for other tools but are stripped from the picture. See `skills/playbooks/graph/SKILL.md` §2 for the full contract.

**Key concepts.**
- Topology is not interpretation. The play surfaces what is connected; whether a region of the structure being thin is a problem or a deliberate choice is a question the leader answers — the play poses it.
- Conditional voice on thin regions. "The structure has not been written down here yet", not "the org is missing X".
- Mechanically built. Build does not invent nodes or edges. The audit refuses unresolved endpoints; the autoresearch gate refuses graph-theory jargon and other-playbook framework leakage.

**Anti-hallucination discipline.**
- Every edge endpoint must resolve to a real node (audit gate).
- Decisions cite a node id or a relative path under `org/`; the autoresearch's `audit_grounded` check verifies any `node_ids` referenced.
- Plain-language gate forbids `node degree`, `degree centrality`, `betweenness`, `clustering coefficient`, `hub`, `subgraph` in user-visible prose, plus the framework primitives of the other four playbooks (capability stack, world model, value chain, bundle, moat).

**Open question.**
- Per-unit scoping. The current build walks the whole org. A `--scope <unit-id>` mode that produces a subgraph centred on one Direzione (its activities, the stakeholders it touches, the sources its activities cite, the people in it) would be a useful narrower read. Reserved as a future flag — the topology of the whole graph is the more useful first pass.

## 6 — new-playbook

**What it does.** Meta-skill. Lets a person interacting via mcp author a new analytical playbook for their organization, scaffolded from the patterns of the existing five. The output is a new `skills/playbooks/<name>/` folder with a SKILL.md, a build skeleton, an audit gate, and a viewer template — all populated with the user's question, scope, and signal source.

**Inputs.**
- A question the user wants to ask repeatedly about their organization (e.g., "where are the fragility points in our commitments?", "which sub-team is overcommitted?", "what would a partner-of-the-month playbook show?").
- The existing five skills as composable patterns (structure access, AEI overlay, audit gate structure, viewer template, force-directed topology).
- Optionally: a reference to source material the user wants the new skill grounded in.

**Outputs.**
- A new skill folder under `skills/playbooks/`.
- A SKILL.md following the established template (output style, methodology, schema, workflow, audit contract).
- Stub `build.py`, `audit.py`, `viewer.py` with the structure-walking and AEI-attaching machinery already wired in, plus the question-specific shape.

**Key concepts.**
- Composition over template. The skill does not produce a fixed playbook; it composes one from the user's question and the existing primitives.
- Plays are the verb the user becomes capable of. Skills are the playbooks they accumulate.
- The structure, the mcp server, and the five base skills are the primitives the meta-skill composes.

**Anti-hallucination discipline.**
- Generated SKILL.md must be structure-grounded: every audit rule it proposes must trace to a structure constraint.
- Generated `build.py` reuses the existing primitives (structure readers, AEI attachment) — the meta-skill does not invent file formats or schemas.
- The output is reviewed before being committed to `skills/playbooks/`. The meta-skill produces a draft; the user accepts or rewrites.

**Open question.**
- How much scaffolding is automatic vs prompted. Auto-scaffolding risks producing a thin skeleton that the user has to fill anyway. Prompted scaffolding is closer to a guided conversation and may not feel meta-enough. Likely answer: a hybrid — auto-generate the structural files, prompt the user for the analytical decisions (audit gate, viewer columns, SKILL.md output-language section).

## What "done" looks like for each

| Playbook    | Test play (proposed)              | Audit gate                                                              |
|-------------|-----------------------------------|-------------------------------------------------------------------------|
| value-map   | example-pipeline                  | every component cites a signal; predictions tagged                      |
| reshuffle   | example-pipeline                  | every constraint claim cites; engine/tool tag per AI use case           |
| world-model | full org capability map           | every capability reachable from ≥3 activities                           |
| graph       | whole-org topology                | every edge endpoint resolves; ≥1 node of each required kind; ≥3 cited decisions |

## Constraints that apply to all three

- English skill content. Italian content lives in plays and structure, not in skills.
- Author names allowed in skill body; not allowed in any artifact under `org/`.
- Structure-first: every numerical or structural claim in a play traces to structure.
- One play, one date, frozen at creation.
- A standalone audit script that another agent can run before commit.
- Generic placeholders in skill examples — no organization-specific terms in the productizable layer.

## What this roadmap is not

It is not a commitment to build all five playbooks for every organization. The order proposed here works because each playbook builds on the priors of the previous one, but pragmatic deployments often pick two or three depending on the question the organization wants to answer first.

## Recent additions (May 2026)

Tracked here so a fork merging upstream sees what changed:

- **`graph` viewer redesigned to App-pure (May 2026).** Full-bleed canvas, floating editorial chrome (dateline top-left, `Analysis →` outline button top-right, kinds ribbon bottom-left, zoom + Reset focus bottom-right), floating Inspect card sliding in from the right on focus, *Carta sbiadita* paper palette (slate / sage / ink / lilac / terracotta / sand). Mobile-first: Pointer Events for mouse + touch through one path, two-finger pinch zoom, safe-area insets for the iPhone notch. Replaces the editorial-column shell that the other four playbooks still use. Locked by 28 regression checks in `mcp-server/test-e2e.py`. The other four playbooks (`ai-exposure`, `value-map`, `reshuffle`, `world-model`) still use the editorial-column chrome — propagation to them is a separate decision.
- **Conditional voice rule for emerging items.** Anything `is_new` (component / stakeholder / piece-to-build / candidate role) is written with `if / would / could / depends on`, never `when / will / makes`. Lives in `STYLE.md` with examples.
- **Plain-language jargon avoid-list.** Framework primitive names are fine as labels; paraphrased into prose they become jargon. Avoid-list grows in `STYLE.md`: moat, commodity (in body), commoditize, judgment density, capability stack, coordination tax, piece to build, thin (metaphor), see-saw, flywheel, engine candidate, rebundle, production-tier, rich subset, O\*NET, AEI, embedding, cosine similarity, top-K, p25/p75, JSON field-name leaks (evolution_target, ai_effect, ai_autonomy_mean).
- **Autoresearch as a 5-dimension gate**, four deterministic + one LLM judge. Per-playbook `autoresearch.py` with shared `skills/autoresearch_lib.py`. Each playbook tunes its own jargon blacklist + judge rubric. Surfaced as a property of the structure itself via the `org_autoresearch_run` mcp tool — agent can score a play right after rendering it without shelling out.
- **`init` Path B (interview-first).** When the user has no founding documents, a structured ten-question interview becomes the founding source. The transcript is saved verbatim and cited by every node it generates. Combines with Path A (documents-first) for partial-document orgs.
- **`org_autoresearch_run` mcp tool.** 13 tools total now (was 12). Same surface as `org_lint_run`.
- **DRI as a distinct role** in `CAPABILITIES.md`. Three roles, not interchangeable: DRI (single accountable person, throat-to-choke), IC (executes), player-coach (hybrid, on capabilities large enough to need both building and people development).
- **Activity density layer** documented in `org/AGENTS.md`. Optional fields (trigger, quality_gates, decision_criteria, output_format, fallback, handoff) that turn an activity into something a Claude skill can be compiled from. Filled by interviewing the performer; the transcript becomes a source citation.
- **`graph` playbook (May 2026).** Reads the structure as the operational dependency layer: the six load-bearing kinds (unit, activity, person, role, stakeholder, commitment) and the typed relations between them, rendered as one force-directed picture. The lightest of the bundled playbooks — no AEI dependency, no interpretive theory layered on top, run after the first ingest. Five playbooks total now (was four). Vanilla-JS force simulation on HTML5 canvas, no D3 dependency.

## Future (deferred)

- **`compile-agent` skill** — given a scope (org / unit / person), emit a `CLAUDE.md` instruction file for an agent that knows that scope. Level 1 of agentic deployment; the data is mostly already in `org/`.
- **`interview-activity` skill** — the Q&A flow that fills the activity density layer for a specific activity. Level 2 enabler. Once one activity has all six density fields, a Claude skill can be generated from it.
- **`context-bundle` playbook** — exporting a knowledge graph + capability×role matrix + Gherkin scenarios as a deployable bundle for agentic pipelines. Cicero's "context bundling" thread (Through The Boundary, May 2026). Level 3 of agentic deployment.
