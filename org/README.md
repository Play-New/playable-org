# org/

Representation of an organization as a navigable graph of markdown files. Content language is the organization's working language. The schema is in English. Curated by humans, maintained by agents.

## Who reads it

Three readers expected.

A team lead who does not remember exactly what neighbouring teams do. They open `nodes/units/<area>.md` and read the perimeter cited from the role-description document.

A new hire who wants to understand how the organization holds together. They start from `identity/`, descend into `nodes/units/`, follow the cross-references.

An AI agent connected via `mcp` that receives a question and looks for relevant pages to answer with citations to sources.

## What's inside, in numbers

(All counts at zero in the public template. After running `init` against your sources, this section reflects your organization.)

- 0 organizational units
- 0 activities
- 0 named people
- 0 roles
- 0 external stakeholders
- 0 organization-specific language terms
- 0 commitments
- 0 financial-summary nodes
- 3 identity stubs (mission, limits, rules — to be replaced)
- 0 raw documents in `sources/`

## Structure

```
org/
├── identity/            mission, limits, rules — what the org is and is not (3 files)
├── language/            organization-specific glossary
├── nodes/
│   ├── units/           organizational units
│   ├── people/          named individuals
│   ├── roles/           position types
│   ├── activities/      who does what
│   └── stakeholders/    external entities
├── commitments/         relationships between nodes (5 levels)
├── financials/          market snapshot — annual lines, revenue lines, headcount, costs
├── sources/             raw immutable source documents
├── plays/               point-in-time interpretations, frozen at creation (artefacts in plays/data/)
├── AGENTS.md            operational contract for anyone who modifies org
├── README.md            this file
├── index.md             content-oriented catalog
├── log.md               prepend-only audit
└── open-questions.md    questions requiring human input from the organization
```

## How to read

For what the organization is: `identity/mission.md`, `identity/limits.md`, `identity/rules.md`. Short, cited, re-grounded on the founding documents.

For organization-specific vocabulary: `language/`. Each term has a canonical definition and a citation to its source.

For who does what: start at `nodes/units/<area>.md`, descend to the linked `nodes/activities/<area>-*.md`. Each activity has a verbatim quote from the role-description document plus a short paraphrase and cross-references.

For cardinal commitments: `commitments/`. org-stakeholder commitments are typically the cardinal ones; cross-area commitments document internal coordination; inter-organization commitments document partnerships.

For interpretations: `plays/`. Frozen at creation, cited, distinct from the structure.

## What the graph does not yet know

`open-questions.md` lists questions that require a person inside the organization to answer.

When the agent hits an ambiguity during `init` or `ingest` or playbook authoring, it appends an entry there. None of these are blocking for using the system. They are inputs requested from the people who know the organization from the inside.

## Constraints on whoever modifies

Five invariants, summary.

Source files in `sources/` are never modified.

Every claim cites a source, with inline citations of the form `(source-id)` or `(source-id §X.Y)`.

Paraphrase, do not copy verbatim. Verbatim quotes are allowed only as short blockquotes (≤3 lines) with attribution.

Humans curate, agents maintain.

Plays are frozen at creation. To revise an analysis, write a new one. Old ones are not deleted.

The complete schema and operational workflows are in `AGENTS.md`.

## Language

The body content is in the organization's working language (Italian, English, French, whatever). The schema, frontmatter keys, and folder names are in English. This separation keeps the productizable layer (English schema) reusable across organizations while letting the substance live in whatever language the organization actually uses.
