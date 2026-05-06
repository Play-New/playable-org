# plays/

Point-in-time interpretations of the structure, produced by playbooks. Distinct from the cited facts in the rest of `org/`.

A play is the output of one playbook applied to one slice of the structure on one date. It is **frozen at creation**: once written, it records that interpretation at that moment. To revise an analysis, write a new play with today's date. Old plays are not deleted.

Required frontmatter: `type: play`, `playbook` (the skill name), `target` (slice or node ids), `dated` (YYYY-MM-DD), `frozen: true`, `sources`. Each playbook adds its own schema-specific fields — see `<repo>/skills/playbooks/<name>/SKILL.md`.

## Subfolders

`data/` holds the structured artefacts the playbook scripts emit (JSON map, interactive HTML viewer, optional SVG). When a play has a markdown summary as well, the `.md` file lives at the root of `plays/` and references the artefacts in `data/` by relative path.

## How to invoke

Playbooks are invoked through Claude Desktop in plain language ("Run the value-map for [anchor]", "Build the world-model"). Claude reads `<repo>/skills/playbooks/<name>/SKILL.md`, walks the structure, calls `org_play_run` to execute the playbook scripts. Output lands here.
