# nodes/roles/

Position types, separate from the person holding them. One file per role, kebab-case id (e.g., `head-of-operations`, `area-lead-finance`).

Required frontmatter: `id`, `type: role`, `unit`, `description`, `activities`, `sources`. Optional `reports_to`.

Schema reference: [`org/AGENTS.md` §role](../../AGENTS.md). The body describes the position's responsibilities in plain language with inline citations to the source (typically a role-description document or governance charter).

The role exists independently of the person. When a person changes, the role node stays; the `nodes/people/<id>.md` file is updated.
