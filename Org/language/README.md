# language/

Domain terms specific to this organization. Flat glossary, one file per term, kebab-case id matching the canonical form of the term.

Required frontmatter: `id`, `type: language-term`, `description` (≤200 characters), `sources`. Optional `related` (other term ids or node ids).

Schema reference: [`Org/AGENTS.md` §language-term](../AGENTS.md). The body opens with the canonical definition citing the source, followed by usage notes, abbreviations, and cross-references where the term appears in the rest of the structure.

Examples of what belongs here: program names internal to the organization, regulatory acronyms specific to the jurisdiction or sector, naming conventions inherited from history. Generic English / Italian vocabulary does not belong here.
