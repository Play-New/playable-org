---
name: lint
description: "Periodic health check on org/. Composes Tier 1 (mechanical structure) + Tier 2 (semantics). Output: markdown report at repo root + chat summary."
---

# Skill: lint

Health check on `org/` at two levels. Implemented as 2 Python scripts at repo root, run sequentially by the agent.

## Tier 1 — mechanical (`lint.py`)

7 deterministic checks on graph structure. Output: `lint-report-<YYYY-MM-DD>.md` at repo root.

| Check | What it measures |
|---|---|
| Broken markdown links | `[text](path.md)` with non-existent target |
| Duplicate IDs | Multiple nodes with the same `id` in frontmatter |
| Filename mismatches | `id` ≠ filename slug |
| Frontmatter required | Required fields per type (per AGENTS.md schema) |
| Cross-reference issues | Frontmatter id references (`unit`, `parent`, `parties_*`, etc.) that don't resolve |
| Files without frontmatter | Markdown files without parseable frontmatter (excluded: README, AGENTS, index, log, open-questions) |
| Orphan nodes | Nodes with no incoming links from any other node |

Semantic skip: Tier 1 ignores fenced code blocks AND inline code spans to avoid false positives on documentation examples.

## Tier 2 — semantic (`lint-semantic.py`)

4 Karpathy-style metrics: cheap, automatable, convergent, action-driving. Output: `lint-semantic-report-<YYYY-MM-DD>.md`.

### M1 — Commitment integrity

For each commitment:
- `parties_committing` and `parties_benefiting` non-empty, all valid IDs
- If `state ∈ {degraded, broken}` → `failure_mode` populated + `state_evidence` non-empty
- Connectivity: body links ≥1 other commitment OR is referenced by ≥1 unit/activity body

### M2 — Unit↔activity referential closure

- For each activity with `unit: X`, X body must link it
- For each link `[activity](path)` in unit body, the activity must have corresponding `unit: X`

### M3 — Language term usage

For each `language/<term>.md`, count inbound links:
- 0 = DEAD (remove or explain)
- 1 = BORDERLINE (flag)
- ≥2 = OK

### M4 — Stub detection (per-type threshold)

| Type | Threshold | Rationale |
|---|---|---|
| activity | ≥20 words body | Quote + minimum cross-ref |
| unit, stakeholder, commitment, identity | ≥30 words | Substantive body |
| language-term | skip | Glossary entry, brief by nature |
| person | skip | Source-constrained (funzionigrammi describe roles, not persons) |
| role | skip | Responsibility lives in unit body |

## Workflow

```bash
cd /repo/root
python3 lint.py        # Tier 1
python3 lint-semantic.py  # Tier 2
```

Reports in `lint-report-*.md` and `lint-semantic-report-*.md`.

## When to run

- **After every ingest** (part of the ingest workflow, step 8)
- **After every Pass B** completed
- **Weekly** as baseline check
- **Before every `play`** to ensure the structure is healthy

## Triage

For each issue:

1. **Autonomously fixable?** (typical broken link, missing required field) → fix with `org_write_node` or direct edit
2. **Requires user decision?** → keep in lint report, propose to user
3. **Acceptable trade-off?** (e.g., M3 borderline = legitimate single-anchor language term) → document explicitly in log

## Invariant during execution

Lint **does not modify** nodes. It is read-only. Fixes are separate and tracked.

## Iteration (autoresearch)

Typical execution is iterative:
1. Run lint → produces N issues
2. Fix triageable ones → re-run → N' < N
3. Re-run until convergence

On a stable corpus (no ongoing ingest), Tier 1 + Tier 2 should stabilize at 0 with any borderlines explicitly accepted.

## When NOT to use

- During an ongoing ingest (run **after**, not during)
- On `org/` modified concurrently by multiple sessions — may produce transient false positives

## References

- `lint.py` — Tier 1 implementation
- `lint-semantic.py` — Tier 2 implementation
- `org/AGENTS.md` schema — defines required fields per type
- `org/AGENTS.md` invariants — constraints the lint protects
