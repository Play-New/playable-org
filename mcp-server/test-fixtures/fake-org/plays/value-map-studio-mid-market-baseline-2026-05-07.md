---
id: value-map-studio-mid-market-baseline-2026-05-07
type: play
playbook: value-map
target: studio-mid-market-baseline
dated: 2026-05-07
frozen: true
sources: [outline-charter-2024, outline-roles-2025, outline-annual-review-2025]
references:
  - map_json: plays/data/value-map-studio-mid-market-baseline-2026-05-07.json
  - map_svg:  plays/data/value-map-studio-mid-market-baseline-2026-05-07.svg
  - map_html: plays/data/value-map-studio-mid-market-baseline-2026-05-07.html
---

# Value-map · studio ↔ mid-market clients · 2026-05-07

## Anchor and end users

The cardinal commitment of the studio: deliver the strategy → identity → digital product flow on a fixed-price 12-16 week scope (outline-charter-2024 §15). The end user is the [mid-market client](../nodes/stakeholders/mid-market-clients.md). The user need is a coherent package — positioning + identity + digital artefact — delivered on time at the price agreed at pitch.

The map walks the four committed areas — [strategy](../nodes/units/strategy.md), [design](../nodes/units/design.md), [digital product](../nodes/units/digital-product.md), [client services](../nodes/units/client-services.md) — and the twelve activities reachable from them.

## The map

See `plays/data/value-map-studio-mid-market-baseline-2026-05-07.html` for the interactive viewer. Static SVG at `plays/data/value-map-studio-mid-market-baseline-2026-05-07.svg`.

## Per-component placement (audit-grounded)

Components grouped by stage on the evolution axis.

### Custom-built (0.17 → 0.40)

The bespoke craft territory. Where the studio differentiates today.

- **brand-positioning** (0.30, vis 0.65) — written craft, owned by [Marco Bellini](../nodes/people/marco-bellini.md). Not delegated (outline-roles-2025).
- **visual-language** (0.28, vis 0.60) — defined by the design lead per engagement (outline-roles-2025).
- **brand-book** (0.32, vis 0.85) — the studio's signature artefact. Built personally by [Lena Thorvaldsen](../nodes/people/lena-thorvaldsen.md) on every engagement, not delegated (outline-roles-2025).

### Product / rental (0.40 → 0.70)

The "product" tier. Multiple vendors do this; the studio competes on execution quality.

- **strategy** unit (0.42, vis 0.55) — the area as a whole.
- **design** unit (0.45, vis 0.70).
- **identity-system-build** (0.45, vis 0.72) — senior designer-owned (outline-roles-2025).
- **audience-research** (0.40, vis 0.50) — strategy lead + one strategist (outline-roles-2025).
- **ux-research** (0.50, vis 0.40) — embedded with client product team (outline-roles-2025).
- **competitive-audit** (0.52, vis 0.45) — strategists on assigned engagements (outline-roles-2025).
- **digital-product** unit (0.55, vis 0.78).
- **ui-design** (0.58, vis 0.85) — senior product designers, paired with client front-end (outline-roles-2025).
- **design-system-build** (0.65, vis 0.55) — mid-level product designers documenting for client handoff (outline-roles-2025).

### Commodity / utility (0.70 → 1.00)

Standard-of-market practice. Every agency runs these. No differentiation lives here.

- **client-services** unit (0.72, vis 0.92).
- **asset-handover** (0.75, vis 0.95) — the moment of delivery (outline-roles-2025).
- **kickoff-workshop** (0.78, vis 0.95) — runs at engagement start, scope agreement (outline-roles-2025).
- **weekly-check-in** (0.82, vis 0.90) — account managers run three each (outline-roles-2025).

## Decisions this play enables

Five concrete questions a leader at Outline can take to the next monthly studio review.

### 1. Where to invest in tighter templating?

The four client-services activities (kickoff, weekly check-in, asset handover) sit at evolution 0.72 → 0.82 — already commodity. Tightening templates here saves time but does not gain margin. Real margin lives in the **custom-built tier** (brand-book, brand-positioning, visual-language at 0.28 → 0.32).

**Move:** invest templating effort in the *commodity tier so it consumes less senior time*. Free that senior time to the *custom-built tier*. Concretely: Tomás's account managers should be able to run 4 engagements each instead of 3 within a year, freeing Tomás's hours for the upstream pitch-scoping and kickoff workshop concentration. Source: [outline-roles-2025](../sources/outline-roles-2025.md).

### 2. Which roles are most exposed if AI commoditizes their day-to-day?

The activities at evolution 0.50+ that are repetitive and well-defined: weekly-check-in (0.82), competitive-audit (0.52), ui-design (0.58). The roles running these are account managers, strategists, and senior product designers respectively.

**Move:** the roles running these activities should not be the same roles defined as the studio's differentiation. Today the strategy lead writes positioning (custom, 0.30) but also signs the competitive audits (product, 0.52). Splitting those activities across role types — and having juniors specialize on the productized activities — is a hedge against the AI-commoditization scenario. Source: [outline-charter-2024](../sources/outline-charter-2024.md) §10 (junior development).

### 3. Where can the studio raise prices?

Pricing power lives in two places: high evolution × high visibility (clients pay because they cannot easily substitute), or low evolution × high visibility (clients pay because the artefact is differentiated craft).

The studio's strongest pricing positions:
- **brand-book** (0.32, 0.85) — bespoke + visible. Already where the studio's reputation lives. Pricing should reflect this.
- **kickoff-workshop** (0.78, 0.95) — commodity but ultra-visible. Cannot raise prices on the commodity dimension; can re-frame as discovery + scoping not just kickoff.

**Move:** the brand-book is currently absorbed in the engagement scope. Carving out a brand-book retainer post-engagement (annual updates, evolution of the system) is a high-margin cross-sell with low senior-time demand. Source: [studio-employees-development](../commitments/studio-employees-development.md), [outline-roles-2025](../sources/outline-roles-2025.md).

### 4. Which engagement components are at greatest risk of becoming undifferentiated?

UI-design (0.58, 0.85) and design-system-build (0.65, 0.55) are at the product tier with high visibility. Clients can compare them to other studios' equivalent work. As more competitors offer design systems and accessibility-baked-in UI, these activities drift further toward commodity.

**Move:** the differentiation hedge is **the upstream link**. UI-design that flows from a custom-built positioning + brand book is hard to commoditize because the input is unique. UI-design as a standalone deliverable is easy to commoditize. The studio should refuse pure-product engagements that don't include strategy + identity upstream — which the charter already does (outline-charter-2024 §1: "we turn down purely tactical work"). The play confirms the charter's positioning is correct.

### 5. What does the value chain say about the next hire?

The map shows no component owned at the production-handoff layer. Every discipline lead manages their own vendor partner relationships, and every engagement passes through asset-handover (commodity, 0.75) without a dedicated owner above the account-manager tier. As the studio grows toward the 30-person cap (outline-charter-2024 §20), this becomes a single point of failure.

**Move:** before the next discipline-area headcount expansion, hire a **production lead** — one person who owns vendor partner relationships across all four client-facing areas, owns asset-handover quality, and owns the studio's vendor partner SLA conversations. This consolidates today's fragmented production handoffs into a named role and frees discipline leads from vendor-management overhead. Source: [outline-roles-2025](../sources/outline-roles-2025.md), [outline-annual-review-2025](../sources/outline-annual-review-2025.md) (vendor spend €0.6M, no named owner above operations).

## Method limits

The map has no AI overlay (no `ai_effect`, no `evolution_target`) because there are no Anthropic Economic Index matches attached for this fixture. The five decisions above use the structural facts of the studio (charter §§, role descriptions, annual review numbers) but do not draw on observed AI-usage data. With AEI matches attached the play would include directional arrows showing where each component is being pushed, and decisions 2 and 4 would be sharper.

The component placements are agent-authored from the structural sources. A different agent might place ui-design at 0.55 instead of 0.58, or weekly-check-in at 0.85 instead of 0.82 — the precise number is judgement; the band (custom / product / commodity) is the load-bearing claim.

## Cross-references

- Source: [outline-charter-2024](../sources/outline-charter-2024.md) — the studio's positioning and governance.
- Source: [outline-roles-2025](../sources/outline-roles-2025.md) — who runs what across the five areas.
- Source: [outline-annual-review-2025](../sources/outline-annual-review-2025.md) — 2025 numbers feeding decision 1 (operating margin 24%) and decision 5 (vendor spend €0.6M).
- Anchor commitment: [studio-mid-market-baseline](../commitments/studio-mid-market-baseline.md).
- Stakeholder: [mid-market-clients](../nodes/stakeholders/mid-market-clients.md).
