# nodes/activities/

Atomic units of observed work: who does what. One activity per file, kebab-case id (typically `<unit-prefix>-<verb>`, e.g., `ops-quality-check`, `sales-contract-negotiation`).

Required frontmatter: `id`, `type: activity`, `performer` (person-id or role-id), `unit`, `description`, `fte`, `artifacts`, `inputs`, `outputs`, `stakeholders_touched`, `frequency` (`daily | weekly | monthly | on-demand`), `sources`.

Schema reference: [`Org/AGENTS.md` §activity](../../AGENTS.md). The body typically opens with a verbatim quote from the role-description source (≤3 lines, in blockquote, with attribution), followed by a paraphrase elaboration and cross-references to parent unit + adjacent activities.

Activities are the finest-grain decomposition of work in the structure. Playbooks (especially `ai-exposure`, `value-map`, `reshuffle`) operate primarily on this layer.
