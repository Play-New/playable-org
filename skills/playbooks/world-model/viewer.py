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
/* Legacy variable bridge — keeps the existing rules below tied to Play New tokens. */
:root {
  --bg: var(--bg-soft);
  --fg: var(--fg);
  --muted: var(--muted);
  --line: var(--line);
  --card: var(--bg);
  --accent: var(--fg);
  --moat: #c47558;
  --commodity: var(--soft);
  --layer-stakeholder-bg: var(--fg); --layer-stakeholder-fg: var(--bg);
  --layer-interface-bg: #f5f8fc; --layer-interface-border: #c7d4ec;
  --layer-intelligence-bg: #f6f4fb; --layer-intelligence-border: #c4bcd9;
  --layer-worldmodel-bg: #f3f7f1; --layer-worldmodel-border: #c0d3b9;
  --layer-capability-bg: #f8f3e8; --layer-capability-border: #d8c89e;
  --principle-bg: #fbe8dd; --principle-border: #c47558;
}

body { background: var(--bg-soft); }

.container { max-width: 1280px; margin: 0 auto; padding: 48px 32px 80px; }
.scope-line { font-size: 0.78rem; color: var(--muted); font-family: ui-monospace, SF Mono, Menlo, monospace; text-transform: uppercase; letter-spacing: 0.04em; }

header { padding-bottom: 24px; border-bottom: 1px solid var(--line); margin-bottom: 32px; }
header h1 { font-size: 1.9rem; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 6px; }

.intro, .layer-block, .signals-block { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 28px 32px; margin-bottom: 22px; }
.intro p { font-size: 0.95rem; line-height: 1.7; margin: 0 0 12px; color: var(--fg); }
.intro .pull { background: var(--bg-soft); border-left: 2px solid var(--fg); padding: 14px 18px; margin: 18px 0; font-size: 0.95rem; color: var(--fg); }
.intro h2 { font-size: 1.15rem; font-weight: 500; margin-bottom: 12px; letter-spacing: -0.01em; }

.stack { display: flex; flex-direction: column; gap: 14px; }
.stack-layer { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 0; overflow: hidden; transition: border-color 0.2s ease; }
.stack-layer:hover { border-color: var(--line); }
.stack-layer .layer-head { padding: 16px 24px 14px; border-bottom: 1px solid var(--line); display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
.stack-layer .layer-head .layer-name { font-size: 0.95rem; font-weight: 500; letter-spacing: -0.01em; }
.stack-layer .layer-head .layer-hint { font-size: 0.82rem; color: var(--muted); flex: 1; min-width: 200px; line-height: 1.55; }
.stack-layer .layer-body { padding: 20px 24px 24px; }
.layer-explainer { font-size: 0.92rem; color: var(--fg); line-height: 1.65; margin: 0 0 12px; max-width: 780px; }
.layer-explainer strong { font-weight: 500; color: var(--fg); }
.il-section-hint { font-size: 0.82rem; color: var(--muted); margin-bottom: 10px; line-height: 1.55; }

.stack-layer.layer-stakeholders .layer-head { background: var(--bg-soft); border-left: 3px solid var(--fg); }
.stack-layer.layer-interfaces .layer-head { background: var(--layer-interface-bg); border-left: 3px solid var(--layer-interface-border); }
.stack-layer.layer-intelligence .layer-head { background: var(--layer-intelligence-bg); border-left: 3px solid var(--layer-intelligence-border); }
.stack-layer.layer-worldmodel .layer-head { background: var(--layer-worldmodel-bg); border-left: 3px solid var(--layer-worldmodel-border); }
.stack-layer.layer-capabilities .layer-head { background: var(--layer-capability-bg); border-left: 3px solid var(--layer-capability-border); }

.principle-block { background: var(--principle-bg); border: 1px solid var(--principle-border); border-radius: 8px; padding: 20px 24px; margin: 22px 0; }
.principle-block .label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: #8c4a30; font-weight: 600; margin-bottom: 6px; }
.principle-block .text { font-size: 0.95rem; color: var(--fg); line-height: 1.6; }

.frame-diagram { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 22px; margin: 0 0 22px; text-align: center; }
.frame-diagram svg { max-width: 100%; height: auto; display: block; margin: 0 auto; }
.frame-diagram-caption { font-size: 0.82rem; color: var(--muted); margin-top: 14px; }

.stakeholder-row, .interface-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.stakeholder { background: var(--layer-stakeholder-bg); color: var(--layer-stakeholder-fg); padding: 7px 14px; border-radius: 999px; font-size: 0.8rem; font-weight: 500; cursor: pointer; transition: opacity 0.15s; }
.stakeholder:hover { opacity: 0.82; }

.interface { background: var(--card); border: 1px solid var(--layer-interface-border); border-left: 2px solid var(--layer-interface-border); border-radius: 3px; padding: 7px 14px; font-size: 0.82rem; cursor: pointer; color: var(--fg); transition: background 0.15s; }
.interface:hover { background: var(--layer-interface-bg); }

.il-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.il-section .il-title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin-bottom: 8px; font-weight: 500; }
.il-card { background: var(--card); border: 1px solid var(--line); border-radius: 3px; padding: 12px 14px; margin-bottom: 8px; font-size: 0.85rem; cursor: pointer; transition: border-color 0.15s; }
.il-card:hover { border-color: var(--line); }
.il-card.potential { border-left: 2px solid var(--fg); }
.il-card .trigger { font-weight: 500; margin-bottom: 4px; color: var(--fg); }
.il-card .meta { font-size: 0.75rem; color: var(--muted); }

.wm-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.wm-section .wm-title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin-bottom: 8px; font-weight: 500; }
.wm-card { background: var(--card); border: 1px solid var(--line); border-radius: 3px; padding: 12px 14px; margin-bottom: 8px; font-size: 0.85rem; }
.wm-card .label { font-weight: 500; margin-bottom: 2px; color: var(--fg); }
.wm-card .meta { font-size: 0.75rem; color: var(--muted); }

.cap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.cap-card { background: var(--card); border: 1px solid var(--line); border-radius: 3px; padding: 14px 16px; cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; border-left: 2px solid var(--commodity); }
.cap-card.moat { border-left-color: var(--moat); }
.cap-card:hover { border-color: var(--line); box-shadow: none; }
.cap-card .name { font-weight: 600; font-size: 0.9rem; font-family: ui-monospace, SF Mono, Menlo, monospace; margin-bottom: 6px; color: var(--fg); }
.cap-card .desc { font-size: 0.85rem; color: var(--fg); line-height: 1.5; margin-bottom: 10px; }
.cap-card .meta { display: flex; flex-wrap: wrap; gap: 6px; font-size: 0.7rem; }
.cap-card .pill { background: var(--bg-soft); padding: 2px 8px; border-radius: 999px; color: var(--muted); border: 1px solid var(--line); font-weight: 500; letter-spacing: 0.02em; }
.cap-card .pill.moat { background: var(--moat); color: white; border-color: var(--moat); }
.cap-card .pill.commodity { background: var(--bg-soft); color: var(--muted); }

.signals-block { border-left: 2px solid var(--fg); }
.signal-card { background: var(--card); border: 1px solid var(--line); border-radius: 3px; padding: 14px 16px; margin-bottom: 10px; cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.signal-card:hover { border-color: var(--line); box-shadow: none; }
.signal-card .trigger { font-weight: 500; font-size: 0.92rem; margin-bottom: 6px; color: var(--fg); }
.signal-card .missing { font-size: 0.78rem; color: var(--fg); font-family: ui-monospace, SF Mono, Menlo, monospace; }

.modal-backdrop { position: fixed; inset: 0; background: rgba(23,23,23,0.32); display: none; align-items: flex-start; justify-content: center; padding: 60px 16px 16px; z-index: 100; overflow-y: auto; backdrop-filter: blur(4px); }
.modal-backdrop.open { display: flex; animation: pn-fade 0.2s ease; }
.modal { background: var(--card); border-radius: 4px; border: 1px solid var(--line); max-width: 760px; width: 100%; padding: 32px; box-shadow: none; animation: pn-pop 0.25s ease; }
.modal .close { float: right; background: transparent; border: 0; cursor: pointer; font-size: 1.5rem; color: var(--muted); margin: -10px -10px 0 0; padding: 0; }
.modal .close:hover { color: var(--fg); background: transparent; }
.modal h3 { margin: 0 0 4px; font-size: 1.4rem; font-weight: 600; letter-spacing: -0.01em; }
.modal .subtitle { font-size: 0.82rem; color: var(--muted); margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.04em; }
.modal .section-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 500; margin-top: 18px; margin-bottom: 6px; }
.modal .desc { font-size: 0.92rem; line-height: 1.65; color: var(--fg); }
.modal .contract { background: var(--bg-soft); padding: 14px 16px; border-radius: 3px; margin-top: 6px; border: 1px solid var(--line); }
.modal .contract dl { margin: 0; display: grid; grid-template-columns: 140px 1fr; gap: 8px 16px; font-size: 0.85rem; }
.modal .contract dt { color: var(--muted); margin: 0; font-weight: 500; }
.modal .contract dd { margin: 0; color: var(--fg); }
.modal .pill-row { display: flex; flex-wrap: wrap; gap: 6px; }
.modal .pill { background: var(--bg-soft); padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; color: var(--fg); border: 1px solid var(--line); }
.modal .citation { font-size: 0.75rem; color: var(--muted); font-family: ui-monospace, SF Mono, Menlo, monospace; padding: 4px 0; }
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
      <div class="scope-line">scope: {scope} · {n_caps} capabilities · {n_signals} segnali di fallimento</div>
    </header>

    <div class="intro">
      <h2>Cosa stai guardando</h2>
      <p>Questa pagina rappresenta l'organizzazione come la descriverebbe un modello operativo basato su quattro componenti, applicato alla sostanza dell'organizzazione invece che al suo organigramma.</p>
      <p>Il modello viene da un articolo di Jack Dorsey e Roelof Botha pubblicato nel marzo 2026 (Block, "From Hierarchy to Intelligence"). L'idea centrale è che le organizzazioni grandi sono tenute insieme da gerarchie che fanno routing di informazione, e che l'AI può sostituire quel routing rendendo la conoscenza un sistema condiviso. La struttura che emerge ha quattro livelli, raffigurati nello stack qui sotto.</p>
      <p><strong>Capabilities (in basso).</strong> Le funzioni invocabili dell'organizzazione, ognuna con un contratto pubblico (input, output, target di servizio, vincoli regolatori). Sono atomiche e componibili: chi ha un'esigenza compone più capabilities per ottenerne una soluzione.</p>
      <p><strong>World model (sopra le capabilities).</strong> Come l'organizzazione capisce sé stessa (operazioni, performance, priorità) e come capisce i propri stakeholder (donatori, clienti, ricercatori, partner). I segnali più onesti sono comportamenti registrati, non opinioni dichiarate.</p>
      <p><strong>Intelligence layer (sopra il world model).</strong> Il pezzo che, quando il world model rileva un segnale, compone le capabilities giuste per rispondere. Oggi è quasi sempre umano-mediato (riunioni, fascicoli che si passano fra team). Quando diventa un sistema, l'organizzazione non ha più bisogno di un livello di middle management.</p>
      <p><strong>Interfaces (in alto).</strong> Le superfici di delivery: web, app, telefono, eventi fisici, posta. Importanti ma non è qui che vive il valore: la valuta vera è nelle capabilities e nel world model.</p>
      <div class="pull">Il roadmap futuro non è il piano triennale che il top management decide. È la lista delle composizioni che oggi falliscono perché manca una capability. Quei "segnali di fallimento" sono il backlog reale, e li trovi nel pannello a destra di questa pagina.</div>
      <p style="font-style: italic; color: var(--muted);">Click su qualsiasi elemento dello stack o un segnale di fallimento per leggere il dettaglio: cos'è, chi può chiamarlo, quale contratto ha, quali sono le evidenze nella struttura.</p>
    </div>

    <!-- CONCEPTUAL FRAME DIAGRAM -->
    <div class="frame-diagram">
      {frame_diagram_svg}
      <div class="frame-diagram-caption">Il modello operativo a quattro layer. La pagina sotto è la stessa struttura applicata a questa organizzazione, popolata con dati reali della struttura.</div>
    </div>

    <!-- THE STACK -->
    <div class="stack">

      <div class="stack-layer layer-stakeholders">
        <div class="layer-head">
          <div class="layer-name">Stakeholder</div>
          <div class="layer-hint">Chi usa l'organizzazione e in cambio le fornisce qualcosa. Nel modello Dorsey ogni stakeholder è entrambe le cose contemporaneamente: utente e contributore.</div>
        </div>
        <div class="layer-body">
          <p class="layer-explainer">Nella vecchia distinzione, un'organizzazione ha clienti che ricevono valore e dipendenti che lo producono. In questo modello l'asimmetria sparisce: ogni tipo di stakeholder <strong>usa qualcosa</strong> dell'organizzazione (capability invocate) e <strong>contribuisce qualcosa</strong> in cambio (un segnale, un'azione, un dato che alimenta il world model). Il contributo dello stakeholder rende l'organizzazione più capace di servire bene il prossimo stakeholder simile, e così via: il ciclo si auto-rinforza.</p>
          <p class="layer-explainer">Click su un tipo di stakeholder per leggere: cosa è, cosa ottiene dall'organizzazione, cosa restituisce, qual è il segnale più onesto che l'organizzazione registra di lui, quanta maturità ha la rappresentazione del world model lato stakeholder oggi, e dove vive frammentata fra team diversi.</p>
          <div class="stakeholder-row">{stakeholders_html}</div>
        </div>
      </div>

      <div class="stack-layer layer-interfaces">
        <div class="layer-head">
          <div class="layer-name">Interfaces</div>
          <div class="layer-hint">Le superfici attraverso cui le capability vengono consegnate. Non è qui che si crea valore, è qui che lo si recapita.</div>
        </div>
        <div class="layer-body">
          <div class="interface-row">{interfaces_html}</div>
        </div>
      </div>

      <div class="stack-layer layer-intelligence">
        <div class="layer-head">
          <div class="layer-name">Intelligence layer</div>
          <div class="layer-hint">Il livello che riconosce un segnale e compone più capability per produrre una risposta. È il pezzo strategico del modello: dove vive il valore prodotto dall'AI quando smette di essere acceleratore e diventa infrastruttura di coordinamento.</div>
        </div>
        <div class="layer-body">
          <p class="layer-explainer">Una "composizione" è quando l'organizzazione mette insieme più di una capability per servire una richiesta specifica. Un esempio classico: un donatore importante chiede di destinare il proprio contributo a un certo tipo di ricerca; per rispondere bene servono <em>cultivate-major-relationship</em> (per gestire la relazione 1-1), <em>review-proposal</em> (per identificare il progetto giusto), <em>publish-finding</em> (per restituire l'impatto). Tre capability composte in una soluzione singola.</p>
          <p class="layer-explainer">Le composizioni si dividono in due categorie. <strong>A sinistra</strong>, quelle che già accadono oggi attraverso il lavoro umano: riunioni di coordinamento, fascicoli che si passano fra team, comitati di handover. Sono il <em>coordination tax</em> che l'organizzazione paga in forma di tempo e attrito. <strong>A destra</strong>, quelle che potrebbero diventare automatiche quando il world model raccoglie abbastanza segnale: il sistema riconosce il trigger e attiva la composizione senza richiedere un umano che se ne accorga.</p>
          <p class="layer-explainer">Click su una composizione per leggere il trigger che la attiva, le capability che vengono messe insieme, e (per le umane) cosa fallisce oggi; (per le potenziali) la precondizione di world model che serve perché diventino sistemiche.</p>
          <div class="il-grid">
            <div class="il-section">
              <div class="il-title">Composizioni umano-mediate oggi ({n_current_compositions})</div>
              <div class="il-section-hint">Quello che l'organizzazione già fa, ma pagandolo in coordinamento umano. Ogni voce è una candidata a essere automatizzata.</div>
              {current_compositions_html}
            </div>
            <div class="il-section">
              <div class="il-title">Composizioni potenzialmente automatiche ({n_potential_compositions})</div>
              <div class="il-section-hint">Quello che l'AI potrebbe abilitare se il world model fosse abbastanza ricco. Sono le mosse strategiche di lungo termine.</div>
              {potential_compositions_html}
            </div>
          </div>
        </div>
      </div>

      <div class="stack-layer layer-worldmodel">
        <div class="layer-head">
          <div class="layer-name">World model</div>
          <div class="layer-hint">Cosa l'organizzazione sa di sé stessa e dei propri stakeholder. È la struttura che il layer di intelligenza interroga per comporre una risposta.</div>
        </div>
        <div class="layer-body">
          <div class="wm-grid">
            <div class="wm-section">
              <div class="wm-title">Lato organizzazione &mdash; maturità {company_maturity}</div>
              {company_observations_html}
            </div>
            <div class="wm-section">
              <div class="wm-title">Lato stakeholder &mdash; {customer_unified_label}</div>
              {customer_observations_html}
            </div>
          </div>
        </div>
      </div>

      <div class="stack-layer layer-capabilities">
        <div class="layer-head">
          <div class="layer-name">Capabilities</div>
          <div class="layer-hint">Le funzioni atomiche dell'organizzazione: chiunque le può chiamare e ottenere un'esecuzione. Sono i mattoni con cui l'intelligence layer costruisce le composizioni di sopra.</div>
        </div>
        <div class="layer-body">
          <p class="layer-explainer">Una capability non è "qualcosa che il team fa". È una <strong>funzione invocabile</strong>: ha un input dichiarato, un output strutturato, target di servizio (tempi, qualità, copertura), vincoli regolatori, una modalità di chiamata. Per essere considerata tale deve passare cinque proprietà: invocabile, atomica, hard to acquire, produce output strutturato, componibile con altre.</p>
          <p class="layer-explainer">Sono divise in due categorie visive. La cornice <strong style="color: #c47558;">arancione</strong> a sinistra del nome segnala una capability <strong>moat</strong>: difficile da acquisire (regolazione, network effect, anni di costruzione), differenziante per quest'organizzazione, non replicabile in tempi corti. La cornice <strong style="color: #6b6b6b;">grigia</strong> segnala una capability <strong>commodity</strong>: necessaria per operare ma non differenziante, presente in qualunque organizzazione del settore.</p>
          <p class="layer-explainer">Il valore strategico dell'organizzazione vive nelle capability moat. Le commodity sono pre-condizione, ma investirvi non sposta competitività; investire nelle moat sì.</p>
          <p class="layer-explainer">Click su una capability per leggere il contratto pubblico: <em>cosa accetta come input, cosa restituisce, target operativi, vincoli regolatori, modalità di chiamata</em>. Inoltre: chi può chiamarla, con quali altre capability si compone, quali Direzioni la ospitano oggi (questo è importante: capability che attraversano più Direzioni richiedono ridisegno organizzativo per essere esposte come funzioni atomiche).</p>
          <div class="cap-grid">{capabilities_html}</div>
        </div>
      </div>

    </div>

    <!-- SHARED PRINCIPLE -->
    <div class="principle-block">
      <div class="label">Principio condiviso</div>
      <div class="text">Sostituire il routing gerarchico delle informazioni con un sistema che accumula intelligenza nel tempo. Ogni chiamata di capability arricchisce il world model, che migliora le composizioni future, che rende le capability più utili. È un ciclo che si auto-rafforza.</div>
    </div>

    <!-- FAILURE SIGNALS -->
    <div class="signals-block">
      <h2>Segnali di fallimento &mdash; il roadmap che emerge</h2>
      <p class="layer-explainer">Un segnale di fallimento è una richiesta che l'intelligence layer (anche se oggi non esiste come sistema) tenterebbe di soddisfare componendo capability esistenti, e che <strong>fallisce perché una delle capability necessarie non c'è ancora</strong>. Ogni segnale di fallimento è quindi una <em>candidate capability</em> da costruire.</p>
      <p class="layer-explainer">È una rivoluzione di prospettiva sul roadmap. Il roadmap tradizionale viene dal top management che decide cosa l'organizzazione costruirà l'anno prossimo, sulla base di un piano triennale. Il roadmap che emerge da qui invece è la lista delle composizioni che gli stakeholder <em>già richiederebbero oggi</em> e a cui l'organizzazione non sa rispondere completamente. È un backlog generato dalla domanda, non dall'offerta.</p>
      <p class="layer-explainer">Ogni card sotto descrive: il <strong>trigger</strong> (la situazione di stakeholder che fa nascere la richiesta), la <strong>composizione tentata</strong> (quali capability esistenti il sistema metterebbe insieme), la <strong>capability mancante</strong> (cosa servirebbe in più), e l'<strong>evidenza nella struttura</strong> che la richiesta nascerebbe davvero (non è ipotetica). Click per il dettaglio completo.</p>
      {signals_html}
    </div>
  </div>

  <div class="modal-backdrop" id="modal-backdrop">
    <div class="modal">
      <button class="close" id="modal-close">×</button>
      <div id="modal-body"></div>
    </div>
  </div>

<script>
const CAPABILITIES = {capabilities_json};
const STAKEHOLDERS_BY_TYPE = {stakeholders_index_json};
const INTERFACES = {interfaces_json};
const SIGNALS = {signals_json};
const COMPOSITIONS_CURRENT = {current_compositions_json};
const COMPOSITIONS_POTENTIAL = {potential_compositions_json};

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }})[c]);
}}

function pillList(items, cls) {{
  if (!items || !items.length) return '<span style="color:var(--muted); font-size:12px;">nessuno</span>';
  return '<div class="pill-row">' + items.map(i => `<span class="pill ${{cls||''}}">${{escapeHtml(i)}}</span>`).join('') + '</div>';
}}

function renderCapabilityModal(c) {{
  let html = `<h3>${{escapeHtml(c.name)}}</h3>`;
  html += `<div class="subtitle">Capability ${{c.moat_grade === 'moat' ? '&middot; moat' : '&middot; commodity'}}</div>`;
  html += `<div class="section-label">Cos'è</div>`;
  html += `<div class="desc">${{escapeHtml(c.description || '')}}</div>`;
  html += `<div class="section-label">Contratto pubblico</div>`;
  html += `<div class="contract"><dl>`;
  html += `<dt>Input</dt><dd>${{escapeHtml(c.input || '')}}</dd>`;
  html += `<dt>Output</dt><dd>${{escapeHtml(c.output || '')}}</dd>`;
  html += `<dt>Target operativi</dt><dd>${{(c.slo_targets || []).map(t => '&bull; ' + escapeHtml(t)).join('<br>') || '<em>non dichiarati</em>'}}</dd>`;
  html += `<dt>Vincoli regolatori</dt><dd>${{(c.regulatory_constraints || []).map(t => escapeHtml(t)).join(', ') || '<em>nessuno</em>'}}</dd>`;
  html += `<dt>Modalità di chiamata</dt><dd>${{escapeHtml(c.invocation_modality || '')}}</dd>`;
  html += `</dl></div>`;
  html += `<div class="section-label">Chi può chiamarla</div>`;
  html += pillList(c.is_callable_by, 'caller');
  html += `<div class="section-label">Si compone con</div>`;
  html += pillList(c.composes_with, 'composes');
  html += `<div class="section-label">Chi la possiede oggi (struttura)</div>`;
  html += pillList(c.current_owners, 'owner');
  if (c.moat_rationale) {{
    html += `<div class="section-label">Perché è ${{c.moat_grade === 'moat' ? 'un moat' : 'commodity'}}</div>`;
    html += `<div class="desc">${{escapeHtml(c.moat_rationale)}}</div>`;
  }}
  if (c._substrate_evidence && c._substrate_evidence.length) {{
    html += `<div class="section-label">Evidenza nella struttura</div>`;
    html += c._substrate_evidence.map(p => `<div class="citation">${{escapeHtml(p)}}</div>`).join('');
  }}
  return html;
}}

function renderStakeholderModal(stype) {{
  const data = STAKEHOLDERS_BY_TYPE[stype] || {{}};
  let html = `<h3>${{escapeHtml(stype)}}</h3>`;
  html += `<div class="subtitle">Tipo di stakeholder</div>`;

  if (data.description) {{
    html += `<div class="section-label">Cos'è</div>`;
    html += `<div class="desc">${{escapeHtml(data.description)}}</div>`;
  }}

  if (data.what_they_get_from_org) {{
    html += `<div class="section-label">Cosa ottiene dall'organizzazione (lato utente)</div>`;
    html += `<div class="desc">${{escapeHtml(data.what_they_get_from_org)}}</div>`;
  }}
  if (data.what_they_contribute_back) {{
    html += `<div class="section-label">Cosa restituisce in cambio (lato contributore)</div>`;
    html += `<div class="desc">${{escapeHtml(data.what_they_contribute_back)}}</div>`;
  }}

  if (data.honest_signal) {{
    html += `<div class="section-label">Segnale più onesto registrato dall'organizzazione</div>`;
    html += `<div class="desc">${{escapeHtml(data.honest_signal)}}</div>`;
  }}
  if (data.current_maturity) {{
    const matLabel = {{high:'alta', medium:'media', low:'bassa'}}[data.current_maturity] || data.current_maturity;
    html += `<div class="section-label">Maturità della rappresentazione lato stakeholder</div>`;
    html += `<div class="desc">${{escapeHtml(matLabel)}} &mdash; ${{data.current_maturity === 'high' ? 'l\\'organizzazione ha una vista coerente di questo stakeholder' : (data.current_maturity === 'medium' ? 'l\\'organizzazione ha una vista parziale, con buchi noti' : 'l\\'organizzazione ha pochi dati strutturati su questo stakeholder')}}</div>`;
  }}
  if (data.fragmentation) {{
    html += `<div class="section-label">Frammentazione attuale fra team / sistemi</div>`;
    html += `<div class="desc">${{escapeHtml(data.fragmentation)}}</div>`;
  }}

  // Capabilities the stakeholder can invoke
  const invoked = CAPABILITIES.filter(c => (c.is_callable_by || []).includes(stype));
  if (invoked.length) {{
    html += `<div class="section-label">Capability che questo stakeholder può chiamare</div>`;
    html += pillList(invoked.map(c => c.name), 'caller');
  }}
  return html;
}}

function renderInterfaceModal(idx) {{
  const ifc = INTERFACES[idx];
  if (!ifc) return '';
  let html = `<h3>${{escapeHtml(ifc.name)}}</h3>`;
  html += `<div class="subtitle">Interface &mdash; superficie di delivery</div>`;
  if (ifc.description) {{
    html += `<div class="section-label">Cosa è</div>`;
    html += `<div class="desc">${{escapeHtml(ifc.description)}}</div>`;
  }}
  if (ifc.surfaces_capabilities && ifc.surfaces_capabilities.length) {{
    html += `<div class="section-label">Capability che attraversa</div>`;
    html += pillList(ifc.surfaces_capabilities, 'surfaces');
  }}
  if (ifc._substrate) {{
    html += `<div class="section-label">Evidenza nella struttura</div>`;
    html += `<div class="citation">${{escapeHtml(ifc._substrate)}}</div>`;
  }}
  return html;
}}

function renderSignalModal(idx) {{
  const s = SIGNALS[idx];
  if (!s) return '';
  let html = `<h3>${{escapeHtml(s.trigger || '')}}</h3>`;
  html += `<div class="subtitle">Segnale di fallimento &mdash; voce di backlog</div>`;
  html += `<div class="section-label">Composizione tentata</div>`;
  if (Array.isArray(s.composition_attempted)) {{
    html += pillList(s.composition_attempted, 'caller');
  }} else {{
    html += `<div class="desc">${{escapeHtml(s.composition_attempted || '')}}</div>`;
  }}
  html += `<div class="section-label">Capability mancante</div>`;
  html += `<div class="desc"><code style="background:var(--bg); padding:2px 6px; border-radius:4px; font-family:ui-monospace,SF Mono,Menlo,monospace;">${{escapeHtml(s.missing_capability || '')}}</code></div>`;
  if (s.what_would_be_needed) {{
    html += `<div class="section-label">Cosa servirebbe per costruirla</div>`;
    html += `<div class="desc">${{escapeHtml(s.what_would_be_needed)}}</div>`;
  }}
  if (s.substrate_evidence) {{
    html += `<div class="section-label">Evidenza che la richiesta nascerebbe</div>`;
    html += `<div class="citation">${{escapeHtml(s.substrate_evidence)}}</div>`;
  }}
  return html;
}}

function renderCompositionModal(idx, kind) {{
  const c = (kind === 'current' ? COMPOSITIONS_CURRENT : COMPOSITIONS_POTENTIAL)[idx];
  if (!c) return '';
  let html = `<h3>${{escapeHtml(c.trigger || '')}}</h3>`;
  html += `<div class="subtitle">${{kind === 'current' ? 'Composizione umano-mediata, in corso oggi' : 'Composizione potenzialmente automatizzabile'}}</div>`;
  if (c.description) {{
    html += `<div class="section-label">Descrizione</div>`;
    html += `<div class="desc">${{escapeHtml(c.description)}}</div>`;
  }}
  const caps = c.capabilities_composed || c.capabilities || [];
  if (caps.length) {{
    html += `<div class="section-label">Capability componute</div>`;
    html += pillList(caps, 'composes');
  }}
  if (c.failure_modes) {{
    html += `<div class="section-label">Cosa fallisce o è fragile oggi</div>`;
    html += `<div class="desc">${{escapeHtml(c.failure_modes)}}</div>`;
  }}
  if (c.precondition) {{
    html += `<div class="section-label">Precondizione perché diventi automatica</div>`;
    html += `<div class="desc">${{escapeHtml(c.precondition)}}</div>`;
  }}
  return html;
}}

document.addEventListener('click', (e) => {{
  const cap = e.target.closest('.cap-card');
  if (cap) {{
    const name = cap.dataset.name;
    const c = CAPABILITIES.find(x => x.name === name);
    if (c) {{
      document.getElementById('modal-body').innerHTML = renderCapabilityModal(c);
      document.getElementById('modal-backdrop').classList.add('open');
    }}
    return;
  }}
  const sh = e.target.closest('.stakeholder');
  if (sh) {{
    document.getElementById('modal-body').innerHTML = renderStakeholderModal(sh.dataset.type);
    document.getElementById('modal-backdrop').classList.add('open');
    return;
  }}
  const ifc = e.target.closest('.interface');
  if (ifc) {{
    document.getElementById('modal-body').innerHTML = renderInterfaceModal(parseInt(ifc.dataset.idx));
    document.getElementById('modal-backdrop').classList.add('open');
    return;
  }}
  const sig = e.target.closest('.signal-card');
  if (sig) {{
    document.getElementById('modal-body').innerHTML = renderSignalModal(parseInt(sig.dataset.idx));
    document.getElementById('modal-backdrop').classList.add('open');
    return;
  }}
  const comp = e.target.closest('.il-card');
  if (comp) {{
    document.getElementById('modal-body').innerHTML = renderCompositionModal(parseInt(comp.dataset.idx), comp.dataset.kind);
    document.getElementById('modal-backdrop').classList.add('open');
    return;
  }}
}});
document.getElementById('modal-close').addEventListener('click', () => document.getElementById('modal-backdrop').classList.remove('open'));
document.getElementById('modal-backdrop').addEventListener('click', (e) => {{ if (e.target.id === 'modal-backdrop') document.getElementById('modal-backdrop').classList.remove('open'); }});
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') document.getElementById('modal-backdrop').classList.remove('open'); }});
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

    interfaces_html = "\n".join(
        f'<div class="interface" data-idx="{i}">{escape(ifc.get("name", ""))}</div>'
        for i, ifc in enumerate(interfaces)
    ) or '<span style="color:var(--muted); font-size:12.5px;">(da popolare)</span>'

    def comp_card(c: dict, idx: int, kind: str) -> str:
        trigger = c.get("trigger", "")
        cls = "il-card" + (" potential" if kind == "potential" else "")
        caps_list = c.get("capabilities_composed") or c.get("capabilities") or []
        caps_meta = " &middot; ".join(caps_list[:3]) + ("…" if len(caps_list) > 3 else "")
        return (
            f'<div class="{cls}" data-idx="{idx}" data-kind="{kind}">'
            f'<div class="trigger">{escape(trigger)}</div>'
            f'<div class="meta">{escape(caps_meta)}</div>'
            f'</div>'
        )

    current_compositions_html = "\n".join(comp_card(c, i, "current") for i, c in enumerate(cur_comp)) or '<span style="color:var(--muted); font-size:12.5px;">(da popolare)</span>'
    potential_compositions_html = "\n".join(comp_card(c, i, "potential") for i, c in enumerate(pot_comp)) or '<span style="color:var(--muted); font-size:12.5px;">(da popolare)</span>'

    company_observations_html = "\n".join(
        f'<div class="wm-card"><div class="label">{escape(o.get("dimension", ""))}</div>'
        f'<div class="meta">vive in: {escape(o.get("lives_in", "?"))} &middot; maturità: <strong>{escape(o.get("maturity", "?"))}</strong></div></div>'
        for o in (company.get("observations", []) or [])
    ) or '<span style="color:var(--muted); font-size:12.5px;">(da popolare)</span>'

    customer_observations_html = "\n".join(
        f'<div class="wm-card"><div class="label">{escape(s.get("type", ""))}</div>'
        f'<div class="meta">segnale onesto: {escape((s.get("honest_signal") or "?")[:70])}{"…" if len(s.get("honest_signal","")) > 70 else ""} &middot; '
        f'maturità: <strong>{escape(s.get("current_maturity", "?"))}</strong></div></div>'
        for s in (customer.get("by_stakeholder", []) or [])
    ) or '<span style="color:var(--muted); font-size:12.5px;">(da popolare)</span>'

    company_maturity = company.get("overall_maturity", "?")
    customer_unified = customer.get("is_unified", False)
    customer_unified_label = "rappresentazione unificata" if customer_unified else "rappresentazione frammentata"

    def cap_card(c: dict) -> str:
        moat = c.get("moat_grade", "")
        cls = "cap-card" + (" moat" if moat == "moat" else "")
        owners = c.get("current_owners") or []
        owners_pill = f'<span class="pill">{escape(", ".join(owners[:2]))}{"…" if len(owners) > 2 else ""}</span>' if owners else ""
        moat_pill = f'<span class="pill {moat}">{escape(moat)}</span>' if moat in ("moat", "commodity") else ""
        return (
            f'<div class="{cls}" data-name="{escape(c.get("name", ""))}">'
            f'<div class="name">{escape(c.get("name", ""))}</div>'
            f'<div class="desc">{escape(c.get("description", ""))}</div>'
            f'<div class="meta">{moat_pill}{owners_pill}</div>'
            f'</div>'
        )

    capabilities_html = "\n".join(cap_card(c) for c in caps) or '<span style="color:var(--muted);">(nessuna capability identificata)</span>'

    def signal_card(s: dict, idx: int) -> str:
        return (
            f'<div class="signal-card" data-idx="{idx}">'
            f'<div class="trigger">{escape(s.get("trigger", ""))}</div>'
            f'<div class="missing">manca: {escape(s.get("missing_capability", ""))}</div>'
            f'</div>'
        )

    signals_html = "\n".join(signal_card(s, i) for i, s in enumerate(signals)) or '<span style="color:var(--muted); font-size:13px;">(nessun segnale di fallimento identificato; il roadmap potenziale è vuoto)</span>'

    # Conceptual frame diagram, inline SVG (mirrors skills/capability-stack.svg)
    frame_diagram_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 480" style="font-family: ui-sans-serif, system-ui, sans-serif;">
  <defs>
    <marker id="arr-up" viewBox="0 0 10 10" refX="5" refY="9" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 0 0 L 5 9 L 10 0 Z" fill="#6b6b6b" transform="rotate(180 5 5)"/>
    </marker>
  </defs>
  <text x="360" y="22" text-anchor="middle" font-size="11" fill="#6b6b6b" font-weight="600" letter-spacing="1.2px">IL MODELLO OPERATIVO A QUATTRO LAYER</text>
  <rect x="160" y="48" width="400" height="56" rx="6" fill="#dde7f8" stroke="#9ab1d8"/>
  <text x="360" y="70" text-anchor="middle" font-size="14" fill="#1a1a1a" font-weight="600">Interfaces</text>
  <text x="360" y="90" text-anchor="middle" font-size="11" fill="#5a5a5a">dove arriva il valore agli stakeholder</text>
  <line x1="360" y1="130" x2="360" y2="108" stroke="#6b6b6b" stroke-width="1.5" marker-end="url(#arr-up)"/>
  <rect x="160" y="130" width="400" height="56" rx="6" fill="#e1ddec" stroke="#a59cc4"/>
  <text x="360" y="152" text-anchor="middle" font-size="14" fill="#1a1a1a" font-weight="600">Intelligence layer</text>
  <text x="360" y="172" text-anchor="middle" font-size="11" fill="#5a5a5a">compone capability in soluzioni per stakeholder specifici</text>
  <line x1="360" y1="212" x2="360" y2="190" stroke="#6b6b6b" stroke-width="1.5" marker-end="url(#arr-up)"/>
  <rect x="160" y="212" width="400" height="56" rx="6" fill="#dee7d8" stroke="#a0bf95"/>
  <text x="360" y="234" text-anchor="middle" font-size="14" fill="#1a1a1a" font-weight="600">World model</text>
  <text x="360" y="254" text-anchor="middle" font-size="11" fill="#5a5a5a">conoscenza condivisa di operazioni e segnale stakeholder</text>
  <line x1="360" y1="294" x2="360" y2="272" stroke="#6b6b6b" stroke-width="1.5" marker-end="url(#arr-up)"/>
  <rect x="160" y="294" width="400" height="56" rx="6" fill="#ede4ce" stroke="#c8b88a"/>
  <text x="360" y="316" text-anchor="middle" font-size="14" fill="#1a1a1a" font-weight="600">Capabilities</text>
  <text x="360" y="336" text-anchor="middle" font-size="11" fill="#5a5a5a">funzioni atomiche invocabili, hard to acquire, componibili</text>
  <rect x="80" y="384" width="560" height="56" rx="6" fill="#fbe8dd" stroke="#c47558" stroke-width="1.5"/>
  <text x="360" y="406" text-anchor="middle" font-size="11" fill="#8c4a30" font-weight="600" letter-spacing="0.6px">PRINCIPIO CONDIVISO</text>
  <text x="360" y="426" text-anchor="middle" font-size="12" fill="#1a1a1a">sostituire il routing gerarchico delle informazioni con un sistema che accumula intelligenza nel tempo</text>
  <text x="572" y="80" font-size="10" fill="#6b6b6b" font-style="italic">superfici di delivery</text>
  <text x="572" y="162" font-size="10" fill="#6b6b6b" font-style="italic">composer</text>
  <text x="572" y="244" font-size="10" fill="#6b6b6b" font-style="italic">substrate</text>
  <text x="572" y="326" font-size="10" fill="#6b6b6b" font-style="italic">primitives</text>
</svg>'''

    return HTML_TEMPLATE.format(
        css=base_css() + EXTRA_CSS,
        title=escape(title),
        scope=escape(d.get("_scope", "?")),
        n_caps=len(caps),
        n_signals=len(signals),
        frame_diagram_svg=frame_diagram_svg,
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
        potential_compositions_json=json.dumps(pot_comp, ensure_ascii=False),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render world-model JSON as interactive HTML.")
    parser.add_argument("--map", required=True, help="World-model JSON path")
    parser.add_argument("--html", required=True, help="Output HTML path")
    parser.add_argument("--title", default="World-model snapshot", help="Page title")
    args = parser.parse_args()

    d = json.loads(Path(args.map).read_text(encoding="utf-8"))
    html = render_html(d, args.title)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"Wrote {Path(args.html).resolve()} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
