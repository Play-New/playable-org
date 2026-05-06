# AGENTS.md — operational contract for `org/`

Any agent (LLM or human) that reads or writes `org/` follows this contract. Read it before any operation.

## What `org/` is

A folder of markdown files representing one organization. Each entity (unit, person, role, activity, stakeholder) and each relationship (commitment) is one file with YAML frontmatter. The folder structure is the schema.

`org/` contains **only observable, cited facts**. Interpretations are produced by applying playbooks and live in `plays/` as point-in-time artefacts, frozen at creation.

## Five invariants

These constrain every operation. Violation = bug.

1. **Sources are immutable.** Files in `sources/` are never modified. The structure must be re-compilable from `sources/` alone.

2. **Every assertion cites a source.** No orphan assertions in `identity/`, `language/`, `nodes/`, `commitments/`, `financials/`, `plays/`. Inline citations: `(source-id)` or `(source-id §X.Y)`.

3. **Paraphrase, do not copy verbatim.** The body of a node summarizes sources in plain language. Verbatim quotation is allowed only as short blockquotes (≤3 lines, with `> ` and attribution).

4. **Humans curate, agents maintain.** No automatic ingest without explicit request. No structural changes (new node types, folder restructures) without explicit request. No play generated without request.

5. **Plays are frozen at creation.** Once written, a play records a moment in time. To revise, write a new one. Old plays are never deleted.

**Related rule: `org/` describes the as-is.** Sources document what is or has been, not what could be. The to-be (proposals, targets, gaps) lives in `plays/`. No `state: current | proposed` field on structure nodes.

## Folders

| Folder | Content | Mutability |
|---|---|---|
| `sources/` | Raw documents | Never modified |
| `identity/` | Mission, limits, governance rules | Slow, human-edited |
| `language/` | Domain terms (flat glossary) | Maintained by ingest |
| `nodes/units/` | Organizational units (divisions, areas, teams, governance bodies) | Maintained by ingest |
| `nodes/people/` | Named individuals | Maintained by ingest |
| `nodes/roles/` | Position types | Maintained by ingest |
| `nodes/activities/` | Atomic activities (who does what, FTE, artefacts) | Maintained by ingest |
| `nodes/stakeholders/` | Donors, partners, regulators, peers, suppliers | Maintained by ingest |
| `commitments/` | Relationships between nodes (5 levels, 3 state dimensions) | Maintained by ingest |
| `financials/` | Market view of the organization (revenue lines, headcount, costs by division) | Maintained by ingest |
| `plays/` | Point-in-time playbook executions (interpretations) | Frozen at creation |
| `log.md` | Prepend-only audit | Prepend-only |

## Special files at root of `org/`

- `README.md` — entry point for the organization.
- `AGENTS.md` — this file. Operational contract.
- `log.md` — prepend-only audit. One operation, one line.
- `index.md` — content-oriented catalog: one page, one link, one-line summary, organized by category. **Updated by the agent on every ingest.** To answer a query, the agent reads `index.md` first to find relevant pages, then accesses them.
- `open-questions.md` — questions requiring human input from inside the organization.

## Node schemas

Every node has `id` (kebab-case, unique in `org/`, equal to the file name without extension) and `type` (equal to the folder name).

### unit

Organizational unit at any level: division, area, team, governance body.

```yaml
id: <kebab-case>
type: unit
parent: <unit-id or null>
level: division | area | team | governance-body
description: "..."
head_role: <role-id or null>
n_persons: 0
authority_basis: [...]
sources: [...]
```

#### Governance bodies — why no activity

Statutory bodies (board, councils, statutory auditors, ethics committee) are modeled as `unit` with `level: governance-body` and a descriptive body, but **without decomposition into `activity`**. Bodies *deliberate and meet* (output: resolutions, minutes, sessions counted), they do not *execute recurring activities* in the role-description sense. Modeling them as an activity-graph forces the schema. Future decomposition belongs in a dedicated play (e.g. `governance-decision-flow`), not in the structure.

### person

A named individual currently holding a role.

```yaml
id: <kebab-case>
type: person
role: <role-id>
unit: <unit-id>
status: active | exiting | departed
since: YYYY-MM-DD          # optional
description: "..."
sources: [...]
```

### role

A position type, separate from the person holding it.

```yaml
id: <kebab-case>
type: role
unit: <unit-id>
reports_to: <role-id or null>
description: "..."
activities: [...]          # activity ids the role performs
sources: [...]
```

### activity

Atomic unit of observed work: who does what.

```yaml
id: <kebab-case>
type: activity
performer: <person-id or role-id>
unit: <unit-id>
description: "..."
fte: 0.0
artifacts: [...]
inputs: [...]
outputs: [...]
stakeholders_touched: [...]
frequency: "..."           # daily, weekly, monthly, on-demand
sources: [...]
```

### stakeholder

External entity that interacts with the organization.

```yaml
id: <kebab-case>
type: stakeholder
kind: donor | partner | supplier | regulator | institution | peer | customer
description: "..."
engagement_mode: "..."     # factual: how the org interacts
sources: [...]
```

### commitment

```yaml
id: <kebab-case>
type: commitment
parties_committing: [<id>, ...]      # any node id
parties_benefiting: [<id>, ...]
level: person | role | unit | org-stakeholder | inter-org
direction: reciprocal | unilateral
explicit: yes | no
terms: "..."
conditions: "..."
consequences_if_broken: [...]

state: active | degraded | broken
failure_mode: obvious | vacuous | misaligned    # only if state ≠ active
state_evidence: "..."

fallback: designed | partial | none
fallback_description: "..."

lifecycle: draft | active | paused | expired | superseded

sources: [...]
```

#### When to register a commitment

The schema supports 5 levels, but the decision to **register** a specific commitment is independent of level and follows three tests in AND:

1. **Cited or derivable from sources** (invariant #2).
2. **Load-bearing**: if removed from the graph, it weakens reasoning about the organization. "It exists" is not enough; there must be an articulable harm if it breaks.
3. **Non-redundant**: it does not duplicate what is already described in the body of a `unit` or `activity` as a "Cross-area" section.

Typical consequences by level:
- `org-stakeholder` and `inter-org`: few, cardinal. Breaking causes the org to cease or take structural damage.
- `unit`: cross-area dependencies documented in role-descriptions with articulable operational consequences.
- `role`: only when role-descriptions explicitly codify "shared responsibilities".
- `person`: only when a source names a specific pair of people as a structural pattern (broken or load-bearing). Normal collaboration is not registered.

Operational relations that don't pass the three tests stay in the body of `unit` or `activity` as a "Cross-area" section, not as `commitment` nodes.

### language-term

```yaml
id: <kebab-case>
type: language-term
description: "≤200 characters"
related: [...]             # other term or node ids
sources: [...]
```

### play

Every play has at minimum: `type: play`, `playbook: <name>`, `target: <slice or node-ids>`, `dated: YYYY-MM-DD`, `frozen: true`, `sources: [...]`. Generated artefacts (structured JSON, interactive HTML, optional SVG) live in `plays/data/`; the optional frozen markdown that summarizes the play lives at the root of `plays/`. See `<repo>/skills/playbooks/<name>/SKILL.md` for the schema specific to each playbook.

### financial-summary

```yaml
id: <kebab-case>
type: financial-summary
dated: YYYY                # reference year of the data
description: "..."
sources: [...]             # annual report, institutional profile, HR analysis, etc.
```

Market view of the organization: annual snapshot, revenue lines, headcount, operating costs by division. The body is prose with tables and inline citations to the source.

## Frontmatter conventions

- `id`: kebab-case, unique across `org/`. Filename = `<id>.md`.
- `description`: ≤150 characters, plain language, no marketing tone.
- Inline citations: `(source-id)` or `(source-id §X.Y)`. The `source-id` values used must appear in the `sources:` frontmatter array.
- Keys in English. Free-text values in the organization's working language.

## Cross-references between nodes

Cross-references live in two complementary places.

**Frontmatter — structured.** Arrays of ids referenced by the node's role. Examples:
- in a `commitment`: `parties_committing: [alice, bob]`
- in a `role`: `activities: [recruitment-screening, onboarding-buddy]`
- in an `activity`: `performer: alice`, `unit: people-ops`

The agent reads these as data. The mcp tool `org_neighbors` exploits them to traverse the graph.

**Body — standard markdown links.** When a node is mentioned in prose:

```markdown
# Alice ↔ Bob — operational duplication

Implicit reciprocal-backup commitment between [alice](../nodes/people/alice.md) and [bob](../nodes/people/bob.md) on the payroll perimeter.
```

Relative paths from the current file's folder. Standard markdown: renders everywhere (Claude.ai, GitHub, IDE, Obsidian) without proprietary conventions. Clickable by humans, navigable by agents.

**Dual resolution**: the link reads both as a filesystem path (the agent opens the file) and as an id (the `id` is unique in `org/`, the agent can search via the mcp tool `org_read(id)` if needed).

**Path-based brittleness**: links break if files move. Mitigation: the folder structure is fixed; the lint workflow catches broken links.

## Writing rules (body)

1. No transition fillers ("first of all", "it's worth noting").
2. No self-reference of the document.
3. Verbs over nominalizations.
4. Numbers over adjectives.
5. Specifics over generics.
6. Lists for atoms, prose for relationships and reasons.
7. No editorializing.
8. **No author names of analytical frameworks in `org/`.** Frameworks are visible only as named playbooks.
9. System vocabulary: *org*, *playbook*, *play*, *point-in-time*, *frozen at creation*. Terms outside this list are not used to describe the system.
10. Inline citations to sources: `(source-id)`. Cross-references to nodes: standard markdown link `[text](../path/to/node.md)`.

If a sentence can be cut without loss of meaning, cut it. Empty fields are honest, not failures.

## Operations (high-level workflows)

Workflows are procedures the agent composes using the **mcp tools** of the bundled server in `<repo>/mcp-server/`. The server exposes 12 tools; their schemas are introspectable from the client via `tools/list`. Step-by-step detail for each workflow lives in `<repo>/skills/<name>/SKILL.md`. Here only the high shape.

### init

**One-time bulk ingest at first install.** The user drops a folder of source documents into `org/sources/` (founding charter, organizational charts, role-descriptions, annual report, internal process maps). Then in chat: *initialize the structure from sources/*. The agent iterates each document, proposes nodes in batches (5–15 per batch), shows diffs, writes on confirmation, appends one log line per batch. A first-install init session typically produces 200–400 nodes in 30–60 minutes.

Detail: `<repo>/skills/init/SKILL.md`.

### ingest

**Default after init: one source at a time, human in the loop.** A new document arrives (loaded in chat or moved into `sources/`); the agent verifies its relevance against `identity/`, reads the content, saves the source under a canonicalized name in `sources/<id>.<ext>`, proposes 5–15 structure updates (only observable facts, no interpretation), shows the diff, applies on confirmation, updates `index.md`, appends to `log.md`.

Detail: `<repo>/skills/ingest/SKILL.md`.

### query

Question → agent reads `index.md` first to locate relevant pages → fetches those pages via mcp → answers with inline source citations and standard markdown links to nodes. Default behaviour, no dedicated SKILL.md.

### lint

Periodic health check. Surfaces orphan nodes; citations to non-existent sources (refused mechanically, no exceptions); stale assertions; missing required frontmatter; commitments with `state ≠ active` and `fallback: none` (escalation candidates); concentration of commitments at the `person` level (signals fragility); mismatch between `index.md` and the filesystem.

Detail: `<repo>/skills/lint/SKILL.md`.

### play

Application of a named playbook to a slice of `org/` → produces a structured JSON + interactive HTML artefact under `plays/data/`, and (when materialized) a frozen markdown summary at the root of `plays/`.

Playbooks (procedure templates) live in `<repo>/skills/playbooks/`, outside `org/`. They are product, not content.

Playbooks are named for what they do, never for the author. Four base playbooks:

- `ai-exposure` — maps each activity to AEI tasks and classifies AI exposure on two layers (observed signal + organizational constraints).
- `value-map` — positions an anchor's components on the evolution axis with AI overlay grounded in AEI evidence.
- `reshuffle` — diagnoses which constraints hold a bundle together (scarcity / risk / coordination) and classifies AI uses as tools or engines.
- `world-model` — re-reads the organization as a stack of capability + world model + intelligence layer + interfaces; produces a roadmap from failure signals.

Plus a meta-skill `new-play` (5-question interview that scaffolds a new playbook by forking the closest base). See `<repo>/skills/ROADMAP.md` for the order, and `<repo>/skills/playbooks/<name>/SKILL.md` for each.

## Format of `log.md`

```
YYYY-MM-DD — <operation> — <change summary>
```

Lines are appended at the top (most recent first).
