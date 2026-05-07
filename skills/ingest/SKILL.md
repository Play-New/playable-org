---
name: ingest
description: Ingest a new source into org/. One source at a time, with scope check, paraphrased citation, full ripple (units, activities, roles, language, stakeholders, commitments, index, log).
---

# Skill: ingest

Recipe for ingesting a source (organizational chart, statute, paper, slide deck, dataset) into `org/`. Codifies the Pass B practice applied 22 times during the pilot project.

## Pre-conditions

- The source is available as a file (PDF, DOCX, XLSX, PPTX, MD, HTML, TXT) or as text to paste in chat. **Interview transcripts count as sources** — the same way `init` Path B treats the founding interview, an ingest-time conversation about a specific topic (a strategy meeting, a stakeholder call, a quarterly review) can be saved verbatim as `<topic>-interview-<date>.md` and cited the same way as a document.
- Identity/ already exists: the agent verifies relevance against `identity/`
- Lint Tier 1 and Tier 2 clean before starting (ingest does not fix preexisting debt)

## mcp tools the workflow composes

- `org_save_source` — register the raw file in `sources/` (immutable)
- `org_search`, `org_list`, `org_neighbors` — verify what already exists
- `org_read` — read existing nodes to decide update vs create
- `org_write_node` — apply changes to the structure
- `org_log_append` — record the operation in `log.md`

## Workflow (8 steps)

### 1. Save the source

`org_save_source` with `filename` canonicalized to kebab-case + `content` (text) or `content_base64` (binary). The tool refuses overwrite (sources/ is immutable).

Output: `sources/<canonicalized-name>.<ext>`. The source-id will be the filename without extension.

#### Binary sources (PDF, DOCX, XLSX, PPTX) — important caveat

When the user drags a binary document into the Claude Desktop chat, Claude receives the **extracted text** of that document, not the raw bytes. The agent therefore cannot pass `content_base64` for that file — only the text extraction. The saved file in `sources/` will be a `.md` text version, not the original binary.

This is **honest** but not always desirable. Two approaches:

- **Text-only ingest (default).** Save the extracted text as `<canonicalized-name>.md` via `content`. Tell the user explicitly that the binary original is not preserved by this flow. Do not pretend `.pdf`, `.docx`, etc. when only text is available.
- **Preserve original binary.** Ask the user to copy the original file into `org/sources/` directly via Finder / file manager **before** the chat ingest. Then call `org_save_source` only if needed for the text extraction sidecar. The original binary is preserved alongside.

If the user did not copy the binary manually and only dragged it in chat, **say so explicitly** in the ingest summary: *"il file originale non è stato salvato come binario; in `sources/` c'è la sola estrazione testo. Per preservarlo, copialo manualmente nella cartella `org/sources/`."*

Never guess the original extension. If the content is text, save with `.md` extension. If you actually have base64 bytes (rare in Claude Desktop drag-and-drop, possible with a filesystem mcp tool), save with the correct binary extension.

### 2. Scope check vs identity

Read `identity/mission.md`, `identity/limits.md`. If the source addresses something outside the organization's scope (e.g., research on space technologies for a cancer-research foundation), **stop** and flag. No out-of-scope ingest.

### 3. Extract candidate entities

Read the source content. Identify:

- **Units** mentioned (areas, sub-teams, committees, governance bodies)
- **Persons** named (proper names of staff)
- **Roles** described
- **Activities** described (typically in "Responsibilities" / "Activities" sections)
- **Stakeholders** mentioned (donors, suppliers, institutions, peer orgs)
- **Commitments** documented (cardinal, cross-area, role-role, etc. — apply the AGENTS.md "When to register a commitment" policy)
- **Domain terms** organization-specific not yet in `language/`
- **Discrepancies** vs what already exists in `org/`

For each entity, **cite the source inline**: `(<source-id>)` or `(<source-id> §X.Y)`.

### 4. Map entities → existing nodes

For each candidate entity: `org_search` by id and by description. Decide:

- **Already exists**: update (append/edit with diff)
- **Doesn't exist**: create new node
- **Exists but differs**: flag as **discrepancy** (do NOT silently overwrite)

### 5. Compose changes

For each node to create/update:

- Complete frontmatter for the type (see `org/AGENTS.md` schema)
- Body in the org's working language: paraphrase the source, **don't copy verbatim** (invariant #3). Verbatim quotes allowed as short blockquote (≤3 lines) with `(source-id)` attribution
- Cross-references via standard markdown: `[text](../path/to/node.md)`
- Inline source citations: `(source-id)`

For **activities** specifically: pattern adopted = verbatim blockquote of the role-description document + paragraph of elaboration + cross-ref to parent unit + 1-2 adjacent activities.

### 6. Apply via `org_write_node`

One write per node. Mode `create` for new, `update` for existing, `upsert` for mixed (recommended).

For large batches (>10 nodes): prefer bash heredoc + `cat > file <<'EOF'` on local filesystem, because `org_write_node` is atomic but more verbose. For Pass B over an entire area, heredoc is recommended.

### 7. Full ripple

Update cascade in this order:

1. **Units** modified or created
2. **Activities** under those units
3. **Roles** if new
4. **Persons** if new (rare: only if the source names new individuals)
5. **Stakeholders** if new
6. **Language terms** if new (respect the policy: only domain terms of the organization, not internal project names)
7. **Commitments** if any emerge (3 tests in AND: cited, load-bearing, non-redundant)
8. **`index.md`** — add new entries by category

### 8. `log.md` — MANDATORY closing step

Append one line to `log.md` via `org_log_append`. **An ingest is not complete until this is done.** Do not declare the ingest finished or move to lint without this call.

The line must include: date, source-id, count of nodes created/updated, list of node ids touched (or area name if many).

Example:
```
2026-05-06 — ingest annual-grant-2026 — 1 source + 4 activity (operations) + 1 language-term (grant-cycle) + index.md update
```

### 9. Mechanical verification

Run `python3 lint.py` and `python3 lint-semantic.py` from repo root. All checks must remain at 0 (or remain at borderline values accepted before the ingest).

If new issues appear: triage and fix before considering the ingest complete.

## Definition of done

The ingest is complete only when **all of these** are true:

- [ ] Source file present in `sources/` (text via `content` or binary via `content_base64`).
- [ ] Structure updates applied via `org_write_node` (one call per node).
- [ ] `index.md` updated with new entries.
- [ ] **`log.md` has a new entry via `org_log_append`** — without this line the ingest did not happen, audit-wise.
- [ ] If the source was a binary file (PDF/DOCX/XLSX/PPTX) and Claude Desktop only had the text extraction, the user has been told explicitly that the original binary was not preserved.

If any of these is missing, do not declare the ingest finished. Do not move to lint or to a new request from the user until they are satisfied. The user can interrupt and ask for a partial save, but the agent must not pretend a half-done ingest is done.

## Output of the ingest

- 1 source file in `sources/`
- N nodes created/updated (typically 5-20 per area role-description document)
- 1 entry appended to `log.md` with summary
- 0 new lint issues

## Cases & exceptions

### Interpretive source (paper, position, analysis)

Examples: position papers, organizational analyses, framework documents. **Do not ingest as structure.** They live in `sources/` but do not produce new activity/unit nodes from their content.

Minimal extraction allowed:
- Fact about authorship (in `nodes/people/<author>.md`)
- Domain terms actually used (in `language/`)
- Reference to the paper as a **trigger** for a future `play`

### Source with discrepancies vs the structure

Examples: org chart March vs April, registry funzionigrammi vs chart. **Flag inline** in the unit body: "**Discrepancy**: ...". Do not overwrite. Add to `open-questions.md` if not autonomously resolvable.

### Batch ingest (>1 source)

Opt-in mode. Same workflow per source, BUT ripple cascade and lint run **only once** at the end of the batch, not per source.

## When NOT to use this skill

- For structure changes that don't come from a source (e.g., style fixes, refactor): use `org_write_node` directly, no ingest skill
- For identity changes (mission/limits/rules): human-only, `force_identity=true` on `org_write_node`
- For sources/ itself: immutable, no ingest

## References

- `org/AGENTS.md` — node schemas, invariants, locked vocabulary
- `org/AGENTS.md` "When to register a commitment" — 3 tests in AND
- `lint.py` (Tier 1) and `lint-semantic.py` (Tier 2) at repo root
- `org/open-questions.md` — discrepancies and open questions
