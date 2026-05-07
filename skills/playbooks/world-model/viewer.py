#!/usr/bin/env python3
"""
world-model / viewer.py — Render a world-model JSON as interactive HTML.

The visualization is a layered stack: stakeholders at the top, interfaces
below, intelligence layer, world model, capabilities at the bottom. A
side panel shows the failure-signal roadmap. Click any element for full
detail.

Output is for a reader with no prior knowledge of the source framework
or of the organization. Every term is defined inline; every number
declares its scale. Style charter applies.

Usage:
    python3 viewer.py --map <world-model.json> --html <out.html>
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
/* world-model viewer — Play New design (unified with value-map and ai-exposure).
   Pure white surface, editorial typography, hairlines, single accent.
   One uniform container width applied to every block on the page. */

:root {
  /* Stack layers + moat / commodity — data-viz palette mirror, used
     only as light tint accents on the layer heads. */
  --moat:                       var(--ds-coral);
  --commodity:                  var(--fg-hairline);
  --layer-stakeholder-accent:   var(--fg);
  --layer-interface-accent:     var(--ds-slate);
  --layer-intelligence-accent:  var(--ds-lilac);
  --layer-worldmodel-accent:    var(--ds-sage);
  --layer-capability-accent:    var(--ds-sand);
}

body { background: #FFFFFF; color: var(--fg); }

/* One container width, applied uniformly to every block on the page. */
.container { max-width: 1240px; margin: 0 auto; padding: 80px 40px 96px; }
@media (max-width: 900px) { .container { padding: 56px 24px 80px; } }

/* Editorial text columns at the start and end of the page sit in a
   centered narrower column inside the 1240px container; data-heavy
   blocks (stack, capability grid, signals) span the full container. */
header { max-width: 820px; margin: 0 auto 48px; }
header .eyebrow { font-family: var(--font-display); font-size: 0.74rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); margin-bottom: 16px; }
header h1 { font-family: var(--font-display); font-size: clamp(1.9rem, 3.5vw, 2.6rem); font-weight: 500; letter-spacing: -0.025em; line-height: 1.1; margin: 0 0 16px; color: var(--fg); }
header .lead { font-size: 1.0rem; color: var(--fg-muted); line-height: 1.65; margin: 0; }

.intro { max-width: 820px; margin: 0 auto 56px; }
.intro h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 16px; }
.intro p { font-size: 0.95rem; line-height: 1.7; margin: 0 0 14px; color: var(--fg); }
.intro p strong { font-weight: 500; }
.intro .pull { padding: 14px 0 14px 18px; margin: 22px 0; font-size: 1.0rem; color: var(--fg); border-left: 2px solid var(--fg); line-height: 1.65; }

/* Stack — vertical flow of layer blocks, each in the same 820px
   centered column as the rest of the page so nothing escapes the
   editorial grid. */
.stack { max-width: 820px; margin: 0 auto; display: flex; flex-direction: column; }
.stack-layer { padding: 36px 0 36px; border-top: 1px solid var(--fg-hairline); }
.stack-layer .layer-head { margin-bottom: 18px; }
.stack-layer .layer-name { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; padding-left: 14px; border-left: 2px solid var(--commodity); margin-bottom: 10px; }
.stack-layer.layer-stakeholders   .layer-name { border-left-color: var(--layer-stakeholder-accent); }
.stack-layer.layer-interfaces     .layer-name { border-left-color: var(--layer-interface-accent); }
.stack-layer.layer-intelligence   .layer-name { border-left-color: var(--layer-intelligence-accent); }
.stack-layer.layer-worldmodel     .layer-name { border-left-color: var(--layer-worldmodel-accent); }
.stack-layer.layer-capabilities   .layer-name { border-left-color: var(--layer-capability-accent); }
.stack-layer .layer-hint { font-size: 0.92rem; color: var(--fg-muted); line-height: 1.65; padding-left: 16px; }
.stack-layer .layer-body { }
.layer-explainer { font-size: 0.95rem; color: var(--fg); line-height: 1.7; margin: 0 0 12px; max-width: 720px; }
.layer-explainer strong { font-weight: 500; }
.layer-explainer em { font-style: italic; color: var(--fg); }
.il-section-hint { font-size: 0.85rem; color: var(--fg-muted); margin-bottom: 12px; line-height: 1.6; max-width: 720px; }

/* All clickable items render as cards with a full hairline border.
   Hover signal is uniform across the page: the border darkens to fg.
   The moat accent on capability cards is the full border in the
   data-viz coral, not just a left rule. */
.stakeholder-row, .interface-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 14px; }
.stakeholder { background: transparent; color: var(--fg); padding: 7px 14px; border: 1px solid var(--fg-hairline); border-radius: 4px; font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: border-color 0.15s; }
.stakeholder:hover { border-color: var(--fg); }

.interface { background: transparent; border: 1px solid var(--fg-hairline); border-radius: 4px; padding: 7px 14px; font-size: 0.85rem; cursor: pointer; color: var(--fg); transition: border-color 0.15s; }
.interface:hover { border-color: var(--fg); }

/* Intelligence layer / world model — two columns side-by-side inside
   the 820px column, because each layer is a comparison: held-by-
   people-today vs could-be-held-by-systems on the intelligence layer,
   about-itself vs about-the-people-it-serves on the world model. The
   contrast is the point. */
.il-grid, .wm-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 14px; }
@media (max-width: 720px) { .il-grid, .wm-grid { grid-template-columns: 1fr; gap: 16px; } }
.il-section .il-title, .wm-section .wm-title { font-family: var(--font-display); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); margin-bottom: 10px; font-weight: 500; }
.il-card, .wm-card { padding: 14px 16px; margin-bottom: 10px; font-size: 0.88rem; border: 1px solid var(--fg-hairline); border-radius: 4px; transition: border-color 0.15s; cursor: pointer; }
.il-card:hover, .wm-card:hover { border-color: var(--fg); }
.il-card.potential { border-color: var(--fg); }
.il-card .trigger, .wm-card .label { font-weight: 500; margin-bottom: 4px; color: var(--fg); }
.il-card .meta, .wm-card .meta { font-size: 0.78rem; color: var(--fg-muted); }

/* Capability cards — grid that fits inside the 820px column. */
.cap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin-top: 14px; }
.cap-card { padding: 14px 16px; cursor: pointer; transition: border-color 0.15s; border: 1px solid var(--fg-hairline); border-radius: 4px; }
.cap-card.moat { border-color: var(--moat); }
.cap-card:hover { border-color: var(--fg); }
.cap-card.moat:hover { border-color: var(--moat); }
.cap-card .name { font-weight: 500; font-size: 0.95rem; font-family: var(--font-display); letter-spacing: -0.01em; margin-bottom: 6px; color: var(--fg); }
.cap-card .desc { font-size: 0.85rem; color: var(--fg-muted); line-height: 1.55; margin-bottom: 10px; }
.cap-card .meta { display: flex; flex-wrap: wrap; gap: 6px; font-size: 0.7rem; }
.cap-card .pill { background: transparent; border: 1px solid var(--fg-hairline); padding: 1px 8px; border-radius: 999px; color: var(--fg-muted); font-weight: 500; letter-spacing: 0.02em; }
.cap-card .pill.moat { background: var(--moat); color: var(--fg); border-color: var(--moat); }
.cap-card .pill.commodity { color: var(--fg-muted); }

/* Shared principle — editorial pull, no filled background. Centered. */
.principle-block { max-width: 820px; margin: 56px auto; padding: 18px 0 18px 18px; border-left: 2px solid var(--moat); }
.principle-block .label { font-family: var(--font-display); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.10em; color: var(--ds-coral); font-weight: 600; margin-bottom: 8px; }
.principle-block .text { font-size: 0.95rem; color: var(--fg); line-height: 1.65; }

/* Failure signals — same 820px column. Cards stack vertically. */
.signals-block { max-width: 820px; margin: 56px auto 0; padding-top: 36px; border-top: 1px solid var(--fg-hairline); }
.signals-block h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 16px; }
.signals-block > p.layer-explainer { margin: 0 0 24px; }
.signals-grid { display: flex; flex-direction: column; gap: 12px; }
.signal-card { padding: 14px 16px; cursor: pointer; transition: border-color 0.15s; border: 1px solid var(--fg-hairline); border-radius: 4px; }
.signal-card:hover { border-color: var(--fg); }
.signal-card .trigger { font-weight: 500; font-size: 0.95rem; margin-bottom: 6px; color: var(--fg); }
.signal-card .missing { font-size: 0.8rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }

/* Decisions section — centered editorial column, same as value-map and ai-exposure. */
.section { max-width: 820px; margin: 96px auto 0; padding-top: 40px; border-top: 1px solid var(--fg-hairline); }
.section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 20px; }
.section p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; max-width: 720px; }
.section .lead { font-size: 0.95rem; color: var(--fg-muted); line-height: 1.65; max-width: 720px; margin: 0 0 28px; }

.decision { margin-bottom: 32px; }
.decision .question { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; color: var(--fg); margin: 0 0 8px; letter-spacing: -0.01em; }
.decision .answer { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 6px; max-width: 720px; }
.decision .source { font-size: 0.78rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }

/* Popover — same pattern as value-map and ai-exposure. */
.popover { position: absolute; display: none; max-width: 380px; min-width: 240px; padding: 14px 18px 16px; background: #FFFFFF; border: 1px solid var(--fg-hairline); border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); z-index: 100; animation: pn-pop 0.18s ease; }
.popover.open { display: block; }
.popover .close { position: absolute; top: 6px; right: 8px; background: transparent; border: 0; cursor: pointer; font-size: 1.1rem; color: var(--fg-muted); padding: 0; line-height: 1; }
.popover .close:hover { color: var(--fg); }
.popover .eyebrow { font-family: var(--font-display); font-size: 0.62rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px; color: var(--fg-muted); }
.popover .eyebrow.moat { color: var(--ds-coral); }
.popover h3 { font-family: var(--font-display); font-size: 1.0rem; font-weight: 500; letter-spacing: -0.015em; margin: 0 0 8px; line-height: 1.25; color: var(--fg); padding-right: 18px; }
.popover .desc { font-size: 0.85rem; line-height: 1.55; color: var(--fg); margin: 0 0 10px; }
.popover .section-label { font-family: var(--font-display); font-size: 0.62rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; font-weight: 500; margin-top: 12px; margin-bottom: 4px; }
.popover .contract { padding: 8px 10px; background: var(--bg-alt); border-radius: 3px; margin-top: 6px; }
.popover .contract dl { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 4px 12px; font-size: 0.78rem; }
.popover .contract dt { color: var(--fg-muted); margin: 0; }
.popover .contract dd { margin: 0; color: var(--fg); }
.popover .pill-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.popover .pill { background: transparent; border: 1px solid var(--fg-hairline); padding: 1px 8px; border-radius: 999px; font-size: 0.7rem; color: var(--fg); }
.popover .citation { font-size: 0.7rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; padding-top: 8px; margin-top: 10px; border-top: 1px solid var(--fg-hairline); }
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title} · world model</title>
<style>{css}</style>
</head>
<body>
  <div class="container">
    <header>
      <div class="eyebrow">world model</div>
      <h1>{title}</h1>
      <p class="lead">A read of how this organization is structured underneath the org-chart — the people it serves, where it meets them, how it composes a response, what it knows, and what it can actually do.</p>
    </header>

    <div class="intro">
      <p>Behind every org-chart there is a different structure: who the org serves, the surfaces where it reaches them, the way requests get composed into responses, the things the org knows about itself and its world, and the atomic things it can do. The map below reads each layer for this organization and surfaces the pieces that aren't there yet.</p>
      <div class="pull">The bottom layers are where the value compounds. The top layers are where it gets delivered. The work that lives between them — picking the right things to do and connecting them — is where the cost of keeping everyone aligned shows up today, paid in meeting hours and hand-off attrition. Replacing it with shared knowledge is the move that ages well.</div>
    </div>

    <div class="stack">

      <div class="stack-layer layer-stakeholders">
        <div class="layer-head">
          <div class="layer-name">Stakeholders</div>
          <div class="layer-hint">Who the organization serves and who serves it back. Every type both uses something the org offers and contributes something in return — the contribution makes the org better at serving the next person of the same type.</div>
        </div>
        <div class="layer-body">
          <div class="stakeholder-row">{stakeholders_html}</div>
        </div>
      </div>

      <div class="stack-layer layer-interfaces">
        <div class="layer-head">
          <div class="layer-name">Interfaces</div>
          <div class="layer-hint">The surfaces where the org meets people — a website, an app, a call, an event, a hand-off. Where work gets delivered, not where its value is made.</div>
        </div>
        <div class="layer-body">
          <div class="interface-row">{interfaces_html}</div>
        </div>
      </div>

      <div class="stack-layer layer-intelligence">
        <div class="layer-head">
          <div class="layer-name">Intelligence layer</div>
          <div class="layer-hint">When a request needs more than one thing the org does, the response is composed: the right things, in the right order. Today most of this lives in meetings and hand-offs. The right column is where it could live in shared systems instead.</div>
        </div>
        <div class="layer-body">
          <div class="il-grid">
            <div class="il-section">
              <div class="il-title">Held together by people today ({n_current_compositions})</div>
              <div class="il-section-hint">The compositions the org already runs, paid for in meeting hours and hand-off attrition. Each one is a candidate to move into shared systems.</div>
              {current_compositions_html}
            </div>
            <div class="il-section">
              <div class="il-title">Could be held together by systems ({n_potential_compositions})</div>
              <div class="il-section-hint">The compositions that would run automatically if the org's shared knowledge were richer. Long-term moves; each names the precondition that has to land first.</div>
              {potential_compositions_html}
            </div>
          </div>
        </div>
      </div>

      <div class="stack-layer layer-worldmodel">
        <div class="layer-head">
          <div class="layer-name">World model</div>
          <div class="layer-hint">What the organization knows about itself and the people it serves. The most honest signal is observed behaviour, not declared opinion.</div>
        </div>
        <div class="layer-body">
          <div class="wm-grid">
            <div class="wm-section">
              <div class="wm-title">About itself — overall maturity: {company_maturity}</div>
              {company_observations_html}
            </div>
            <div class="wm-section">
              <div class="wm-title">About the people it serves — {customer_unified_label}</div>
              {customer_observations_html}
            </div>
          </div>
        </div>
      </div>

      <div class="stack-layer layer-capabilities">
        <div class="layer-head">
          <div class="layer-name">Capabilities</div>
          <div class="layer-hint">The atomic things the org can actually do. Each one is a function: declared input, structured output, service targets, an invocation pattern. Cards framed in <strong style="color: #c47558;">coral</strong> are differentiated for this org — hard to acquire, hard to copy. Cards in plain hairline are necessary but standard across the category.</div>
        </div>
        <div class="layer-body">
          <div class="cap-grid">{capabilities_html}</div>
        </div>
      </div>

    </div>

    <div class="principle-block">
      <div class="label">The shared principle</div>
      <div class="text">Replace hierarchical information routing with a system that accumulates knowledge over time. Every call enriches the shared knowledge; richer knowledge composes better responses; better responses make the next call worth more. A loop that compounds.</div>
    </div>

    <div class="signals-block">
      <h2>What to build next</h2>
      <p class="layer-explainer">Each card below names a request the organization would already try to handle, and where the response would fall short because one needed piece of the chain isn't there yet. Each one is a candidate to build. The list comes from the demand the structure already produces — not from a three-year plan made at the top.</p>
      <div class="signals-grid">{signals_html}</div>
    </div>

    {decisions_section}
  </div>

  <div class="popover" id="popover">
    <button class="close" id="popover-close" aria-label="Close">×</button>
    <div id="popover-body"></div>
  </div>

<script>
const CAPABILITIES = {capabilities_json};
const STAKEHOLDERS_BY_TYPE = {stakeholders_index_json};
const INTERFACES = {interfaces_json};
const SIGNALS = {signals_json};
const COMPOSITIONS_CURRENT = {current_compositions_json};
const COMPOSITIONS_POTENTIAL = {potential_compositions_json};
const COMPANY_OBSERVATIONS = {company_observations_json};

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }})[c]);
}}

function pillList(items, cls) {{
  if (!items || !items.length) return '<span style="color: var(--fg-muted); font-size: 0.78rem;">none</span>';
  return '<div class="pill-row">' + items.map(i => `<span class="pill ${{cls||''}}">${{escapeHtml(i)}}</span>`).join('') + '</div>';
}}

function renderCapabilityPopover(c) {{
  const eyebrow = c.moat_grade === 'moat'
    ? '<div class="eyebrow moat">capability · differentiated</div>'
    : '<div class="eyebrow">capability · standard</div>';
  let html = eyebrow;
  html += `<h3>${{escapeHtml(c.name)}}</h3>`;
  if (c.description) html += `<div class="desc">${{escapeHtml(c.description)}}</div>`;
  html += `<div class="section-label">Contract</div>`;
  html += `<div class="contract"><dl>`;
  if (c.input)              html += `<dt>Takes</dt><dd>${{escapeHtml(c.input)}}</dd>`;
  if (c.output)             html += `<dt>Returns</dt><dd>${{escapeHtml(c.output)}}</dd>`;
  if (c.invocation_modality) html += `<dt>How called</dt><dd>${{escapeHtml(c.invocation_modality)}}</dd>`;
  html += `</dl></div>`;
  if (c.is_callable_by && c.is_callable_by.length) {{
    html += `<div class="section-label">Can be called by</div>`;
    html += pillList(c.is_callable_by);
  }}
  if (c.current_owners && c.current_owners.length) {{
    html += `<div class="section-label">Held today by</div>`;
    html += pillList(c.current_owners);
  }}
  if (c.moat_rationale) {{
    html += `<div class="section-label">${{c.moat_grade === 'moat' ? 'Why differentiated' : 'Why standard'}}</div>`;
    html += `<div class="desc">${{escapeHtml(c.moat_rationale)}}</div>`;
  }}
  if (c._structure_id) {{
    html += `<div class="citation">${{escapeHtml(c._structure_id)}}</div>`;
  }}
  return html;
}}

function renderStakeholderPopover(stype) {{
  const data = STAKEHOLDERS_BY_TYPE[stype] || {{}};
  let html = `<div class="eyebrow">stakeholder</div>`;
  html += `<h3>${{escapeHtml(stype)}}</h3>`;
  if (data.description) html += `<div class="desc">${{escapeHtml(data.description)}}</div>`;
  if (data.what_they_get_from_org) {{
    html += `<div class="section-label">What they get from the org</div>`;
    html += `<div class="desc">${{escapeHtml(data.what_they_get_from_org)}}</div>`;
  }}
  if (data.what_they_contribute_back) {{
    html += `<div class="section-label">What they give back</div>`;
    html += `<div class="desc">${{escapeHtml(data.what_they_contribute_back)}}</div>`;
  }}
  if (data.honest_signal) {{
    html += `<div class="section-label">Most honest signal observed</div>`;
    html += `<div class="desc">${{escapeHtml(data.honest_signal)}}</div>`;
  }}
  if (data.fragmentation) {{
    html += `<div class="section-label">Where the picture is fragmented</div>`;
    html += `<div class="desc">${{escapeHtml(data.fragmentation)}}</div>`;
  }}
  const invoked = CAPABILITIES.filter(c => (c.is_callable_by || []).includes(stype));
  if (invoked.length) {{
    html += `<div class="section-label">What they can call</div>`;
    html += pillList(invoked.map(c => c.name));
  }}
  return html;
}}

function renderInterfacePopover(idx) {{
  const ifc = INTERFACES[idx];
  if (!ifc) return '';
  let html = `<div class="eyebrow">interface</div>`;
  html += `<h3>${{escapeHtml(ifc.name)}}</h3>`;
  if (ifc.description) html += `<div class="desc">${{escapeHtml(ifc.description)}}</div>`;
  if (ifc.surfaces_capabilities && ifc.surfaces_capabilities.length) {{
    html += `<div class="section-label">Capabilities it carries</div>`;
    html += pillList(ifc.surfaces_capabilities);
  }}
  if (ifc._structure_id || ifc._structure) {{
    html += `<div class="citation">${{escapeHtml(ifc._structure_id || ifc._structure)}}</div>`;
  }}
  return html;
}}

function renderSignalPopover(idx) {{
  const s = SIGNALS[idx];
  if (!s) return '';
  let html = `<div class="eyebrow">a piece to build</div>`;
  html += `<h3>${{escapeHtml(s.trigger || '')}}</h3>`;
  html += `<div class="section-label">What's missing</div>`;
  html += `<div class="desc">${{escapeHtml(s.missing_capability || '')}}</div>`;
  if (s.composition_attempted) {{
    html += `<div class="section-label">What the org would try to do</div>`;
    if (Array.isArray(s.composition_attempted)) html += pillList(s.composition_attempted);
    else html += `<div class="desc">${{escapeHtml(s.composition_attempted)}}</div>`;
  }}
  if (s.what_would_be_needed) {{
    html += `<div class="section-label">What it would take to build it</div>`;
    html += `<div class="desc">${{escapeHtml(s.what_would_be_needed)}}</div>`;
  }}
  if (s.structure_evidence) {{
    html += `<div class="citation">${{escapeHtml(s.structure_evidence)}}</div>`;
  }}
  return html;
}}

function renderCompositionPopover(idx, kind) {{
  const c = (kind === 'current' ? COMPOSITIONS_CURRENT : COMPOSITIONS_POTENTIAL)[idx];
  if (!c) return '';
  const eb = kind === 'current' ? 'held together by people today' : 'could be held together by systems';
  let html = `<div class="eyebrow">${{eb}}</div>`;
  html += `<h3>${{escapeHtml(c.trigger || '')}}</h3>`;
  if (c.description) html += `<div class="desc">${{escapeHtml(c.description)}}</div>`;
  const caps = c.capabilities_composed || c.capabilities || [];
  if (caps.length) {{
    html += `<div class="section-label">What gets composed</div>`;
    html += pillList(caps);
  }}
  if (c.failure_modes) {{
    html += `<div class="section-label">What breaks today</div>`;
    html += `<div class="desc">${{escapeHtml(c.failure_modes)}}</div>`;
  }}
  if (c.precondition) {{
    html += `<div class="section-label">What has to land first</div>`;
    html += `<div class="desc">${{escapeHtml(c.precondition)}}</div>`;
  }}
  return html;
}}

function renderCompanyObservationPopover(idx) {{
  const o = COMPANY_OBSERVATIONS[idx];
  if (!o) return '';
  let html = `<div class="eyebrow">what the org knows about itself</div>`;
  html += `<h3>${{escapeHtml(o.dimension || '')}}</h3>`;
  if (o.lives_in) {{
    html += `<div class="section-label">Where this knowledge lives today</div>`;
    html += `<div class="desc">${{escapeHtml(o.lives_in)}}</div>`;
  }}
  if (o.maturity) {{
    html += `<div class="section-label">How mature the picture is</div>`;
    html += `<div class="desc">${{escapeHtml(o.maturity)}}</div>`;
  }}
  if (o.gaps) {{
    html += `<div class="section-label">What's missing</div>`;
    html += `<div class="desc">${{escapeHtml(o.gaps)}}</div>`;
  }}
  return html;
}}

// Popover positioning + click handlers — same shape as value-map and ai-exposure.
const popoverEl   = document.getElementById('popover');
const popoverBody = document.getElementById('popover-body');

function showPopover(html, anchorRect) {{
  // Open the popover BELOW the clicked element, centered horizontally
  // on it. If there's not enough room below, flip to above. Always
  // clamped inside the viewport. This keeps the popover predictably
  // close to what was clicked, instead of jumping to the left or right
  // margin depending on screen width.
  popoverBody.innerHTML = html;
  const margin = 12;
  popoverEl.style.left = '0px';
  popoverEl.style.top  = '0px';
  popoverEl.classList.add('open');
  const r = popoverEl.getBoundingClientRect();
  const anchorCenterX = (anchorRect.left + anchorRect.right) / 2;
  const viewportRight  = window.scrollX + window.innerWidth;
  const viewportBottom = window.scrollY + window.innerHeight;
  // Horizontal: centered on anchor, clamped to viewport.
  let x = anchorCenterX - r.width / 2;
  if (x + r.width > viewportRight - margin) x = viewportRight - r.width - margin;
  if (x < window.scrollX + margin) x = window.scrollX + margin;
  // Vertical: below the anchor by default; if no room, flip above.
  let y = anchorRect.bottom + margin;
  if (y + r.height > viewportBottom - margin) {{
    const above = anchorRect.top - margin - r.height;
    if (above >= window.scrollY + margin) y = above;
    else y = viewportBottom - r.height - margin;  // last resort: bottom-clamp
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
    if (n.classList && n.classList.contains('cap-card')) {{
      const c = CAPABILITIES.find(x => x.name === n.dataset.name);
      if (c) showFor(n, renderCapabilityPopover(c));
      return;
    }}
    if (n.classList && n.classList.contains('stakeholder')) {{
      showFor(n, renderStakeholderPopover(n.dataset.type));
      return;
    }}
    if (n.classList && n.classList.contains('interface')) {{
      showFor(n, renderInterfacePopover(parseInt(n.dataset.idx, 10)));
      return;
    }}
    if (n.classList && n.classList.contains('signal-card')) {{
      showFor(n, renderSignalPopover(parseInt(n.dataset.idx, 10)));
      return;
    }}
    if (n.classList && n.classList.contains('il-card')) {{
      showFor(n, renderCompositionPopover(parseInt(n.dataset.idx, 10), n.dataset.kind));
      return;
    }}
    if (n.classList && n.classList.contains('wm-card')) {{
      if (n.dataset.wmKind === 'company') {{
        showFor(n, renderCompanyObservationPopover(parseInt(n.dataset.idx, 10)));
      }} else if (n.dataset.wmKind === 'customer') {{
        // Customer-side wm-cards are stakeholder summaries — re-use the
        // stakeholder popover so the leader sees the full picture.
        showFor(n, renderStakeholderPopover(n.dataset.type));
      }}
      return;
    }}
    if (n.id === 'popover') return;  // click inside the popover, leave it open
    n = n.parentNode;
  }}
  hidePopover();
}}, true);

document.getElementById('popover-close').addEventListener('click', hidePopover);
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') hidePopover(); }});
</script>
</body>
</html>"""


def render_html(d: dict, title: str) -> str:
    caps = d.get("capabilities", [])
    interfaces = d.get("interfaces", [])
    signals = d.get("failure_signals", [])
    il = d.get("intelligence_layer", {}) or {}
    cur_comp = il.get("current_human_compositions", []) or []
    pot_comp = il.get("potential_compositions", []) or []
    company = d.get("world_model_company", {}) or {}
    customer = d.get("world_model_customer", {}) or {}

    # Stakeholder set: union of is_callable_by across capabilities + customer side
    stakeholder_types: list[str] = []
    seen: set[str] = set()
    for c in caps:
        for t in c.get("is_callable_by", []) or []:
            if t not in seen:
                stakeholder_types.append(t)
                seen.add(t)
    for s in customer.get("by_stakeholder", []) or []:
        t = s.get("type", "")
        if t and t not in seen:
            stakeholder_types.append(t)
            seen.add(t)

    # Stakeholder index for modal
    stakeholders_index = {}
    for s in customer.get("by_stakeholder", []) or []:
        stakeholders_index[s.get("type", "")] = s

    stakeholders_html = "\n".join(
        f'<div class="stakeholder" data-type="{escape(t)}">{escape(t)}</div>'
        for t in stakeholder_types
    )

    empty_pill = '<span style="color: var(--fg-muted); font-size: 0.82rem;">— none mapped yet</span>'

    interfaces_html = "\n".join(
        f'<div class="interface" data-idx="{i}">{escape(ifc.get("name", ""))}</div>'
        for i, ifc in enumerate(interfaces)
    ) or empty_pill

    def comp_card(c: dict, idx: int, kind: str) -> str:
        trigger = c.get("trigger", "")
        cls = "il-card" + (" potential" if kind == "potential" else "")
        caps_list = c.get("capabilities_composed") or c.get("capabilities") or []
        caps_meta = " · ".join(caps_list[:3]) + ("…" if len(caps_list) > 3 else "")
        return (
            f'<div class="{cls}" data-idx="{idx}" data-kind="{kind}">'
            f'<div class="trigger">{escape(trigger)}</div>'
            f'<div class="meta">{escape(caps_meta)}</div>'
            f'</div>'
        )

    current_compositions_html   = "\n".join(comp_card(c, i, "current")   for i, c in enumerate(cur_comp)) or empty_pill
    potential_compositions_html = "\n".join(comp_card(c, i, "potential") for i, c in enumerate(pot_comp)) or empty_pill

    company_observations_html = "\n".join(
        f'<div class="wm-card" data-wm-kind="company" data-idx="{i}">'
        f'<div class="label">{escape(o.get("dimension", ""))}</div>'
        f'<div class="meta">lives in {escape(o.get("lives_in", "?"))} · {escape(o.get("maturity", "?"))} maturity</div></div>'
        for i, o in enumerate(company.get("observations", []) or [])
    ) or empty_pill

    customer_observations_html = "\n".join(
        f'<div class="wm-card" data-wm-kind="customer" data-type="{escape(s.get("type", ""))}">'
        f'<div class="label">{escape(s.get("type", ""))}</div>'
        f'<div class="meta">honest signal: {escape((s.get("honest_signal") or "?")[:70])}{"…" if len(s.get("honest_signal","")) > 70 else ""} · '
        f'{escape(s.get("current_maturity", "?"))} maturity</div></div>'
        for s in (customer.get("by_stakeholder", []) or [])
    ) or empty_pill

    company_maturity = company.get("overall_maturity", "?")
    customer_unified = customer.get("is_unified", False)
    customer_unified_label = "one unified picture" if customer_unified else "fragmented across teams"

    def cap_card(c: dict) -> str:
        moat = c.get("moat_grade", "")
        cls = "cap-card" + (" moat" if moat == "moat" else "")
        owners = c.get("current_owners") or []
        owners_pill = f'<span class="pill">{escape(", ".join(owners[:2]))}{"…" if len(owners) > 2 else ""}</span>' if owners else ""
        moat_label = "differentiated" if moat == "moat" else ("standard" if moat == "commodity" else "")
        moat_pill = f'<span class="pill {moat}">{escape(moat_label)}</span>' if moat_label else ""
        return (
            f'<div class="{cls}" data-name="{escape(c.get("name", ""))}">'
            f'<div class="name">{escape(c.get("name", ""))}</div>'
            f'<div class="desc">{escape(c.get("description", ""))}</div>'
            f'<div class="meta">{moat_pill}{owners_pill}</div>'
            f'</div>'
        )

    capabilities_html = "\n".join(cap_card(c) for c in caps) or '<span style="color: var(--fg-muted);">— no capabilities identified yet</span>'

    def signal_card(s: dict, idx: int) -> str:
        return (
            f'<div class="signal-card" data-idx="{idx}">'
            f'<div class="trigger">{escape(s.get("trigger", ""))}</div>'
            f'<div class="missing">missing: {escape(s.get("missing_capability", ""))}</div>'
            f'</div>'
        )

    signals_html = "\n".join(signal_card(s, i) for i, s in enumerate(signals)) or '<span style="color: var(--fg-muted); font-size: 0.85rem;">— no failure-signals identified yet; the emerging roadmap is empty</span>'

    # Decisions section — same shape as value-map and ai-exposure.
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
            '<p class="lead">The leader-facing reading of the map: what the layers say about what to build, what to reorganize, what to keep human, and what to let compound.</p>'
            + "".join(items)
            + '</div>'
        )

    # Conceptual frame diagram, inline SVG, English plain-language labels.
    frame_diagram_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 540" style="font-family: ui-sans-serif, system-ui, sans-serif;">
  <defs>
    <marker id="arr-up" viewBox="0 0 10 10" refX="5" refY="9" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 0 0 L 5 9 L 10 0 Z" fill="#6b6b6b" transform="rotate(180 5 5)"/>
    </marker>
  </defs>
  <text x="360" y="22" text-anchor="middle" font-size="11" fill="#6b6b6b" font-weight="600" letter-spacing="1.2px">FIVE LAYERS, BOTTOM-UP</text>
  <rect x="160" y="48" width="400" height="56" rx="6" fill="#1a1a1a" stroke="#1a1a1a"/>
  <text x="360" y="70" text-anchor="middle" font-size="14" fill="#FFFFFF" font-weight="600">Stakeholders</text>
  <text x="360" y="90" text-anchor="middle" font-size="11" fill="#cccccc">who the org serves and who serves it back</text>
  <line x1="360" y1="130" x2="360" y2="108" stroke="#6b6b6b" stroke-width="1.5" marker-end="url(#arr-up)"/>
  <rect x="160" y="130" width="400" height="56" rx="6" fill="#dde7f8" stroke="#9ab1d8"/>
  <text x="360" y="152" text-anchor="middle" font-size="14" fill="#1a1a1a" font-weight="600">Interfaces</text>
  <text x="360" y="172" text-anchor="middle" font-size="11" fill="#5a5a5a">where the org meets people</text>
  <line x1="360" y1="212" x2="360" y2="190" stroke="#6b6b6b" stroke-width="1.5" marker-end="url(#arr-up)"/>
  <rect x="160" y="212" width="400" height="56" rx="6" fill="#e1ddec" stroke="#a59cc4"/>
  <text x="360" y="234" text-anchor="middle" font-size="14" fill="#1a1a1a" font-weight="600">Intelligence layer</text>
  <text x="360" y="254" text-anchor="middle" font-size="11" fill="#5a5a5a">how a request gets composed into a response</text>
  <line x1="360" y1="294" x2="360" y2="272" stroke="#6b6b6b" stroke-width="1.5" marker-end="url(#arr-up)"/>
  <rect x="160" y="294" width="400" height="56" rx="6" fill="#dee7d8" stroke="#a0bf95"/>
  <text x="360" y="316" text-anchor="middle" font-size="14" fill="#1a1a1a" font-weight="600">World model</text>
  <text x="360" y="336" text-anchor="middle" font-size="11" fill="#5a5a5a">what the org knows about itself and the people it serves</text>
  <line x1="360" y1="376" x2="360" y2="354" stroke="#6b6b6b" stroke-width="1.5" marker-end="url(#arr-up)"/>
  <rect x="160" y="376" width="400" height="56" rx="6" fill="#ede4ce" stroke="#c8b88a"/>
  <text x="360" y="398" text-anchor="middle" font-size="14" fill="#1a1a1a" font-weight="600">Capabilities</text>
  <text x="360" y="418" text-anchor="middle" font-size="11" fill="#5a5a5a">the atomic things the org can actually do</text>
  <rect x="80" y="466" width="560" height="56" rx="6" fill="#fbe8dd" stroke="#c47558" stroke-width="1.5"/>
  <text x="360" y="488" text-anchor="middle" font-size="11" fill="#8c4a30" font-weight="600" letter-spacing="0.6px">THE SHARED PRINCIPLE</text>
  <text x="360" y="508" text-anchor="middle" font-size="12" fill="#1a1a1a">replace hierarchical routing with a system that accumulates knowledge over time</text>
</svg>'''

    return HTML_TEMPLATE.format(
        css=base_css() + EXTRA_CSS,
        title=escape(title),
        n_caps=len(caps),
        n_signals=len(signals),
        frame_diagram_svg=frame_diagram_svg,
        decisions_section=decisions_section,
        stakeholders_html=stakeholders_html,
        interfaces_html=interfaces_html,
        n_current_compositions=len(cur_comp),
        n_potential_compositions=len(pot_comp),
        current_compositions_html=current_compositions_html,
        potential_compositions_html=potential_compositions_html,
        company_observations_html=company_observations_html,
        customer_observations_html=customer_observations_html,
        company_maturity=escape(company_maturity),
        customer_unified_label=escape(customer_unified_label),
        capabilities_html=capabilities_html,
        signals_html=signals_html,
        capabilities_json=json.dumps(caps, ensure_ascii=False),
        stakeholders_index_json=json.dumps(stakeholders_index, ensure_ascii=False),
        interfaces_json=json.dumps(interfaces, ensure_ascii=False),
        signals_json=json.dumps(signals, ensure_ascii=False),
        current_compositions_json=json.dumps(cur_comp, ensure_ascii=False),
        company_observations_json=json.dumps(company.get("observations", []) or [], ensure_ascii=False),
        potential_compositions_json=json.dumps(pot_comp, ensure_ascii=False),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render world-model JSON as interactive HTML.")
    parser.add_argument("--map", required=True, help="World-model JSON path")
    parser.add_argument("--html", required=True, help="Output HTML path")
    parser.add_argument("--title", default="World-model snapshot", help="Page title")
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

    html = render_html(d, args.title)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"Wrote {Path(args.html).resolve()} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
