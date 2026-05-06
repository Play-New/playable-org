# nodes/units/

Organizational units: divisions, areas, teams, governance bodies. One file per unit, kebab-case id matching the filename.

Required frontmatter: `id`, `type: unit`, `level` (`division | area | team | governance-body`), `description`, `head_role`, `n_persons`, `authority_basis`, `sources`. Optional `parent` to link upward.

Schema reference: [`Org/AGENTS.md` §unit](../../AGENTS.md). The body is one to three paragraphs describing the unit's perimeter in plain language, with inline citations.
