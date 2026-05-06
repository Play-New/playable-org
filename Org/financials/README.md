# financials/

Market view of the organization: annual snapshot, revenue lines, headcount, operating costs by division. One file per summary, kebab-case id (e.g., `financial-snapshot-2024`, `revenue-lines-2024`, `headcount`, `cost-by-division`).

Required frontmatter: `id`, `type: financial-summary`, `dated` (year), `description`, `sources`.

Schema reference: [`Org/AGENTS.md` §financial-summary](../AGENTS.md). The body is prose with tables and inline citations to the financial source (typically the annual report or audited statements).

Financial nodes are the bridge between the structure (units, activities, commitments) and the dimension that makes them tractable in business terms: revenue per line, cost per division, headcount per area. Playbooks can read this layer to surface quantitative signals alongside the structural ones.
