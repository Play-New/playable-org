#!/usr/bin/env python3
"""
ai-exposure / viewer.py: Generate a static HTML viewer for match results.

Visual style inspired by Anthropic's Job Explorer (anthropic.com/economic-index).
Each activity is a card with a grid of small colored squares: one square per
top-K match: colored by classification.

Output: a single self-contained HTML file (vanilla HTML/CSS/JS, no external deps).

Usage:
    python3 viewer.py --matches <matches.json>
                      [--metadata <metadata.json>]
                      [--lang en|it]
                      [--task-translations <translations.json>]
                      --out viewer.html [--title "..."]

The optional --metadata file enriches the cards. It is a JSON list of
{id, title, description, area, unit, ...} objects (same id as in matches).
Without it, only id is shown on each card.

The optional --task-translations file is a JSON dict {english_task: translated_task}
that lets the viewer display O*NET task names in the target UI language.
Translations can be produced by any pipeline (manual, LLM-assisted, MT): the
viewer just consumes the dict.

Color scheme per match:
    green   = rich + autonomy ≥ p75 (mostly automated)
    purple  = rich + autonomy in [p25, p75] (mostly augmented)
    light   = rich + autonomy < p25 (assistive)
    beige   = fallback (not in Anthropic rich subset)
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path
from typing import Any

# Shared App-pure shell: palette, body, mobile baseline, chrome
# helpers, modal, favicon, font. The viewer composes on top.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from design import (  # noqa: E402
    app_pure_about_modal_html,
    app_pure_baseline_js,
    app_pure_css,
    app_pure_dateline_html,
    app_pure_head_meta,
    app_pure_modal_html,
    app_pure_top_right_html,
    inline_md,
)


EXTRA_CSS = """
/* ai-exposure viewer: App-pure scroll-on-paper. The shared shell in
   skills/design.py provides palette, typography, mobile baseline,
   dateline + Analysis CTA + modal + colophon + safe-area + favicon.
   This file adds only the playbook-specific viz: heatmap squares
   (one per top-K AEI match, coloured by category), area sections,
   activity cards, popover-on-click, and the bottom legend. */

:root {
  /* Category colours: ai-exposure's four levels mapped onto the
     Carta sbiadita data-viz palette (sage / lilac / slate / sand). */
  --automated: var(--k-activity);   /* sage  · mostly automated */
  --augmented: var(--k-stakeholder);/* lilac · mostly augmented */
  --assistive: var(--k-unit);       /* slate · assistive */
  --no-data:   var(--k-role);       /* sand  · outside observed sample */
  --low-conf:  var(--ink-25);
}

/* Filter row: sits directly below the chrome (dateline + ? +
   Analysis CTA) and above the dashboard. Carries the unit pills
   and the live "N of M activities" counter on the right. */
.filter-row {
  display: flex; align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  max-width: 1440px;
  margin: max(70px, calc(env(safe-area-inset-top) + 64px)) auto 18px;
  padding: 0 max(28px, env(safe-area-inset-left))
           0 max(28px, env(safe-area-inset-right));
}
.filter-row .summary {
  margin-left: auto;
  font-size: 11.5px;
  color: var(--ink-60);
  font-style: italic;
  letter-spacing: -0.005em;
  white-space: nowrap;
}

/* Dashboard: full viewport width, fills the rest of the screen
   with activity cards. The "?" popover holds the explanatory
   chrome. */
.dashboard {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 max(28px, env(safe-area-inset-left))
           max(80px, calc(env(safe-area-inset-bottom) + 60px))
           max(28px, env(safe-area-inset-right));
}
@media (max-width: 760px) {
  .filter-row {
    margin-top: max(56px, calc(env(safe-area-inset-top) + 50px));
    padding: 0 14px;
    gap: 8px;
  }
  /* Pills scroll horizontally on narrow viewports: small chevron
     would help but the system scrollbar is enough as a primer. */
  .filter-row .filter-pills {
    overflow-x: auto;
    flex-wrap: nowrap;
    scrollbar-width: none;
  }
  .filter-row .filter-pills::-webkit-scrollbar { display: none; }
  .filter-row .summary { display: none; }
  .filter-row .unit-filter-label { display: none; }
  .dashboard { padding: 0 14px max(80px, calc(env(safe-area-inset-bottom) + 60px)); }
}

/* Legend: small inline strip under the intro. */
.legend {
  display: flex; gap: 22px; flex-wrap: wrap;
  font-size: 12.5px; color: var(--ink-60);
  align-items: center; margin: 22px 0 28px;
}
.legend-item { display: flex; align-items: center; gap: 8px; }
.legend-square {
  width: 12px; height: 12px;
  border-radius: 2px;
  display: inline-block;
  box-shadow: 0 0 0 1px rgba(28,26,22,0.12) inset;
}
.legend-square.automated { background: var(--automated); }
.legend-square.augmented { background: var(--augmented); }
.legend-square.assistive { background: var(--assistive); }
.legend-square.no-data { background: var(--no-data); }

/* Activity cards: paper, hairline border, no shadow. Each card has
   the activity title + description + a small grid of K coloured
   squares (one per AEI match). */
.card {
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 4px;
  padding: 18px 18px 16px;
}
.card.low-confidence { opacity: 0.55; }
.card-title {
  font-size: 14.5px;
  font-weight: 540;
  letter-spacing: -0.012em;
  color: var(--ink);
  line-height: 1.3;
  margin: 0 0 4px;
  text-wrap: pretty;
}
.card-id {
  font-size: 10.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-40);
  margin: 0 0 10px;
}
.card-desc {
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--ink-80);
  margin: 0 0 14px;
  text-wrap: pretty;
}
.task-grid {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.task-square {
  width: 22px;
  height: 22px;
  border-radius: 2px;
  cursor: pointer;
  background: var(--no-data);
  box-shadow: 0 0 0 1px rgba(28,26,22,0.10) inset;
  transition: transform 0.12s ease;
}
.task-square:hover { transform: scale(1.18); }
.task-square.automated { background: var(--automated); }
.task-square.augmented { background: var(--augmented); }
.task-square.assistive { background: var(--assistive); }
.task-square.no-data { background: var(--no-data); }
.task-square.low-confidence { background: var(--low-conf); }
.card-stat {
  font-size: 11px;
  color: var(--ink-40);
  font-style: italic;
  letter-spacing: -0.005em;
}

/* Area sections: one editorial-width header per organizational area,
   then the cards for that area span the wider grid. */
.area-section { margin: 56px 0 0; }
.area-section:first-of-type { margin-top: 32px; }
.area-section h2 {
  font-size: 19px;
  font-weight: 540;
  letter-spacing: -0.018em;
  margin: 0 0 6px;
}
.area-section .area-meta {
  font-size: 12px;
  color: var(--ink-60);
  font-style: italic;
  margin: 0 0 12px;
}
.area-desc {
  font-size: 13.5px;
  color: var(--ink-95);
  line-height: 1.55;
  margin: 0 0 14px;
  text-wrap: pretty;
}
.area-notes {
  margin: 14px 0 0;
  padding: 12px 14px;
  background: var(--paper-2);
  border-left: 2px solid var(--hairline);
  border-radius: 3px;
  font-size: 12.5px;
  line-height: 1.55;
}
.area-notes-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin-bottom: 6px;
}
.desc-label, .area-notes-label {
  font-family: inherit;
}

/* Stat row + distribution bar (org overview). */
.stats-row {
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
  font-size: 12.5px;
  color: var(--ink-60);
  margin: 14px 0;
}
.stats-row strong { color: var(--ink); font-weight: 540; }
.dist-bar {
  display: flex;
  height: 10px;
  border-radius: 2px;
  overflow: hidden;
  margin: 12px 0;
  background: var(--paper-2);
}
.dist-bar > div { height: 100%; }
.dist-bar .seg.automated { background: var(--automated); }
.dist-bar .seg.augmented { background: var(--augmented); }
.dist-bar .seg.assistive { background: var(--assistive); }
.dist-bar .seg.no-data { background: var(--no-data); }

/* Popover: small floating card opened on click of a task square.
   `position: absolute` so it stays anchored to the clicked square's
   document position; the JS uses document-coordinate maths. */
.popover {
  position: absolute;
  display: none;
  max-width: 360px;
  min-width: 260px;
  padding: 16px 20px 18px;
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 4px;
  box-shadow: 0 4px 18px rgba(28,26,22,0.10);
  z-index: 50;
  font-size: 12.5px;
  line-height: 1.55;
}
.popover.open { display: block; }
.popover .close {
  position: absolute;
  top: 8px; right: 10px;
  background: transparent; border: 0;
  cursor: pointer;
  font: inherit; font-size: 16px;
  color: var(--ink-40);
  padding: 2px 6px;
  line-height: 1;
}
.popover .close:hover { color: var(--ink); }
.popover h3 {
  font-size: 14px;
  font-weight: 540;
  letter-spacing: -0.012em;
  margin: 0 0 4px;
  padding-right: 20px;
  text-wrap: pretty;
}
.popover .eyebrow {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin-bottom: 6px;
}
.popover .pop-id {
  font-family: ui-monospace, SF Mono, Menlo, monospace;
  font-size: 10.5px;
  color: var(--ink-40);
  margin-bottom: 10px;
}
.popover .pop-task {
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--ink-95);
  padding: 10px 12px;
  background: var(--paper-2);
  border-radius: 3px;
  margin-bottom: 10px;
}
.popover .pop-task strong { font-weight: 540; }
.popover dl {
  margin: 0;
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 4px 14px;
  font-size: 11.5px;
}
.popover dt { color: var(--ink-60); margin: 0; }
.popover dd { margin: 0; color: var(--ink); }
.popover .pop-chain {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--hairline-2);
  font-size: 10.5px;
  color: var(--ink-60);
  font-style: italic;
  line-height: 1.55;
}
.popover .pop-chain strong {
  font-style: normal; color: var(--ink-80); font-weight: 540;
}

/* Empty state when filters return no results. */
.empty {
  text-align: center;
  padding: 64px 0;
  color: var(--ink-40);
  font-size: 13px;
  font-style: italic;
}

/* Unit filter label (used inside .filter-row above the dashboard). */
.unit-filter-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  white-space: nowrap;
}
.filter-pills {
  display: flex; gap: 6px;
  flex-wrap: wrap;
}
.pill {
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  padding: 5px 12px 6px;
  cursor: pointer;
  font: inherit;
  font-size: 11.5px;
  letter-spacing: -0.005em;
  color: var(--ink);
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
  white-space: nowrap;
}
.pill:hover { border-color: var(--ink); }
.pill.active {
  background: var(--ink);
  border-color: var(--ink);
  color: var(--paper);
}

/* JS-produced classes: preserved from the v4 viewer with the
   palette swapped to Carta sbiadita. Listed flat here so the JS in
   render_html doesn't need any change. */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
@media (min-width: 1100px) {
  .grid { grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 18px; }
}
@media (min-width: 1440px) {
  .grid { grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
}
.area-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
  gap: 56px;
  margin: 0 0 28px;
  align-items: start;
}
@media (max-width: 1100px) {
  .area-head { grid-template-columns: 1fr; gap: 24px; }
}
.area-head-left, .area-head-right { min-width: 0; }
.summary {
  font-size: 12.5px; color: var(--ink-60);
  margin: 14px 0 22px; font-style: italic;
}
.summary-label, .desc-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin-bottom: 8px;
}
.org-overview { margin: 0 0 48px; }
.org-overview .label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin-bottom: 12px;
}
.org-desc {
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--ink-95);
  margin: 0 0 18px;
  text-wrap: pretty;
}
.dist-legend {
  display: flex; gap: 18px; flex-wrap: wrap;
  font-size: 11.5px;
  color: var(--ink-60);
  margin-top: 8px;
}
.dist-legend .item { display: flex; align-items: center; gap: 6px; }
.dist-legend .swatch {
  width: 11px; height: 11px;
  border-radius: 2px;
  display: inline-block;
}
.dist-legend .swatch.automated { background: var(--automated); }
.dist-legend .swatch.augmented { background: var(--augmented); }
.dist-legend .swatch.assistive { background: var(--assistive); }
.dist-legend .swatch.no-data { background: var(--no-data); }

/* Closest-match block (inline inside each card). */
.closest-match {
  padding: 10px 12px;
  margin: 12px 0;
  background: var(--paper-2);
  border-radius: 3px;
  font-size: 12px;
  line-height: 1.55;
}
.closest-match .label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin-bottom: 6px;
}
.closest-match .task-it { color: var(--ink); margin-bottom: 4px; }
.closest-match .task-en { color: var(--ink-60); font-style: italic; font-size: 11px; }
.closest-match .metrics {
  display: flex; gap: 14px; margin-top: 8px; flex-wrap: wrap;
  font-size: 11px;
}
.closest-match .metric strong { font-weight: 540; color: var(--ink); }
.closest-match .metric .key { color: var(--ink-60); margin-right: 3px; }
.closest-match.no-rich .warn { color: var(--ink-60); font-size: 11px; margin-top: 6px; }

/* Card stat + level-tag pill. */
.card-stat .level-tag {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 2px;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  margin-right: 8px;
  color: var(--ink);
}
.level-tag.strong { background: var(--automated); }
.level-tag.medium { background: var(--augmented); }
.level-tag.mixed { background: var(--assistive); }
.level-tag.zero { background: var(--no-data); }
.level-tag.low-confidence {
  background: transparent;
  border: 1px solid var(--hairline);
  color: var(--ink-60);
}
.card.low-confidence .task-grid::before {
  content: "Low confidence: top-1 similarity below threshold.";
  width: 100%;
  font-size: 11px;
  color: var(--ink-60);
  padding: 8px 10px;
  background: var(--paper-2);
  border-radius: 2px;
  margin-bottom: 6px;
}

/* Area section override: single editorial column above its cards. */
.area-section { margin-top: 56px; padding-top: 28px; border-top: 1px solid var(--hairline-2); }

/* Bottom colophon strip: same shape as the canvas viewers. */
.colophon-strip {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  z-index: 5;
  padding: 12px max(28px, env(safe-area-inset-right))
           max(14px, calc(env(safe-area-inset-bottom) + 10px))
           max(28px, env(safe-area-inset-left));
  display: flex; justify-content: space-between; align-items: center;
  gap: 16px;
  font-size: 11px;
  font-style: italic;
  color: var(--ink-40);
  letter-spacing: -0.005em;
  background: linear-gradient(to bottom, transparent, var(--paper) 55%);
  pointer-events: none;
}
.colophon-strip strong {
  font-style: normal; color: var(--ink-80); font-weight: 540;
}

@media (max-width: 760px) {
  .activity-grid {
    grid-template-columns: 1fr;
    padding: 0 14px;
  }
  .colophon-strip { font-size: 10px; padding: 8px 14px; }
}
"""

# Legacy CSS (pre-v5) intentionally removed below. All chrome and viz
# classes used by the JS-rendered content are now defined in EXTRA_CSS
# above (App-pure scroll-on-paper).
_LEGACY_CSS_REMOVED = """
.dist-legend { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.78rem; color: var(--fg-muted); margin-top: 8px; }
.dist-legend .item { display: flex; align-items: center; gap: 6px; }
.dist-legend .swatch { width: 11px; height: 11px; border-radius: 2px; display: inline-block; }
.dist-legend .swatch.automated { background: var(--automated); }
.dist-legend .swatch.augmented { background: var(--augmented); }
.dist-legend .swatch.assistive { background: var(--assistive); }
.dist-legend .swatch.no-data { background: var(--no-data); }

/* Per-area sections. The head spans the container width with a
   two-column layout: title + scope on the left, distribution on the
   right. The card grid below fills the full container with smaller
   cards so more fit per row on wide displays. */
.area-section { margin: 0 0 72px; padding-top: 36px; border-top: 1px solid var(--fg-hairline); }
.area-section .area-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: 56px; margin: 0 0 28px; align-items: start; }
@media (max-width: 1100px) { .area-section .area-head { grid-template-columns: 1fr; gap: 24px; } }
.area-section .area-head-left { min-width: 0; }
.area-section .area-head-right { min-width: 0; }
.area-section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; margin: 0 0 14px; letter-spacing: -0.02em; }
.area-section .area-desc { font-size: 0.95rem; color: var(--fg); line-height: 1.7; margin: 0 0 0; }
.area-section .desc-label, .area-section .summary-label, .area-section .area-notes-label { font-family: var(--font-display); font-size: 0.7rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 8px; font-weight: 500; }
.area-section .area-notes { margin-top: 18px; font-size: 0.92rem; line-height: 1.7; color: var(--fg); }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
/* Activity cards: full border, padding, hover signal. Even though
   the wrapper itself isn't the click target (the inner task-squares
   are), the border gives the activity a clean visual frame consistent
   with the other playbooks. */
.card { background: transparent; border: 1px solid var(--fg-hairline); border-radius: 4px; padding: 18px 20px; transition: border-color 0.15s; }
.card-title { font-family: var(--font-display); font-size: 1.0rem; font-weight: 500; margin: 0 0 4px; line-height: 1.35; color: var(--fg); letter-spacing: -0.01em; }
.card-id { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.68rem; color: var(--fg-muted); margin-bottom: 12px; }
.card-desc { font-size: 0.88rem; color: var(--fg-muted); margin-bottom: 14px; line-height: 1.55; }

/* Closest-match block: nested inside .card, distinguished by a
   subtle background tint, not by another border. */
.closest-match { padding: 10px 12px; margin: 14px 0; background: var(--bg-alt); border-radius: 3px; font-size: 0.85rem; line-height: 1.55; }
.closest-match .label { font-family: var(--font-display); font-size: 0.66rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px; font-weight: 500; }
.closest-match .task-it { color: var(--fg); margin-bottom: 4px; }
.closest-match .task-en { color: var(--fg-muted); font-style: italic; font-size: 0.78rem; }
.closest-match .metrics { display: flex; gap: 14px; margin-top: 8px; font-size: 0.78rem; flex-wrap: wrap; }
.closest-match .metric strong { font-weight: 500; color: var(--fg); }
.closest-match .metric .key { color: var(--fg-muted); margin-right: 3px; }
.closest-match.no-rich .warn { color: var(--fg-muted); font-size: 0.78rem; margin-top: 6px; }

.task-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 3px; margin: 12px 0 14px; max-width: 200px; }
.task-square { aspect-ratio: 1; border-radius: 2px; cursor: pointer; transition: transform 0.1s; position: relative; }
.task-square:hover { transform: scale(1.15); outline: 1.5px solid var(--fg); z-index: 5; }
.task-square.automated { background: var(--automated); }
.task-square.augmented { background: var(--augmented); }
.task-square.assistive { background: var(--assistive); }
.task-square.no-data { background: var(--no-data); }

.card-stat { font-size: 0.82rem; color: var(--fg-muted); padding-top: 10px; }
.card-stat .level-tag { display: inline-block; padding: 1px 8px; border-radius: 2px; font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.10em; color: #FFFFFF; margin-right: 8px; font-weight: 500; }
.level-tag.strong { background: var(--automated); color: var(--fg); }
.level-tag.medium { background: var(--augmented); color: var(--fg); }
.level-tag.mixed { background: var(--assistive); color: var(--fg); }
.level-tag.zero { background: var(--no-data); color: var(--fg); }
.level-tag.low-confidence { background: var(--low-conf); color: var(--fg); }

.card.low-confidence .task-grid::before { content: "Low confidence: top-1 similarity below threshold."; grid-column: 1 / -1; font-size: 0.76rem; color: var(--fg-muted); padding: 8px 10px; background: var(--bg-alt); border-radius: 2px; }
.card.low-confidence .task-grid { max-width: none; }

/* Decisions section: centered editorial column, same as value-map and world-model. */
.section { max-width: 820px; margin: 96px auto 0; padding-top: 40px; border-top: 1px solid var(--fg-hairline); }
.section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 20px; }
.section p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; max-width: 720px; }
.section .lead { font-size: 0.95rem; color: var(--fg-muted); line-height: 1.65; max-width: 720px; margin: 0 0 28px; }

.decision { margin-bottom: 32px; }
.decision .question { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; color: var(--fg); margin: 0 0 8px; letter-spacing: -0.01em; }
.decision .answer { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 6px; max-width: 720px; }
.decision .source { font-size: 0.78rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }

/* Popover: small floating card next to the clicked square. Replaces
   the full-screen modal: pop-overs read as 'a tooltip you can read',
   not 'a page you have to dismiss'. */
.popover { position: absolute; display: none; max-width: 360px; min-width: 240px; padding: 14px 18px 16px; background: #FFFFFF; border: 1px solid var(--fg-hairline); border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); z-index: 100; animation: pn-pop 0.18s ease; }
.popover.open { display: block; }
.popover .close { position: absolute; top: 6px; right: 8px; background: transparent; border: 0; cursor: pointer; font-size: 1.1rem; color: var(--fg-muted); padding: 0; line-height: 1; }
.popover .close:hover { color: var(--fg); }
.popover .eyebrow { font-family: var(--font-display); font-size: 0.62rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px; color: var(--fg-muted); }
.popover h3 { font-family: var(--font-display); font-size: 1rem; font-weight: 500; letter-spacing: -0.015em; margin: 0 0 4px; line-height: 1.25; color: var(--fg); padding-right: 18px; }
.popover .pop-id { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.7rem; color: var(--fg-muted); margin-bottom: 12px; }
.popover .pop-task { font-size: 0.85rem; line-height: 1.55; color: var(--fg); padding: 10px 12px; background: var(--bg-alt); border-radius: 3px; margin-bottom: 10px; }
.popover .pop-task strong { font-weight: 500; }
.popover dl { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 4px 14px; font-size: 0.82rem; }
.popover dt { color: var(--fg-muted); margin: 0; }
.popover dd { margin: 0; color: var(--fg); }
.popover .pop-chain { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--fg-hairline); font-size: 0.76rem; color: var(--fg-muted); line-height: 1.5; }
.popover .pop-chain strong { color: var(--fg); font-weight: 500; }

.empty { text-align: center; padding: 64px 0; color: var(--fg-muted); font-size: 0.95rem; }

.footer { max-width: 820px; margin: 80px auto 0; padding-top: 20px; border-top: 1px solid var(--fg-hairline); color: var(--fg-muted); font-size: 0.78rem; line-height: 1.6; }
.footer p { margin: 0; }
"""

P25 = 3.21
P75 = 3.57

STRINGS = {
    "en": {
        "subtitle": "How AI usage observed in the public Claude sample maps onto each activity this organization actually does, by matching every activity to the closest tasks in a public catalog of work.",
        "intro_h2": "What this map is",
        "intro_p1": "Each activity on the page is a piece of work this organization actually does. For each one, the system finds the five closest tasks in a public catalog of about 18,500 occupations, and shows how Claude was used on those tasks in a sample of public conversations. The colour key is in the legend below.",
        "intro_p2": "Every activity is shown with five matches. Picking only the single closest one would be fragile: that match is often partially right. Five squares show whether the pattern holds across the nearby matches. Five greens means Claude reliably worked alone on tasks like this in the sample. A mix of colours means the signal is noisier and worth taking with a pinch of salt.",
        "intro_p3": "Click any square to read the matched task in its original wording, how close it is to the activity, how Claude was used on it, and how big the sample behind the observation is.",
        "legend_automated": "Mostly automated",
        "legend_augmented": "Mostly augmented",
        "legend_assistive": "Assistive",
        "legend_no_data": "Outside the observed sample",
        "search_label": "Search",
        "search_placeholder": "Words from the activity title or description",
        "signal_label": "Signal",
        "unit_label": "Unit",
        "all": "All",
        "all_units": "Entire org",
        "analysis_btn": "Analysis",
        "help_btn_label": "What is this map?",
        "level_strong": "High signal",
        "level_medium": "Some signal",
        "level_mixed": "Low signal",
        "level_zero": "No signal",
        "level_low_confidence": "Low confidence",
        "summary": "{n} of {total} activities",
        "no_match": "No activities match the current filter.",
        "footer": "Source: Anthropic's public release of how Claude was used across a sample of conversations (March 2026 release, around 18,500 work-task descriptions from the public US occupational catalog). The matching uses a multilingual sentence-similarity model. Activities are kept only when the closest match is at least 55% similar; below that the read isn't reliable.",
        "closest_match": "Closest O*NET task",
        "confidence": "Confidence",
        "automation": "Automation",
        "low_conf_hint": "Low confidence: top-1 similarity below threshold.",
        "no_unit": "(no area)",
        "activities_count": "{n} activities",
        "tooltip_click": "Click for details",
        "tooltip_conv_one": "1 conversation on Claude.ai",
        "tooltip_conv_many": "{n} conversations on Claude.ai",
        "tooltip_no_data": "outside the observed sample",
        "tooltip_aut": "autonomy {x}/5",
        "modal_task_label": "Closest O*NET task (original, EN)",
        "modal_task_it_label": "Suggested Italian translation",
        "modal_confidence": "Confidence (cosine similarity)",
        "modal_autonomy": "Average autonomy in Claude conversations",
        "modal_count": "Sample size (Claude.ai conversations)",
        "modal_count_warn_small": "small sample: interpret cautiously",
        "modal_category": "Anthropic category for the sample",
        "modal_no_rich": "Below the minimum activity count for stable estimates. The square is shown as 'no data'.",
        "modal_chain": "What this card actually says",
        "modal_chain_text": "this org's activity → closest match in the public catalog of work → category from how Claude was used on that catalog task in the Anthropic sample. The category describes that sample. Reading it back onto the org's activity depends on how close the two really are.",
        "area_summary_label": "Snapshot",
        "area_distribution": "Distribution",
        "area_avg_confidence": "Avg. top-1 confidence",
        "area_avg_automation": "Avg. automation (where data)",
        "area_evidence_total": "Evidence base (Claude.ai conversations across all top matches)",
        "area_evidence_thin": "thin",
        "area_evidence_moderate": "moderate",
        "area_evidence_solid": "solid",
        "area_most": "Strongest signal",
        "area_least": "Weakest signal",
        "area_no_strong": "no activity rated 'strong' in this area",
        "area_no_weak": "no zero-signal activity in this area",
        "area_notes_label": "Notes",
        "area_no_data_full": "No autonomy data observed for any activity in this area (all closest matches fall outside the sample).",
        "org_overview_label": "Organization snapshot",
        "area_description_label": "Scope",
        "task_distribution_label": "O*NET task distribution (top-K matches)",
        "matches_label": "matches",
        "activities_label": "activities",
    },
    "it": {
        "subtitle": "Come l'uso di AI osservato nel campione pubblico Claude si mappa su ogni attività che questa organizzazione fa, cercando la mansione più vicina in un catalogo pubblico del lavoro.",
        "intro_h2": "Cos'è questa mappa",
        "intro_p1": "Ogni attività in pagina è un pezzo di lavoro che l'organizzazione fa davvero. Per ognuna il sistema cerca le cinque mansioni più vicine in un catalogo pubblico di circa 18.500 occupazioni, e mostra come Claude è stato usato su quelle mansioni in un campione di conversazioni pubbliche. La legenda dei colori è qui sotto.",
        "intro_p2": "Ogni attività è mostrata con cinque match. Prendere solo la mansione più vicina sarebbe fragile: quel singolo match spesso è parzialmente azzeccato. Cinque quadratini mostrano se il pattern regge attraverso le mansioni vicine. Cinque verdi vuol dire che Claude ha lavorato in autonomia su mansioni simili nel campione. Un mix di colori vuol dire che il segnale è più rumoroso e va preso con cautela.",
        "intro_p3": "Click su qualunque quadratino per leggere la mansione nella sua formulazione originale, quanto è vicina all'attività, come Claude è stato usato, e quanto è ampio il campione dietro l'osservazione.",
        "legend_automated": "Claude lavorava in autonomia (4-5 su 5)",
        "legend_augmented": "Claude assisteva con supervisione (3-4 su 5)",
        "legend_assistive": "Claude usato come strumento puntuale (1-3 su 5)",
        "legend_no_data": "Mansione fuori dal campione osservato",
        "search_label": "Cerca",
        "search_placeholder": "Parole dal titolo o dalla descrizione dell'attività",
        "signal_label": "Segnale",
        "unit_label": "Unit",
        "all": "Tutto",
        "all_units": "Tutta l'organizzazione",
        "analysis_btn": "Analisi",
        "help_btn_label": "Cos'è questa mappa?",
        "level_strong": "Forte: Claude in autonomia su almeno 3 mansioni vicine",
        "level_medium": "Medio: almeno 5 mansioni vicine assistite o autonome",
        "level_mixed": "Misto: mansioni vicine con dati spariti",
        "level_zero": "Nessun dato osservato sulle mansioni vicine",
        "level_low_confidence": "Match incerto (mansione troppo distante)",
        "summary": "{n} di {total} attività",
        "no_match": "Nessuna attività corrisponde al filtro corrente.",
        "footer": "Fonte: campione Anthropic delle conversazioni Claude (release 2026-03-24, 18.510 mansioni del catalogo americano dei mestieri). Soglia minima di vicinanza per considerare il match utile: 55%.",
        "closest_match": "Mansione più vicina nel catalogo americano dei mestieri",
        "confidence": "Vicinanza",
        "automation": "Autonomia di Claude",
        "low_conf_hint": "Match incerto: la mansione più vicina nel catalogo è troppo distante per fidarsi del dato.",
        "no_unit": "(senza area)",
        "activities_count": "{n} attività",
        "tooltip_click": "Click per il dettaglio numerico",
        "tooltip_conv_one": "osservato su 1 conversazione Claude.ai (campione minimo)",
        "tooltip_conv_many": "osservato su {n} conversazioni Claude.ai",
        "tooltip_no_data": "mansione fuori dal campione osservato",
        "tooltip_aut": "autonomia Claude {x}/5 (1=solo aiuto, 5=lavoro autonomo)",
        "modal_task_label": "Mansione più vicina nel catalogo americano (testo originale in inglese)",
        "modal_task_it_label": "Traduzione italiana di lavoro",
        "modal_confidence": "Quanto la mansione del catalogo è vicina all'attività (in %)",
        "modal_autonomy": "Quanto Claude lavorava in autonomia in quelle conversazioni (1=solo aiuto, 5=lavoro autonomo)",
        "modal_count": "Su quante conversazioni Claude.ai si basa l'osservazione",
        "modal_count_warn_small": "campione piccolo, indicazione fragile",
        "modal_category": "Etichetta del campione Anthropic",
        "modal_no_rich": "Per questa mansione il campione Anthropic non ha dato osservato (nessuna conversazione Claude o sotto soglia minima). Il quadratino compare come 'fuori dati'.",
        "modal_chain": "Cosa dice davvero questo riquadro",
        "modal_chain_text": "La catena: attività dell'organizzazione → mansione più vicina nel catalogo americano dei mestieri → categoria che Anthropic ha dato alle conversazioni Claude su quella mansione. L'etichetta descrive il campione Anthropic. Riferirla all'attività dell'organizzazione è un salto separato, che dipende da quanto le due cose sono davvero vicine. Le distanze fra mansioni del catalogo USA e attività italiane di una fondazione possono essere reali.",
        "area_summary_label": "In sintesi",
        "area_distribution": "Come si dividono le mansioni vicine",
        "area_avg_confidence": "Vicinanza media della mansione più vicina",
        "area_avg_automation": "Autonomia media osservata di Claude (dove c'è dato)",
        "area_evidence_total": "Totale conversazioni Claude.ai osservate sulle mansioni vicine",
        "area_evidence_thin": "campione limitato",
        "area_evidence_moderate": "campione moderato",
        "area_evidence_solid": "campione solido",
        "area_most": "Attività con segnale più forte",
        "area_least": "Attività con segnale più debole",
        "area_no_strong": "nessuna attività di quest'area mostra Claude in autonomia su almeno 3 mansioni vicine",
        "area_no_weak": "tutte le attività di quest'area hanno almeno qualche dato osservato",
        "area_notes_label": "Commento all'area",
        "area_no_data_full": "Nessuna metrica di automazione disponibile per quest'area (tutti i match sono fuori dal sottoinsieme ricco Anthropic).",
        "org_overview_label": "L'organizzazione in una pagina",
        "area_description_label": "Cosa fa quest'area",
        "task_distribution_label": "Come si dividono le mansioni vicine (5 per ogni attività)",
        "matches_label": "match (5 per attività)",
        "activities_label": "attività",
    },
}

LEVEL_LABEL = {
    "en": {"strong": "Strong", "medium": "Medium", "mixed": "Mixed", "zero": "Zero", "low-confidence": "Low conf"},
    "it": {"strong": "forte", "medium": "medio", "mixed": "misto", "zero": "zero", "low-confidence": "bassa conf"},
}

CAT_LABEL = {
    "en": {"automated": "automated", "augmented": "augmented", "assistive": "assistive", "no-data": "no data"},
    "it": {"automated": "automatizzata", "augmented": "aumentata", "assistive": "assistiva", "no-data": "fuori dati"},
}


def fmt_num(value: float, lang: str, decimals: int = 1) -> str:
    s = f"{value:.{decimals}f}"
    return s.replace(".", ",") if lang == "it" else s


SAMPLE_SMALL_THRESHOLD = 100


def classify_match(m: dict) -> str:
    aut = m.get("ai_autonomy_mean")
    if aut is None:
        return "no-data"
    aut = float(aut)
    if aut >= P75:
        return "automated"
    if aut >= P25:
        return "augmented"
    return "assistive"


def classify_activity(activity: dict) -> dict:
    if activity.get("low_confidence"):
        return {"level": "low-confidence", "n_rich": 0, "n_total": 0, "categories": {}}
    matches = activity["matches"]
    cats = {"automated": 0, "augmented": 0, "assistive": 0, "no-data": 0}
    for m in matches:
        cats[classify_match(m)] += 1
    rich = matches and any(m.get("ai_autonomy_mean") for m in matches)
    if not rich:
        level = "zero"
    elif cats["automated"] >= 3:
        level = "strong"
    elif cats["automated"] + cats["augmented"] >= 5:
        level = "medium"
    else:
        level = "mixed"
    return {"level": level, "n_rich": cats["automated"] + cats["augmented"] + cats["assistive"], "n_total": len(matches), "categories": cats}


def render_html(matches: list[dict], title: str, metadata: dict[str, dict], lang: str = "en", task_translations: dict[str, str] | None = None, area_notes: dict[str, str] | None = None, area_descriptions: dict[str, str] | None = None, org_description: str = "", decisions: list[dict] | None = None) -> str:
    if lang not in STRINGS:
        lang = "en"
    S = STRINGS[lang]
    LEVELS = LEVEL_LABEL[lang]
    CATS = CAT_LABEL[lang]
    translations = task_translations or {}

    classified = []
    for a in matches:
        c = classify_activity(a)
        meta = metadata.get(a["id"], {}) if metadata else {}
        # Annotate each match with optional Italian translation.
        annotated = []
        for m in a.get("matches", []):
            mm = dict(m)
            t = m.get("task") or ""
            if t in translations:
                mm["task_it"] = translations[t]
            annotated.append(mm)
        # Resolution order for `_unit`: explicit metadata field if
        # passed via --metadata, else the `_unit` already on the
        # activity match (populated by the build/match step from the
        # activity's frontmatter `unit` field), else empty.
        unit_value = meta.get("unit") or a.get("_unit") or ""
        classified.append({
            **a,
            "matches": annotated,
            **c,
            "_title": meta.get("title") or a.get("label") or a["id"],
            "_description": meta.get("description") or a.get("description") or "",
            "_unit": unit_value,
        })

    levels = [c["level"] for c in classified]
    counts = {lv: levels.count(lv) for lv in ("strong", "medium", "mixed", "zero", "low-confidence")}

    # Distinct areas, sorted
    units = sorted({c["_unit"] for c in classified if c["_unit"]})

    data_js = json.dumps(classified, ensure_ascii=False)
    strings_js = json.dumps(S, ensure_ascii=False)
    levels_js = json.dumps(LEVELS, ensure_ascii=False)
    cats_js = json.dumps(CATS, ensure_ascii=False)
    area_notes_js = json.dumps(area_notes or {}, ensure_ascii=False)
    area_desc_js = json.dumps(area_descriptions or {}, ensure_ascii=False)
    org_desc_escaped = (org_description or "").replace("</", "<\\/")

    # --- App-pure chrome assembly ---
    n_activities = len(classified)
    n_units = len(units)
    org_name = (
        # Resolution order: explicit metadata `_org` if present, else
        # one of the JSON-level fields the build pipeline may have
        # populated, else generic "AI exposure".
        (metadata.get("_org") if isinstance(metadata, dict) else None)
        or "AI exposure"
    )
    # Filled by main() from the JSON payload, set on metadata if
    # present. Fallback to today's date so the chrome never renders
    # the literal em dash placeholder STYLE.md bans.
    from datetime import date as _date
    dated = ""
    if isinstance(metadata, dict):
        dated = metadata.get("_dated", "")
    if not dated:
        dated = _date.today().isoformat()
    if lang == "it":
        what_html = "esposizione all'AI · attività × catalogo pubblico del lavoro"
    else:
        what_html = "ai exposure · activities × public catalog of work"

    # Decisions go into the shared Analysis modal.
    has_decisions = bool(decisions)
    modal_html_str = ""
    if has_decisions:
        from html import escape as _esc
        items = []
        for d in decisions:
            q = _esc(d.get("question", ""))
            ans_paragraphs = "".join(
                f"<p>{inline_md(p)}</p>"
                for p in (d.get("answer", "") or "").split("\n\n")
                if p.strip()
            )
            src = _esc(d.get("source", ""))
            src_html = f'<p class="source">{src}</p>' if src else ""
            items.append(f"<li><h3>{q}</h3>{ans_paragraphs}{src_html}</li>")
        kicker = "Reading the map" if lang == "en" else "Come leggere questa mappa"
        headline = (
            f"{n_activities} activities, mapped against the public catalog of work."
            if lang == "en"
            else f"{n_activities} attività, viste attraverso il catalogo pubblico del lavoro."
        )
        modal_html_str = app_pure_modal_html(
            headline=headline,
            org_name=org_name,
            dated=dated or "",
            decisions_html="".join(items),
            kicker=kicker,
            lede="",
        )

    # About-modal body: the editorial intro behind the "?" button.
    # Plain-language definitions of every category, no jargon (per
    # skills/STYLE.md). The colour-coded labels on the squares above
    # are otherwise opaque to a leader reading this for the first time.
    if lang == "it":
        colour_defs = """
  <h2>Cosa vogliono dire i colori dei quadratini</h2>
  <p><strong>Per lo più automatizzata</strong>: sulle mansioni del catalogo più vicine a questa attività, nel campione pubblico Claude ha lavorato in autonomia. Nella maggior parte delle conversazioni l'umano non è dovuto intervenire.</p>
  <p><strong>Per lo più aumentata</strong>: Claude e l'umano hanno lavorato insieme. Entrambi hanno contribuito al risultato.</p>
  <p><strong>Assistiva</strong>: Claude ha dato una mano (cercare informazioni, suggerire bozze). L'umano è rimasto in guida e ha preso le decisioni.</p>
  <p><strong>Fuori dal campione osservato</strong>: nessuna conversazione pubblica con Claude nel campione corrispondeva abbastanza a questa attività. Vuol dire "non lo sappiamo da questo campione". Vuol dire anche che il colore non si può leggere come "qui Claude non si usa": semplicemente il campione non lo riporta.</p>
"""
    else:
        colour_defs = """
  <h2>What the colours mean</h2>
  <p><strong>Mostly automated</strong>: on the public-catalog tasks closest to this activity, Claude in the sample handled the work on its own. In most of those conversations the human didn't step in.</p>
  <p><strong>Mostly augmented</strong>: the human and Claude worked together. Both contributed to the result.</p>
  <p><strong>Assistive</strong>: Claude helped (looking things up, drafting, summarising). The human stayed in the lead and made the calls.</p>
  <p><strong>Outside the observed sample</strong>: no public Claude conversation in the sample was close enough to this activity. Read as "we don't know from this sample". The colour does not say "Claude isn't used here"; the sample just doesn't report it.</p>
"""

    about_body = f"""
  <p class="lede">{escape(S['subtitle'])}</p>

  <h2>{escape(S['intro_h2'])}</h2>
  <p>{escape(S['intro_p1'])}</p>
  <p>{escape(S['intro_p2'])}</p>
  <p>{escape(S['intro_p3'])}</p>

{colour_defs}

  <div class="legend">
    <div class="legend-item"><span class="legend-square automated"></span>{escape(S["legend_automated"])}</div>
    <div class="legend-item"><span class="legend-square augmented"></span>{escape(S["legend_augmented"])}</div>
    <div class="legend-item"><span class="legend-square assistive"></span>{escape(S["legend_assistive"])}</div>
    <div class="legend-item"><span class="legend-square no-data"></span>{escape(S["legend_no_data"])}</div>
  </div>

  <div id="org-overview"></div>
"""
    about_modal_html_str = app_pure_about_modal_html(
        kicker=f"№ {n_activities:02d} · ai exposure",
        headline=title,
        lede="",
        body_html=about_body,
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
{app_pure_head_meta(f"{title} · ai exposure")}
<style>{app_pure_css(layout="scroll") + EXTRA_CSS}</style>
</head>
<body>

{app_pure_dateline_html(org_name, what=what_html)}

{app_pure_top_right_html(dated, show_analysis=has_decisions, show_help=True,
                          analysis_label=S.get("analysis_btn", "Analysis"),
                          help_label=S.get("help_btn_label", "What is this map?"))}

<!-- Filter row + dashboard live in the body directly. Editorial
     intro / legend / org snapshot are behind the "?" button. -->
<div class="filter-row">
  <span class="unit-filter-label">{escape(S.get("unit_label", "Unit"))}</span>
  <div class="filter-pills" id="filter-unit">
    <button class="pill active" data-unit="all">{escape(S.get("all_units", "Entire org"))}</button>
    {''.join(f'<button class="pill" data-unit="{escape(u)}">{escape(u)}</button>' for u in units)}
  </div>
  <span class="summary" id="summary"></span>
</div>

<section class="dashboard">
  <div id="content"></div>
  <div class="empty" id="empty" style="display:none">{escape(S["no_match"])}</div>
</section>

{about_modal_html_str}

<!-- Hidden inputs the legacy JS binds to (search box + signal-level
     filter dropped from the App-pure UI). Display:none on the wrapper. -->
<div style="display:none">
  <input id="search" />
  <div id="filter-level">
    <button class="pill active" data-level="all"></button>
  </div>
</div>

<div class="colophon-strip">
  <span><strong>{n_activities}</strong> activities · <strong>{n_units}</strong> areas</span>
  <span>{S['footer'][:80]}…</span>
</div>

<div class="popover" id="popover">
  <button class="close" id="popover-close" aria-label="Close">×</button>
  <div id="popover-body"></div>
</div>

{modal_html_str}

<script>
{app_pure_baseline_js()}
</script>

<script>
const data = {data_js};
const S = {strings_js};
const LEVELS = {levels_js};
const CATS = {cats_js};
const AREA_NOTES = {area_notes_js};
const AREA_DESCRIPTIONS = {area_desc_js};
const ORG_DESCRIPTION = {json.dumps(org_desc_escaped, ensure_ascii=False)};
const SAMPLE_SMALL = {SAMPLE_SMALL_THRESHOLD};

function classifyMatch(m) {{
  if (m.ai_autonomy_mean == null) return 'no-data';
  const aut = m.ai_autonomy_mean;
  if (aut >= 3.57) return 'automated';
  if (aut >= 3.21) return 'augmented';
  return 'assistive';
}}

function escapeHtml(s) {{
  return String(s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }})[c]);
}}

let currentLevel = 'all';
let currentUnit = 'all';
let currentQuery = '';

function applyFilters() {{
  const q = currentQuery.trim().toLowerCase();
  return data.filter(d => {{
    if (currentLevel !== 'all' && d.level !== currentLevel) return false;
    if (currentUnit !== 'all' && d._unit !== currentUnit) return false;
    if (q) {{
      const blob = `${{d._title}} ${{d._description}} ${{d.id}} ${{d._unit}}`.toLowerCase();
      if (!blob.includes(q)) return false;
    }}
    return true;
  }});
}}

function categoryDistribution(items) {{
  // Aggregate task-level (per-match) distribution across categories.
  const cats = {{automated: 0, augmented: 0, assistive: 0, 'no-data': 0}};
  let simSum = 0, simN = 0;
  let convTotal = 0;
  for (const d of items) {{
    for (const m of (d.matches || [])) {{
      if (!m) continue;
      cats[classifyMatch(m)]++;
      if (m.similarity != null) {{ simSum += m.similarity; simN++; }}
      if (m.count != null) convTotal += m.count;
    }}
  }}
  const total = cats.automated + cats.augmented + cats.assistive + cats['no-data'];
  return {{
    n: items.length,
    cats,
    total,
    avgConfidence: simN ? simSum / simN : null,
    convTotal,
  }};
}}

function renderDistBar(cats, total) {{
  if (total === 0) return '';
  const seg = (cls) => {{
    const v = cats[cls];
    if (v === 0) return '';
    const pct = (v / total) * 100;
    return `<div class="seg ${{cls}}" style="width:${{pct}}%" title="${{CATS[cls]}}: ${{v}} (${{Math.round(pct)}}%)"></div>`;
  }};
  return `<div class="dist-bar">${{seg('automated')}}${{seg('augmented')}}${{seg('assistive')}}${{seg('no-data')}}</div>`;
}}

function renderDistLegend(cats, total) {{
  if (total === 0) return '';
  const item = (cls) => {{
    const v = cats[cls];
    const pct = total ? Math.round(v / total * 100) : 0;
    return `<div class="item"><span class="swatch ${{cls}}"></span>${{CATS[cls]}} <strong>${{pct}}%</strong> (${{v}})</div>`;
  }};
  return `<div class="dist-legend">${{item('automated')}}${{item('augmented')}}${{item('assistive')}}${{item('no-data')}}</div>`;
}}

function renderOrgOverview() {{
  const dist = categoryDistribution(data);
  const desc = ORG_DESCRIPTION
    ? `<div class="org-desc">${{escapeHtml(ORG_DESCRIPTION).replace(/\\n/g, '<br>')}}</div>`
    : '';
  const stats = `<div class="stats-row">
    <div><strong>${{data.length}}</strong> ${{S.activities_label}}</div>
    <div><strong>${{dist.total}}</strong> ${{S.matches_label}}</div>
    <div><strong>${{dist.avgConfidence != null ? fmtPct(dist.avgConfidence) : '—'}}</strong> ${{S.area_avg_confidence}}</div>
    <div><strong>${{dist.convTotal}}</strong> Claude.ai conv.</div>
  </div>`;
  const distLabel = `<div class="label">${{S.task_distribution_label}}</div>`;
  return `
    <div class="org-overview">
      <div class="label">${{S.org_overview_label}}</div>
      ${{desc}}
      ${{stats}}
      ${{distLabel}}
      ${{renderDistBar(dist.cats, dist.total)}}
      ${{renderDistLegend(dist.cats, dist.total)}}
    </div>`;
}}

function renderAreaSummary(area, items) {{
  // Returns {{left, right}} so the caller can place each column in the
  // two-column .area-head layout.
  const dist = categoryDistribution(items);
  const description = AREA_DESCRIPTIONS[area];
  const descHtml = description
    ? `<div class="desc-label">${{S.area_description_label}}</div><div class="area-desc">${{escapeHtml(description)}}</div>`
    : '';
  const distLabel = `<div class="desc-label">${{S.task_distribution_label}}</div>`;
  const note = AREA_NOTES[area];
  let noteRendered = '';
  if (note) {{
    let safe = escapeHtml(note).replace(/\\n/g, '<br>');
    safe = safe.replace(/\\*([^*\\n]+?)\\*/g, '<em>$1</em>');
    noteRendered = `<div class="area-notes"><div class="area-notes-label">${{S.area_notes_label}}</div>${{safe}}</div>`;
  }}
  return {{
    left:  `${{descHtml}}${{noteRendered}}`,
    right: `${{distLabel}}${{renderDistBar(dist.cats, dist.total)}}${{renderDistLegend(dist.cats, dist.total)}}`,
  }};
}}

function fmtNum(value, decimals) {{
  if (value == null || isNaN(value)) return '—';
  const s = Number(value).toFixed(decimals);
  return S.summary.indexOf(' di ') >= 0 ? s.replace('.', ',') : s;
}}

function fmtPct(value) {{
  if (value == null || isNaN(value)) return '—';
  return Math.round(value * 100) + '%';
}}

function renderClosest(d) {{
  if (!d.matches || d.matches.length === 0) return '';
  const m = d.matches[0];
  if (!m) return '';
  const sim = fmtPct(m.similarity);
  const aut = m.ai_autonomy_mean != null ? `${{fmtNum(m.ai_autonomy_mean, 1)}} / 5` : '—';
  const taskIt = m.task_it || '';
  const taskEn = m.task || '';
  const cls = classifyMatch(m);
  const noRich = (m.ai_autonomy_mean == null);
  const itLine = taskIt ? `<div class="task-it">${{escapeHtml(taskIt)}}</div>` : '';
  const enLine = taskIt
    ? `<div class="task-en">${{escapeHtml(taskEn)}}</div>`
    : `<div class="task-it">${{escapeHtml(taskEn)}}</div>`;
  const metricsHtml = noRich
    ? `<div class="warn">${{escapeHtml(S.modal_no_rich)}}</div>`
    : `<div class="metrics">
         <div class="metric"><span class="key">${{S.confidence}}:</span><strong>${{sim}}</strong></div>
         <div class="metric"><span class="key">${{S.automation}}:</span><strong>${{aut}}</strong></div>
         <div class="metric"><span class="key">${{S.modal_count}}:</span><strong>${{m.count != null ? m.count : '—'}}${{(m.count != null && m.count < SAMPLE_SMALL) ? ' ⚠' : ''}}</strong></div>
       </div>`;
  return `
    <div class="closest-match ${{noRich ? 'no-rich' : ''}}">
      <div class="label">${{S.closest_match}}</div>
      ${{itLine}}
      ${{enLine}}
      ${{metricsHtml}}
    </div>`;
}}

function renderCard(d) {{
  const isLow = d.level === 'low-confidence';
  let squaresHtml = '';
  if (!isLow) {{
    // Render exactly the matches that exist: no padding to a fixed
    // grid size. With top-K = 5 (default) this gives 5 squares per
    // activity; the grid CSS wraps them into rows of 5.
    const real = d.matches.map((m, idx) => ({{m, idx, cls: classifyMatch(m)}}));
    const order = {{automated: 0, augmented: 1, assistive: 2, 'no-data': 3}};
    real.sort((a, b) => order[a.cls] - order[b.cls]);
    squaresHtml = real.map(s => {{
      const m = s.m;
      const cls = s.cls;
      const taskShort = (m.task_it || m.task || '');
      const taskTrunc = taskShort.length > 140 ? taskShort.slice(0, 140) + '…' : taskShort;
      const sim = fmtPct(m.similarity);
      const catLabel = CATS[cls] || cls;
      const countLine = (m.count != null)
        ? (m.count === 1 ? S.tooltip_conv_one : S.tooltip_conv_many.replace('{{n}}', m.count))
        : S.tooltip_no_data;
      const autLine = (m.ai_autonomy_mean != null) ? S.tooltip_aut.replace('{{x}}', fmtNum(m.ai_autonomy_mean, 1)) : '';
      const tail = [countLine, autLine].filter(Boolean).join(' · ');
      const label = `${{taskTrunc}}\\n\\n${{S.confidence}} ${{sim}} · ${{catLabel}}\\n${{tail}}\\n\\n${{S.tooltip_click}}`;
      return `<div class="task-square ${{cls}}" data-activity="${{escapeHtml(d.id)}}" data-idx="${{s.idx}}" data-tooltip="${{escapeHtml(label)}}"></div>`;
    }}).join('');
  }}
  const cats = d.categories || {{}};
  const stat = isLow
    ? `<span class="level-tag low-confidence">${{LEVELS['low-confidence']}}</span> ${{S.low_conf_hint}}`
    : `${{cats.automated || 0}} ${{CATS.automated}} · ${{cats.augmented || 0}} ${{CATS.augmented}} · ${{cats.assistive || 0}} ${{CATS.assistive}} · ${{cats['no-data'] || 0}} ${{CATS['no-data']}}`;
  const closest = isLow ? '' : renderClosest(d);
  return `
    <div class="card ${{isLow ? 'low-confidence' : ''}}">
      <div class="card-title">${{escapeHtml(d._title || d.id)}}</div>
      <div class="card-id">${{escapeHtml(d.id)}} · ${{escapeHtml(d._unit)}}</div>
      <div class="card-desc">${{escapeHtml(d._description || '')}}</div>
      ${{closest}}
      <div class="task-grid">${{squaresHtml}}</div>
      <div class="card-stat">${{stat}}</div>
    </div>`;
}}

function render() {{
  const items = applyFilters();
  const summary = document.getElementById('summary');
  const empty = document.getElementById('empty');
  const content = document.getElementById('content');
  const overview = document.getElementById('org-overview');

  // org overview only when no specific area filter is active.
  overview.innerHTML = (currentUnit === 'all') ? renderOrgOverview() : '';

  summary.textContent = S.summary.replace('{{n}}', items.length).replace('{{total}}', data.length);

  if (items.length === 0) {{
    content.innerHTML = '';
    empty.style.display = 'block';
    return;
  }}
  empty.style.display = 'none';

  // Group by area when "All areas" + no specific area filter
  if (currentUnit === 'all') {{
    const groups = {{}};
    items.forEach(d => {{
      const key = d._unit || S.no_unit;
      if (!groups[key]) groups[key] = [];
      groups[key].push(d);
    }});
    const sortedUnits = Object.keys(groups).sort();
    // When there is only one area (often the case for orgs without
    // area metadata, where everything falls into the "no_unit"
    // bucket), suppress the area-head: its per-area summary just
    // duplicates the org-overview already shown above. Render cards
    // flat in that case.
    if (sortedUnits.length === 1) {{
      const cards = groups[sortedUnits[0]].map(renderCard).join('');
      content.innerHTML = `<div class="grid">${{cards}}</div>`;
    }} else {{
    content.innerHTML = sortedUnits.map(area => {{
      const cards = groups[area].map(renderCard).join('');
      const summary = renderAreaSummary(area, groups[area]);
      return `
        <div class="area-section">
          <div class="area-head">
            <div class="area-head-left">
              <h2>${{escapeHtml(area)}}</h2>
              ${{summary.left}}
            </div>
            <div class="area-head-right">
              ${{summary.right}}
            </div>
          </div>
          <div class="grid">${{cards}}</div>
        </div>`;
    }}).join('');
    }}
  }} else if (currentUnit !== 'all') {{
    const summary = renderAreaSummary(currentUnit, items);
    content.innerHTML = `
      <div class="area-section">
        <div class="area-head">
          <div class="area-head-left">
            <h2>${{escapeHtml(currentUnit)}}</h2>
            ${{summary.left}}
          </div>
          <div class="area-head-right">
            ${{summary.right}}
          </div>
        </div>
        <div class="grid">${{items.map(renderCard).join('')}}</div>
      </div>`;
  }} else {{
    content.innerHTML = `<div class="grid">${{items.map(renderCard).join('')}}</div>`;
  }}
}}

document.querySelectorAll('#filter-level .pill').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('#filter-level .pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentLevel = btn.dataset.level;
    render();
  }});
}});

document.querySelectorAll('#filter-unit .pill').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('#filter-unit .pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentUnit = btn.dataset.unit;
    render();
  }});
}});

document.getElementById('search').addEventListener('input', e => {{
  currentQuery = e.target.value;
  render();
}});

// Popover positioning + click handlers: same shape as value-map.
const popoverEl   = document.getElementById('popover');
const popoverBody = document.getElementById('popover-body');

function showPopover(html, anchorRect) {{
  // Open the popover BELOW the clicked square, centered horizontally
  // on it. If there's not enough room below, flip above. Always
  // clamped inside the viewport.
  popoverBody.innerHTML = html;
  const margin = 12;
  popoverEl.style.left = '0px';
  popoverEl.style.top = '0px';
  popoverEl.classList.add('open');
  const r = popoverEl.getBoundingClientRect();
  const anchorCenterX = (anchorRect.left + anchorRect.right) / 2;
  const viewportRight  = window.scrollX + window.innerWidth;
  const viewportBottom = window.scrollY + window.innerHeight;
  let x = anchorCenterX - r.width / 2;
  if (x + r.width > viewportRight - margin) x = viewportRight - r.width - margin;
  if (x < window.scrollX + margin) x = window.scrollX + margin;
  let y = anchorRect.bottom + margin;
  if (y + r.height > viewportBottom - margin) {{
    const above = anchorRect.top - margin - r.height;
    if (above >= window.scrollY + margin) y = above;
    else y = viewportBottom - r.height - margin;
  }}

  popoverEl.style.left = x + 'px';
  popoverEl.style.top  = y + 'px';
}}

function hidePopover() {{
  popoverEl.classList.remove('open');
}}

document.addEventListener('click', e => {{
  // Square click → popover with task detail
  if (e.target.classList && e.target.classList.contains('task-square')) {{
    const aid = e.target.dataset.activity;
    const idx = parseInt(e.target.dataset.idx, 10);
    if (!aid || isNaN(idx)) return;
    const a = data.find(x => x.id === aid);
    if (!a) return;
    const m = a.matches[idx];
    if (!m) return;
    const cls = classifyMatch(m);
    const catLabel = CATS[cls] || cls;
    const countWarn = (m.count != null && m.count < SAMPLE_SMALL) ? ` <span style="color:var(--ds-coral)">(${{S.modal_count_warn_small}})</span>` : '';
    const richHtml = m.ai_autonomy_mean != null
      ? `<dl>
           <dt>${{S.modal_autonomy}}</dt><dd>${{fmtNum(m.ai_autonomy_mean, 2)}} / 5</dd>
           <dt>${{S.modal_count}}</dt><dd>${{m.count != null ? m.count : 0}}${{countWarn}}</dd>
           <dt>${{S.modal_category}}</dt><dd>${{catLabel}}</dd>
           <dt>${{S.modal_confidence}}</dt><dd>${{fmtPct(m.similarity)}}</dd>
         </dl>`
      : `<p style="color: var(--fg-muted); font-size: 0.82rem; margin: 0 0 10px">${{escapeHtml(S.modal_no_rich)}}</p>
         <dl>
           <dt>${{S.modal_category}}</dt><dd>${{catLabel}}</dd>
           <dt>${{S.modal_confidence}}</dt><dd>${{fmtPct(m.similarity)}}</dd>
         </dl>`;
    const taskItHtml = m.task_it ? `<div class="pop-task"><strong>${{escapeHtml(m.task_it)}}</strong><br><span style="color: var(--fg-muted); font-size: 0.78rem; font-style: italic">${{escapeHtml(m.task)}}</span></div>` : `<div class="pop-task">${{escapeHtml(m.task)}}</div>`;
    const html = `
      <div class="eyebrow">${{escapeHtml(a._unit || '')}}</div>
      <h3>${{escapeHtml(a._title || a.id)}}</h3>
      <div class="pop-id">${{escapeHtml(a.id)}}</div>
      ${{taskItHtml}}
      ${{richHtml}}
      <div class="pop-chain"><strong>${{S.modal_chain}}.</strong> ${{escapeHtml(S.modal_chain_text)}}</div>
    `;
    const r = e.target.getBoundingClientRect();
    showPopover(html, {{
      left:   r.left   + window.scrollX,
      right:  r.right  + window.scrollX,
      top:    r.top    + window.scrollY,
      bottom: r.bottom + window.scrollY,
    }});
    return;
  }}

  // Click outside the popover and outside any square → close
  let n = e.target;
  while (n && n.nodeType === 1) {{
    if (n.id === 'popover') return;
    n = n.parentNode;
  }}
  hidePopover();
}}, true);

document.getElementById('popover-close').addEventListener('click', hidePopover);
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') hidePopover(); }});

render();
</script>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a static HTML viewer for ai-exposure matches.")
    parser.add_argument("--matches", required=True, help="match.py output JSON")
    parser.add_argument("--out", required=True, help="Output HTML file")
    parser.add_argument("--title", default="ai-exposure viewer", help="Page title")
    parser.add_argument("--metadata", help="Optional JSON list of {id, title, description, area, unit, ...}")
    parser.add_argument("--lang", choices=["en", "it"], default="en", help="UI language")
    parser.add_argument(
        "--task-translations",
        help="Optional JSON dict {english_task: target_language_task} to display task names in the UI language.",
    )
    parser.add_argument(
        "--area-notes",
        help="Optional JSON dict {area_id: 'commentary text'} rendered above each area's grid. "
             "Notes should pass audit-notes.py before being shipped.",
    )
    parser.add_argument(
        "--area-descriptions",
        help="Optional JSON dict {area_id: 'high-level scope description'} shown at the top of each area section. "
             "Structure-grounded one-liners.",
    )
    parser.add_argument(
        "--org-description",
        default="",
        help="Free-text org description rendered at the top of the page. Plain text or use \\n for line breaks.",
    )
    parser.add_argument(
        "--org-description-file",
        help="Optional path to a file containing the org description (overrides --org-description).",
    )
    parser.add_argument(
        "--decisions",
        help="Optional JSON list of {question, answer, source} rendered in the bottom 'How to read this map' section. The agent fills these as the final step of the playbook; autoresearch.py scores them.",
    )
    args = parser.parse_args()

    raw = json.loads(Path(args.matches).read_text())
    # Two accepted shapes:
    # 1. Bare list of activity matches (the original match.py output).
    # 2. Wrapper object {matches, decisions, _scope, ...} for the
    #    mcp-tool render flow where the agent passes the whole play
    #    context via json_content.
    embedded_decisions: list[dict] | None = None
    embedded_dated = ""
    embedded_org = ""
    if isinstance(raw, dict) and "matches" in raw:
        matches = raw["matches"]
        if "decisions" in raw and isinstance(raw["decisions"], list):
            embedded_decisions = raw["decisions"]
        embedded_dated = (raw.get("_dated") or "").strip()
        embedded_org = (raw.get("_org") or "").strip()
    else:
        matches = raw
    metadata: dict[str, dict] = {}
    if args.metadata:
        meta_list = json.loads(Path(args.metadata).read_text())
        if isinstance(meta_list, list):
            metadata = {m["id"]: m for m in meta_list if "id" in m}
        elif isinstance(meta_list, dict):
            metadata = meta_list
    # Surface wrapper-level fields so render_html's chrome can read them.
    if embedded_dated:
        metadata["_dated"] = embedded_dated
    if embedded_org:
        metadata["_org"] = embedded_org

    translations: dict[str, str] = {}
    if args.task_translations:
        translations = json.loads(Path(args.task_translations).read_text())
        if not isinstance(translations, dict):
            print("--task-translations must be a JSON dict {english_task: translated_task}", file=sys.stderr)
            return 1

    area_notes: dict[str, str] = {}
    if args.area_notes:
        area_notes = json.loads(Path(args.area_notes).read_text())
        if not isinstance(area_notes, dict):
            print("--area-notes must be a JSON dict {area_id: 'note text'}", file=sys.stderr)
            return 1

    area_descriptions: dict[str, str] = {}
    if args.area_descriptions:
        area_descriptions = json.loads(Path(args.area_descriptions).read_text())
        if not isinstance(area_descriptions, dict):
            print("--area-descriptions must be a JSON dict {area_id: 'description'}", file=sys.stderr)
            return 1

    org_description = args.org_description
    if args.org_description_file:
        org_description = Path(args.org_description_file).read_text().strip()

    # Decisions: --decisions flag wins over wrapper-embedded decisions
    # (so a CLI user can override a wrapper). Otherwise use wrapper if
    # present.
    decisions: list[dict] = embedded_decisions or []
    if args.decisions:
        decisions = json.loads(Path(args.decisions).read_text())
        if not isinstance(decisions, list):
            print("--decisions must be a JSON list of {question, answer, source}", file=sys.stderr)
            return 1

    html = render_html(
        matches, args.title, metadata, lang=args.lang,
        task_translations=translations, area_notes=area_notes,
        area_descriptions=area_descriptions, org_description=org_description,
        decisions=decisions,
    )
    Path(args.out).write_text(html, encoding="utf-8")
    print(
        f"Wrote {Path(args.out).resolve()} "
        f"({len(matches)} activities, {len(html):,} bytes, lang={args.lang}, "
        f"translations={len(translations)}, area_notes={len(area_notes)}, "
        f"area_descriptions={len(area_descriptions)}, org_description={'yes' if org_description else 'no'})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
