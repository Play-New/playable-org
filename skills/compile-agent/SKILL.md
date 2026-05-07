---
name: compile-agent
description: "Given a scope (org / unit / person / commitment), emit a CLAUDE.md instruction file that turns a Claude Code or Claude Desktop session into an agent that knows that scope. Walks the structure, packs the relevant nodes into a single self-contained context, exports it as a CLAUDE.md the user can drop into a fork, a clone, or a fresh repo. Output: one CLAUDE.md per scope, plus a manifest listing what was included and what was deliberately omitted."
---

# Skill: compile-agent

This is the first concrete step toward agentic deployment. Given a populated `org/`, the skill compiles a `CLAUDE.md` for any scope inside it — the whole org, a single unit, a single person, a single commitment. The output is an instruction-oriented document that, when placed in a fork, a clone, or a fresh repo, gives a Claude session enough context to act as that scope.

## What kinds of scope are supported

| Scope | Example | Contents the compiled CLAUDE.md inherits |
|---|---|---|
| **whole-org** | `compile-agent --scope org` | identity (mission, limits, rules), all units, key commitments, all stakeholders, the catalog from `index.md`, recent log entries |
| **unit** | `compile-agent --scope unit:strategy` | the unit's frontmatter + body, all activities owned by the unit, all people in the unit, all commitments where the unit is a party, the unit's stakeholders, sources cited |
| **person** | `compile-agent --scope person:marco-bellini` | the person's frontmatter + body, all activities they perform, all commitments they're party to, the unit they belong to, the people they hand off to or receive from, sources cited |
| **commitment** | `compile-agent --scope commitment:studio-mid-market-baseline` | the commitment's terms, conditions, consequences, state evidence, fallback, all parties (committing + benefiting), the activities executed under it, the sources |

The scope is hard-cut: a `unit:strategy` agent does not know about the financials of `digital-product` unless those are explicitly cited in `strategy`'s nodes. The skill resists scope creep — that's the point.

## What the compiled CLAUDE.md looks like

Five sections, in order:

1. **Identity** — who the agent is in this scope. Two-sentence opening: "You are an agent that knows `<scope-name>` of `<org-name>`. Your knowledge is limited to what's listed below; if asked something outside it, say you don't know."
2. **Structure** — the relevant nodes, embedded verbatim or summarised with a path-pointer. Frontmatter preserved (so the agent can read structured fields) plus the body.
3. **Commitments in scope** — the load-bearing relations, with terms and conditions inline.
4. **Sources cited** — list of source ids the agent can reference. The full source content is NOT inlined (would bloat) but the path is given so a tool-equipped agent can fetch.
5. **Operating discipline** — three rules: every claim cites a source; no claim outside scope without flagging; conditional voice for emerging items per `STYLE.md`.

A typical compiled `CLAUDE.md` is 5-30KB depending on scope size. The whole-org one for sample-org is ~25KB; a single-person one is ~3-5KB.

## Workflow

### 1. Resolve the scope

Read the scope argument and walk the graph:
- For `org`: every node, including `identity/` and `commitments/`, plus `index.md` for the catalog.
- For `unit:<id>`: the unit + every activity with `unit: <id>` + every person with `unit: <id>` + every commitment with the unit in `parties_committing` or `parties_benefiting` + every activity's stakeholders.
- For `person:<id>`: the person + every activity with `performer: <id>` + every commitment they're a party of + their unit + the people they hand off to / from (read from the activities' inputs/outputs/handoff fields when present).
- For `commitment:<id>`: the commitment + every node listed in its parties + every activity executed under it + the sources it cites.

### 2. Pack into a single CLAUDE.md

Concatenate frontmatter + body of every in-scope node, with section headings. Preserve cross-references as relative paths. Normalize all paths to be relative to a hypothetical fork root.

### 3. Generate the manifest

A `manifest.json` next to the CLAUDE.md listing:
- `scope`: kind + id
- `included_nodes`: list of every node id and path
- `included_sources`: list of source ids referenced
- `excluded_by_design`: the 3-5 categories the skill deliberately omitted (e.g. "other units' commitments", "log entries older than 6 months")
- `compiled_at`: timestamp

The manifest exists so the user can audit what the agent got vs what they didn't.

### 4. Write to disk

`org/agents/<scope-kind>-<scope-id>/CLAUDE.md` and `manifest.json`. The path under `org/agents/` is by convention; the user can move them after.

### 5. Optional: also write a slash-command skill bundle

If the scope is a `person`, the user can pass `--with-skills` to also export Claude skills (one per activity the person performs that has the density layer filled). This is the bridge to Level 2 deployment — see `interview-activity` for filling the density layer. Without filled density, the flag is a no-op and the skill warns.

## What this skill does NOT do

- It does not infer. Every claim in the compiled CLAUDE.md is cited from a node in `org/` or omitted.
- It does not interpret. There's no "summary" prose — only the org's own words, filtered to scope.
- It does not generate a Claude skill from the activity descriptions alone. To compile a skill (slash command) you need the activity density layer; see `interview-activity`.
- It does not export `plays/`. Plays are point-in-time interpretations, not durable agent context. The compiled CLAUDE.md is structure-only.
- It does not produce a runtime — it produces a *document*. The user pairs the document with their own Claude Code / Claude Desktop session.

## Output

```
org/agents/<scope-kind>-<scope-id>/
├── CLAUDE.md            # the agent's instruction file
└── manifest.json        # what was included, what was omitted, when
```

The user moves the folder to their target deployment (a fork, a clone, a fresh repo with just a `CLAUDE.md`), opens it in Claude Code, and the agent boots with the right knowledge.

## Implementation status

This SKILL.md is the contract. The Python compiler script (`compile.py`) is not yet bundled — `compile-agent` is currently a *recipe an agent follows by hand* via `org_read` / `org_neighbors` / `org_list`. When the skill matures, a `compile.py` will mechanise the structure walk + CLAUDE.md emission.

Today the agent runs the skill manually:

1. Read this SKILL.md.
2. Resolve scope via `org_neighbors` and `org_list`.
3. Read each in-scope node via `org_read`.
4. Concatenate into a CLAUDE.md following the five-section shape above.
5. Write via `org_write_node` to `agents/<scope>/CLAUDE.md`.
6. Write the manifest alongside.

The mechanised version is the next iteration. The hand-driven version works today and produces the same output.

## When to run this skill

- A new team is forking the org's playable-org install and wants a scope-limited agent (a unit head wanting just their unit's structure)
- A specific person wants a personal agent that knows their role and commitments
- A consultant or partner is being given access to one commitment and only that
- An audit / review needs a snapshot of a scope at a specific date

Not for: real-time analysis (use `org_read` directly), playbook runs (use `org_play_run`), or interpretive work (use the playbooks).

## Distance to Level 2 (Claude skills per activity)

Level 1 is what this skill produces: a scoped CLAUDE.md the agent reads as context. The agent can ANSWER questions about the scope but doesn't have invocable skills.

Level 2 is what `interview-activity` enables: density-filled activities become slash-command skills the agent can RUN. A person's compiled agent at Level 2 can be told *"run brand-positioning for this engagement"* and the skill loads the density layer (trigger / quality_gates / decision_criteria / output_format / fallback / handoff) and walks the agent through it.

The bridge: once an activity has the density layer filled (per `org/AGENTS.md`), `compile-agent --with-skills` exports it as a skill alongside the CLAUDE.md.
