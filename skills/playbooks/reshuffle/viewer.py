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
from design import base_css  # noqa: E402

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
/* reshuffle viewer — Play New design (unified with value-map, ai-exposure, world-model).
   Pure white surface, editorial typography, hairlines, single accent.
   One uniform 1240px container; editorial text in centered 820px columns
   at the start and end; data-heavy blocks span the full container. */

:root {
  /* Constraint colours from the data-viz palette. */
  --scarcity:    var(--ds-lilac);
  --risk:        var(--ds-coral);
  --coordination: var(--ds-sage);
}

body { background: #FFFFFF; color: var(--fg); }

.container { max-width: 1240px; margin: 0 auto; padding: 80px 40px 96px; }
@media (max-width: 900px) { .container { padding: 56px 24px 80px; } }

/* Editorial text columns at the start and end of the page. */
header { max-width: 820px; margin: 0 auto 48px; }
header .eyebrow { font-family: var(--font-display); font-size: 0.74rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); margin-bottom: 16px; }
header h1 { font-family: var(--font-display); font-size: clamp(1.9rem, 3.5vw, 2.6rem); font-weight: 500; letter-spacing: -0.025em; line-height: 1.1; margin: 0 0 16px; color: var(--fg); }
header .lead { font-size: 1.0rem; color: var(--fg-muted); line-height: 1.65; margin: 0; }
header .anchor-line { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.78rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.04em; margin-top: 12px; }

.intro { max-width: 820px; margin: 0 auto 56px; }
.intro h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 16px; }
.intro h3 { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; letter-spacing: -0.01em; margin: 22px 0 10px; }
.intro p { font-size: 0.95rem; line-height: 1.7; margin: 0 0 14px; color: var(--fg); }
.intro p strong { font-weight: 500; }
.intro .pull { padding: 14px 0 14px 18px; margin: 22px 0; font-size: 1.0rem; color: var(--fg); border-left: 2px solid var(--fg); line-height: 1.65; }
.intro ul { font-size: 0.95rem; line-height: 1.7; padding-left: 24px; margin: 0 0 14px; color: var(--fg); }
.intro ul li { margin-bottom: 6px; }
.intro ul li strong { font-weight: 500; }

/* Data zones — full container width */
.panel, .ledger, .candidates { margin: 0 0 64px; padding-top: 36px; border-top: 1px solid var(--fg-hairline); }
.panel-head, .ledger-head, .candidates-head { max-width: 820px; margin: 0 auto 28px; }
.panel h2, .ledger h2, .candidates h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 12px; }
.panel-hint, .ledger-hint, .candidates-hint { font-size: 0.95rem; color: var(--fg-muted); margin: 0; line-height: 1.65; }

.dist-bar { display: flex; height: 14px; border-radius: 2px; overflow: hidden; margin: 14px 0; }
.dist-bar > div { height: 100%; }
.dist-bar .seg.scarcity { background: var(--scarcity); }
.dist-bar .seg.risk { background: var(--risk); }
.dist-bar .seg.coordination { background: var(--coordination); }
.dist-legend { display: grid; gap: 12px; font-size: 0.88rem; color: var(--fg); margin-top: 14px; max-width: 820px; }
.dist-legend .item { display: flex; gap: 12px; align-items: flex-start; }
.dist-legend .swatch { width: 12px; height: 12px; border-radius: 2px; margin-top: 5px; flex-shrink: 0; }
.dist-legend strong { font-weight: 500; color: var(--fg); }
.dist-legend .count { color: var(--fg-muted); }

.bundle-state { max-width: 820px; margin: 28px auto 0; }
.bundle-state .key { font-family: var(--font-display); font-size: 0.7rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 8px; font-weight: 500; }
.bundle-state .text { font-size: 0.95rem; color: var(--fg); line-height: 1.65; margin: 0 0 14px; }

.group { margin: 32px 0; }
.group-header { max-width: 820px; margin: 0 auto 16px; display: flex; align-items: center; gap: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--fg-hairline); }
.group-header .swatch { width: 12px; height: 12px; border-radius: 2px; }
.group-header h3 { font-family: var(--font-display); margin: 0; font-size: 1.1rem; font-weight: 500; color: var(--fg); letter-spacing: -0.01em; }
.group-header .count { font-size: 0.8rem; color: var(--fg-muted); margin-left: auto; }
.group-explain { max-width: 820px; margin: 0 auto 18px; font-size: 0.92rem; color: var(--fg-muted); line-height: 1.65; }

/* All clickable items render as full-bordered cards. The engine accent
   is the full border in the data-viz coral, not a left rule. Hover
   signal is uniform — the border darkens to fg. */
.activity-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.activity-card { padding: 14px 16px; cursor: pointer; transition: border-color 0.15s; border: 1px solid var(--fg-hairline); border-radius: 4px; }
.activity-card:hover { border-color: var(--fg); }
.activity-card.engine { border-color: var(--ds-coral); }
.activity-card.engine:hover { border-color: var(--ds-coral); }
.activity-card .label { font-family: var(--font-display); font-weight: 500; font-size: 0.95rem; line-height: 1.35; margin-bottom: 6px; color: var(--fg); letter-spacing: -0.01em; }
.activity-card .ai-label { font-size: 0.78rem; color: var(--fg-muted); }
.activity-card.engine .ai-label { color: var(--ds-coral); font-weight: 500; }

.candidate-card { padding: 16px 18px; margin-bottom: 12px; cursor: pointer; transition: border-color 0.15s; border: 1px solid var(--fg-hairline); border-radius: 4px; }
.candidate-card:hover { border-color: var(--fg); }
.candidate-card.engine-card { border-color: var(--ds-coral); }
.candidate-card.engine-card:hover { border-color: var(--ds-coral); }
.candidate-card .name { font-family: var(--font-display); font-weight: 500; font-size: 1.0rem; margin-bottom: 6px; color: var(--fg); letter-spacing: -0.01em; }
.candidate-card .meta { font-size: 0.9rem; color: var(--fg-muted); line-height: 1.55; }

/* Decisions section */
.section { max-width: 820px; margin: 96px auto 0; padding-top: 40px; border-top: 1px solid var(--fg-hairline); }
.section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 20px; }
.section p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; max-width: 720px; }
.section .lead { font-size: 0.95rem; color: var(--fg-muted); line-height: 1.65; max-width: 720px; margin: 0 0 28px; }
.decision { margin-bottom: 32px; }
.decision .question { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; color: var(--fg); margin: 0 0 8px; letter-spacing: -0.01em; }
.decision .answer { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 6px; max-width: 720px; }
.decision .source { font-size: 0.78rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }

/* Popover — same pattern as the other viewers. */
.popover { position: absolute; display: none; max-width: 420px; min-width: 260px; padding: 14px 18px 16px; background: #FFFFFF; border: 1px solid var(--fg-hairline); border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); z-index: 100; animation: pn-pop 0.18s ease; }
.popover.open { display: block; }
.popover .close { position: absolute; top: 6px; right: 8px; background: transparent; border: 0; cursor: pointer; font-size: 1.1rem; color: var(--fg-muted); padding: 0; line-height: 1; }
.popover .close:hover { color: var(--fg); }
.popover .eyebrow { font-family: var(--font-display); font-size: 0.62rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px; color: var(--fg-muted); }
.popover .eyebrow.engine { color: var(--ds-coral); }
.popover h3 { font-family: var(--font-display); font-size: 1.0rem; font-weight: 500; letter-spacing: -0.015em; margin: 0 0 8px; line-height: 1.3; color: var(--fg); padding-right: 18px; }
.popover .desc { font-size: 0.85rem; line-height: 1.55; color: var(--fg); margin: 0 0 8px; }
.popover .section-label { font-family: var(--font-display); font-size: 0.62rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; font-weight: 500; margin-top: 12px; margin-bottom: 4px; }
.popover .narration { font-size: 0.84rem; line-height: 1.55; color: var(--fg); }
.popover .narration strong { font-weight: 500; }
.popover .citation { font-size: 0.7rem; color: var(--fg-muted); padding: 4px 0 4px 10px; border-left: 1px solid var(--fg-hairline); margin-top: 6px; line-height: 1.5; font-family: ui-monospace, SF Mono, Menlo, monospace; }
.popover .data-block { background: var(--bg-alt); padding: 10px 12px; border-radius: 3px; margin-top: 8px; font-size: 0.78rem; }
.popover .data-block .help { font-size: 0.74rem; color: var(--fg-muted); line-height: 1.5; margin-bottom: 8px; }
.popover .data-table { width: 100%; border-collapse: collapse; font-size: 0.74rem; }
.popover .data-table th, .popover .data-table td { text-align: left; padding: 4px 6px; border-bottom: 1px solid var(--fg-hairline); }
.popover .data-table th { color: var(--fg-muted); font-weight: 500; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.10em; }
.popover .data-table .num { font-family: ui-monospace, SF Mono, Menlo, monospace; }
.popover .data-table .small-sample { color: var(--ds-coral); font-weight: 500; }

.footer { max-width: 820px; margin: 80px auto 0; padding-top: 20px; border-top: 1px solid var(--fg-hairline); color: var(--fg-muted); font-size: 0.78rem; line-height: 1.6; }
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title} · reshuffle</title>
<style>{css}</style>
</head>
<body>
  <div class="container">
    <header>
      <div class="eyebrow">reshuffle</div>
      <h1>{title}</h1>
      <p class="lead">{description}</p>
      <div class="anchor-line">{anchor_id}</div>
    </header>

    <div class="intro">
      <p>This page is an analysis of one process the organization runs today, and where AI might actually change it. It's a read of the structure, not a proposal — the recommendations come at the end, in plain language.</p>

      <p>The starting question is just one: <strong>for this process, what's the most expensive part — doing the work, or keeping the teams that do it aligned?</strong> The answer matters because AI can do two very different things, and they should not be confused.</p>

      <h3>Two different things AI can do</h3>

      <p><strong>Accelerator.</strong> AI makes a single piece of work faster inside a team: drafts a document, summarises a call, looks up a fact. The team moves faster. But the way teams hand off work to each other — the file passes, the alignment meetings, the context rebuilds — stays exactly the same. Useful. Not strategic.</p>

      <p><strong>Shared-knowledge infrastructure.</strong> AI turns the org's knowledge into something genuinely shared: not documents chasing each other across teams, but a common memory each team queries in real time. This dissolves a structural cost. The classical rule "more autonomy on one team = less alignment with the rest" stops holding. It changes how the organization holds the work together.</p>

      <div class="pull">The most common mistake is shipping AI as an accelerator in some teams while believing it has been deployed as infrastructure. Some teams move faster, others don't, and the speed asymmetry makes the alignment problem worse.</div>

      <h3>What keeps each activity tied to the current process</h3>
      <p>Not every activity is alike. For each one we ask what holds it in place, picking from three:</p>
      <ul>
        <li><strong>Rare resource or skill</strong> — only a few people (or a few vendors) can do it, because it takes a regulated qualification, a rare skill, or an exclusive relationship.</li>
        <li><strong>Cost of being wrong</strong> — getting it wrong is expensive (legal, reputational, financial). It needs layered review and someone who signs.</li>
        <li><strong>Cost of keeping teams aligned</strong> — the work itself isn't hard. The expensive part is moving information and decisions between the team upstream and the team downstream.</li>
      </ul>

      <p>Click on any activity or any direction option to read what it actually is, what holds it in place, what AI does to it, and where the analysis comes from.</p>
    </div>

    <div class="panel">
      <div class="panel-head">
        <h2>The process, grouped by what holds each activity in place</h2>
        <p class="panel-hint">The bar shows how this process divides up: how many activities depend on a rare resource, how many on the cost of being wrong, how many on the cost of keeping teams aligned. The bigger the alignment slice, the more this process stands to gain from AI deployed as shared-knowledge infrastructure.</p>
      </div>
      {dist_bar}
      <div class="dist-legend-wrap">{dist_legend}</div>
      <div class="bundle-state">
        <div class="key">How the process runs today</div>
        {bundle_state_html}
      </div>
    </div>

    <div class="ledger">
      <div class="ledger-head">
        <h2>Each activity, one by one</h2>
        <p class="ledger-hint">Each activity in this process, grouped by what holds it in place. The mark on each card says what AI does to it: <strong>infrastructure</strong> (AI changes structure), <strong>accelerator</strong> (changes speed not structure), or <strong>not relevant</strong>. Click a card to read what the activity is and why the analysis stands.</p>
      </div>
      {groups_html}
    </div>

    <div class="candidates">
      <div class="candidates-head">
        <h2>Where AI would change structure, not just speed ({n_engines})</h2>
        <p class="candidates-hint">These are the activities where AI, in the observed data, can do more than accelerate: it can change how knowledge is shared between teams, and so untie a constraint that holds the process together in its current shape. Click a card to read which specific constraint would dissolve.</p>
      </div>
      {engines_html}
    </div>

    <div class="candidates">
      <div class="candidates-head">
        <h2>Direction options ({n_rebundles})</h2>
        <p class="candidates-hint">Below are options for putting this process back together differently — each with a different depth of change, from conservative to radical. They're <strong>options</strong>, not recommendations: the organization picks. For each, read what it changes for the people doing the work, what stays binding anyway, and how risky it is. Click for the detail.</p>
      </div>
      {rebundles_html}
    </div>

    {decisions_section}
  </div>

  <div class="popover" id="popover">
    <button class="close" id="popover-close" aria-label="Close">×</button>
    <div id="popover-body"></div>
  </div>

<script>
const NODES = {nodes_json};
const ENGINES = {engines_json};
const REBUNDLES = {rebundles_json};
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

function renderRebundlePopover(rb) {{
  let html = `<div class="eyebrow">direction option</div>`;
  html += `<h3>${{escapeHtml(rb.name)}}</h3>`;
  if (rb.description) {{
    html += `<div class="desc">${{escapeHtml(rb.description)}}</div>`;
  }}
  if (rb.activities && rb.activities.length) {{
    html += `<div class="section-label">Activities recombined here</div>`;
    html += `<ul style="font-size: 0.82rem; padding-left: 22px; margin: 6px 0; line-height: 1.55;">`;
    for (const aid of rb.activities) {{
      const n = NODES[aid];
      html += `<li>${{escapeHtml(n ? n.label : aid)}}</li>`;
    }}
    html += `</ul>`;
  }}
  if (rb.enabled_by_engine) {{
    const eng = ENGINES.find(e => e.component_id === rb.enabled_by_engine);
    const dissolved = eng?.dissolves_constraint;
    html += `<div class="section-label">What makes it possible</div>`;
    html += `<div class="narration">The activity <strong>${{eng ? escapeHtml(NODES[eng.component_id]?.label || eng.component_id) : '—'}}</strong>`;
    if (dissolved) {{
      html += `, deployed as shared-knowledge infrastructure, dissolves the "${{escapeHtml(CONSTRAINT_LABEL[dissolved] || dissolved)}}" constraint that holds the process together today.`;
    }} else {{
      html += `.`;
    }}
    html += `</div>`;
  }}
  if (rb.remaining_binding_constraint) {{
    html += `<div class="section-label">What stays binding even after</div>`;
    html += `<div class="narration"><strong>${{escapeHtml(CONSTRAINT_LABEL[rb.remaining_binding_constraint] || rb.remaining_binding_constraint)}}.</strong> ${{escapeHtml(CONSTRAINT_PLAIN[rb.remaining_binding_constraint] || '')}}</div>`;
  }}
  if (rb.autonomy_coordination_mode) {{
    const mode = rb.autonomy_coordination_mode;
    const modeLabel = mode === 'flywheel'
      ? 'New rule — more autonomy and more alignment together'
      : 'Old rule — more autonomy means less alignment';
    const modePlain = mode === 'flywheel'
      ? 'Shared knowledge available in real time lets teams stay aligned without losing autonomy.'
      : 'The classical trade-off still holds: more autonomy on one team means less alignment with the rest.';
    html += `<div class="section-label">How this new process would run</div>`;
    html += `<div class="narration"><strong>${{modeLabel}}.</strong> ${{modePlain}}</div>`;
  }}
  if (rb.what_changes) {{
    html += `<div class="section-label">What changes for the people in the process</div>`;
    html += `<div class="desc">${{escapeHtml(rb.what_changes)}}</div>`;
  }}
  if (rb.risk_of_rebundle) {{
    html += `<div class="section-label">How risky the move is</div>`;
    html += `<div class="desc">${{escapeHtml(rb.risk_of_rebundle)}}</div>`;
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
    if (n.classList && n.classList.contains('candidate-card') && n.dataset.id) {{
      const node = NODES[n.dataset.id];
      if (node) showFor(n, renderActivityPopover(node));
      return;
    }}
    if (n.classList && n.classList.contains('candidate-card') && n.dataset.rb) {{
      const data = REBUNDLES[parseInt(n.dataset.rb, 10)];
      if (data) showFor(n, renderRebundlePopover(data));
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

    # Distribution
    dist = {"scarcity": 0, "risk": 0, "coordination": 0}
    for c in comps:
        pc = c.get("primary_constraint")
        if pc in dist:
            dist[pc] += 1
    total = sum(dist.values()) or 1

    bar_segs = []
    legend_items = []
    for ct in ("coordination", "risk", "scarcity"):
        n = dist[ct]
        if n > 0:
            pct = n / total * 100
            bar_segs.append(f'<div class="seg {ct}" style="width:{pct}%" title="{CONSTRAINT_LABEL[ct]}: {n}"></div>')
        legend_items.append(
            f'<div class="item"><span class="swatch" style="background: var(--{ct})"></span>'
            f'<div><strong>{CONSTRAINT_LABEL[ct]}</strong> <span class="count">— {n} {"activity" if n == 1 else "activities"}</span><br>'
            f'<span style="font-size: 0.82rem; color: var(--fg-muted);">{CONSTRAINT_PLAIN[ct]}</span></div></div>'
        )
    dist_bar = f'<div class="dist-bar">{"".join(bar_segs)}</div>'
    dist_legend = f'<div class="dist-legend">{"".join(legend_items)}</div>'

    # Bundle state
    bd = d.get("bundle_state") or {}
    bd_blocks = []
    if bd.get("current_mode"):
        mode = bd["current_mode"]
        bd_blocks.append(
            f'<p class="text"><strong>{escape(MODE_LABEL.get(mode, mode))}.</strong> {escape(MODE_PLAIN.get(mode, ""))}</p>'
        )
    me = bd.get("mode_evidence") or []
    if me:
        ev_text = []
        for e in me:
            cl = e.get("claim", "") if isinstance(e, dict) else str(e)
            src = e.get("source", "") if isinstance(e, dict) else ""
            ev_text.append(f'{escape(cl)} <span style="color: var(--fg-muted); font-size: 0.82rem;">({escape(src)})</span>')
        bd_blocks.append(
            f'<div class="key" style="margin-top: 18px;">Where this read comes from</div>'
            f'<p class="text">{"<br>".join(ev_text)}</p>'
        )
    cpr = bd.get("coordination_paradox_risk")
    if cpr:
        bd_blocks.append(
            f'<div class="key" style="margin-top: 18px;">Trap to avoid when deploying AI</div>'
            f'<p class="text">{escape(cpr)}</p>'
        )
    bundle_state_html = "".join(bd_blocks) if bd_blocks else ""

    # Groups by constraint with plain-language explanatory paragraph
    groups_html_parts = []
    group_order = ("coordination", "risk", "scarcity")
    group_explanations = {
        "coordination": "For these activities the expensive part isn't doing the work — it's coordinating information and decisions with other teams. Natural candidates for AI deployed as shared-knowledge infrastructure.",
        "risk": "For these activities, being wrong has serious consequences. AI can help prepare and check, but the final responsibility stays human — the constraint doesn't dissolve.",
        "scarcity": "For these activities you need someone with a skill, a qualification, or a relationship that doesn't scale. AI can support but not replace the person who holds the rare resource.",
    }
    for ct in group_order:
        in_group = [c for c in comps if c.get("primary_constraint") == ct]
        if not in_group:
            continue
        cards = []
        for c in in_group:
            ac = c.get("ai_classification")
            engine_class = " engine" if ac == "engine" else ""
            ai_label_short = AI_CLASS_SHORT.get(ac, "—")
            cards.append(
                f'<div class="activity-card{engine_class}" data-id="{escape(c["id"])}">'
                f'<div class="label">{escape(c.get("label", ""))}</div>'
                f'<div class="ai-label">AI is {escape(ai_label_short)}</div>'
                f'</div>'
            )
        groups_html_parts.append(
            f'<div class="group">'
            f'<div class="group-header">'
            f'<span class="swatch" style="background: var(--{ct})"></span>'
            f'<h3>{CONSTRAINT_LABEL[ct]}</h3>'
            f'<span class="count">{len(in_group)} {"activity" if len(in_group) == 1 else "activities"}</span>'
            f'</div>'
            f'<p class="group-explain">{group_explanations[ct]}</p>'
            f'<div class="activity-grid">{"".join(cards)}</div>'
            f'</div>'
        )
    unset = [c for c in comps if not c.get("primary_constraint")]
    if unset:
        cards = "".join(
            f'<div class="activity-card" data-id="{escape(c["id"])}">'
            f'<div class="label">{escape(c.get("label", ""))}</div>'
            f'<div class="ai-label">unclassified</div>'
            f'</div>' for c in unset
        )
        groups_html_parts.append(
            f'<div class="group">'
            f'<div class="group-header"><h3>Unclassified</h3>'
            f'<span class="count">{len(unset)} {"activity" if len(unset) == 1 else "activities"}</span></div>'
            f'<div class="activity-grid">{cards}</div></div>'
        )
    groups_html = "\n".join(groups_html_parts) if groups_html_parts else '<p style="max-width: 820px; margin: 0 auto; color: var(--fg-muted);">No activities in scope.</p>'

    # Engine candidates
    engines = d.get("engine_candidates") or []
    by_id = {c["id"]: c for c in comps}
    engine_cards = []
    for e in engines:
        cid = e.get("component_id")
        c = by_id.get(cid)
        if not c:
            continue
        dissolves = e.get("dissolves_constraint", "")
        engine_cards.append(
            f'<div class="candidate-card engine-card" data-id="{escape(cid)}">'
            f'<div class="name">{escape(c.get("label", ""))}</div>'
            f'<div class="meta">Deployed as shared-knowledge infrastructure, dissolves: <strong>{escape(CONSTRAINT_LABEL.get(dissolves, dissolves))}</strong></div>'
            f'</div>'
        )
    engines_html = "\n".join(engine_cards) if engine_cards else '<p style="color: var(--fg-muted); font-size: 0.9rem;">No place identified where AI would change the structure of this process. Every AI use found is an accelerator. See the trap above: shipping accelerators without infrastructure can make the process worse, not better.</p>'

    # Rebundle candidates
    rebundles = d.get("rebundle_candidates") or []
    rb_cards = []
    for i, rb in enumerate(rebundles):
        rc = rb.get("remaining_binding_constraint", "")
        rb_cards.append(
            f'<div class="candidate-card" data-rb="{i}">'
            f'<div class="name">{escape(rb.get("name", "?"))}</div>'
            f'<div class="meta">What stays binding: <strong>{escape(CONSTRAINT_LABEL.get(rc, rc))}</strong> · '
            f'covers {len(rb.get("activities") or [])} {"activity" if len(rb.get("activities") or []) == 1 else "activities"}</div>'
            f'</div>'
        )
    rebundles_html = "\n".join(rb_cards) if rb_cards else '<p style="color: var(--fg-muted); font-size: 0.9rem;">No direction option proposed — at least one place where AI would be deployed as infrastructure is required.</p>'

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
    engines_json = json.dumps(engines, ensure_ascii=False)
    rebundles_json = json.dumps(rebundles, ensure_ascii=False)

    return HTML_TEMPLATE.format(
        css=base_css() + EXTRA_CSS,
        title=escape(title),
        anchor_id=escape(anchor_id),
        description=escape(description_text),
        dist_bar=dist_bar,
        dist_legend=dist_legend,
        bundle_state_html=bundle_state_html,
        groups_html=groups_html,
        engines_html=engines_html,
        n_engines=len(engines),
        rebundles_html=rebundles_html,
        n_rebundles=len(rebundles),
        decisions_section=decisions_section,
        nodes_json=nodes_json,
        engines_json=engines_json,
        rebundles_json=rebundles_json,
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
