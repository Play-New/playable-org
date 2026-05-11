#!/usr/bin/env python3
"""
reshuffle / viewer.py — Render a reshuffle slice as interactive HTML.

The HTML is written for a reader with zero prior knowledge of the framework
or of the organization. Every term is defined inline; every number declares its scale;
every section opens with a plain sentence saying what it is and why.

Usage:
    python3 viewer.py --map <slice.json> --html <out.html>
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

# Import the shared Play New design system
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from design import (  # noqa: E402
    app_pure_about_modal_html,
    app_pure_baseline_js,
    app_pure_css,
    app_pure_dateline_html,
    app_pure_head_meta,
    app_pure_inspect_aside_html,
    app_pure_modal_html,
    app_pure_top_right_html,
)

# Plain-language labels (no metaphors, no framework jargon).
CONSTRAINT_LABEL = {
    "scarcity": "Rare resource or skill",
    "risk": "Cost of being wrong",
    "coordination": "Cost of keeping teams aligned",
}
CONSTRAINT_PLAIN = {
    "scarcity": "Only a few people can do this work — it takes a rare skill, a regulated qualification, or a relationship that doesn't scale.",
    "risk": "Being wrong here is expensive (penalty, reputation damage, financial loss). It needs layered review and someone who signs.",
    "coordination": "The work itself isn't hard. The expensive part is moving information and decisions between teams that have to stay aligned.",
}
KM_LABEL = {
    "encoding": "Writing things down",
    "organizing": "Organizing and finding information",
    "deploying": "Using what's known at decision time",
    "none": "—",
}
AI_CLASS_LABEL = {
    "tool": "Accelerator (changes speed, not structure)",
    "engine": "Shared-knowledge infrastructure (changes structure)",
    "not-applicable": "AI not relevant for this activity",
}
AI_CLASS_SHORT = {
    "tool": "accelerator",
    "engine": "infrastructure",
    "not-applicable": "not relevant",
}
AI_CLASS_PLAIN = {
    "tool": "AI makes this work faster, but the way it gets handed across teams stays the same. Useful, not strategic.",
    "engine": "AI changes a structural cost of the process: shared knowledge replaces document-passing between teams, so people can work in parallel instead of in sequence. This is the move that reconfigures how the organization holds the work together.",
    "not-applicable": "Either there isn't enough observed evidence for this activity, or the dominant constraint (a regulation, a hard cost-of-error) makes AI not the relevant lever here.",
}
MODE_LABEL = {
    "see-saw": "Old rule: more autonomy means less alignment",
    "flywheel": "New rule: more autonomy and more alignment together",
}
MODE_PLAIN = {
    "see-saw": "Today the process follows the classical trade-off: giving teams more autonomy makes them faster but harder to keep aligned. A gain on one side costs something on the other.",
    "flywheel": "The process can follow a new rule: shared knowledge available in real time lets teams stay aligned without losing autonomy. More of one means more of the other.",
}

EXTRA_CSS = """
/* reshuffle viewer — App-pure canvas-first matrix. The shared shell
   in skills/design.py provides palette, typography, mobile baseline,
   chrome (dateline / ? / Analysis CTA), modal, favicon. This file
   adds the matrix layout (constraint × AI class), activity chips,
   rebundle option cards, inspect card body styling. */

:root {
  /* Constraint colours from the Carta sbiadita palette. */
  --scarcity:     var(--k-stakeholder); /* lilac · rare resource / skill */
  --risk:         var(--k-commitment);  /* terracotta · cost of being wrong */
  --coordination: var(--k-activity);    /* sage · coordination cost */
}

/* Body wrapper — fills the viewport with the matrix and rebundle
   row underneath. No scroll-paper editorial column; this view is
   diagrammatic. */
.reshuffle-body {
  max-width: 1320px;
  margin: 0 auto;
  padding: max(72px, calc(env(safe-area-inset-top) + 60px))
           max(28px, env(safe-area-inset-right))
           max(80px, calc(env(safe-area-inset-bottom) + 60px))
           max(28px, env(safe-area-inset-left));
}

/* The reading question, sitting just under the chrome. One italic
   sentence — frames what the matrix below answers. */
.reading {
  font-size: 14.5px;
  font-style: italic;
  color: var(--ink-95);
  letter-spacing: -0.005em;
  line-height: 1.45;
  margin: 0 0 28px;
  max-width: 760px;
  text-wrap: pretty;
}
.reading em {
  font-style: normal;
  color: var(--ink);
  font-weight: 540;
}

/* ── MATRIX — 3 columns (constraint) × 3 rows (AI class) ────────── */
.matrix {
  display: grid;
  /* First column = row labels (the AI class). The other three are the
     constraint columns. */
  grid-template-columns: 200px repeat(3, 1fr);
  grid-template-rows: auto auto auto auto;
  gap: 1px;
  background: var(--hairline);
  border: 1px solid var(--hairline);
  border-radius: 4px;
  overflow: hidden;
  margin: 0 0 36px;
}
.matrix > * {
  background: var(--paper);
  padding: 14px 16px;
  min-height: 80px;
}
.matrix .axis-corner { background: var(--paper); }
.matrix .col-head {
  font-size: 13px;
  font-weight: 540;
  letter-spacing: -0.005em;
  color: var(--ink);
  line-height: 1.3;
  display: flex; flex-direction: column; gap: 4px;
  min-height: 60px;
}
.matrix .col-head .col-explain {
  font-size: 11px;
  font-weight: 380;
  font-style: italic;
  color: var(--ink-60);
  line-height: 1.45;
  text-wrap: pretty;
}
.matrix .row-label {
  display: flex; flex-direction: column; gap: 4px;
  font-size: 13px;
  font-weight: 540;
  color: var(--ink);
  letter-spacing: -0.005em;
  line-height: 1.3;
  background: var(--paper-2);
}
.matrix .row-label .row-explain {
  font-size: 11px;
  font-weight: 380;
  font-style: italic;
  color: var(--ink-60);
  line-height: 1.45;
  text-wrap: pretty;
}
.matrix .cell {
  display: flex; flex-direction: column; gap: 4px;
  padding: 10px 12px;
  align-items: stretch;
  background: var(--paper);
}
/* The high-leverage cell — infrastructure × coordination. The picture
   teaches the frame: this is "where AI changes structure". */
.matrix .cell.leverage {
  background: var(--paper-2);
  position: relative;
}
.matrix .cell.leverage::before {
  content: "where AI changes structure";
  position: absolute;
  top: -10px; left: 12px;
  background: var(--paper);
  padding: 0 8px;
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--k-commitment);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  line-height: 1.6;
  white-space: nowrap;
  z-index: 1;
}
.matrix .cell.empty {
  font-size: 11px;
  font-style: italic;
  color: var(--ink-25);
  align-items: center; justify-content: center;
  min-height: 80px;
}

/* Activity chips inside cells. Engine candidates carry a coral
   left-rule. */
.activity-chip {
  display: flex; flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border: 1px solid var(--hairline);
  border-radius: 3px;
  background: var(--paper);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  font-size: 12px;
}
.activity-chip:hover {
  border-color: var(--ink);
  background: var(--paper-2);
}
.activity-chip.engine {
  border-color: var(--k-commitment);
  border-left-width: 3px;
  padding-left: 9px;
}
.activity-chip .chip-label {
  font-weight: 540;
  color: var(--ink);
  letter-spacing: -0.005em;
  line-height: 1.3;
}
.activity-chip .chip-meta {
  font-size: 10.5px;
  color: var(--ink-60);
  font-style: italic;
}
.activity-chip.engine .chip-meta { color: var(--k-commitment); font-style: normal; }

/* Rebundle options — full-bleed named cards inside the Analysis
   modal, stacked vertically. The modal already constrains width
   (~ 720px), so a single column reads well. */
.rebundle-section {
  margin: 24px 0 0;
}
.rebundle-section-head {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-60);
  margin: 0 0 6px;
}
.rebundle-section-hint {
  font-size: 13px;
  color: var(--ink-60);
  font-style: italic;
  margin: 0 0 14px;
  line-height: 1.55;
}
.rebundle-card {
  padding: 18px 22px 20px;
  margin-bottom: 12px;
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 4px;
}
.rebundle-card.alignment { border-left: 3px solid var(--k-activity); padding-left: 19px; }
.rebundle-card .rebundle-eyebrow {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin-bottom: 6px;
}
.rebundle-card .rebundle-name {
  font-size: 15px;
  font-weight: 540;
  letter-spacing: -0.012em;
  margin: 0 0 8px;
  text-wrap: pretty;
}
.rebundle-card .rebundle-desc {
  font-size: 13px;
  color: var(--ink-95);
  line-height: 1.55;
  margin: 0 0 10px;
  text-wrap: pretty;
}
.rebundle-card .rebundle-section-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin: 14px 0 4px;
}
.rebundle-card .rebundle-narration {
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--ink-95);
  text-wrap: pretty;
}
.rebundle-card .rebundle-narration strong { font-weight: 540; }
.rebundle-card .rebundle-list {
  font-size: 12.5px;
  padding-left: 22px;
  margin: 6px 0 0;
  line-height: 1.55;
  color: var(--ink-95);
}
.rebundle-card .rebundle-list li { margin: 1px 0; }

/* Section heads above matrix and rebundle row. */
.section-head {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-60);
  margin: 0 0 12px;
}

/* Inspect card body styling — same fields as before, restyled to
   match the App-pure inspect convention. */
.inspect .inspect-row {
  display: flex; align-items: baseline;
  gap: 12px;
  font-size: 11.5px;
  margin: 4px 0;
  letter-spacing: -0.005em;
}
.inspect .inspect-row .key {
  color: var(--ink-60);
  font-style: italic;
  white-space: nowrap;
}
.inspect .inspect-row .val {
  color: var(--ink);
  font-weight: 540;
}
.inspect .narration {
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--ink-95);
  margin: 12px 0 8px;
  text-wrap: pretty;
}
.inspect .narration strong { font-weight: 540; }
.inspect .citation-box {
  font-size: 11px;
  color: var(--ink-60);
  padding: 6px 10px;
  border-left: 1px solid var(--hairline);
  margin-top: 6px;
  line-height: 1.5;
  font-family: ui-monospace, SF Mono, Menlo, monospace;
  font-style: italic;
}

@media (max-width: 900px) {
  .matrix { grid-template-columns: 130px repeat(3, 1fr); gap: 1px; }
  .matrix > * { padding: 10px 10px; }
  .matrix .col-head, .matrix .row-label { font-size: 11.5px; }
  .matrix .col-head .col-explain, .matrix .row-label .row-explain { font-size: 10px; }
  .matrix .cell.leverage::before { font-size: 9px; padding: 0 6px; }
}
@media (max-width: 760px) {
  .reshuffle-body {
    padding: max(56px, calc(env(safe-area-inset-top) + 50px)) 14px max(72px, calc(env(safe-area-inset-bottom) + 56px));
  }
  /* Matrix collapses on phones: stack each row as its own block, with
     the row label on top and the three cells below as a horizontal
     mini-row. */
  .matrix {
    grid-template-columns: 1fr;
    grid-auto-rows: auto;
  }
  .matrix .axis-corner, .matrix .col-head { display: none; }
  .matrix .row-label {
    background: var(--paper-2);
    padding: 14px 14px 10px;
  }
  .matrix .cell {
    padding: 12px 14px;
    border-top: 1px solid var(--hairline-2);
  }
  .matrix .cell.empty { display: none; }
  .matrix .cell::before {
    content: attr(data-constraint);
    display: block;
    font-size: 10px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: var(--ink-40);
    margin-bottom: 6px;
  }
  .matrix .cell.leverage::before {
    content: "where AI changes structure · " attr(data-constraint);
    position: static;
    background: transparent; border: 0;
    padding: 0;
    color: var(--k-commitment);
    text-transform: uppercase;
  }
}

.dist-bar {
  display: flex;
  height: 14px;
  border-radius: 2px;
  overflow: hidden;
  margin: 14px 0;
  background: var(--paper-2);
}
.dist-bar > div { height: 100%; }
.dist-bar .seg.scarcity { background: var(--scarcity); }
.dist-bar .seg.risk { background: var(--risk); }
.dist-bar .seg.coordination { background: var(--coordination); }
.dist-legend { display: grid; gap: 12px; font-size: 12.5px; color: var(--ink-95); margin-top: 14px; }
.dist-legend .item { display: flex; gap: 12px; align-items: flex-start; }
.dist-legend .swatch {
  width: 12px; height: 12px; border-radius: 2px;
  margin-top: 5px; flex-shrink: 0;
}
.dist-legend strong { font-weight: 540; color: var(--ink); }
.dist-legend .count { color: var(--ink-60); }

.bundle-state { margin: 24px 0 0; }
.bundle-state .key {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin-bottom: 8px;
}
.bundle-state .text {
  font-size: 13px;
  color: var(--ink-95);
  line-height: 1.6;
  margin: 0 0 12px;
  text-wrap: pretty;
}

.group { margin: 24px 0; }
.group-header {
  margin: 0 0 14px;
  display: flex; align-items: center; gap: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--hairline-2);
}
.group-header .swatch { width: 12px; height: 12px; border-radius: 2px; }
.group-header h3 {
  margin: 0;
  font-size: 14.5px;
  font-weight: 540;
  letter-spacing: -0.012em;
}
.group-header .count {
  font-size: 11px;
  color: var(--ink-40);
  margin-left: auto;
  font-style: italic;
}
.group-explain {
  margin: 0 0 14px;
  font-size: 12.5px;
  color: var(--ink-60);
  line-height: 1.6;
}

/* Activity cards — paper, hairline border. Engine accent uses the
   commitment terracotta. */
.activity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.activity-card {
  padding: 14px 16px;
  cursor: pointer;
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 4px;
  transition: border-color 0.15s;
}
.activity-card:hover { border-color: var(--ink); }
.activity-card.engine { border-color: var(--k-commitment); }
.activity-card .label {
  font-weight: 540;
  font-size: 13.5px;
  line-height: 1.35;
  margin-bottom: 6px;
  letter-spacing: -0.012em;
}
.activity-card .ai-label {
  font-size: 11px;
  color: var(--ink-60);
  font-style: italic;
}
.activity-card.engine .ai-label {
  color: var(--k-commitment);
  font-style: normal;
  font-weight: 540;
}

/* Engine + rebundle candidate cards — wider, prose-rich. */
.candidate-card {
  padding: 16px 20px;
  margin-bottom: 10px;
  cursor: pointer;
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 4px;
  transition: border-color 0.15s;
}
.candidate-card:hover { border-color: var(--ink); }
.candidate-card.engine-card { border-color: var(--k-commitment); }
.candidate-card .name {
  font-weight: 540;
  font-size: 14.5px;
  margin-bottom: 6px;
  letter-spacing: -0.012em;
  text-wrap: pretty;
}
.candidate-card .meta {
  font-size: 12.5px;
  color: var(--ink-60);
  line-height: 1.55;
}

/* Popover — opened by clicking an activity / candidate card. Same
   pattern as ai-exposure. */
.popover {
  position: absolute;
  display: none;
  max-width: 420px;
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
  font: inherit; font-size: 16px;
  color: var(--ink-40);
  cursor: pointer;
  padding: 2px 6px; line-height: 1;
}
.popover .close:hover { color: var(--ink); }
.popover .eyebrow {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin-bottom: 6px;
}
.popover .eyebrow.engine { color: var(--k-commitment); }
.popover h3 {
  font-size: 14.5px;
  font-weight: 540;
  letter-spacing: -0.012em;
  margin: 0 0 8px;
  padding-right: 20px;
  text-wrap: pretty;
}
.popover .desc {
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--ink-95);
  margin: 0 0 10px;
}
.popover .section-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ink-60);
  margin: 12px 0 4px;
}
.popover .narration {
  font-size: 12px;
  line-height: 1.55;
  color: var(--ink-95);
}
.popover .narration strong { font-weight: 540; }
.popover .citation {
  font-size: 11px;
  color: var(--ink-60);
  padding: 4px 0 4px 10px;
  border-left: 1px solid var(--hairline);
  margin-top: 6px;
  line-height: 1.5;
  font-family: ui-monospace, SF Mono, Menlo, monospace;
  font-style: italic;
}
.popover .data-block {
  background: var(--paper-2);
  padding: 10px 12px;
  border-radius: 3px;
  margin-top: 8px;
  font-size: 11.5px;
}
.popover .data-block .help {
  font-size: 10.5px;
  color: var(--ink-60);
  line-height: 1.55;
  margin-bottom: 8px;
}
.popover .data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
.popover .data-table th, .popover .data-table td {
  text-align: left;
  padding: 4px 6px;
  border-bottom: 1px solid var(--hairline-2);
}
.popover .data-table th {
  color: var(--ink-60);
  font-weight: 500;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.10em;
}
.popover .data-table .num {
  font-family: ui-monospace, SF Mono, Menlo, monospace;
}
.popover .data-table .small-sample {
  color: var(--k-commitment);
  font-weight: 540;
}

@media (max-width: 760px) {
  .reshuffle-body { padding: max(56px, calc(env(safe-area-inset-top) + 50px)) 16px max(72px, calc(env(safe-area-inset-bottom) + 56px)); }
  .activity-grid { grid-template-columns: 1fr; }
}
"""


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
{head_meta}
<style>{css}</style>
</head>
<body>

{dateline}

{top_right}

<main class="reshuffle-body">

  <div class="matrix">
    <div class="axis-corner"></div>
    <div class="col-head">Rare resource or skill<span class="col-explain">Only specific people or vendors can do it</span></div>
    <div class="col-head">Cost of being wrong<span class="col-explain">Failure is expensive, needs layered review</span></div>
    <div class="col-head">Cost of keeping teams aligned<span class="col-explain">The work isn't hard; moving information between teams is</span></div>

    <div class="row-label">AI as infrastructure<span class="row-explain">Changes how knowledge is shared between teams</span></div>
    {row_infrastructure}

    <div class="row-label">AI as accelerator<span class="row-explain">Makes work inside one team faster</span></div>
    {row_accelerator}

    <div class="row-label">AI not relevant<span class="row-explain">Observed AI usage doesn't move it either way</span></div>
    {row_not_relevant}
  </div>

</main>

{inspect_aside}

{about_modal_html}

{decisions_modal_html}

<div class="popover" id="popover">
  <button class="close" id="popover-close" aria-label="Close">×</button>
  <div id="popover-body"></div>
</div>

<script>
{baseline_js}
</script>

<script>
const NODES = {nodes_json};
const CONSTRAINT_LABEL = {constraint_label_json};
const CONSTRAINT_PLAIN = {constraint_plain_json};
const KM_LABEL = {km_label_json};
const AI_CLASS_LABEL = {ai_class_label_json};
const AI_CLASS_PLAIN = {ai_class_plain_json};

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }})[c]);
}}

function renderActivityPopover(node) {{
  const pc = node.primary_constraint;
  const km = node.km_cost_dominant;
  const ac = node.ai_classification;
  const ebCls = ac === 'engine' ? 'eyebrow engine' : 'eyebrow';
  const ebText = ac === 'engine' ? 'where AI changes structure' : 'activity in this process';
  let html = `<div class="${{ebCls}}">${{ebText}}</div>`;
  html += `<h3>${{escapeHtml(node.label)}}</h3>`;

  if (node._body || node._description) {{
    html += `<div class="desc">${{escapeHtml(node._body || node._description)}}</div>`;
  }}

  if (pc) {{
    html += `<div class="section-label">What holds it in place</div>`;
    html += `<div class="narration"><strong>${{CONSTRAINT_LABEL[pc]}}.</strong> ${{escapeHtml(CONSTRAINT_PLAIN[pc])}}</div>`;
    if (node.constraint_evidence && node.constraint_evidence.length) {{
      for (const e of node.constraint_evidence) {{
        html += `<div class="citation">${{escapeHtml(e.claim || '')}} (${{escapeHtml(e.source || '')}})</div>`;
      }}
    }}
  }}

  if (km && km !== 'none') {{
    html += `<div class="section-label">Where the main cost sits</div>`;
    html += `<div class="narration">${{escapeHtml(KM_LABEL[km])}}.</div>`;
  }}

  if (ac) {{
    html += `<div class="section-label">What AI does here</div>`;
    html += `<div class="narration"><strong>${{escapeHtml(AI_CLASS_LABEL[ac])}}.</strong> ${{escapeHtml(AI_CLASS_PLAIN[ac])}}</div>`;
    if (node.ai_evidence && node.ai_evidence.length) {{
      for (const e of node.ai_evidence) {{
        html += `<div class="citation">${{escapeHtml(e.claim || '')}}</div>`;
      }}
    }}
  }}

  if (node._aei && node._aei.top_matches && node._aei.top_matches.length) {{
    html += `<div class="section-label">Where the analysis comes from</div>`;
    html += `<div class="data-block">`;
    html += `<div class="help">Closest tasks in the Anthropic Economic Index sample. Similarity is semantic; autonomy is on a 1-to-5 scale (1 = AI assists, 5 = AI works alone); sample = number of Claude.ai conversations the observation is based on (under 100 the read is fragile).</div>`;
    html += `<table class="data-table"><thead><tr><th>Closest task</th><th>Similarity</th><th>Autonomy</th><th>Sample</th></tr></thead><tbody>`;
    for (const m of node._aei.top_matches) {{
      const sim = m.similarity != null ? Math.round(Number(m.similarity) * 100) + '%' : '—';
      let aut = '<span style="color: var(--fg-muted)">—</span>';
      if (m.ai_autonomy_mean != null) {{
        aut = `<span class="num">${{Number(m.ai_autonomy_mean).toFixed(1)}}/5</span>`;
      }}
      let cnt = '<span style="color: var(--fg-muted)">0</span>';
      if (m.count != null && m.count > 0) {{
        const c = Math.round(m.count);
        cnt = c < 100 ? `<span class="num small-sample">${{c}} (small)</span>` : `<span class="num">${{c}}</span>`;
      }}
      html += `<tr><td>${{escapeHtml((m.task||'').slice(0,90))}}</td><td class="num">${{sim}}</td><td>${{aut}}</td><td>${{cnt}}</td></tr>`;
    }}
    html += `</tbody></table></div>`;
  }}

  return html;
}}

// Popover positioning + click handlers — same shape as the other viewers.
const popoverEl   = document.getElementById('popover');
const popoverBody = document.getElementById('popover-body');

function showPopover(html, anchorRect) {{
  // Open the popover BELOW the clicked card, centered horizontally
  // on it. If there's not enough room below, flip above. Always
  // clamped inside the viewport.
  popoverBody.innerHTML = html;
  const margin = 12;
  popoverEl.style.left = '0px';
  popoverEl.style.top  = '0px';
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

function showFor(target, html) {{
  const r = target.getBoundingClientRect();
  showPopover(html, {{
    left:   r.left   + window.scrollX,
    right:  r.right  + window.scrollX,
    top:    r.top    + window.scrollY,
    bottom: r.bottom + window.scrollY,
  }});
}}

document.addEventListener('click', (e) => {{
  let n = e.target;
  while (n && n.nodeType === 1) {{
    if (n.classList && n.classList.contains('activity-card')) {{
      const node = NODES[n.dataset.id];
      if (node) showFor(n, renderActivityPopover(node));
      return;
    }}
    if (n.id === 'popover') return;
    n = n.parentNode;
  }}
  hidePopover();
}}, true);

document.getElementById('popover-close').addEventListener('click', hidePopover);
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') hidePopover(); }});
</script>
</body>
</html>"""


def render_html(d: dict) -> str:
    anchor = d.get("_anchor", {})
    title = anchor.get("title") or "Process"
    anchor_id = anchor.get("id", "")
    description_text = anchor.get("description", "") or anchor.get("terms", "")[:300]

    comps = [c for c in d.get("components", []) if c.get("_kind") != "stakeholder"]

    # ── Matrix: constraint × AI class ──────────────────────────────
    # Rows = AI class (infrastructure / accelerator / not-relevant);
    # columns = primary constraint (scarcity / risk / coordination).
    # The (infrastructure × coordination) cell is the high-leverage
    # cell — labelled "where AI changes structure".
    engines = d.get("engine_candidates") or []
    engine_ids = {e.get("component_id") for e in engines}
    engine_dissolves = {e.get("component_id"): e.get("dissolves_constraint", "") for e in engines}

    def _ai_class(c: dict) -> str:
        if c["id"] in engine_ids:
            return "infrastructure"
        ac = (c.get("ai_classification") or "").strip()
        if ac in ("infrastructure", "accelerator", "not-relevant"):
            return ac
        return "accelerator"  # default when nothing observed

    cells: dict[tuple[str, str], list[dict]] = {}
    for c in comps:
        constraint = c.get("primary_constraint") or "coordination"
        if constraint not in ("scarcity", "risk", "coordination"):
            constraint = "coordination"
        ai_class = _ai_class(c)
        cells.setdefault((ai_class, constraint), []).append(c)

    def _chip_html(c: dict) -> str:
        is_engine = c["id"] in engine_ids
        engine_class = " engine" if is_engine else ""
        unit = (c.get("_unit") or "").strip()
        meta = f"in {escape(unit)}" if unit else ""
        return (
            f'<div class="activity-chip activity-card{engine_class}" data-id="{escape(c["id"])}">'
            f'<div class="chip-label">{escape(c.get("label", c["id"]))}</div>'
            f'{f"<div class=\"chip-meta\">{meta}</div>" if meta else ""}'
            f'</div>'
        )

    def _cell_html(ai_class: str, constraint: str) -> str:
        items = cells.get((ai_class, constraint)) or []
        leverage_class = " leverage" if (ai_class == "infrastructure" and constraint == "coordination") else ""
        if not items:
            return (
                f'<div class="cell empty{leverage_class}" data-constraint="{CONSTRAINT_LABEL[constraint]}">'
                f'—'
                f'</div>'
            )
        chips = "\n".join(_chip_html(c) for c in items)
        return (
            f'<div class="cell{leverage_class}" data-constraint="{CONSTRAINT_LABEL[constraint]}">'
            f'{chips}'
            f'</div>'
        )

    row_infrastructure = "".join(_cell_html("infrastructure", c) for c in ("scarcity", "risk", "coordination"))
    row_accelerator    = "".join(_cell_html("accelerator", c)    for c in ("scarcity", "risk", "coordination"))
    row_not_relevant   = "".join(_cell_html("not-relevant", c)   for c in ("scarcity", "risk", "coordination"))

    # ── Direction options — fully expanded named cards that go INSIDE
    # the Analysis modal (via body_html), above the decisions list.
    # Each card carries everything inline: description, the activities
    # it brings together, what would make it possible, what would still
    # hold it back, how the new process would run, what would change
    # for the people in it, and how risky the move would be.
    rebundles = d.get("rebundle_candidates") or []
    by_id = {c["id"]: c for c in comps}

    def _rebundle_card_html(rb: dict) -> str:
        parts: list[str] = []
        parts.append('<div class="rebundle-eyebrow">Direction option</div>')
        parts.append(f'<div class="rebundle-name">{escape(rb.get("name", "?"))}</div>')
        if rb.get("description"):
            parts.append(f'<div class="rebundle-desc">{escape(rb["description"])}</div>')

        acts = rb.get("activities") or []
        if acts:
            parts.append('<div class="rebundle-section-label">Activities this would bring together</div>')
            items = []
            for aid in acts:
                n = by_id.get(aid)
                label = (n or {}).get("label") or aid
                items.append(f'<li>{escape(label)}</li>')
            parts.append(f'<ul class="rebundle-list">{"".join(items)}</ul>')

        eng_id = rb.get("enabled_by_engine")
        if eng_id:
            eng = next((e for e in engines if e.get("component_id") == eng_id), None)
            eng_label = (by_id.get(eng_id, {}) or {}).get("label") or eng_id
            removed = (eng or {}).get("dissolves_constraint")
            parts.append('<div class="rebundle-section-label">What would make it possible</div>')
            if removed:
                rl = CONSTRAINT_LABEL.get(removed, removed).lower()
                parts.append(
                    f'<div class="rebundle-narration">The activity <strong>{escape(eng_label)}</strong>, '
                    f'used as a memory each team can read in real time instead of a chain of documents '
                    f'passed between teams, would remove the {escape(rl)} that holds the process together today.</div>'
                )
            else:
                parts.append(
                    f'<div class="rebundle-narration">The activity <strong>{escape(eng_label)}</strong>, '
                    f'used as a memory each team can read in real time.</div>'
                )

        rc = rb.get("remaining_binding_constraint")
        if rc:
            rc_label = CONSTRAINT_LABEL.get(rc, rc)
            rc_plain = CONSTRAINT_PLAIN.get(rc, "")
            parts.append('<div class="rebundle-section-label">What would still hold it back</div>')
            parts.append(
                f'<div class="rebundle-narration"><strong>{escape(rc_label)}.</strong> {escape(rc_plain)}</div>'
            )

        mode = rb.get("autonomy_coordination_mode")
        mode_class = " alignment" if mode == "flywheel" else ""
        if mode in MODE_LABEL:
            parts.append('<div class="rebundle-section-label">How the new process would run</div>')
            parts.append(
                f'<div class="rebundle-narration"><strong>{escape(MODE_LABEL[mode])}.</strong> '
                f'{escape(MODE_PLAIN.get(mode, ""))}</div>'
            )

        if rb.get("what_changes"):
            parts.append('<div class="rebundle-section-label">What would change for the people in the process</div>')
            parts.append(f'<div class="rebundle-narration">{escape(rb["what_changes"])}</div>')

        if rb.get("risk_of_rebundle"):
            parts.append('<div class="rebundle-section-label">How risky the move would be</div>')
            parts.append(f'<div class="rebundle-narration">{escape(rb["risk_of_rebundle"])}</div>')

        return f'<div class="rebundle-card{mode_class}">{"".join(parts)}</div>'

    rb_cards = [_rebundle_card_html(rb) for rb in rebundles]

    if rb_cards:
        n_rb = len(rb_cards)
        word = "alternative" if n_rb == 1 else "alternatives"
        n_dec_preview = len(d.get("decisions") or [])
        decisions_intro = (
            f'<p class="rebundle-section-head" style="margin-top: 32px;">'
            f'{n_dec_preview} decision{"s" if n_dec_preview != 1 else ""} that follow'
            f'</p>'
            if n_dec_preview
            else ""
        )
        rebundle_section_html = (
            '<div class="rebundle-section">'
            f'<p class="rebundle-section-head">{n_rb} {word} the matrix opens up</p>'
            '<p class="rebundle-section-hint">If the studio first turned one of the activities in the top row into a memory each team can read in real time — rather than a chain of documents passed between teams — the work could be put back together in these ways.</p>'
            + "\n".join(rb_cards)
            + decisions_intro
            + '</div>'
        )
    else:
        rebundle_section_html = ""

    # Decisions section — same shape as the other viewers.
    decisions = d.get("decisions") or []
    decisions_section = ""
    if decisions:
        items = []
        for dec in decisions:
            q = escape(dec.get("question", ""))
            ans_paragraphs = "".join(
                f'<p class="answer">{escape(p)}</p>'
                for p in (dec.get("answer", "") or "").split("\n\n") if p.strip()
            )
            src = escape(dec.get("source", ""))
            src_html = f'<div class="source">{src}</div>' if src else ""
            items.append(f'<div class="decision"><div class="question">{q}</div>{ans_paragraphs}{src_html}</div>')
        decisions_section = (
            '<div class="section" id="decisions">'
            '<h2>How to read this map</h2>'
            '<p class="lead">The leader-facing reading: which place to deploy AI as infrastructure (not just accelerator), which constraint to dissolve, which direction option to take and why.</p>'
            + "".join(items)
            + '</div>'
        )

    nodes_json = json.dumps({c["id"]: c for c in comps}, ensure_ascii=False)

    # --- App-pure chrome assembly ---
    n_activities = len(d.get("activities", []) or [])
    org_name = (d.get("_org") or "").strip() or "Reshuffle"
    dated = d.get("_dated", "—")

    # About modal — the intro that used to sit at the top of the
    # page. Plain-language definitions of every term, no jargon
    # (per skills/STYLE.md). Each label the leader will see on a
    # card or a pill is unpacked here.
    about_body = """
  <p>This page is an analysis of one process the organisation runs today, and where AI might actually change it. It is a read of the structure as it has been written down — not a proposal. The recommendations sit in the "Analysis" modal on the right.</p>

  <p>The starting question is single: <strong>for this process, what is the most expensive part — doing the work, or keeping the teams that do it aligned?</strong> The answer matters because AI can do two very different things, and they should not be confused.</p>

  <h2>Two things AI can do</h2>
  <p><strong>Accelerator</strong> — AI makes a single piece of work faster inside a team: drafts a document, summarises a call, looks up a fact. The team moves faster. The way teams hand off work to each other — the file passes, the alignment meetings, the context rebuilds — stays exactly the same. Useful, not structural.</p>
  <p><strong>Shared-knowledge infrastructure</strong> — AI turns the organisation's knowledge into something genuinely shared: not documents chasing each other across teams, but a common memory each team queries in real time. The classical rule "more autonomy on one team means less alignment with the rest" stops holding. This dissolves a structural cost; it changes how the organisation holds the work together.</p>
  <p><em>The most common mistake</em>: shipping AI as an accelerator in some teams while believing it has been deployed as infrastructure. Some teams move faster, others don't, and the speed asymmetry makes the alignment problem worse.</p>

  <h2>What keeps each activity tied to the current process</h2>
  <p>Not every activity is alike. For each one we ask what holds it in place, picking from three constraints:</p>
  <p><strong>Rare resource or skill</strong> — only a few people (or a few vendors) can do it, because it takes a regulated qualification, a rare skill, or an exclusive relationship.</p>
  <p><strong>Cost of being wrong</strong> — getting it wrong is expensive (legal, reputational, financial). It needs layered review and someone who signs.</p>
  <p><strong>Cost of keeping teams aligned</strong> — the work itself isn't hard. The expensive part is moving information and decisions between the team upstream and the team downstream. This is the constraint AI-as-infrastructure can dissolve.</p>

  <h2>What the colour and the mark on each card mean</h2>
  <p>Each activity card carries one mark: <strong>infrastructure</strong> means AI changes the constraint that holds the activity in place; <strong>accelerator</strong> means AI makes the work inside the activity faster but does not change what holds it; <strong>not relevant</strong> means observed AI usage today does not move it either way. The card border is darker for activities where the change would be structural — these are the places to start.</p>

  <p>Click any activity or direction option for its rationale and the cited evidence behind it.</p>
"""
    about_modal_html_str = app_pure_about_modal_html(
        kicker=f"№ {n_activities:02d} · reshuffle",
        headline=title,
        lede=description_text,
        body_html=about_body,
    )

    # Decisions go into the shared Analysis modal.
    decisions = d.get("decisions") or []
    decisions_modal_html_str = ""
    has_decisions = bool(decisions)
    if has_decisions:
        items = []
        for dec in decisions:
            q = escape(dec.get("question", ""))
            ans = "".join(
                f"<p>{escape(p)}</p>"
                for p in (dec.get("answer", "") or "").split("\n\n")
                if p.strip()
            )
            src = escape(dec.get("source", ""))
            src_html = f'<p class="source">{src}</p>' if src else ""
            items.append(f"<li><h3>{q}</h3>{ans}{src_html}</li>")
        if rebundles:
            modal_headline = "What AI could change about this process, and what to decide."
        else:
            n_dec = len(decisions)
            modal_headline = f"{n_dec} decision{'s' if n_dec != 1 else ''} to take from this process."
        decisions_modal_html_str = app_pure_modal_html(
            headline=modal_headline,
            org_name=org_name,
            dated=dated,
            decisions_html="".join(items),
            kicker="Reading the process",
            lede="",
            body_html=rebundle_section_html,
        )

    return HTML_TEMPLATE.format(
        head_meta=app_pure_head_meta(f"{title} · reshuffle"),
        css=app_pure_css(layout="scroll") + EXTRA_CSS,
        baseline_js=app_pure_baseline_js(),
        dateline=app_pure_dateline_html(
            org_name,
            what=f"reshuffle · slice anchored on <em>{escape(anchor_id)}</em>",
        ),
        top_right=app_pure_top_right_html(
            dated, show_analysis=has_decisions, show_help=True
        ),
        about_modal_html=about_modal_html_str,
        decisions_modal_html=decisions_modal_html_str,
        inspect_aside=app_pure_inspect_aside_html(),
        row_infrastructure=row_infrastructure,
        row_accelerator=row_accelerator,
        row_not_relevant=row_not_relevant,
        nodes_json=nodes_json,
        constraint_label_json=json.dumps(CONSTRAINT_LABEL, ensure_ascii=False),
        constraint_plain_json=json.dumps(CONSTRAINT_PLAIN, ensure_ascii=False),
        km_label_json=json.dumps(KM_LABEL, ensure_ascii=False),
        ai_class_label_json=json.dumps(AI_CLASS_LABEL, ensure_ascii=False),
        ai_class_plain_json=json.dumps(AI_CLASS_PLAIN, ensure_ascii=False),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render reshuffle slice JSON as interactive HTML.")
    parser.add_argument("--map", required=True, help="Slice JSON path")
    parser.add_argument("--html", required=True, help="Output HTML path")
    parser.add_argument(
        "--decisions",
        help="Optional JSON list of {question, answer, source} merged into the map under top-level "
             "'decisions[]'. Renders the 'How to read this map' section. Required for a shippable "
             "play — autoresearch fails without it.",
    )
    args = parser.parse_args()

    d = json.loads(Path(args.map).read_text(encoding="utf-8"))
    if args.decisions:
        decisions = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
        if not isinstance(decisions, list):
            print("--decisions must be a JSON list of {question, answer, source}", file=sys.stderr)
            return 1
        d["decisions"] = decisions

    html = render_html(d)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"Wrote {Path(args.html).resolve()} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
