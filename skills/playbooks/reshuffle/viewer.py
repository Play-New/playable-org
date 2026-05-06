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

# Plain-language labels (no metaphors, no jargon).
CONSTRAINT_LABEL = {
    "scarcity": "Risorsa o competenza rara",
    "risk": "Rischio di sbagliare",
    "coordination": "Costo di tenere allineati team diversi",
}
CONSTRAINT_PLAIN = {
    "scarcity": "Solo poche persone possono fare questa attività — perché serve una competenza rara, un'abilitazione regolata, o una relazione che non si può scalare.",
    "risk": "Il costo di sbagliare è alto (sanzione, danno reputazionale, perdita finanziaria). Serve verifica a strati e qualcuno che firmi.",
    "coordination": "L'attività in sé non è difficile. Il pezzo costoso è far passare informazioni e decisioni fra team diversi che dovrebbero restare allineati.",
}
KM_LABEL = {
    "encoding": "Scrivere e codificare la conoscenza",
    "organizing": "Organizzare e ritrovare informazioni",
    "deploying": "Usare la conoscenza al momento delle decisioni",
    "none": "—",
}
AI_CLASS_LABEL = {
    "tool": "Acceleratore (cambia velocità, non struttura)",
    "engine": "Infrastruttura di coordinamento (cambia struttura)",
    "not-applicable": "AI non rilevante per questa attività",
}
AI_CLASS_SHORT = {
    "tool": "acceleratore",
    "engine": "infrastruttura",
    "not-applicable": "non rilevante",
}
AI_CLASS_PLAIN = {
    "tool": "L'AI rende quest'attività più veloce, ma il modo in cui il lavoro è organizzato fra team rimane lo stesso. Utile, non strategico.",
    "engine": "L'AI cambia un vincolo strutturale del processo: la conoscenza diventa condivisa fra team, e si può lavorare in parallelo invece che a staffetta. È la mossa che riconfigura come l'organizzazione tiene insieme questo pezzo di lavoro.",
    "not-applicable": "Per quest'attività non c'è evidenza sufficiente nei dati osservativi, oppure il vincolo dominante (per esempio una norma di legge) rende l'AI non rilevante qui.",
}
MODE_LABEL = {
    "see-saw": "Modello tradizionale: o autonomia o allineamento",
    "flywheel": "Modello AI-mediato: autonomia e allineamento insieme",
}
MODE_PLAIN = {
    "see-saw": "Oggi il processo funziona secondo la regola classica: dare più autonomia ai team li fa correre più veloci, ma rende più difficile mantenerli allineati. Il guadagno di uno costa qualcosa all'altro.",
    "flywheel": "Il processo può funzionare secondo una regola nuova: una conoscenza condivisa accessibile in tempo reale permette ai team di restare allineati senza perdere autonomia. Più hai dell'una, più puoi avere dell'altra.",
}

EXTRA_CSS = """
:root {
  --bg: var(--bg-soft);
  --fg: var(--fg);
  --muted: var(--muted);
  --line: var(--line);
  --card: var(--bg);
  --accent: var(--fg);
  --scarcity: #c4bcd9;
  --risk: #e0b3b3;
  --coordination: #b6cdaf;
}

body { background: var(--bg-soft); }

.container { max-width: 1100px; margin: 0 auto; padding: 48px 32px 80px; }
header { padding-bottom: 24px; border-bottom: 1px solid var(--line); margin-bottom: 32px; }
header h1 { font-size: 1.9rem; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 6px; }
.anchor-line { font-size: 0.78rem; color: var(--muted); margin-bottom: 8px; font-family: ui-monospace, SF Mono, Menlo, monospace; text-transform: uppercase; letter-spacing: 0.04em; }
.description { font-size: 0.95rem; color: var(--fg); line-height: 1.65; }

.intro, .panel, .ledger, .candidates { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 28px 32px; margin-bottom: 22px; }
.panel h2, .ledger h2, .candidates h2, .intro h2 { font-size: 1.15rem; font-weight: 500; margin: 0 0 6px; letter-spacing: -0.01em; }
.panel-hint { font-size: 0.85rem; color: var(--muted); margin: 0 0 18px; line-height: 1.55; }
.intro p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); }
.intro .pull { background: var(--bg-soft); border-left: 2px solid var(--fg); padding: 14px 18px; margin: 18px 0; font-size: 0.95rem; color: var(--fg); }
h3 { font-size: 0.95rem; font-weight: 500; margin: 18px 0 10px; }
p { margin: 0 0 12px; font-size: 0.92rem; }

.dist-bar { display: flex; height: 22px; border-radius: 3px; overflow: hidden; border: 1px solid var(--line); margin: 14px 0; }
.dist-bar > div { height: 100%; }
.dist-bar .seg.scarcity { background: var(--scarcity); }
.dist-bar .seg.risk { background: var(--risk); }
.dist-bar .seg.coordination { background: var(--coordination); }
.dist-legend { display: grid; gap: 10px; font-size: 0.85rem; color: var(--fg); margin-top: 12px; }
.dist-legend .item { display: flex; gap: 10px; align-items: flex-start; }
.dist-legend .swatch { width: 14px; height: 14px; border-radius: 3px; margin-top: 3px; flex-shrink: 0; }
.dist-legend strong { font-weight: 500; color: var(--fg); }
.dist-legend .count { color: var(--muted); }

.stat-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin: 16px 0; }
.stat { background: var(--card); padding: 14px 18px; border-radius: 3px; border: 1px solid var(--line); border-left: 2px solid var(--soft); font-size: 0.85rem; }
.stat.engine { border-left-color: var(--fg); }
.stat .key { color: var(--muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; font-weight: 500; }
.stat .val strong { font-weight: 500; color: var(--fg); }

.group { margin: 24px 0; }
.group-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--line); }
.group-header .swatch { width: 14px; height: 14px; border-radius: 3px; }
.group-header h3 { margin: 0; font-size: 0.95rem; font-weight: 500; color: var(--fg); }
.group-header .count { font-size: 0.78rem; color: var(--muted); margin-left: auto; }
.group-explain { font-size: 0.85rem; color: var(--muted); margin-bottom: 14px; line-height: 1.55; }
.activity-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }
.activity-card { background: var(--card); border: 1px solid var(--line); border-radius: 3px; padding: 14px 16px; cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.activity-card:hover { border-color: var(--line); box-shadow: none; }
.activity-card.engine { border-left: 2px solid var(--fg); }
.activity-card .label { font-weight: 500; font-size: 0.9rem; line-height: 1.4; margin-bottom: 6px; color: var(--fg); }
.activity-card .ai-label { font-size: 0.75rem; color: var(--muted); }
.activity-card.engine .ai-label { color: var(--fg); font-weight: 500; }

.candidate-card { background: var(--card); border: 1px solid var(--line); border-left: 2px solid var(--fg); border-radius: 3px; padding: 16px 20px; margin-bottom: 10px; cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.candidate-card:hover { border-color: var(--line); box-shadow: none; border-left-color: var(--fg); }
.candidate-card .name { font-weight: 500; font-size: 0.95rem; margin-bottom: 6px; color: var(--fg); }
.candidate-card .meta { font-size: 0.85rem; color: var(--muted); line-height: 1.5; }

.modal-backdrop { position: fixed; inset: 0; background: rgba(23,23,23,0.32); display: none; align-items: flex-start; justify-content: center; padding: 60px 16px 16px; z-index: 100; overflow-y: auto; backdrop-filter: blur(4px); }
.modal-backdrop.open { display: flex; animation: pn-fade 0.2s ease; }
.modal { background: var(--card); border-radius: 4px; border: 1px solid var(--line); max-width: 720px; width: 100%; padding: 32px; box-shadow: none; animation: pn-pop 0.25s ease; }
.modal .close { float: right; background: transparent; border: 0; cursor: pointer; font-size: 1.5rem; color: var(--muted); margin: -10px -10px 0 0; padding: 0; }
.modal .close:hover { color: var(--fg); background: transparent; }
.modal h3 { margin: 0 0 4px; font-size: 1.4rem; font-weight: 600; letter-spacing: -0.01em; }
.modal .kind { font-size: 0.78rem; color: var(--muted); margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.04em; }
.modal .section-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 500; margin-top: 18px; margin-bottom: 6px; }
.modal .desc { font-size: 0.92rem; line-height: 1.7; color: var(--fg); }
.modal .narration { font-size: 0.92rem; line-height: 1.65; color: var(--fg); }
.modal .narration strong { font-weight: 500; color: var(--fg); }
.modal .citation { font-size: 0.82rem; color: var(--muted); margin-top: 8px; padding-left: 14px; border-left: 2px solid var(--line); line-height: 1.55; }
.modal .citation em { color: var(--muted); }
.modal .data-block { background: var(--bg-soft); padding: 16px 18px; border-radius: 3px; margin-top: 10px; font-size: 0.85rem; border: 1px solid var(--line); }
.modal .data-block .help { font-size: 0.82rem; color: var(--muted); line-height: 1.55; margin-bottom: 10px; }
.modal .data-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.modal .data-table th, .modal .data-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); }
.modal .data-table th { color: var(--muted); font-weight: 500; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; background: var(--bg-soft); }
.modal .data-table .num { font-family: ui-monospace, SF Mono, Menlo, monospace; }
.modal .data-table .small-sample { color: var(--fg); font-weight: 500; }
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>{title}</h1>
      <div class="anchor-line">{anchor_id}</div>
      <p class="description">{description}</p>
    </header>

    <div class="intro">
      <h2>Cosa stai guardando</h2>
      <p>Questa pagina è un'<strong>analisi</strong> di un processo dell'organizzazione. Non è una proposta di cambiamento, è un'analisi di come funziona oggi e di dove l'AI potrebbe cambiarlo davvero.</p>

      <p>La domanda di partenza è una sola: <strong>per questo processo, qual è il pezzo più costoso — fare il lavoro, o tenere allineati i team che lo fanno?</strong> La risposta cambia tutto, perché l'AI può fare due cose molto diverse e non vanno confuse.</p>

      <h3 style="margin-top: 22px;">Le due cose che l'AI può fare (e non vanno confuse)</h3>

      <p><strong>Acceleratore.</strong> L'AI rende un singolo lavoro più veloce dentro un team: redige un documento, riassume una call, cerca un dato. Il team va più veloce. Ma il modo in cui i team si allineano fra loro — i passaggi di fascicoli, le riunioni di coordinamento, le ricostruzioni di contesto — rimane uguale. Utile, non strategico.</p>

      <p><strong>Infrastruttura di coordinamento.</strong> L'AI trasforma la conoscenza dell'organizzazione in qualcosa di condiviso: non più documenti che si rincorrono fra team, ma una memoria comune che ogni team interroga in tempo reale. Questo dissolve un vincolo strutturale. La regola classica "più autonomia di un team = meno allineamento col resto" cessa di valere. Cambia come l'organizzazione tiene insieme i suoi pezzi.</p>

      <div class="pull">L'errore più frequente è dispiegare l'AI come acceleratore in alcuni reparti pensando di averla messa come infrastruttura. Risultato: alcuni reparti corrono, altri no, e l'asimmetria di velocità peggiora il problema di allineamento.</div>

      <h3>Cosa tiene legata un'attività al processo</h3>
      <p>Non tutte le attività sono uguali. Per ognuna ho identificato cosa <em>la tiene legata</em> al processo attuale, scegliendo fra tre cose:</p>
      <ul style="font-size: 14.5px; line-height: 1.65; padding-left: 24px; margin: 0 0 12px;">
        <li><strong>Risorsa o competenza rara</strong> — solo poche persone (o pochi fornitori) possono farla, perché serve un'abilitazione, una competenza rara, o una relazione esclusiva.</li>
        <li><strong>Rischio di sbagliare</strong> — sbagliare ha conseguenze serie (legali, reputazionali, finanziarie); serve verifica a strati e qualcuno che firmi.</li>
        <li><strong>Costo di tenere allineati team diversi</strong> — l'attività in sé non è difficile, il pezzo costoso è il coordinamento fra chi sta a monte e chi sta a valle.</li>
      </ul>

      <h3>Da dove vengono le letture sull'AI</h3>
      <p>Quando dico che l'AI è "acceleratore" o "infrastruttura" su una specifica attività, mi appoggio a un campione di osservazione: i ricercatori di Anthropic hanno raccolto un campione di conversazioni pubbliche con Claude e hanno classificato che tipo di lavoro veniva fatto e con quanta autonomia (1 = AI assiste, 5 = AI lavora sola). Per ogni attività dell'organizzazione ho cercato la mansione più vicina in quel campione. <strong>Ogni numero che leggi nel dettaglio ha la sua scala dichiarata</strong> e dice esplicitamente quanto è ampio il campione (sotto le 100 conversazioni segnalo che il dato è fragile).</p>

      <p style="font-style: italic; color: var(--muted); margin-top: 18px;">Click su qualsiasi attività o riconfigurazione per leggere il dettaglio: che attività è, cosa la tiene legata al processo, che effetto ha l'AI, e da quali numeri viene l'analisi.</p>
    </div>

    <div class="panel">
      <h2>Le attività di questo processo, raggruppate per cosa le tiene legate</h2>
      <p class="panel-hint">La barra mostra come si divide il processo: quante attività dipendono da una risorsa rara, quante dal rischio di sbagliare, quante dal costo di tenere allineati team diversi. Più la barra verde (allineamento) è grande, più il processo può beneficiare di un'AI dispiegata come infrastruttura di coordinamento.</p>
      {dist_bar}
      {dist_legend}

      <h3 style="margin-top: 24px;">Come funziona oggi questo processo</h3>
      {bundle_state_html}
    </div>

    <div class="ledger">
      <h2>Le attività una per una</h2>
      <p class="panel-hint">Sotto, ogni attività del processo. È raggruppata per cosa la tiene legata oggi, e per ognuna è marcata l'effetto AI: <strong>infrastruttura</strong> (l'AI cambia struttura), <strong>acceleratore</strong> (cambia velocità non struttura), o <strong>non rilevante</strong>. Click su una card per leggere cosa è davvero quell'attività e perché l'analisi sta in piedi.</p>
      {groups_html}
    </div>

    <div class="candidates">
      <h2>Punti dove l'AI cambierebbe struttura ({n_engines})</h2>
      <p class="panel-hint">Sono le attività dove l'AI, secondo i dati osservati, può fare più che accelerare: può trasformare il modo in cui la conoscenza viene condivisa fra team, e quindi sciogliere un vincolo che oggi tiene insieme il processo in un certo modo. Click su una card per leggere quale vincolo specifico verrebbe sciolto.</p>
      {engines_html}
    </div>

    <div class="candidates">
      <h2>Opzioni di direzione ({n_rebundles})</h2>
      <p class="panel-hint">Sotto ci sono opzioni di come potresti rimettere insieme questo processo, ognuna con un livello diverso di cambiamento (da conservativa a radicale). Sono <strong>opzioni</strong>, non raccomandazioni: l'organizzazione decide. Per ognuna leggi cosa cambia per chi lavora nel processo, cosa resta vincolante anche dopo, e quanto è rischiosa. Click per il dettaglio.</p>
      {rebundles_html}
    </div>
  </div>

  <div class="modal-backdrop" id="modal-backdrop">
    <div class="modal">
      <button class="close" id="modal-close">×</button>
      <div id="modal-body"></div>
    </div>
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

function renderActivityModal(node) {{
  const pc = node.primary_constraint;
  const km = node.km_cost_dominant;
  const ac = node.ai_classification;
  let html = `<h3>${{escapeHtml(node.label)}}</h3>`;
  let kindLine = 'Attività del processo';
  html += `<div class="kind">${{escapeHtml(kindLine)}}</div>`;

  // 1. Cosa è
  if (node._body || node._description) {{
    html += `<div class="section-label">Che attività è</div>`;
    html += `<div class="desc">${{escapeHtml(node._body || node._description)}}</div>`;
  }}

  // 2. Cosa la tiene legata al processo
  if (pc) {{
    html += `<div class="section-label">Cosa la tiene legata al processo attuale</div>`;
    html += `<div class="narration"><strong>${{CONSTRAINT_LABEL[pc]}}.</strong> ${{escapeHtml(CONSTRAINT_PLAIN[pc])}}</div>`;
    if (node.constraint_evidence && node.constraint_evidence.length) {{
      for (const e of node.constraint_evidence) {{
        html += `<div class="citation">${{escapeHtml(e.claim || '')}} <em>(fonte: ${{escapeHtml(e.source || '')}})</em></div>`;
      }}
    }}
  }}

  // 3. Dove si paga il costo
  if (km && km !== 'none') {{
    html += `<div class="section-label">Dove si paga il costo principale di quest'attività</div>`;
    html += `<div class="narration">${{escapeHtml(KM_LABEL[km])}}.</div>`;
  }}

  // 4. Effetto AI
  if (ac) {{
    html += `<div class="section-label">Che effetto ha l'AI su quest'attività</div>`;
    html += `<div class="narration"><strong>${{escapeHtml(AI_CLASS_LABEL[ac])}}.</strong> ${{escapeHtml(AI_CLASS_PLAIN[ac])}}</div>`;
    if (node.ai_evidence && node.ai_evidence.length) {{
      for (const e of node.ai_evidence) {{
        html += `<div class="citation">${{escapeHtml(e.claim || '')}}</div>`;
      }}
    }}
  }}

  // 5. Dato osservativo
  if (node._aei && node._aei.top_matches && node._aei.top_matches.length) {{
    html += `<div class="section-label">Da cosa viene questa analisi</div>`;
    html += `<div class="data-block">`;
    html += `<div class="help">Per quest'attività ho cercato la mansione più vicina nel campione di conversazioni Claude raccolto da Anthropic. Sotto vedi le mansioni più simili (catalogo americano dei mestieri, descritto in inglese), quanto sono semanticamente vicine, quanto Claude ha lavorato in autonomia (scala 1 = solo assistenza, 5 = lavoro autonomo), e su quante conversazioni Claude.ai è basata l'osservazione (sotto 100 conversazioni il dato è fragile).</div>`;
    html += `<table class="data-table"><thead><tr><th>Mansione vicina</th><th>Vicinanza</th><th>Autonomia AI</th><th>Conversazioni</th></tr></thead><tbody>`;
    for (const m of node._aei.top_matches) {{
      const sim = m.similarity != null ? Math.round(Number(m.similarity) * 100) + '%' : '—';
      let aut = '<span style="color:#999">—</span>';
      if (m.ai_autonomy_mean != null) {{
        aut = `<span class="num">${{Number(m.ai_autonomy_mean).toFixed(1)}}/5</span>`;
      }}
      let cnt = '<span style="color:#999">0</span>';
      if (m.count != null && m.count > 0) {{
        const c = Math.round(m.count);
        cnt = c < 100 ? `<span class="num small-sample">${{c}} (campione piccolo)</span>` : `<span class="num">${{c}}</span>`;
      }}
      html += `<tr><td>${{escapeHtml((m.task||'').slice(0,110))}}</td><td class="num">${{sim}}</td><td>${{aut}}</td><td>${{cnt}}</td></tr>`;
    }}
    html += `</tbody></table></div>`;
  }}

  return html;
}}

function renderRebundleModal(rb) {{
  let html = `<h3>${{escapeHtml(rb.name)}}</h3>`;
  html += `<div class="kind">Riconfigurazione possibile del processo</div>`;
  if (rb.description) {{
    html += `<div class="section-label">Cosa propone</div>`;
    html += `<div class="desc">${{escapeHtml(rb.description)}}</div>`;
  }}
  if (rb.activities && rb.activities.length) {{
    html += `<div class="section-label">Le attività che si aggregano nel nuovo modo</div>`;
    html += `<ul style="font-size:14px; padding-left: 22px; margin: 6px 0;">`;
    for (const aid of rb.activities) {{
      const n = NODES[aid];
      html += `<li>${{escapeHtml(n ? n.label : aid)}}</li>`;
    }}
    html += `</ul>`;
  }}
  if (rb.enabled_by_engine) {{
    const eng = ENGINES.find(e => e.component_id === rb.enabled_by_engine);
    const dissolved = eng?.dissolves_constraint;
    html += `<div class="section-label">Cosa lo rende possibile</div>`;
    html += `<div class="narration">L'attività <strong>${{eng ? escapeHtml(NODES[eng.component_id]?.label || eng.component_id) : '—'}}</strong>`;
    if (dissolved) {{
      html += `, dispiegata come infrastruttura di coordinamento, scioglie il vincolo "${{escapeHtml(CONSTRAINT_LABEL[dissolved] || dissolved)}}" che oggi tiene insieme il processo nella forma attuale.`;
    }} else {{
      html += `.`;
    }}
    html += `</div>`;
  }}
  if (rb.remaining_binding_constraint) {{
    html += `<div class="section-label">Cosa resta vincolante anche dopo la riconfigurazione</div>`;
    html += `<div class="narration"><strong>${{escapeHtml(CONSTRAINT_LABEL[rb.remaining_binding_constraint] || rb.remaining_binding_constraint)}}.</strong> ${{escapeHtml(CONSTRAINT_PLAIN[rb.remaining_binding_constraint] || '')}}</div>`;
  }}
  if (rb.autonomy_coordination_mode) {{
    html += `<div class="section-label">In che modalità lavorerebbe questo nuovo processo</div>`;
    const mode = rb.autonomy_coordination_mode;
    const modeLabel = mode === 'flywheel'
      ? 'Modello AI-mediato — autonomia e allineamento insieme'
      : 'Modello tradizionale — o autonomia o allineamento';
    const modePlain = mode === 'flywheel'
      ? 'Una conoscenza condivisa accessibile in tempo reale permette ai team di restare allineati senza perdere autonomia.'
      : 'Resta valida la regola classica: più autonomia di un team = meno allineamento col resto.';
    html += `<div class="narration"><strong>${{modeLabel}}.</strong> ${{modePlain}}</div>`;
  }}
  if (rb.what_changes) {{
    html += `<div class="section-label">Cosa cambia per chi lavora nel processo</div>`;
    html += `<div class="desc">${{escapeHtml(rb.what_changes)}}</div>`;
  }}
  if (rb.risk_of_rebundle) {{
    html += `<div class="section-label">Quanto è rischioso riconfigurare</div>`;
    html += `<div class="desc">${{escapeHtml(rb.risk_of_rebundle)}}</div>`;
  }}
  return html;
}}

document.addEventListener('click', (e) => {{
  const card = e.target.closest('.activity-card');
  if (card) {{
    const id = card.dataset.id;
    const n = NODES[id];
    if (n) {{
      document.getElementById('modal-body').innerHTML = renderActivityModal(n);
      document.getElementById('modal-backdrop').classList.add('open');
    }}
    return;
  }}
  const eng = e.target.closest('.candidate-card[data-id]');
  if (eng) {{
    const id = eng.dataset.id;
    const n = NODES[id];
    if (n) {{
      document.getElementById('modal-body').innerHTML = renderActivityModal(n);
      document.getElementById('modal-backdrop').classList.add('open');
    }}
    return;
  }}
  const rb = e.target.closest('.candidate-card[data-rb]');
  if (rb) {{
    const idx = parseInt(rb.dataset.rb, 10);
    const data = REBUNDLES[idx];
    if (data) {{
      document.getElementById('modal-body').innerHTML = renderRebundleModal(data);
      document.getElementById('modal-backdrop').classList.add('open');
    }}
  }}
}});
document.getElementById('modal-close').addEventListener('click', () => document.getElementById('modal-backdrop').classList.remove('open'));
document.getElementById('modal-backdrop').addEventListener('click', (e) => {{ if (e.target.id === 'modal-backdrop') document.getElementById('modal-backdrop').classList.remove('open'); }});
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') document.getElementById('modal-backdrop').classList.remove('open'); }});
</script>
</body>
</html>"""


def render_html(d: dict) -> str:
    anchor = d.get("_anchor", {})
    title = anchor.get("title") or "Processo"
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
            f'<div><strong>{CONSTRAINT_LABEL[ct]}</strong> <span class="count">— {n} attività</span><br>'
            f'<span style="font-size:13px; color: var(--muted);">{CONSTRAINT_PLAIN[ct]}</span></div></div>'
        )
    dist_bar = f'<div class="dist-bar">{"".join(bar_segs)}</div>'
    dist_legend = f'<div class="dist-legend">{"".join(legend_items)}</div>'

    # Bundle state
    bd = d.get("bundle_state") or {}
    bd_blocks = []
    if bd.get("current_mode"):
        mode = bd["current_mode"]
        bd_blocks.append(
            f'<div class="stat"><div class="key">Modalità di funzionamento</div>'
            f'<div class="val"><strong>{escape(MODE_LABEL.get(mode, mode))}</strong>. {escape(MODE_PLAIN.get(mode, ""))}</div></div>'
        )
    me = bd.get("mode_evidence") or []
    if me:
        ev_text = []
        for e in me:
            cl = e.get("claim", "") if isinstance(e, dict) else str(e)
            src = e.get("source", "") if isinstance(e, dict) else ""
            ev_text.append(f'{escape(cl)} <span style="color:var(--muted); font-size:12px;">(fonte: {escape(src)})</span>')
        bd_blocks.append(
            f'<div class="stat"><div class="key">Su cosa si basa questa analisi</div>'
            f'<div class="val">{"<br><br>".join(ev_text)}</div></div>'
        )
    cpr = bd.get("coordination_paradox_risk")
    if cpr:
        bd_blocks.append(
            f'<div class="stat engine" style="grid-column: 1 / -1;">'
            f'<div class="key">Trappola da evitare nel dispiegare l\'AI</div>'
            f'<div class="val">{escape(cpr)}</div></div>'
        )
    bundle_state_html = f'<div class="stat-row">{"".join(bd_blocks)}</div>' if bd_blocks else ""

    # Groups by constraint with explanatory paragraph
    groups_html_parts = []
    group_order = ("coordination", "risk", "scarcity")
    group_explanations = {
        "coordination": "Per queste attività, il pezzo costoso non è fare l'attività: è coordinare il passaggio di informazioni e decisioni con altri team. Sono i candidati naturali per l'AI come infrastruttura di coordinamento.",
        "risk": "Per queste attività, sbagliare ha conseguenze serie. L'AI può aiutare a preparare e a controllare, ma la responsabilità finale resta umana — il vincolo non è dissolvibile.",
        "scarcity": "Per queste attività, serve qualcuno con una competenza, un'abilitazione o una relazione che non si scala. L'AI può supportare ma non sostituire chi possiede la risorsa rara.",
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
                f'<div class="ai-label">AI come {escape(ai_label_short)}</div>'
                f'</div>'
            )
        groups_html_parts.append(
            f'<div class="group">'
            f'<div class="group-header">'
            f'<span class="swatch" style="background: var(--{ct})"></span>'
            f'<h3>{CONSTRAINT_LABEL[ct]}</h3>'
            f'<span class="count">{len(in_group)} attività</span>'
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
            f'<div class="ai-label">non classificata</div>'
            f'</div>' for c in unset
        )
        groups_html_parts.append(
            f'<div class="group">'
            f'<div class="group-header"><h3>Non classificate</h3>'
            f'<span class="count">{len(unset)} attività</span></div>'
            f'<div class="activity-grid">{cards}</div></div>'
        )
    groups_html = "\n".join(groups_html_parts) if groups_html_parts else "<p>Nessuna attività in scope.</p>"

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
            f'<div class="candidate-card" data-id="{escape(cid)}">'
            f'<div class="name">{escape(c.get("label", ""))}</div>'
            f'<div class="meta">Dispiegata come infrastruttura, scioglie: <strong>{escape(CONSTRAINT_LABEL.get(dissolves, dissolves))}</strong></div>'
            f'</div>'
        )
    engines_html = "\n".join(engine_cards) if engine_cards else "<p style='color:var(--muted); font-size: 13px;'>Nessun punto identificato dove l'AI cambierebbe la struttura del processo. Tutti gli usi AI individuati sono acceleratori. Vedi la trappola sopra: dispiegare acceleratori senza infrastruttura può peggiorare il processo invece di migliorarlo.</p>"

    # Rebundle candidates
    rebundles = d.get("rebundle_candidates") or []
    rb_cards = []
    for i, rb in enumerate(rebundles):
        rc = rb.get("remaining_binding_constraint", "")
        rb_cards.append(
            f'<div class="candidate-card" data-rb="{i}">'
            f'<div class="name">{escape(rb.get("name", "?"))}</div>'
            f'<div class="meta">Cosa resta vincolante: <strong>{escape(CONSTRAINT_LABEL.get(rc, rc))}</strong> · '
            f'Riguarda {len(rb.get("activities") or [])} attività</div>'
            f'</div>'
        )
    rebundles_html = "\n".join(rb_cards) if rb_cards else "<p style='color:var(--muted); font-size: 13px;'>Nessuna riconfigurazione proposta — richiede almeno un punto AI dispiegato come infrastruttura.</p>"

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
    args = parser.parse_args()

    d = json.loads(Path(args.map).read_text(encoding="utf-8"))
    html = render_html(d)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"Wrote {Path(args.html).resolve()} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
