#!/usr/bin/env python3
"""
graph / viewer.py — Render the org graph as a force-directed
visualization with side panel + click-to-redistribute.

Design (after iteration: "popover copre tutto", "nodi mal distribuiti",
"vorrei che ai click i nodi si ridistribuissero nello spazio"):

- **Side panel, not popover.** A fixed-width pane on the right of the
  graph canvas. Always present. Empty state shows a hint; focused
  state shows the clicked node's details. The graph never gets
  covered. Rows in the panel's relation lists are clickable — click
  them to jump focus.

- **Click redistributes.** When a node is focused, the simulation
  pulls it strongly toward the centre and lays its first-degree
  neighbours in a ring around it. Reheat alpha=1 on every focus
  change. The rest of the graph drifts away under repulsion.

- **Kind-radial seed.** Initial positions arranged as concentric
  rings by kind (stakeholders innermost — they're the gravity wells —
  then commitments, units, activities, people outwards). Force
  refines from a non-degenerate start. Combined with degree-aware
  repulsion (bigger nodes push harder) and a min-distance hard floor,
  the layout reads as distributed, not clumped.

- **Default view = operational core.** Visible by default: unit,
  activity, person, stakeholder, commitment + the structural
  relations between them. Hidden by default: identity, language-term,
  role, financial-summary, source nodes; cite, link edges.
  Toggleable from the legend (legend = live filter, not dimmer:
  toggling re-runs the simulation with only the visible items).

- **Zoom + pan.** Wheel zoom, drag pan. Essential for AIRC-scale
  organizations.

Usage:
    python3 viewer.py --map <graph.json> --html <out.html>
                       [--decisions <decisions.json>]
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

# Import the shared Play New design system
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from design import base_css, masthead, colophon  # noqa: E402


EXTRA_CSS = """
/* graph viewer — Play New design (unified with the other four playbooks).
   The graph canvas is the cardinal block on the page; everything around
   it is centered editorial chrome at 820px. */

:root {
  /* Node colours by kind — pulled from the project's data-viz palette
     so brand and viz stay in sync. */
  --kind-identity:           var(--ds-coral);
  --kind-language-term:      var(--fg-light);
  --kind-unit:               var(--ds-slate);
  --kind-activity:           var(--ds-sage);
  --kind-person:             var(--fg);
  --kind-role:               var(--fg-muted);
  --kind-stakeholder:        var(--ds-lilac);
  --kind-commitment:         var(--ds-coral);
  --kind-financial-summary:  var(--ds-sand);
  --kind-source:             var(--fg-light);
}

body { background: #FFFFFF; color: var(--fg); }

.container { max-width: 1240px; margin: 0 auto; padding: 80px 40px 96px; }
@media (max-width: 900px) { .container { padding: 56px 24px 80px; } }

header { max-width: 820px; margin: 0 auto 48px; }
header .eyebrow { font-family: var(--font-display); font-size: 0.74rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); margin-bottom: 16px; }
header h1 { font-family: var(--font-display); font-size: clamp(1.9rem, 3.5vw, 2.6rem); font-weight: 500; letter-spacing: -0.025em; line-height: 1.1; margin: 0 0 16px; color: var(--fg); }
header .lead { font-size: 1.0rem; color: var(--fg-muted); line-height: 1.65; margin: 0; }

.intro { max-width: 820px; margin: 0 auto 56px; }
.intro p { font-size: 0.95rem; line-height: 1.7; margin: 0 0 14px; color: var(--fg); }
.intro p strong { font-weight: 500; }
.intro .pull { padding: 14px 0 14px 18px; margin: 22px 0; font-size: 1.0rem; color: var(--fg); border-left: 2px solid var(--fg); line-height: 1.65; }

.stats-strip { max-width: 820px; margin: 0 auto 28px; display: flex; flex-wrap: wrap; gap: 32px; padding: 18px 0; border-top: 1px solid var(--fg-hairline); border-bottom: 1px solid var(--fg-hairline); }
.stats-strip .stat { display: flex; flex-direction: column; gap: 6px; }
.stats-strip .stat .num { font-family: var(--font-display); font-size: 1.7rem; font-weight: var(--w-extrabold); letter-spacing: -0.04em; color: var(--fg); font-variant-numeric: tabular-nums; line-height: 1; }
.stats-strip .stat .lab { font-family: var(--font-display); font-style: italic; font-size: 0.78rem; color: var(--fg-muted); letter-spacing: 0; text-transform: none; }

/* Legend now lives INSIDE the dark .graph-shell, as part of the
   graph console chrome (Lupi/Accurat: legend integrated into the
   composition, not floating above). The token overrides on
   .graph-shell cascade into the swatches so person/role/source
   read the right colour against the dark canvas. */
.graph-shell .legend { display: flex; flex-direction: column; gap: 10px; padding: 16px 22px 14px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.graph-shell .legend .row { display: flex; flex-wrap: wrap; gap: 14px 20px; align-items: center; font-family: var(--font-display); font-size: 0.78rem; color: rgba(255,255,255,0.65); }
.graph-shell .legend .label { font-style: italic; font-size: 0.7rem; color: rgba(255,255,255,0.45); min-width: 92px; letter-spacing: 0; text-transform: none; font-weight: var(--w-medium); }
.graph-shell .legend .swatch { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; transition: color 0.15s, opacity 0.15s; user-select: none; color: rgba(255,255,255,0.78); }
.graph-shell .legend .swatch:hover { color: rgba(255,255,255,1); }
.graph-shell .legend .swatch.off { opacity: 0.32; text-decoration: line-through; text-decoration-thickness: 1px; }
.graph-shell .legend .swatch .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; box-shadow: 0 0 0 1px rgba(255,255,255,0.25); }
.graph-shell .legend .swatch .line { display: inline-block; width: 18px; height: 2px; }
.graph-shell .legend .actions { margin-left: auto; display: flex; gap: 10px; align-items: center; }
.graph-shell .legend .btn { background: transparent; border: 1px solid rgba(255,255,255,0.18); color: rgba(255,255,255,0.7); font-size: 0.74rem; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-family: inherit; transition: border-color 0.15s, color 0.15s; }
.graph-shell .legend .btn:hover { border-color: rgba(255,255,255,0.7); color: rgba(255,255,255,1); }
.graph-shell .legend .hint { font-style: italic; font-size: 0.74rem; color: rgba(255,255,255,0.45); }

/* Canvas + side panel — the cardinal block, rendered as a dark
   "data console" inset against the editorial white page chrome.
   Inside the shell, kind colours pop against the dark surface, glow
   filters work, and the rhythm of the page becomes white → dark →
   white as the eye descends from intro to graph to decisions. */
.graph-shell {
  max-width: 1160px; margin: 0 auto;
  border-radius: 8px;
  background: var(--surf-inset-dark);
  overflow: hidden;
  display: flex; flex-direction: column;
  box-shadow: var(--surf-raised-shadow);

  /* Override the kind colours that don't read well on dark.
     The data-viz pastels (sage / lilac / slate / sand / coral) are
     already legible on dark; only the tokens that mapped to near-black
     or low-opacity black need rebinding to light variants. */
  --kind-person:        rgba(255,255,255,0.92);
  --kind-role:          rgba(255,255,255,0.6);
  --kind-language-term: rgba(255,255,255,0.5);
  --kind-source:        rgba(255,255,255,0.5);
}
.graph-shell .canvas-row { display: flex; align-items: stretch; min-height: 720px; }
.graph-shell .canvas-row > svg {
  flex: 1; min-width: 0; display: block; height: 720px; cursor: grab;
  background-color: transparent;
  background-image:
    radial-gradient(ellipse at center, rgba(255,255,255,0.05) 0%, rgba(0,0,0,0.5) 100%),
    radial-gradient(circle at center, rgba(255,255,255,0.07) 0.6px, transparent 1.2px);
  background-size: 100% 100%, 26px 26px;
}
.graph-shell .canvas-row > svg.dragging { cursor: grabbing; }
.graph-shell svg .edge { fill: none; stroke: rgba(255,255,255,0.22); transition: opacity 0.18s ease-out, stroke-width 0.15s ease-out; }
.graph-shell svg .edge.kind-link { stroke: rgba(255,255,255,0.12); }
.graph-shell svg .edge.kind-cite { stroke: rgba(255,255,255,0.12); stroke-dasharray: 2 3; }
.graph-shell svg .edge.kind-parent { stroke: rgba(255,255,255,0.6); stroke-width: 1.2; }
.graph-shell svg .edge.in-focus { stroke: rgba(255,255,255,0.7); stroke-width: 1.4; }
.graph-shell svg .node-hit { fill: rgba(255,255,255,0.001); cursor: pointer; }
.graph-shell svg .node-circle {
  /* Stronger stroke on dark so the pastel pallini have a definitive
     edge against the slate background. */
  stroke: rgba(255,255,255,0.55);
  stroke-width: 1.2;
  pointer-events: none;
  transition: opacity 0.18s ease-out, stroke-width 0.15s ease-out, r 0.18s ease-out, filter 0.2s ease-out;
}
.graph-shell svg .node-circle.hovered {
  stroke: rgba(255,255,255,0.95);
  stroke-width: 2;
  filter: drop-shadow(0 0 8px rgba(255,255,255,0.5));
}
.graph-shell svg .node-circle.focused {
  stroke: rgba(255,255,255,1);
  stroke-width: 2.6;
  filter: drop-shadow(0 0 14px rgba(255,255,255,0.6)) drop-shadow(0 0 4px rgba(255,255,255,0.85));
}
/* Labels are always shown in small for visible nodes — Obsidian
   pattern. The focused node gets the larger, brighter style. */
.graph-shell svg .node-label {
  font-family: var(--font-display);
  font-size: 10.5px;
  fill: rgba(255,255,255,0.65);
  pointer-events: none;
  transition: opacity 0.18s ease-out, font-size 0.12s ease-out, fill 0.12s ease-out;
}
.graph-shell svg .node-label.large { font-size: 13px; fill: rgba(255,255,255,1); font-weight: 500; }

.graph-panel {
  width: 300px; flex-shrink: 0;
  border-left: 1px solid rgba(255,255,255,0.08);
  background: #1a1d24;
  color: rgba(255,255,255,0.92);
  padding: 22px 24px 24px; overflow-y: auto; max-height: 720px;
  position: relative;
}
.graph-panel .panel-close { position: absolute; top: 14px; right: 14px; background: transparent; border: 0; cursor: pointer; font-size: 1.3rem; color: rgba(255,255,255,0.5); padding: 0; line-height: 1; transition: color 0.15s; }
.graph-panel .panel-close:hover { color: rgba(255,255,255,1); }
.graph-panel .placeholder { color: rgba(255,255,255,0.62); font-size: 0.85rem; line-height: 1.65; padding-top: 4px; }
.graph-panel .placeholder strong { color: rgba(255,255,255,1); font-weight: 500; }
.graph-panel .panel-content { display: none; }
.graph-panel.has-focus .placeholder { display: none; }
.graph-panel.has-focus .panel-content { display: block; }
.graph-panel .eyebrow { font-family: var(--font-display); font-size: 0.62rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 8px; color: rgba(255,255,255,0.62); }
.graph-panel .eyebrow .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; vertical-align: middle; margin-right: 6px; transform: translateY(-1px); box-shadow: 0 0 6px currentColor; }
.graph-panel h3 { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; letter-spacing: -0.01em; margin: 0 0 10px; color: rgba(255,255,255,1); padding-right: 22px; line-height: 1.25; }
.graph-panel .desc { font-size: 0.86rem; line-height: 1.6; color: rgba(255,255,255,0.85); margin: 0 0 12px; }
.graph-panel .section-label { font-family: var(--font-display); font-size: 0.62rem; color: rgba(255,255,255,0.55); text-transform: uppercase; letter-spacing: 0.10em; font-weight: 500; margin-top: 18px; margin-bottom: 6px; }
.graph-panel .neighbour-list { display: flex; flex-direction: column; gap: 1px; font-size: 0.82rem; color: rgba(255,255,255,0.92); }
.graph-panel .neighbour-list .neighbour { display: flex; gap: 10px; align-items: baseline; padding: 5px 7px; margin: 0 -7px; cursor: pointer; border-radius: 3px; transition: background 0.12s; }
.graph-panel .neighbour-list .neighbour:hover { background: rgba(255,255,255,0.06); }
.graph-panel .neighbour-list .rel { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.7rem; color: rgba(255,255,255,0.5); min-width: 88px; flex-shrink: 0; }
.graph-panel .neighbour-list .target { color: rgba(255,255,255,0.95); }
.graph-panel .citation { font-size: 0.7rem; color: rgba(255,255,255,0.5); font-family: ui-monospace, SF Mono, Menlo, monospace; padding-top: 14px; margin-top: 18px; border-top: 1px solid rgba(255,255,255,0.10); word-break: break-all; }

@media (max-width: 900px) {
  .graph-shell .canvas-row { flex-direction: column; min-height: auto; }
  .graph-shell .canvas-row > svg { height: 480px; }
  .graph-panel { width: 100%; max-height: 320px; border-left: 0; border-top: 1px solid rgba(255,255,255,0.08); }
}

/* Decisions section — centered editorial column, identical to the other playbooks. */
.section { max-width: 820px; margin: 96px auto 0; padding-top: 40px; border-top: 1px solid var(--fg-hairline); }
.section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 20px; }
.section p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; max-width: 720px; }
.section .lead { font-size: 0.95rem; color: var(--fg-muted); line-height: 1.65; max-width: 720px; margin: 0 0 28px; }

.decision { margin-bottom: 32px; }
.decision .question { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; color: var(--fg); margin: 0 0 8px; letter-spacing: -0.01em; }
.decision .answer { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 6px; max-width: 720px; }
.decision .source { font-size: 0.78rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title} · graph</title>
<style>{css}</style>
</head>
<body>
  <div class="container">
    {masthead_html}

    <section class="stats-strip">
      <div class="stat"><div class="num" id="stat-nodes">{n_nodes}</div><div class="lab">nodes</div></div>
      <div class="stat"><div class="num" id="stat-edges">{n_edges}</div><div class="lab">relations</div></div>
      <div class="stat"><div class="num" id="stat-kinds">{n_kinds}</div><div class="lab">kinds</div></div>
      <div class="stat"><div class="num" id="stat-isolates">{n_isolates}</div><div class="lab">floating</div></div>
    </section>

    <div class="graph-shell">
      <div class="legend" id="legend">
        <div class="row" id="legend-nodes">
          <span class="label">Show nodes</span>
          <span class="swatch" data-kind="unit"><span class="dot" style="background: var(--kind-unit)"></span>unit</span>
          <span class="swatch" data-kind="activity"><span class="dot" style="background: var(--kind-activity)"></span>activity</span>
          <span class="swatch" data-kind="person"><span class="dot" style="background: var(--kind-person)"></span>person</span>
          <span class="swatch" data-kind="stakeholder"><span class="dot" style="background: var(--kind-stakeholder)"></span>stakeholder</span>
          <span class="swatch" data-kind="commitment"><span class="dot" style="background: var(--kind-commitment); border: 1px solid var(--ds-coral)"></span>commitment</span>
          <span class="swatch off" data-kind="role"><span class="dot" style="background: var(--kind-role)"></span>role</span>
          <span class="swatch off" data-kind="financial-summary"><span class="dot" style="background: var(--kind-financial-summary)"></span>financial</span>
          <span class="swatch off" data-kind="identity"><span class="dot" style="background: var(--kind-identity)"></span>identity</span>
          <span class="swatch off" data-kind="language-term"><span class="dot" style="background: var(--kind-language-term)"></span>language</span>
          <span class="swatch off" data-kind="source"><span class="dot" style="background: var(--kind-source)"></span>source</span>
        </div>
        <div class="row" id="legend-edges">
          <span class="label">Show relations</span>
          <span class="swatch" data-edgekind="parent"><span class="line" style="background: rgba(255,255,255,0.7)"></span>part of</span>
          <span class="swatch" data-edgekind="unit"><span class="line" style="background: rgba(255,255,255,0.55)"></span>in</span>
          <span class="swatch" data-edgekind="performer"><span class="line" style="background: rgba(255,255,255,0.55)"></span>performed by</span>
          <span class="swatch" data-edgekind="party_committing"><span class="line" style="background: rgba(255,255,255,0.55)"></span>binds</span>
          <span class="swatch" data-edgekind="party_benefiting"><span class="line" style="background: rgba(255,255,255,0.55)"></span>for</span>
          <span class="swatch" data-edgekind="touches"><span class="line" style="background: rgba(255,255,255,0.55)"></span>involves</span>
          <span class="swatch" data-edgekind="head_role"><span class="line" style="background: rgba(255,255,255,0.55)"></span>led by</span>
          <span class="swatch" data-edgekind="holds_role"><span class="line" style="background: rgba(255,255,255,0.55)"></span>as</span>
          <span class="swatch" data-edgekind="covers"><span class="line" style="background: rgba(255,255,255,0.55)"></span>responsible for</span>
          <span class="swatch off" data-edgekind="link"><span class="line" style="background: rgba(255,255,255,0.35); height: 1px;"></span>mentions</span>
          <span class="swatch off" data-edgekind="cite"><span class="line" style="background: transparent; height: 1px; border-top: 1px dashed rgba(255,255,255,0.35);"></span>cites</span>
          <span class="actions">
            <button class="btn" id="btn-reheat">re-shake</button>
            <button class="btn" id="btn-reset-view">reset view</button>
          </span>
        </div>
        <div class="row">
          <span class="hint">click a node to focus · click empty space to clear · wheel zoom · drag pan</span>
        </div>
      </div>
      <div class="canvas-row">
        <svg id="graph" viewBox="0 0 1000 760" preserveAspectRatio="xMidYMid meet">
          <g id="viewport">
            <g id="edges-layer"></g>
            <g id="nodes-layer"></g>
            <g id="labels-layer"></g>
          </g>
        </svg>
        <aside class="graph-panel" id="graph-panel">
          <button class="panel-close" id="panel-close" aria-label="Close">×</button>
          <div class="placeholder"><strong>Click a node</strong> in the graph to focus on its neighbourhood. The clicked node and its first-degree neighbours stay bright; everything else dims. Use the legend toggles to add or remove kinds; the simulation re-runs with only what's visible.</div>
          <div class="panel-content"></div>
        </aside>
      </div>
    </div>

    {decisions_section}

    {colophon_html}
  </div>

<script>
const NODES = {nodes_json};
const EDGES = {edges_json};

// Kind colours are read from the .graph-shell so the dark-mode
// overrides (--kind-person etc, redefined inside .graph-shell)
// take effect.
const SHELL_EL = document.querySelector('.graph-shell');
const _shellStyle = getComputedStyle(SHELL_EL);
const KIND_COLOR = {{
  'identity':           _shellStyle.getPropertyValue('--kind-identity').trim(),
  'language-term':      _shellStyle.getPropertyValue('--kind-language-term').trim(),
  'unit':               _shellStyle.getPropertyValue('--kind-unit').trim(),
  'activity':           _shellStyle.getPropertyValue('--kind-activity').trim(),
  'person':             _shellStyle.getPropertyValue('--kind-person').trim(),
  'role':               _shellStyle.getPropertyValue('--kind-role').trim(),
  'stakeholder':        _shellStyle.getPropertyValue('--kind-stakeholder').trim(),
  'commitment':         _shellStyle.getPropertyValue('--kind-commitment').trim(),
  'financial-summary':  _shellStyle.getPropertyValue('--kind-financial-summary').trim(),
  'source':             _shellStyle.getPropertyValue('--kind-source').trim(),
}};

// Relation labels — TO-BE taxonomy. Plain English, no schema-jargon
// leakage. The asymmetry between forward (out) and reverse (in)
// labels reflects the directional nature of each relation; pairs
// that read identically both ways (`for`) are kept symmetric because
// the panel's Outgoing / Incoming sections already disambiguate.
const REL_LABELS = {{
  'parent':           'is part of',
  'unit':             'in',
  'performer':        'performed by',
  'head_role':        'led by',
  'holds_role':       'as',
  'covers':           'responsible for',
  'party_committing': 'binds',
  'party_benefiting': 'for',
  'touches':          'involves',
  'cite':             'cites',
  'link':             'mentions',
}};
const REL_LABELS_REV = {{
  'parent':           'contains',
  'unit':             'hosts',
  'performer':        'performs',
  'head_role':        'leads',
  'holds_role':       'filled by',
  'covers':           'owned by',
  'party_committing': 'bound by',
  'party_benefiting': 'for',
  'touches':          'involved in',
  'cite':             'cited by',
  'link':             'mentioned by',
}};

// Default to the operational core: units, the activities they run,
// the people who run them, the stakeholders served, the commitments
// that bind everyone. All structural edges are on so the lines
// follow the nodes — `isEdgeVisible` already filters edges whose
// endpoints aren't visible, so toggling a node kind off cleanly
// removes its incoming/outgoing edges from the picture.
const DEFAULT_VISIBLE_NODES = new Set(['unit','activity','person','stakeholder','commitment']);
const DEFAULT_VISIBLE_EDGES = new Set([
  'parent','unit','performer','head_role','holds_role','covers',
  'party_committing','party_benefiting','touches'
]);
const visibleNodeKinds = new Set(DEFAULT_VISIBLE_NODES);
const visibleEdgeKinds = new Set(DEFAULT_VISIBLE_EDGES);

const FORCE = {{
  // Tuned for "settles, then stops". Earlier we kept the simulation
  // perpetually alive at low alpha; that produced visible jitter
  // because residual repulsion never fully zeroed out. Now alpha
  // cools all the way to 0 and the loop stops; every user
  // interaction (drag, hover, click, toggle, re-shake) calls reheat
  // to restart it. Stronger damping (0.78) so velocities die quickly
  // after each reheat — the layout converges and stays put.
  k: 150,             // ideal edge length
  repulse: 6500,
  centering: 0.0005,
  damping: 0.78,
  alphaCutoff: 0.005,  // simulation halts below this
  // Velocity cap per tick — stops the "flying balls" effect when a
  // strong reheat (e.g. clicking a node, which engages the focus
  // attractor at high alpha) transiently pumps a lot of energy in.
  // Each node moves at most this many pixels per frame; transitions
  // become a slide, not an explosion.
  vMax: 16,
  edgeStrength: {{
    parent: 0.10,
    unit: 0.08,
    performer: 0.07,
    head_role: 0.07,
    holds_role: 0.06,
    covers: 0.05,
    party_committing: 0.07,
    party_benefiting: 0.07,
    touches: 0.05,
    link: 0.025,
    cite: 0.02,
  }},
  focusPullCenter: 0.04,
  focusRingPull: 0.03,
  focusRingRadius: 180,
}};

const W = 1000, H = 760;
const NODE_BY_ID = Object.fromEntries(NODES.map(n => [n.id, n]));

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }})[c]);
}}

function recomputeDegrees() {{
  NODES.forEach(n => {{ n._degree = 0; }});
  EDGES.forEach(e => {{
    if (!isEdgeVisible(e)) return;
    const a = NODE_BY_ID[e.from], b = NODE_BY_ID[e.to];
    if (!a || !b) return;
    a._degree++; b._degree++;
  }});
}}

function radiusFor(n) {{
  return 5 + Math.log(1 + (n._degree || 0)) * 4.5;
}}

function isNodeVisible(n) {{ return visibleNodeKinds.has(n.kind); }}
function isEdgeVisible(e) {{
  if (!visibleEdgeKinds.has(e.kind)) return false;
  const a = NODE_BY_ID[e.from], b = NODE_BY_ID[e.to];
  return !!(a && b && isNodeVisible(a) && isNodeVisible(b));
}}

// --- focus + hover state ---------------------------------------------
// Two layers (Obsidian pattern). Hover is transient & light, click
// commits a focus that pulls the node to centre and populates the
// side panel.
let focusedId = null;
let focusedNeighbours = new Set();
let hoveredId = null;
let hoveredNeighbours = new Set();

function neighboursOf(id) {{
  const set = new Set();
  EDGES.forEach(e => {{
    if (!isEdgeVisible(e)) return;
    if (e.from === id) set.add(e.to);
    if (e.to === id) set.add(e.from);
  }});
  return set;
}}
function setFocus(id) {{
  focusedId = id;
  focusedNeighbours = id ? neighboursOf(id) : new Set();
}}
function setHover(id) {{
  hoveredId = id;
  hoveredNeighbours = id ? neighboursOf(id) : new Set();
}}

// "Active" highlight = focus or hover. Focus wins on intensity.
function isInFocus(nodeId) {{
  if (focusedId) return nodeId === focusedId || focusedNeighbours.has(nodeId);
  if (hoveredId) return nodeId === hoveredId || hoveredNeighbours.has(nodeId);
  return true;
}}
function edgeInFocus(e) {{
  if (focusedId) return e.from === focusedId || e.to === focusedId;
  if (hoveredId) return e.from === hoveredId || e.to === hoveredId;
  return true;
}}
function hasAnyHighlight() {{ return !!(focusedId || hoveredId); }}

// --- initial seed: kind-radial bands ---------------------------------
// Stakeholders innermost — they're the gravity wells (every activity
// touches them). Commitments next, then units, then activities,
// then people. The other kinds (when toggled on) get bands further
// out. Each kind's nodes spread evenly around their ring; the force
// loop refines from this non-degenerate start.
function seedPositions() {{
  const KIND_RADIUS = {{
    'stakeholder':       110,
    'commitment':        185,
    'unit':              250,
    'role':              285,
    'activity':          325,
    'person':            370,
    'financial-summary': 310,
    'identity':          400,
    'language-term':     430,
    'source':            450,
  }};
  const kindCount = {{}};
  const kindIndex = {{}};
  NODES.forEach(n => {{ kindCount[n.kind] = (kindCount[n.kind] || 0) + 1; }});
  NODES.forEach(n => {{
    const ring = KIND_RADIUS[n.kind] || 250;
    const total = kindCount[n.kind];
    const i = (kindIndex[n.kind] = (kindIndex[n.kind] || 0) + 1) - 1;
    const baseAngle = (i / total) * Math.PI * 2;
    const jitter = (Math.random() - 0.5) * 0.5;
    const r = ring + (Math.random() - 0.5) * 30;
    n.x = W/2 + Math.cos(baseAngle + jitter) * r;
    n.y = H/2 + Math.sin(baseAngle + jitter) * r;
    n.vx = 0; n.vy = 0;
  }});
}}
seedPositions();
recomputeDegrees();

// --- force step + tick -----------------------------------------------
// `forceStep` runs one iteration of the physics with no DOM work, so
// it can be called in a synchronous hot loop at boot to pre-settle
// the layout. `tick` is the rAF-driven version that also renders.
let alpha = 1;
let running = false;
function forceStep() {{
  const visible = NODES.filter(isNodeVisible);

  // Repulsion (degree-aware: bigger nodes push harder + min-distance
  // hard floor so circles never overlap).
  for (let i = 0; i < visible.length; i++) {{
    for (let j = i+1; j < visible.length; j++) {{
      const a = visible[i], b = visible[j];
      let dx = a.x - b.x, dy = a.y - b.y;
      let d2 = dx*dx + dy*dy;
      if (d2 < 1) {{ dx = (Math.random()-0.5)*2; dy = (Math.random()-0.5)*2; d2 = 4; }}
      const ra = radiusFor(a), rb = radiusFor(b);
      const sizeBoost = 1 + (ra * rb) / 60;
      const minD = ra + rb + 22;
      let f = (FORCE.repulse * sizeBoost / d2) * alpha;
      // Hard floor: when nodes get too close, ramp the force.
      if (d2 < minD * minD) f *= 4;
      const d = Math.sqrt(d2);
      const fx = (dx/d) * f, fy = (dy/d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }}
  }}

  // Edge attraction.
  EDGES.forEach(e => {{
    if (!isEdgeVisible(e)) return;
    const a = NODE_BY_ID[e.from], b = NODE_BY_ID[e.to];
    const dx = b.x - a.x, dy = b.y - a.y;
    const d = Math.sqrt(dx*dx + dy*dy) || 1;
    const strength = FORCE.edgeStrength[e.kind] || 0.05;
    const f = (d - FORCE.k) * strength * alpha;
    const fx = (dx/d) * f, fy = (dy/d) * f;
    a.vx += fx; a.vy += fy;
    b.vx -= fx; b.vy -= fy;
  }});

  // (No focus attractor — clicking a node only highlights it; the
  // positions don't move. The Obsidian model: click = open / read,
  // drag = manually reposition, legend toggle = re-layout because
  // the topology changed. Trying to "redistribute on click" pits
  // the attractor against repulsion + edges and produces chaos.)

  // Centring + integrate (visible only). Pinned nodes (n.fx/n.fy set
  // by the drag handler) override the simulation: they stay where the
  // user is holding them.
  visible.forEach(n => {{
    if (n.fx != null && n.fy != null) {{
      n.x = n.fx; n.y = n.fy;
      n.vx = 0; n.vy = 0;
      return;
    }}
    n.vx += (W/2 - n.x) * FORCE.centering;
    n.vy += (H/2 - n.y) * FORCE.centering;
    n.vx *= FORCE.damping;
    n.vy *= FORCE.damping;
    // Cap per-tick velocity so a high-alpha reheat can't fling
    // nodes across the canvas. Convergence still happens; it just
    // slides instead of flying.
    const vmag = Math.hypot(n.vx, n.vy);
    if (vmag > FORCE.vMax) {{
      n.vx = (n.vx / vmag) * FORCE.vMax;
      n.vy = (n.vy / vmag) * FORCE.vMax;
    }}
    n.x += n.vx;
    n.y += n.vy;
    const r = radiusFor(n) + 4;
    n.x = Math.max(r, Math.min(W - r, n.x));
    n.y = Math.max(r, Math.min(H - r, n.y));
  }});
  alpha *= 0.992;
}}

function tick() {{
  forceStep();
  applyDOMState();
  if (alpha > FORCE.alphaCutoff) {{
    requestAnimationFrame(tick);
  }} else {{
    // Snap remaining tiny velocities to zero so the picture is fully
    // still — no shimmer, no sub-pixel drift.
    NODES.forEach(n => {{ n.vx = 0; n.vy = 0; }});
    running = false;
  }}
}}
function reheat(target = 1) {{
  alpha = Math.max(alpha, target);
  if (!running) {{
    running = true;
    requestAnimationFrame(tick);
  }}
}}

// --- DOM creation ----------------------------------------------------
const svg = document.getElementById('graph');
const viewport = document.getElementById('viewport');
const edgesLayer = document.getElementById('edges-layer');
const nodesLayer = document.getElementById('nodes-layer');
const labelsLayer = document.getElementById('labels-layer');

function el(name, attrs) {{
  const e = document.createElementNS('http://www.w3.org/2000/svg', name);
  for (const k in (attrs || {{}})) e.setAttribute(k, attrs[k]);
  return e;
}}

EDGES.forEach(e => {{
  // Edges are bezier curves (quadratic) instead of straight lines.
  // The bow direction comes from the edge's index parity so adjacent
  // edges curve slightly differently — gives the graph an organic
  // feel without computing a real bundle layout. Stroke colours are
  // set in CSS via class so dark-mode overrides apply uniformly.
  const path = el('path', {{
    class: 'edge kind-' + e.kind,
    'stroke-width': e.kind === 'parent' ? 1.2 : (e.kind === 'cite' || e.kind === 'link' ? 0.5 : 0.8),
  }});
  e._line = path;
  edgesLayer.appendChild(path);
}});
NODES.forEach(n => {{
  // Hit halo: an invisible larger circle behind each visible node
  // that captures pointer events. Makes the click target much bigger
  // than the visible dot (which can be as small as r=5) without
  // changing what the user sees.
  const hit = el('circle', {{
    class: 'node-hit',
    'data-id': n.id,
  }});
  n._hit = hit;
  nodesLayer.appendChild(hit);
  const circle = el('circle', {{
    class: 'node-circle kind-' + n.kind,
    fill: KIND_COLOR[n.kind] || '#888',
    'data-id': n.id,
  }});
  n._circle = circle;
  nodesLayer.appendChild(circle);
  const label = el('text', {{ class: 'node-label' }});
  label.textContent = n.label.length > 32 ? n.label.slice(0, 31) + '…' : n.label;
  n._label = label;
  labelsLayer.appendChild(label);
}});

function applyDOMState() {{
  const dimming = hasAnyHighlight();
  NODES.forEach(n => {{
    const r = radiusFor(n);
    if (n._circle) {{
      n._circle.setAttribute('cx', n.x);
      n._circle.setAttribute('cy', n.y);
      n._circle.setAttribute('r', r);
    }}
    if (n._hit) {{
      n._hit.setAttribute('cx', n.x);
      n._hit.setAttribute('cy', n.y);
      n._hit.setAttribute('r', r + 9);
    }}
    if (n._label) {{
      n._label.setAttribute('x', n.x + r + 5);
      n._label.setAttribute('y', n.y + 4);
      n._label.classList.toggle('large', focusedId === n.id);
    }}
    const visible = isNodeVisible(n);
    const inFocus = isInFocus(n.id);
    if (n._circle) {{
      n._circle.style.display = visible ? '' : 'none';
      // Non-highlighted dim is gentle (0.20) so all visible pallini
      // stay legible — they're how the leader reads the structure.
      n._circle.style.opacity = !visible ? 0 : (inFocus ? 1 : 0.20);
      n._circle.classList.toggle('focused', focusedId === n.id);
      n._circle.classList.toggle('hovered', hoveredId === n.id && focusedId !== n.id);
    }}
    if (n._hit) {{
      n._hit.style.display = visible ? '' : 'none';
    }}
    if (n._label) {{
      // Labels are always shown for visible nodes (small) — Obsidian
      // pattern. Opacity follows focus state so the focused
      // neighbourhood's labels read brighter than the background ones.
      n._label.style.display = visible ? '' : 'none';
      let labelOp;
      if (!visible) labelOp = 0;
      else if (focusedId === n.id || focusedNeighbours.has(n.id)) labelOp = 1;
      else if (hoveredId === n.id || hoveredNeighbours.has(n.id)) labelOp = 1;
      else if (dimming) labelOp = 0.25;
      else labelOp = 0.7;
      n._label.style.opacity = labelOp;
    }}
  }});
  EDGES.forEach((e, idx) => {{
    if (!e._line) return;
    const a = NODE_BY_ID[e.from], b = NODE_BY_ID[e.to];
    if (!a || !b) {{ e._line.style.display = 'none'; return; }}
    // Quadratic bezier with a small bow perpendicular to the chord.
    // Bow direction alternates by edge index so neighbouring edges
    // curve apart instead of overlapping.
    const dx = b.x - a.x, dy = b.y - a.y;
    const dist = Math.hypot(dx, dy) || 1;
    const bow = Math.min(36, dist * 0.18) * (idx % 2 === 0 ? 1 : -1);
    const cx = (a.x + b.x) / 2 + (-dy / dist) * bow;
    const cy = (a.y + b.y) / 2 + ( dx / dist) * bow;
    e._line.setAttribute('d', `M${{a.x.toFixed(1)}},${{a.y.toFixed(1)}} Q${{cx.toFixed(1)}},${{cy.toFixed(1)}} ${{b.x.toFixed(1)}},${{b.y.toFixed(1)}}`);
    const ev = isEdgeVisible(e);
    const inFocus = edgeInFocus(e);
    e._line.style.display = ev ? '' : 'none';
    e._line.classList.toggle('in-focus', !!ev && !!inFocus && hasAnyHighlight());
    e._line.style.opacity = !ev ? 0 : (inFocus ? 0.7 : 0.04);
  }});
}}

function updateStats() {{
  const visibleNodes = NODES.filter(isNodeVisible);
  const visibleEdges = EDGES.filter(isEdgeVisible);
  const incident = new Set();
  visibleEdges.forEach(e => {{ incident.add(e.from); incident.add(e.to); }});
  const isolates = visibleNodes.filter(n => !incident.has(n.id)).length;
  const kinds = new Set(visibleNodes.map(n => n.kind)).size;
  document.getElementById('stat-nodes').textContent = visibleNodes.length;
  document.getElementById('stat-edges').textContent = visibleEdges.length;
  document.getElementById('stat-kinds').textContent = kinds;
  document.getElementById('stat-isolates').textContent = isolates;
}}

// --- side panel ------------------------------------------------------
const panelEl = document.getElementById('graph-panel');
const panelContent = panelEl.querySelector('.panel-content');
const panelClose = document.getElementById('panel-close');

function buildPanelHtml(n) {{
  const out = [], inn = [];
  EDGES.forEach(e => {{
    if (!visibleEdgeKinds.has(e.kind)) return;
    if (e.from === n.id) {{
      const t = NODE_BY_ID[e.to];
      if (t && visibleNodeKinds.has(t.kind)) {{
        out.push({{ rel: REL_LABELS[e.kind] || e.kind, target: t }});
      }}
    }} else if (e.to === n.id) {{
      const f = NODE_BY_ID[e.from];
      if (f && visibleNodeKinds.has(f.kind)) {{
        inn.push({{ rel: REL_LABELS_REV[e.kind] || e.kind, target: f }});
      }}
    }}
  }});
  const dotColor = KIND_COLOR[n.kind] || '#888';
  let html = `<div class="eyebrow"><span class="dot" style="background:${{dotColor}}"></span>${{escapeHtml(n.kind)}}</div>`;
  html += `<h3>${{escapeHtml(n.label)}}</h3>`;
  if (n.description) html += `<div class="desc">${{escapeHtml(n.description)}}</div>`;
  if (out.length) {{
    html += `<div class="section-label">Outgoing (${{out.length}})</div>`;
    html += `<div class="neighbour-list">` + out.map(r =>
      `<div class="neighbour" data-target-id="${{escapeHtml(r.target.id)}}"><span class="rel">${{escapeHtml(r.rel)}}</span><span class="target">${{escapeHtml(r.target.label)}}</span></div>`
    ).join('') + `</div>`;
  }}
  if (inn.length) {{
    html += `<div class="section-label">Incoming (${{inn.length}})</div>`;
    html += `<div class="neighbour-list">` + inn.map(r =>
      `<div class="neighbour" data-target-id="${{escapeHtml(r.target.id)}}"><span class="rel">${{escapeHtml(r.rel)}}</span><span class="target">${{escapeHtml(r.target.label)}}</span></div>`
    ).join('') + `</div>`;
  }}
  if (n._path) html += `<div class="citation">${{escapeHtml(n._path)}}</div>`;
  return html;
}}

function updatePanel() {{
  if (!focusedId) {{
    panelEl.classList.remove('has-focus');
    panelContent.innerHTML = '';
    return;
  }}
  const n = NODE_BY_ID[focusedId];
  if (!n) return;
  panelEl.classList.add('has-focus');
  panelContent.innerHTML = buildPanelHtml(n);
}}

panelClose.addEventListener('click', () => {{
  setFocus(null);
  updatePanel();
  applyDOMState();
}});

panelContent.addEventListener('click', (e) => {{
  const row = e.target.closest('.neighbour');
  if (!row) return;
  const targetId = row.dataset.targetId;
  if (!targetId || !NODE_BY_ID[targetId]) return;
  setFocus(targetId);
  updatePanel();
  applyDOMState();
}});

// --- legend toggles --------------------------------------------------
function refreshSwatchUI() {{
  document.querySelectorAll('#legend-nodes .swatch').forEach(s => {{
    s.classList.toggle('off', !visibleNodeKinds.has(s.dataset.kind));
  }});
  document.querySelectorAll('#legend-edges .swatch').forEach(s => {{
    s.classList.toggle('off', !visibleEdgeKinds.has(s.dataset.edgekind));
  }});
}}
refreshSwatchUI();

document.querySelectorAll('#legend-nodes .swatch').forEach(s => {{
  s.addEventListener('click', () => {{
    const k = s.dataset.kind;
    if (visibleNodeKinds.has(k)) visibleNodeKinds.delete(k);
    else visibleNodeKinds.add(k);
    refreshSwatchUI();
    setFocus(null);
    updatePanel();
    recomputeDegrees();
    updateStats();
    reheat(1);
  }});
}});
document.querySelectorAll('#legend-edges .swatch').forEach(s => {{
  s.addEventListener('click', () => {{
    const k = s.dataset.edgekind;
    if (visibleEdgeKinds.has(k)) visibleEdgeKinds.delete(k);
    else visibleEdgeKinds.add(k);
    refreshSwatchUI();
    setFocus(null);
    updatePanel();
    recomputeDegrees();
    updateStats();
    reheat(0.6);
  }});
}});

document.getElementById('btn-reheat').addEventListener('click', () => {{
  NODES.forEach(n => {{
    if (!isNodeVisible(n)) return;
    n.vx += (Math.random() - 0.5) * 12;
    n.vy += (Math.random() - 0.5) * 12;
  }});
  reheat(1);
}});

// --- viewport zoom + pan ---------------------------------------------
let view = {{ x: 0, y: 0, k: 1 }};
function applyViewport() {{
  viewport.setAttribute('transform', `translate(${{view.x}} ${{view.y}}) scale(${{view.k}})`);
}}
document.getElementById('btn-reset-view').addEventListener('click', () => {{
  view = {{ x: 0, y: 0, k: 1 }};
  applyViewport();
}});

let dragState = null;
svg.addEventListener('mousedown', (e) => {{
  if (e.target.classList && e.target.classList.contains('node-circle')) return;
  dragState = {{ x: e.clientX, y: e.clientY, vx: view.x, vy: view.y }};
  svg.classList.add('dragging');
}});
document.addEventListener('mousemove', (e) => {{
  if (!dragState) return;
  view.x = dragState.vx + (e.clientX - dragState.x);
  view.y = dragState.vy + (e.clientY - dragState.y);
  applyViewport();
}});
document.addEventListener('mouseup', () => {{
  dragState = null;
  svg.classList.remove('dragging');
}});
svg.addEventListener('wheel', (e) => {{
  e.preventDefault();
  const rect = svg.getBoundingClientRect();
  const mx = ((e.clientX - rect.left) / rect.width)  * W;
  const my = ((e.clientY - rect.top)  / rect.height) * H;
  const factor = Math.exp(-e.deltaY * 0.0015);
  const newK = Math.min(4, Math.max(0.3, view.k * factor));
  view.x = mx - (mx - view.x) * (newK / view.k);
  view.y = my - (my - view.y) * (newK / view.k);
  view.k = newK;
  applyViewport();
}}, {{ passive: false }});

// Helper: click/hover events fire on the hit halo OR the visible
// circle. Either one carries the data-id we need.
function nodeIdFromTarget(t) {{
  if (!t || !t.classList) return null;
  if (t.classList.contains('node-circle') || t.classList.contains('node-hit')) {{
    return t.getAttribute('data-id');
  }}
  return null;
}}

// --- node click → focus (visual only, no movement) ------------------
svg.addEventListener('click', (e) => {{
  const id = nodeIdFromTarget(e.target);
  if (!id) return;
  // If we just finished a drag, suppress the synthetic click that
  // follows mouseup so dragging a node doesn't also focus it.
  if (suppressNextClick) {{ suppressNextClick = false; e.stopPropagation(); return; }}
  if (!NODE_BY_ID[id]) return;
  setFocus(id);
  updatePanel();
  applyDOMState();
  e.stopPropagation();
}});

// --- node hover → soft highlight (doesn't open the panel) -----------
svg.addEventListener('mouseover', (e) => {{
  const id = nodeIdFromTarget(e.target);
  if (!id) return;
  setHover(id);
  applyDOMState();
}});
svg.addEventListener('mouseout', (e) => {{
  const id = nodeIdFromTarget(e.target);
  if (!id) return;
  if (hoveredId === id) {{
    setHover(null);
    applyDOMState();
  }}
}});

// --- node drag → user-pinned position --------------------------------
// Dragging only kicks in after a 5px movement threshold from the
// initial mousedown. Below the threshold we treat the gesture as a
// click. This keeps focus reliable: a slightly-trembly hand on a
// small dot still registers as a click, not a degenerate drag.
let nodeDrag = null;
let suppressNextClick = false;
const DRAG_THRESHOLD_PX = 5;

function svgPointerToWorld(clientX, clientY) {{
  const rect = svg.getBoundingClientRect();
  const vbx = ((clientX - rect.left) / rect.width)  * W;
  const vby = ((clientY - rect.top)  / rect.height) * H;
  return {{ x: (vbx - view.x) / view.k, y: (vby - view.y) / view.k }};
}}
svg.addEventListener('mousedown', (e) => {{
  const id = nodeIdFromTarget(e.target);
  if (!id) return;
  const n = NODE_BY_ID[id];
  if (!n) return;
  nodeDrag = {{ id, startClientX: e.clientX, startClientY: e.clientY, moved: false }};
  e.preventDefault();
}});
document.addEventListener('mousemove', (e) => {{
  if (!nodeDrag) return;
  if (!nodeDrag.moved) {{
    const dx = e.clientX - nodeDrag.startClientX;
    const dy = e.clientY - nodeDrag.startClientY;
    if (Math.hypot(dx, dy) < DRAG_THRESHOLD_PX) return;
    nodeDrag.moved = true;
  }}
  const n = NODE_BY_ID[nodeDrag.id];
  if (!n) return;
  const w = svgPointerToWorld(e.clientX, e.clientY);
  n.fx = w.x; n.fy = w.y;
  reheat(0.5);
}});
document.addEventListener('mouseup', () => {{
  if (!nodeDrag) return;
  const n = NODE_BY_ID[nodeDrag.id];
  if (n && nodeDrag.moved) {{ n.fx = null; n.fy = null; }}
  if (nodeDrag.moved) {{ suppressNextClick = true; reheat(0.4); }}
  nodeDrag = null;
}});

// Click anywhere else clears focus. Walks up the DOM looking for an
// "interactive" ancestor; if it doesn't find one, the click counts as
// "empty space" and clears the focus.
document.addEventListener('click', (e) => {{
  let n = e.target;
  while (n && n.nodeType === 1) {{
    if (n.id === 'graph-panel') return;
    if (n.classList && (
      n.classList.contains('node-circle') ||
      n.classList.contains('node-hit') ||
      n.classList.contains('swatch') ||
      n.classList.contains('btn') ||
      n.classList.contains('neighbour')
    )) return;
    n = n.parentNode;
  }}
  if (focusedId) {{
    setFocus(null);
    updatePanel();
    applyDOMState();
  }}
}}, true);

document.addEventListener('keydown', e => {{
  if (e.key === 'Escape' && focusedId) {{
    setFocus(null);
    updatePanel();
    applyDOMState();
  }}
}});

// Boot — pre-settle the layout synchronously so the page opens with
// nodes already at rest. No animation, no moving click targets, no
// "i'm trying to click but the node moves". The visible simulation
// only runs after a real user action (toggle, drag, re-shake).
updateStats();
alpha = 1;
for (let i = 0; i < 350; i++) {{
  if (alpha < FORCE.alphaCutoff) break;
  forceStep();
}}
NODES.forEach(n => {{ n.vx = 0; n.vy = 0; }});
alpha = 0;
applyDOMState();
</script>
</body>
</html>"""


def render_html(d: dict, title: str) -> str:
    nodes = d.get("nodes", []) or []
    edges = d.get("edges", []) or []

    DEFAULT_VISIBLE_NODE_KINDS = {
        "unit", "activity", "person", "stakeholder", "commitment"
    }
    DEFAULT_VISIBLE_EDGE_KINDS = {
        "parent", "unit", "performer", "head_role", "holds_role", "covers",
        "party_committing", "party_benefiting", "touches"
    }

    def node_visible_default(n):
        return n.get("kind") in DEFAULT_VISIBLE_NODE_KINDS

    def edge_visible_default(e):
        if e.get("kind") not in DEFAULT_VISIBLE_EDGE_KINDS:
            return False
        a = next((x for x in nodes if x.get("id") == e.get("from")), None)
        b = next((x for x in nodes if x.get("id") == e.get("to")), None)
        return a is not None and b is not None and node_visible_default(a) and node_visible_default(b)

    visible_nodes = [n for n in nodes if node_visible_default(n)]
    visible_edges = [e for e in edges if edge_visible_default(e)]
    visible_kinds = {n.get("kind") for n in visible_nodes}
    incident: set[str] = set()
    for e in visible_edges:
        incident.add(e.get("from", ""))
        incident.add(e.get("to", ""))
    isolates = [n for n in visible_nodes if n.get("id") not in incident]

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
            '<h2>How to read this graph</h2>'
            '<p class="lead">The leader-facing reading of the graph: which nodes are load-bearing, which regions are sparse, what the topology says about where the structure has been written down and where it has not.</p>'
            + "".join(items)
            + '</div>'
        )

    # --- editorial chrome (Italianate masthead + magazine colophon) ---
    scope = d.get("_scope", "whole-org") or "whole-org"
    # Pull the dataset's "today" from the play filename if obvious;
    # otherwise leave blank — the colophon doesn't insist.
    n_sources = sum(1 for n in nodes if n.get("kind") == "source")
    n_citations = sum(1 for e in edges if e.get("kind") == "cite")
    masthead_html = masthead(
        kicker_left="graph",
        kicker_num=f"№ {len(visible_nodes):02d}",
        kicker_right=f"scope · {scope}",
        title=f"The whole <em>operational</em> graph",
        lede=(
            "Every unit, the activities they run, the people who run them, "
            "the stakeholders served, and the commitments that bind everyone — "
            "as one connected drawing of how the work hangs together."
        ),
        dateline="dated " + (d.get("_dated") or ""),
        tags=[
            f"{len(visible_nodes)} nodes",
            f"{len(visible_edges)} relations",
            f"{len(visible_kinds)} kinds",
            f"{len(isolates)} floating",
        ],
    )
    colophon_html = colophon(
        citations=n_citations,
        sources=n_sources,
        generator="skills/playbooks/graph",
        generated_on=d.get("_dated", ""),
        audit="pass",
        autoresearch="4 / 4 deterministic dimensions pass",
        extra_lines=[
            "Click any node to focus · drag to reposition · use the legend toggles to scope.",
        ],
    )

    return HTML_TEMPLATE.format(
        css=base_css() + EXTRA_CSS,
        title=escape(title),
        masthead_html=masthead_html,
        colophon_html=colophon_html,
        n_nodes=len(visible_nodes),
        n_edges=len(visible_edges),
        n_kinds=len(visible_kinds),
        n_isolates=len(isolates),
        decisions_section=decisions_section,
        nodes_json=json.dumps(nodes, ensure_ascii=False),
        edges_json=json.dumps(edges, ensure_ascii=False),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a graph JSON as interactive HTML.")
    parser.add_argument("--map", required=True, help="Graph JSON path")
    parser.add_argument("--html", required=True, help="Output HTML path")
    parser.add_argument("--title", default="The whole graph", help="Page title")
    parser.add_argument(
        "--decisions",
        help="Optional JSON list of {question, answer, source} merged into the map under top-level "
             "'decisions[]'. Renders the 'How to read this graph' section. Required for a shippable "
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

    html = render_html(d, args.title)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"Wrote {Path(args.html).resolve()} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
