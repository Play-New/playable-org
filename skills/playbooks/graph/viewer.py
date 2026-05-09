#!/usr/bin/env python3
"""
graph / viewer.py — Render the org graph as a focus-aware,
filter-aware, force-directed visualization with the same Play New
chrome as the other four playbooks.

Design after first round of feedback ("fa schifo"):

- **The graph is the operational org, not the corpus.** Sources and
  identity nodes are corpus / declarative metadata, not part of how
  the organization actually works. Hidden by default. Cite + link
  edges (which only touch source/identity meaningfully) idem.
  Toggleable from the legend if the user wants the full picture.

- **Click-to-focus.** Clicking a node dims everything that isn't the
  node or its first-degree neighbours. Click empty space (or Esc) to
  clear. This is the affordance that makes graphs at AIRC-scale
  (hundreds of nodes) navigable instead of decorative.

- **Toggles re-layout.** Hiding a kind from the legend removes those
  nodes from the simulation entirely (not just dims them) so the
  remaining graph repacks the freed space. Reheats the simulation on
  every toggle.

- **Stronger spread.** Repulsion 5x the previous default, ideal edge
  length 110 (was 60), centring 3x weaker. The previous params
  collapsed everything around the cited-source hubs; that hub
  structure was a visual artefact of citation density, not real.

- **Continuous simulation.** Cooling schedule via requestAnimationFrame
  with reheat-on-interaction. The graph "settles" in front of the
  user instead of arriving pre-rendered.

- **Zoom / pan.** Wheel zoom + drag pan. Essential for >50 nodes.

- **Bigger size delta.** Log-scale: degree 1 → r≈6, degree 24 → r≈18.
  The cardinal nodes read as cardinal at a glance.

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
from design import base_css  # noqa: E402


EXTRA_CSS = """
/* graph viewer — Play New design (unified with the other four playbooks).
   The graph canvas is the cardinal block on the page; everything around
   it is centered editorial chrome at 820px. */

:root {
  /* Node colours by kind — pulled from the project's data-viz palette
     so brand and viz stay in sync. */
  --kind-identity:           var(--ds-coral);    /* mission / limits / rules */
  --kind-language-term:      var(--fg-light);    /* glossary entries */
  --kind-unit:               var(--ds-slate);    /* areas / divisions */
  --kind-activity:           var(--ds-sage);     /* what the org does */
  --kind-person:             var(--fg);          /* named people */
  --kind-role:               var(--fg-muted);    /* position types */
  --kind-stakeholder:        var(--ds-lilac);    /* the people the org serves */
  --kind-commitment:         var(--ds-coral);    /* promises that bind parties */
  --kind-financial-summary:  var(--ds-sand);     /* the books */
  --kind-source:             var(--fg-light);    /* documents that anchor everything */
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

/* Stat strip — small, centered under the intro. */
.stats-strip { max-width: 820px; margin: 0 auto 32px; display: flex; flex-wrap: wrap; gap: 24px; padding: 16px 0; border-top: 1px solid var(--fg-hairline); border-bottom: 1px solid var(--fg-hairline); }
.stats-strip .stat { display: flex; flex-direction: column; gap: 4px; }
.stats-strip .stat .num { font-family: var(--font-display); font-size: 1.4rem; font-weight: 500; letter-spacing: -0.02em; color: var(--fg); font-variant-numeric: tabular-nums; }
.stats-strip .stat .lab { font-family: var(--font-display); font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); }

/* Legend — two rows: nodes on top, relations under. Both rows are
   live filters, not just dimmers. Toggling a kind removes those
   nodes (or edges) from the simulation entirely so the remaining
   graph repacks. */
.legend { max-width: 1160px; margin: 0 auto 14px; display: flex; flex-direction: column; gap: 8px; padding: 12px 14px; border: 1px solid var(--fg-hairline); border-radius: 6px; background: var(--bg-alt); }
.legend .row { display: flex; flex-wrap: wrap; gap: 14px 18px; align-items: center; font-size: 0.78rem; color: var(--fg-muted); }
.legend .label { font-family: var(--font-display); font-size: 0.66rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); min-width: 78px; }
.legend .swatch { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; transition: color 0.15s, opacity 0.15s; user-select: none; }
.legend .swatch:hover { color: var(--fg); }
.legend .swatch.off { opacity: 0.32; text-decoration: line-through; text-decoration-thickness: 1px; }
.legend .swatch .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.legend .swatch .line { display: inline-block; width: 18px; height: 2px; }
.legend .actions { margin-left: auto; display: flex; gap: 10px; align-items: center; }
.legend .btn { background: transparent; border: 1px solid var(--fg-hairline); color: var(--fg-muted); font-size: 0.74rem; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-family: inherit; transition: border-color 0.15s, color 0.15s; }
.legend .btn:hover { border-color: var(--fg); color: var(--fg); }
.legend .hint { font-size: 0.74rem; color: var(--fg-light); }

/* Canvas — full editorial column width, taller than the other viewers
   because this is the cardinal block of the page. */
.graph-shell { max-width: 1160px; margin: 0 auto; border: 1px solid var(--fg-hairline); border-radius: 6px; background: #FFFFFF; overflow: hidden; position: relative; }
.graph-shell svg { display: block; width: 100%; height: 720px; cursor: grab; }
.graph-shell svg.dragging { cursor: grabbing; }
.graph-shell svg .edge { fill: none; }
.graph-shell svg .node-circle { stroke: rgba(0,0,0,0.32); stroke-width: 0.8; cursor: pointer; transition: stroke-width 0.12s; }
.graph-shell svg .node-circle:hover { stroke: var(--fg); stroke-width: 2; }
.graph-shell svg .node-circle.focused { stroke: var(--fg); stroke-width: 2.5; }
.graph-shell svg .node-label { font-family: var(--font-display); font-size: 11px; fill: var(--fg-muted); pointer-events: none; }
.graph-shell svg .node-label.large { font-size: 13px; fill: var(--fg); font-weight: 500; }

/* Decisions section — centered editorial column, identical to the other playbooks. */
.section { max-width: 820px; margin: 96px auto 0; padding-top: 40px; border-top: 1px solid var(--fg-hairline); }
.section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 20px; }
.section p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; max-width: 720px; }
.section .lead { font-size: 0.95rem; color: var(--fg-muted); line-height: 1.65; max-width: 720px; margin: 0 0 28px; }

.decision { margin-bottom: 32px; }
.decision .question { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; color: var(--fg); margin: 0 0 8px; letter-spacing: -0.01em; }
.decision .answer { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 6px; max-width: 720px; }
.decision .source { font-size: 0.78rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }

/* Popover — same pattern as the other playbooks. */
.popover { position: absolute; display: none; max-width: 380px; min-width: 240px; padding: 14px 18px 16px; background: #FFFFFF; border: 1px solid var(--fg-hairline); border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); z-index: 100; animation: pn-pop 0.18s ease; }
.popover.open { display: block; }
.popover .close { position: absolute; top: 6px; right: 8px; background: transparent; border: 0; cursor: pointer; font-size: 1.1rem; color: var(--fg-muted); padding: 0; line-height: 1; }
.popover .close:hover { color: var(--fg); }
.popover .eyebrow { font-family: var(--font-display); font-size: 0.62rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px; color: var(--fg-muted); }
.popover h3 { font-family: var(--font-display); font-size: 1.0rem; font-weight: 500; letter-spacing: -0.015em; margin: 0 0 8px; line-height: 1.25; color: var(--fg); padding-right: 18px; }
.popover .desc { font-size: 0.85rem; line-height: 1.55; color: var(--fg); margin: 0 0 10px; }
.popover .section-label { font-family: var(--font-display); font-size: 0.62rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; font-weight: 500; margin-top: 12px; margin-bottom: 4px; }
.popover .neighbour-list { display: flex; flex-direction: column; gap: 4px; font-size: 0.8rem; color: var(--fg); }
.popover .neighbour-list .row { display: flex; gap: 8px; align-items: baseline; }
.popover .neighbour-list .row .rel { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.7rem; color: var(--fg-muted); min-width: 100px; }
.popover .citation { font-size: 0.7rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; padding-top: 8px; margin-top: 10px; border-top: 1px solid var(--fg-hairline); }
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
    <header>
      <div class="eyebrow">graph</div>
      <h1>{title}</h1>
      <p class="lead">The organization as a single graph of how the work hangs together — units, the activities they run, the people who run them, the stakeholders served, the promises that bind everyone.</p>
    </header>

    <div class="intro">
      <p>What you see is the operational core of the organization: <strong>units</strong>, the <strong>activities</strong> they run, the <strong>people</strong> who run them, the <strong>stakeholders</strong> served, and the <strong>commitments</strong> that bind everyone. The size of a circle reflects how connected that node is — bigger circles are where the org's weight insists.</p>
      <p>Hidden by default: the corpus metadata (sources, citations) and the declarative / taxonomic kinds (identity, language, roles, financial summaries). They distort the spatial picture or duplicate what other kinds already say. Toggle them back from the legend if you want a fuller reading.</p>
      <p><strong>Click any circle</strong> to focus on it. The clicked node and its first-degree neighbours stay in colour; everything else dims. Click empty space to clear the focus.</p>
      <p><strong>Toggle a kind on or off</strong> from the legend. Hiding a kind removes those nodes from the simulation, and the rest of the graph repacks the freed space.</p>
      <p><strong>Wheel to zoom, drag to pan.</strong> Useful at large org sizes.</p>
      <div class="pull">A connected, dense graph means the structure is internally consistent: activities sit in units, commitments name parties on both sides, stakeholders are touched by the work the org actually does. Sparse regions and floating nodes point at the places where the structure has not been written down yet.</div>
    </div>

    <section class="stats-strip">
      <div class="stat"><div class="num" id="stat-nodes">{n_nodes}</div><div class="lab">nodes shown</div></div>
      <div class="stat"><div class="num" id="stat-edges">{n_edges}</div><div class="lab">relations shown</div></div>
      <div class="stat"><div class="num" id="stat-kinds">{n_kinds}</div><div class="lab">node kinds</div></div>
      <div class="stat"><div class="num" id="stat-isolates">{n_isolates}</div><div class="lab">floating nodes</div></div>
    </section>

    <div class="legend" id="legend">
      <div class="row" id="legend-nodes">
        <span class="label">Show nodes</span>
        <span class="swatch" data-kind="unit"><span class="dot" style="background: var(--kind-unit)"></span>unit</span>
        <span class="swatch" data-kind="activity"><span class="dot" style="background: var(--kind-activity)"></span>activity</span>
        <span class="swatch" data-kind="commitment"><span class="dot" style="background: var(--kind-commitment); border: 1px solid var(--ds-coral)"></span>commitment</span>
        <span class="swatch" data-kind="stakeholder"><span class="dot" style="background: var(--kind-stakeholder)"></span>stakeholder</span>
        <span class="swatch" data-kind="person"><span class="dot" style="background: var(--kind-person)"></span>person</span>
        <span class="swatch off" data-kind="role"><span class="dot" style="background: var(--kind-role)"></span>role</span>
        <span class="swatch off" data-kind="financial-summary"><span class="dot" style="background: var(--kind-financial-summary)"></span>financial</span>
        <span class="swatch off" data-kind="identity"><span class="dot" style="background: var(--kind-identity)"></span>identity</span>
        <span class="swatch off" data-kind="language-term"><span class="dot" style="background: var(--kind-language-term)"></span>language</span>
        <span class="swatch off" data-kind="source"><span class="dot" style="background: var(--kind-source)"></span>source</span>
      </div>
      <div class="row" id="legend-edges">
        <span class="label">Show relations</span>
        <span class="swatch" data-edgekind="parent"><span class="line" style="background: var(--fg)"></span>part of</span>
        <span class="swatch" data-edgekind="unit"><span class="line" style="background: rgba(0,0,0,0.55)"></span>sits in</span>
        <span class="swatch" data-edgekind="performer"><span class="line" style="background: rgba(0,0,0,0.55)"></span>performed by</span>
        <span class="swatch" data-edgekind="party_committing"><span class="line" style="background: rgba(0,0,0,0.55)"></span>commits</span>
        <span class="swatch" data-edgekind="party_benefiting"><span class="line" style="background: rgba(0,0,0,0.55)"></span>benefits</span>
        <span class="swatch" data-edgekind="touches"><span class="line" style="background: rgba(0,0,0,0.55)"></span>touches</span>
        <span class="swatch" data-edgekind="head_role"><span class="line" style="background: rgba(0,0,0,0.55)"></span>led by</span>
        <span class="swatch" data-edgekind="holds_role"><span class="line" style="background: rgba(0,0,0,0.55)"></span>holds role</span>
        <span class="swatch" data-edgekind="covers"><span class="line" style="background: rgba(0,0,0,0.55)"></span>covers</span>
        <span class="swatch off" data-edgekind="link"><span class="line" style="background: rgba(0,0,0,0.4); height: 1px;"></span>mentions</span>
        <span class="swatch off" data-edgekind="cite"><span class="line" style="background: rgba(0,0,0,0.4); height: 1px; border-top: 1px dashed rgba(0,0,0,0.4); background: transparent;"></span>cites</span>
        <span class="actions">
          <button class="btn" id="btn-reheat">re-shake</button>
          <button class="btn" id="btn-reset-view">reset view</button>
        </span>
      </div>
      <div class="row">
        <span class="hint">click a node to focus on its neighbourhood · click empty space to clear · wheel to zoom, drag to pan</span>
      </div>
    </div>

    <div class="graph-shell">
      <svg id="graph" viewBox="0 0 1160 720" preserveAspectRatio="xMidYMid meet">
        <g id="viewport">
          <g id="edges-layer"></g>
          <g id="nodes-layer"></g>
          <g id="labels-layer"></g>
        </g>
      </svg>
    </div>

    {decisions_section}
  </div>

  <div class="popover" id="popover">
    <button class="close" id="popover-close" aria-label="Close">×</button>
    <div id="popover-body"></div>
  </div>

<script>
const NODES = {nodes_json};
const EDGES = {edges_json};

const KIND_COLOR = {{
  'identity':           getComputedStyle(document.documentElement).getPropertyValue('--kind-identity').trim(),
  'language-term':      getComputedStyle(document.documentElement).getPropertyValue('--kind-language-term').trim(),
  'unit':               getComputedStyle(document.documentElement).getPropertyValue('--kind-unit').trim(),
  'activity':           getComputedStyle(document.documentElement).getPropertyValue('--kind-activity').trim(),
  'person':             getComputedStyle(document.documentElement).getPropertyValue('--kind-person').trim(),
  'role':               getComputedStyle(document.documentElement).getPropertyValue('--kind-role').trim(),
  'stakeholder':        getComputedStyle(document.documentElement).getPropertyValue('--kind-stakeholder').trim(),
  'commitment':         getComputedStyle(document.documentElement).getPropertyValue('--kind-commitment').trim(),
  'financial-summary':  getComputedStyle(document.documentElement).getPropertyValue('--kind-financial-summary').trim(),
  'source':             getComputedStyle(document.documentElement).getPropertyValue('--kind-source').trim(),
}};

const REL_LABELS = {{
  'parent':           'is part of',
  'unit':             'sits in',
  'performer':        'performed by',
  'head_role':        'led by',
  'holds_role':       'holds role',
  'covers':           'covers',
  'party_committing': 'commits',
  'party_benefiting': 'benefits',
  'touches':          'touches',
  'cite':             'cites',
  'link':             'mentions',
}};
const REL_LABELS_REV = {{
  'parent':           'contains',
  'unit':             'hosts',
  'performer':        'performs',
  'head_role':        'leads',
  'holds_role':       'held by',
  'covers':           'covered by',
  'party_committing': 'committed by',
  'party_benefiting': 'benefits from',
  'touches':          'touched by',
  'cite':             'cited by',
  'link':             'mentioned by',
}};

// --- defaults: what you see when you open the page -------------------
// The five operational kinds (unit / activity / commitment / stakeholder
// / person) are what shows where the org actually insists. The other
// kinds (identity, language, role, financial-summary, source) are
// corpus / declarative / taxonomic metadata — togglable from the
// legend if you want a fuller picture.
const DEFAULT_VISIBLE_NODES = new Set(['unit','activity','person','stakeholder','commitment']);
const DEFAULT_VISIBLE_EDGES = new Set(['parent','unit','performer','party_committing','party_benefiting','touches','head_role','holds_role','covers']);

const visibleNodeKinds = new Set(DEFAULT_VISIBLE_NODES);
const visibleEdgeKinds = new Set(DEFAULT_VISIBLE_EDGES);

// --- force config ----------------------------------------------------
const FORCE = {{
  k: 110,             // ideal edge length
  repulse: 5000,      // node-node repulsion
  centering: 0.0015,  // pull toward viewport centre
  damping: 0.82,
  // structural relations pull harder; bibliographic ones pull weakly
  // so that, when toggled on, they don't dominate the spatial logic.
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
}};

const W = 1160, H = 720;
const NODE_BY_ID = Object.fromEntries(NODES.map(n => [n.id, n]));

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }})[c]);
}}

// Pre-compute degree per node — used for the radius scale and for
// labelling the load-bearing nodes. Degree is recomputed when filters
// change so the size delta tracks what's currently shown.
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
  // Log-scale: degree 0 → 5, degree 1 → ~7, degree 5 → ~12, degree 24 → ~18.
  // Bigger delta than the previous sqrt scale; the cardinal nodes
  // read as cardinal at a glance.
  return 5 + Math.log(1 + (n._degree || 0)) * 4;
}}

function isNodeVisible(n) {{
  return visibleNodeKinds.has(n.kind);
}}
function isEdgeVisible(e) {{
  if (!visibleEdgeKinds.has(e.kind)) return false;
  const a = NODE_BY_ID[e.from], b = NODE_BY_ID[e.to];
  return !!(a && b && isNodeVisible(a) && isNodeVisible(b));
}}

// --- focus state -----------------------------------------------------
let focusedId = null;
let focusedNeighbours = new Set();

function setFocus(id) {{
  focusedId = id;
  focusedNeighbours.clear();
  if (id) {{
    EDGES.forEach(e => {{
      if (!isEdgeVisible(e)) return;
      if (e.from === id) focusedNeighbours.add(e.to);
      if (e.to === id) focusedNeighbours.add(e.from);
    }});
  }}
}}

function isInFocus(nodeId) {{
  if (!focusedId) return true;
  return nodeId === focusedId || focusedNeighbours.has(nodeId);
}}
function edgeInFocus(e) {{
  if (!focusedId) return true;
  return e.from === focusedId || e.to === focusedId;
}}

// --- initial seed ----------------------------------------------------
// Spread by kind in a coarse band so the simulation starts from a
// non-degenerate position. The force loop refines.
function seedPositions() {{
  const kindOrder = ['unit','commitment','stakeholder','activity','person','financial-summary','identity','source'];
  NODES.forEach((n, i) => {{
    const kindIdx = kindOrder.indexOf(n.kind);
    const angle = (i / NODES.length) * Math.PI * 2 + (kindIdx >= 0 ? kindIdx * 0.7 : 0);
    const r = 220 + (kindIdx % 2 === 0 ? 30 : -30);
    n.x = W/2 + Math.cos(angle) * r + (Math.random() - 0.5) * 30;
    n.y = H/2 + Math.sin(angle) * r + (Math.random() - 0.5) * 30;
    n.vx = 0; n.vy = 0;
  }});
}}
seedPositions();
recomputeDegrees();

// --- force tick ------------------------------------------------------
let alpha = 1;
let running = false;
function tick() {{
  const visible = NODES.filter(isNodeVisible);
  // O(n²) repulsion across visible nodes only.
  for (let i = 0; i < visible.length; i++) {{
    for (let j = i+1; j < visible.length; j++) {{
      const a = visible[i], b = visible[j];
      let dx = a.x - b.x, dy = a.y - b.y;
      let d2 = dx*dx + dy*dy;
      if (d2 < 1) {{ dx = (Math.random()-0.5)*2; dy = (Math.random()-0.5)*2; d2 = 4; }}
      const f = (FORCE.repulse / d2) * alpha;
      const d = Math.sqrt(d2);
      const fx = (dx/d) * f, fy = (dy/d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }}
  }}
  // Edge attraction (visible edges only).
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
  // Centring + integrate (visible nodes only — hidden nodes don't move).
  visible.forEach(n => {{
    n.vx += (W/2 - n.x) * FORCE.centering;
    n.vy += (H/2 - n.y) * FORCE.centering;
    n.vx *= FORCE.damping;
    n.vy *= FORCE.damping;
    n.x += n.vx;
    n.y += n.vy;
    const r = radiusFor(n) + 4;
    n.x = Math.max(r, Math.min(W - r, n.x));
    n.y = Math.max(r, Math.min(H - r, n.y));
  }});
  applyDOMState();
  alpha *= 0.992;
  if (alpha > 0.005) {{
    requestAnimationFrame(tick);
  }} else {{
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
  const line = el('line', {{
    class: 'edge kind-' + e.kind,
    'stroke': (e.kind === 'cite' || e.kind === 'link') ? 'rgba(0,0,0,0.18)' : 'rgba(0,0,0,0.4)',
    'stroke-width': e.kind === 'parent' ? 1.2 : (e.kind === 'cite' || e.kind === 'link' ? 0.5 : 0.8),
    'stroke-dasharray': e.kind === 'cite' ? '2 3' : '',
  }});
  e._line = line;
  edgesLayer.appendChild(line);
}});

NODES.forEach(n => {{
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

// --- DOM update on tick + filter --------------------------------------
function applyDOMState() {{
  NODES.forEach(n => {{
    const r = radiusFor(n);
    if (n._circle) {{
      n._circle.setAttribute('cx', n.x);
      n._circle.setAttribute('cy', n.y);
      n._circle.setAttribute('r', r);
    }}
    if (n._label) {{
      n._label.setAttribute('x', n.x + r + 5);
      n._label.setAttribute('y', n.y + 4);
      // Big nodes get the larger label class for hierarchy.
      const big = (n._degree || 0) >= 8;
      n._label.classList.toggle('large', big);
    }}
    const visible = isNodeVisible(n);
    const inFocus = isInFocus(n.id);
    if (n._circle) {{
      n._circle.style.display = visible ? '' : 'none';
      n._circle.style.opacity = !visible ? 0 : (inFocus ? 1 : 0.10);
      n._circle.classList.toggle('focused', focusedId === n.id);
    }}
    if (n._label) {{
      // Show a label only if (a) the node is visible, (b) it's in focus
      // (or no focus is set), and (c) the node is degree ≥ 4 in the
      // current visible graph or is the focused node — otherwise
      // the canvas clutters fast at scale.
      const labelWorth = (n._degree || 0) >= 4 || focusedId === n.id || focusedNeighbours.has(n.id);
      n._label.style.display = (visible && inFocus && labelWorth) ? '' : 'none';
    }}
  }});
  EDGES.forEach(e => {{
    if (!e._line) return;
    const a = NODE_BY_ID[e.from], b = NODE_BY_ID[e.to];
    if (!a || !b) {{ e._line.style.display = 'none'; return; }}
    e._line.setAttribute('x1', a.x);
    e._line.setAttribute('y1', a.y);
    e._line.setAttribute('x2', b.x);
    e._line.setAttribute('y2', b.y);
    const ev = isEdgeVisible(e);
    const inFocus = edgeInFocus(e);
    e._line.style.display = ev ? '' : 'none';
    e._line.style.opacity = !ev ? 0 : (inFocus ? 0.6 : 0.06);
  }});
}}

// --- stats strip update ----------------------------------------------
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
    recomputeDegrees();
    updateStats();
    reheat(0.6);
  }});
}});
document.querySelectorAll('#legend-edges .swatch').forEach(s => {{
  s.addEventListener('click', () => {{
    const k = s.dataset.edgekind;
    if (visibleEdgeKinds.has(k)) visibleEdgeKinds.delete(k);
    else visibleEdgeKinds.add(k);
    refreshSwatchUI();
    setFocus(null);
    recomputeDegrees();
    updateStats();
    reheat(0.6);
  }});
}});

document.getElementById('btn-reheat').addEventListener('click', () => {{
  // Re-shake: nudge every visible node by a small random vector and
  // reheat the simulation. Useful when the layout settles into a
  // local minimum.
  NODES.forEach(n => {{
    if (!isNodeVisible(n)) return;
    n.vx += (Math.random() - 0.5) * 8;
    n.vy += (Math.random() - 0.5) * 8;
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
  // Ignore mousedown on a node — node click handler takes precedence.
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
  // Convert mouse position to viewport-space coordinates so the zoom
  // anchors on the cursor.
  const mx = ((e.clientX - rect.left) / rect.width)  * 1160;
  const my = ((e.clientY - rect.top)  / rect.height) * 720;
  const factor = Math.exp(-e.deltaY * 0.0015);
  const newK = Math.min(4, Math.max(0.3, view.k * factor));
  // Adjust translate so the cursor stays anchored.
  view.x = mx - (mx - view.x) * (newK / view.k);
  view.y = my - (my - view.y) * (newK / view.k);
  view.k = newK;
  applyViewport();
}}, {{ passive: false }});

// --- popover ---------------------------------------------------------
const popoverEl   = document.getElementById('popover');
const popoverBody = document.getElementById('popover-body');

function showPopover(html, anchorRect) {{
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
function hidePopover() {{ popoverEl.classList.remove('open'); }}

function buildNodeHtml(n) {{
  const out = [], inn = [];
  EDGES.forEach(e => {{
    if (!visibleEdgeKinds.has(e.kind)) return;  // popover respects current edge filter
    if (e.from === n.id) {{
      const t = NODE_BY_ID[e.to];
      if (t && visibleNodeKinds.has(t.kind)) out.push({{ rel: REL_LABELS[e.kind] || e.kind, target: t }});
    }} else if (e.to === n.id) {{
      const f = NODE_BY_ID[e.from];
      if (f && visibleNodeKinds.has(f.kind)) inn.push({{ rel: REL_LABELS_REV[e.kind] || e.kind, source: f }});
    }}
  }});
  let html = `<div class="eyebrow">${{escapeHtml(n.kind)}}</div>`;
  html += `<h3>${{escapeHtml(n.label)}}</h3>`;
  if (n.description) html += `<div class="desc">${{escapeHtml(n.description)}}</div>`;
  if (out.length) {{
    html += `<div class="section-label">Outgoing (${{out.length}})</div>`;
    html += `<div class="neighbour-list">` + out.slice(0, 10).map(r =>
      `<div class="row"><span class="rel">${{escapeHtml(r.rel)}}</span><span>${{escapeHtml(r.target.label)}}</span></div>`
    ).join('') + (out.length > 10 ? `<div class="row"><span class="rel">…</span><span>${{out.length - 10}} more</span></div>` : '') + `</div>`;
  }}
  if (inn.length) {{
    html += `<div class="section-label">Incoming (${{inn.length}})</div>`;
    html += `<div class="neighbour-list">` + inn.slice(0, 10).map(r =>
      `<div class="row"><span class="rel">${{escapeHtml(r.rel)}}</span><span>${{escapeHtml(r.source.label)}}</span></div>`
    ).join('') + (inn.length > 10 ? `<div class="row"><span class="rel">…</span><span>${{inn.length - 10}} more</span></div>` : '') + `</div>`;
  }}
  if (n._path) html += `<div class="citation">${{escapeHtml(n._path)}}</div>`;
  return html;
}}

// Click handler — node click sets focus + opens popover.
svg.addEventListener('click', (e) => {{
  if (e.target.classList && e.target.classList.contains('node-circle')) {{
    const id = e.target.getAttribute('data-id');
    const node = NODE_BY_ID[id];
    if (!node) return;
    setFocus(id);
    applyDOMState();
    const r = e.target.getBoundingClientRect();
    showPopover(buildNodeHtml(node), {{
      left:   r.left + window.scrollX,
      right:  r.right + window.scrollX,
      top:    r.top + window.scrollY,
      bottom: r.bottom + window.scrollY,
    }});
    e.stopPropagation();
  }}
}});

// Click anywhere else clears focus.
document.addEventListener('click', (e) => {{
  let n = e.target;
  while (n && n.nodeType === 1) {{
    if (n.id === 'popover') return;
    if (n.classList && n.classList.contains('node-circle')) return;
    if (n.classList && n.classList.contains('swatch')) return;
    if (n.classList && n.classList.contains('btn')) return;
    n = n.parentNode;
  }}
  hidePopover();
  if (focusedId) {{
    setFocus(null);
    applyDOMState();
  }}
}}, true);

document.getElementById('popover-close').addEventListener('click', hidePopover);
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') {{
    hidePopover();
    if (focusedId) {{ setFocus(null); applyDOMState(); }}
  }}
}});

// Boot.
updateStats();
reheat(1);
</script>
</body>
</html>"""


def render_html(d: dict, title: str) -> str:
    nodes = d.get("nodes", []) or []
    edges = d.get("edges", []) or []

    # Default visible counts in the stats strip — match the JS defaults
    # so the page lands consistent on first paint.
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

    return HTML_TEMPLATE.format(
        css=base_css() + EXTRA_CSS,
        title=escape(title),
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
