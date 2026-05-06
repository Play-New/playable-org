# nodes/stakeholders/

External entities that interact with the organization: donors, partners, suppliers, regulators, peers, customers. One file per stakeholder type, kebab-case id (typically describing the category, e.g., `corporate-customers`, `regulator-data-protection`).

Required frontmatter: `id`, `type: stakeholder`, `kind` (`donor | partner | supplier | regulator | institution | peer | customer`), `description`, `engagement_mode`, `sources`.

Schema reference: [`Org/AGENTS.md` §stakeholder](../../AGENTS.md). The body describes the stakeholder type in plain language: what they receive from the organization, what they contribute back, the most honest signal the organization records about them.

Stakeholder nodes are typically the endpoint of cardinal commitments registered in `commitments/`.
