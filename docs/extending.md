# Extending Playable Org

Three extension points. Read them in order.

## 1. Add a new playbook (most common)

The base playbooks are extension targets, not closed. To author a new analytical question:

```
"Voglio creare un playbook nuovo: <name>. <one-sentence question>. Avvia l'intervista new-playbook."
```

In English:

```
"I want to create a new playbook: <name>. <one-sentence question>. Start the new-playbook interview."
```

Claude follows `skills/playbooks/new-playbook/SKILL.md`. Five questions:

1. **What question does the playbook answer?** Must pass the repeatability test (would the org re-run this every quarter / after each restructuring?). One-shot questions are refused.
2. **What is the anchor?** `full-org` | `commitment` | `unit` | `activity-set` | `stakeholder-set`.
3. **What is the primitive?** Name + obligatory fields, with each field declaring its source (`structure` | `aei` | `agent` | `numerical-derived`).
4. **What proves a claim grounded?** For each obligatory field, the evidence rule (structure path exists, AEI traceability, numerical traceability, external citation).
5. **Which viewer pattern?** Tabular distribution | 2-axis map | bundle bands | layered stack.

The meta-skill picks the closest base playbook (default: value-map for 2-axis maps), forks the four files (`SKILL.md`, `build.py`, `audit.py`, `viewer.py`), and adds a row to `skills/ROADMAP.md` with status `pending`.

The new playbook stays `pending` until first run audit-passes against a real anchor.

**Constraints**:
- The new viewer.py uses `from design import ...` and only design primitives. No bespoke `<style>` blocks beyond a slim playbook-specific extension.
- The new audit.py declares at least one rule per obligatory field from question 3.
- The first run of the new playbook is the test that flips it from `pending` to `done`.

## 2. Add a new mcp tool (rarer)

If you need a primitive the existing 12 tools don't cover, add one:

1. Create `mcp-server/src/tools/<name>.ts`. Use the existing tools as templates. Note the safety patterns: path-traversal containment via `safeResolve`, no shell injection, deterministic JSON output.
2. Register the tool in `mcp-server/src/server.ts`.
3. Update the tool count assertion in `mcp-server/test-e2e.py`.
4. Add at least three tests: success path, error path, security boundary (path traversal or similar).
5. Document in `docs/architecture.md` if the addition changes the surface area materially.

Run `cd mcp-server && npm run build && cd .. && python3 mcp-server/test-e2e.py` to verify.

## 3. Modify the design system (rarer still)

`skills/design.py` is the single source of truth for visual identity. Modifications affect every playbook viewer.

When to add a primitive:
- Multiple existing playbooks would benefit from the same UI element.
- The element fits the Anthropic-style aesthetic: hairline rules, monochrome palette, sober typography, minimal animation, no shadows.

When **not** to add a primitive:
- Only one playbook needs it. It belongs in that playbook's slim EXTRA_CSS.
- It introduces a new font family (single-family rule: Inter only).
- It introduces shadows or thick borders or coloured backgrounds beyond state accents (warn / error / ok / info).

Process:
1. Add the CSS rules to the appropriate section of `_base_css()` in `design.py`. Use existing tokens (`--fg`, `--muted`, `--line`, `--bg`, spacing scale `--s-1` through `--s-11`).
2. Add a helper function (e.g., `def my_primitive(...) -> str:`).
3. Document the helper in this file under "Available primitives" if substantive.
4. Update existing viewers if the change makes a previously bespoke pattern available as a primitive.
5. Bump the visual-version comment at the top of `design.py`.

## Available primitives (current)

From `skills/design.py`:

- `shell(body)` — centred page wrapper.
- `header(eyebrow, title, sub)` — page header with all-caps eyebrow + h1 + optional subtitle.
- `rule()` — hairline divider.
- `footer(left, right)` — left-aligned + right-aligned footer text on hairline.
- `section(num, title, hint)` — numbered section header (e.g., `01 · TIER 1 · STRUCTURE` with right-aligned hint).
- `stat_grid(stats, cols)` — grid of (number, label) stats with hairline rules; cols ∈ {2, 3, 4}.
- `pill(label, kind)` — status pill; kind ∈ {`neutral`, `error`, `warn`, `ok`, `info`}.
- `code(text)` — mono inline label for ids and codes.
- `item(meta_html, head, body, refs)` — issue / activity / signal row with left meta and right body.
- `item_list(items)` — vertical list of items with hairline separators.
- `card(name, tag, desc, meta, tag_accent, on_click)` — capability / component card.
- `card_grid(cards, cols)` — grid of cards; cols ∈ {1, 2}.
- `modal_shell(modal_id)` — modal HTML scaffold.
- `modal_script(modal_id)` — modal open/close JS (pair with `pnOpenModal(title, html)`).
- `modal_field(label, value)` — labelled field inside a modal.

## Forks for instance content

If you're using Playable Org for a real organization, fork this repo and keep your fork private (or public, your call). The public template is updated occasionally with new mcp tools, new playbooks, fixes. To pull those into your fork:

```bash
git remote add upstream https://github.com/<user>/playable-org
git fetch upstream
git merge upstream/main
```

The public template never modifies `org/` content beyond the three identity stubs, so merge conflicts are unlikely.

## See also

- [`docs/architecture.md`](architecture.md) — why the system is built this way.
- [`docs/playbooks.md`](playbooks.md) — reference for the four base playbooks.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — rules for proposing changes upstream.
