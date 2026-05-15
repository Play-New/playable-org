#!/usr/bin/env python3
"""
world-model / viewer.py — Render a world-model slice as an editorial-column
3-layer page per the frozen spec in SKILL.md §8.

Three layers stacked: Interfaces (top), Capabilities (middle, dominant),
World model (bottom, three sub-sections). Intelligence layer rendered as
a thin annotation between Capabilities and World model. Roadmap section
reads the captured-signals subset of the world model that no current
composition can fulfil. Decisions follow.

Visual code (frozen): cards with full hairline border, coral border for
differentiated capabilities, hairline for standard. No left-rule cards.
Click → popover (below the clicked card, centered, flips above when no
room). Plain-language labels: differentiated / standard, never moat /
commodity.

Usage:
    python3 viewer.py --map <slice.json> --html <out.html>
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

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


def _humanize(s: str) -> str:
    """Title-case a kebab-case id."""
    return (
        (s or "")
        .replace("-", " ")
        .replace("_", " ")
        .strip()
        .split()
    )


def _human(s: str) -> str:
    """Title-case (each word capitalized): used for proper nouns like
    person names. marco-bellini → Marco Bellini."""
    parts = _humanize(s)
    if not parts:
        return ""
    return " ".join(p[0].upper() + p[1:] if p else "" for p in parts)


def _sentence(s: str) -> str:
    """Sentence-case (first letter capitalized only): used for capability
    names and other verb-object kebab ids that read as actions, not as
    proper nouns. define-positioning → Define positioning."""
    if not s:
        return ""
    cleaned = s.replace("-", " ").replace("_", " ").strip()
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]


EXTRA_CSS = """
/* world-model viewer — editorial-column 3-layer page (SKILL.md §8 frozen).
   1240px outer container; every block lives in a centered 820px column.
   Layers stacked: Interfaces → Capabilities → World model. Intelligence
   layer rendered as a thin annotation between Capabilities and World
   model. Roadmap + Decisions sections follow. Cards full-border, coral
   for differentiated, hairline for standard. Click → popover. */

.wm-body {
  max-width: 1240px;
  margin: 0 auto;
  padding: max(72px, calc(env(safe-area-inset-top) + 60px))
           max(28px, env(safe-area-inset-right))
           max(80px, calc(env(safe-area-inset-bottom) + 60px))
           max(28px, env(safe-area-inset-left));
}

.editorial {
  max-width: 820px;
  margin-left: auto;
  margin-right: auto;
}

/* === HEADER === */
.wm-header { margin: 0 auto 28px; max-width: 820px; }
.wm-header .eyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-60);
  margin: 0 0 8px;
}
.wm-header h1 {
  font-size: 34px;
  font-weight: 540;
  letter-spacing: -0.018em;
  line-height: 1.12;
  margin: 0 0 14px;
  color: var(--ink);
  text-wrap: pretty;
}
.wm-header .lead {
  font-size: 15px;
  line-height: 1.55;
  color: var(--ink-95);
  margin: 0;
  text-wrap: pretty;
}
.wm-intro {
  font-size: 14px;
  line-height: 1.65;
  color: var(--ink-95);
  margin: 0 auto 36px;
  max-width: 820px;
  text-wrap: pretty;
}

/* === LAYER === */
.layer { margin: 32px auto; max-width: 820px; }
.layer-head {
  margin: 0 0 14px;
  border-top: 2px solid var(--ink);
  padding-top: 12px;
}
.layer-head .layer-name {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink);
  margin: 0 0 4px;
}
.layer-head .layer-hint {
  font-size: 12.5px;
  font-style: italic;
  color: var(--ink-60);
  line-height: 1.55;
  margin: 0;
  text-wrap: pretty;
}

/* === CARD (shared shape) === */
.card {
  padding: 14px 18px 16px;
  border: 1px solid var(--hairline);
  border-radius: 4px;
  background: var(--paper);
  cursor: pointer;
  transition: border-color 0.15s, opacity 0.2s;
}
.card:hover { border-color: var(--ink); }
.card.differentiated { border-color: var(--k-commitment); }
.card.is-focused { box-shadow: inset 0 0 0 1px var(--ink); border-color: var(--ink); }
.card.dimmed { opacity: 0.30; }
.card .card-eyebrow {
  font-size: 9.5px;
  font-weight: 500;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-60);
  margin: 0 0 4px;
}
.card.differentiated .card-eyebrow { color: var(--k-commitment); }
.card .card-name {
  font-size: 14px;
  font-weight: 540;
  line-height: 1.25;
  letter-spacing: -0.005em;
  color: var(--ink);
  margin: 0 0 4px;
  text-wrap: pretty;
}
.card .card-meta {
  font-size: 11.5px;
  font-style: italic;
  color: var(--ink-60);
  margin: 4px 0;
  letter-spacing: -0.005em;
  line-height: 1.4;
}

/* === INTERFACES row === */
.if-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.if-card .card-state {
  font-size: 11.5px;
  line-height: 1.5;
  margin: 4px 0 0;
  color: var(--ink-95);
}
.if-card .state-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-40);
  margin-right: 5px;
}

/* === CAPABILITIES grid (dominant) === */
.cap-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}
.cap-card .card-contract {
  font-size: 10.5px;
  color: var(--ink-95);
  font-family: ui-monospace, SF Mono, Menlo, monospace;
  line-height: 1.5;
  margin: 6px 0 0;
  word-break: break-word;
}
.cap-card .card-contract .arrow { color: var(--ink-40); padding: 0 4px; }
.cap-card .wrapper-status {
  display: flex;
  gap: 4px;
  margin: 8px 0 0;
  align-items: center;
}
.cap-card .wrapper-status .ws-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  border: 1px solid var(--ink-40);
  background: var(--paper);
}
.cap-card .wrapper-status .ws-dot.met       { background: var(--ink); border-color: var(--ink); }
.cap-card .wrapper-status .ws-dot.partial   { background: var(--ink-40); border-color: var(--ink-40); }
.cap-card .wrapper-status .ws-label {
  font-size: 9px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-40);
  margin-left: 6px;
}

/* === Intelligence layer annotation === */
.intelligence-annotation {
  text-align: center;
  font-size: 12px;
  font-style: italic;
  color: var(--ink-60);
  letter-spacing: -0.005em;
  line-height: 1.55;
  margin: 36px auto;
  max-width: 820px;
  padding: 10px 14px;
  border-top: 1px dashed var(--hairline);
  border-bottom: 1px dashed var(--hairline);
}
.intelligence-annotation strong {
  font-style: normal;
  font-weight: 540;
  color: var(--ink);
}

/* === World model (2 columns: organization + stakeholder) === */
.wm-two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.wm-two h4 {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-60);
  margin: 0 0 4px;
}
.wm-two .col-hint {
  font-size: 11px;
  font-style: italic;
  color: var(--ink-60);
  line-height: 1.5;
  margin: 0 0 10px;
  text-wrap: pretty;
}
.wm-two ul {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 11.5px;
  line-height: 1.45;
  color: var(--ink-95);
}
.wm-two li {
  padding: 6px 10px;
  border-left: 2px solid var(--hairline);
  margin: 0 0 4px;
}
.wm-two li.maturity-low    { border-left-color: var(--k-commitment); }
.wm-two li.maturity-medium { border-left-color: var(--ink-40); }
.wm-two li.maturity-high   { border-left-color: var(--ink); }
.wm-two li.clickable {
  cursor: pointer;
  transition: background 0.15s, border-left-width 0.15s;
}
.wm-two li.clickable:hover { background: var(--paper); border-left-width: 3px; }
.wm-two li.clickable.is-focused { background: var(--paper); border-left-width: 3px; }
.wm-two li em { font-style: italic; color: var(--ink-60); font-weight: 380; font-size: 10.5px; }
.wm-two .where { font-size: 10.5px; color: var(--ink-60); font-style: italic; }
.wm-two .empty {
  font-size: 11.5px;
  font-style: italic;
  color: var(--ink-40);
  line-height: 1.55;
}

/* === Roadmap (also used inside the Analysis modal) === */
.modal-roadmap { margin: 24px 0 0; }
.modal-section-head {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-60);
  margin: 0 0 6px;
}
.modal-section-hint {
  font-size: 13px;
  font-style: italic;
  color: var(--ink-60);
  line-height: 1.55;
  margin: 0 0 14px;
  text-wrap: pretty;
}
.moves-list {
  list-style: none;
  counter-reset: move;
  padding: 0;
  margin: 0 0 8px;
}
.moves-list li {
  counter-increment: move;
  padding: 14px 0 14px 36px;
  border-top: 1px solid var(--hairline-2);
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--ink-95);
  position: relative;
  text-wrap: pretty;
}
.moves-list li:last-child { border-bottom: 1px solid var(--hairline-2); }
.moves-list li::before {
  content: counter(move, decimal-leading-zero);
  position: absolute;
  left: 0;
  top: 16px;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.12em;
  color: var(--ink-40);
}
.moves-list li strong { color: var(--ink); font-weight: 540; }
.roadmap-section { margin: 56px auto 32px; max-width: 820px; }
.roadmap-section h2 {
  font-size: 18px;
  font-weight: 540;
  letter-spacing: -0.012em;
  margin: 0 0 8px;
  color: var(--ink);
}
.roadmap-section .lead {
  font-size: 13.5px;
  color: var(--ink-95);
  line-height: 1.55;
  margin: 0 0 20px;
  text-wrap: pretty;
}
.roadmap-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.roadmap-card { border-color: var(--k-commitment); }
.roadmap-card .card-trigger {
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--ink-95);
  margin: 4px 0 8px;
  text-wrap: pretty;
}
.roadmap-card .card-trigger strong { font-weight: 540; }
.roadmap-card .card-needed {
  font-size: 11.5px;
  color: var(--ink-60);
  font-style: italic;
  line-height: 1.55;
  margin: 0;
  text-wrap: pretty;
}

/* === Decisions === */
.decisions-section { margin: 56px auto 80px; max-width: 820px; }
.decisions-section h2 {
  font-size: 18px;
  font-weight: 540;
  letter-spacing: -0.012em;
  margin: 0 0 8px;
}
.decisions-section .lead {
  font-size: 13.5px;
  color: var(--ink-95);
  line-height: 1.55;
  margin: 0 0 20px;
}
.decisions-section ol {
  list-style: none;
  counter-reset: dec;
  padding: 0;
  margin: 0;
}
.decisions-section li {
  counter-increment: dec;
  padding: 18px 0;
  border-top: 1px solid var(--hairline-2);
}
.decisions-section li::before {
  content: counter(dec, decimal-leading-zero) " ";
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.12em;
  color: var(--ink-40);
}
.decisions-section .question {
  font-size: 14.5px;
  font-weight: 540;
  letter-spacing: -0.005em;
  color: var(--ink);
  margin: 0 0 8px;
  display: inline;
}
.decisions-section .answer {
  font-size: 13px;
  color: var(--ink-95);
  line-height: 1.65;
  margin: 8px 0;
  text-wrap: pretty;
}
.decisions-section .source {
  font-size: 10.5px;
  color: var(--ink-60);
  font-family: ui-monospace, SF Mono, Menlo, monospace;
  margin: 8px 0 0;
}

/* === Popover === */
.popover {
  position: absolute;
  display: none;
  max-width: 420px;
  min-width: 280px;
  padding: 16px 20px 18px;
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 4px;
  box-shadow: 0 4px 18px rgba(28,26,22,0.12);
  z-index: 150; /* above modal scrim (100) so popovers in Analysis are visible */
}
.popover.open { display: block; }
.popover .pop-close {
  position: absolute;
  top: 8px; right: 10px;
  background: transparent; border: 0;
  font: inherit; font-size: 16px;
  color: var(--ink-40);
  cursor: pointer;
  padding: 2px 6px; line-height: 1;
}
.popover .pop-close:hover { color: var(--ink); }
.popover .pop-eyebrow {
  font-size: 10px; font-weight: 500;
  letter-spacing: 0.10em; text-transform: uppercase;
  color: var(--ink-60);
  margin: 0 0 4px;
}
.popover .pop-eyebrow.differentiated { color: var(--k-commitment); }
.popover h3 {
  font-size: 14.5px;
  font-weight: 540;
  letter-spacing: -0.012em;
  margin: 0 0 8px;
  padding-right: 24px;
  text-wrap: pretty;
  color: var(--ink);
}
.popover .desc {
  font-size: 12.5px;
  line-height: 1.55;
  margin: 0 0 8px;
  color: var(--ink-95);
  text-wrap: pretty;
}
.popover .desc strong { font-weight: 540; }
.popover .section-label {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ink-60);
  margin: 12px 0 4px;
}
.popover ul {
  font-size: 12px;
  padding-left: 20px;
  margin: 4px 0;
  line-height: 1.55;
  color: var(--ink-95);
}
.popover .citation {
  font-size: 10.5px;
  color: var(--ink-60);
  padding: 4px 0 4px 10px;
  border-left: 1px solid var(--hairline);
  margin-top: 6px;
  line-height: 1.5;
  font-family: ui-monospace, SF Mono, Menlo, monospace;
  font-style: italic;
}

@media (max-width: 760px) {
  .wm-body { padding: max(56px, calc(env(safe-area-inset-top) + 50px)) 14px max(72px, calc(env(safe-area-inset-bottom) + 56px)); }
  .wm-two { grid-template-columns: 1fr; }
  .cap-grid { grid-template-columns: 1fr 1fr; }
  .if-row { grid-template-columns: 1fr 1fr; }
  .layer { margin: 24px auto; }
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

<main class="wm-body">

  <header class="wm-header">
    <p class="eyebrow">world model</p>
    <h1>{org_name}</h1>
    <p class="lead">{lead_text}</p>
  </header>

  <p class="wm-intro">{intro_text}</p>

  <section class="layer" id="layer-interfaces">
    <div class="layer-head">
      <p class="layer-name">Interfaces</p>
      <p class="layer-hint">Where customers, partners, vendors meet the studio: meetings, calls, documents. Today these mostly push deliverables out. With AI in the middle, they could also catch what comes back: preferences, complaints, drift signals. Each card shows the contrast between what the surface delivers today and what it could also collect.</p>
    </div>
    <div class="if-row">{interface_cards}</div>
  </section>

  <section class="layer" id="layer-capabilities">
    <div class="layer-head">
      <p class="layer-name">Capabilities</p>
      <p class="layer-hint">The things this studio can be asked to do, each with a contract: what goes in, what comes out, who runs it, when it falls short. Coral border marks differentiated craft: work this studio does that nobody else can replicate. Hairline border marks competent practice the category shares. The five dots under each card show how callable that function is today, from informal (a person you have to know) to fully wired (anyone or any system can ask for it).</p>
    </div>
    <div class="cap-grid">{capability_cards}</div>
  </section>

  <p class="intelligence-annotation">Between the memory below and the functions above sits the layer that does the routing: it reads what the studio knows, picks which functions to put together for each request, and writes the outcome back into memory. <strong>AI is what makes this layer possible.</strong></p>

  <section class="layer" id="layer-world-model">
    <div class="layer-head">
      <p class="layer-name">World models</p>
      <p class="layer-hint">{world_model_hint}</p>
    </div>
    <div class="wm-two">
      <div>
        <h4>Organization side</h4>
        <p class="col-hint">What the studio knows about itself: hours, profitability, win rates, how its own work is going. Click any item for where it lives today and what's still missing.</p>
        {operational_html}
      </div>
      <div>
        <h4>Stakeholder side</h4>
        <p class="col-hint">What the studio knows about each kind of stakeholder it serves, built up in principle from every past interaction. Click any item for what they get, what they give back, and where the picture sits today.</p>
        {customer_html}
      </div>
    </div>
  </section>

</main>

{about_modal_html}

{decisions_modal_html}

<div class="popover" id="popover" role="dialog" aria-modal="false">
  <button class="pop-close" id="pop-close" aria-label="Close">×</button>
  <div id="pop-body"></div>
</div>

<script>
{baseline_js}
</script>

<script>
const NODES = {nodes_json};

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }})[c]);
}}

function _humanize(s) {{
  // Title case (each word capitalized): for proper nouns like person names.
  return (s || '').replace(/[-_]/g, ' ').trim().split(/\\s+/)
    .map(w => w ? w.charAt(0).toUpperCase() + w.slice(1) : '').join(' ');
}}

function _sentence(s) {{
  // Sentence case (first letter only): for verb-object capability names.
  // define-positioning → Define positioning
  if (!s) return '';
  const cleaned = (s + '').replace(/[-_]/g, ' ').trim();
  if (!cleaned) return '';
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}}

function _list(arr, asSentence) {{
  if (!arr || !arr.length) return '';
  const fmt = asSentence ? _sentence : (x => x);
  return '<ul>' + arr.map(x => `<li>${{escapeHtml(fmt(x))}}</li>`).join('') + '</ul>';
}}

function renderCapabilityPopover(n) {{
  const moat = n.moat_grade === 'moat';
  const eyebrowCls = moat ? 'pop-eyebrow differentiated' : 'pop-eyebrow';
  const eyebrowText = moat ? 'differentiated' : 'standard';
  let h = `<p class="${{eyebrowCls}}">${{escapeHtml(eyebrowText)}}</p>`;
  h += `<h3>${{escapeHtml(_sentence(n.name))}}</h3>`;
  if (n.description) h += `<p class="desc">${{escapeHtml(n.description)}}</p>`;
  if (n.input || n.output) {{
    h += `<div class="section-label">Contract</div>`;
    if (n.input)               h += `<p class="desc"><strong>Takes:</strong> ${{escapeHtml(n.input)}}</p>`;
    if (n.output)              h += `<p class="desc"><strong>Returns:</strong> ${{escapeHtml(n.output)}}</p>`;
    if (n.slo_targets)         h += `<p class="desc"><strong>Reliability target:</strong> ${{escapeHtml(n.slo_targets)}}</p>`;
    if (n.regulatory_constraints && n.regulatory_constraints.toLowerCase() !== 'none') {{
      h += `<p class="desc"><strong>Regulatory:</strong> ${{escapeHtml(n.regulatory_constraints)}}</p>`;
    }}
    if (n.invocation_modality) h += `<p class="desc"><strong>How called:</strong> ${{escapeHtml(n.invocation_modality)}}</p>`;
  }}
  if (n.current_dri) {{
    h += `<div class="section-label">Who's on the hook today</div>`;
    h += `<p class="desc">${{escapeHtml(_humanize(n.current_dri))}}</p>`;
  }}
  if (n.is_callable_by && n.is_callable_by.length) {{
    h += `<div class="section-label">Who can ask for it</div>`;
    h += _list(n.is_callable_by.map(_humanize));
  }}
  if (n.composes_with && n.composes_with.length) {{
    h += `<div class="section-label">Used together with</div>`;
    h += _list(n.composes_with, true);
  }}
  if (n.exposure_status) {{
    const e = n.exposure_status;
    const items = [
      ['the promise to the customer is written down', e.contract_written],
      ['one named person is accountable',             e.dri_named],
      ['anyone in the org can find it',               e.discoverable],
      ['anyone can ask for it through a known channel', e.invocable_channel],
      ['the org records when it falls short',         e.failure_log],
    ];
    h += `<div class="section-label">How callable today</div>`;
    h += '<ul>';
    for (const [label, val] of items) {{
      const v = (val === true) ? 'yes'
              : (val === false) ? 'no'
              : escapeHtml(String(val));
      h += `<li>${{label}}: <em>${{v}}</em></li>`;
    }}
    h += '</ul>';
  }}
  if (moat && n.moat_rationale) {{
    h += `<div class="section-label">Why differentiated</div>`;
    h += `<p class="desc">${{escapeHtml(n.moat_rationale)}}</p>`;
  }}
  if (n._structure_evidence && n._structure_evidence.length) {{
    for (const e of n._structure_evidence) h += `<div class="citation">${{escapeHtml(e)}}</div>`;
  }}
  return h;
}}

function renderInterfacePopover(n) {{
  let h = `<p class="pop-eyebrow">interface</p>`;
  h += `<h3>${{escapeHtml(n.name)}}</h3>`;
  if (n.description) h += `<p class="desc">${{escapeHtml(n.description)}}</p>`;
  if (n.today_state) {{
    h += `<div class="section-label">Today</div>`;
    h += `<p class="desc">${{escapeHtml(n.today_state)}}</p>`;
  }}
  if (n.signals_lost_today) {{
    h += `<div class="section-label">What passes through unrecorded today</div>`;
    h += `<p class="desc">${{escapeHtml(n.signals_lost_today)}}</p>`;
  }}
  if (n.after_state_hint) {{
    h += `<div class="section-label">After the move</div>`;
    h += `<p class="desc">${{escapeHtml(n.after_state_hint)}}</p>`;
  }}
  if (n.surfaces_capabilities && n.surfaces_capabilities.length) {{
    h += `<div class="section-label">Surfaces</div>`;
    h += _list(n.surfaces_capabilities, true);
  }}
  return h;
}}

function renderRoadmapPopover(n) {{
  let h = `<p class="pop-eyebrow differentiated">missing capability</p>`;
  h += `<h3>${{escapeHtml(_sentence(n.missing_capability || '?'))}}</h3>`;
  if (n.trigger) {{
    h += `<div class="section-label">When this happens</div>`;
    h += `<p class="desc">${{escapeHtml(n.trigger)}}</p>`;
  }}
  if (n.composition_attempted && n.composition_attempted.length) {{
    h += `<div class="section-label">Composition the layer would attempt</div>`;
    h += _list(n.composition_attempted, true);
  }}
  if (n.what_would_be_needed) {{
    h += `<div class="section-label">What it would take to close</div>`;
    h += `<p class="desc">${{escapeHtml(n.what_would_be_needed)}}</p>`;
  }}
  if (n.structure_evidence) h += `<div class="citation">${{escapeHtml(n.structure_evidence)}}</div>`;
  return h;
}}

function renderOperationalPopover(n) {{
  let h = `<p class="pop-eyebrow">what the org tracks about its own work</p>`;
  h += `<h3>${{escapeHtml(n.dimension || '?')}}</h3>`;
  if (n.lives_in) {{
    h += `<div class="section-label">Where it lives today</div>`;
    h += `<p class="desc">${{escapeHtml(n.lives_in)}}</p>`;
  }}
  if (n.maturity) {{
    h += `<div class="section-label">How mature the picture is</div>`;
    h += `<p class="desc"><strong>${{escapeHtml(n.maturity)}}.</strong></p>`;
  }}
  if (n.gaps) {{
    h += `<div class="section-label">What's still missing</div>`;
    h += `<p class="desc">${{escapeHtml(n.gaps)}}</p>`;
  }}
  return h;
}}

function renderPerCallerPopover(n) {{
  let h = `<p class="pop-eyebrow">what the org tracks about this stakeholder</p>`;
  h += `<h3>${{escapeHtml(_humanize(n.type || '?'))}}</h3>`;
  if (n.description) h += `<p class="desc">${{escapeHtml(n.description)}}</p>`;
  if (n.what_they_get_from_org) {{
    h += `<div class="section-label">What they get from the org</div>`;
    h += `<p class="desc">${{escapeHtml(n.what_they_get_from_org)}}</p>`;
  }}
  if (n.what_they_contribute_back) {{
    h += `<div class="section-label">What they give back</div>`;
    h += `<p class="desc">${{escapeHtml(n.what_they_contribute_back)}}</p>`;
  }}
  if (n.honest_signal) {{
    h += `<div class="section-label">The metric to weigh first</div>`;
    h += `<p class="desc">${{escapeHtml(n.honest_signal)}}</p>`;
  }}
  if (n.fragmentation) {{
    h += `<div class="section-label">Where the picture currently sits</div>`;
    h += `<p class="desc">${{escapeHtml(n.fragmentation)}}</p>`;
  }}
  if (n.current_maturity) {{
    h += `<div class="section-label">How mature</div>`;
    h += `<p class="desc"><strong>${{escapeHtml(n.current_maturity)}}.</strong></p>`;
  }}
  return h;
}}

const RENDERERS = {{
  capability:  renderCapabilityPopover,
  interface:   renderInterfacePopover,
  roadmap:     renderRoadmapPopover,
  operational: renderOperationalPopover,
  per_caller:  renderPerCallerPopover,
}};

const popoverEl = document.getElementById('popover');
const popoverBody = document.getElementById('pop-body');

function showPopover(html, anchorRect) {{
  popoverBody.innerHTML = html;
  const margin = 12;
  popoverEl.style.left = '0px';
  popoverEl.style.top = '0px';
  popoverEl.classList.add('open');
  const r = popoverEl.getBoundingClientRect();
  const anchorCenterX = (anchorRect.left + anchorRect.right) / 2;
  const viewportRight = window.scrollX + window.innerWidth;
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
  popoverEl.style.top = y + 'px';
}}

function hidePopover() {{
  popoverEl.classList.remove('open');
  document.querySelectorAll('.card.is-focused').forEach(el => el.classList.remove('is-focused'));
}}

document.querySelectorAll('[data-id]').forEach(el => {{
  el.addEventListener('click', (e) => {{
    e.stopPropagation();
    const id = el.dataset.id;
    const node = NODES[id];
    if (!node) return;
    const renderer = RENDERERS[node._band];
    if (!renderer) return;
    hidePopover();
    el.classList.add('is-focused');
    const r = el.getBoundingClientRect();
    showPopover(renderer(node), {{
      left:   r.left + window.scrollX,
      right:  r.right + window.scrollX,
      top:    r.top + window.scrollY,
      bottom: r.bottom + window.scrollY,
    }});
  }});
}});

document.addEventListener('click', (e) => {{
  if (!e.target.closest('[data-id], #popover')) hidePopover();
}});
document.getElementById('pop-close').addEventListener('click', hidePopover);
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') hidePopover(); }});
</script>

</body>
</html>"""


# ── builders ─────────────────────────────────────────────────────


def _interface_card(it: dict) -> str:
    """Card for the Interfaces row, two states (today / after)."""
    name = it.get("name", "?")
    today = (it.get("today_state") or it.get("description") or "").strip()
    after = (it.get("after_state_hint") or "").strip()
    if_id = "if:" + (it.get("_structure_id") or name)
    today_html = (
        f'<p class="card-state"><span class="state-label">today</span>{escape(today[:120])}</p>'
        if today else ""
    )
    after_html = (
        f'<p class="card-state"><span class="state-label">after</span>{escape(after[:120])}</p>'
        if after else ""
    )
    return (
        f'<div class="card if-card" data-id="{escape(if_id)}">'
        f'<h3 class="card-name">{escape(name)}</h3>'
        f'{today_html}'
        f'{after_html}'
        f'</div>'
    )


def _wrapper_dots(exposure: dict | None) -> str:
    """Five dots showing how callable a capability is today.

    Each dot is one criterion. Filled = met, half-filled = partial, empty = no.
    Hover any dot for the plain-language explanation of what that criterion
    means. The label below counts how many of the five are met.
    """
    if not exposure:
        return ""
    plain = {
        "contract_written":   "the promise to the customer is written down",
        "dri_named":          "one named person is accountable",
        "discoverable":       "anyone in the org can find it",
        "invocable_channel":  "anyone can ask for it through a known channel",
        "failure_log":        "the org records when it falls short",
    }
    keys = ["contract_written", "dri_named", "discoverable", "invocable_channel", "failure_log"]
    dots = []
    n_met = 0
    for k in keys:
        v = exposure.get(k)
        if v is True:
            cls = "ws-dot met"; state = "yes"; n_met += 1
        elif v in ("implicit", "partial", "informal"):
            cls = "ws-dot partial"; state = "partial"
        else:
            cls = "ws-dot"; state = "no"
        dots.append(
            f'<span class="{cls}" title="{escape(plain[k])}: {state}"></span>'
        )
    label = f'<span class="ws-label">callable {n_met}/5</span>'
    return '<div class="wrapper-status">' + "".join(dots) + label + '</div>'


def _capability_card(c: dict) -> str:
    moat = c.get("moat_grade") == "moat"
    cls = "differentiated" if moat else "standard"
    tag = "differentiated" if moat else "standard"
    name = c.get("name", "?")
    display_name = _sentence(name)  # define-positioning → Define positioning
    dri = (c.get("current_dri") or (c.get("current_owners") or [""])[0] or "").strip()
    in_ = (c.get("input") or "").strip()
    out = (c.get("output") or "").strip()
    contract_html = ""
    if in_ or out:
        contract_html = (
            f'<p class="card-contract">'
            f'{escape(in_[:48])}'
            f'<span class="arrow">→</span>'
            f'{escape(out[:48])}'
            f'</p>'
        )
    dri_html = (
        f'<p class="card-meta">Run by {escape(_human(dri))}</p>'
        if dri else ""
    )
    cap_id = "cap:" + (c.get("_structure_id") or name)
    return (
        f'<div class="card cap-card {cls}" data-id="{escape(cap_id)}">'
        f'<p class="card-eyebrow">{tag}</p>'
        f'<h3 class="card-name">{escape(display_name)}</h3>'
        f'{dri_html}'
        f'{contract_html}'
        f'{_wrapper_dots(c.get("exposure_status"))}'
        f'</div>'
    )


def _operational_html(observations: list[dict]) -> str:
    if not observations:
        return '<p class="empty">Nothing recorded about its own work yet.</p>'
    items = []
    for i, o in enumerate(observations):
        mat = (o.get("maturity") or "").lower()
        cls = f"maturity-{mat}" if mat in ("low", "medium", "high") else ""
        dim = o.get("dimension", "")
        lives = o.get("lives_in", "")
        obs_id = "obs:op:" + (o.get("dimension") or str(i)).lower().replace(" ", "-")
        items.append(
            f'<li class="{cls} clickable" data-id="{escape(obs_id)}">'
            f'<strong>{escape(dim)}</strong>'
            f' <em>{escape(mat)}</em>'
            f'{f"<br><span class=\"where\">lives in {escape(lives)}</span>" if lives else ""}'
            f'</li>'
        )
    return "<ul>" + "".join(items) + "</ul>"


def _customer_html(by_stakeholder: list[dict], is_unified: bool) -> str:
    if not by_stakeholder:
        return '<p class="empty">Nothing recorded about each stakeholder yet.</p>'
    items = []
    for i, s in enumerate(by_stakeholder):
        mat = (s.get("current_maturity") or "").lower()
        cls = f"maturity-{mat}" if mat in ("low", "medium", "high") else ""
        name = _human(s.get("type", ""))
        frag = "" if is_unified else " · fragmented"
        sh_id = "obs:cu:" + (s.get("type") or str(i))
        items.append(
            f'<li class="{cls} clickable" data-id="{escape(sh_id)}">'
            f'<strong>{escape(name)}</strong>'
            f' <em>{escape(mat)}{frag}</em>'
            f'</li>'
        )
    return "<ul>" + "".join(items) + "</ul>"


def _roadmap_card(p: dict) -> str:
    missing = p.get("missing_capability", "?")
    display_missing = _sentence(missing)
    trigger = (p.get("trigger") or "").strip()
    needed = (p.get("what_would_be_needed") or "").strip()
    rmp_id = "rmp:" + missing
    trigger_html = (
        f'<p class="card-trigger"><strong>When this happens:</strong> {escape(trigger)}</p>'
        if trigger else ""
    )
    needed_html = (
        f'<p class="card-needed">{escape(needed[:240])}</p>'
        if needed else ""
    )
    return (
        f'<div class="card roadmap-card" data-id="{escape(rmp_id)}">'
        f'<p class="card-eyebrow">missing capability</p>'
        f'<h3 class="card-name">{escape(display_missing)}</h3>'
        f'{trigger_html}'
        f'{needed_html}'
        f'</div>'
    )


# ── render ───────────────────────────────────────────────────────


def render_html(d: dict) -> str:
    org_name = (d.get("_org") or "").strip() or "World model"
    dated = d.get("_dated", "—")

    capabilities = d.get("capabilities") or []
    interfaces = d.get("interfaces") or []
    pieces = d.get("pieces_to_build") or []
    wmc = d.get("world_model_company") or {}
    wmcust = d.get("world_model_customer") or {}
    decisions = d.get("decisions") or []

    # ── Cards ─────────────────────────────────────────────────
    interface_cards = "\n".join(_interface_card(it) for it in interfaces)
    capability_cards = "\n".join(_capability_card(c) for c in capabilities)
    operational_html = _operational_html(wmc.get("observations") or [])
    customer_html = _customer_html(
        wmcust.get("by_stakeholder") or [], bool(wmcust.get("is_unified"))
    )
    roadmap_cards = (
        "\n".join(_roadmap_card(p) for p in pieces)
        if pieces
        else '<p style="color: var(--ink-60); font-style: italic; font-size: 13px;">No roadmap entries surfaced yet.</p>'
    )

    # ── Header / intro / hint copy (plain language) ──────────
    n_caps = len(capabilities)
    n_moat = sum(1 for c in capabilities if c.get("moat_grade") == "moat")
    n_std = n_caps - n_moat
    n_pieces = len(pieces)

    lead_text = (
        "The studio mapped as a set of functions a customer could ask for, "
        "with the memory and the AI layer that decide how to deliver each."
    )
    intro_text = (
        "Every customer interaction follows the same shape. Someone reaches the studio "
        "through an interface (a meeting, a call, a doc). The studio reads what it knows "
        "and decides which of its functions to put together. The response goes back, and "
        "the outcome (what worked, what didn't, what was asked but couldn't be done) "
        "becomes new memory. The 'asked but couldn't be done' parts become the roadmap "
        "of what to build next."
    )

    overall = (wmc.get("overall_maturity") or "").lower()
    is_unified = bool(wmcust.get("is_unified"))
    op_today = {
        "low":    "thin",
        "medium": "partial",
        "high":   "structured",
    }.get(overall, "still partial")
    sh_today = (
        "unified across the org"
        if is_unified
        else "fragmented across heads, CRMs, and delivered files"
    )
    world_model_hint = (
        f"Two memories the AI layer reads. About the studio itself: operations, performance, "
        f"priorities. About each kind of stakeholder it serves: what's known about them. "
        f"Today the studio-side picture is {op_today}; the stakeholder-side picture is {sh_today}. "
        f"Both should grow denser with every interaction."
    )

    # ── Analysis modal — what to do about it. Two sections:
    # 1. The move, in three steps (the structural transformation).
    # 2. Decisions (the leader-facing reading taken from the read).
    # The "missing capabilities" list is deliberately not surfaced here:
    # in the source's framework, the roadmap is what the loop produces
    # once it's running, not a list compiled today. Showing it would
    # invite planning-table thinking, the opposite of the move.
    decisions_modal_html_str = ""
    has_analysis = bool(decisions)
    if has_analysis:
        three_moves_html = (
            '<div class="modal-moves">'
            '<p class="modal-section-head">The move, in three steps</p>'
            '<p class="modal-section-hint">What it would take to run the loop on the studio. The work is structural. It reshapes what the org is.</p>'
            '<ol class="moves-list">'
            '<li><strong>Make interfaces collect what comes back.</strong> '
            'Today pitch, kickoff, weekly, handover hand finished work to the client and let what comes back disappear into people\'s heads. '
            'The shift is to delivering tools the client uses. A brand system that lives with them as a queryable, extensible asset takes the place of the frozen PDF. '
            'A structured weekly check-in takes the place of free-text notes. '
            'A 12-month follow-up channel is built into the engagement from day one. '
            'Every interaction becomes a place where the work is being used, and that use generates signal.</li>'
            '<li><strong>Reorganize around the studio\'s invokable functions.</strong> '
            'Today work lives inside named people: someone has to know who to ask. '
            'Around each function above, put a wrapper. A written contract: what goes in, what comes back, what reliability the studio commits to. '
            'A single person on the hook for that contract. Named specialists who execute it. A known channel anyone can use to request it. A log of when the contract isn\'t met. '
            'The studio\'s structure reorganizes around the functions; units shrink to containers, and the unit chart stops being the operating model.</li>'
            '<li><strong>Build the memory the studio uses to decide.</strong> '
            'Every signal captured at an interface, every outcome of an invocation, every fall-short writes into the studio\'s memory. '
            'The memory has two sides: about the studio itself (how its work is going, what\'s costing money, what\'s working) and about each kind of stakeholder (what they get, what they give back, how fragmented the current picture is). '
            'AI in the middle reads this memory and decides what to put together for each new request. '
            'The longer the loop runs, the deeper this memory grows, holding patterns no one else has because no one else has captured the signals.</li>'
            '</ol>'
            '</div>'
        )

        # Decisions list as decisions_html
        items = []
        for dec in decisions:
            q = escape(dec.get("question", ""))
            ans = "".join(
                f"<p>{inline_md(p)}</p>"
                for p in (dec.get("answer", "") or "").split("\n\n")
                if p.strip()
            )
            src = escape(dec.get("source", ""))
            src_html = f'<p class="source">{src}</p>' if src else ""
            items.append(f"<li><h3>{q}</h3>{ans}{src_html}</li>")

        modal_headline = "Running the loop on the studio."

        body_with_intro = three_moves_html
        if decisions:
            body_with_intro += (
                f'<p class="modal-section-head" style="margin-top: 36px;">'
                f'{len(decisions)} decision{"s" if len(decisions) != 1 else ""} from this read of the studio'
                f'</p>'
            )

        decisions_modal_html_str = app_pure_modal_html(
            headline=modal_headline,
            org_name=org_name,
            dated=dated,
            decisions_html="".join(items),
            kicker="Reading the world model",
            lede="",
            body_html=body_with_intro,
        )

    # ── About modal — the loop tesi in plain language ────────
    about_body = f"""
  <p>The point of this page is one move. Today the studio has interfaces, capabilities, and a world model, but in a primitive form. Interfaces are mostly delivery surfaces; signals that come back through them get lost. Capabilities live inside named people, callable through availability rather than contract. The world model is implicit, scattered across heads and delivered files.</p>

  <p>The move described in <em>From Hierarchy to Intelligence</em> (Jack Dorsey + Roelof Botha, Block, March 2026) is to insert intelligence, typically AI-mediated, that transforms the three. Interfaces start catching signal in addition to delivering outcomes. Capabilities become invokable systems: the same person stays accountable, and a wrapper makes the function callable from outside their availability. The world model becomes a memory that auto-updates from the signals.</p>

  <h2>The loop</h2>
  <p>A request arrives via an interface. The middle layer reads the world model and decides. If a function matches, it is invoked; the response goes back via the interface; the outcome is captured into the world model. If no function matches, the unanswered request is itself captured. That captured signal becomes the future roadmap. The loop surfaces it. A planning meeting does not.</p>

  <h2>The three layers, top to bottom on the page</h2>
  <p><strong>Interfaces</strong>. Where stakeholders arrive. Each card shows two states: today (mostly delivery) and after (also signal collection).</p>
  <p><strong>Capabilities</strong>. The invokable functions of the studio. Coral border marks differentiated craft this studio does that nobody else can replicate. Hairline border marks standard practice the category shares. Each card shows the contract (input → output), who runs it today, and a row of five dots showing how callable the function is right now: whether the promise is written down, whether one person is accountable, whether anyone in the org can find it, whether anyone can ask for it through a known channel, whether the org records when it falls short. Filled dots mean yes; outlined mean not yet.</p>
  <p><strong>World model</strong>. The memory the middle layer reads, in two halves: about the studio itself (its operations, performance, priorities) and about each kind of stakeholder it serves (what it knows of them, how fragmented that picture is today).</p>
  <p>Between the functions and the memory, a thin annotation names the middle layer: where AI lives.</p>

  <h2>What to do about it</h2>
  <p>Open <strong>Analysis</strong> at top-right. It names the three structural moves the studio would make to actually run this: turn interfaces into signal collection, reorganize around the functions, build the memory that decides. Plus the leader-facing decisions taken from this read.</p>

  <p>This particular reading covers <strong>{n_caps} {'function' if n_caps == 1 else 'functions'}</strong> ({n_moat} differentiated, {n_std} standard). Click any card on the page for its full content.</p>
"""
    about_modal_html_str = app_pure_about_modal_html(
        kicker=f"№ {n_caps:02d} · world-model",
        headline=org_name,
        lede="An operating-model read of the studio: capabilities, interfaces, world model, plus the runtime that connects them.",
        body_html=about_body,
    )

    # ── NODES dict for popover lookup ────────────────────────
    nodes: dict[str, dict] = {}
    for c in capabilities:
        n = dict(c)
        n["_band"] = "capability"
        nodes[f"cap:{c.get('_structure_id') or c['name']}"] = n
    for it in interfaces:
        n = dict(it)
        n["_band"] = "interface"
        nodes[f"if:{it.get('_structure_id') or it['name']}"] = n
    for p in pieces:
        n = dict(p)
        n["_band"] = "roadmap"
        nodes[f"rmp:{p.get('missing_capability')}"] = n
    # World-model band entries: operational observations and per-stakeholder
    # representations are clickable too, with their own popovers.
    for i, o in enumerate(wmc.get("observations") or []):
        n = dict(o)
        n["_band"] = "operational"
        oid = "obs:op:" + (o.get("dimension") or str(i)).lower().replace(" ", "-")
        nodes[oid] = n
    for i, s in enumerate(wmcust.get("by_stakeholder") or []):
        n = dict(s)
        n["_band"] = "per_caller"
        n["_unified"] = bool(wmcust.get("is_unified"))
        sid = "obs:cu:" + (s.get("type") or str(i))
        nodes[sid] = n

    nodes_json = json.dumps(nodes, ensure_ascii=False).replace("</", "<\\/")

    return HTML_TEMPLATE.format(
        head_meta=app_pure_head_meta(f"{org_name} — world model"),
        css=app_pure_css(layout="scroll") + EXTRA_CSS,
        baseline_js=app_pure_baseline_js(),
        dateline=app_pure_dateline_html(org_name, what="world model"),
        top_right=app_pure_top_right_html(
            dated, show_analysis=has_analysis, show_help=True
        ),
        about_modal_html=about_modal_html_str,
        decisions_modal_html=decisions_modal_html_str,
        org_name=escape(org_name),
        lead_text=escape(lead_text),
        intro_text=escape(intro_text),
        interface_cards=interface_cards,
        capability_cards=capability_cards,
        world_model_hint=escape(world_model_hint),
        operational_html=operational_html,
        customer_html=customer_html,
        nodes_json=nodes_json,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render world-model JSON as editorial-column page.")
    parser.add_argument("--map", required=True, help="World-model JSON path")
    parser.add_argument("--html", required=True, help="Output HTML path")
    parser.add_argument(
        "--decisions",
        help="Optional JSON list of {question, answer, source} merged into the map under top-level "
             "'decisions[]'. Renders the 'How to read this map' section. Required for a shippable play.",
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
