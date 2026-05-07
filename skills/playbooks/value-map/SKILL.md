---
name: value-map
description: "Build a value-chain map for an anchor (a commitment or a unit) of the organization. Each component is positioned on an evolution axis with an optional AI overlay. The artefact is a JSON + HTML + SVG triplet under org/plays/data/: the HTML is an interactive map with a popover next to each clicked node, a 'How to read this map' section with three to five concrete operational decisions tied to component positions, and an explicit notice when no AI overlay is attached. Canonical reference output: mcp-server/test-fixtures/fake-org/plays/data/value-map-studio-mid-market-baseline-2026-05-07.html (Outline & Co., a fake creative agency)."
---

# Playbook: value-map

Build a value-chain map for an anchor in the organization. The map answers two questions:

## How this playbook is run (read this first)

This playbook **must** produce a persistent file artefact under `org/plays/data/`, not an in-chat widget. The agent's job is to drive the bundled tooling, not to render the map manually inside the conversation.

**Required tooling**: `org_play_run` (mcp tool). Two calls per run:

1. `org_play_run(playbook="value-map", mode="build", anchor=<id>, kind="commitment"|"unit")` → returns the JSON skeleton from `build.py`. Read it, fill the agent-interpretive fields per §3 below.
2. `org_play_run(playbook="value-map", mode="render", json_content=<the filled JSON as a JSON string>)` → writes JSON, runs `audit.py`, runs `viewer.py`, returns the HTML and SVG paths plus the audit pass/fail.

**Do not** use Claude Desktop's inline `visualize` / `show_widget` / artifact features for this playbook. Reasons: (a) those widgets are ephemeral (lost when the chat ends), (b) they bypass the audit gate, (c) they don't use the Play New design system that the bundled `viewer.py` applies. The HTML returned by `org_play_run` mode=render is the canonical visualization.

The JSON + HTML + SVG triplet under `plays/data/` is the canonical artefact. A **markdown play** at `plays/value-map-<anchor>-<date>.md` is **optional but encouraged** — it is the surface where the agent commits to *what the map means for the org*. When written, the markdown play must contain a **"Decisions enabled"** section with 3–5 concrete operational decisions, each tied to specific component positions and citing structural sources (charter §, role descriptions, financial summary). Without that section the markdown is overhead. With it, the play moves from "here is a Wardley map" to "here are the moves the studio can make this quarter, grounded in the studio's own facts."

The `org_log_append` line closes the run.

If `org_play_run` returns an error (wrong arguments, audit failure, missing python3), report the error verbatim to the user and stop. Do not fall back to an in-chat widget.

**How to present the result — strict protocol** (do not paraphrase any of these steps):

1. As soon as render returns with `status: "ok"`, call `org_open` immediately with the value of `artefacts.html` (the relative path). This opens the file in the user's default browser without further interaction.
2. In your chat reply, paste the response field `presentation_markdown` **verbatim**, exactly as returned. It is already a `[text](file://absolute-path)` Markdown link; do not wrap it in code fences, do not surround it with quotes, do not rephrase. Pasted verbatim it renders as clickable in Claude Desktop and serves as a backup for the user if step 1's auto-open is blocked.
3. Add one sentence of context above or below the link summarizing the result (e.g. "12 componenti posizionati, 3 con evolution_target, audit pass").
4. Do NOT extract the SVG from the artefacts and inline-render it as a widget. The HTML opened in step 1 is the canonical visualization (Play New design system, brand font embedded, click-to-modal on every component).

If the user later asks to re-open the artefact, call `org_open` again. If they ask for a smaller preview, send the SVG path — but only on explicit request, not by default.

## Output style

All consumer-facing text produced by this skill (play body, viewer copy, modals, interpretive narratives, chat replies to the user) must follow the project style charter in [skills/STYLE.md](../../STYLE.md). The charter does not govern this SKILL.md, schema fields, or code — it governs what the reader sees.

**Forbidden in any output**: the surname of the author historically associated with this kind of map (the one starting with W). Internal type names like `WardleyMap` exist only for dashboard interop and never appear in agent-facing chat, in play bodies, or in viewer copy. Call the artefact "value-map" (English) or "mappa di valore" (Italian). The methodology — evolution stages, components, climatic patterns — is described without naming the author.

1. Where does each component on the value chain sit on the evolution curve (genesis / custom / product / commodity), and where is AI pushing it?
2. What new components or stakeholder needs are emerging as the chain shifts?

The output uses the same JSON schema as the play-new-dashboard's `WardleyMap` type — so a play produced here can be loaded into the dashboard's renderer, and conversely a dashboard-generated map can be ingested as a play.

## Output schema

The play produces three artefacts under `org/plays/data/`:

- `value-map-<anchor>-<date>.json` — the WardleyMap (schema below)
- `value-map-<anchor>-<date>.svg` — static rendering of the map (same visual style as the dashboard)
- `value-map-<anchor>-<date>.html` — optional interactive HTML companion

The frozen play in `org/plays/value-map-<anchor>-<date>.md` references these artefacts and adds the structure citations and the operational interpretation.

### JSON schema

```ts
type WardleyMap = {
  end_user: string | string[];          // single or multi-sided
  new_end_users?: { label: string; description: string }[];
  anchors: {
    id: string;                         // "a1", "a2", ...
    label: string;                      // user need (verbatim, short)
    description?: string;
    evolution: number;                  // 0..1
    evolution_target?: number;          // 0..1, must be > evolution; omit if stable
    is_new?: boolean;                   // true = emerging need; never combine with evolution_target
  }[];
  components: {
    id: string;                         // "c1", "c2", ...
    label: string;
    visibility: number;                 // 0..1, 1 = closest to user, 0 = deep infra
    evolution: number;                  // 0..1
    evolution_target?: number;          // 0..1, must be > evolution; omit if stable
    ai_effect?: string;                 // free text; if present must cite AEI evidence
    is_new?: boolean;                   // true = emerging component; never combine with evolution_target
  }[];
  edges: { from: string; to: string }[];   // dependencies down the chain
  new_value?: { label: string; description: string; stakeholder: string; enabled_by: string }[];

  // The load-bearing interpretive surface. Three to five concrete
  // operational decisions a leader can take from the map. Each is a
  // tuple: a reader-facing question, the answer derived from the
  // positions on the map, and a citation to a structural source
  // (charter §, role descriptions, financial summary, prior play).
  // The HTML viewer renders these as the "How to read this map"
  // section. Without the array the section degrades to a "no
  // interpretation attached" notice.
  decisions?: {
    question: string;     // reader-facing question, plain English
    answer: string;       // 2-4 sentence answer + a concrete move
    source: string;       // citation, e.g. "outline-charter-2024 §15"
  }[];
};
```

### Evolution stages (numeric ranges)

Inherited from the dashboard's convention:

- **0.00–0.17** — genesis (novel, unknown)
- **0.17–0.40** — custom-built (in-house, learning)
- **0.40–0.70** — product / rental (proven, repeatable, multiple providers)
- **0.70–1.00** — commodity / utility (standardized, ubiquitous)

### Sample (real dashboard assessment, talent matching business)

```json
{
  "end_user": ["Aziende clienti", "Professionisti indipendenti"],
  "anchors": [
    {
      "id": "a1",
      "label": "Talento qualificato in 72 ore",
      "evolution": 0.72,
      "evolution_target": 0.88,
      "description": "Bisogno consolidato nel mercato enterprise; l'AI accelera l'aspettativa verso matching quasi istantaneo."
    }
  ],
  "components": [
    {
      "id": "c1",
      "label": "Matching talento-cliente",
      "visibility": 0.95,
      "evolution": 0.55,
      "evolution_target": 0.82,
      "ai_effect": "I modelli di linguaggio riducono il costo di analisi di brief e profili, spingendo il matching verso commodity. Il vantaggio difendibile si sposta sulla qualità del segnale in ingresso, non sull'algoritmo."
    }
  ],
  "edges": [{"from": "a1", "to": "c1"}]
}
```

12–16 components per map (dashboard convention). Each component has at least one inbound or outbound edge.

## When to use

- After an `ai-exposure` play, to see where the AI signal applies along the evolution axis (the `evolution_target` is grounded in AEI evidence)
- Before a strategic decision on insourcing/outsourcing/build/buy
- When a stakeholder commitment looks fragile and you need to see *why* (often: a component held in custom-built form when the market has moved to product)

## Pre-conditions

- Structure `org/` healthy (lint Tier 1 + Tier 2 = 0)
- Anchor exists in the structure:
  - `commitment` anchor: a node under `org/commitments/`
  - `unit` anchor: a node under `org/nodes/units/`
- Optional but recommended: a matching `ai-exposure` play already produced — the `ai_effect` and `evolution_target` fields are grounded in AEI matches by reference

## What the map measures (and what it does NOT measure)

| Element | What it measures | What it does NOT measure |
|---|---|---|
| `evolution` | How standardized/commoditized the component is, judged from cited evidence | Future state |
| `evolution_target` | Where AI or competitive pressure is pushing this component, citing AEI evidence | Speed of change, deterministic trajectory |
| `visibility` | How close the component is to the end-stakeholder need at the top | Importance, business value |
| `ai_effect` | Free-text description of the AI shift, with cited AEI evidence | Capability ceiling, vendor capability |
| `is_new` | Component (or anchor) does not exist today but emerges from the chain shift | Probability of emergence |

## Workflow

### 0. Canonical invocation via mcp (preferred)

When the bundled mcp server is available, the canonical way to launch this playbook is `org_play_run`:

1. Call `org_play_run` with `playbook="value-map"`, `mode="build"`, `anchor=<id>`, `kind="commitment"|"unit"`. The tool runs `build.py` for you and returns the skeleton JSON inline.
2. Read the skeleton, then for every component fill `evolution`, `visibility`, and optionally `evolution_target` / `ai_effect` / `is_new` per §3 below. Cite structure or AEI evidence.
3. Call `org_play_run` again with `mode="render"`, `json_content=<the filled JSON as a string>`. The tool writes to `plays/data/`, runs `audit.py`, then `viewer.py`, and returns the artefact paths (`json`, `html`, `svg`) plus the audit result.
4. Append a one-line entry to `log.md` via `org_log_append`. The play's success or failure is determined by the audit pass returned by render.

The JSON + HTML + SVG triplet under `plays/data/` is the primary artefact. The optional markdown play under `plays/` mirrors the JSON's decisions verbatim and is encouraged once the autoresearch loop passes.

If `org_play_run` is not available (older mcp build), fall back to the manual steps below.

### 1. Define the anchor

Pick one:
- A `commitment` ID (typical) — produces a value-chain map for that commitment
- A `unit` ID (whole-area case) — produces a map of the unit's value chain to its main stakeholder

Identify the **end_user**: who consumes the value at the top of the chain. For multi-sided cases, supply an array (e.g., `["donatori", "ricercatori"]`).

Write the **anchors** (user needs) — what the end users want, verbatim if possible, citing the source.

### 2. Build the value chain skeleton

```bash
python3 skills/playbooks/value-map/build.py \
  --anchor <anchor-id> \
  --kind commitment|unit \
  --org-dir org \
  [--ai-exposure-matches <path-to-matches.json>] \
  --out <chain.json>
```

The builder:
1. Walks the structure edges starting from the anchor (`requires`, `produces`, sub-units, activity links).
2. Emits a skeleton `WardleyMap` JSON with anchors and components extracted from the structure. **No `evolution`, `evolution_target`, or `ai_effect` is set yet** — these are agent-authored in step 3.
3. If `--ai-exposure-matches` is provided, attaches each component's matched AEI tasks as a hidden `_aei` field for the agent to consult when filling `ai_effect`.

The skeleton is deterministic. The agent cannot add components that don't exist in the structure — it can only add `is_new` components with explicit citation in step 3.

### 3. Position each component

For each component in the skeleton, the agent sets:

- `evolution` (0..1) — position by ubiquity and certainty in the market, not org perception. Stage bands above.
- `visibility` (0..1) — position in the dependency chain (1 = consumed by stakeholder directly, 0 = deep infra). Visibility is structural, not variable.
- Optional `evolution_target` — only if AEI evidence (or other cited signal) supports a rightward shift. Must be ≥ `evolution`.
- Optional `ai_effect` — free text, max ~50 words, with at least one citation to AEI matches or structure document.
- Optional `is_new: true` — for components that don't exist today but emerge from the chain shift. Must be connected to existing components via edges. Never combine with `evolution_target`.

For each anchor, the agent sets:

- `evolution` — how well-defined the user need is in the market
- Optional `evolution_target`, `is_new` — same rules as components

### 3b. Write the decisions

This is the load-bearing step of the playbook. The map is the evidence; the `decisions` array is what the map *means*. Without it, the play is a static positioning chart that asks the reader to be a Wardley specialist. With it, the play is a set of moves a leader can take to the next monthly review.

**Three to five decisions per play.** Fewer than three: the map's interpretation surface is thin; ask whether the playbook is the right tool for the question. More than five: each decision dilutes the others; pick the load-bearing ones.

**Each decision is a (question, answer, source) tuple:**

- `question`: a reader-facing question, plain English, no Wardley vocabulary. Imagine the leader of the org reading it cold over coffee. Examples that work:
  - *"Where does the value of an Outline engagement actually sit?"*
  - *"For what should the studio actually be paid?"*
  - *"Where does AI commoditize first, and what's the funnel?"*
  - *"Which roles need to shift?"*
  - *"What role is missing as the studio scales?"*

  Examples that don't work (too generic / too jargon):
  - *"Where to raise prices?"* (too shallow — see the deeper reframe below)
  - *"Which components are at evolution 0.5+?"* (jargon, not a leader's question)
  - *"What does the map show?"* (no commitment to interpretation)

- `answer`: 2-4 short sentences ending in a concrete move. The structure is: observation derived from the map → interpretation → move. Plain English. No "evolution 0.X" numbers, no Wardley terms standalone (the words *commodity* and *custom* can appear if used as plain English: "common practice" / "built in-house" are usually preferable). Cite the relevant component IDs in passing.

- `source`: a citation that the audit can verify, in the form `<source-id>` or `<source-id> §X.Y`. The citation must point to a real file under `org/sources/` referenced in the structure.

**Frame for the pricing question.** When the reader asks "where can the studio raise prices?" they are usually asking the wrong question. The deeper question is *for what should the studio be paid?*  Decompose the work into nodes; ask per node where value sits, what the feedback speed is, what the judgment density is. Bundles where commodity work subsidizes premium work must break apart. Commodity work becomes infrastructure (gift it or margin-price it as a funnel). Value shifts upstream toward irreplicable, context-specific judgment. (Reference: Roversi, *Il contesto e l'organizzazione*, https://workafter.substack.com/p/il-contesto-e-lorganizzazione, 2026.)

**Frame for the AI question.** AI commoditizing the production layer is not the threat. It is the funnel. The play surfaces this if it shows: which nodes are about to drift to commodity, which differentiated nodes upstream they funnel toward, and what the gift/margin-price strategy looks like.

### 4. Add new_end_users and new_value (if applicable)

If the chain shift produces a new stakeholder type (e.g., a fundraising org starting to serve researchers directly), document it under `new_end_users`. If the chain produces a new value flow that didn't exist before, document under `new_value`.

These fields are optional. Use only when the structure or AEI evidence supports them.

### 5. Visualize

```bash
python3 skills/playbooks/value-map/viewer.py \
  --map <chain.json> \
  --html <chain.html> \
  [--svg <chain.svg>]
```

The HTML is the **primary consumer artefact**: an interactive document a stakeholder can open in any browser. It contains:

1. A header with anchor title, id, and free-text description (from structure).
2. A **process introduction** explaining how to read the map (axes, shapes, the AI overlay arrows).
3. The map itself (inline SVG) with clickable nodes — clicking an anchor or component opens a modal showing label, kind, current/target evolution stage, AI effect, and the AEI top-K matches as evidence.
4. A text fallback below the map: components grouped by stage, each clickable to open the same modal.

Visual conventions (mirror the play-new-dashboard's `WardleyMapView` component):

- 1400×900 (or 1100 if more than 14 items)
- End-user nodes at the top, with extra padding so labels don't clip
- Anchors as diamond polygons; labels placed *below* the diamond to avoid colliding with end-user labels above
- Components as circles, positioned at `(evolution, visibility)`
- Edges as gentle curved arcs
- New components/anchors highlighted with accent color
- `evolution_target` rendered as a dashed arrow from current to target position
- Long labels truncated in SVG (~22 chars) — the modal shows the full label

The optional `--svg` flag also produces a standalone SVG file useful for embedding in the markdown play (`![](data/<map>.svg)`). The standalone SVG has the same truncations and is non-interactive.

### 6. Audit (anti-hallucination gate, mandatory)

```bash
python3 skills/playbooks/value-map/audit.py \
  --map <chain.json> \
  --org-dir org \
  [--ai-exposure-matches <path-to-matches.json>]
```

The audit verifies:

1. **Every component label matches a structure node** OR has `is_new: true` AND a citation in the play body.
2. **Every `ai_effect`** must cite at least one AEI match (when `--ai-exposure-matches` provided) or an explicit structure evidence ID.
3. **Every `evolution_target`** must have supporting evidence — typically from AEI penetration data on the matched O*NET task.
4. **Constraints on `is_new` and `evolution_target`** — the schema rules (never combine the two) are enforced.
5. **Edge integrity** — every edge's `from` and `to` reference an existing anchor, component, or end-user node.
6. **Component count** in the 12–16 range (warning, not failure).
7. **Decisions** — at least three items in `decisions[]`, each with a non-empty question, an answer ≥ 60 chars, and a non-empty source. Warning (not failure) when missing or short, since some plays can be saved without a markdown play. Run `autoresearch.py` for the strict gate.

Exit code: 0 = pass, 1 = fail. Same contract as `audit.py` for ai-exposure plays.

### 7. Write the play

In `org/plays/value-map-<anchor>-<date>.md`:

```yaml
---
id: value-map-<anchor>-<date>
type: play
playbook: value-map
target: <anchor-id>
dated: <YYYY-MM-DD>
frozen: true
sources: [<anchor file>, <activity files>, <unit files>, <external sources>]
references:
  - builder: skills/playbooks/value-map/build.py
  - viewer: skills/playbooks/value-map/viewer.py
  - audit: skills/playbooks/value-map/audit.py
  - map_json: org/plays/data/value-map-<anchor>-<date>.json
  - map_svg: org/plays/data/value-map-<anchor>-<date>.svg
  - ai_exposure_play: org/plays/ai-exposure-<scope>-<date>.md  # if applicable
---
```

Body (in order):

1. **Anchor and end users** (one paragraph + citation)
2. **The map** (link to the HTML/SVG artefact; mobile/text fallback as bulleted list grouped by stage)
3. **Per-component placement** grouped by stage band, each row citing the source where the placement is grounded
4. **Decisions enabled** — *the load-bearing section*. Three to five concrete operational decisions a leader can take to the next monthly review. Each decision is a (question, position-derived answer, move, citation) tuple. Without this section the play is a static map; with it, the play is a what-if simulation grounded in the studio's facts. Examples (from `mcp-server/test-fixtures/fake-org/plays/value-map-studio-mid-market-baseline-2026-05-07.md`): *"Where to invest in tighter templating?"*, *"Which roles are most exposed to AI commoditization?"*, *"Where can the studio raise prices?"*, *"What does the value chain say about the next hire?"*.
5. **New components / new value** (if any) — what emerges from the shift
6. **Method limits** — what the map can't say (no AEI overlay, agent-authored placements at the margin, etc.)
7. **Cross-references**

### 8. Lint + log

`python3 lint.py` must pass. `org_log_append` with a one-line summary.

## Output: what the play enables

People in the organization can ask Claude:

- "Which components of the legacy-fulfilment pipeline are commoditizing under AI pressure?"
- "Where is this commitment exposed to the genesis of new stakeholder needs?"
- "Compare two pipelines on the evolution axis."
- "Which components could become new value flows if AI commoditizes them?"

Answers are grounded in the frozen map and cited to structure + AEI matches.

## Method limits

- **Position is a judgment call**. The audit gate enforces evidence per placement, but reasonable agents can place the same component differently. The play surfaces the evidence; the reader can disagree.
- **`evolution_target` is a prediction**. It assumes current AEI and competitive forces continue. The play should flag this explicitly.
- **AEI grounding is partial**. AEI covers ~3,259 O*NET tasks with rich data; the rest are silent. `ai_effect` claims on components with only `fallback` matches must cite that as a limitation.
- **12–16 components is a heuristic**. Smaller anchors (a single sub-team commitment) may need fewer; cross-Direzione commitments may need more.
- **Structure-bounded**. External components (a vendor, a regulator, a market trend) appear as `is_new` or with explicit external citation in the play body.

## Anti-hallucination discipline

Three structural rules:

1. **Component existence is grounded**. The builder produces the skeleton deterministically by reading structure edges; the agent cannot add components that don't exist as structure nodes (except `is_new` with body-level citation).
2. **`ai_effect` and `evolution_target` cite evidence** that the audit script can find — typically an AEI match in `matches.json`.
3. **Interpretation is demarcated**. The "decisions" array is the interpretive surface; every decision must cite a structural source the audit can resolve.

The agent generates narrative around audited structure; the agent does not assert evolution shifts without cited AEI or structure evidence.

## Autoresearch loop

The agent runs the playbook iteratively. Each iteration produces a play (JSON + HTML + SVG); each iteration is then scored on five dimensions before the next pass — four deterministic gates plus an opt-in LLM judge.

**Score**:

```bash
python3 skills/playbooks/value-map/autoresearch.py \
  --map <chain.json> \
  --org-dir <org-dir> \
  [--llm]
```

The script runs the checks and prints a per-dimension score plus an overall pass/fail.

| Dimension | What it checks |
|---|---|
| **Recognizability** | Does the play mention specific units / people / activities of the org by name (not as generic placeholders)? |
| **Plain language** | Density of jargon: standalone Wardley terms, "evolution 0.X" patterns, technical acronyms without expansion. |
| **Decision anchoring** | At least three items in `decisions[]`, each ≥ 60 chars in `answer`, each citing a non-empty `source`. |
| **Audit grounded** | Every component has `_structure_id` resolving to a real file. (Inherits from `audit.py`.) |
| **LLM judge** *(opt-in: `--llm`)* | Claude Sonnet 4.6 scores each decision on three axes the deterministic checks can't see: `actionable` (yes/no — names a Monday move, not just an observation), `distinctive` (high/medium/low — could only be made of *this* org), `readable` (yes/no — would the leader of this org track the prose). Skipped (does not fail the gate) when `ANTHROPIC_API_KEY` is not set. |

The script returns exit code 0 only if every non-skipped dimension passes. The agent's iteration loop:

1. Run `org_play_run` build → render → first HTML.
2. Run `autoresearch.py`. If a dimension fails, the script prints which.
3. Read the failure mode, edit the JSON (positions, decisions, ai_effect prose), call render again.
4. Re-score. Repeat until everything passes or the operator intervenes.

The reference iteration (the canonical example produced for `Outline & Co.`) reached pass on iter-2 after the iter-1 decisions were rewritten in plain English with the Roversi pricing frame.

**Reference example** — the canonical artefact for this skill is the Outline & Co. fake-org play, shipped in the public template's test fixtures:

- `mcp-server/test-fixtures/fake-org/plays/data/value-map-studio-mid-market-baseline-2026-05-07.json` — the source JSON with `decisions[]` filled in
- `mcp-server/test-fixtures/fake-org/plays/data/value-map-studio-mid-market-baseline-2026-05-07.html` — the rendered viewer
- `mcp-server/test-fixtures/fake-org/plays/data/value-map-studio-mid-market-baseline-2026-05-07.svg` — the static SVG companion

Open the HTML in a browser to see exactly what this skill produces. The play sits over the studio's mid-market baseline commitment and frames where the studio's value actually lives, the pricing reframe (separating slow-feedback judgment work from fast-feedback production), the AI commodity funnel, and the missing context-steward role.

**Output of the loop**: the same JSON + HTML + SVG triplet, but the JSON now has audited decisions and the HTML renders them in the "How to read this map" section. The play markdown under `org/plays/` is optional; when written it mirrors the JSON's decisions verbatim.

## Author-name policy

Per project rules: framework author names (the surnames historically associated with this kind of map, with platform reshuffle, with capability composition, etc.) **never appear** in the play body or in any artefact under `org/`. They may appear in this `SKILL.md` for productizable documentation but are stripped from output.
