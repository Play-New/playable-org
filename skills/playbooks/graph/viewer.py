#!/usr/bin/env python3
"""
graph / viewer.py — Render the org graph as a single-file App-pure
viewer. Canvas-first layout: full-bleed force-directed picture, with
floating editorial chrome (dateline + Analysis CTA + colophon-strip
of kinds pills + tools cluster) on the *Carta sbiadita* paper.

Layout
    ┌─────────────────────────────────────────────────────────┐
    │ {org} / the operational structure        [date] [Analy] │
    │                                                          │
    │                                                          │
    │                  full-bleed canvas                       │
    │                  (force-directed graph)                  │
    │                                                          │
    │                          inspect ─── floats in on focus  │
    │ kinds-as-pills                hint            zoom       │
    │ unit · activity · ...                         Reset focus│
    └─────────────────────────────────────────────────────────┘

The shared App-pure shell (palette tokens, body baseline, mobile
polish, dateline + Analysis CTA + Inspect + Modal + responsive,
favicon, embedded font) lives in `skills/design.py` v5 and is reused
across all five playbook viewers. This module adds only the
graph-specific bits: canvas styling, kinds-pills row, tools cluster,
the force simulation + Pointer Events + pinch-zoom + node rendering
+ inspect grouping by verb.

Usage:
    python3 viewer.py --map <graph.json> --html <out.html>
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

# Shared App-pure shell — palette, body, mobile baseline, chrome
# helpers, modal, favicon, font. The graph viewer composes on top.
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
    inline_md,
)


# ----------------------------------------------------------------------
# Per-edge-kind verb labels. The structure stores edge.kind (e.g.
# "performer", "party_committing"), the inspect panel needs a readable
# verb in both directions ("performed by" outgoing, "performs" incoming).
# ----------------------------------------------------------------------
REL_LABELS_OUT = {
    "parent":           "is part of",
    "unit":             "in",
    "performer":        "performed by",
    "head_role":        "led by",
    "holds_role":       "holds",
    "covers":           "responsible for",
    "party_committing": "binds",
    "party_benefiting": "benefits",
    "touches":          "involves",
    "cite":             "cites",
    "link":             "links to",
}
REL_LABELS_IN = {
    "parent":           "contains",
    "unit":             "groups",
    "performer":        "performs",
    "head_role":        "leads",
    "holds_role":       "filled by",
    "covers":           "owned by",
    "party_committing": "bound by",
    "party_benefiting": "benefits from",
    "touches":          "involved in",
    "cite":             "cited by",
    "link":             "linked from",
}

# The viewer's reading: this is the *operational* structure — the
# topology of who does what for whom under which commitments. Six
# kinds qualify (unit, activity, person, role, stakeholder,
# commitment); the rest of the schema (sources, identity, financial
# summaries, language terms) is corpus / declarative metadata that
# build.py still emits into the JSON for other tools, but the viewer
# strips it before rendering. All six kinds are visible by default.
KIND_ORDER = [
    "unit", "activity", "person", "role", "stakeholder", "commitment",
]
KIND_LABEL_DISPLAY = {}
EXCLUDED_KINDS = {"source", "identity", "language-term", "financial-summary"}
# `link` is body-markdown cross-references (not a dependency); `cite`
# only points at sources we're already dropping. Both go.
EXCLUDED_EDGE_KINDS = {"link", "cite"}

# Palette: "Carta sbiadita" v2 (Claude Design — Play New, paper-aged,
# never saturated). The five operational kinds carry distinguishing
# hue; the five default-off kinds sit closer to warm grey so they
# read as ambient when toggled on.
KIND_COLORS = {
    "unit":              "#6b7d8c",  # blu polvere
    "activity":          "#8a9d6b",  # verde foglia secca
    "person":            "#1c1a16",  # ink
    "stakeholder":       "#9b8aa3",  # lilla cenere
    "commitment":        "#b87b5e",  # terracotta
    "role":              "#bca787",  # sabbia
    "financial-summary": "#7e8a6b",  # oliva
    "identity":          "#b89b94",  # rosa antico
    "language-term":     "#8c8a83",  # pietra
    "source":            "#a09a8e",  # grigio caldo
}

# All six operational kinds are visible by default. There is no
# default-off any more (the corpus / declarative kinds are stripped
# upstream in _adapt_data, not just hidden).
DEFAULT_ON = set(KIND_ORDER)


# ----------------------------------------------------------------------
# Graph-specific CSS — composes on top of design.app_pure_css(). Only
# the bits that don't generalise to the other viewers live here:
# canvas full-bleed sizing, the kinds-pills ribbon, the bottom-right
# tools cluster (zoom readout + Reset focus link).
# ----------------------------------------------------------------------
EXTRA_CSS = r"""
/* ─── CANVAS — full-bleed. The artefact. ──────────────────────── */
canvas {
  display: block;
  position: fixed;
  inset: 0;
  width: 100vw; height: 100vh;
  cursor: grab;
  touch-action: none;
}
canvas.dragging { cursor: grabbing; }

/* ─── KINDS RIBBON (bottom-left) — one pill per visible kind. ─── */
.kinds {
  display: flex; flex-wrap: nowrap; align-items: center;
  gap: 6px 8px;
  max-width: calc(100vw - 220px);
  overflow-x: auto;
  scrollbar-width: none;
}
.kinds::-webkit-scrollbar { display: none; }
.k {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 11px 6px;
  cursor: pointer; user-select: none;
  font-size: 11.5px;
  letter-spacing: -0.005em;
  color: var(--ink-95);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  background: var(--paper);
  white-space: nowrap;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}
.k .swatch { width: 7px; height: 7px; border-radius: 50%; background: var(--swatch, var(--ink-40)); }
.k .num { font-size: 10px; color: var(--ink-40); font-style: italic; }
.k:hover { border-color: var(--ink); }
.k.off { color: var(--ink-40); background: transparent; }
.k.off .swatch { opacity: 0.35; }
.k.off .num { color: var(--ink-25); }

/* ─── TOOLS (bottom-right) — zoom readout + Reset focus link ──── */
.tools {
  display: inline-flex; flex-direction: column; align-items: flex-end;
  gap: 6px;
  font-size: 11.5px;
  color: var(--ink-60);
  white-space: nowrap;
}
.tools .zoom { font-style: italic; color: var(--ink-40); }
.tools .zoom em {
  font-style: normal;
  color: var(--ink-80);
  border-bottom: 0.5px solid var(--ink-40);
  padding-bottom: 1px;
}
.tools button {
  background: transparent;
  border: 0;
  padding: 0 0 1px;
  cursor: pointer;
  font: inherit;
  font-size: 11.5px;
  color: var(--ink);
  letter-spacing: -0.005em;
  border-bottom: 0.5px solid var(--ink-40);
  line-height: 1;
}
.tools button:hover { border-bottom-color: var(--ink); }

@media (max-width: 760px) {
  .kinds { gap: 6px 6px; max-width: 60vw; }
  .k { padding: 7px 11px; font-size: 11.5px; }
  .tools { gap: 8px; font-size: 11.5px; }
  .tools button { padding: 6px 0; }
}
"""


# ----------------------------------------------------------------------
# Graph-specific JavaScript — force simulation + Pointer Events + pinch
# zoom + node rendering on canvas + kinds ribbon toggle + inspect
# grouping by verb. Modal open/close, Esc handler, "?" shortcut, and
# `?focus=<id>` permalink are provided by design.app_pure_baseline_js;
# the graph exposes `window.setFocus(id)` so those callers can drive it.
# ----------------------------------------------------------------------
JS = r"""
(() => {
  const DATA = JSON.parse(document.getElementById('graph-data').textContent);
  const KIND = Object.fromEntries(DATA.kinds.map(k => [k.id, k]));
  const NODE = Object.fromEntries(DATA.nodes.map(n => [n.id, n]));
  const REL_OUT = DATA.rel_out || {};
  const REL_IN  = DATA.rel_in  || {};

  // adjacency
  const ADJ = {};
  DATA.nodes.forEach(n => ADJ[n.id] = []);
  DATA.edges.forEach((e, i) => {
    e._i = i;
    ADJ[e.f].push({other: e.t, e, dir: 'out'});
    ADJ[e.t].push({other: e.f, e, dir: 'in'});
  });

  const state = {
    on: new Set(DATA.kinds.filter(k => k.default).map(k => k.id)),
    focus: null,
    hover: null,
    nodePos: {},
    pan: {x: 0, y: 0},
    zoom: 1,
    sim: {alpha: 1.0},
    drag: null,
  };

  // ---------- canvas ----------
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  const DPR = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
  let W = 0, H = 0;
  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * DPR; canvas.height = H * DPR;
    canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  window.addEventListener('resize', () => { resize(); state.sim.alpha = Math.max(state.sim.alpha, 0.3); });
  resize();

  // ---------- initial layout (kind-radial seed + warm-up) ----------
  function initLayout() {
    const groups = {};
    DATA.nodes.forEach(n => (groups[n.kind] = groups[n.kind] || []).push(n));
    const kindIds = DATA.kinds.map(k => k.id);
    const cx = W/2, cy = H/2;
    const R = Math.min(W, H) * 0.28;
    kindIds.forEach((kid, ki) => {
      const ang = (ki / kindIds.length) * Math.PI * 2;
      const cxk = cx + Math.cos(ang) * R * 0.6;
      const cyk = cy + Math.sin(ang) * R * 0.6;
      const list = groups[kid] || [];
      list.forEach((n, i) => {
        const a = (i / Math.max(1, list.length)) * Math.PI * 2;
        const r = 20 + Math.random() * 50;
        state.nodePos[n.id] = { x: cxk + Math.cos(a)*r, y: cyk + Math.sin(a)*r, vx:0, vy:0, fixed:false };
      });
    });
    state.sim.alpha = 1.0;
    // Warm-up: run the simulation synchronously so the first frame
    // already shows a settled, centred graph instead of a cluster
    // collapsing into one quadrant. Reset alpha each iteration so
    // step()'s built-in cooling doesn't bail mid-warmup.
    for (let i = 0; i < 280; i++) { state.sim.alpha = 1.0; step(); }
    state.sim.alpha = 0.4;
  }

  // ---------- simulation ----------
  function visibleNodes() { return DATA.nodes.filter(n => state.on.has(n.kind)); }
  function visibleEdges() { return DATA.edges.filter(e => state.on.has(NODE[e.f].kind) && state.on.has(NODE[e.t].kind)); }

  function step() {
    if (state.sim.alpha < 0.005) return;
    const nodes = visibleNodes();
    const edges = visibleEdges();
    const cx = W/2, cy = H/2;
    const a = state.sim.alpha;
    for (let i = 0; i < nodes.length; i++) {
      const A = state.nodePos[nodes[i].id];
      for (let j = i + 1; j < nodes.length; j++) {
        const B = state.nodePos[nodes[j].id];
        let dx = A.x - B.x, dy = A.y - B.y;
        let d2 = dx*dx + dy*dy;
        if (d2 < 0.01) { dx = (Math.random()-0.5); dy = (Math.random()-0.5); d2 = 1; }
        const d = Math.sqrt(d2);
        const f = 1500 / d2;
        const fx = (dx/d)*f, fy = (dy/d)*f;
        A.vx += fx*a; A.vy += fy*a; B.vx -= fx*a; B.vy -= fy*a;
      }
    }
    edges.forEach(e => {
      const A = state.nodePos[e.f], B = state.nodePos[e.t];
      const dx = B.x - A.x, dy = B.y - A.y;
      const d = Math.sqrt(dx*dx+dy*dy) || 1;
      const desired = 100;
      const k = 0.04;
      const f = (d - desired) * k;
      const fx = (dx/d)*f, fy = (dy/d)*f;
      A.vx += fx*a; A.vy += fy*a; B.vx -= fx*a; B.vy -= fy*a;
    });
    nodes.forEach(n => {
      const p = state.nodePos[n.id];
      p.vx += (cx - p.x) * 0.0055 * a;
      p.vy += (cy - p.y) * 0.0055 * a;
    });
    nodes.forEach(n => {
      const p = state.nodePos[n.id];
      if (p.fixed) { p.vx = 0; p.vy = 0; return; }
      p.vx *= 0.82; p.vy *= 0.82;
      p.x += p.vx * 0.5; p.y += p.vy * 0.5;
    });
    state.sim.alpha *= 0.985;
  }

  initLayout();

  // ---------- transforms ----------
  function w2s(p) {
    return { x: (p.x - W/2) * state.zoom + W/2 + state.pan.x * state.zoom,
             y: (p.y - H/2) * state.zoom + H/2 + state.pan.y * state.zoom };
  }
  function s2w(sx, sy) {
    return { x: (sx - W/2 - state.pan.x * state.zoom) / state.zoom + W/2,
             y: (sy - H/2 - state.pan.y * state.zoom) / state.zoom + H/2 };
  }

  function neighborSet(id) { const s = new Set([id]); (ADJ[id]||[]).forEach(a => s.add(a.other)); return s; }
  function nodeRadius(n) {
    const deg = (ADJ[n.id]||[]).filter(a => state.on.has(NODE[a.other].kind)).length;
    return 4.5 + Math.min(8, deg * 0.45);
  }

  // ---------- render ----------
  function render() {
    ctx.clearRect(0, 0, W, H);
    const nodes = visibleNodes();
    const edges = visibleEdges();
    const focusSet = state.focus ? neighborSet(state.focus) : null;
    const hoverSet = state.hover ? neighborSet(state.hover) : null;

    // edges
    edges.forEach(e => {
      const fp = state.nodePos[e.f], tp = state.nodePos[e.t];
      if (!fp || !tp) return;
      const sf = w2s(fp), st = w2s(tp);
      let alpha = 0.30;
      const dim = focusSet ? !(focusSet.has(e.f) && focusSet.has(e.t)) : false;
      if (dim) alpha = 0.05;
      if (hoverSet && !focusSet && (hoverSet.has(e.f) || hoverSet.has(e.t))) alpha = 0.55;
      ctx.strokeStyle = `rgba(28,26,22,${alpha})`;
      ctx.lineWidth = (focusSet && focusSet.has(e.f) && focusSet.has(e.t) ? 1.1 : 0.8);
      ctx.beginPath();
      ctx.moveTo(sf.x, sf.y);
      const dx = st.x - sf.x, dy = st.y - sf.y;
      const len = Math.hypot(dx, dy) || 1;
      const nx = -dy/len, ny = dx/len;
      const bow = 5;
      ctx.quadraticCurveTo((sf.x+st.x)/2 + nx*bow*0.4, (sf.y+st.y)/2 + ny*bow*0.4, st.x, st.y);
      ctx.stroke();
    });

    // nodes
    nodes.forEach(n => {
      const p = state.nodePos[n.id]; if (!p) return;
      const s = w2s(p);
      const r = nodeRadius(n) * Math.sqrt(state.zoom);
      const dim = focusSet ? !focusSet.has(n.id) : false;
      const focused = state.focus === n.id;
      const k = KIND[n.kind];
      ctx.globalAlpha = dim ? 0.18 : 1;
      if (focused || state.hover === n.id) {
        ctx.beginPath();
        ctx.arc(s.x, s.y, r + 6, 0, Math.PI*2);
        ctx.strokeStyle = state.hover === n.id && !focused ? 'rgba(28,26,22,0.35)' : 'rgba(28,26,22,0.10)';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(s.x, s.y, r + 5, 0, Math.PI*2);
        ctx.fillStyle = 'rgba(28,26,22,0.05)';
        ctx.fill();
      }
      ctx.beginPath();
      ctx.arc(s.x, s.y, r, 0, Math.PI*2);
      ctx.fillStyle = k.color;
      ctx.fill();
      ctx.lineWidth = focused ? 1.5 : 1;
      ctx.strokeStyle = focused ? 'rgba(28,26,22,0.95)' : 'rgba(28,26,22,0.18)';
      ctx.stroke();
      ctx.globalAlpha = 1;
    });

    // ---- focus label, tight against node ----
    if (state.focus) {
      const n = NODE[state.focus];
      const p = state.nodePos[n.id];
      if (p) {
        const s = w2s(p);
        const r = nodeRadius(n) * Math.sqrt(state.zoom);
        ctx.textBaseline = 'middle';
        ctx.textAlign = 'left';
        ctx.font = '540 13px Inter, system-ui, sans-serif';
        const tw = ctx.measureText(n.label).width;
        const lx = s.x + r + 8;
        const ly = s.y;
        ctx.fillStyle = 'rgba(244,238,226,0.92)';
        ctx.fillRect(lx - 3, ly - 9, tw + 8, 18);
        ctx.fillStyle = 'rgba(28,26,22,0.95)';
        ctx.fillText(n.label, lx, ly);
        ctx.font = 'italic 10px Inter, system-ui, sans-serif';
        ctx.fillStyle = 'rgba(28,26,22,0.5)';
        ctx.fillText(n.kind, lx, ly - 14);
      }
    }

    // labels for focus-neighbors only
    if (focusSet) {
      DATA.nodes.forEach(n => {
        if (!state.on.has(n.kind)) return;
        if (!focusSet.has(n.id)) return;
        if (n.id === state.focus) return;
        const p = state.nodePos[n.id]; if (!p) return;
        const s = w2s(p);
        const r = nodeRadius(n) * Math.sqrt(state.zoom);
        ctx.font = '460 11px Inter, system-ui, sans-serif';
        const tw = ctx.measureText(n.label).width;
        ctx.fillStyle = 'rgba(244,238,226,0.85)';
        ctx.fillRect(s.x + r + 5, s.y - 7, tw + 4, 14);
        ctx.fillStyle = 'rgba(28,26,22,0.85)';
        ctx.textBaseline = 'middle';
        ctx.fillText(n.label, s.x + r + 7, s.y);
      });
    }
  }

  function hitTest(sx, sy) {
    const nodes = visibleNodes();
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const p = state.nodePos[n.id]; if (!p) continue;
      const s = w2s(p);
      const r = nodeRadius(n) * Math.sqrt(state.zoom) + 3;
      const dx = sx - s.x, dy = sy - s.y;
      if (dx*dx + dy*dy <= r*r) return n;
    }
    return null;
  }

  function loop() { step(); render(); requestAnimationFrame(loop); }
  requestAnimationFrame(loop);

  // ---------- inputs ----------
  const tooltip = document.getElementById('tooltip');
  const hint = document.getElementById('hint');
  const zoomReadout = document.getElementById('zoom-readout');
  function updateZoom() { zoomReadout.querySelector('em').textContent = Math.round(state.zoom*100) + '%'; }

  // ── Pointer Events: a single code path for mouse, touch, and
  //    pen. Tracks all active pointers so we can do pinch-zoom on
  //    touch (two fingers) without losing the mouse-drag flow.
  const pointers = new Map(); // id -> {x, y}
  let pinch = null;           // {dist, cx, cy} when 2 pointers down
  let lastPointerType = 'mouse';

  function setPinch() {
    if (pointers.size !== 2) { pinch = null; return; }
    const [a, b] = [...pointers.values()];
    const dx = b.x - a.x, dy = b.y - a.y;
    pinch = { dist: Math.hypot(dx, dy), cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 };
  }

  canvas.addEventListener('pointerdown', (ev) => {
    canvas.setPointerCapture(ev.pointerId);
    pointers.set(ev.pointerId, {x: ev.clientX, y: ev.clientY});
    lastPointerType = ev.pointerType || 'mouse';

    if (pointers.size >= 2) {
      if (state.drag && state.drag.type === 'node') {
        state.nodePos[state.drag.id].fixed = false;
      }
      state.drag = null;
      canvas.classList.remove('dragging');
      setPinch();
      return;
    }

    const sx = ev.clientX, sy = ev.clientY;
    const hit = hitTest(sx, sy);
    if (hit) {
      state.drag = { type:'node', id:hit.id, lastX:sx, lastY:sy, moved:false };
      state.nodePos[hit.id].fixed = true;
      canvas.classList.add('dragging');
    } else {
      state.drag = { type:'pan', lastX:sx, lastY:sy, moved:false };
      canvas.classList.add('dragging');
    }

    if (lastPointerType === 'touch') {
      state.hover = null;
      tooltip.classList.remove('show');
    }
  });

  canvas.addEventListener('pointermove', (ev) => {
    if (pointers.has(ev.pointerId)) {
      pointers.set(ev.pointerId, {x: ev.clientX, y: ev.clientY});
    }

    if (pinch && pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      const dx = b.x - a.x, dy = b.y - a.y;
      const newDist = Math.hypot(dx, dy);
      const newCx = (a.x + b.x) / 2, newCy = (a.y + b.y) / 2;
      if (pinch.dist > 0) {
        const scale = newDist / pinch.dist;
        const before = s2w(newCx, newCy);
        state.zoom = Math.max(0.4, Math.min(3.0, state.zoom * scale));
        const after = s2w(newCx, newCy);
        state.pan.x += (after.x - before.x);
        state.pan.y += (after.y - before.y);
        const panDx = (newCx - pinch.cx) / state.zoom;
        const panDy = (newCy - pinch.cy) / state.zoom;
        state.pan.x += panDx;
        state.pan.y += panDy;
        updateZoom();
      }
      pinch.dist = newDist; pinch.cx = newCx; pinch.cy = newCy;
      return;
    }

    const sx = ev.clientX, sy = ev.clientY;
    if (state.drag) {
      const dx = sx - state.drag.lastX;
      const dy = sy - state.drag.lastY;
      state.drag.lastX = sx; state.drag.lastY = sy;
      if (Math.abs(dx) + Math.abs(dy) > 2) state.drag.moved = true;
      if (state.drag.type === 'node') {
        const p = state.nodePos[state.drag.id];
        p.x += dx / state.zoom; p.y += dy / state.zoom;
        p.vx = 0; p.vy = 0;
        state.sim.alpha = Math.max(state.sim.alpha, 0.4);
      } else {
        state.pan.x += dx / state.zoom;
        state.pan.y += dy / state.zoom;
      }
    } else if (lastPointerType !== 'touch') {
      const hit = hitTest(sx, sy);
      const newHover = hit ? hit.id : null;
      if (newHover !== state.hover) {
        state.hover = newHover;
        if (hit) {
          tooltip.innerHTML = `${hit.label}<span class="meta">${hit.kind}</span>`;
          tooltip.classList.add('show');
          canvas.style.cursor = 'pointer';
        } else {
          tooltip.classList.remove('show');
          canvas.style.cursor = state.drag ? 'grabbing' : 'grab';
        }
      }
      if (hit) {
        tooltip.style.left = sx + 'px';
        tooltip.style.top = sy + 'px';
      }
    }
  });

  function endPointer(ev) {
    pointers.delete(ev.pointerId);
    if (pointers.size < 2) pinch = null;
    if (!state.drag) return;
    if (pointers.size > 0) return;
    const d = state.drag;
    canvas.classList.remove('dragging');
    if (d.type === 'node' && !d.moved) setFocus(d.id);
    if (d.type === 'pan' && !d.moved) setFocus(null);
    if (d.type === 'node') { state.nodePos[d.id].fixed = false; state.sim.alpha = Math.max(state.sim.alpha, 0.25); }
    state.drag = null;
  }
  canvas.addEventListener('pointerup', endPointer);
  canvas.addEventListener('pointercancel', endPointer);

  canvas.addEventListener('wheel', (ev) => {
    ev.preventDefault();
    const before = s2w(ev.clientX, ev.clientY);
    state.zoom = Math.max(0.4, Math.min(3.0, state.zoom * Math.exp(-ev.deltaY * 0.0015)));
    const after = s2w(ev.clientX, ev.clientY);
    state.pan.x += (after.x - before.x);
    state.pan.y += (after.y - before.y);
    updateZoom();
  }, {passive:false});

  // hide hint after first interaction
  let hintHidden = false;
  function hideHint() { if (hintHidden || !hint) return; hintHidden = true; hint.classList.add('gone'); setTimeout(() => hint.remove(), 700); }
  canvas.addEventListener('pointerdown', hideHint, {once:true});
  canvas.addEventListener('wheel', hideHint, {once:true});

  // ---------- kinds ribbon ----------
  function renderKinds() {
    const root = document.getElementById('kinds');
    root.innerHTML = '';
    DATA.kinds.forEach((k) => {
      const count = DATA.nodes.filter(n => n.kind === k.id).length;
      const span = document.createElement('span');
      span.className = 'k' + (state.on.has(k.id) ? '' : ' off');
      span.style.setProperty('--swatch', k.color);
      span.innerHTML = `<span class="swatch"></span><span class="lbl">${k.label}</span> <span class="num">${count}</span>`;
      span.addEventListener('click', () => {
        if (state.on.has(k.id)) state.on.delete(k.id); else state.on.add(k.id);
        state.sim.alpha = Math.max(state.sim.alpha, 0.6);
        renderKinds();
        if (state.focus && !state.on.has(NODE[state.focus].kind)) setFocus(null);
        if (state.focus) renderInspect();
      });
      root.appendChild(span);
    });
  }
  renderKinds();

  // ---------- inspect ----------
  const inspect = document.getElementById('inspect');
  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  }
  function groupByVerb(rows, verbFn) {
    const order = [];
    const groups = new Map();
    rows.forEach(a => {
      const v = verbFn(a.e.verb);
      if (!groups.has(v)) { groups.set(v, []); order.push(v); }
      groups.get(v).push(a);
    });
    return order.map(v => ({verb: v, items: groups.get(v)}));
  }
  function renderRelSection(label, count, groups) {
    if (!count) return '';
    const body = groups.map(g => `
      <div class="rel-verb"><span>${escapeHtml(g.verb)}</span><span class="rel-verb-count">${g.items.length}</span></div>
      ${g.items.map(a => `<div class="rel" data-id="${escapeHtml(a.other)}">
        <span class="swatch" style="background:${KIND[NODE[a.other].kind].color}"></span>
        <span class="name">${escapeHtml(NODE[a.other].label)}</span>
      </div>`).join('')}
    `).join('');
    return `<div class="rel-group"><h3>${escapeHtml(label)} <span class="count">${count}</span></h3>${body}</div>`;
  }
  function renderInspect() {
    const body = document.getElementById('inspect-body');
    if (!state.focus) { inspect.classList.remove('open'); return; }
    inspect.classList.add('open');
    const n = NODE[state.focus]; const k = KIND[n.kind];
    const adj = ADJ[n.id] || [];
    const out = adj.filter(a => a.dir==='out' && state.on.has(NODE[a.other].kind));
    const inn = adj.filter(a => a.dir==='in'  && state.on.has(NODE[a.other].kind));
    const verbOut = (kind) => REL_OUT[kind] || kind;
    const verbIn  = (kind) => REL_IN[kind]  || kind;

    const outGroups = groupByVerb(out, verbOut);
    const innGroups = groupByVerb(inn, verbIn);

    const outLabel = DATA.inspect_outgoing || 'Outgoing';
    const innLabel = DATA.inspect_incoming || 'Incoming';

    // `n.blurb_html` is pre-rendered HTML from inline_md() at build
    // time, so we set innerHTML directly. Internal links inside it are
    // <a class="anchor" data-focus="<id>"> elements; we wire them to
    // setFocus below.
    body.innerHTML = `
      <div class="kind-tag" style="--tagcolor:${k.color}"><span class="swatch"></span><span>${escapeHtml(k.label)}</span></div>
      <h2>${escapeHtml(n.label)}</h2>
      ${n.blurb_html ? `<div class="blurb">${n.blurb_html}</div>` : ''}
      ${renderRelSection(outLabel, out.length, outGroups)}
      ${renderRelSection(innLabel, inn.length, innGroups)}`;
    body.querySelectorAll('.rel[data-id]').forEach(li => li.addEventListener('click', () => setFocus(li.dataset.id)));
    // Inline links inside the blurb (rendered by inline_md at build
    // time) navigate the canvas to the target node when clicked.
    body.querySelectorAll('.anchor[data-focus]').forEach(a => {
      a.addEventListener('click', (ev) => {
        ev.preventDefault();
        const id = a.dataset.focus;
        if (id && NODE[id]) setFocus(id);
      });
    });
  }

  function setFocus(id) {
    state.focus = id;
    if (id) { const h = document.getElementById('hint'); if (h) h.classList.add('gone'); }
    if (id && !state.on.has(NODE[id].kind)) {
      state.on.add(NODE[id].kind);
      renderKinds();
    }
    if (id) state.sim.alpha = Math.max(state.sim.alpha, 0.2);
    renderInspect();
  }
  document.getElementById('inspect-close').addEventListener('click', () => setFocus(null));

  // ---------- buttons ----------
  document.getElementById('reset').addEventListener('click', () => {
    setFocus(null);
    state.pan = {x:0, y:0};
    state.zoom = 1;
    updateZoom();
  });

  // Expose setFocus for the shared modal anchors and ?focus permalink.
  // The wrapper also pans + zooms slightly so the focused node lands
  // visibly left of centre (so the inspect card doesn't cover it).
  window.setFocus = function(id) {
    if (!id) { setFocus(null); return; }
    if (!NODE[id]) return;
    setFocus(id);
    const p = state.nodePos[id];
    if (p) {
      state.pan.x = -(p.x - W/2) - 80;
      state.pan.y = -(p.y - H/2);
      state.zoom = Math.max(state.zoom, 1.15);
      updateZoom();
    }
  };

  // Esc clears focus (the shared baseline closes modals on Esc, but
  // doesn't know to clear focus on a canvas viewer — graph-specific).
  window.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
      const scrim = document.getElementById('modal-scrim');
      if (scrim && scrim.classList.contains('open')) return;  // baseline handled it
      setFocus(null);
    }
  });

  setTimeout(() => { resize(); state.sim.alpha = 1.0; }, 60);
  updateZoom();
})();
"""


# ----------------------------------------------------------------------
# HTML template — assembled at render time from the App-pure shell
# helpers + graph-specific body (canvas, tooltip, hint, kinds, tools).
# ----------------------------------------------------------------------
HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
{head_meta}
<style>
{css}
</style>
</head>
<body>

{dateline}

{top_right}

<canvas id="canvas"></canvas>
<div class="tooltip" id="tooltip"></div>

<div class="hint" id="hint">click any node to <em>focus</em> · drag to reposition · scroll to zoom · drag empty space to pan</div>

<div class="colophon">
  <div class="kinds" id="kinds"></div>
  <div class="tools">
    <span class="zoom" id="zoom-readout">zoom <em>100%</em></span>
    <button id="reset" type="button">Reset focus</button>
  </div>
</div>

{inspect_aside}

{modal_html}

<script type="application/json" id="graph-data">{data_json}</script>
<script>
{baseline_js}
{js}
</script>
</body>
</html>
"""


# ----------------------------------------------------------------------
# Localized UI strings
# ----------------------------------------------------------------------
# Every viewer-emitted user-visible string lives here so non-English forks
# (e.g. AIRC, an Italian foundation) can pass `--lang it` and get the
# chrome + About modal in their working language. The pattern matches
# ai-exposure's STRINGS dict — keep keys consistent across viewers.
#
# Decisions, source citations, and any prose that comes from the agent
# stay in whatever language the agent wrote them; this dict is for the
# scaffolding around them only.
STRINGS = {
    "en": {
        # Chrome
        "analysis_btn": "Analysis",
        "help_btn_label": "What is this map?",
        "inspect_eyebrow": "Inspect",
        "inspect_close_title": "Reset focus",
        "analysis_kicker": "Reading the structure",
        # Inspect panel
        "inspect_outgoing": "Outgoing",
        "inspect_incoming": "Incoming",
        "kind_labels": {
            "unit": "Unit",
            "activity": "Activity",
            "person": "Person",
            "role": "Role",
            "stakeholder": "Stakeholder",
            "commitment": "Commitment",
        },
        # Per-edge-kind verb labels grouped by direction in the inspect
        # panel. OUT = the focused node's relation expressed in the
        # direction it points; IN = the relation as seen from the
        # focused node when others point at it.
        "rel_out": {
            "parent":           "is part of",
            "unit":             "in",
            "performer":        "performed by",
            "head_role":        "led by",
            "holds_role":       "holds",
            "covers":           "responsible for",
            "party_committing": "binds",
            "party_benefiting": "benefits",
            "touches":          "involves",
            "cite":             "cites",
            "link":             "links to",
        },
        "rel_in": {
            "parent":           "contains",
            "unit":             "groups",
            "performer":        "performs",
            "head_role":        "leads",
            "holds_role":       "filled by",
            "covers":           "owned by",
            "party_committing": "bound by",
            "party_benefiting": "benefits from",
            "touches":          "involved in",
            "cite":             "cited by",
            "link":             "linked from",
        },
        # Decision anchor
        "show_on_canvas": "show <em>{label}</em> on the canvas →",
        # Headline (count of decisions surfaced)
        "headline_four": "Four decisions sit on the desk after one pass through the graph.",
        "headline_one": "1 decision surfaces from one pass through the graph.",
        "headline_n": "{n} decisions surface from one pass through the graph.",
        # About modal — body
        "about_lede": (
            "The operational structure as it has been written down: "
            "every node, every typed dependency, no interpretive framework "
            "layered on top."
        ),
        "about_intro": (
            "The picture above is the operational structure of the organisation, "
            "drawn from the cited markdown corpus under <code>org/</code>. Every "
            "dot is a node the corpus declares; every line is a typed dependency "
            "declared in frontmatter (an activity belongs to a unit, a person "
            "performs an activity, a commitment binds a party, ...)."
        ),
        "about_h2_shows": "What this map shows",
        "about_shows_kinds": (
            "<strong>The six load-bearing kinds.</strong> Units (containers of "
            "work), activities (the work that gets done), people (who does it), "
            "roles (named accountability slots), stakeholders (who the work is "
            "for), commitments (the obligations that bind parties together)."
        ),
        "about_shows_pills": (
            "Pills at the bottom-left toggle each kind on or off. Hovering a node "
            "highlights it; clicking focuses it. First-degree neighbours stay "
            "bright, the rest dims, and the Inspect card on the right fills with "
            "the node's incoming and outgoing dependencies, grouped by verb."
        ),
        "about_h2_not_shows": "What it does not show",
        "about_not_shows_corpus": (
            "<strong>Sources, identity, glossary, financial summaries</strong> "
            "are part of the JSON but stripped from this picture. They are "
            "corpus-level metadata (provenance, mission, vocabulary, money "
            "flows), not operational dependencies. Other tools read them; this "
            "view doesn't."
        ),
        "about_not_shows_links": (
            "<strong>Body-markdown links</strong> (a node's prose mentioning "
            "another node by name) are also stripped. They are cross-references "
            "in writing, not dependencies in the structure. Including them "
            "would muddy the load picture without adding signal."
        ),
        "about_h2_read": "How to read it",
        "about_read_sizes": (
            'Bigger circles = more first-degree neighbours in the currently '
            'visible kinds. The size is a directly-readable proxy for "how '
            'much load this node is carrying right now". Toggle a kind off '
            'and sizes recompute to reflect the slimmer picture.'
        ),
        "about_read_controls": (
            "<strong>Drag</strong> a node to reposition it · <strong>scroll</strong> "
            "to zoom · <strong>drag empty space</strong> to pan · <strong>two-finger "
            "pinch</strong> on touch · <strong>?focus=&lt;node-id&gt;</strong> in "
            "the URL is a permalink to a focused view."
        ),
        "about_h2_source": "Where it comes from",
        "about_source": (
            "Unlike the other four bundled playbooks (ai-exposure, value-map, "
            "reshuffle, world-model), <em>graph</em> has no external source "
            "theory: it renders the structure as the structure declares itself, "
            "with no analytical framework layered on top. It is the lightest "
            "read, useful right after the first ingest, before any of the "
            "framed analyses."
        ),
    },
    "it": {
        "analysis_btn": "Analisi",
        "help_btn_label": "Cos'è questa mappa?",
        "inspect_eyebrow": "Ispeziona",
        "inspect_close_title": "Reimposta focus",
        "analysis_kicker": "Lettura della struttura",
        "inspect_outgoing": "In uscita",
        "inspect_incoming": "In entrata",
        "kind_labels": {
            "unit": "Unità",
            "activity": "Attività",
            "person": "Persona",
            "role": "Ruolo",
            "stakeholder": "Stakeholder",
            "commitment": "Commitment",
        },
        "rel_out": {
            "parent":           "appartiene a",
            "unit":             "fa parte di",
            "performer":        "eseguito da",
            "head_role":        "guidato da",
            "holds_role":       "occupa il ruolo",
            "covers":           "responsabile per",
            "party_committing": "vincola",
            "party_benefiting": "beneficia",
            "touches":          "coinvolge",
            "cite":             "cita",
            "link":             "rimanda a",
        },
        "rel_in": {
            "parent":           "contiene",
            "unit":             "raggruppa",
            "performer":        "esegue",
            "head_role":        "guida",
            "holds_role":       "occupato da",
            "covers":           "di responsabilità di",
            "party_committing": "vincolato a",
            "party_benefiting": "beneficia di",
            "touches":          "coinvolto in",
            "cite":             "citato da",
            "link":             "linkato da",
        },
        "show_on_canvas": "mostra <em>{label}</em> sulla mappa →",
        "headline_four": "Quattro decisioni emergono da una lettura del grafo.",
        "headline_one": "1 decisione emerge da una lettura del grafo.",
        "headline_n": "{n} decisioni emergono da una lettura del grafo.",
        "about_lede": (
            "La struttura operativa come è stata scritta: "
            "ogni nodo, ogni dipendenza tipizzata, senza framework "
            "interpretativo sopra."
        ),
        "about_intro": (
            "La figura qui sopra è la struttura operativa dell'organizzazione, "
            "letta dal corpus markdown citato sotto <code>org/</code>. Ogni "
            "punto è un nodo che il corpus dichiara; ogni linea è una "
            "dipendenza tipizzata dichiarata nel frontmatter (un'attività "
            "appartiene a un'unità, una persona svolge un'attività, un "
            "commitment lega due parti, ...)."
        ),
        "about_h2_shows": "Cosa mostra la mappa",
        "about_shows_kinds": (
            "<strong>I sei tipi portanti.</strong> Unità (contenitori di "
            "lavoro), attività (il lavoro che viene fatto), persone (chi lo "
            "fa), ruoli (slot nominati di responsabilità), stakeholder (per "
            "chi viene fatto), commitment (le obbligazioni che legano le "
            "parti)."
        ),
        "about_shows_pills": (
            "I pill in basso a sinistra accendono o spengono ogni tipo. "
            "Passare sopra un nodo lo evidenzia; cliccarlo lo mette a fuoco: "
            "i vicini di primo grado restano accesi, gli altri si "
            "attenuano, e la card Ispeziona a destra si riempie con le "
            "dipendenze in entrata e in uscita del nodo, raggruppate per "
            "verbo."
        ),
        "about_h2_not_shows": "Cosa non mostra",
        "about_not_shows_corpus": (
            "<strong>Sources, identity, glossary, financial summaries</strong> "
            "sono nel JSON ma vengono rimossi da questa figura. Sono "
            "metadati a livello di corpus (provenienza, missione, vocabolario, "
            "flussi finanziari), non dipendenze operative. Altri strumenti "
            "li leggono; questa vista no."
        ),
        "about_not_shows_links": (
            "<strong>I link nel testo dei nodi</strong> (la prosa di un nodo "
            "che ne nomina un altro) sono anch'essi rimossi. Sono "
            "cross-reference di scrittura, non dipendenze nella struttura. "
            "Includerli sporcherebbe la figura del carico senza aggiungere "
            "segnale."
        ),
        "about_h2_read": "Come si legge",
        "about_read_sizes": (
            'Cerchi più grandi = più vicini di primo grado fra i tipi '
            'attualmente visibili. La dimensione è una proxy diretta di '
            '"quanto carico sta portando questo nodo adesso". Spegnere un '
            "tipo e le dimensioni si ricalcolano sulla figura più snella."
        ),
        "about_read_controls": (
            "<strong>Trascina</strong> un nodo per spostarlo · "
            "<strong>scroll</strong> per zoomare · <strong>trascina uno "
            "spazio vuoto</strong> per traslare · <strong>pinch con due "
            "dita</strong> su touch · <strong>?focus=&lt;node-id&gt;</strong> "
            "nell'URL è un permalink a una vista focalizzata."
        ),
        "about_h2_source": "Da dove viene",
        "about_source": (
            "A differenza degli altri quattro playbook (ai-exposure, "
            "value-map, reshuffle, world-model), <em>graph</em> non ha una "
            "fonte teorica esterna: rende la struttura come la struttura si "
            "dichiara, senza framework interpretativo sopra. È la lettura "
            "più leggera, utile subito dopo il primo ingest, prima di "
            "qualsiasi analisi framework-driven."
        ),
    },
}


# ----------------------------------------------------------------------
# Adapter — our schema → the JS data shape
# ----------------------------------------------------------------------
def _adapt_data(d: dict, org_name: str, *, S: dict) -> dict:
    # Filter to load-bearing kinds only. Sources / identity / language /
    # financial summaries belong to other readings (provenance, mission,
    # money flow) — they pollute the dependency picture if rendered here.
    raw_nodes = d.get("nodes", []) or []
    nodes_in = [n for n in raw_nodes if n.get("kind") not in EXCLUDED_KINDS]
    valid_ids = {n["id"] for n in nodes_in}

    # Drop body-markdown link edges (not a dependency, just prose
    # cross-reference) and cite edges (point at sources we just
    # dropped). Also drop any edge whose endpoint disappeared with the
    # node filter.
    raw_edges = d.get("edges", []) or []
    edges_in = [
        e for e in raw_edges
        if e.get("kind") not in EXCLUDED_EDGE_KINDS
        and e.get("from") in valid_ids
        and e.get("to") in valid_ids
    ]

    # Pre-render each node's description (markdown) into HTML at Python
    # side. `inline_md` handles **bold**, *italic*, `code`, and markdown
    # links. Internal links — those whose target is another node id in
    # the corpus — render as <a class="anchor" data-focus="<id>">label</a>
    # so clicking re-focuses the canvas on the linked node, the same
    # behaviour the Analysis modal anchors have. External URLs render as
    # plain <a href>. The pre-rendering pushes the markdown parser to
    # the build side, leaving the JS to set innerHTML on a trusted
    # string.
    node_ids = valid_ids
    def _link_resolver(target: str) -> str | None:
        return target if target in node_ids else None

    js_nodes = []
    for n in nodes_in:
        blurb = (n.get("description") or "").strip()
        js_nodes.append({
            "id":         n["id"],
            "kind":       n["kind"],
            "label":      n.get("label") or n["id"],
            "blurb_html": inline_md(blurb, link_resolver=_link_resolver) if blurb else "",
        })

    js_edges = [
        {"f": e["from"], "t": e["to"], "verb": e["kind"]}
        for e in edges_in
    ]

    kind_labels = S.get("kind_labels", {}) or {}
    present_kinds = {n["kind"] for n in nodes_in}
    js_kinds = []
    for k in KIND_ORDER:
        if k not in present_kinds:
            continue
        js_kinds.append({
            "id":      k,
            "label":   kind_labels.get(k, k),
            "color":   KIND_COLORS.get(k, "#888"),
            "default": k in DEFAULT_ON,
        })
    # Surface unexpected kinds (e.g. a future kind added to build.py
    # before viewer.py learns about it) so they show up rather than
    # vanish silently.
    for k in sorted(present_kinds - set(KIND_ORDER)):
        js_kinds.append({
            "id":      k,
            "label":   kind_labels.get(k, k),
            "color":   "#888",
            "default": False,
        })

    return {
        "org":              org_name,
        "kinds":            js_kinds,
        "nodes":            js_nodes,
        "edges":            js_edges,
        "rel_out":          S.get("rel_out", REL_LABELS_OUT),
        "rel_in":           S.get("rel_in",  REL_LABELS_IN),
        "inspect_outgoing": S.get("inspect_outgoing", "Outgoing"),
        "inspect_incoming": S.get("inspect_incoming", "Incoming"),
    }


def _build_modal_html(d: dict, org_name: str, dated: str, *, S: dict) -> str:
    decisions = d.get("decisions") or []
    if not decisions:
        return ""

    # Build node label + id lookups once.
    node_label = {n["id"]: (n.get("label") or n["id"]) for n in d.get("nodes", []) or []}
    node_ids = set(node_label.keys())

    # Internal-node markdown links written inside decision answers
    # (`[label](node-id)`) get rewritten as focus anchors at render
    # time, the same shape the inspect-panel descriptions use.
    def _link_resolver(target: str) -> str | None:
        return target if target in node_ids else None

    items = []
    for dec in decisions:
        question = (dec.get("question") or "").strip()
        answer_paragraphs = [
            p.strip() for p in (dec.get("answer") or "").split("\n\n") if p.strip()
        ]
        # Per-decision list. Named distinctly from the corpus-wide
        # `node_ids` (line 1141) so the link_resolver closure keeps
        # seeing the full set instead of this slice.
        dec_node_ids = dec.get("node_ids") or []
        anchor_html = ""
        if dec_node_ids:
            first = dec_node_ids[0]
            label = node_label.get(first, first)
            anchor_inner = S["show_on_canvas"].format(label=escape(label))
            anchor_html = (
                f'<span class="anchor" data-focus="{escape(first)}">'
                f'{anchor_inner}'
                f'</span>'
            )
        source = (dec.get("source") or "").strip()
        source_html = f'<p class="source">{escape(source)}</p>' if source else ""
        ps_html = "".join(
            f"<p>{inline_md(p, link_resolver=_link_resolver)}</p>"
            for p in answer_paragraphs
        )
        items.append(
            f'<li><h3>{escape(question)}</h3>{ps_html}{source_html}{anchor_html}</li>'
        )

    # Headline + lede: synthesise a neutral one from the count of
    # decisions. The agent that populates `decisions[]` can override
    # by including a top-level `_headline` / `_lede` in the JSON.
    n = len(decisions)
    if n == 4:
        default_headline = S["headline_four"]
    elif n == 1:
        default_headline = S["headline_one"]
    else:
        default_headline = S["headline_n"].format(n=n)
    headline = d.get("_headline") or default_headline
    lede_text = d.get("_lede") or ""
    lede_html = ""
    if lede_text:
        # Pre-escape; lede in app_pure_modal_html accepts inline HTML
        # for emphasis but we don't have any here — escape to be safe.
        lede_html = escape(lede_text)

    return app_pure_modal_html(
        headline=headline,
        org_name=org_name,
        dated=dated,
        decisions_html="".join(items),
        kicker=S["analysis_kicker"],
        lede=lede_html,
    )


# ----------------------------------------------------------------------
# render_html — the public entry point
# ----------------------------------------------------------------------
def render_html(d: dict, title: str, *, org_name: str = "", lang: str = "en") -> str:
    # Resolution order for the org name in the dateline:
    # 1. --org-name CLI flag (explicit override)
    # 2. JSON `_org` field (populated by build.py from identity/mission.md
    #    frontmatter key `org_name`)
    # 3. The page title — last resort so the chrome never goes blank.
    org = org_name or d.get("_org") or title
    dated = d.get("_dated", "—")
    S = STRINGS.get(lang, STRINGS["en"])

    js_data = _adapt_data(d, org, S=S)
    modal_html = _build_modal_html(d, org, dated, S=S)
    has_decisions = bool(d.get("decisions"))

    # About modal — plain-language explanation of what this picture is,
    # what's been kept and what's been stripped, and how to read it.
    # graph is the only playbook without an external analytical
    # framework — it renders the structure as the structure declares
    # itself. The about-modal makes that explicit.
    n_nodes = len(js_data.get("nodes") or [])
    n_edges = len(js_data.get("edges") or [])
    about_body = f"""
  <p>{S["about_intro"]}</p>

  <h2>{S["about_h2_shows"]}</h2>
  <p>{S["about_shows_kinds"]}</p>
  <p>{S["about_shows_pills"]}</p>

  <h2>{S["about_h2_not_shows"]}</h2>
  <p>{S["about_not_shows_corpus"]}</p>
  <p>{S["about_not_shows_links"]}</p>

  <h2>{S["about_h2_read"]}</h2>
  <p>{S["about_read_sizes"]}</p>
  <p>{S["about_read_controls"]}</p>

  <h2>{S["about_h2_source"]}</h2>
  <p>{S["about_source"]}</p>
"""
    about_modal_html_str = app_pure_about_modal_html(
        kicker=f"№ {n_nodes:02d} · graph",
        headline=org,
        lede=S["about_lede"],
        body_html=about_body,
    )

    # The page <title> reads "<org> — graph" so the browser tab matches
    # the dateline. The CLI's --title flag still wins if explicitly set
    # (the default sentinel "The whole graph" is checked here so we can
    # tell apart "user passed nothing" from "user passed a custom title").
    page_title = title if title and title != "The whole graph" else f"{org} — graph"
    return HTML_TEMPLATE.format(
        head_meta=app_pure_head_meta(page_title),
        css=app_pure_css(layout="canvas") + EXTRA_CSS,
        dateline=app_pure_dateline_html(org),
        top_right=app_pure_top_right_html(
            dated,
            show_analysis=has_decisions,
            show_help=True,
            analysis_label=S["analysis_btn"],
            help_label=S["help_btn_label"],
        ),
        inspect_aside=app_pure_inspect_aside_html(
            eyebrow_label=S["inspect_eyebrow"],
            close_title=S["inspect_close_title"],
        ),
        modal_html=modal_html + about_modal_html_str,
        # Escape "</" inside embedded JSON so a stray "</script>" in
        # the data cannot close the wrapping <script> tag. JSON allows
        # "\/" as an escape for "/", so the parser still gets clean data.
        data_json=json.dumps(js_data, ensure_ascii=False).replace("</", "<\\/"),
        baseline_js=app_pure_baseline_js(),
        js=JS,
    )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Render a graph JSON as a fullscreen app.")
    parser.add_argument("--map", required=True, help="Graph JSON path")
    parser.add_argument("--html", required=True, help="Output HTML path")
    parser.add_argument("--title", default="The whole graph", help="Page title")
    parser.add_argument("--org-name", default="", help="Organization name for the masthead")
    parser.add_argument(
        "--lang",
        default="en",
        choices=sorted(STRINGS.keys()),
        help="Language for the chrome and About modal (en, it). Default en.",
    )
    parser.add_argument(
        "--decisions",
        help="Optional JSON list merged into the map under 'decisions[]' before render.",
    )
    args = parser.parse_args()

    d = json.loads(Path(args.map).read_text(encoding="utf-8"))
    if args.decisions:
        d["decisions"] = json.loads(Path(args.decisions).read_text(encoding="utf-8"))

    # Pass the CLI override through verbatim (may be empty). render_html
    # resolves the dateline org name in this order: --org-name > JSON
    # `_org` > page title. Don't shortcut to title here.
    html = render_html(d, args.title, org_name=args.org_name, lang=args.lang)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"Wrote {Path(args.html).resolve()} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
