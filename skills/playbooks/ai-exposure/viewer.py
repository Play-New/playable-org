#!/usr/bin/env python3
"""
ai-exposure / viewer.py — Generate a static HTML viewer for match results.

Visual style inspired by Anthropic's Job Explorer (anthropic.com/economic-index).
Each activity is a card with a grid of small colored squares — one square per
top-K match — colored by classification.

Output: a single self-contained HTML file (vanilla HTML/CSS/JS, no external deps).

Usage:
    python3 viewer.py --matches <matches.json>
                      [--metadata <metadata.json>]
                      [--lang en|it]
                      [--task-translations <translations.json>]
                      --out viewer.html [--title "..."]

The optional --metadata file enriches the cards. It is a JSON list of
{id, title, description, area, unit, ...} objects (same id as in matches).
Without it, only id is shown on each card.

The optional --task-translations file is a JSON dict {english_task: translated_task}
that lets the viewer display O*NET task names in the target UI language.
Translations can be produced by any pipeline (manual, LLM-assisted, MT) — the
viewer just consumes the dict.

Color scheme per match:
    green   = rich + autonomy ≥ p75 (mostly automated)
    purple  = rich + autonomy in [p25, p75] (mostly augmented)
    light   = rich + autonomy < p25 (assistive)
    beige   = fallback (not in Anthropic rich subset)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Import the shared Play New design system
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from design import base_css, masthead, colophon  # noqa: E402


EXTRA_CSS = """
/* ai-exposure viewer — Play New design (unified with value-map).
   Pure white surface, editorial typography, hairlines, single accent. */

:root {
  /* Category colours route through the data-viz palette in design.py */
  --automated: var(--ds-sage);
  --augmented: var(--ds-lilac);
  --assistive: var(--ds-slate);
  --no-data:   var(--ds-sand);
  --low-conf:  #c8c0b6;
}

body { background: #FFFFFF; color: var(--fg); }

/* One container width, applied uniformly to every block on the page.
   Header, legend, org-overview, area-section, decisions, footer all
   share the same horizontal frame. Text inside a block can still wrap
   at a readable length via inline max-width on the prose element, but
   the block itself is always container-width. */
.container { max-width: 1240px; margin: 0 auto; padding: 80px 40px 96px; }
@media (max-width: 900px) { .container { padding: 56px 24px 80px; } }

/* Editorial text columns at the start and end of the page sit in a
   centered narrower column inside the 1240px container; data-heavy
   blocks (filters, org-overview, area sections, card grid) span the
   full container. */
header { max-width: 820px; margin: 0 auto 48px; }
header .eyebrow { font-family: var(--font-display); font-size: 0.74rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); margin-bottom: 16px; }
header h1 { font-family: var(--font-display); font-size: clamp(1.9rem, 3.5vw, 2.6rem); font-weight: 500; letter-spacing: -0.025em; line-height: 1.1; margin: 0 0 16px; color: var(--fg); }
header .lead { font-size: 1.0rem; color: var(--fg-muted); line-height: 1.65; margin: 0; }

/* Intro: editorial prose explaining how to read the map. Same column
   width as the header, sits between header and legend. */
.intro { max-width: 820px; margin: 0 auto 48px; }
.intro h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 16px; }
.intro p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; }
.intro p:last-child { margin-bottom: 0; }

.legend-wrap { max-width: 820px; margin: 0 auto 40px; }
.legend { display: flex; gap: 22px; flex-wrap: wrap; font-size: 0.82rem; color: var(--fg-muted); align-items: center; }
.legend-item { display: flex; align-items: center; gap: 7px; }
.legend-square { width: 12px; height: 12px; border-radius: 2px; display: inline-block; }
.legend-square.automated { background: var(--automated); }
.legend-square.augmented { background: var(--augmented); }
.legend-square.assistive { background: var(--assistive); }
.legend-square.no-data { background: var(--no-data); }

/* Filter row — inline editorial controls, no chunky borders. */
.controls { max-width: 820px; margin: 0 auto 40px; display: flex; flex-direction: column; gap: 14px; }
.control-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.control-label { font-family: var(--font-display); font-size: 0.7rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; min-width: 60px; font-weight: 500; }
.search-box { flex: 1; min-width: 240px; padding: 8px 14px; border: 1px solid var(--fg-hairline); border-radius: 3px; font-size: 0.9rem; background: #FFFFFF; font-family: inherit; color: var(--fg); }
.search-box:focus { outline: none; border-color: var(--fg); }
.filter-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.pill { background: #FFFFFF; border: 1px solid var(--fg-hairline); border-radius: 999px; padding: 4px 12px; cursor: pointer; font-size: 0.76rem; font-family: inherit; color: var(--fg); transition: all 0.15s ease; white-space: nowrap; }
.pill:hover { border-color: var(--fg); }
.pill.active { background: var(--fg); color: #FFFFFF; border-color: var(--fg); }

.summary { max-width: 820px; margin: 0 auto 24px; font-size: 0.82rem; color: var(--fg-muted); }

/* Org snapshot — editorial block, centered column. */
.org-overview { max-width: 820px; margin: 0 auto 64px; }
.org-overview .label { font-family: var(--font-display); font-size: 0.7rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 14px; font-weight: 500; }
.org-overview .org-desc { font-size: 0.95rem; line-height: 1.7; margin-bottom: 22px; color: var(--fg); max-width: 720px; }
.org-overview .stats-row { display: flex; gap: 36px; flex-wrap: wrap; font-size: 0.85rem; color: var(--fg-muted); margin-bottom: 18px; }
.org-overview .stats-row strong { color: var(--fg); font-weight: 500; }

.dist-bar { display: flex; height: 12px; border-radius: 2px; overflow: hidden; margin: 10px 0; }
.dist-bar > div { height: 100%; }
.dist-bar .seg.automated { background: var(--automated); }
.dist-bar .seg.augmented { background: var(--augmented); }
.dist-bar .seg.assistive { background: var(--assistive); }
.dist-bar .seg.no-data { background: var(--no-data); }
.dist-legend { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.78rem; color: var(--fg-muted); margin-top: 8px; }
.dist-legend .item { display: flex; align-items: center; gap: 6px; }
.dist-legend .swatch { width: 11px; height: 11px; border-radius: 2px; display: inline-block; }
.dist-legend .swatch.automated { background: var(--automated); }
.dist-legend .swatch.augmented { background: var(--augmented); }
.dist-legend .swatch.assistive { background: var(--assistive); }
.dist-legend .swatch.no-data { background: var(--no-data); }

/* Per-area sections. The head spans the container width with a
   two-column layout: title + scope on the left, distribution on the
   right. The card grid below fills the full container with smaller
   cards so more fit per row on wide displays. */
.area-section { margin: 0 0 72px; padding-top: 36px; border-top: 1px solid var(--fg-hairline); }
.area-section .area-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: 56px; margin: 0 0 28px; align-items: start; }
@media (max-width: 1100px) { .area-section .area-head { grid-template-columns: 1fr; gap: 24px; } }
.area-section .area-head-left { min-width: 0; }
.area-section .area-head-right { min-width: 0; }
.area-section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; margin: 0 0 14px; letter-spacing: -0.02em; }
.area-section .area-desc { font-size: 0.95rem; color: var(--fg); line-height: 1.7; margin: 0 0 0; }
.area-section .desc-label, .area-section .summary-label, .area-section .area-notes-label { font-family: var(--font-display); font-size: 0.7rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 8px; font-weight: 500; }
.area-section .area-notes { margin-top: 18px; font-size: 0.92rem; line-height: 1.7; color: var(--fg); }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
/* Activity cards — full border, padding, hover signal. Even though
   the wrapper itself isn't the click target (the inner task-squares
   are), the border gives the activity a clean visual frame consistent
   with the other playbooks. */
.card { background: transparent; border: 1px solid var(--fg-hairline); border-radius: 4px; padding: 18px 20px; transition: border-color 0.15s; }
.card-title { font-family: var(--font-display); font-size: 1.0rem; font-weight: 500; margin: 0 0 4px; line-height: 1.35; color: var(--fg); letter-spacing: -0.01em; }
.card-id { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.68rem; color: var(--fg-muted); margin-bottom: 12px; }
.card-desc { font-size: 0.88rem; color: var(--fg-muted); margin-bottom: 14px; line-height: 1.55; }

/* Closest-match block — nested inside .card, distinguished by a
   subtle background tint, not by another border. */
.closest-match { padding: 10px 12px; margin: 14px 0; background: var(--bg-alt); border-radius: 3px; font-size: 0.85rem; line-height: 1.55; }
.closest-match .label { font-family: var(--font-display); font-size: 0.66rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px; font-weight: 500; }
.closest-match .task-it { color: var(--fg); margin-bottom: 4px; }
.closest-match .task-en { color: var(--fg-muted); font-style: italic; font-size: 0.78rem; }
.closest-match .metrics { display: flex; gap: 14px; margin-top: 8px; font-size: 0.78rem; flex-wrap: wrap; }
.closest-match .metric strong { font-weight: 500; color: var(--fg); }
.closest-match .metric .key { color: var(--fg-muted); margin-right: 3px; }
.closest-match.no-rich .warn { color: var(--fg-muted); font-size: 0.78rem; margin-top: 6px; }

.task-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 3px; margin: 12px 0 14px; max-width: 200px; }
.task-square { aspect-ratio: 1; border-radius: 2px; cursor: pointer; transition: transform 0.1s; position: relative; }
.task-square:hover { transform: scale(1.15); outline: 1.5px solid var(--fg); z-index: 5; }
.task-square.automated { background: var(--automated); }
.task-square.augmented { background: var(--augmented); }
.task-square.assistive { background: var(--assistive); }
.task-square.no-data { background: var(--no-data); }

.card-stat { font-size: 0.82rem; color: var(--fg-muted); padding-top: 10px; }
.card-stat .level-tag { display: inline-block; padding: 1px 8px; border-radius: 2px; font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.10em; color: #FFFFFF; margin-right: 8px; font-weight: 500; }
.level-tag.strong { background: var(--automated); color: var(--fg); }
.level-tag.medium { background: var(--augmented); color: var(--fg); }
.level-tag.mixed { background: var(--assistive); color: var(--fg); }
.level-tag.zero { background: var(--no-data); color: var(--fg); }
.level-tag.low-confidence { background: var(--low-conf); color: var(--fg); }

.card.low-confidence .task-grid::before { content: "Low confidence — top-1 similarity below threshold."; grid-column: 1 / -1; font-size: 0.76rem; color: var(--fg-muted); padding: 8px 10px; background: var(--bg-alt); border-radius: 2px; }
.card.low-confidence .task-grid { max-width: none; }

/* Decisions section — centered editorial column, same as value-map and world-model. */
.section { max-width: 820px; margin: 96px auto 0; padding-top: 40px; border-top: 1px solid var(--fg-hairline); }
.section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 20px; }
.section p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; max-width: 720px; }
.section .lead { font-size: 0.95rem; color: var(--fg-muted); line-height: 1.65; max-width: 720px; margin: 0 0 28px; }

.decision { margin-bottom: 32px; }
.decision .question { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; color: var(--fg); margin: 0 0 8px; letter-spacing: -0.01em; }
.decision .answer { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 6px; max-width: 720px; }
.decision .source { font-size: 0.78rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }

/* Popover — small floating card next to the clicked square. Replaces
   the full-screen modal: pop-overs read as 'a tooltip you can read',
   not 'a page you have to dismiss'. */
.popover { position: absolute; display: none; max-width: 360px; min-width: 240px; padding: 14px 18px 16px; background: #FFFFFF; border: 1px solid var(--fg-hairline); border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); z-index: 100; animation: pn-pop 0.18s ease; }
.popover.open { display: block; }
.popover .close { position: absolute; top: 6px; right: 8px; background: transparent; border: 0; cursor: pointer; font-size: 1.1rem; color: var(--fg-muted); padding: 0; line-height: 1; }
.popover .close:hover { color: var(--fg); }
.popover .eyebrow { font-family: var(--font-display); font-size: 0.62rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px; color: var(--fg-muted); }
.popover h3 { font-family: var(--font-display); font-size: 1rem; font-weight: 500; letter-spacing: -0.015em; margin: 0 0 4px; line-height: 1.25; color: var(--fg); padding-right: 18px; }
.popover .pop-id { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.7rem; color: var(--fg-muted); margin-bottom: 12px; }
.popover .pop-task { font-size: 0.85rem; line-height: 1.55; color: var(--fg); padding: 10px 12px; background: var(--bg-alt); border-radius: 3px; margin-bottom: 10px; }
.popover .pop-task strong { font-weight: 500; }
.popover dl { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 4px 14px; font-size: 0.82rem; }
.popover dt { color: var(--fg-muted); margin: 0; }
.popover dd { margin: 0; color: var(--fg); }
.popover .pop-chain { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--fg-hairline); font-size: 0.76rem; color: var(--fg-muted); line-height: 1.5; }
.popover .pop-chain strong { color: var(--fg); font-weight: 500; }

.empty { text-align: center; padding: 64px 0; color: var(--fg-muted); font-size: 0.95rem; }

.footer { max-width: 820px; margin: 80px auto 0; padding-top: 20px; border-top: 1px solid var(--fg-hairline); color: var(--fg-muted); font-size: 0.78rem; line-height: 1.6; }
.footer p { margin: 0; }
"""

P25 = 3.21
P75 = 3.57

STRINGS = {
    "en": {
        "subtitle": "How AI usage observed in the public Claude sample maps onto each activity this organization actually does, by matching every activity to the closest tasks in a public catalog of work.",
        "intro_h2": "What this map is",
        "intro_p1": "Each activity below is a piece of work this organization actually does. For each one, this page finds the closest tasks in a public catalog of about 18,500 occupations, and shows how Claude was used on those tasks in a sample of public conversations. The colours describe how Claude was used in the sample — not what the activity is in this organization.",
        "intro_p2": "Each activity is shown with five matches, not one. Picking only the single closest match would be fragile — that one match is often only partially right. Five squares show whether the pattern holds across nearby matches: five greens means Claude reliably worked alone on tasks like this in the sample; a mix of colours means the read is noisier and worth taking with a pinch of salt.",
        "intro_p3": "Click any square to read the matched task verbatim, how close it is to the activity (similarity), how Claude was used on it, and how big the sample behind that observation is. The colour key is in the legend below.",
        "legend_automated": "Mostly automated",
        "legend_augmented": "Mostly augmented",
        "legend_assistive": "Assistive",
        "legend_no_data": "Outside the observed sample",
        "search_label": "Search",
        "search_placeholder": "Words from the activity title or description",
        "signal_label": "Signal",
        "area_label": "Area",
        "all": "All",
        "all_areas": "All areas",
        "level_strong": "High signal",
        "level_medium": "Some signal",
        "level_mixed": "Low signal",
        "level_zero": "No signal",
        "level_low_confidence": "Low confidence",
        "summary": "{n} of {total} activities",
        "no_match": "No activities match the current filter.",
        "footer": "Source: Anthropic's public release of how Claude was used across a sample of conversations (March 2026 release, around 18,500 work-task descriptions from the public US occupational catalog). The matching uses a multilingual sentence-similarity model. Activities are kept only when the closest match is at least 55% similar; below that the read isn't reliable.",
        "closest_match": "Closest O*NET task",
        "confidence": "Confidence",
        "automation": "Automation",
        "low_conf_hint": "Low confidence — top-1 similarity below threshold.",
        "no_area": "(no area)",
        "activities_count": "{n} activities",
        "tooltip_click": "Click for details",
        "tooltip_conv_one": "1 conversation on Claude.ai",
        "tooltip_conv_many": "{n} conversations on Claude.ai",
        "tooltip_no_data": "outside the observed sample",
        "tooltip_aut": "autonomy {x}/5",
        "modal_task_label": "Closest O*NET task (original, EN)",
        "modal_task_it_label": "Suggested Italian translation",
        "modal_confidence": "Confidence (cosine similarity)",
        "modal_autonomy": "Average autonomy in Claude conversations",
        "modal_count": "Sample size (Claude.ai conversations)",
        "modal_count_warn_small": "small sample — interpret cautiously",
        "modal_category": "Anthropic category for the sample",
        "modal_no_rich": "Below the minimum activity count for stable estimates. The square is shown as 'no data'.",
        "modal_chain": "What this card actually says",
        "modal_chain_text": "this org's activity → closest match in the public catalog of work → category from how Claude was used on that catalog task in the Anthropic sample. The category describes that sample, not your activity.",
        "area_summary_label": "Snapshot",
        "area_distribution": "Distribution",
        "area_avg_confidence": "Avg. top-1 confidence",
        "area_avg_automation": "Avg. automation (where data)",
        "area_evidence_total": "Evidence base (Claude.ai conversations across all top matches)",
        "area_evidence_thin": "thin",
        "area_evidence_moderate": "moderate",
        "area_evidence_solid": "solid",
        "area_most": "Strongest signal",
        "area_least": "Weakest signal",
        "area_no_strong": "no activity rated 'strong' in this area",
        "area_no_weak": "no zero-signal activity in this area",
        "area_notes_label": "Notes",
        "area_no_data_full": "No autonomy data observed for any activity in this area (all closest matches fall outside the sample).",
        "org_overview_label": "Organization snapshot",
        "area_description_label": "Scope",
        "task_distribution_label": "O*NET task distribution (top-K matches)",
        "matches_label": "matches",
        "activities_label": "activities",
    },
    "it": {
        "subtitle": "Come l'uso di AI osservato nel campione pubblico Claude si mappa su ogni attività che questa organizzazione fa, cercando la mansione più vicina in un catalogo pubblico del lavoro.",
        "intro_h2": "Cos'è questa mappa",
        "intro_p1": "Ogni attività qui sotto è un pezzo di lavoro che l'organizzazione fa davvero. Per ognuna la pagina cerca le mansioni più vicine in un catalogo pubblico di circa 18.500 occupazioni, e mostra come Claude è stato usato su quelle mansioni in un campione di conversazioni pubbliche. I colori descrivono come Claude è stato usato nel campione — non cosa è l'attività dentro questa organizzazione.",
        "intro_p2": "Ogni attività è mostrata con cinque match, non uno. Prendere solo la mansione più vicina sarebbe fragile — quel singolo match spesso è solo parzialmente azzeccato. Cinque quadratini mostrano se il pattern regge attraverso match diversi: cinque verdi vuol dire che Claude ha lavorato in autonomia su mansioni simili nel campione; un mix di colori vuol dire che il segnale è più rumoroso e va preso con cautela.",
        "intro_p3": "Click su qualunque quadratino per leggere la mansione verbatim, quanto è vicina all'attività (similarità), come Claude è stato usato, e quanto è ampio il campione dietro quell'osservazione. La legenda dei colori è qui sotto.",
        "legend_automated": "Claude lavorava in autonomia (4-5 su 5)",
        "legend_augmented": "Claude assisteva con supervisione (3-4 su 5)",
        "legend_assistive": "Claude usato come strumento puntuale (1-3 su 5)",
        "legend_no_data": "Mansione fuori dal campione osservato",
        "search_label": "Cerca",
        "search_placeholder": "Parole dal titolo o dalla descrizione dell'attività",
        "signal_label": "Segnale",
        "area_label": "Area",
        "all": "Tutto",
        "all_areas": "Tutte le aree",
        "level_strong": "Forte: Claude in autonomia su almeno 3 mansioni vicine",
        "level_medium": "Medio: almeno 5 mansioni vicine assistite o autonome",
        "level_mixed": "Misto: mansioni vicine con dati spariti",
        "level_zero": "Nessun dato osservato sulle mansioni vicine",
        "level_low_confidence": "Match incerto (mansione troppo distante)",
        "summary": "{n} di {total} attività",
        "no_match": "Nessuna attività corrisponde al filtro corrente.",
        "footer": "Fonte: campione Anthropic delle conversazioni Claude (release 2026-03-24, 18.510 mansioni del catalogo americano dei mestieri). Soglia minima di vicinanza per considerare il match utile: 55%.",
        "closest_match": "Mansione più vicina nel catalogo americano dei mestieri",
        "confidence": "Vicinanza",
        "automation": "Autonomia di Claude",
        "low_conf_hint": "Match incerto: la mansione più vicina nel catalogo è troppo distante per fidarsi del dato.",
        "no_area": "(senza area)",
        "activities_count": "{n} attività",
        "tooltip_click": "Click per il dettaglio numerico",
        "tooltip_conv_one": "osservato su 1 conversazione Claude.ai (campione minimo)",
        "tooltip_conv_many": "osservato su {n} conversazioni Claude.ai",
        "tooltip_no_data": "mansione fuori dal campione osservato",
        "tooltip_aut": "autonomia Claude {x}/5 (1=solo aiuto, 5=lavoro autonomo)",
        "modal_task_label": "Mansione più vicina nel catalogo americano (testo originale in inglese)",
        "modal_task_it_label": "Traduzione italiana di lavoro",
        "modal_confidence": "Quanto la mansione del catalogo è vicina all'attività (in %)",
        "modal_autonomy": "Quanto Claude lavorava in autonomia in quelle conversazioni (1=solo aiuto, 5=lavoro autonomo)",
        "modal_count": "Su quante conversazioni Claude.ai si basa l'osservazione",
        "modal_count_warn_small": "campione piccolo, indicazione fragile",
        "modal_category": "Etichetta del campione Anthropic",
        "modal_no_rich": "Per questa mansione il campione Anthropic non ha dato osservato (nessuna conversazione Claude o sotto soglia minima). Il quadratino compare come 'fuori dati'.",
        "modal_chain": "Cosa dice davvero questo riquadro",
        "modal_chain_text": "La catena è: attività dell'organizzazione → mansione più vicina nel catalogo americano dei mestieri → categoria che Anthropic ha dato alle conversazioni Claude su quella mansione. L'etichetta descrive il campione Anthropic, non l'attività dell'organizzazione. Le distanze fra mansioni del catalogo USA e attività italiane di una fondazione sono spesso reali.",
        "area_summary_label": "In sintesi",
        "area_distribution": "Come si dividono le mansioni vicine",
        "area_avg_confidence": "Vicinanza media della mansione più vicina",
        "area_avg_automation": "Autonomia media osservata di Claude (dove c'è dato)",
        "area_evidence_total": "Totale conversazioni Claude.ai osservate sulle mansioni vicine",
        "area_evidence_thin": "campione limitato",
        "area_evidence_moderate": "campione moderato",
        "area_evidence_solid": "campione solido",
        "area_most": "Attività con segnale più forte",
        "area_least": "Attività con segnale più debole",
        "area_no_strong": "nessuna attività di quest'area mostra Claude in autonomia su almeno 3 mansioni vicine",
        "area_no_weak": "tutte le attività di quest'area hanno almeno qualche dato osservato",
        "area_notes_label": "Commento all'area",
        "area_no_data_full": "Nessuna metrica di automazione disponibile per quest'area (tutti i match sono fuori dal sottoinsieme ricco Anthropic).",
        "org_overview_label": "L'organizzazione in una pagina",
        "area_description_label": "Cosa fa quest'area",
        "task_distribution_label": "Come si dividono le mansioni vicine (5 per ogni attività)",
        "matches_label": "match (5 per attività)",
        "activities_label": "attività",
    },
}

LEVEL_LABEL = {
    "en": {"strong": "Strong", "medium": "Medium", "mixed": "Mixed", "zero": "Zero", "low-confidence": "Low conf"},
    "it": {"strong": "forte", "medium": "medio", "mixed": "misto", "zero": "zero", "low-confidence": "bassa conf"},
}

CAT_LABEL = {
    "en": {"automated": "automated", "augmented": "augmented", "assistive": "assistive", "no-data": "no data"},
    "it": {"automated": "automatizzata", "augmented": "aumentata", "assistive": "assistiva", "no-data": "fuori dati"},
}


def fmt_num(value: float, lang: str, decimals: int = 1) -> str:
    s = f"{value:.{decimals}f}"
    return s.replace(".", ",") if lang == "it" else s


SAMPLE_SMALL_THRESHOLD = 100


def classify_match(m: dict) -> str:
    aut = m.get("ai_autonomy_mean")
    if aut is None:
        return "no-data"
    aut = float(aut)
    if aut >= P75:
        return "automated"
    if aut >= P25:
        return "augmented"
    return "assistive"


def classify_activity(activity: dict) -> dict:
    if activity.get("low_confidence"):
        return {"level": "low-confidence", "n_rich": 0, "n_total": 0, "categories": {}}
    matches = activity["matches"]
    cats = {"automated": 0, "augmented": 0, "assistive": 0, "no-data": 0}
    for m in matches:
        cats[classify_match(m)] += 1
    rich = matches and any(m.get("ai_autonomy_mean") for m in matches)
    if not rich:
        level = "zero"
    elif cats["automated"] >= 3:
        level = "strong"
    elif cats["automated"] + cats["augmented"] >= 5:
        level = "medium"
    else:
        level = "mixed"
    return {"level": level, "n_rich": cats["automated"] + cats["augmented"] + cats["assistive"], "n_total": len(matches), "categories": cats}


def render_html(matches: list[dict], title: str, metadata: dict[str, dict], lang: str = "en", task_translations: dict[str, str] | None = None, area_notes: dict[str, str] | None = None, area_descriptions: dict[str, str] | None = None, org_description: str = "", decisions: list[dict] | None = None) -> str:
    if lang not in STRINGS:
        lang = "en"
    S = STRINGS[lang]
    LEVELS = LEVEL_LABEL[lang]
    CATS = CAT_LABEL[lang]
    translations = task_translations or {}

    classified = []
    for a in matches:
        c = classify_activity(a)
        meta = metadata.get(a["id"], {}) if metadata else {}
        # Annotate each match with optional Italian translation.
        annotated = []
        for m in a.get("matches", []):
            mm = dict(m)
            t = m.get("task") or ""
            if t in translations:
                mm["task_it"] = translations[t]
            annotated.append(mm)
        classified.append({
            **a,
            "matches": annotated,
            **c,
            "_title": meta.get("title") or a["id"],
            "_description": meta.get("description") or "",
            "_area": meta.get("area") or "",
            "_unit": meta.get("unit") or "",
        })

    levels = [c["level"] for c in classified]
    counts = {lv: levels.count(lv) for lv in ("strong", "medium", "mixed", "zero", "low-confidence")}

    # Distinct areas, sorted
    areas = sorted({c["_area"] for c in classified if c["_area"]})

    data_js = json.dumps(classified, ensure_ascii=False)
    strings_js = json.dumps(S, ensure_ascii=False)
    levels_js = json.dumps(LEVELS, ensure_ascii=False)
    cats_js = json.dumps(CATS, ensure_ascii=False)
    area_notes_js = json.dumps(area_notes or {}, ensure_ascii=False)
    area_desc_js = json.dumps(area_descriptions or {}, ensure_ascii=False)
    org_desc_escaped = (org_description or "").replace("</", "<\\/")

    # --- editorial chrome (Italianate masthead + magazine colophon) ---
    n_activities = len(classified)
    n_areas = len(areas)
    if lang == "it":
        kicker_left = "esposizione all'AI"
        kicker_right = f"organizzazione · {n_activities} attività"
        title_html = f"<em>{title}</em>"
        lede_text = S.get("subtitle", "")
        dateline_text = ""
        masthead_tags = [f"{n_activities} attività", f"{n_areas} aree"]
        colo_extra = ["Clicca un quadratino per leggere la classificazione, la fonte AEI, l'articolo dietro la mossa."]
    else:
        kicker_left = "ai exposure"
        kicker_right = f"organization · {n_activities} activities"
        title_html = f"<em>{title}</em>"
        lede_text = S.get("subtitle", "")
        dateline_text = ""
        masthead_tags = [f"{n_activities} activities", f"{n_areas} areas"]
        colo_extra = ["Click any square to read its classification, the AEI source, and the story behind the move."]
    masthead_html = masthead(
        kicker_left=kicker_left,
        kicker_num=f"№ {n_activities:02d}",
        kicker_right=kicker_right,
        title=title_html,
        lede=lede_text,
        dateline=dateline_text,
        tags=masthead_tags,
    )
    colophon_html = colophon(
        citations=None, sources=None,
        generator="skills/playbooks/ai-exposure",
        generated_on="",
        audit="pass",
        autoresearch="4 / 4 deterministic dimensions pass",
        extra_lines=colo_extra,
    )

    decisions_html = ""
    if decisions:
        from html import escape as _esc
        items = []
        for d in decisions:
            q = _esc(d.get("question", ""))
            ans_paragraphs = "".join(f'<p class="answer">{_esc(p)}</p>' for p in (d.get("answer", "") or "").split("\n\n") if p.strip())
            src = _esc(d.get("source", ""))
            src_html = f'<div class="source">{src}</div>' if src else ""
            items.append(f'<div class="decision"><div class="question">{q}</div>{ans_paragraphs}{src_html}</div>')
        decisions_eyebrow = "How to read this map" if lang == "en" else "Come leggere questa mappa"
        decisions_lead = (
            "Each square above is one of the closest matches in the public catalog of work; the decisions below translate the pattern into moves the leader could make."
            if lang == "en"
            else "Ogni quadratino sopra è una delle attività più vicine nel catalogo pubblico del lavoro; le decisioni qui sotto traducono il pattern in mosse che chi guida l'organizzazione può fare."
        )
        decisions_html = f"""
    <div class="section" id="decisions">
      <h2>{decisions_eyebrow}</h2>
      <p class="lead">{decisions_lead}</p>
      {''.join(items)}
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<title>{title} · ai exposure</title>
<style>{base_css() + EXTRA_CSS}</style>
</head>
<body>
  <div class="container">
    {masthead_html}

    <div class="intro">
      <h2>{S["intro_h2"]}</h2>
      <p>{S["intro_p1"]}</p>
      <p>{S["intro_p2"]}</p>
      <p>{S["intro_p3"]}</p>
    </div>

    <div class="legend-wrap">
      <div class="legend">
        <div class="legend-item"><span class="legend-square automated"></span>{S["legend_automated"]}</div>
        <div class="legend-item"><span class="legend-square augmented"></span>{S["legend_augmented"]}</div>
        <div class="legend-item"><span class="legend-square assistive"></span>{S["legend_assistive"]}</div>
        <div class="legend-item"><span class="legend-square no-data"></span>{S["legend_no_data"]}</div>
      </div>
    </div>

    <div class="controls">
      <div class="control-row">
        <span class="control-label">{S["search_label"]}</span>
        <input class="search-box" id="search" placeholder="{S["search_placeholder"]}" />
      </div>
      <div class="control-row">
        <span class="control-label">{S["signal_label"]}</span>
        <div class="filter-pills" id="filter-level">
          <button class="pill active" data-level="all">{S["all"]}</button>
          <button class="pill" data-level="strong">{S["level_strong"]}</button>
          <button class="pill" data-level="medium">{S["level_medium"]}</button>
          <button class="pill" data-level="mixed">{S["level_mixed"]}</button>
          <button class="pill" data-level="zero">{S["level_zero"]}</button>
          <button class="pill" data-level="low-confidence">{S["level_low_confidence"]}</button>
        </div>
      </div>
      <div class="control-row">
        <span class="control-label">{S["area_label"]}</span>
        <div class="filter-pills" id="filter-area">
          <button class="pill active" data-area="all">{S["all_areas"]}</button>
          {''.join(f'<button class="pill" data-area="{a}">{a}</button>' for a in areas)}
        </div>
      </div>
    </div>

    <div id="org-overview"></div>

    <div class="summary" id="summary"></div>

    <div id="content"></div>
    <div class="empty" id="empty" style="display:none">{S["no_match"]}</div>

    {decisions_html}

    <div class="footer"><p>{S["footer"]}</p></div>

    {colophon_html}
  </div>

  <div class="popover" id="popover">
    <button class="close" id="popover-close" aria-label="Close">×</button>
    <div id="popover-body"></div>
  </div>

<script>
const data = {data_js};
const S = {strings_js};
const LEVELS = {levels_js};
const CATS = {cats_js};
const AREA_NOTES = {area_notes_js};
const AREA_DESCRIPTIONS = {area_desc_js};
const ORG_DESCRIPTION = {json.dumps(org_desc_escaped, ensure_ascii=False)};
const SAMPLE_SMALL = {SAMPLE_SMALL_THRESHOLD};

function classifyMatch(m) {{
  if (m.ai_autonomy_mean == null) return 'no-data';
  const aut = m.ai_autonomy_mean;
  if (aut >= 3.57) return 'automated';
  if (aut >= 3.21) return 'augmented';
  return 'assistive';
}}

function escapeHtml(s) {{
  return String(s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }})[c]);
}}

let currentLevel = 'all';
let currentArea = 'all';
let currentQuery = '';

function applyFilters() {{
  const q = currentQuery.trim().toLowerCase();
  return data.filter(d => {{
    if (currentLevel !== 'all' && d.level !== currentLevel) return false;
    if (currentArea !== 'all' && d._area !== currentArea) return false;
    if (q) {{
      const blob = `${{d._title}} ${{d._description}} ${{d.id}} ${{d._area}}`.toLowerCase();
      if (!blob.includes(q)) return false;
    }}
    return true;
  }});
}}

function categoryDistribution(items) {{
  // Aggregate task-level (per-match) distribution across categories.
  const cats = {{automated: 0, augmented: 0, assistive: 0, 'no-data': 0}};
  let simSum = 0, simN = 0;
  let convTotal = 0;
  for (const d of items) {{
    for (const m of (d.matches || [])) {{
      if (!m) continue;
      cats[classifyMatch(m)]++;
      if (m.similarity != null) {{ simSum += m.similarity; simN++; }}
      if (m.count != null) convTotal += m.count;
    }}
  }}
  const total = cats.automated + cats.augmented + cats.assistive + cats['no-data'];
  return {{
    n: items.length,
    cats,
    total,
    avgConfidence: simN ? simSum / simN : null,
    convTotal,
  }};
}}

function renderDistBar(cats, total) {{
  if (total === 0) return '';
  const seg = (cls) => {{
    const v = cats[cls];
    if (v === 0) return '';
    const pct = (v / total) * 100;
    return `<div class="seg ${{cls}}" style="width:${{pct}}%" title="${{CATS[cls]}}: ${{v}} (${{Math.round(pct)}}%)"></div>`;
  }};
  return `<div class="dist-bar">${{seg('automated')}}${{seg('augmented')}}${{seg('assistive')}}${{seg('no-data')}}</div>`;
}}

function renderDistLegend(cats, total) {{
  if (total === 0) return '';
  const item = (cls) => {{
    const v = cats[cls];
    const pct = total ? Math.round(v / total * 100) : 0;
    return `<div class="item"><span class="swatch ${{cls}}"></span>${{CATS[cls]}} <strong>${{pct}}%</strong> (${{v}})</div>`;
  }};
  return `<div class="dist-legend">${{item('automated')}}${{item('augmented')}}${{item('assistive')}}${{item('no-data')}}</div>`;
}}

function renderOrgOverview() {{
  const dist = categoryDistribution(data);
  const desc = ORG_DESCRIPTION
    ? `<div class="org-desc">${{escapeHtml(ORG_DESCRIPTION).replace(/\\n/g, '<br>')}}</div>`
    : '';
  const stats = `<div class="stats-row">
    <div><strong>${{data.length}}</strong> ${{S.activities_label}}</div>
    <div><strong>${{dist.total}}</strong> ${{S.matches_label}}</div>
    <div><strong>${{dist.avgConfidence != null ? fmtPct(dist.avgConfidence) : '—'}}</strong> ${{S.area_avg_confidence}}</div>
    <div><strong>${{dist.convTotal}}</strong> Claude.ai conv.</div>
  </div>`;
  const distLabel = `<div class="label">${{S.task_distribution_label}}</div>`;
  return `
    <div class="org-overview">
      <div class="label">${{S.org_overview_label}}</div>
      ${{desc}}
      ${{stats}}
      ${{distLabel}}
      ${{renderDistBar(dist.cats, dist.total)}}
      ${{renderDistLegend(dist.cats, dist.total)}}
    </div>`;
}}

function renderAreaSummary(area, items) {{
  // Returns {{left, right}} so the caller can place each column in the
  // two-column .area-head layout.
  const dist = categoryDistribution(items);
  const description = AREA_DESCRIPTIONS[area];
  const descHtml = description
    ? `<div class="desc-label">${{S.area_description_label}}</div><div class="area-desc">${{escapeHtml(description)}}</div>`
    : '';
  const distLabel = `<div class="desc-label">${{S.task_distribution_label}}</div>`;
  const note = AREA_NOTES[area];
  let noteRendered = '';
  if (note) {{
    let safe = escapeHtml(note).replace(/\\n/g, '<br>');
    safe = safe.replace(/\\*([^*\\n]+?)\\*/g, '<em>$1</em>');
    noteRendered = `<div class="area-notes"><div class="area-notes-label">${{S.area_notes_label}}</div>${{safe}}</div>`;
  }}
  return {{
    left:  `${{descHtml}}${{noteRendered}}`,
    right: `${{distLabel}}${{renderDistBar(dist.cats, dist.total)}}${{renderDistLegend(dist.cats, dist.total)}}`,
  }};
}}

function fmtNum(value, decimals) {{
  if (value == null || isNaN(value)) return '—';
  const s = Number(value).toFixed(decimals);
  return S.summary.indexOf(' di ') >= 0 ? s.replace('.', ',') : s;
}}

function fmtPct(value) {{
  if (value == null || isNaN(value)) return '—';
  return Math.round(value * 100) + '%';
}}

function renderClosest(d) {{
  if (!d.matches || d.matches.length === 0) return '';
  const m = d.matches[0];
  if (!m) return '';
  const sim = fmtPct(m.similarity);
  const aut = m.ai_autonomy_mean != null ? `${{fmtNum(m.ai_autonomy_mean, 1)}} / 5` : '—';
  const taskIt = m.task_it || '';
  const taskEn = m.task || '';
  const cls = classifyMatch(m);
  const noRich = (m.ai_autonomy_mean == null);
  const itLine = taskIt ? `<div class="task-it">${{escapeHtml(taskIt)}}</div>` : '';
  const enLine = taskIt
    ? `<div class="task-en">${{escapeHtml(taskEn)}}</div>`
    : `<div class="task-it">${{escapeHtml(taskEn)}}</div>`;
  const metricsHtml = noRich
    ? `<div class="warn">${{escapeHtml(S.modal_no_rich)}}</div>`
    : `<div class="metrics">
         <div class="metric"><span class="key">${{S.confidence}}:</span><strong>${{sim}}</strong></div>
         <div class="metric"><span class="key">${{S.automation}}:</span><strong>${{aut}}</strong></div>
         <div class="metric"><span class="key">${{S.modal_count}}:</span><strong>${{m.count != null ? m.count : '—'}}${{(m.count != null && m.count < SAMPLE_SMALL) ? ' ⚠' : ''}}</strong></div>
       </div>`;
  return `
    <div class="closest-match ${{noRich ? 'no-rich' : ''}}">
      <div class="label">${{S.closest_match}}</div>
      ${{itLine}}
      ${{enLine}}
      ${{metricsHtml}}
    </div>`;
}}

function renderCard(d) {{
  const isLow = d.level === 'low-confidence';
  let squaresHtml = '';
  if (!isLow) {{
    // Render exactly the matches that exist — no padding to a fixed
    // grid size. With top-K = 5 (default) this gives 5 squares per
    // activity; the grid CSS wraps them into rows of 5.
    const real = d.matches.map((m, idx) => ({{m, idx, cls: classifyMatch(m)}}));
    const order = {{automated: 0, augmented: 1, assistive: 2, 'no-data': 3}};
    real.sort((a, b) => order[a.cls] - order[b.cls]);
    squaresHtml = real.map(s => {{
      const m = s.m;
      const cls = s.cls;
      const taskShort = (m.task_it || m.task || '');
      const taskTrunc = taskShort.length > 140 ? taskShort.slice(0, 140) + '…' : taskShort;
      const sim = fmtPct(m.similarity);
      const catLabel = CATS[cls] || cls;
      const countLine = (m.count != null)
        ? (m.count === 1 ? S.tooltip_conv_one : S.tooltip_conv_many.replace('{{n}}', m.count))
        : S.tooltip_no_data;
      const autLine = (m.ai_autonomy_mean != null) ? S.tooltip_aut.replace('{{x}}', fmtNum(m.ai_autonomy_mean, 1)) : '';
      const tail = [countLine, autLine].filter(Boolean).join(' · ');
      const label = `${{taskTrunc}}\\n\\n${{S.confidence}} ${{sim}} · ${{catLabel}}\\n${{tail}}\\n\\n${{S.tooltip_click}}`;
      return `<div class="task-square ${{cls}}" data-activity="${{escapeHtml(d.id)}}" data-idx="${{s.idx}}" data-tooltip="${{escapeHtml(label)}}"></div>`;
    }}).join('');
  }}
  const cats = d.categories || {{}};
  const stat = isLow
    ? `<span class="level-tag low-confidence">${{LEVELS['low-confidence']}}</span> ${{S.low_conf_hint}}`
    : `${{cats.automated || 0}} ${{CATS.automated}} · ${{cats.augmented || 0}} ${{CATS.augmented}} · ${{cats.assistive || 0}} ${{CATS.assistive}} · ${{cats['no-data'] || 0}} ${{CATS['no-data']}}`;
  const closest = isLow ? '' : renderClosest(d);
  return `
    <div class="card ${{isLow ? 'low-confidence' : ''}}">
      <div class="card-title">${{escapeHtml(d._title || d.id)}}</div>
      <div class="card-id">${{escapeHtml(d.id)}} · ${{escapeHtml(d._area)}}</div>
      <div class="card-desc">${{escapeHtml(d._description || '')}}</div>
      ${{closest}}
      <div class="task-grid">${{squaresHtml}}</div>
      <div class="card-stat">${{stat}}</div>
    </div>`;
}}

function render() {{
  const items = applyFilters();
  const summary = document.getElementById('summary');
  const empty = document.getElementById('empty');
  const content = document.getElementById('content');
  const overview = document.getElementById('org-overview');

  // org overview only when no specific area filter is active.
  overview.innerHTML = (currentArea === 'all') ? renderOrgOverview() : '';

  summary.textContent = S.summary.replace('{{n}}', items.length).replace('{{total}}', data.length);

  if (items.length === 0) {{
    content.innerHTML = '';
    empty.style.display = 'block';
    return;
  }}
  empty.style.display = 'none';

  // Group by area when "All areas" + no specific area filter
  if (currentArea === 'all') {{
    const groups = {{}};
    items.forEach(d => {{
      const key = d._area || S.no_area;
      if (!groups[key]) groups[key] = [];
      groups[key].push(d);
    }});
    const sortedAreas = Object.keys(groups).sort();
    content.innerHTML = sortedAreas.map(area => {{
      const cards = groups[area].map(renderCard).join('');
      const summary = renderAreaSummary(area, groups[area]);
      return `
        <div class="area-section">
          <div class="area-head">
            <div class="area-head-left">
              <h2>${{escapeHtml(area)}}</h2>
              ${{summary.left}}
            </div>
            <div class="area-head-right">
              ${{summary.right}}
            </div>
          </div>
          <div class="grid">${{cards}}</div>
        </div>`;
    }}).join('');
  }} else if (currentArea !== 'all') {{
    const summary = renderAreaSummary(currentArea, items);
    content.innerHTML = `
      <div class="area-section">
        <div class="area-head">
          <div class="area-head-left">
            <h2>${{escapeHtml(currentArea)}}</h2>
            ${{summary.left}}
          </div>
          <div class="area-head-right">
            ${{summary.right}}
          </div>
        </div>
        <div class="grid">${{items.map(renderCard).join('')}}</div>
      </div>`;
  }} else {{
    content.innerHTML = `<div class="grid">${{items.map(renderCard).join('')}}</div>`;
  }}
}}

document.querySelectorAll('#filter-level .pill').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('#filter-level .pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentLevel = btn.dataset.level;
    render();
  }});
}});

document.querySelectorAll('#filter-area .pill').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('#filter-area .pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentArea = btn.dataset.area;
    render();
  }});
}});

document.getElementById('search').addEventListener('input', e => {{
  currentQuery = e.target.value;
  render();
}});

// Popover positioning + click handlers — same shape as value-map.
const popoverEl   = document.getElementById('popover');
const popoverBody = document.getElementById('popover-body');

function showPopover(html, anchorRect) {{
  // Open the popover BELOW the clicked square, centered horizontally
  // on it. If there's not enough room below, flip above. Always
  // clamped inside the viewport.
  popoverBody.innerHTML = html;
  const margin = 12;
  popoverEl.style.left = '0px';
  popoverEl.style.top = '0px';
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

document.addEventListener('click', e => {{
  // Square click → popover with task detail
  if (e.target.classList && e.target.classList.contains('task-square')) {{
    const aid = e.target.dataset.activity;
    const idx = parseInt(e.target.dataset.idx, 10);
    if (!aid || isNaN(idx)) return;
    const a = data.find(x => x.id === aid);
    if (!a) return;
    const m = a.matches[idx];
    if (!m) return;
    const cls = classifyMatch(m);
    const catLabel = CATS[cls] || cls;
    const countWarn = (m.count != null && m.count < SAMPLE_SMALL) ? ` <span style="color:var(--ds-coral)">(${{S.modal_count_warn_small}})</span>` : '';
    const richHtml = m.ai_autonomy_mean != null
      ? `<dl>
           <dt>${{S.modal_autonomy}}</dt><dd>${{fmtNum(m.ai_autonomy_mean, 2)}} / 5</dd>
           <dt>${{S.modal_count}}</dt><dd>${{m.count != null ? m.count : 0}}${{countWarn}}</dd>
           <dt>${{S.modal_category}}</dt><dd>${{catLabel}}</dd>
           <dt>${{S.modal_confidence}}</dt><dd>${{fmtPct(m.similarity)}}</dd>
         </dl>`
      : `<p style="color: var(--fg-muted); font-size: 0.82rem; margin: 0 0 10px">${{escapeHtml(S.modal_no_rich)}}</p>
         <dl>
           <dt>${{S.modal_category}}</dt><dd>${{catLabel}}</dd>
           <dt>${{S.modal_confidence}}</dt><dd>${{fmtPct(m.similarity)}}</dd>
         </dl>`;
    const taskItHtml = m.task_it ? `<div class="pop-task"><strong>${{escapeHtml(m.task_it)}}</strong><br><span style="color: var(--fg-muted); font-size: 0.78rem; font-style: italic">${{escapeHtml(m.task)}}</span></div>` : `<div class="pop-task">${{escapeHtml(m.task)}}</div>`;
    const html = `
      <div class="eyebrow">${{escapeHtml(a._area || '')}}</div>
      <h3>${{escapeHtml(a._title || a.id)}}</h3>
      <div class="pop-id">${{escapeHtml(a.id)}}</div>
      ${{taskItHtml}}
      ${{richHtml}}
      <div class="pop-chain"><strong>${{S.modal_chain}}.</strong> ${{escapeHtml(S.modal_chain_text)}}</div>
    `;
    const r = e.target.getBoundingClientRect();
    showPopover(html, {{
      left:   r.left   + window.scrollX,
      right:  r.right  + window.scrollX,
      top:    r.top    + window.scrollY,
      bottom: r.bottom + window.scrollY,
    }});
    return;
  }}

  // Click outside the popover and outside any square → close
  let n = e.target;
  while (n && n.nodeType === 1) {{
    if (n.id === 'popover') return;
    n = n.parentNode;
  }}
  hidePopover();
}}, true);

document.getElementById('popover-close').addEventListener('click', hidePopover);
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') hidePopover(); }});

render();
</script>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a static HTML viewer for ai-exposure matches.")
    parser.add_argument("--matches", required=True, help="match.py output JSON")
    parser.add_argument("--out", required=True, help="Output HTML file")
    parser.add_argument("--title", default="ai-exposure viewer", help="Page title")
    parser.add_argument("--metadata", help="Optional JSON list of {id, title, description, area, unit, ...}")
    parser.add_argument("--lang", choices=["en", "it"], default="en", help="UI language")
    parser.add_argument(
        "--task-translations",
        help="Optional JSON dict {english_task: target_language_task} to display task names in the UI language.",
    )
    parser.add_argument(
        "--area-notes",
        help="Optional JSON dict {area_id: 'commentary text'} rendered above each area's grid. "
             "Notes should pass audit-notes.py before being shipped.",
    )
    parser.add_argument(
        "--area-descriptions",
        help="Optional JSON dict {area_id: 'high-level scope description'} shown at the top of each area section. "
             "Structure-grounded one-liners.",
    )
    parser.add_argument(
        "--org-description",
        default="",
        help="Free-text org description rendered at the top of the page. Plain text or use \\n for line breaks.",
    )
    parser.add_argument(
        "--org-description-file",
        help="Optional path to a file containing the org description (overrides --org-description).",
    )
    parser.add_argument(
        "--decisions",
        help="Optional JSON list of {question, answer, source} rendered in the bottom 'How to read this map' section. The agent fills these as the final step of the playbook; autoresearch.py scores them.",
    )
    args = parser.parse_args()

    raw = json.loads(Path(args.matches).read_text())
    # Two accepted shapes:
    # 1. Bare list of activity matches (the original match.py output).
    # 2. Wrapper object {matches, decisions, _scope, ...} for the
    #    mcp-tool render flow where the agent passes the whole play
    #    context via json_content.
    embedded_decisions: list[dict] | None = None
    if isinstance(raw, dict) and "matches" in raw:
        matches = raw["matches"]
        if "decisions" in raw and isinstance(raw["decisions"], list):
            embedded_decisions = raw["decisions"]
    else:
        matches = raw
    metadata: dict[str, dict] = {}
    if args.metadata:
        meta_list = json.loads(Path(args.metadata).read_text())
        if isinstance(meta_list, list):
            metadata = {m["id"]: m for m in meta_list if "id" in m}
        elif isinstance(meta_list, dict):
            metadata = meta_list

    translations: dict[str, str] = {}
    if args.task_translations:
        translations = json.loads(Path(args.task_translations).read_text())
        if not isinstance(translations, dict):
            print("--task-translations must be a JSON dict {english_task: translated_task}", file=sys.stderr)
            return 1

    area_notes: dict[str, str] = {}
    if args.area_notes:
        area_notes = json.loads(Path(args.area_notes).read_text())
        if not isinstance(area_notes, dict):
            print("--area-notes must be a JSON dict {area_id: 'note text'}", file=sys.stderr)
            return 1

    area_descriptions: dict[str, str] = {}
    if args.area_descriptions:
        area_descriptions = json.loads(Path(args.area_descriptions).read_text())
        if not isinstance(area_descriptions, dict):
            print("--area-descriptions must be a JSON dict {area_id: 'description'}", file=sys.stderr)
            return 1

    org_description = args.org_description
    if args.org_description_file:
        org_description = Path(args.org_description_file).read_text().strip()

    # Decisions: --decisions flag wins over wrapper-embedded decisions
    # (so a CLI user can override a wrapper). Otherwise use wrapper if
    # present.
    decisions: list[dict] = embedded_decisions or []
    if args.decisions:
        decisions = json.loads(Path(args.decisions).read_text())
        if not isinstance(decisions, list):
            print("--decisions must be a JSON list of {question, answer, source}", file=sys.stderr)
            return 1

    html = render_html(
        matches, args.title, metadata, lang=args.lang,
        task_translations=translations, area_notes=area_notes,
        area_descriptions=area_descriptions, org_description=org_description,
        decisions=decisions,
    )
    Path(args.out).write_text(html, encoding="utf-8")
    print(
        f"Wrote {Path(args.out).resolve()} "
        f"({len(matches)} activities, {len(html):,} bytes, lang={args.lang}, "
        f"translations={len(translations)}, area_notes={len(area_notes)}, "
        f"area_descriptions={len(area_descriptions)}, org_description={'yes' if org_description else 'no'})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
