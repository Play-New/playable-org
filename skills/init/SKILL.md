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

- It does not interview the user for content. The principle is: facts come from cited sources, not from the user's head. If the user has no documents, init cannot run.
- It does not bypass the "every assertion cites a source" invariant. Every node it writes carries `(source-id)` citations.
- It does not produce interpretations. No playbooks run during init. `plays/` stays empty until a playbook is invoked separately.
- It does not write in batch-and-forget mode. Every batch of writes is shown to the user as a diff before being applied.

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
