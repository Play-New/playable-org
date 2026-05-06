# commitments/

Cardinal relationships between nodes: org-stakeholder, inter-organization, cross-unit, role-role, person-person. One file per commitment, kebab-case id describing the parties (e.g., `org-customer-base-delivery`, `ops-finance-handover`).

Required frontmatter: `id`, `type: commitment`, `parties_committing`, `parties_benefiting`, `level` (`person | role | unit | org-stakeholder | inter-org`), `direction` (`reciprocal | unilateral`), `explicit` (`yes | no`), `terms`, `conditions`, `consequences_if_broken`, `state` (`active | degraded | broken`), `fallback` (`designed | partial | none`), `lifecycle`, `sources`.

Schema reference: [`Org/AGENTS.md` §commitment](../AGENTS.md).

A commitment is registered only if it passes three tests in AND: cited in a source, load-bearing (its breaking causes articulable harm), non-redundant (not already documented as a Cross-area section in a unit body). See `AGENTS.md` for the full rule.
