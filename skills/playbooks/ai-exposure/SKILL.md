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

**Standalone HTML viewer** — the leader-facing artefact. Generated from the matches JSON plus the agent's interpretive inputs:

```bash
python3 skills/playbooks/ai-exposure/viewer.py \
  --matches <path-to-matches.json> \
  --metadata <path-to-activities-metadata.json> \
  --decisions <path-to-decisions.json> \
  --area-notes <path-to-area-notes.json> \
  --area-descriptions <path-to-area-descriptions.json> \
  --org-description-file <path-to-org-description.txt> \
  --lang en|it \
  [--task-translations <path-to-translations.json>] \
  --out <path-to-viewer.html> \
  --title "<title>"
```

Output: a single self-contained HTML file (vanilla HTML/CSS/JS, no external deps). Visual style is the Play New design system, **identical chrome to the value-map viewer**: pure white surface, editorial Inter Variable typography, hairlines, single accent. One uniform container width (1240px) is applied to every block on the page; editorial prose blocks (header, intro, decisions, footer) sit in a centered 820px column inside the 1240px container; data-heavy blocks (legend, filters, org-overview, per-area cards) span the same 820px column too. The result is a single vertical edge down the page — nothing escapes the column.

**This shape is frozen.** The reference Outline & Co. artefact is the canonical render. Any fork producing this skill must match the structure below, in this order, with no additions or omissions:

1. **Header** (820px centered): eyebrow `ai exposure` + h1 with the play title + a one-sentence lead. The lead is a punch, not a paragraph — the long explanation lives in the next block.

2. **"How to read this map" intro** (820px centered): an h2 + three short paragraphs. The intro answers three questions every leader has on first open:
   - *What is the matching doing?* — every activity matched against ~18,500 work-task descriptions in a public catalogue; colours describe how Claude was used in the public sample, not what the activity is in this organization.
   - *Why five squares per activity, not one?* — picking the single closest match is fragile because it's often only partially right. Five squares show whether the pattern holds across nearby tasks: five greens = solid read, mixed colours = noisier signal, take with caution. Anti cherry-pick.
   - *What does clicking do?* — open the matched task verbatim, the similarity, observed Claude usage, and sample size.

3. **Legend** (820px centered): four colour swatches with plain-language labels. No autonomy numbers shown here; those live in the popover.
   - 🟢 sage — Claude worked autonomously on the matched task (observed)
   - 🟣 lilac — Claude assisted under supervision (observed)
   - 🔵 slate — Claude used as a punctual tool (observed)
   - 🟤 sand — task is outside the observed sample

4. **Filters** (820px centered): search box, signal-level pills (high signal / some signal / low signal / no signal / low confidence — activity-level rollups from the per-task category counts; thresholds in §4), area filter pills. Restyled as inline editorial controls — no chunky borders.

5. **Organization snapshot** (820px centered, only when no area filter is active): the free-text `--org-description` (1-2 lines describing the organization), a counts row (N activities · N matches · avg confidence · total sample size), an org-wide horizontal distribution bar with percentages legend.

6. **Per-area sections** (when "All areas" is active, grouped by area; otherwise show only the selected area). Each section starts with a hairline and uses a **two-column area-head** at 820px:
   - Left column: area heading + scope description (structure-grounded one-liner from the area's `nodes/units/<area>.md` frontmatter `description`) + interpretive commentary note (free prose authored by the agent, audited by `audit-notes.py`).
   - Right column: distribution bar specific to that area + dist legend.
   - Below the head: grid of activity cards. Cards have a full hairline border (no border-left rule) with 18-20px padding inside.

7. **Activity card** (full-bordered, hairline frame + 4px radius, `.card-title` display weight + `.card-id` mono + `.card-desc` muted):
   - **Closest-match pull-quote**: a tinted block (`bg-alt`, no border) with the top-1 matched task verbatim, similarity %, observed autonomy /5, sample size if known, plus a fragility note when the sample is below 100 conversations.
   - **Task-square grid**: exactly `d.matches.length` squares (top-K = 5 by default → 5 squares in a row, the grid wraps after 5 if K > 5). **No padding to a fixed grid size**. Each square is colour-coded per the legend, has a hover tooltip with the matched task + similarity + observation, and is click-to-popover.
   - **Stat line**: per-category counts ("X automated · Y augmented · Z assistive · W no data") or, for low-confidence activities, the low-confidence hint instead of the grid.

8. **Decisions section** "How to read this map" (820px centered): h2 + lead + each decision rendered as `.question` (display-weight) + `.answer` (one or more paragraphs) + `.source` (mono-font citation). This is the leader-facing reading of the map. It is the load-bearing interpretive surface — the deterministic numbers come from `match.py`, the page chrome comes from the design system, but the *meaning* of the map for this org lives in this section.

9. **Footer** (820px centered): dataset reference in plain language. **Not** a technical citation line — the leader reads "Source: Anthropic's public release of how Claude was used across a sample of conversations (March 2026 release, around 18,500 work-task descriptions from the public US occupational catalog). The matching uses a multilingual sentence-similarity model. Activities are kept only when the closest match is at least 55% similar; below that the read isn't reliable." — no model names, no acronyms, no raw thresholds.

**Click on a task-square** opens a small **floating popover** (never a modal) next to the clicked square: eyebrow with the area, the activity title, the matched task, confidence + autonomy + sample size + category, and a one-sentence chain-of-inference disclaimer ("this org's activity → closest match in the public catalog → category from how Claude was used on that catalog task in the Anthropic sample. The category describes that sample, not your activity."). Esc / click outside / close button dismisses. The popover positions itself relative to the click target and clamps to the viewport edges.

**Plain-language discipline (frozen)**. No user-visible string in the rendered HTML may use any of: `O*NET`, `AEI`, `embedding`, `cosine similarity`, `MiniLM`, `paraphrase-multilingual`, `top-K`, `top-1`, `p25`, `p75`, raw autonomy thresholds (`3.21`, `3.57`), framework field names (`ai_autonomy_mean`, `ai_education_years_mean`, `penetration`). The autoresearch.py jargon-list dimension catches these on the decisions text; the same discipline applies by hand to the hardcoded prose in the viewer's STRINGS dict and the SVG diagram captions.

The viewer is the **consumer surface**: the leader/decision-maker opens it in a browser, reads the header, scans the org snapshot, drills into an area, opens individual cards, then reads the decisions section to land on what to do. The markdown play remains the audit trail; the HTML is the navigable consumer artefact.

**Decisions JSON shape** — the agent fills this as the final step of the playbook:

```json
[
  {
    "question": "Which activities are most exposed to AI delegation today, and how exposed?",
    "answer": "Multi-paragraph prose. Names this org's units and people. Ends on a Monday move, not just an observation.\n\nSecond paragraph if needed for the move.",
    "source": "outline-charter-2024 §1, §9; Anthropic Economic Index 2026-03-24"
  },
  ...
]
```

Each decision is a question the leader of this org should be able to answer after reading the map, plus the answer the play asserts. The autoresearch loop (see §11) scores these on five dimensions before a play is considered shippable.

**Reference example** — the canonical artefact for this skill is the Outline & Co. fake-org play:
- `mcp-server/test-fixtures/fake-org/plays/data/ai-exposure-outline-2026-05-07.json` — the play wrapper (matches + scope + decisions)
- `mcp-server/test-fixtures/fake-org/plays/data/ai-exposure-outline-2026-05-07.html` — the rendered viewer

Open the HTML in a browser to see exactly what this skill produces. The four decisions in that play frame displacement vs augmentation, hours reallocation across the studio's four units, and the missing context-keeping role. They mention `audience-research`, `brand-book`, `identity-system-build`, `visual-language` by name, use no AEI vocabulary in the prose, and pass autoresearch on all four deterministic dimensions.

**Optional inputs** that enrich the viewer:

- **`--metadata <list.json>`**: list of `{id, title, description, area, unit, ...}` for each activity. Title and description make cards readable instead of showing only IDs.
- **`--decisions <list.json>`**: list of `{question, answer, source}`. When supplied, renders the "How to read this map" section. **Required** for a shippable play — autoresearch fails without it.
- **`--area-descriptions <dict.json>`**: `{area_id: "high-level scope description"}`. One line per area, structure-grounded (typically copied from the area's `nodes/units/<area>.md` frontmatter `description` field).
- **`--area-notes <dict.json>`**: `{area_id: "interpretive commentary"}`. Free prose, 3-5 sentences per area, authored by the agent. Must pass `audit-notes.py` before being shipped.
- **`--org-description` / `--org-description-file`**: free text describing the organization, rendered at the top.
- **`--task-translations <dict.json>`**: `{english_task: target_language_task}` for displaying O*NET task names in the UI language. Translations can come from any pipeline (manual, LLM-assisted, machine translation) — the viewer only consumes the dict.
- **`--lang en|it`**: UI language for labels, legends, popover copy. Default `en`.

### 9. Write the play (optional — the HTML viewer is the primary consumer surface)

The leader-facing artefact is the rendered HTML from §8 (with the `decisions[]` array attached). The markdown play is now an optional companion for the audit trail; when written, its body mirrors the HTML's `decisions[]` content verbatim plus the §10 audit notes. Forks that don't ship the markdown play but do ship the HTML pass autoresearch the same way.

When a markdown play is written, place it in `org/plays/ai-exposure-<scope>-<date>.md`:

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

## Autoresearch loop

The agent runs the playbook iteratively. Each iteration produces a play; each iteration is then scored on five dimensions before the next pass — four deterministic gates plus an opt-in LLM judge.

Unlike the other playbooks, the ai-exposure pipeline's primary build output is a *list* of activity matches with no top-level wrapper. The autoresearch script therefore consumes a separate **play file** that wraps the matches with the agent's interpretation:

```json
{
  "_scope":    { ... },
  "matches":   [ ... raw activity → O*NET task matches ... ],
  "decisions": [ {"question": "...", "answer": "...", "source": "..."}, ... ]
}
```

**Score**:

```bash
python3 skills/playbooks/ai-exposure/autoresearch.py \
  --play <ai-exposure-play.json> \
  --org-dir <org-dir> \
  [--llm]
```

| Dimension | What it checks |
|---|---|
| **Recognizability** | Decisions mention named activities and units of the org by their org labels. |
| **Plain language** | No raw AEI vocabulary in decisions: `O*NET`, `ai_autonomy_mean`, `ai_education_years_mean`, `penetration`, `cosine similarity`, `embedding`. The leader reads what the numbers mean, not the field names. |
| **Decision anchoring** | At least three items in `decisions[]`, each ≥ 60 chars in `answer`, each citing a non-empty `source`. |
| **Audit grounded** | Every activity in `matches[]` resolves to a real file under `org/nodes/activities/`. The matches are the cited evidence base; the decisions can only stand if their underlying activities exist. |
| **LLM judge** *(opt-in: `--llm`)* | Claude Sonnet 4.6 scores each decision on `actionable` (yes/no), `distinctive` (high/medium/low), `readable` (yes/no). Skipped when `ANTHROPIC_API_KEY` is not set. |

The agent fills `decisions[]` as the final step of the playbook — the leader-facing reading of which activities are most exposed and how, where the displacement vs. augmentation pattern lands, which roles or units should reallocate hours, and which capabilities the org should build. Iterate until every dimension passes.
