---
name: ai-exposure
description: "For each activity of an organization, classify AI exposure by intersecting the observed-usage signal in the Anthropic Economic Index with organization-specific constraints (legal, statutory, cognitive). Output: a frozen play with tables and 3 visual artefacts."
---

# Playbook: ai-exposure

## How this playbook is run (read this first)

This playbook produces persistent file artefacts under `org/plays/data/`, not in-chat widgets.

After running `match.py` against your activity set the full-org match lands in `org/plays/data/all-org-matches-<date>.json` (18510 O*NET tasks scored against your N activities). The HTML viewer at `org/plays/data/ai-exposure-<date>.html` opens in any browser.

For analyses on a slice (single area / single Direzione), run `match.py` from a terminal as documented in §1-§3 of the workflow below; an `org_play_run` mode for re-running the embedding match against a fresh subset is not yet exposed (the embedding model load is multi-second). The audit + viewer rerun on the existing matches.json works fine via `org_play_run(playbook="ai-exposure", mode="render", json_content=<matches JSON>)` — useful when you want to regenerate the HTML after changing the viewer template.

**Do not** use Claude Desktop's inline `visualize` / `show_widget` / artifact features for this playbook. They are ephemeral, bypass the audit gate, and don't use the bundled design system.

For each activity in scope, produce a two-layer assessment of AI exposure:

## Output style

All consumer-facing text produced by this skill (play body, viewer copy, modals, interpretive narratives) must follow the project style charter in [skills/STYLE.md](../../STYLE.md). The charter does not govern this SKILL.md, schema fields, or code — it governs what the reader sees.

- **Layer 1 — observed usage signal** from the Anthropic Economic Index (descriptive, derived from the dataset)
- **Layer 2 — organization-specific constraints** that require or suggest human work (judgment cited from external sources)

Output: a `play` in `org/plays/ai-exposure-<scope>-<date>.md`, frozen at creation.

The mapping from activities to O*NET tasks is **embedding-based**, not manual. The agent does not pick matches by reading; matches are produced by cosine similarity between multilingual sentence embeddings. This is reproducible and auditable.

## When to use

- Planning of AI investments: where to allocate transformation resources
- Reality-check of automation proposals: does the observed data confirm the intuition?
- Per-area scorecard for the leader: rapid comparison of exposure across areas

## Pre-conditions

- Datasets in `skills/playbooks/ai-exposure/data/`:
  - `anthropic-aei-onet-<release>.csv` — rich subset (per-task `ai_autonomy_mean`, `ai_education_years_mean`, `human_education_years_mean`, `count`, `pct`). Currently 2026-03-24 release, 3,259 tasks with rich metrics.
  - `anthropic-task-penetration.csv` — fallback for tasks not in rich subset. 17,998 tasks with simple penetration score.
- Python ≥ 3.10 with `sentence-transformers` installed (`pip3 install --user sentence-transformers`).
- Structure `org/` healthy (lint Tier 1 + Tier 2 = 0).
- Activities in scope have textual description (frontmatter `description` + body).

## What the Anthropic data measures (and what it does NOT measure)

The dataset comes from **real Claude AI conversations** classified by Clio (Anthropic's automatic classification system) on O*NET tasks.

| Metric | What it measures | What it does NOT measure |
|---|---|---|
| `count`, `pct` | How many Claude conversations were classified as that O*NET task in the sampled week | Technical AI capability; how often the task is performed in the world |
| `ai_autonomy_mean` (1-5) | How autonomously Claude operated in the observed conversations | Capability to operate autonomously in other contexts |
| `ai_education_years_mean` | Sophistication of AI's responses (estimated education level) | AI capability ceiling |
| `count = 0` | **No Claude conversation observed for that task** | Neither AI incapacity nor presence of human-only constraint. **The data is silent on the cause.** |

**Implication**: saying "this task has 0 penetration so it is human-required" is incorrect. The cause of `count = 0` is external to the data (AI capability / legal constraint / not yet tested / sampling). To say "human required" you need external evidence cited — that is Layer 2's job.

## Workflow

### 1. Define scope

The play can target:
- A single **area** (~10-20 activities): quick recipe
- A **direction** (~50-100 activities): requires aggregation
- The **entire functional structure**: massive output

For first execution on a new organization: use scope = single area.

### 2. Build activities input file

For each activity in scope, build a JSON record `{id, text}` where `text` is the description + relevant body content. Save as `activities.json`.

Example builder (Python):
```python
import json, re
from pathlib import Path
out = []
for p in sorted(Path("org/nodes/activities").glob("<area-prefix>-*.md")):
    text = p.read_text()
    desc_m = re.search(r'^description:\s*"([^"]+)"', text, re.M)
    body_m = re.search(r'^# .+?\n\n(.+?)(?=\n\n)', text, re.M | re.S)
    parts = []
    if desc_m: parts.append(desc_m.group(1))
    if body_m: parts.append(body_m.group(1).strip())
    out.append({"id": p.stem, "text": " ".join(parts) or p.stem})
Path("activities.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
```

### 3. Run the embedding matcher

```bash
cd skills/playbooks/ai-exposure
python3 match.py --activities <activities.json> --top-k 5 --out <matches.json>
```

This produces, for each activity, the top-K O*NET tasks by cosine similarity (multilingual model `paraphrase-multilingual-MiniLM-L12-v2`), each annotated with the Anthropic metrics (when available) and an `in_rich` flag (true = task has rich aggregates; false = fallback only, typically with penetration ≈ 0).

The first run downloads the model (~50 MB) and embeds all O*NET tasks (~15 seconds, cached afterwards in `.embeddings-cache.npz`).

### 4. Classify each activity (two layers, separated)

**Layer 1 — Anthropic signal** (descriptive, derived from the matcher output):

| Level | Criteria over top-K matches | Meaning |
|---|---|---|
| strong | majority in `rich` AND mean `ai_autonomy_mean` ≥ p75 of dataset | AI delegation pattern widely observed |
| medium | majority in `rich`, autonomy near median | Pattern present but marginal |
| mixed | partly `rich` (with usable metrics) + partly `fallback` (zero data) | Sub-tasks with different signals |
| zero | all top-K in `fallback` (penetration = 0) | AI not observed. Cause external to data. |

**Thresholds** are calibrated on the percentiles of the specific dataset release (e.g., for 2026-03-24: p25 = 3.21, p75 = 3.57).

**Layer 2 — Organization-specific constraint** (judgment cited from external source):

| Type | Source of authority | What it captures |
|---|---|---|
| **legal-bound** | laws and regulations of the country in which the organization operates | public deeds, court representation, regulated-profession requirements |
| **statutory-bound** | statute and internal regulations of the organization | governance body decisions, board deliberations |
| **judgement-preserved** | internal analysis documents (papers, position docs, organizational models) | typically-human capabilities: emotionally charged contexts, integrated judgment, discretion, long-term relationships |
| **none** | — | unconstrained activities |

For each constraint: **cite the specific source** (article of law, article of statute, section of internal document). If no source can be cited, the activity is classified as "none".

### 5. Synthesis (operational decision)

Emerges from intersecting the two layers:

| Layer 1 | Layer 2 | Operational decision |
|---|---|---|
| strong | none | **Invest in AI** (low risk, model already demonstrated elsewhere) |
| strong | statutory-bound | **AI prepares, body decides** (documental delegation, final decision to the body) |
| strong | legal-bound | **Verify whether constraint is only on final output** (e.g., notarial signature): if so, AI prepares, person signs |
| mixed | any | **Workflow redesign**: define handover point AI → human clearly |
| zero | legal-bound | **Blocked upstream by norm** (do not invest AI for substitution; possibly for support) |
| zero | judgement-preserved | **Keep human by organizational choice** (revisable if culture evolves) |
| zero | none | **Uncertainty**: monitor adoption evolution |

### 6. Aggregate at scope level

Counts by Layer 1 level and Layer 2 type. Patterns observed.

### 7. Validate against internal sources (if available)

If the organization has an existing manual analysis of activities in scope (paper, position document, operating model): compare the play's classification with the internal one. Substantial alignment = play is valid. Differences = candidates for iteration.

### 8. Visualize (recommended)

Two channels: markdown-native artefacts (in the play body) + standalone HTML viewer (interactive).

**Markdown-native artefacts** (in the play):

**a. Mermaid quadrantChart (2D)** — AI adoption (X axis) × freedom from organizational constraint (Y axis). The 4 quadrants map to operational decisions.

```mermaid
quadrantChart
    title <Scope title>
    x-axis "Low observed AI adoption" --> "High observed AI adoption"
    y-axis "Legal/statutory constraint" --> "Operational freedom"
    quadrant-1 "Invest in AI: mature + free"
    quadrant-2 "AI emerging, monitor"
    quadrant-3 "Blocked by norm"
    quadrant-4 "AI prepares, body decides"
    "Activity name": [x_signal, y_freedom]
    ...
```

**b. Compact bar chart per activity** — ASCII sparkline for Anthropic signal + symbol for constraint + decision in 2 words:

```
Activity name       █████████░  🏛   AI prepares, body decides
```

Symbol convention: ⚖ legal, 🏛 statutory, 💬 judgement-preserved, ⚪ none.

**c. Scope aggregate** — distribution of operational decisions as ASCII bars.

**Standalone HTML viewer** (optional, generated from the matches JSON):

```bash
python3 skills/playbooks/ai-exposure/viewer.py \
  --matches <path-to-matches.json> \
  --metadata <path-to-activities-metadata.json> \
  --area-notes <path-to-area-notes.json> \
  --area-descriptions <path-to-area-descriptions.json> \
  --org-description-file <path-to-org-description.txt> \
  --lang en|it \
  [--task-translations <path-to-translations.json>] \
  --out <path-to-viewer.html> \
  --title "<title>"
```

Output: a single self-contained HTML file (vanilla HTML/CSS/JS, no external deps). Visual style inspired by Anthropic's Job Explorer (anthropic.com/economic-index).

Page structure, top to bottom:

1. **Organization snapshot** (only when no specific area filter is active): free-text description + summary numbers + a horizontal distribution bar showing the org-wide split across the four Anthropic categories (automated / augmented / assistive / no-data) + legend with percentages.

2. **Filters**: search box, signal level (high signal / some signal / low signal / no signal / low confidence — these are activity-level levels derived from the per-task category counts; see thresholds in §4), area filter pills.

3. **Per-area sections** (when "All areas" is active, group by area; otherwise show only the selected area):
   - Area heading
   - **Snapshot block**: scope description (structure-grounded one-liner from the area's `nodes/units/<area>.md` perimeter), distribution bar specific to that area, and an interpretive **commentary note** (free prose authored by the agent, audited by `audit-notes.py`).
   - Grid of activity cards.

4. **Activity card**: title, ID + area, short description, **closest O*NET task block** (top-1 task with confidence % and autonomy /5; supports an optional Italian translation when `--task-translations` provided), 5×5 grid of squares (one per top-K match) clustered by category color (verde → viola → azzurro → beige) with hover tooltip and click-to-modal, and a stat line showing the per-category breakdown (e.g., "X automated · Y augmented · Z assistive · W no data").

5. **Modal (on square click)**: full O*NET task text (and translation if available), confidence, autonomy, sample size with warning if `< 100`, category, and a chain-of-inference disclaimer ("org activity → closest O*NET task → category labels the conversation sample, not the activity").

The viewer is consumer-facing: the leader/decision-maker opens it in a browser, scans the org snapshot, drills into an area, opens individual cards. The markdown play remains the audit trail; the HTML is the navigable consumer surface.

**Optional inputs** that enrich the viewer:

- **`--metadata <list.json>`**: list of `{id, title, description, area, unit, ...}` for each activity. Title and description make cards readable instead of showing only IDs.
- **`--area-descriptions <dict.json>`**: `{area_id: "high-level scope description"}`. One line per area, structure-grounded (typically copied from the area's `nodes/units/<area>.md` frontmatter `description` field).
- **`--area-notes <dict.json>`**: `{area_id: "interpretive commentary"}`. Free prose, 3-5 sentences per area, authored by the agent. Must pass `audit-notes.py` before being shipped.
- **`--org-description` / `--org-description-file`**: free text describing the organization, rendered at the top.
- **`--task-translations <dict.json>`**: `{english_task: target_language_task}` for displaying O*NET task names in the UI language. Translations can come from any pipeline (manual, LLM-assisted, machine translation) — the viewer only consumes the dict.
- **`--lang en|it`**: UI language for labels, legends, modal copy. Default `en`.

### 9. Write the play

In `org/plays/ai-exposure-<scope>-<date>.md`:

```yaml
---
id: ai-exposure-<scope>-<date>
type: play
playbook: ai-exposure
target: <scope>
dated: <YYYY-MM-DD>
frozen: true
sources: [<role-description docs / specs of scope>, <internal documents cited in Layer 2>, ...]
references:
  - dataset: anthropic-aei-onet-<release>
  - matcher: skills/playbooks/ai-exposure/match.py
  - matches_input: <path to activities.json>
  - matches_output: <path to matches.json>
---
```

Body (in order):
1. **Actionable summary** (3-5 lines): what to do / not to do
2. **2D view** (Mermaid quadrantChart)
3. **Compact bar chart per activity** + **Scope aggregate**
4. **What the Anthropic data measures** (the limits table copied into the play for honesty)
5. **What the organizational constraint is** (the 3 types + cited examples specific to scope)
6. **Per activity** (detailed tables with the two layers separated, top-K matches and similarity scores from the matcher)
7. **Aggregate** (counts)
8. **Validation vs internal source** (if applicable)
9. **Method limits** (explicit caveats, declared biases)
10. **Operational consequences** (concrete decisions for the recipient)
11. **Cross-references**

### 10. Audit (anti-hallucination gate, mandatory)

Before saving the play, run:

```bash
python3 skills/playbooks/ai-exposure/audit.py \
  --play <path-to-play.md> \
  --matches <path-to-matches.json> \
  [--legal-source "Civil Code"] [--legal-source "Bar Regulations"] ...
```

The audit is deterministic and verifies:

1. **Every numerical claim** in per-activity sections (autonomy, count, similarity) is traceable to the matches JSON. The agent cannot cite values it didn't get from the matcher.
2. **Legal/regulatory claims**, for any source name passed via `--legal-source`, without a specific article reference (`art.`, `article`, `§` followed by a number) are flagged. The play must include a dedicated review section (heading containing "review", "validate", "unverified", or equivalent) listing those claims for human-legal review, otherwise the audit fails.

The legal-source list is **per-organization**: the play applies the audit to whichever country/legal frame the organization operates in, by passing the relevant source names. The skill itself is country-agnostic.

If the audit returns exit code 1, the play is not committable. Fix the issues and re-run.

This is the **anti-hallucination gate**: it makes inventing numbers or unverified legal claims structurally hard. The agent's role becomes generating narrative around verified data, not asserting facts.

### 10b. Audit per-area commentary (if you ship area notes)

If the play is accompanied by per-area commentary notes (rendered above each area's grid in the HTML viewer), those notes are also free prose authored by the agent and must pass a deterministic gate.

```bash
python3 skills/playbooks/ai-exposure/audit-notes.py \
  --notes <path-to-area-notes.json> \
  --matches <path-to-all-org-matches.json> \
  --metadata <path-to-activities-metadata.json>
```

The audit verifies:

1. **Every integer** in each note (digits or Italian/English number words) traces to a known fact for that area: activity count, level counts, category counts, total Claude.ai conversations on top matches. Years in a recent window pass. A small, documented allow-list permits external constants (e.g., a regulation reference) — extend with care.
2. **Every percentage** in each note traces to a known fact: average top-1 confidence (rounded), per-category percentage (automated/augmented/assistive/no-data), or a level-quota percentage. ±1 rounding tolerance is applied.
3. **Every decimal** in each note matches the area's average autonomy (one or two decimals).
4. **Every italicized title** (`*…*`) exists as a real activity in that area.

Same exit-code contract: 0 = pass, 1 = fail. Like `audit.py`, the gate eliminates plausible-but-fabricated numbers from the prose. The agent writes naturally; the gate enforces traceability.

### 11. Lint + log

`python3 lint.py` and `python3 lint-semantic.py` must pass. `org_log_append` with a summary.

## Output: what the play enables

People in the organization can ask Claude:
- "Which activities of area X are highly AI-exposed?"
- "How much of [person]'s capacity could be freed by AI?"
- "Where NOT to invest AI in area X?"
- "Comparison: is area X more or less exposed than area Y?"

Answers based on the frozen play, cited with traceable sources (Anthropic data + cited constraints).

## Method limits

- **Embedding mapping is reproducible but not perfect**: cosine similarity surfaces semantically related tasks but not always the most operationally relevant. Top-K reduces single-pick risk; reading the top-K with similarity scores is more honest than asserting one match. Sometimes the top-1 from embedding misses domain nuances that an expert reader would catch — but this is fine because the play reports the top-K, not a single forced choice.
- **Adoption ≠ capability**: penetration 0 does not mean AI is incapable. The data is silent on the cause.
- **Temporal snapshot**: the dataset is a point-in-time release. Values will change with new releases.
- **Geo-bias**: Anthropic Economic Index is geo-global but probably US-weighted. Country-specific legal constraints are documented in Layer 2.
- **`human_with_ai_time` not used**: the metric is counter-intuitive in the dataset (systematically longer than `human_only_time`). Probably measures Claude session duration with iterations, not net cognitive time. Not used.
- **Layer 2 depends on internal sources**: the quality of the "judgement-preserved" classification depends on how much the organization has articulated its cognitive/relational constraints. Without internal source, those activities stay in "none".

## Method iterations

- **v1** (initial): cherry-picked manual mapping, absolute thresholds, narrative output, no separation of layers. Over-claimed AI capability from observational data.
- **v2**: thresholds recalibrated on dataset percentiles; comparison with internal source; actionable summary.
- **v3**: explicit separation into 2 layers (Anthropic signal vs organizational constraint); categories renamed to avoid over-claiming; constraint sub-types (legal/statutory/judgement-preserved).
- **v4**: 3 markdown-native visual artefacts (2D quadrant, ASCII bar chart, aggregate).
- **v5**: manual mapping replaced with embedding-based matcher (`match.py` + multilingual sentence-transformer). Reproducible, auditable, no agent confirmation bias in the matching step.
- **v6**: audit.py introduced as mandatory gate. Every play must pass deterministic checks before commit: (a) every cited number traces back to matches.json, (b) unverified legal claims must be acknowledged in a dedicated review section. Eliminates the residual hallucination of an agent inserting plausible-sounding numbers from prior context.
- **v7** (current): viewer redesigned around the four real Anthropic categories (automated/augmented/assistive/no-data). Top-of-page organization snapshot (description + distribution bar). Per-area snapshot with structure-grounded scope description, distribution bar, and audited commentary. Confusing made-up labels ("mixed", "strong/medium" tags on cards) removed. `audit-notes.py` introduced as a dedicated gate for per-area commentary, mirroring `audit.py` for plays. Click-to-modal on each square with chain-of-inference disclaimer; hover tooltips for quick reads.

## Anti-hallucination discipline

Three structural rules:

1. **Computed content is not written by the agent**. Tables of activity → top-K matches → metrics are produced by `match.py` reading the JSON. The agent's role is to format and narrate, not to assert numerical facts.
2. **Every numerical claim in the play is auditable** via `audit.py`. If you can't trace it back to the JSON, audit fails.
3. **Interpretive content is clearly demarcated**. Sections labeled "Actionable summary", "Operational decision", "Consequences" (or equivalent in the org's working language) are interpretation. Tables and per-activity sections with extracted metrics are computed.

The agent is only allowed to interpret in the demarcated sections, and even there every claim should cite a source (data layer, internal document, or be marked as opinion).
