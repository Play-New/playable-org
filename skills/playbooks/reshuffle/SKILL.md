---
name: reshuffle
description: "Assess where coordination tax is paid in a slice of an organization and whether AI dissolves it (engine) or just speeds it up (tool). Output: a frozen play with the bundle's current constraints, tool/engine classification per AI use, autonomy-coordination position, and rebundle candidates emerging when constraints shift."
---

# Playbook: reshuffle

## How this playbook is run (read this first)

This playbook **must** produce a persistent file artefact under `org/plays/data/`, not an in-chat widget.

**Required tooling**: `org_play_run` (mcp tool). Two calls per run:

1. `org_play_run(playbook="reshuffle", mode="build", anchor=<slice-id>, kind="commitment"|"unit")` → returns the activity inventory + AEI evidence from `build.py`. Tag constraints, classify tool/engine, propose rebundles per §3-§5.
2. `org_play_run(playbook="reshuffle", mode="render", json_content=<filled JSON>)` → writes JSON, runs `audit.py`, runs `viewer.py`, returns the HTML path plus audit summary.

**Do not** use Claude Desktop's inline `visualize` / `show_widget` / artifact features. They are ephemeral, bypass the audit gate, and don't use the bundled design system. The HTML returned by `org_play_run` mode=render is the canonical visualization.

**Do not** hand-write a markdown play file under `plays/`. The JSON + HTML pair under `plays/data/` is the play.

If `org_play_run` errors, report verbatim and stop. Do not fall back to an in-chat widget.

**How to present the result — strict protocol**:

1. As soon as render returns `status: "ok"`, call `org_open` immediately with `artefacts.html` (relative path). Opens in default browser.
2. Paste the response `presentation_markdown` field **verbatim** in your reply. It is already a `[text](file://...)` Markdown link; do not wrap, quote, or rephrase.
3. Add one short sentence of context (e.g. "13 attività classificate per vincolo, 4 motori AI individuati, 3 candidati di riconfigurazione, audit pass").
4. Do NOT inline-render any custom widget.

For a slice of the organization (a commitment, an area, a value chain), produce a structured assessment of:

## Output style

All consumer-facing text produced by this skill (play body, viewer copy, modals, interpretive narratives) must follow the project style charter in [skills/STYLE.md](../../STYLE.md). The charter does not govern this SKILL.md, schema fields, or code — it governs what the reader sees.

1. **Where the coordination tax is paid**: across which team boundaries does work currently get stuck (encoding, organizing, or deploying knowledge)?
2. **Which constraints hold the current bundle**: scarcity-based (rare expertise/resource), risk-based (compliance, certainty), or coordination-based (handover cost between teams)?
3. **Tool or engine classification** per AI use case: does this AI use leave the bundle intact and just accelerate it (tool) or does it dissolve a binding constraint and force the bundle to reshuffle (engine)?
4. **Autonomy-coordination position**: is the current bundle on the see-saw (zero-sum trade-off between team autonomy and cross-team alignment) or in flywheel mode (mutually reinforcing)?
5. **Rebundle candidates**: new aggregations that emerge when AI dissolves the binding constraint.

The deliverable is a frozen `play` in `org/plays/reshuffle-<slice>-<date>.md`, with companion JSON and an interactive HTML viewer.

## Output language — mandatory

The intended reader of the deliverables is **not** a strategy consultant. It is an executive or area lead with no prior knowledge of the source framework, of organizational theory, or of the dataset. Every word in the visible output (the HTML viewer, the play body, the modal copy) must be readable by such a reader on first pass. The schema fields and the variable names in code can stay technical — those are not visible.

When authoring `ai_evidence`, `constraint_evidence` claims, `bundle_state.coordination_paradox_risk`, `bundle_state.mode_evidence`, rebundle `description` / `what_changes` / `risk_of_rebundle`, and the play body, **do not use** the framework terms below. Use the plain Italian equivalent listed in the right column.

| Internal / framework term | Output language (Italian) |
|---|---|
| bundle | processo |
| rebundle | riconfigurazione del processo |
| tool (AI as) | acceleratore (cambia velocità non struttura) |
| engine (AI as) | infrastruttura di coordinamento (cambia struttura) |
| coordination tax | costo di tenere allineati team diversi |
| knowledge-management cost (encoding/organizing/deploying) | scrivere e codificare conoscenza / organizzare e ritrovare informazione / usare la conoscenza al momento delle decisioni |
| see-saw mode | modello tradizionale (o autonomia o allineamento) |
| flywheel mode | modello AI-mediato (autonomia e allineamento insieme) |
| coordination paradox | trappola da evitare: dispiegare AI come acceleratore in alcuni reparti senza allineare gli altri crea asimmetrie di velocità che peggiorano il problema di coordinamento |
| AEI | dato osservativo Anthropic / campione di conversazioni Claude |
| O*NET task | mansione vicina nel catalogo americano dei mestieri |
| autonomy mean | autonomia (su scala 1 = sola assistenza, 5 = lavoro autonomo) |

JSON field values that are **closed-set codes** (`primary_constraint`, `km_cost_dominant`, `ai_classification`, `autonomy_coordination_mode`) keep their internal codes (e.g., `"engine"`, `"see-saw"`) — the renderer translates them at display time. But agent-authored free-text fields (claims, descriptions, narratives) must use the plain Italian above.

A small acid test before saving: read the play out loud as if explaining the analysis to someone who doesn't know the organization and has never heard of any organizational framework. If a sentence requires a glossary lookup, rewrite it.

## Three constraint types

The skill recognizes **only three** constraint types. Regulatory constraints fold into either `risk` (compliance risk) or `scarcity` (a regulated credential is a scarce resource); they are not a separate type. This stays faithful to the source frame.

| Constraint | What holds the bundle | Examples in a nonprofit context |
|---|---|---|
| **scarcity** | A rare resource/expertise/credential — only specific roles or providers can do it | A sub-team with deep institutional knowledge; a regulated profession (notary, lawyer); a strategic relationship |
| **risk** | The cost of being wrong (compliance failure, reputational damage, financial loss) requires layered verification and human accountability | A multi-step approval (governance body → legal → finance); notarial certainty; an audit trail required by an external authority |
| **coordination** | The cost of getting work across teams is high — encoding, organizing, deploying knowledge requires meetings, documents, handovers | Cross-Direzione handover of a fascicolo; a matrix unit with people borrowed from many teams; a process that requires many people to share a mental model |

Each activity in the slice is tagged with **one primary constraint** (the one whose removal would change the bundle the most). Citations are required from the structure (statute, code of ethics, regulation, role-description, commitment terms).

## Tool vs. engine — the primary diagnostic

This is the opening question of every reshuffle play. For each AI use case identified in the slice (typically grounded in the AEI matches from `ai-exposure`), the agent must classify:

| Classification | Definition | What it implies |
|---|---|---|
| **tool** | AI accelerates a step inside the existing bundle. The bundle's structure is unchanged. The competitive/operational basis is unchanged. | Local efficiency gain. Watch for the **coordination paradox**: tool-only deployment can *increase* total coordination tax if it creates asymmetric capabilities across teams. |
| **engine** | AI dissolves a binding constraint — most often the coordination constraint (by making knowledge shared, structured, deployable in real time). The bundle reshuffles around the remaining constraints. | The basis of how the slice operates changes. The skill's rebundle proposals apply only here. |

**Tools are not bad**. Many AI uses are tools, and that is honest. But only **engines** justify a rebundle proposal. Confusing the two produces hype-driven reorgs.

The classification must cite evidence:
- For *engine*: cite the AEI match (rich autonomy data on the matched O*NET task) AND name which of the three knowledge-management activities it changes (encoding, organizing, deploying).
- For *tool*: cite either AEI evidence of incremental efficiency, or note "no engine evidence available — defaulting to tool".

## The three knowledge-management costs

Coordination tax accumulates in three distinct activities (Ch 6 of the source). The skill maps each of them in the slice:

| Activity | Where the cost shows up | What dissolves it |
|---|---|---|
| **encoding** | Knowledge workers write documentation, capture lessons, package methods *alongside* their main work. Opportunity cost of pulling experts away from value work. | AI converts unstructured work artefacts (calls, drafts, voice notes) into structured documentation automatically. |
| **organizing** | Clerical/admin staff or knowledge-management tools categorize and synthesize. Scattered documents, lost emails, "where is that file". | AI queries knowledge across silos, surfaces the right thing at the right time without manual retrieval. |
| **deploying** | Meetings, chats, emails to recreate lost context before a decision. People asking each other "what's the latest on X". | AI delivers contextual answers in workflow; agentic execution closes loops automatically. |

For each activity in the slice, the agent identifies which of the three is the dominant tax (citing structure or AEI evidence). This is the foundation for tool/engine classification.

## The autonomy-coordination dimension

The current bundle's position on the autonomy-coordination plane is part of the assessment (Ch 6 of the source: "From see-saws to flywheels"):

- **See-saw mode** (zero-sum): more team autonomy ↔ less cross-team alignment. The org buys one with the other.
- **Flywheel mode** (mutually reinforcing): better coordination *enables* greater autonomy because shared organizational knowledge is the AI-mediated structure.

The play declares the current mode and proposes which mode the rebundle would operate in. A rebundle that stays in see-saw mode is unlikely to be transformative; a rebundle that moves to flywheel mode is more interesting but harder to validate.

## Workflow

### 0. Canonical invocation via mcp (preferred)

When the bundled mcp server is available, launch this playbook via `org_play_run`:

1. Call `org_play_run` with `playbook="reshuffle"`, `mode="build"`, `anchor=<slice id>`, `kind="commitment"|"unit"`. The tool runs `build.py` and returns the activity inventory + AEI evidence inline.
2. Read the skeleton; for every activity tag the binding constraint type (scarcity / risk / coordination), classify each AI use as tool or engine, and propose any rebundle candidates per §3-§5 below. Every claim cites structure or an AEI match.
3. Call `org_play_run` again with `mode="render"` and `json_content=<filled JSON>`. The tool writes to `plays/data/`, runs `audit.py`, runs `viewer.py`, returns artefact paths and audit summary.
4. Append a log line via `org_log_append`.

Do **not** hand-write a markdown play under `plays/` for this flow — the JSON + HTML in `plays/data/` is the artefact.

If `org_play_run` is not available (older mcp build), fall back to the manual steps below.

### 1. Define the slice

Pick one:
- A `commitment` (typical, recommended) — the bundle is the set of activities that fulfill the commitment
- An `area` (`unit` of level=area) — the bundle is the area's value chain
- A `Direzione` (`unit` of level=division) — the bundle is the cross-area collaboration

### 2. Build the slice skeleton

```bash
python3 skills/playbooks/reshuffle/build.py \
  --slice <id> \
  --kind commitment|unit \
  --org-dir org \
  [--ai-exposure-matches <path-to-matches.json>] \
  [--value-map <path-to-value-map.json>] \
  --out <slice-skeleton.json>
```

The builder:
1. Walks structure edges to enumerate activities and units in scope (same logic as `value-map/build.py` — division expansion, stakeholder differentiation).
2. For each activity, attaches `_aei` (top-K AEI matches) and `_value_map_position` if `--value-map` is provided (the evolution + visibility from a prior value-map play).
3. Extracts candidate constraint signals from structure citations — `regulation`, `civil code`, `board resolution`, role-description cross-references, sub-team membership crossing division boundaries.

The skeleton is deterministic. The agent does the constraint-tagging and tool/engine classification in step 3.

### 3. Classify each activity

> **Reminder**: when authoring the `evidence` claims below, follow the [Output language](#output-language--mandatory) policy. Use plain Italian, not framework terms. The reader does not know what "engine" or "encoding" mean.

For each activity, the agent records:

- **`primary_constraint`**: one of `scarcity` | `risk` | `coordination` — citing a structure document or AEI signal
- **`km_cost_dominant`**: one of `encoding` | `organizing` | `deploying` | `none` — which of the three knowledge-management activities is the dominant tax for this activity
- **`ai_classification`**: one of `tool` | `engine` | `not-applicable`
  - `engine` is allowed only when AEI shows rich autonomy on the matched task AND the AI use changes the dominant `km_cost`
  - `tool` is the default when AI improves the activity without changing its position in the bundle
  - `not-applicable` when no AEI evidence at all
- **`evidence`**: list of citations supporting the above

### 4. Diagnose the bundle

The agent writes:
- The slice's current **dominant constraint distribution** (e.g., "12 activities: 7 coordination-bound, 3 risk-bound, 2 scarcity-bound")
- The **autonomy-coordination mode** the bundle currently operates in (see-saw or flywheel) with cited reasoning
- The **set of engine candidates** — AI uses tagged `engine` — and which constraint each of them dissolves
- The **coordination-paradox risk** — if tools are deployed in isolated functions, does asymmetric capability create new bottlenecks? Cite which functions.

### 5. Propose direction options (the unbundle / componentize / rebundle moves)

The source frame describes three moves, in order: **unbundle** (which activities AI separates from the current process), **componentize** (which separated activities become reusable building blocks), **rebundle** (how they recombine into one or more alternative processes). The skill makes the third move explicit and surfaces the first two implicitly through the engine_candidates list.

**Default: produce 2 to 3 alternative rebundle options, ranged by depth of change.** A single option is rarely enough — the value of this analysis is letting the organization compare directions, not pushing one. The expected pattern is:

- **Conservative option**: AI deployed as accelerator across activities, structure unchanged. The bundle keeps its current see-saw mode. Low risk, low transformation.
- **Structural option**: one or more engines deployed; the bundle reshuffles around the strongest engine. The bundle may move from see-saw to flywheel mode. Medium risk, real change.
- **Radical option** (when defensible): the engines compose into a new value proposition that crosses out of the current bundle's boundaries. High risk, high transformation. Include only when the structure genuinely supports it — do not invent radical options for symmetry.

A rebundle option exists only when at least one `engine` AI use dissolves a binding constraint (the conservative option is an exception: it explicitly does *not* deploy engines, but is included as the baseline against which the other options are compared, so its `enabled_by_engine` field references the engine that *would* be activated if the option were taken further).

Each option records:

- **Name** of the new bundle (e.g., "Pre-screening pre-mortem unificato")
- **Activities** that compose it (referenced by id)
- **The binding constraint that remains** after the engine dissolves the dissolved one (a rebundle is always anchored to a remaining constraint)
- **Autonomy-coordination position** of the rebundle (see-saw or flywheel)
- **What would change** in the autonomy-coordination tradeoff
- **Risk-of-rebundle**: high/medium/low — how reversible is the move, what fails if the engine doesn't deliver as expected

Rebundle candidates are explicitly **proposals**, not plans. They do not modify structure.

### 6. Visualize

```bash
python3 skills/playbooks/reshuffle/viewer.py \
  --map <slice-map.json> \
  --html <slice.html> \
  [--decisions <decisions.json>]
```

The HTML is the **primary consumer artefact** — a self-contained interactive document the leader opens in a browser. **This shape is frozen**; the canonical Outline & Co. play under `mcp-server/test-fixtures/sample-org/plays/data/reshuffle-outline-2026-05-07.html` is the reference render. Page structure, in order, with all blocks living in a centered 820px column inside the 1240px container so nothing escapes the editorial grid:

1. **Header** (eyebrow `reshuffle` + h1 process title + lead description + anchor-id mono line).
2. **Intro** — three short editorial paragraphs framing what the page does, the two things AI can do (accelerator vs shared-knowledge infrastructure), the trap to avoid as a pull-quote, and the three things that hold each activity in place (rare resource / cost of being wrong / cost of keeping teams aligned).
3. **Distribution panel**: a hairline-topped block titled "The process, grouped by what holds each activity in place". Stacked horizontal bar showing the split across the three constraint types, plus the per-constraint legend with one-line plain-language explanations. Below, a `bundle-state` block with how the process runs today (current_mode), where the read comes from (mode_evidence with citations), and the trap to avoid (coordination_paradox_risk) — all in plain English, no framework jargon.
4. **Activity ledger**: a hairline-topped block titled "Each activity, one by one". Activities grouped by primary constraint, each group with its swatch + heading + count + plain-language explanation, then a grid of activity cards. Each card is full-bordered hairline by default; activities classified as `engine` get a coral border accent so the leader's eye picks out where AI changes structure. Card content: activity label + "AI is accelerator / infrastructure / not relevant" tag.
5. **Engine candidates**: a hairline-topped block titled "Where AI would change structure, not just speed (N)". Each candidate is a coral-bordered card naming the activity + which constraint dissolves when AI is deployed there as shared-knowledge infrastructure.
6. **Direction options**: a hairline-topped block titled "Direction options (N)". Each option is a hairline-bordered card naming the rebundle + what stays binding + how many activities are recombined.
7. **Decisions section** "How to read this map": h2 + lead + each decision rendered as `.question` + `.answer` + `.source` citation. The load-bearing interpretive surface — the maps shows the structure, this section says which engine to deploy when and which direction option fits next year.

**Visual code (frozen, matches value-map and world-model)**:

- **Shape = kind**: cards (rounded-corner full hairline border) for everything content-rich. All clickable items use the same shape and the same hover signal (border darkens to `--fg`).
- **Colour = state / role**: hairline border = standard / not-engine; coral border = `engine` (where AI changes structure, not just speed). The shape never changes when an activity is `engine`-classified — only the border colour does.
- **No left-rule cards**. Every card has a full hairline border.

**Click on any card** opens a small floating popover (never a modal) next to the clicked element. The popover contains:

- Eyebrow with the kind: `activity in this process` (default) or `where AI changes structure` (engine, in coral).
- The activity label as h3.
- A description.
- "What holds it in place" (constraint label + plain-language explanation + cited evidence).
- "Where the main cost sits" (knowledge-management cost dominant: writing things down / organizing and finding / using at decision time).
- "What AI does here" (accelerator / shared-knowledge infrastructure / not relevant — plain language, no framework jargon).
- "Where the analysis comes from" (data block: closest matched tasks in the public catalog, similarity, observed autonomy /5, sample size; sample under 100 flagged).

For direction-option cards, the popover instead renders: option name + description + activities recombined + what makes it possible (the engine that dissolves the constraint) + what stays binding even after + how the new process would run (old rule vs new rule) + what changes for people in the process + how risky the move is.

Esc / click outside / close button dismisses. Position relative to click target, viewport-edge clamped.

**Plain-language discipline (frozen)**. The closed-set codes in the JSON (`see-saw`, `flywheel`, `engine`, `tool`, `scarcity`, `risk`, `coordination`) stay as enums — the renderer translates them at display time. **In every user-visible string**, no framework vocabulary leaks: `see-saw` becomes "old rule: more autonomy means less alignment"; `flywheel` becomes "new rule: more autonomy and more alignment together"; `engine` becomes "shared-knowledge infrastructure"; `tool` becomes "accelerator"; `coordination paradox` becomes a plain explanation. The autoresearch jargon-list dimension catches leakage in the decisions text; the same discipline applies editorially to the constraint_evidence, ai_evidence, mode_evidence, and rebundle description / what_changes / risk_of_rebundle fields.

**`--decisions <list.json>`** merges a JSON list of `{question, answer, source}` into the map's `decisions[]` field before rendering. **Required** for a shippable play — autoresearch fails without it.

### 7. Audit (anti-hallucination gate, mandatory)

```bash
python3 skills/playbooks/reshuffle/audit.py \
  --map <slice-map.json> \
  --org-dir org
```

The audit verifies:

1. Every activity has a `primary_constraint` from the closed set {scarcity, risk, coordination} with at least one cited source.
2. Every `engine` classification has rich AEI evidence (autonomy data on the matched task) AND specifies which `km_cost` it changes.
3. Every rebundle candidate cites the engine that enables it, and names the remaining binding constraint.
4. Every autonomy-coordination claim cites a structure document (e.g., commitment terms, sub-team membership crossing Direzione boundaries).
5. The bundle distribution sums correctly: every activity in the slice has exactly one `primary_constraint`.
6. Coordination paradox is checked: if any function has `tool` classification but no `engine`, the play must include a paragraph acknowledging the risk.

Exit code: 0 = pass, 1 = fail. Same contract as `audit.py` of the other skills.

### 8. Write the play

> **Reminder**: this is consumer-facing output. Apply the [Output language](#output-language--mandatory) policy strictly. The play must read clearly to someone who knows neither the organization nor any organizational framework. Run the acid test before saving.

In `org/plays/reshuffle-<slice>-<date>.md`:

```yaml
---
id: reshuffle-<slice>-<date>
type: play
playbook: reshuffle
target: <slice-id>
dated: <YYYY-MM-DD>
frozen: true
sources: [<commitment file or unit file>, <activity files>, <structure evidence cited>]
references:
  - builder: skills/playbooks/reshuffle/build.py
  - viewer: skills/playbooks/reshuffle/viewer.py
  - audit: skills/playbooks/reshuffle/audit.py
  - map_json: org/plays/data/reshuffle-<slice>-<date>.json
  - map_html: org/plays/data/reshuffle-<slice>-<date>.html
  - ai_exposure_play: org/plays/ai-exposure-<scope>-<date>.md  # if applicable
  - value_map_play: org/plays/value-map-<anchor>-<date>.md     # if applicable
---
```

Body sections (in order):

1. **Slice and current bundle** (one paragraph + cited dominant constraint distribution)
2. **Where the coordination tax is paid** (the 3-cost map: encoding, organizing, deploying)
3. **Tool/engine ledger** (per AI use case)
4. **The autonomy-coordination position** of the current bundle (with cited reasoning)
5. **Engine candidates** — which AI uses dissolve which constraints
6. **Rebundle candidates** (1-3, each with the structure from §5)
7. **Coordination-paradox check** — if tools are present without engines, what risk
8. **Operational consequences** — what to do, what not to do
9. **Method limits**
10. **Cross-references**

### 9. Lint + log

`python3 lint.py` must pass. `org_log_append` with a one-line summary.

## What this skill does NOT do

To stay faithful and avoid scope creep:

- It does not implement the rebundle. It proposes. The org decides.
- It does not score "innovation potential" or "transformation maturity" — those metrics tend to be self-justifying and rhetorical.
- It does not produce a roadmap. The play is a frozen assessment at one date, not a plan.
- It does not extend to capability composition (that is the next playbook's territory: capabilities and co-creators).

## Method limits

- **Constraint classification is interpretive**. Two reasonable agents may classify an activity differently. The audit gate enforces evidence per claim, but the choice of *primary* constraint among multiple plausible ones is a judgment call. The play surfaces the evidence; the reader can disagree.
- **Tool/engine classification depends on AEI snapshot**. The dataset is point-in-time. An activity classified `tool` today may legitimately become `engine` after a new release.
- **Autonomy-coordination mode is the hardest claim to ground**. Structure citations on this dimension are scarce; the play should be conservative.
- **Rebundle proposals are not predictions**. They are conditional: *if* the engine works as observed in AEI, *then* this rebundle becomes available. The play states this conditional explicitly.
- **The skill does not handle multi-slice patterns**. Cross-bundle coordination patterns (e.g., the org has many parallel matrix units, all with the same coordination paradox) require multiple plays + manual synthesis.

## Anti-hallucination discipline

Three structural rules:

1. **Constraint claims cite structure**. The audit verifies that every `primary_constraint` has a structure file or source-id behind it.
2. **Engine claims cite AEI rich data**. The audit refuses an `engine` classification without an AEI rich match supporting the autonomy shift.
3. **Rebundle proposals are conditional and labeled**. The audit verifies that every rebundle candidate names the engine that enables it AND the constraint that still binds.

The agent narrates around audited structure; the agent does not classify constraints or AI uses without cited evidence.

## Autoresearch loop

The agent runs the playbook iteratively. Each iteration produces a play; each iteration is then scored on five dimensions before the next pass — four deterministic gates plus an opt-in LLM judge.

**Score**:

```bash
python3 skills/playbooks/reshuffle/autoresearch.py \
  --map <reshuffle.json> \
  --org-dir <org-dir> \
  [--llm]
```

| Dimension | What it checks |
|---|---|
| **Recognizability** | Decisions mention named components (units, activities, anchor) by their org labels. |
| **Plain language** | No paraphrased framework jargon: `see-saw`, `flywheel`, `coordination paradox`, `bundle state`, `engine candidate`, `rebundle`, `constraint distribution`, `dissolves the constraint`. The leader reads outcomes, not vocabulary. |
| **Decision anchoring** | At least three items in `decisions[]`, each ≥ 60 chars in `answer`, each citing a non-empty `source`. |
| **Audit grounded** | Every component with a `_structure_id` resolves to a real file under `org/`. |
| **LLM judge** *(opt-in: `--llm`)* | Claude Sonnet 4.6 scores each decision on `actionable` (yes/no), `distinctive` (high/medium/low), `readable` (yes/no). Skipped when `ANTHROPIC_API_KEY` is not set. |

The play's primary interpretive surface is the top-level `decisions[]` array — the leader-facing reading of which capability becomes the new constraint, where the see-saw becomes a flywheel, what to hire / divest / reorganise around. Engine candidates and rebundle candidates are the structured intermediates; the decisions translate them for action. The agent fills this array as the final step of the playbook, then iterates until every dimension passes.

**Reference example** — the canonical artefact for this skill is the Outline & Co. sample-org play:

- `mcp-server/test-fixtures/sample-org/plays/data/reshuffle-outline-2026-05-07.json` — the source JSON with components classified, engine candidates, rebundle candidates, bundle state, and `decisions[]`
- `mcp-server/test-fixtures/sample-org/plays/data/reshuffle-outline-2026-05-07.html` — the rendered viewer

Open the HTML in a browser to see exactly what this skill produces. The play covers the studio's mid-market baseline commitment (12 activities across 4 units): 8 coordination-bound, 4 scarcity-bound; 3 engine candidates (kickoff workshop, asset handover, competitive audit) where AI as shared-knowledge infrastructure would dissolve a structural cost; 2 direction options (compounding context as the conservative move, production-handed-off as the radical follow-on). Three leader-facing decisions sequence the moves over 2026-2027.
