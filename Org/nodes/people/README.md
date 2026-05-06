# nodes/people/

Named individuals currently holding a role in the organization. One file per person, kebab-case id (typically a surname or first-name + initial).

Required frontmatter: `id`, `type: person`, `role`, `unit`, `status` (`active | exiting | departed`), `description`, `sources`. Optional `since: YYYY-MM-DD`.

Schema reference: [`Org/AGENTS.md` §person](../../AGENTS.md). The body is short (a few sentences), citing the source that names the person — typically an organizational chart or HR document. Biographical detail is not required at structure time.
