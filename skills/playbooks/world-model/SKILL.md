---
name: world-model
description: "Read an organization through the four-part frame from Block (Dorsey + Botha, March 2026): capabilities, world model, intelligence layer, interfaces. Output: a frozen analysis describing how the three structural layers (interfaces, capabilities, world model) currently operate in the org, and what it would take to actually run the loop. Three structural moves: turn interfaces into signal collection, reorganize around invokable capabilities, build the memory that decides."
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

All consumer-facing text produced by this skill (play body, viewer copy, modals, interpretive narratives) **must** follow the project style charter in [skills/STYLE.md](../../STYLE.md). The agent **must** run the self-check at the end of STYLE.md before saving any prose. The methodology behind the analysis is in [skills/CAPABILITIES.md](../../CAPABILITIES.md), starting from the *"The move"* section.

The skill produces, for an organization in scope, a reading of where it sits along the move from hierarchy to intelligence. For each of the three layers, the play describes the today state and the after state. The gap between them is what the intelligence layer would close.

1. **Interfaces**: delivery surfaces (web, app, physical channels, telephone, post, in-person events). For each, today the surface mostly delivers; after the move it also captures signal. The play names which signals each interface lets pass through unrecorded today.
2. **Capabilities**: the org's invocable functions. Each has a contract (input, output, SLO, regulatory constraints, invocation modality) and a DRI. Today most capabilities are crafts embedded in named people; after the move the person stays as DRI but a wrapper exposes the capability to invocation by the intelligence layer or by external actors. The play lists capabilities and the wrapper criteria each one already satisfies vs still misses.
3. **World model**: the org's living memory. Operational metrics, per-caller representations, the capability registry itself, the log of captured signals (both successful invocations and unanswered requests). Today most of it is implicit, fragmented across heads and files. After the move it is a system that auto-updates from each loop turn.
4. **Intelligence layer**: the runtime that connects the three. Today usually doesn't exist as a system; humans (often a single founder or coordinator) do the routing in their head. The play lists current human-mediated compositions and the compositions that would emerge once the runtime is in place.
5. **Roadmap**: the queryable subset of captured signals with no current composition. Surfaces from running the loop, not from a planning artefact.

The deliverable is a frozen `play` in `org/plays/world-model-<scope>-<date>.md` with companion JSON and an interactive HTML viewer that renders the three layers, the runtime as a connective annotation, and the loop as overlay.

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
- Optional but recommended: completed `ai-exposure` matches and at least one `value-map` play, to inform the customer-side world model and the piece to build analysis.
- The agent has read [skills/CAPABILITIES.md](../../CAPABILITIES.md). The methodology there is non-negotiable for this skill.

## Workflow

### 0. Canonical invocation via mcp (preferred)

When the bundled mcp server is available, launch this playbook via `org_play_run`:

1. Call `org_play_run` with `playbook="world-model"`, `mode="build"`, `scope=<unit-id>` (omit for full org). The tool runs `build.py` and returns the skeleton inline (capability candidates, stakeholder shells, AEI evidence).
2. Read the skeleton; for every capability fill the contract (input/output/SLO/regulatory/invocation_modality), the moat/commodity classification, the structure evidence; for every stakeholder fill the bidirectional fields per §3 below; surface pieces to build per §6. Cite structure.
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

### 6. Surface the roadmap

The roadmap is not a separate planning artefact. It surfaces from the loop: the subset of captured signals that *no current composition can fulfil*. Each one names a request the org would already receive (or already receives, handled badly) and the missing capability that would close it.

For each roadmap entry:
- **Trigger**: the request or signal that generates it. Cite the structure observation that says this request actually arises (a commitment, an activity body that names the situation, an AEI signal).
- **Composition attempted**: the capabilities the intelligence layer would chain (existing or partial) to handle the request.
- **Missing capability**: the one that isn't there, named as a verb-object (e.g., `read-engagement-memory`, `recognize-scope-drift`).
- **What it would take**: a 1-2 sentence sketch of what would need to exist for the missing capability to ship its contract.

The agent does not invent roadmap entries. They emerge from running the diagnostic: which interfaces don't capture the signals they could, which capabilities don't yet have wrappers, where the world model is implicit. Each entry must trace to a concrete observation in the structure or in the captured-signals log.

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
5. Each capability has a named DRI (single person, not a list) and a wrapper status indicating which of the five wrapper criteria are met today.
6. Each capability is tagged moat or commodity, with rationale.
7. Each interface entry has both a today-state (what it delivers) and an after-state hint (which signals it would capture if transformed).
8. Each world-model entry, whether operational, per-caller, or captured-signals, cites the structure source where the data lives today (or "implicit, in heads" if explicitly fragmented).
9. Each roadmap entry names a missing capability in verb-object form and cites a structure observation or captured signal that says the request arises.
10. No capability candidate is in fact a governance organ, an asset, an aspiration, or a staff function (rule from CAPABILITIES.md).

### 8. Visualize

```bash
python3 skills/playbooks/world-model/viewer.py \
  --map <world-model.json> \
  --html <world-model.html> \
  [--decisions <decisions.json>]
```

The HTML is the **primary consumer artefact**, a self-contained interactive document the leader opens in a browser. **The shape is frozen**: the canonical Outline & Co. play under `mcp-server/test-fixtures/sample-org/plays/data/world-model-outline-2026-05-07.html` is the reference render. Every block on the page lives in the same centered 820px column inside the 1240px container; nothing escapes the editorial grid. Page structure, in order:

1. **Header** (820px centered): eyebrow `world model` + h1 title + one-paragraph lead naming the move.
2. **Intro** (820px centered): one paragraph framing the loop the page describes. Plain-language description of how interfaces, capabilities, and world model interact when a request arrives.
3. **The three layers** (820px centered):
   - **Interfaces**: row of cards. Each card names the surface and shows two states (today / after) explaining what the surface delivers today and what signals it would collect after the transformation.
   - **Capabilities**: visually dominant block, largest card area. Grid of cards, roughly 3 per row. Each card shows: the contract (input → output in monospace), who runs it today, the differentiated/standard tag, and a row of five dots showing how callable the function is today (filled = met, half = partial, empty = not yet). Coral border = differentiated craft. Hairline border = standard practice. No left-rule cards.
   - **World model**: wide block at the bottom with two sub-sections side by side. *Organization side* (what the studio knows about its own work: operations, performance, priorities). *Stakeholder side* (per-stakeholder-type representation, with fragmentation explicit). Each item is clickable for the full content.
4. **Intelligence layer**: between Capabilities and World model, a thin annotation band (italic, no background fill) describing where the AI middle layer sits and what it does in plain language. A connective label, not a full block.

**No stakeholder band.** Stakeholders appear inside the stakeholder-side sub-section of the world model. They are not a separate layer.

**No on-page roadmap or decisions sections.** The page itself is the structural read (interfaces / capabilities / world model). The leader-facing reading (what to do, what to decide) lives in the Analysis modal.

### Analysis modal (top-right CTA, opens the leader-facing reading)

1. **Headline**: action-oriented, names the move the studio would make.
2. **The move, in three steps**: numbered list. (1) Make interfaces collect what comes back (the implication: stop delivering finished products, start delivering tools the client uses). (2) Reorganize around the studio's invokable functions. (3) Build the memory the studio uses to decide.
3. **Decisions** (3+): each rendered as `<h3>question</h3>` + `<p>answer</p>` paragraphs + `<p class="source">` citation.

The roadmap (the list of missing capabilities the loop would surface today) is deliberately not surfaced as a section. The framework's claim is that the roadmap emerges from running the loop, not from a list compiled today. Showing it would invite planning-table thinking, the opposite of the move.

**Visual code (frozen)**:

- **Shape = kind**: full-border cards for every content-rich element on the page (interface, capability, world-model entry). All clickable items share the same shape and the same hover signal (border darkens to `--ink`).
- **Colour = state**: hairline border = standard practice. Coral border (`--k-commitment`) = differentiated craft (capability) or emerging item (`is_new`). The shape never changes when an item is differentiated or emerging; only the border colour does.
- **No left-rule cards**. Every card has a full hairline border.

**Click on any clickable element** opens a small floating popover (never a modal). The popover opens below the clicked element, centered horizontally on it, and flips above when there isn't room. Always clamped inside the viewport. Z-index sits above the Analysis modal scrim so popovers triggered inside Analysis stay visible. The popover contains:

- Eyebrow with the kind in one word: "differentiated", "standard", "interface".
- The full label as h3 (capability names sentence-cased: `define-positioning` → `Define positioning`).
- A description paragraph.
- Per-kind sections. For capabilities: the contract (`Takes` / `Returns` / `Reliability target` / `How called`), `Who's on the hook today`, `Who can ask for it`, `Used together with`, `How callable today` (the five wrapper criteria each rendered in plain English), and `Why differentiated` (moat-only). For stakeholders: what-they-get / what-they-give-back / honest-signal / fragmentation. For operational observations: where-it-lives-today / maturity / what's-still-missing.
- Footer citation: the structure source path(s).

Every clickable element on the page (capability card, interface card, world-model list item) opens a popover. Esc / click outside / close button dismisses.

**Plain-language discipline (frozen)**. The framework's layer names (Stakeholders, Interfaces, Intelligence layer, World model, Capabilities) stay as the framework defines them — they are the primitives, not jargon. Below each layer name, the hint paragraph translates the primitive into plain English. **Inside the popover and the prose**, no framework vocabulary leaks. Words to never use in user-visible strings:

- `moat` → "differentiated"
- `commodity` → "standard"
- `judgment density`, `capability stack` → never appear
- `coordination tax` → "the cost of keeping everyone aligned" or "alignment cost"
- `piece to build` → "a piece to build" or "a place where the response would fall short"
- `the structure is thin` → "what to build next" or "the pieces that aren't there yet" — never the word `thin` in user-visible prose. It's metaphorical and the leader stops on it.

Decisions are reviewed by `autoresearch.py` against the deterministic jargon list; the editorial words above are caught by hand on every release.

**`--decisions <list.json>`** merges a JSON list of `{question, answer, source}` into the map's `decisions[]` field before rendering. **Required** for a shippable play — autoresearch fails without it.

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
6. **Pieces to build**: the roadmap. Each signal cited.
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
- **Pieces to build are a partial roadmap, not the full one**. They surface the compositions the layer can't make. They don't capture work that would never trigger composition (pure infrastructure, regulatory upkeep, etc.).

## Anti-hallucination discipline

Three structural rules:

1. Every capability cites structure. The audit gate refuses capabilities without structure evidence paths.
2. Every customer-world-model entry names the honest signal and where it lives. No hand-wave "we have data".
3. Pieces to build are concrete. Each names the trigger, the composition attempted, the missing capability, and the structure source for the request being plausible.

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
| **Plain language** | No paraphrased framework jargon: `world model`, `capability stack`, `intelligence layer`, `piece to build`, `moat`, `judgment density`, etc. |
| **Decision anchoring** | At least three items in `decisions[]`, each ≥ 60 chars in `answer`, each citing a non-empty `source`. |
| **Audit grounded** | Every capability / interface / piece to build that claims a `_structure_id` resolves to a real file under `org/`. |
| **LLM judge** *(opt-in: `--llm`)* | Claude Sonnet 4.6 scores each decision on `actionable` (yes/no), `distinctive` (high/medium/low), `readable` (yes/no). Skipped when `ANTHROPIC_API_KEY` is not set. |

The play's primary interpretive surface is the top-level `decisions[]` array — the leader-facing reading of which capabilities are moat vs commodity, which interfaces are real vs aspirational, and which pieces to build indicate a missing capability the org should build. The agent fills this array as the final step of the playbook, then iterates against the autoresearch output until every dimension passes.

**Reference example** — the canonical artefact for this skill is the Outline & Co. sample-org play:

- `mcp-server/test-fixtures/sample-org/plays/data/world-model-outline-2026-05-07.json` — the source JSON with capabilities, interfaces, intelligence-layer compositions, world-model observations, pieces to build, and `decisions[]`
- `mcp-server/test-fixtures/sample-org/plays/data/world-model-outline-2026-05-07.html` — the rendered viewer

Open the HTML in a browser to see exactly what this skill produces. The play covers the studio's whole-org structure: 9 capabilities (3 differentiated craft owned by Marco / Lena, 6 standard practice the category shares), 4 interfaces (each with a today / after pair), 3 currently human-mediated compositions plus 2 the intelligence layer could automate, world-model entries for the organization side and for each stakeholder type, and 3 entries in `pieces_to_build[]` that all converge on the same missing capability — a context-keeping practice the studio doesn't yet have anyone owning. The page itself shows the three layers and the Analysis modal names the three structural moves; the pieces-to-build data stays in the JSON for the audit gate but is deliberately not rendered as a project list on the page (the framework's claim is that the roadmap emerges from running the loop, not from a list compiled today). Three leader-facing decisions name Marco, Lena, and Tomás by role and the studio's units by name.
