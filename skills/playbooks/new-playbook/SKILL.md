---
name: new-playbook
description: "Meta-skill. Authors a new analytical playbook for the organization. Walks the user through five design decisions, picks the closest of the four base playbooks as scaffold, generates the new skill folder. Output: skills/playbooks/<name>/ with SKILL.md, build.py, audit.py, viewer.py wired to the structure, ready for the first run."
---

# Skill: new-playbook (meta)

The four base playbooks (`ai-exposure`, `value-map`, `reshuffle`, `world-model`) are not a closed list. Any organization that adopts the structure will want questions of its own. This skill is the recipe for adding one.

It is a meta-skill: it produces another skill. The user has a question they want to ask repeatedly about their organization. The output is a new `skills/playbooks/<name>/` folder, scaffolded from the closest existing playbook, with the question-specific shape filled in.

## Output style

All consumer-facing text the new playbook produces (the SKILL.md it generates, the audit messages, the viewer copy) follows [skills/STYLE.md](../../STYLE.md). The methodology references in the new SKILL.md follow [skills/CAPABILITIES.md](../../CAPABILITIES.md) when the playbook touches the capability stack.

## Pre-conditions

- `org/` structure healthy: lint Tier 1 and Tier 2 = 0
- The user can articulate an analytical question — not a one-shot lookup
- At least one of the four base playbooks is conceptually close to what the user wants

## What this skill outputs

- `skills/playbooks/<name>/SKILL.md` — populated from the chosen base, with the methodology rewritten to match the user's design decisions
- `skills/playbooks/<name>/build.py` — forked from the base, with TODO markers at every point that depends on the new primitive's shape
- `skills/playbooks/<name>/audit.py` — forked from the base, with audit rules expressing the evidence requirements from Q4
- `skills/playbooks/<name>/viewer.py` — forked from the base, with the per-primitive popover content from Q5 (and inheriting the frozen chrome conventions: 1240/820 column, full-bordered cards, popover-below-click, decisions section)
- `skills/ROADMAP.md` — appended with a new row, status `pending` until the first run audit-passes

The meta-skill does not produce a frozen play. Plays come from running the generated playbook against an anchor — that is the new playbook's first test.

## The five design questions

The agent asks the user these five questions before writing any file. Each answer is recorded; the answers together specify the new playbook.

### Q1 — What question does the playbook answer?

One sentence. Form: "Which / where / what is X in this organization?".

Repeatability test: the question must be one the organization will want to re-ask — every quarter, after each restructuring, when a new commitment is added. If the answer is "we ask it once and we are done", **stop**. Write the answer as a one-off play under `org/plays/data/`, not as a new skill. Skills exist because the question recurs.

### Q2 — What is the anchor?

The slice of the structure the playbook walks every time it runs.

| Anchor              | Examples                                                    |
|---------------------|-------------------------------------------------------------|
| `full-org`          | every unit, every activity. Used by `ai-exposure`, `world-model` |
| `commitment`        | a single `commitments/<id>.md` and what it reaches. Used by `value-map`, `reshuffle` |
| `unit`              | one Direzione / area / sub-team and its activities          |
| `activity-set`      | a hand-picked set of activities (e.g., all activities tagged with a given language term) |
| `stakeholder-set`   | one or more stakeholder types and the commitments that reach them |
| `other`             | declare it; the meta-skill defaults to `commitment`         |

The anchor determines which structure-walking primitives `build.py` reuses.

### Q3 — What is the primitive, and what fields does it carry?

The primitive is the unit of analysis the playbook produces one of, many of, per run. Examples:

| Playbook       | Primitive                                  |
|----------------|--------------------------------------------|
| ai-exposure    | match (activity ↔ AEI task)                |
| value-map      | component on the evolution axis            |
| reshuffle      | activity tagged with constraint type, plus engine / tool classification per AI use |
| world-model    | capability (and stakeholder, separately)   |

For the new playbook, name the primitive in 1-3 words, then list its obligatory fields. For each field declare:

- **Source**: `structure` (the field reads off a node directly), `aei` (the field reads off an Anthropic Economic Index match), `agent` (the agent fills it after looking at structure + signals), `numerical-derived` (computed from other fields).
- **Required**: yes / no.

Fields the agent fills without evidence are not allowed as primitive fields. Those are interpretation; they go in the play body, not in the structured map.

### Q4 — What proves a claim grounded?

For each obligatory field from Q3, name the evidence the audit gate will require. Patterns from the existing playbooks:

- **Structure path exists** (`world-model` capabilities cite `_structure_evidence: [...]`)
- **AEI traceability** (`ai-exposure` matches cite `_match_score`, `value-map` `ai_effect` cites `_aei`)
- **Numerical traceability** (a percentage cited in narrative must equal the count it claims)
- **External citation** (a regulatory reference cites the article)

The audit rule for the new playbook is the union of these per field. If the user wants a field that has no evidence pattern, **stop** — that is interpretation, it goes in play body not in the primitive schema.

### Q5 — Which viewer pattern? What is in the popover?

Pick one of the four base viewer patterns:

| Pattern               | What it shows                                              | Base playbook |
|-----------------------|------------------------------------------------------------|---------------|
| Tabular distribution  | grid + bucket distribution + per-area summary              | ai-exposure   |
| 2-axis map            | components on evolution × visibility, click-for-detail     | value-map     |
| Bundle bands          | activities grouped by constraint, AI-use badges per activity| reshuffle    |
| Layered stack         | capabilities + world-model knowledge + intelligence-layer compositions + interfaces, click-for-detail on every card | world-model |

For the chosen pattern, list which fields render on the card (the always-visible label) and which fields render in the **popover** (the small click-to-detail card that opens next to the click target — never a full-screen modal). The audit gate later verifies the viewer references only fields that actually exist on the primitive.

**Frozen viewer conventions every new playbook inherits**:

- One uniform container width (1240px), with editorial blocks (header, intro, decisions, footer) constrained to a centered 820px column inside it. Data zones can use the same 820px column or fall back to the wider 1240px when the data is dense.
- **Header pattern**: eyebrow `<playbook-name>` + h1 (the artefact title) + lead (one sentence, what this map is for).
- **Decisions section** at the bottom, titled "How to read this map", with `.question` + `.answer` (one or more paragraphs) + `.source` citation per decision. The load-bearing interpretive surface — the deterministic numbers come from `build.py` / `match.py`, the page chrome from the design system, but the *meaning* of the artefact for this org lives in this section.
- **Visual code (frozen)**:
  - Shape = kind (every clickable item of the same kind shares the same shape: cards, circles, diamonds...). The shape never changes when an item is differentiated/emerging — only the colour does.
  - Colour = state / role (hairline border = standard / commodity; coral border = differentiated / moat / emerging).
  - **Full-bordered cards**, no left-rule cards. Every clickable card has a hairline border that darkens to `--fg` on hover.
- **Click → popover**, never a full-screen modal. The popover opens **below** the clicked element, **centered horizontally on it**, flips above when there's no room below, and clamps to viewport edges. Esc / click outside / close button dismisses.
- **Plain-language discipline**: framework primitive names are fine as labels (Stakeholders, Capabilities, Genesis/Custom/Product/Commodity); paraphrased into prose they become jargon and must be replaced. See [skills/STYLE.md](../../STYLE.md) for the full avoid-list.
- **Conditional voice for emerging items**: any rationale on a `is_new` component, a `new_end_users` entry, or a piece-to-build is written with `if / would / could / depends on`, never `when / will / makes`. The map suggests preconditions are approaching; whether to build the thing stays the org's choice.
- **`decisions[]` field on the JSON** is required for a shippable play. The `--decisions` CLI flag (or, for ai-exposure, the wrapper `{matches, decisions}` shape) lets the agent supply them at render time. Without `decisions[]`, autoresearch fails the decision-anchoring dimension.

The new playbook's `viewer.py` forks one of the four base viewers and inherits all of the above. Diverging from any of them is a deliberate design choice that has to be argued.

## Picking the base playbook

The base is the playbook the new one forks from. Same anchor type or same primitive grain is the strongest signal.

| If the user's playbook... | Base           |
|---------------------------|----------------|
| scores or classifies every activity in the org | ai-exposure |
| places components on a 2D plane                 | value-map   |
| groups activities of a slice by a constraint type and overlays AI engines/tools | reshuffle |
| decomposes the whole org structurally           | world-model |
| does not match the above                        | value-map (most generic anchored pattern; default) |

If two bases are equally close, prefer the one whose viewer pattern matches Q5.

## Workflow

### 1. Interview

Ask Q1 → Q5 in order. Record the user's answers verbatim. Do not write any file yet.

### 2. Audit the design

Two checks before writing anything:

- **Repeatability check** (Q1): is this a recurring question or a one-shot? If one-shot, refuse skill creation. Suggest a one-off play instead.
- **Evidence check** (Q3 + Q4): does every obligatory field have an evidence source? If a field has no audit rule, refuse it. Suggest moving it to the play body as agent prose.

If either check fails, return to interview, do not proceed.

### 3. Pick the base

Apply the base-picking table. State the choice and the reason in one sentence to the user. The user can override.

### 4. Scaffold the new folder

Create `skills/playbooks/<name>/` with:

- `SKILL.md` — copied from the base, then rewritten:
  - frontmatter `name` and `description` from Q1
  - **Output style** section: keep as-is (always references STYLE.md and, when relevant, CAPABILITIES.md)
  - **Pre-conditions** section: adapt to the anchor type from Q2
  - **Workflow** section: rewrite step-by-step against Q3 (primitive schema), Q4 (evidence per field), Q5 (viewer)
  - **Audit gate** section: list one rule per obligatory field
  - **Method limits** section: from the user's own statement of what the playbook cannot say
  - **When to run this skill** section: tie to the structure state required (lint clean, optional prerequisite playbooks)

- `build.py` — copied from the base, with TODO markers at:
  - the structure-walking call (if anchor differs from base)
  - the primitive-schema dictionary (replace with Q3 fields)
  - the output JSON shape

- `audit.py` — copied from the base, with TODO markers at:
  - the field-presence checks (replace with Q4 rules)
  - the numerical-traceability checks (keep if the new playbook has counted narrative)
  - the structure-existence checks (always kept)

- `viewer.py` — copied from the base, with TODO markers at:
  - the primitive-rendering function (replace fields per Q5)
  - the popover content (per Q5 — never a modal)

Each TODO marker has the form `# TODO(new-playbook): replace with <field>` — searchable, reviewable, removable when filled.

### 5. Update ROADMAP.md

Append a row to the **Status** table:

```
| <next-#> | <name> | <kind> | <source theory or "none — composed from base"> | pending |
```

The playbook stays `pending` until the first run audit-passes against a real anchor. At that point the user (or agent) flips it to `done`.

### 6. First run is the test

The meta-skill does not run the new playbook itself. The user picks an anchor (the smallest meaningful one) and runs:

```bash
python3 skills/playbooks/<name>/build.py --anchor <id> --org-dir org > org/plays/data/<name>-<anchor>-<date>.json
python3 skills/playbooks/<name>/audit.py --map org/plays/data/<name>-<anchor>-<date>.json --org-dir org
python3 skills/playbooks/<name>/viewer.py --map ... --html ...
```

If the audit fails, the playbook is not real yet. The TODO markers point at the gaps.

If the audit passes and the viewer renders, the playbook is real. ROADMAP status flips to `done`.

## Audit gate of the meta-skill itself

Before committing the generated folder, the meta-skill verifies:

1. `SKILL.md` exists with frontmatter `name` and `description` matching the folder name.
2. `build.py` imports structure primitives from one of the four base playbooks (no reinvention of structure access).
3. `audit.py` declares at least one check per obligatory field from Q3.
4. `viewer.py` references only fields present in the Q3 schema.
5. `ROADMAP.md` has the new row.
6. No TODO marker is silently filled with placeholder content. TODO markers are kept for the user to address; they are not pretend-implementations.

If any check fails, the meta-skill removes the half-written folder and reports the failure. It does not leave a partial scaffold behind.

## Method limits

- **The meta-skill does not invent the question.** It records what the user said in Q1 and the SKILL.md it writes paraphrases that exactly. If the user gave a vague question, the SKILL.md will be vague.
- **The meta-skill does not invent evidence rules.** Q4 is the user's. The audit.py reflects what the user asked to enforce.
- **The meta-skill does not run the new playbook.** First-run validation is on the user.
- **The meta-skill cannot rescue a bad design.** If Q1 fails the repeatability test or Q3-Q4 fails the evidence test, the only correct output is to stop and explain why.
- **A new playbook is a maintenance commitment.** Every playbook adds an audit script that must keep passing as structure evolves. The meta-skill warns the user before scaffolding the fifth, sixth, seventh playbook: marginal value drops fast past four.

## Anti-hallucination discipline

Three structural rules.

1. **No silent placeholders.** Every TODO marker in the generated files is visible and searchable. The meta-skill never fills a TODO with content the user did not give.
2. **No new structure primitives.** The generated `build.py` reuses structure-walking helpers from the base. New primitives mean the meta-skill is overstepping; it stops and asks.
3. **No new viewer pattern.** The generated `viewer.py` picks one of the four established patterns. A genuinely new pattern is a project-level decision, not a meta-skill decision.

## When NOT to use this skill

- **The question is one-shot.** Write a play directly under `org/plays/data/` without a skill folder.
- **The question is the same as an existing playbook with a different filter or anchor.** Run the existing playbook with that anchor instead. Do not fork.
- **The question is about structure health.** Use the `lint` skill, not `new-playbook`.
- **The question requires altering the structure.** Use `org_write_node` directly, plus the `ingest` skill if the change comes from a source.

## References

- [skills/ROADMAP.md](../../ROADMAP.md) — the four base playbooks and their scope
- [skills/CAPABILITIES.md](../../CAPABILITIES.md) — methodology when the new playbook touches the capability stack
- [skills/STYLE.md](../../STYLE.md) — output language for the new playbook's text
- [skills/playbooks/ai-exposure/SKILL.md](../ai-exposure/SKILL.md) — base for activity-grain scoring
- [skills/playbooks/value-map/SKILL.md](../value-map/SKILL.md) — base for 2-axis component maps
- [skills/playbooks/reshuffle/SKILL.md](../reshuffle/SKILL.md) — base for constraint-bundle analysis
- [skills/playbooks/world-model/SKILL.md](../world-model/SKILL.md) — base for structural decomposition
