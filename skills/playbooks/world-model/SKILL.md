---
name: world-model
description: "Read an organization through the four-part frame from Block (Dorsey + Botha, March 2026): capabilities, world model, intelligence layer, interfaces. Output: a frozen analysis with the org's exposed and latent capabilities, the signals that feed its understanding of operations and customers, the compositions that an intelligence layer could perform, the interfaces that deliver them, and the failure signals that constitute the future roadmap."
---

# Playbook: world-model

## How this playbook is run (read this first)

This playbook **must** produce a persistent file artefact under `org/plays/data/`, not an in-chat widget.

**Required tooling**: `org_play_run` (mcp tool). Two calls per run:

1. `org_play_run(playbook="world-model", mode="build", scope=<unit-id>?)` → returns the skeleton (capability candidates, stakeholder shells, AEI summary) from `build.py`. Read `org_skill_read("CAPABILITIES")` and `org_skill_read("STYLE")` before filling.
2. `org_play_run(playbook="world-model", mode="render", json_content=<filled JSON>)` → writes JSON, runs `audit.py`, runs `viewer.py`, returns artefact paths and audit summary.

**Do not** use Claude Desktop's inline `visualize` / `show_widget` / artifact features. They are ephemeral, bypass the audit gate, and don't use the bundled design system. The HTML returned by `org_play_run` mode=render is the canonical visualization.

**Do not** hand-write a markdown play file under `plays/`. The JSON + HTML pair under `plays/data/` is the play.

If `org_play_run` errors, report verbatim and stop. Do not fall back to an in-chat widget.

**How to present the result — strict protocol**:

1. As soon as render returns `status: "ok"`, call `org_open` immediately with `artefacts.html` (relative path). Opens in default browser.
2. Paste the response `presentation_markdown` field **verbatim**. It is already a `[text](file://...)` Markdown link; do not wrap, quote, or rephrase.
3. Add one short sentence of context (e.g. "8 capability identificate (6 moat, 2 commodity), 35 stakeholder con segnale onesto, 7 segnali di fallimento, audit pass").
4. Do NOT inline-render any custom widget.

## Output style

All consumer-facing text produced by this skill (play body, viewer copy, modals, interpretive narratives) must follow the project style charter in [skills/STYLE.md](../../STYLE.md). The methodology behind the analysis is in [skills/CAPABILITIES.md](../../CAPABILITIES.md), which the SKILL.md and the agent both reference.

For an organization in scope, the skill produces a structured analysis of:

1. **Capabilities**: the atomic invocable functions of the organization. Each has a contract (input, output, target SLO, regulatory constraints) and is tagged moat or commodity.
2. **World model — company side**: how the organization understands its own operations, performance, priorities. Built from structure observations.
3. **World model — customer side**: per-stakeholder representation built from the most honest signals the organization records (transactions, recurring choices, declared intentions). Often fragmented across teams; the analysis surfaces the fragmentation.
4. **Intelligence layer**: the (typically not-yet-existing) component that composes capabilities into solutions for specific stakeholders at specific moments. The analysis lists current compositions that today are human-mediated and could become systemic.
5. **Interfaces**: delivery surfaces (web, app, physical channels, telephone, post). Not where value is created; where it's delivered.
6. **Failure signals**: compositions an intelligence layer would attempt that fail because a capability is missing. Each failure signal is a roadmap item.

The deliverable is a frozen `play` in `org/plays/world-model-<scope>-<date>.md` with companion JSON and an interactive HTML viewer that renders the four parts as a layered stack.

## What this skill does that's different

This skill differs from the previous three:

- **ai-exposure** maps activities to AEI tasks, classifies AI penetration. Activity-grain.
- **value-map** maps a value chain on the evolution-visibility plane. Component-grain, anchored on a commitment.
- **reshuffle** diagnoses how AI changes the bundle structure of a slice. Bundle-grain, with constraint analysis.
- **world-model** redescribes the entire organization as a graph of invocable capabilities + a representation system + a composer + delivery surfaces. Organization-grain, structural.

The first three help an organization understand specific aspects of itself. This skill rewrites the operating model.

## Pre-conditions

- Structure `org/` healthy (lint Tier 1 + Tier 2 = 0).
- Activities, units, commitments, stakeholders fully populated.
- Optional but recommended: completed `ai-exposure` matches and at least one `value-map` play, to inform the customer-side world model and the failure-signal analysis.
- The agent has read [skills/CAPABILITIES.md](../../CAPABILITIES.md). The methodology there is non-negotiable for this skill.

## Workflow

### 0. Canonical invocation via mcp (preferred)

When the bundled mcp server is available, launch this playbook via `org_play_run`:

1. Call `org_play_run` with `playbook="world-model"`, `mode="build"`, `scope=<unit-id>` (omit for full org). The tool runs `build.py` and returns the skeleton inline (capability candidates, stakeholder shells, AEI evidence).
2. Read the skeleton; for every capability fill the contract (input/output/SLO/regulatory/invocation_modality), the moat/commodity classification, the structure evidence; for every stakeholder fill the bidirectional fields per §3 below; surface failure signals per §6. Cite structure.
3. Call `org_play_run` again with `mode="render"` and `json_content=<filled JSON>`. The tool writes to `plays/data/`, runs `audit.py`, runs `viewer.py`, returns artefact paths plus audit summary.
4. Append a log line via `org_log_append`.

Do **not** hand-write a markdown play under `plays/` for this flow — the JSON + HTML in `plays/data/` is the artefact.

The cross-cutting docs `CAPABILITIES.md` (the five-property frame) and `STYLE.md` (output language rules) are readable via `org_skill_read("CAPABILITIES")` and `org_skill_read("STYLE")` — read both before filling the skeleton.

If `org_play_run` is not available (older mcp build), fall back to the manual steps below.

### 1. Identify capabilities

Apply the five-property test from CAPABILITIES.md to candidate functions in the organization:

1. Invocable (declared way to activate).
2. Produces structured output (verifiable result, not opinion).
3. Atomic (right granularity).
4. Hard to acquire (regulation, network effects, expertise, time).
5. Composable (with other capabilities, into different flows).

Expected count: 5 to 15 for a medium organization. If you find 50, you are calling capabilities things that are not capabilities. The four-question pragmatic test from CAPABILITIES.md is the discipline.

For each capability, record:
- `name` (verb-object form: `process-donation`, `review-proposal`, `execute-legacy`)
- `description` (what it does, plain language, no jargon)
- `input`, `output`, `slo_targets`, `regulatory_constraints`, `invocation_modality`
- `is_callable_by`: list of stakeholder types
- `composes_with`: ids of other capabilities it pairs with in known flows
- `current_owners`: structure units / Direzioni that host the activities composing it
- `moat_grade`: `moat` (hard to acquire, network/regulatory effect) vs `commodity` (necessary but not differentiating)
- `_structure_evidence`: paths to structure files supporting the existence of the capability

### 2. Map the company-side world model

For each structure observation type the organization records about itself, declare:
- What it captures (which dimension of operations)
- Where it lives (which structure files, which systems)
- Maturity (high / medium / low)
- Gaps (what the current structure can't yet describe)

The output is a list of "what the organization understands about itself" entries. Each must cite structure.

### 3. Map the customer-side world model

For each stakeholder type the organization interacts with, fill the following fields:

- `type`: short label (e.g., "individual donor", "researcher", "partner institution").
- `description`: 1-2 sentences in plain language explaining what kind of stakeholder this is, written for a reader who doesn't know the organization. Avoid jargon and avoid restating the type label.
- `what_they_get_from_org`: what value the stakeholder receives from the organization (the "user" side of the bidirectional relationship). 1 sentence.
- `what_they_contribute_back`: what signal, work, or value the stakeholder feeds back to the organization (the "contributor" side, per the rule in CAPABILITIES.md that every stakeholder is also contributor). 1 sentence.
- `honest_signal`: the most honest signal the organization records about this stakeholder type (transactions, recurring choices, declared intentions, completed actions, not stated preferences). 1 sentence naming the signal and its source.
- `current_maturity`: `high` | `medium` | `low`. How well the organization currently represents this stakeholder type internally.
- `fragmentation`: 1-2 sentences explaining which teams or systems hold which slice of the stakeholder representation, and what's missing for a unified per-stakeholder view. If the representation is unified, say so explicitly.

The output: per-stakeholder-type representation status with rich narrative. Most organizations score `medium` or `low` on `current_maturity` even when they think they score high.

### 4. Surface the intelligence layer (current and potential)

Currently, organizations compose capabilities through human-mediated coordination (cross-team meetings, fascicoli, recurring committees). For the analysis:

- **Current compositions, human-mediated**: list 5 to 10 cases where human coordinators today compose capabilities to address stakeholder situations. For each, name the stakeholder signal that triggers the composition, the capabilities composed, the failure modes.
- **Potential compositions**: 5 to 10 cases where the intelligence layer (if it existed) could compose capabilities automatically given a world-model signal. For each, name the signal, the capabilities, the precondition (which world-model maturity it requires).

The intelligence layer is rarely a thing today; this section is mostly diagnostic.

### 5. Map interfaces

List delivery surfaces (web, app, telephone, post, physical channels, in-person events). For each, name which capabilities it surfaces today.

Interfaces are not where value is created. The section exists to make the layer separation explicit.

### 6. Compute failure signals

A failure signal is: a stakeholder request that an intelligence layer would attempt to compose, and that fails because at least one capability is missing.

For each failure signal:
- **Trigger**: the stakeholder situation or signal that generates the request.
- **Composition attempted**: which capabilities the layer would chain.
- **What's missing**: the capability that doesn't exist yet (named as a verb-object).
- **Structure evidence**: which structure file or AEI signal indicates the request would actually arise.

Failure signals are the roadmap. They are concrete; each should map to a specific missing capability.

### 7. Audit

```bash
python3 skills/playbooks/world-model/audit.py \
  --map <world-model.json> \
  --org-dir org
```

The audit verifies:
1. Each capability passes the five-property test (each property explicitly checked).
2. Each capability has structure evidence (citation paths exist).
3. Each capability has at least three stakeholder types in `is_callable_by` (the three-actors rule).
4. Each capability has a non-empty contract (input, output, slo_targets, invocation_modality).
5. Each capability is tagged moat or commodity, with rationale.
6. Each customer-side world model entry cites a stakeholder type and an honest signal.
7. Each failure signal names a missing capability and cites a structure or AEI source.
8. No capability candidate is in fact a governance organ, an asset, an aspiration, or a function of staff (rule from CAPABILITIES.md).

### 8. Visualize

```bash
python3 skills/playbooks/world-model/viewer.py \
  --map <world-model.json> \
  --html <world-model.html>
```

The viewer renders the organization as a layered stack:

- Top band: stakeholder types as circles.
- Second band: interfaces as labeled rectangles, connected to stakeholders that use them.
- Third band: intelligence layer as a horizontal panel listing current human-mediated compositions and potential automated ones.
- Fourth band: world model (company-side and customer-side panels).
- Bottom band: capability cards in a grid, each with name, moat indicator, current owners, contract excerpt.
- Right side: failure signals panel, each card linking to the missing capability.

Click any element for full detail in a modal. Apply the style charter: every term defined inline, no acronyms left unexplained, every number declares its scale.

### 9. Write the play

In `org/plays/world-model-<scope>-<date>.md`. Frontmatter:

```yaml
---
id: world-model-<scope>-<date>
type: play
playbook: world-model
target: <scope>
dated: <YYYY-MM-DD>
frozen: true
sources: [<structure files cited>]
references:
  - methodology: skills/CAPABILITIES.md
  - builder: skills/playbooks/world-model/build.py
  - viewer: skills/playbooks/world-model/viewer.py
  - audit: skills/playbooks/world-model/audit.py
  - map_json: org/plays/data/world-model-<scope>-<date>.json
  - map_html: org/plays/data/world-model-<scope>-<date>.html
---
```

Body sections:
1. **Capabilities**: per-capability table with contract excerpts.
2. **World model — company side**: what the organization understands about itself, with structure citations.
3. **World model — customer side**: per-stakeholder representation status, with fragmentation explicit.
4. **Intelligence layer**: current human-mediated compositions, potential automatable ones.
5. **Interfaces**: delivery surfaces, with capabilities surfaced.
6. **Failure signals**: the roadmap. Each signal cited.
7. **Operational consequences**: what to do with the analysis. Concrete.
8. **Method limits**: what the analysis cannot say.
9. **Cross-references**.

### 10. Lint + log

`python3 lint.py` must pass. `org_log_append` with a one-line summary.

## Method limits

- **Capability identification is interpretive**. The five-property test reduces ambiguity but two reasonable agents can disagree at the margins. The audit gate enforces evidence per capability; choices at the margin are recorded as such in the play.
- **Customer-side signal richness varies by sector**. Block has transactional data on millions of users every day. Most non-profit organizations have less continuous signal. The skill must adapt the customer-side world model to whatever signal density the structure actually has.
- **The intelligence layer is mostly hypothetical for most organizations today**. The skill describes potential compositions; deploying them is not in scope.
- **The frame assumes structural willingness**. An organization unwilling to question Direzione boundaries can read the analysis as a thought experiment. The same analysis applied with structural intent is a different conversation.
- **Failure signals are a partial roadmap, not the full one**. They surface the compositions the layer can't make. They don't capture work that would never trigger composition (pure infrastructure, regulatory upkeep, etc.).

## Anti-hallucination discipline

Three structural rules:

1. Every capability cites structure. The audit gate refuses capabilities without structure evidence paths.
2. Every customer-world-model entry names the honest signal and where it lives. No hand-wave "we have data".
3. Failure signals are concrete. Each names the trigger, the composition attempted, the missing capability, and the structure source for the request being plausible.

## When to run this skill

After at least one ai-exposure pass and ideally one value-map play. The structural assessment benefits from the activity-level and value-chain views as priors.

For a first run, scope = whole organization. Per-Direzione scoping is possible but loses the cross-Direzione capabilities (which are the most informative ones, often).

## Autoresearch loop

The agent runs the playbook iteratively. Each iteration produces a play; each iteration is then scored on five dimensions before the next pass — four deterministic gates plus an opt-in LLM judge.

**Score**:

```bash
python3 skills/playbooks/world-model/autoresearch.py \
  --map <world-model.json> \
  --org-dir <org-dir> \
  [--llm]
```

| Dimension | What it checks |
|---|---|
| **Recognizability** | Decisions mention specific units / activities / stakeholders / capabilities of the org by name. |
| **Plain language** | No paraphrased framework jargon: `world model`, `capability stack`, `intelligence layer`, `failure signal`, `moat`, `judgment density`, etc. |
| **Decision anchoring** | At least three items in `decisions[]`, each ≥ 60 chars in `answer`, each citing a non-empty `source`. |
| **Audit grounded** | Every capability / interface / failure-signal that claims a `_structure_id` resolves to a real file under `org/`. |
| **LLM judge** *(opt-in: `--llm`)* | Claude Sonnet 4.6 scores each decision on `actionable` (yes/no), `distinctive` (high/medium/low), `readable` (yes/no). Skipped when `ANTHROPIC_API_KEY` is not set. |

The play's primary interpretive surface is the top-level `decisions[]` array — the leader-facing reading of which capabilities are moat vs commodity, which interfaces are real vs aspirational, and which failure-signals indicate a missing capability the org should build. The agent fills this array as the final step of the playbook, then iterates against the autoresearch output until every dimension passes.

**Reference example** — the canonical artefact for this skill is the Outline & Co. fake-org play:

- `mcp-server/test-fixtures/fake-org/plays/data/world-model-outline-2026-05-07.json` — the source JSON with capabilities, interfaces, intelligence-layer compositions, world-model observations, failure-signals, and `decisions[]`
- `mcp-server/test-fixtures/fake-org/plays/data/world-model-outline-2026-05-07.html` — the rendered viewer

Open the HTML in a browser to see exactly what this skill produces. The play covers the studio's whole-org structure: 7 capabilities (3 differentiated, 4 standard), 4 touchpoints, 3 currently-human-mediated compositions + 2 potentially automatic, knowledge observations on the org and on each stakeholder type, and 3 failure-signals that all converge on the same missing capability — a context-keeping practice the studio doesn't yet have anyone owning. Three leader-facing decisions name Marco, Lena, and Tomás by role and the studio's units by name.
