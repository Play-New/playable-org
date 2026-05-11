# Contributing

Pull requests welcome. This file describes the lay of the land and the rules.

## Project structure

```
playable-org/
├── org/                  empty starter (3 identity stubs); your instance content goes here
├── mcp-server/           TypeScript stdio mcp server, exposes 13 tools to Claude Desktop
├── skills/               agent-followed recipes + analytical playbooks + design system
│   ├── CAPABILITIES.md   four-property pattern for capabilities (referenced by world-model)
│   ├── STYLE.md          anti-rhetoric writing charter applied to consumer-facing prose
│   ├── ROADMAP.md        order of the four base playbooks + meta-skill
│   ├── design.py         single source of truth for the visual language
│   ├── _assets/          embedded fonts + design assets
│   ├── ingest/           one-source-at-a-time ingest workflow
│   ├── lint/             quality control workflow
│   ├── init/             one-time bulk ingest (first install)
│   └── playbooks/        ai-exposure, value-map, reshuffle, world-model, new-playbook
├── docs/                 architecture, playbooks reference, extension guide
├── install.{sh,command,bat,ps1}  installers
├── lint.py, lint-semantic.py  Tier 1 + Tier 2 lint
├── make-zip.sh           build the customer-shippable zip
├── SETUP.md              user-facing setup guide
└── README.md, LICENSE, CONTRIBUTING.md
```

## What goes where

Three layers, kept distinct.

**`org/`** is your instance content. Forks of this repo populate it. The public template ships with three empty identity stubs.

**`mcp-server/`** is the bridge from Claude Desktop to `org/`. It exposes 13 tools. Adding a new tool = adding a TypeScript file under `src/tools/`, registering it in `src/server.ts`, and writing a test in `test-e2e.py`.

**`skills/`** is what the agent does. Each skill is a `SKILL.md` recipe (sometimes plus Python scripts for playbooks that need numerical work). `design.py` is the only place visual decisions live. Adding a playbook = creating a folder under `skills/playbooks/` with a `SKILL.md` that follows the established shape.

## Rules for changes

### `org/` (the instance)

The public template stays empty. Do not commit your organization's content here. If you want to share an example instance, fork separately and link from the README.

### `mcp-server/`

- TypeScript only.
- Every new tool gets a test in `mcp-server/test-e2e.py`.
- Tools that spawn subprocesses (`org_lint_run`, `org_play_run`, `org_open`) must keep their argument validation strict — paths constrained to the repo, no shell injection vectors.
- The `org_save_source` invariant (sources are immutable) is non-negotiable; PRs that allow overwriting `sources/` are rejected.
- Keep tool descriptions in English and concise. They are read by the agent and shown to users.

### `skills/`

- All skill content (SKILL.md, Python, design.py) is in **English**.
- Skills compose mcp tools, they do not bypass them. If a skill needs a primitive that doesn't exist, add an mcp tool first.
- Playbooks must produce a JSON + audit + viewer triplet. The viewer must use only `design.py` primitives — no bespoke `<style>` blocks beyond a small playbook-specific extension that uses design tokens.
- The four base playbooks have declared theoretical lineage. New playbooks proposed via PR should declare the same: which authors, which papers, what the playbook adapts.

### `design.py`

Single source of truth for visual language. Adding a primitive = adding a CSS class + helper function + documentation in `docs/extending.md` if the addition affects multiple viewers.

Do not introduce: shadows (Anthropic-style is hairline-and-spacing), em dashes in CSS-generated copy, animations beyond simple opacity/transform transitions, multiple font families.

### Tests

`mcp-server/test-e2e.py` is the contract. Every tool change updates a test. Run via:

```bash
cd mcp-server && npm run build
cd .. && python3 mcp-server/test-e2e.py
```

Lint passes:

```bash
python3 lint.py            # Tier 1: structural
python3 lint-semantic.py   # Tier 2: semantic metrics
```

The test fixture for tool tests is `mcp-server/test-fixtures/sample-org/` (the Outline & Co. fake creative studio — a fully populated org with 5 units, 14 activities, 5 people, 4 stakeholders, 4 commitments, 3 sources, and the four canonical playbook artefacts under `plays/data/`).

## Forks for instance content

If you populate this template for a real organization, fork the repo and keep your fork private (or public, your call). Update `org/README.md` to declare your fork as an instance of this template.

The public template is updated occasionally with new mcp tools, new playbooks, fixes. To pull those into your fork:

```bash
git remote add upstream https://github.com/...
git fetch upstream
git merge upstream/main   # or cherry-pick specific commits
```

The public template never modifies `org/` content beyond the three identity stubs, so merge conflicts are unlikely.

## Author names rule

Names of analytical-framework authors (Wardley, Choudary, Dorsey, Botha, Cicero, Karpathy, etc.) appear only in `skills/` documentation, in this `CONTRIBUTING.md`, and in the public-facing `README.md`. They never appear under `org/` (which is the structure of facts cited from primary sources). Playbook output (viewer copy, modal text, agent chat replies about a play) follows the same rule: the methodology is described, the author is not named.

## License

By contributing you agree your contribution is licensed under the same MIT License as the project. See [LICENSE](LICENSE).
