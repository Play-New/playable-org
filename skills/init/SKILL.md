---
name: init
description: "Initialize the structure of org/ by bulk-ingesting source documents at first install. One-time operation. Walks the agent through reading every file in org/sources/, extracting nodes in batches, writing on confirmation. Output: a populated graph (typically 200-400 nodes after one session) ready for queries and playbook runs. After init, the regular `ingest` skill handles new documents one at a time."
---

# Skill: init

The first thing a new instance of Playable Org needs is content. The user has just installed the bundle. The graph has three empty identity stubs in `org/identity/`. The structure under `nodes/`, `commitments/`, `financials/`, `language/` is empty.

The `init` skill is the recipe for populating it from raw documents in one session. It is a one-time operation. After init, the regular `ingest` skill handles new documents one at a time as they arrive.

## Pre-conditions

- The mcp server is connected (Claude Desktop reads `org/`).
- The user has dropped source documents into `org/sources/` via Finder / file manager. Acceptable formats: PDF, DOCX, XLSX, PPTX, MD, HTML, TXT.
- The user knows what kind of organization is being represented (so the agent can scope-check against `identity/` later).
- Lint Tier 1 reports 3 frontmatter issues on the unmodified starter (the three `identity/` stubs ship with empty `sources: []` arrays because they haven't been pointed at a source yet). After init fills the identity from real founding documents, those three warnings go away and Tier 1 should land at 0.

## What `init` does NOT do

- It does not bypass the "every assertion cites a source" invariant. Every node it writes carries `(source-id)` citations.
- It does not produce interpretations. No playbooks run during init. `plays/` stays empty until a playbook is invoked separately.
- It does not write in batch-and-forget mode. Every batch of writes is shown to the user as a diff before being applied.

## Two starting paths

`init` accepts the org in either of two states:

- **Path A — documents-first.** The user has dropped real source documents (charter, role descriptions, contracts) into `org/sources/`. This is the canonical path; everything below in §Workflow describes it.
- **Path B — interview-first.** The user has no written documents to drop, or the documents that exist don't cover the structure (typical for orgs whose conventions live in conversation). The agent runs a structured interview; the transcript itself becomes a citable source. See §Path B below.

The two paths can also combine: start with whatever documents exist, then fill the gaps with a targeted interview anchored on what the documents leave unsaid.

## Workflow

### 1. Inventory `sources/`

The agent calls `org_list` against the `sources/` path (or reads the filenames directly via the filesystem if the mcp tool supports it). Result: list of files with extension and size.

For each file, the agent classifies it into one of these archetypes:

| Archetype | Examples | Typical yield |
|---|---|---|
| **Founding** | charter, statute, articles of association, governance charter | identity (mission/limits/rules), 1-2 organizational units, governance commitments |
| **Operational** | role-description per division/area, process map, internal SOP | many units, activities, roles, sub-team structure |
| **org chart** | organizational chart (current or historical) | units (the chart itself), people (named individuals), roles |
| **Stakeholder** | partner agreement, supplier contract, MOU | stakeholder, commitment (org-stakeholder or inter-org) |
| **Financial** | annual report, audited statements, financial summary | financial-summary nodes, commitments to funders |
| **Code-of-conduct** | ethics code, compliance framework, risk management framework | rules, governance commitments |
| **HR analysis** | capability assessment, headcount report, role analysis | people (where named), updates to existing units |
| **External analysis** | a paper or assessment about the org | typically NOT ingested as structure; preserved as source for citation, possibly triggers a play later |

### 2. Read identity-bearing documents first

Order matters. The agent reads founding documents first because `identity/` (mission, limits, rules) anchors everything else. Without identity, scope-checks have no reference.

For each founding document, the agent:
1. Calls `org_save_source` on the file (text via `content` if available, or noted as "binary archived in sources/" if Claude Desktop only has the text extraction).
2. Reads the source content.
3. Proposes updates to `identity/mission.md`, `identity/limits.md`, `identity/rules.md`, replacing the `# REPLACE ME` stubs with cited content.
4. Shows the diff (what will be written into each identity file).
5. Writes on user confirmation via `org_write_node`.

### 3. Read operational documents in batches

Once `identity/` is filled, the agent moves to operational documents. For each one, it:

1. Calls `org_save_source`.
2. Reads the content.
3. Verifies relevance against the freshly-filled `identity/` (scope check, per the `ingest` skill rule).
4. Extracts candidate entities by archetype:
   - **Units** mentioned (areas, sub-teams, committees)
   - **Persons** named (proper names of staff)
   - **Roles** described
   - **Activities** (typically in "Responsibilities" / "Activities" sections)
   - **Stakeholders** mentioned (donors, suppliers, institutions, peer orgs)
   - **Commitments** documented (apply the `AGENTS.md` "When to register a commitment" 3-test policy)
   - **Domain terms** organization-specific not yet in `language/`
5. Maps each candidate against existing nodes via `org_search`. Decides update vs create.
6. Composes changes (frontmatter + body, paraphrased, with inline `(source-id)` citations).
7. Shows a batch of 5-15 proposed writes to the user.
8. Writes on confirmation via `org_write_node` (one call per node).
9. Updates `index.md` after the batch.
10. Appends one line to `log.md` summarizing the batch.

The agent stays in the loop. After each batch, the user can pause, redirect, or end the session.

### 4. Read stakeholder and financial documents

Treat these archetypes last because they reference the units and commitments already established. A stakeholder document like an MOU is best ingested when the parties on both sides exist as nodes. A financial summary is best ingested when the divisions/areas it references already exist.

For these, the agent follows the same pattern (save source → extract → batch → confirm → write → log) but the entity types differ: more `stakeholder` and `commitment` and `financial-summary` nodes, fewer `unit` and `activity`.

### 5. Triage the rest

What remains in `sources/` after the four passes above is typically:

- External analyses about the organization. The agent registers them as sources (so they can be cited later by plays) but does not extract structure from them. They might trigger playbooks later.
- Old org charts or process maps. The agent flags discrepancies vs the current structure (existing units that are gone, or units in the chart but absent from the current role-description). Discrepancies are documented inline in the relevant unit, not silently overwritten.
- Documents the agent cannot classify. Listed in `open-questions.md` for the user to triage.

### 6. Final pass

After all batches:

1. The agent reviews `index.md` for completeness — every node should have one line in the catalog.
2. The agent runs `org_lint_run` (Tier 1 + Tier 2). Reports issues to the user.
3. The agent appends one line to `log.md` summarizing the session: total nodes by type, sources triaged, issues found.
4. The agent suggests next steps: which playbook would yield interesting first results given the structure now populated.

## Path B — interview-first init

Use this path when:
- the user has no source documents to drop into `org/sources/`, or
- the documents that exist don't cover the structure (e.g. a tiny charter and nothing else, with the actual operating model living in conversation).

The principle stays: every node in `org/` cites a source. In Path B the source IS the interview transcript — saved verbatim into `org/sources/`, given a stable id (e.g. `init-interview-YYYY-MM-DD`), and cited by every node the interview generates.

### B1. Frame the interview

Before asking any question, the agent says what's about to happen and why:

> "I'm going to ask you ten or so questions about the organization. Your answers will be saved verbatim as a source document in `org/sources/`, and the structure I write — units, people, activities, commitments — will cite that source. So whatever you say, I treat as a fact you're attesting to. If you're not sure about something, say so explicitly; I'll write 'unverified per <interview>' rather than dropping it."

This frames the interview as testimony, not brainstorming. Honesty about what's certain vs. what's a hunch travels into the structure.

### B2. The ten questions

Asked one at a time, in order. The agent waits for an answer to each before moving on. Each answer feeds a specific block in the structure.

| # | Question | Yields |
|---|---|---|
| 1 | "In one paragraph: what does this organization do, and for whom?" | `identity/mission.md` |
| 2 | "What kinds of people or organizations does it serve? List the categories — even if there's only one." | `nodes/stakeholders/*` |
| 3 | "What does each kind of stakeholder get from the organization, and what do they give back? Anything from money to attention to data." | stakeholder bodies + first-pass commitments (org-stakeholder) |
| 4 | "How is the work organized internally? List the teams or areas, even informal ones (the people who handle X, the people who handle Y)." | `nodes/units/*` |
| 5 | "Name the people who anchor each team or area. For each, one sentence on what they uniquely own." | `nodes/people/*` with role description |
| 6 | "Walk me through what each team actually does, week by week. Not what it's supposed to do — what it does. Five to ten activities per team, no more." | `nodes/activities/*` |
| 7 | "What promises has the organization made to the outside world that bind it? Contracts, mission statements, charter clauses, regulatory commitments — anything where breaking the promise has real consequences." | `commitments/*` (org-stakeholder, inter-org) |
| 8 | "What promises bind people inside the organization to each other? Who owes what to whom, even informally, when nobody is watching?" | `commitments/*` (org-internal) |
| 9 | "What hard constraints — legal, ethical, financial — would the organization refuse to cross even if it cost a lot? Three to five, no more." | `identity/limits.md` |
| 10 | "What's recently changed or is changing? A new unit forming, a stakeholder type drying up, a piece of work that used to matter and doesn't anymore. The thing you'd say first if a friend asked 'what's going on at work'." | `log.md` first entry + candidates for `plays/` later |

The agent does not paraphrase answers into structure during the interview. Answers go in raw, verbatim, into the transcript. The transcript becomes a single source. Structure-extraction happens AFTER.

### B3. Save the transcript as a source

The agent calls `org_save_source` with:
- `path: sources/init-interview-<YYYY-MM-DD>.md`
- `content: <the full transcript, verbatim, including the agent's questions>`

The transcript header includes the interview frame from B1, so anyone reading the source later understands its epistemic status (testimony, not document).

### B4. Extract structure from the transcript

The agent now treats the saved transcript as the only source. It walks back through each answer and proposes structure exactly as it would for a documents-first init: §2 (identity), §3 (operational), §4 (stakeholder + financial). Every proposed node cites `(init-interview-<date>)`. Every diff is shown to the user before being written.

### B5. Drop a §clarifications block in the transcript

If during structure-extraction the agent finds that an answer is too thin to support a node (e.g. "we have a finance team" with no further detail), it doesn't invent. It either:
- Asks one targeted clarification question and appends the Q&A to the transcript (treating it as a continuation of the same source), then writes the node, OR
- Drops the candidate node and notes the gap in `open-questions.md` for a later session.

### B6. Hand off to documents-first

After the interview-first pass produces a baseline structure, the user is encouraged to start dropping real documents into `org/sources/` whenever any appear. The regular `ingest` skill (one document at a time) takes over from there. Each new document either reinforces a node already cited from the interview, or contradicts it — in which case the agent surfaces the contradiction and asks which source wins.

The interview source is never "replaced": it stays as the founding citation for everything it created. New documents add citations alongside, they don't erase.

## What `init` produces

A typical first-install session, with ~10-30 source documents:

- 3 identity nodes filled (mission, limits, rules)
- 10-50 organizational units
- 5-30 named people
- 10-40 roles
- 100-400 activities
- 5-20 external stakeholders
- 5-20 cardinal commitments
- 1-5 financial-summary nodes
- 10-50 organization-specific language terms
- 1 entry in `log.md` per batch (typically 5-15 batches in a session)

Total: 200-400 nodes after a 30-60 minute session.

## Boundary with `ingest`

After init, every new document arrival uses `ingest` (one source at a time, full ripple, lint check). Use init only for the first installation, when the graph is being populated from a backlog of existing documents. Do not re-run init on a populated graph — that would propose duplicate nodes and damage the audit trail.

If the user wants to re-process a single source they already ingested (because the document changed), they should:

1. Save the new version under a new filename (sources are immutable).
2. Run `ingest` against the new version, which will surface diffs vs existing nodes.

## Anti-hallucination discipline

Three rules.

1. **Every node cites a source.** Even during the speed of bulk-ingest, no node is created without an inline `(source-id)` citation. The lint will catch violations later, but the agent must not produce them in the first place.
2. **Paraphrase, do not copy verbatim.** The body of a node summarizes the source in plain language. Verbatim quotes are short blockquotes (≤3 lines) with attribution.
3. **Confirmation before every batch write.** The agent never writes a batch without user confirmation. The user can ask the agent to slow down, focus on one source at a time, or abort.

## When to use this skill

- First installation of Playable Org for a new organization.
- Adding a substantial backlog of documents at once (e.g., after merger/acquisition or after a previously undocumented organization decides to formalize itself).

For the day-to-day case (one document at a time as it arrives), use `ingest`.

## References

- `org/AGENTS.md` — node schemas, invariants, when to register a commitment
- `skills/ingest/SKILL.md` — the per-document workflow used after init
- `skills/lint/SKILL.md` — quality control invoked at the end of init
