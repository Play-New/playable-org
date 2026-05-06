# skills/ — roadmap

Four base playbooks plus one meta-skill. This file outlines what each does, what it consumes, what it produces, and the order they compose in.

Author names appear here because `skills/` is the productizable layer. They never appear inside `org/` artifacts (structure or plays).

## Status

| # | Playbook       | Kind                       | Source theory                       | Status  |
|---|----------------|----------------------------|-------------------------------------|---------|
| 1 | ai-exposure    | analysis                       | Anthropic Economic Index (v1, 2026)         | done    |
| 2 | value-map      | process mapping & redesign     | Simon Wardley                               | done    |
| 3 | reshuffle      | design                         | Sangeet Choudary                            | done    |
| 4 | world-model    | operating-model design         | Jack Dorsey + Roelof Botha (Block, 2026)    | done    |
| 5 | new-playbook       | meta — author your own skill   | (no source — composition of the other four) | done    |

The four together form a sequence: observe where AI presses (1) → map where each component sits in evolution (2) → propose new bundles around the constraints that remain (3) → recompose around capabilities and co-creators (4).

## Order of composition

**ai-exposure first.** It's the broadest survey: every activity scored against the Anthropic AEI dataset. Tells you which activities are AI-amenable in observed terms, before any normative interpretation.

**Then value-map.** Natural successor to ai-exposure. ai-exposure tells you which activities are AI-amenable; value-map tells you where each of those activities sits on the evolution curve (genesis / custom-built / product / commodity) and which climatic patterns will move them. Without that map, "redesign" lacks a structural footing.

**Then reshuffle.** Once you have a map and an exposure scoring, the unbundle / componentize / rebundle loop becomes operational rather than rhetorical. You can name the constraint that holds each bundle together (scarcity, risk, coordination) and propose what changes when AI dissolves one.

**Then world-model.** The capability frame overlays on top of activities once you've already done the work-decomposition implicit in reshuffle. Co-creator boundaries are a redesign of stakeholder commitments. The structure for that already exists in `commitments/`.

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

**What it does.** Reads the organization as the model in Dorsey/Botha's "From Hierarchy to Intelligence" (Block, March 2026): the org is the set of its capabilities (atomic primitives), a world model of its own operations + its customers, an intelligence layer that composes capabilities into solutions, and interfaces that deliver them. The skill maps the organization in these four parts and surfaces what's missing — particularly the "failure signals" that constitute the future roadmap.

**Inputs.**
- The full activity registry and unit registry.
- The stakeholder registry and the commitments connecting them.
- Optional: a reshuffle play (its componentized building blocks become a strong starting point for the capabilities layer).

**Outputs.**
- A frozen play in `org/plays/world-model-<scope>-<date>.md`.
- A JSON map in `org/plays/data/world-model-<scope>-<date>.json` with four sections: capabilities, world-model (company-side + customer-side), intelligence layer, interfaces. Plus a "failure signals" section for compositions the layer can't yet produce.
- An interactive HTML viewer following the project style charter, with click-to-detail on each capability and intelligence-layer composition.

**Key concepts borrowed.**
- Capabilities as atomic primitives that are hard to acquire (regulation, network effects, expertise) and have no UI of their own.
- World model: the organization's continuously-updated understanding of its own operations and of its users; the structure the intelligence layer queries.
- Intelligence layer: what composes capabilities into solutions for specific users at specific moments. Not "AI as productivity tool"; AI as the coordination mechanism that replaces middle-management information routing.
- The roadmap is what the intelligence layer fails to compose. User signal — not PM hypothesis — generates the backlog.
- Three roles emerge: ICs who build capabilities, DRIs who own outcomes, player-coaches who develop people. No permanent middle layer.

**Anti-hallucination discipline.**
- A "capability" must be reachable from at least three activities in different units OR be a regulated/credentialed primitive (notarial, legal, banking).
- The world-model section must cite which structure observations feed it — no hand-wave "we have data".
- Intelligence-layer compositions are conditional: each cites the capabilities composed and the user signal that would trigger composition.
- Failure signals must cite a specific user need that no current composition addresses.

**Open question.**
- Calibration of the four-part model to a non-profit foundation. Block's frame is built on transactional businesses where money is "the most honest signal in the world". For an organization, the equivalent honest signals are donation patterns, grant outcomes, testator pre-mortem behavior. The skill should adapt the customer-world-model section to whatever signals the structure actually has.

## 5 — new-playbook

**What it does.** Meta-skill. Lets a person interacting via mcp author a new analytical playbook for their organization, scaffolded from the patterns of the existing four. The output is a new `skills/playbooks/<name>/` folder with a SKILL.md, a build skeleton, an audit gate, and a viewer template — all populated with the user's question, scope, and signal source.

**Inputs.**
- A question the user wants to ask repeatedly about their organization (e.g., "where are the fragility points in our commitments?", "which sub-team is overcommitted?", "what would a partner-of-the-month playbook show?").
- The existing four skills as composable patterns (structure access, AEI overlay, audit gate structure, viewer template).
- Optionally: a reference to source material the user wants the new skill grounded in.

**Outputs.**
- A new skill folder under `skills/playbooks/`.
- A SKILL.md following the established template (output style, methodology, schema, workflow, audit contract).
- Stub `build.py`, `audit.py`, `viewer.py` with the structure-walking and AEI-attaching machinery already wired in, plus the question-specific shape.

**Key concepts.**
- Composition over template. The skill does not produce a fixed playbook; it composes one from the user's question and the existing primitives.
- Plays are the verb the user becomes capable of. Skills are the playbooks they accumulate.
- The structure, the mcp server, and the four base skills are the primitives the meta-skill composes.

**Anti-hallucination discipline.**
- Generated SKILL.md must be structure-grounded: every audit rule it proposes must trace to a structure constraint.
- Generated `build.py` reuses the existing primitives (structure readers, AEI attachment) — the meta-skill does not invent file formats or schemas.
- The output is reviewed before being committed to `skills/playbooks/`. The meta-skill produces a draft; the user accepts or rewrites.

**Open question.**
- How much scaffolding is automatic vs prompted. Auto-scaffolding risks producing a thin skeleton that the user has to fill anyway. Prompted scaffolding is closer to a guided conversation and may not feel meta-enough. Likely answer: a hybrid — auto-generate the structural files, prompt the user for the analytical decisions (audit gate, viewer columns, SKILL.md output-language section).

## What "done" looks like for each

| Playbook  | Test play (proposed) | Audit gate                                                      |
|-----------|----------------------|-----------------------------------------------------------------|
| value-map | example-pipeline | every component cites a signal; predictions tagged           |
| reshuffle | example-pipeline           | every constraint claim cites; engine/tool tag per AI use case |
| dorsey    | full org capability map   | every capability reachable from ≥3 activities                 |

## Constraints that apply to all three

- English skill content. Italian content lives in plays and structure, not in skills.
- Author names allowed in skill body; not allowed in any artifact under `org/`.
- Structure-first: every numerical or structural claim in a play traces to structure.
- One play, one date, frozen at creation.
- A standalone audit script that another agent can run before commit.
- Generic placeholders in skill examples — no organization-specific terms in the productizable layer.

## What this roadmap is not

It is not a commitment to build all four playbooks for every organization. The order proposed here works because each playbook builds on the priors of the previous one, but pragmatic deployments often pick two or three depending on the question the organization wants to answer first.
