# sources/

Raw source documents. Immutable. Source of truth. Everything else in `org/` is paraphrase cited from these.

## How to populate

Drop documents here in any of these formats: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.md`, `.html`, `.txt`. Use kebab-case filenames (e.g., `articles-of-association-2024.pdf`, `org-chart-2026-q1.docx`).

The first time you populate `org/`, drop everything you have here, then in chat run:

> Initialize the structure from `sources/`.

The `init` skill iterates each document, extracts entities, proposes nodes in batches, writes on your confirmation. After this first session, the `ingest` skill handles documents one at a time as they arrive.

## What goes here

Anything that documents the organization in primary form:

- Founding documents: charter, articles of association, statute
- Governance documents: governance charter, ethics code, compliance/risk frameworks
- Organizational charts (current and historical)
- Role-description documents (per area or per division)
- Financial reports (annual report, audited statements)
- Process documentation (internal SOPs, workflow descriptions)
- People analyses (HR reports, capability assessments)
- External analyses already produced about the organization

## What does NOT go here

- Personal data of named people beyond what's already in public-facing documents.
- Confidential client/customer data unless you intend the graph to be the system of record for that.
- Anything that would compromise privacy of individuals or violate regulations if it landed on a developer's laptop during a backup.

`sources/` is a local directory. The graph lives on your computer. The decision of what to ingest is yours.

## Citations

Once a document is here, it has a source-id (the filename without extension). Other nodes cite it inline with `(source-id)` or `(source-id §X.Y)`. The `lint` skill verifies that every cited source-id corresponds to a real file here.
