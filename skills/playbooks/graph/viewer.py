#!/usr/bin/env python3
"""
graph / viewer.py — Render the whole-org graph as a vanilla-JS force-directed
visualization with the same Play New chrome as the other four playbooks.

Layout choices:
- 1240px container, 80px horizontal padding (consistent with the other
  viewers on the project).
- Header / intro / decisions live in the 820px editorial column at the
  start and end of the page.
- The graph canvas itself spans the full container width — at 820px the
  topology of 30+ nodes is unreadable, and the canvas is the entire
  point of the page.
- Vanilla force simulation, ~80 lines of JS. No D3 dependency; the
  artefact must open offline anywhere.
- Click a node → popover (same pattern as value-map / world-model /
  ai-exposure / reshuffle): below the click, centered horizontally,
  flips above when there's no room.

Visual code:
- Shape = circle for every node (graphs read shape less reliably than
  position; the differentiator is colour and size).
- Colour = node kind. Pulled from the data-viz palette, tinted in
  the legend so the eye anchors before reading.
- Size = log of degree. Highly-connected nodes appear larger so the
  cardinal nodes (the cited charters, the busiest units) read as
  cardinal at a glance.
- Edge stroke ≈ 0.5px, opacity 0.4. The graph reads as topology, not
  as a wiring diagram.

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
     so brand and viz stay in sync. The legend uses the same hues. */
  --kind-identity:           var(--ds-coral);    /* the org's own writing about itself */
  --kind-unit:               var(--ds-slate);    /* areas / divisions */
  --kind-activity:           var(--ds-sage);     /* what the org does */
  --kind-person:             var(--fg);          /* named people */
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

/* Topology stat strip — small, centered under the intro. */
.stats-strip { max-width: 820px; margin: 0 auto 32px; display: flex; flex-wrap: wrap; gap: 24px; padding: 16px 0; border-top: 1px solid var(--fg-hairline); border-bottom: 1px solid var(--fg-hairline); }
.stats-strip .stat { display: flex; flex-direction: column; gap: 4px; }
.stats-strip .stat .num { font-family: var(--font-display); font-size: 1.4rem; font-weight: 500; letter-spacing: -0.02em; color: var(--fg); font-variant-numeric: tabular-nums; }
.stats-strip .stat .lab { font-family: var(--font-display); font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); }

/* Legend — single row above the canvas, in the same editorial column. */
.legend { max-width: 1160px; margin: 0 auto 14px; display: flex; flex-wrap: wrap; gap: 16px 22px; align-items: center; padding: 0 8px; font-size: 0.78rem; color: var(--fg-muted); }
.legend .swatch { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; transition: color 0.15s; user-select: none; }
.legend .swatch:hover { color: var(--fg); }
.legend .swatch .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.legend .swatch.dim { opacity: 0.32; }
.legend .swatch.dim .dot { opacity: 0.5; }
.legend .sep { color: var(--fg-light); }
.legend .hint { color: var(--fg-light); font-size: 0.74rem; margin-left: auto; }

/* Canvas — the cardinal block. Width: full container, height: tall
   enough that the force layout can spread without crowding. */
.graph-shell { max-width: 1160px; margin: 0 auto; border: 1px solid var(--fg-hairline); border-radius: 6px; background: #FFFFFF; overflow: hidden; position: relative; }
.graph-shell svg { display: block; width: 100%; height: 640px; }
.graph-shell svg .edge { stroke: rgba(0,0,0,0.18); stroke-width: 0.6; }
.graph-shell svg .edge.kind-cite { stroke-dasharray: 2 3; }
.graph-shell svg .edge.kind-link { stroke: rgba(0,0,0,0.10); }
.graph-shell svg .edge.kind-parent { stroke: var(--fg); stroke-width: 1.0; }
.graph-shell svg .node { cursor: pointer; transition: stroke-width 0.12s; }
.graph-shell svg .node:hover { stroke: var(--fg); stroke-width: 2; }
.graph-shell svg .node.selected { stroke: var(--fg); stroke-width: 2.5; }
.graph-shell svg .node-label { font-family: var(--font-display); font-size: 10px; fill: var(--fg-muted); pointer-events: none; }
.graph-shell svg .node-label.large { font-size: 12px; fill: var(--fg); font-weight: 500; }

/* Decisions section — centered editorial column, identical to the other playbooks. */
.section { max-width: 820px; margin: 96px auto 0; padding-top: 40px; border-top: 1px solid var(--fg-hairline); }
.section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 20px; }
.section p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; max-width: 720px; }
.section .lead { font-size: 0.95rem; color: var(--fg-muted); line-height: 1.65; max-width: 720px; margin: 0 0 28px; }

.decision { margin-bottom: 32px; }
.decision .question { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; color: var(--fg); margin: 0 0 8px; letter-spacing: -0.01em; }
.decision .answer { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 6px; max-width: 720px; }
.decision .source { font-size: 0.78rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }

/* Popover — same pattern as value-map / ai-exposure / world-model. */
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
      <p class="lead">The whole organization as a single graph. Every unit, person, activity, stakeholder, commitment, and source — and every relation declared in the structure between them.</p>
    </header>

    <div class="intro">
      <p>Each of the four other playbooks reads the structure through a frame: an exposure map, a value chain, a bundle, a capability stack. This page reads the structure as itself — every node and every relation it declares — without an interpretive layer in between.</p>
      <p>Click any circle to see what it is and what it connects to. The size of a circle reflects how many other things mention it: bigger circles are the structure's load-bearing nodes — the documents most cited, the units most touched, the stakeholders most served.</p>
      <div class="pull">A connected, dense graph means the structure is internally consistent: claims cite sources, activities sit in units, commitments name parties on both sides. Sparse regions and isolates point at the places where the structure has not been written down yet.</div>
    </div>

    <section class="stats-strip">
      <div class="stat"><div class="num">{n_nodes}</div><div class="lab">nodes</div></div>
      <div class="stat"><div class="num">{n_edges}</div><div class="lab">relations</div></div>
      <div class="stat"><div class="num">{n_kinds}</div><div class="lab">node kinds</div></div>
      <div class="stat"><div class="num">{n_isolates}</div><div class="lab">isolates</div></div>
    </section>

    <div class="legend" id="legend">
      <span class="swatch" data-kind="identity"><span class="dot" style="background: var(--kind-identity)"></span>identity</span>
      <span class="swatch" data-kind="unit"><span class="dot" style="background: var(--kind-unit)"></span>unit</span>
      <span class="swatch" data-kind="activity"><span class="dot" style="background: var(--kind-activity)"></span>activity</span>
      <span class="swatch" data-kind="person"><span class="dot" style="background: var(--kind-person)"></span>person</span>
      <span class="swatch" data-kind="stakeholder"><span class="dot" style="background: var(--kind-stakeholder)"></span>stakeholder</span>
      <span class="swatch" data-kind="commitment"><span class="dot" style="background: var(--kind-commitment); border: 1px solid var(--ds-coral)"></span>commitment</span>
      <span class="swatch" data-kind="financial-summary"><span class="dot" style="background: var(--kind-financial-summary)"></span>financial</span>
      <span class="swatch" data-kind="source"><span class="dot" style="background: var(--kind-source)"></span>source</span>
      <span class="hint">click a kind to dim it · click a node to inspect</span>
    </div>

    <div class="graph-shell">
      <svg id="graph" viewBox="0 0 1160 640" preserveAspectRatio="xMidYMid meet"></svg>
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
  'unit':               getComputedStyle(document.documentElement).getPropertyValue('--kind-unit').trim(),
  'activity':           getComputedStyle(document.documentElement).getPropertyValue('--kind-activity').trim(),
  'person':             getComputedStyle(document.documentElement).getPropertyValue('--kind-person').trim(),
  'stakeholder':        getComputedStyle(document.documentElement).getPropertyValue('--kind-stakeholder').trim(),
  'commitment':         getComputedStyle(document.documentElement).getPropertyValue('--kind-commitment').trim(),
  'financial-summary':  getComputedStyle(document.documentElement).getPropertyValue('--kind-financial-summary').trim(),
  'source':             getComputedStyle(document.documentElement).getPropertyValue('--kind-source').trim(),
}};

const REL_LABELS = {{
  'parent':           'is part of',
  'unit':             'sits in',
  'performer':        'performed by',
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
  'party_committing': 'committed by',
  'party_benefiting': 'benefits from',
  'touches':          'touched by',
  'cite':             'cited by',
  'link':             'mentioned by',
}};

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }})[c]);
}}

// ----------------- degrees + radii -----------------
const degree = {{}};
NODES.forEach(n => {{ degree[n.id] = 0; }});
EDGES.forEach(e => {{
  degree[e.from] = (degree[e.from] || 0) + 1;
  degree[e.to]   = (degree[e.to]   || 0) + 1;
}});
function radiusFor(id) {{
  const d = degree[id] || 0;
  return 4 + Math.sqrt(d) * 1.6;
}}

// ----------------- layout -----------------
const W = 1160, H = 640;
NODES.forEach((n, i) => {{
  // Seed positions with a deterministic angular spread by kind so the
  // simulation converges from a non-degenerate start. The force loop
  // does the actual layout; this just nudges the initial topology.
  const kindIdx = ['identity','unit','activity','person','stakeholder','commitment','financial-summary','source'].indexOf(n.kind);
  const ang = (i / NODES.length) * Math.PI * 2 + (kindIdx >= 0 ? kindIdx * 0.6 : 0);
  const r = 200 + (kindIdx % 2 === 0 ? 40 : -20);
  n.x = W/2 + Math.cos(ang) * r;
  n.y = H/2 + Math.sin(ang) * r;
  n.vx = 0; n.vy = 0;
}});

const NODE_BY_ID = Object.fromEntries(NODES.map(n => [n.id, n]));

// Force-directed simulation, vanilla JS. ~150 iterations gets us a
// readable layout for graphs in the 30-100 node range; bigger graphs
// will want a heavier engine, but we don't ship that as a dependency.
function step(t) {{
  const k = 60;            // ideal edge length
  const repulse = 1800;    // node-node repulsion
  const damping = 0.7;

  // Repulsion (O(n²); fine at this scale).
  for (let i = 0; i < NODES.length; i++) {{
    for (let j = i+1; j < NODES.length; j++) {{
      const a = NODES[i], b = NODES[j];
      let dx = a.x - b.x, dy = a.y - b.y;
      let d2 = dx*dx + dy*dy;
      if (d2 < 1) {{ dx = (Math.random()-0.5); dy = (Math.random()-0.5); d2 = 1; }}
      const f = repulse / d2;
      const d = Math.sqrt(d2);
      const fx = (dx/d) * f, fy = (dy/d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }}
  }}
  // Attraction along edges.
  EDGES.forEach(e => {{
    const a = NODE_BY_ID[e.from], b = NODE_BY_ID[e.to];
    if (!a || !b) return;
    const dx = b.x - a.x, dy = b.y - a.y;
    const d = Math.sqrt(dx*dx + dy*dy) || 1;
    const f = (d - k) * 0.05;
    const fx = (dx/d) * f, fy = (dy/d) * f;
    a.vx += fx; a.vy += fy;
    b.vx -= fx; b.vy -= fy;
  }});
  // Centring + integrate.
  NODES.forEach(n => {{
    n.vx += (W/2 - n.x) * 0.005;
    n.vy += (H/2 - n.y) * 0.005;
    n.vx *= damping; n.vy *= damping;
    n.x += n.vx; n.y += n.vy;
    // Clamp.
    const r = radiusFor(n.id) + 4;
    n.x = Math.max(r, Math.min(W - r, n.x));
    n.y = Math.max(r, Math.min(H - r, n.y));
  }});
}}

for (let i = 0; i < 220; i++) step(i);

// ----------------- render -----------------
const svg = document.getElementById('graph');
function el(name, attrs, children) {{
  const e = document.createElementNS('http://www.w3.org/2000/svg', name);
  for (const k in (attrs || {{}})) e.setAttribute(k, attrs[k]);
  (children || []).forEach(c => e.appendChild(c));
  return e;
}}

EDGES.forEach((e, i) => {{
  const a = NODE_BY_ID[e.from], b = NODE_BY_ID[e.to];
  if (!a || !b) return;
  const line = el('line', {{
    x1: a.x, y1: a.y, x2: b.x, y2: b.y,
    class: 'edge kind-' + e.kind,
    'data-from': e.from, 'data-to': e.to, 'data-kind': e.kind,
  }});
  svg.appendChild(line);
}});

NODES.forEach(n => {{
  const r = radiusFor(n.id);
  const c = el('circle', {{
    cx: n.x, cy: n.y, r,
    class: 'node kind-' + n.kind,
    fill: KIND_COLOR[n.kind] || '#888',
    stroke: 'rgba(0,0,0,0.32)',
    'stroke-width': 0.8,
    'data-id': n.id,
  }});
  svg.appendChild(c);
  // Label only the nodes that read as load-bearing (degree >= 6) so
  // the canvas doesn't clutter at this density.
  if ((degree[n.id] || 0) >= 6) {{
    const t = el('text', {{
      x: n.x + r + 4, y: n.y + 3,
      class: 'node-label' + (degree[n.id] >= 12 ? ' large' : ''),
    }});
    t.textContent = n.label.length > 28 ? n.label.slice(0, 27) + '…' : n.label;
    svg.appendChild(t);
  }}
}});

// ----------------- legend filter -----------------
const dimmed = new Set();
function applyDim() {{
  svg.querySelectorAll('.node').forEach(c => {{
    const k = c.classList[1].replace('kind-', '');
    c.style.opacity = dimmed.has(k) ? 0.12 : 1;
  }});
  svg.querySelectorAll('.edge').forEach(line => {{
    const f = NODE_BY_ID[line.getAttribute('data-from')];
    const t = NODE_BY_ID[line.getAttribute('data-to')];
    const off = (f && dimmed.has(f.kind)) || (t && dimmed.has(t.kind));
    line.style.opacity = off ? 0.05 : 1;
  }});
  svg.querySelectorAll('.node-label').forEach(t => {{
    const cx = parseFloat(t.getAttribute('x')) - 4;
    // Find the node circle nearest this label.
    let nearest = null, best = Infinity;
    NODES.forEach(n => {{
      const d = Math.abs(n.x + radiusFor(n.id) - cx) + Math.abs(n.y - parseFloat(t.getAttribute('y')) + 3);
      if (d < best) {{ best = d; nearest = n; }}
    }});
    t.style.opacity = (nearest && dimmed.has(nearest.kind)) ? 0.12 : 1;
  }});
  document.querySelectorAll('.legend .swatch').forEach(s => {{
    s.classList.toggle('dim', dimmed.has(s.dataset.kind));
  }});
}}
document.querySelectorAll('.legend .swatch').forEach(s => {{
  s.addEventListener('click', () => {{
    const k = s.dataset.kind;
    if (dimmed.has(k)) dimmed.delete(k); else dimmed.add(k);
    applyDim();
  }});
}});

// ----------------- popover -----------------
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
  const out = [];
  const inn = [];
  EDGES.forEach(e => {{
    if (e.from === n.id) {{
      const t = NODE_BY_ID[e.to];
      if (t) out.push({{rel: REL_LABELS[e.kind] || e.kind, target: t}});
    }} else if (e.to === n.id) {{
      const f = NODE_BY_ID[e.from];
      if (f) inn.push({{rel: REL_LABELS_REV[e.kind] || e.kind, source: f}});
    }}
  }});
  let html = `<div class="eyebrow">${{escapeHtml(n.kind)}}</div>`;
  html += `<h3>${{escapeHtml(n.label)}}</h3>`;
  if (n.description) html += `<div class="desc">${{escapeHtml(n.description)}}</div>`;
  if (out.length) {{
    html += `<div class="section-label">Outgoing (${{out.length}})</div>`;
    html += `<div class="neighbour-list">` + out.slice(0, 8).map(r =>
      `<div class="row"><span class="rel">${{escapeHtml(r.rel)}}</span><span>${{escapeHtml(r.target.label)}}</span></div>`
    ).join('') + (out.length > 8 ? `<div class="row"><span class="rel">…</span><span>${{out.length - 8}} more</span></div>` : '') + `</div>`;
  }}
  if (inn.length) {{
    html += `<div class="section-label">Incoming (${{inn.length}})</div>`;
    html += `<div class="neighbour-list">` + inn.slice(0, 8).map(r =>
      `<div class="row"><span class="rel">${{escapeHtml(r.rel)}}</span><span>${{escapeHtml(r.source.label)}}</span></div>`
    ).join('') + (inn.length > 8 ? `<div class="row"><span class="rel">…</span><span>${{inn.length - 8}} more</span></div>` : '') + `</div>`;
  }}
  if (n._path) html += `<div class="citation">${{escapeHtml(n._path)}}</div>`;
  return html;
}}

svg.addEventListener('click', (e) => {{
  let n = e.target;
  if (n.classList && n.classList.contains('node')) {{
    const id = n.getAttribute('data-id');
    const node = NODE_BY_ID[id];
    if (!node) return;
    svg.querySelectorAll('.node.selected').forEach(x => x.classList.remove('selected'));
    n.classList.add('selected');
    const r = n.getBoundingClientRect();
    showPopover(buildNodeHtml(node), {{
      left:   r.left + window.scrollX,
      right:  r.right + window.scrollX,
      top:    r.top + window.scrollY,
      bottom: r.bottom + window.scrollY,
    }});
  }}
}});

document.addEventListener('click', (e) => {{
  let n = e.target;
  while (n && n.nodeType === 1) {{
    if (n.id === 'graph') return;
    if (n.id === 'popover') return;
    if (n.classList && n.classList.contains('node')) return;
    if (n.classList && n.classList.contains('swatch')) return;
    n = n.parentNode;
  }}
  hidePopover();
  svg.querySelectorAll('.node.selected').forEach(x => x.classList.remove('selected'));
}}, true);

document.getElementById('popover-close').addEventListener('click', hidePopover);
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') {{ hidePopover(); svg.querySelectorAll('.node.selected').forEach(x => x.classList.remove('selected')); }} }});
</script>
</body>
</html>"""


def render_html(d: dict, title: str) -> str:
    nodes = d.get("nodes", []) or []
    edges = d.get("edges", []) or []

    by_kind: dict[str, int] = {}
    for n in nodes:
        by_kind[n.get("kind", "")] = by_kind.get(n.get("kind", ""), 0) + 1

    # Isolates: nodes with no incident edges.
    incident: set[str] = set()
    for e in edges:
        incident.add(e.get("from", ""))
        incident.add(e.get("to", ""))
    isolates = [n for n in nodes if n.get("id") not in incident]

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
        n_nodes=len(nodes),
        n_edges=len(edges),
        n_kinds=len(by_kind),
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
