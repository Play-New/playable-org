# plays/data/

Generated artefacts from playbook runs. JSON (the structured map), HTML (the interactive viewer), optional SVG (a static fallback for embedding).

This folder is populated by `org_play_run` (see `<repo>/skills/playbooks/<name>/SKILL.md`). Files here are dated and treated as frozen — overwriting them would break the audit trail of when an analysis was produced. To re-run a playbook, generate a new file with today's date.
