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
from design import base_css  # noqa: E402


EXTRA_CSS = """
:root {
  --bg: var(--bg-soft);
  --fg: var(--fg);
  --muted: var(--muted);
  --line: var(--line);
  --card: var(--bg);
  --accent: var(--fg);
  /* Category colours route through the data-viz palette in design.py */
  --automated: var(--ds-sage);
  --augmented: var(--ds-lilac);
  --assistive: var(--ds-slate);
  --no-data:   var(--ds-sand);
  --low-conf:  #c8c0b6;
}

body { background: var(--bg-soft); }

.container { max-width: 1280px; margin: 0 auto; padding: 48px 32px 80px; }
header { padding-bottom: 24px; border-bottom: 1px solid var(--line); margin-bottom: 32px; }
h1 { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 12px; }
.subtitle { font-size: 0.95rem; color: var(--muted); max-width: 720px; margin-bottom: 24px; line-height: 1.65; }

.legend { display: flex; gap: 22px; flex-wrap: wrap; margin-bottom: 24px; font-size: 0.82rem; color: var(--fg); }
.legend-item { display: flex; align-items: center; gap: 7px; }
.legend-square { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }
.legend-square.automated { background: var(--automated); }
.legend-square.augmented { background: var(--augmented); }
.legend-square.assistive { background: var(--assistive); }
.legend-square.no-data { background: var(--no-data); }

.controls { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; padding-top: 20px; border-top: 1px solid var(--line); }
.control-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.control-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; min-width: 60px; font-weight: 500; }
.search-box { flex: 1; min-width: 240px; padding: 10px 14px; border: 1px solid var(--line); border-radius: 3px; font-size: 0.9rem; background: var(--card); font-family: inherit; color: var(--fg); }
.search-box:focus { outline: 2px solid var(--fg); outline-offset: -1px; border-color: var(--fg); }
.filter-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.pill { background: var(--card); border: 1px solid var(--line); border-radius: 999px; padding: 5px 14px; cursor: pointer; font-size: 0.78rem; font-family: inherit; color: var(--fg); transition: all 0.15s ease; white-space: nowrap; }
.pill:hover { background: var(--bg-soft); border-color: var(--line); }
.pill.active { background: var(--fg); color: var(--bg); border-color: var(--fg); }

.summary { font-size: 0.9rem; color: var(--muted); margin-bottom: 24px; }
.area-section { margin-bottom: 48px; }
.area-section h2 { font-size: 1.25rem; font-weight: 500; margin: 0 0 14px; padding-bottom: 10px; border-bottom: 1px solid var(--line); color: var(--fg); letter-spacing: -0.01em; }
.area-meta { font-size: 0.82rem; color: var(--muted); margin-bottom: 16px; }

.org-overview { background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: 24px 28px; margin-bottom: 28px; }
.org-overview .label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px; font-weight: 500; }
.org-overview .org-desc { font-size: 0.92rem; line-height: 1.65; margin-bottom: 18px; color: var(--fg); }
.org-overview .stats-row { display: flex; gap: 28px; flex-wrap: wrap; font-size: 0.85rem; color: var(--muted); margin-bottom: 12px; }
.org-overview .stats-row strong { color: var(--fg); font-weight: 500; }

.dist-bar { display: flex; height: 14px; border-radius: 3px; overflow: hidden; margin: 8px 0; border: 1px solid var(--line); }
.dist-bar > div { height: 100%; }
.dist-bar .seg.automated { background: var(--automated); }
.dist-bar .seg.augmented { background: var(--augmented); }
.dist-bar .seg.assistive { background: var(--assistive); }
.dist-bar .seg.no-data { background: var(--no-data); }
.dist-legend { display: flex; gap: 18px; flex-wrap: wrap; font-size: 0.78rem; color: var(--muted); margin-top: 6px; }
.dist-legend .item { display: flex; align-items: center; gap: 6px; }
.dist-legend .swatch { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }
.dist-legend .swatch.automated { background: var(--automated); }
.dist-legend .swatch.augmented { background: var(--augmented); }
.dist-legend .swatch.assistive { background: var(--assistive); }
.dist-legend .swatch.no-data { background: var(--no-data); }

.area-summary { background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: 20px 24px; margin-bottom: 20px; }
.area-summary .area-desc { font-size: 0.88rem; line-height: 1.6; color: var(--fg); margin-bottom: 14px; }
.area-summary .desc-label, .area-summary .summary-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; font-weight: 500; }
.area-summary .summary-label { margin-top: 14px; margin-bottom: 10px; }
.area-summary dl { margin: 0; display: grid; grid-template-columns: max-content 1fr; gap: 6px 18px; font-size: 0.85rem; }
.area-summary dt { color: var(--muted); margin: 0; }
.area-summary dd { margin: 0; color: var(--fg); }
.area-summary .dist-pill { display: inline-block; padding: 1px 8px; border-radius: 3px; font-size: 0.7rem; margin-right: 4px; color: var(--card); font-weight: 500; }
.area-summary .dist-pill.strong { background: var(--automated); }
.area-summary .dist-pill.medium { background: var(--augmented); }
.area-summary .dist-pill.mixed { background: var(--assistive); color: var(--fg); }
.area-summary .dist-pill.zero { background: var(--no-data); color: var(--fg); }
.area-summary .dist-pill.low-confidence { background: var(--low-conf); color: var(--fg); }
.area-summary .dist-pill.empty { background: transparent; color: var(--muted); border: 1px solid var(--line); }
.area-summary .area-notes { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--line); font-size: 0.88rem; line-height: 1.65; color: var(--fg); }
.area-summary .area-notes-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; font-weight: 500; }
.area-summary .activity-ref { font-style: italic; color: var(--muted); }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 20px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: 22px; transition: border-color 0.2s ease, box-shadow 0.2s ease; }
.card:hover { border-color: var(--line); box-shadow: none; }
.card-title { font-size: 1rem; font-weight: 500; margin: 0 0 4px; line-height: 1.4; color: var(--fg); }
.card-id { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.7rem; color: var(--muted); margin-bottom: 12px; }
.card-desc { font-size: 0.85rem; color: var(--muted); margin-bottom: 14px; line-height: 1.5; max-height: 4.2em; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }

.closest-match { background: var(--bg-soft); border-left: 2px solid var(--fg); padding: 12px 14px; margin: 14px 0; border-radius: 0 3px 3px 0; font-size: 0.85rem; line-height: 1.5; }
.closest-match .label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; font-weight: 500; }
.closest-match .task-it { color: var(--fg); margin-bottom: 4px; }
.closest-match .task-en { color: var(--muted); font-style: italic; font-size: 0.78rem; }
.closest-match .metrics { display: flex; gap: 14px; margin-top: 8px; font-size: 0.78rem; flex-wrap: wrap; }
.closest-match .metric strong { font-weight: 500; color: var(--fg); }
.closest-match .metric .key { color: var(--muted); margin-right: 3px; }
.closest-match.no-rich { border-left-color: var(--no-data); }
.closest-match.no-rich .warn { color: var(--muted); font-size: 0.78rem; margin-top: 6px; }

.task-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; margin: 12px 0 14px; max-width: 220px; }
.task-square { aspect-ratio: 1; border-radius: 3px; cursor: pointer; transition: transform 0.1s; position: relative; }
.task-square:hover { transform: scale(1.18); outline: 2px solid var(--fg); z-index: 5; }
.task-square.automated { background: var(--automated); }
.task-square.augmented { background: var(--augmented); }
.task-square.assistive { background: var(--assistive); }
.task-square.no-data { background: var(--no-data); }
.task-square[data-tooltip]:hover::after {
  content: attr(data-tooltip);
  position: absolute; bottom: calc(100% + 8px); left: 50%;
  transform: translateX(-50%) scale(calc(1 / 1.18)); transform-origin: bottom center;
  background: var(--fg); color: var(--bg);
  padding: 9px 12px; border-radius: 3px;
  font-family: var(--font-sans); font-size: 0.75rem; line-height: 1.5;
  width: max-content; max-width: 280px; white-space: pre-line; text-align: left;
  pointer-events: none; z-index: 50; box-shadow: none;
}
.task-square[data-tooltip]:hover::before {
  content: ""; position: absolute; bottom: 100%; left: 50%;
  transform: translateX(-50%); border: 5px solid transparent;
  border-top-color: var(--fg); z-index: 50; pointer-events: none;
}

.card-stat { font-size: 0.85rem; color: var(--muted); padding-top: 12px; border-top: 1px solid var(--line); }
.card-stat .level-tag { display: inline-block; padding: 2px 9px; border-radius: 3px; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--card); margin-right: 8px; font-weight: 500; }
.level-tag.strong { background: var(--automated); }
.level-tag.medium { background: var(--augmented); }
.level-tag.mixed { background: var(--assistive); color: var(--fg); }
.level-tag.zero { background: var(--no-data); color: var(--fg); }
.level-tag.low-confidence { background: var(--low-conf); color: var(--fg); }

.card.low-confidence .task-grid::before { content: "Low confidence — top-1 similarity below threshold."; grid-column: 1 / -1; font-size: 0.78rem; color: var(--muted); padding: 10px; background: var(--low-conf); border-radius: 3px; }
.card.low-confidence .task-grid { max-width: none; }

.modal-backdrop { position: fixed; inset: 0; background: rgba(23,23,23,0.32); display: none; align-items: flex-start; justify-content: center; padding: 60px 16px 16px; z-index: 100; overflow-y: auto; backdrop-filter: blur(4px); }
.modal-backdrop.open { display: flex; animation: pn-fade 0.2s ease; }
.modal { background: var(--card); border-radius: 4px; border: 1px solid var(--line); max-width: 640px; width: 100%; padding: 32px; box-shadow: none; animation: pn-pop 0.25s ease; }
.modal h3 { margin: 0 0 8px; font-size: 1.2rem; font-weight: 600; letter-spacing: -0.01em; }
.modal .modal-id { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.7rem; color: var(--muted); margin-bottom: 18px; }
.modal .modal-task { background: var(--bg-soft); padding: 14px 16px; border-radius: 3px; margin-bottom: 14px; font-size: 0.9rem; line-height: 1.55; border: 1px solid var(--line); }
.modal .modal-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px 24px; font-size: 0.88rem; }
.modal .modal-stats .label { color: var(--muted); }
.modal .modal-close { float: right; background: transparent; border: 0; cursor: pointer; font-size: 1.5rem; color: var(--muted); margin: -10px -10px 0 0; padding: 0; }
.modal .modal-close:hover { color: var(--fg); background: transparent; }

.empty { text-align: center; padding: 64px 0; color: var(--muted); font-size: 0.95rem; }

.footer { margin-top: 56px; padding-top: 20px; border-top: 1px solid var(--line); color: var(--muted); font-size: 0.78rem; }
"""

P25 = 3.21
P75 = 3.57

STRINGS = {
    "en": {
        "subtitle": "Activities matched to O*NET tasks via multilingual embedding. Each square is one of the top-K closest tasks; color shows how Anthropic users delegate that task to Claude. Hover for a quick read, click for details.",
        "legend_automated": "Mostly automated",
        "legend_augmented": "Mostly augmented",
        "legend_assistive": "Assistive",
        "legend_no_data": "Not in Anthropic rich subset",
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
        "footer": "Source: Anthropic Economic Index (release 2026-03-24, 18,510 O*NET tasks). Embedding: paraphrase-multilingual-MiniLM-L12-v2. Min top-1 similarity threshold: 0.55.",
        "closest_match": "Closest O*NET task",
        "confidence": "Confidence",
        "automation": "Automation",
        "low_conf_hint": "Low confidence — top-1 similarity below threshold.",
        "no_area": "(no area)",
        "activities_count": "{n} activities",
        "tooltip_click": "Click for details",
        "tooltip_conv_one": "1 conversation on Claude.ai",
        "tooltip_conv_many": "{n} conversations on Claude.ai",
        "tooltip_no_data": "not in Anthropic rich subset",
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
        "modal_chain_text": "org activity → closest O*NET task by semantic similarity → category assigned by Anthropic to that task's Claude.ai conversations. The category labels the conversation sample, not your activity.",
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
        "area_no_data_full": "No automation metrics available for this area (all matches outside Anthropic's rich subset).",
        "org_overview_label": "Organization snapshot",
        "area_description_label": "Scope",
        "task_distribution_label": "O*NET task distribution (top-K matches)",
        "matches_label": "matches",
        "activities_label": "activities",
    },
    "it": {
        "subtitle": "Per ogni attività ho cercato la mansione più vicina nel catalogo americano dei mestieri. Per quella mansione, un campione di conversazioni con Claude raccolto da Anthropic osserva quanta autonomia Claude aveva quando veniva usato per fare quel lavoro. Ogni quadratino sotto è una delle 5 mansioni più vicine; il colore indica come Claude è stato osservato lavorare su quella mansione. Passa col mouse per la sintesi rapida, click sul quadratino per il dettaglio numerico.",
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


def render_html(matches: list[dict], title: str, metadata: dict[str, dict], lang: str = "en", task_translations: dict[str, str] | None = None, area_notes: dict[str, str] | None = None, area_descriptions: dict[str, str] | None = None, org_description: str = "") -> str:
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

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{base_css() + EXTRA_CSS}</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>{title}</h1>
      <p class="subtitle">{S["subtitle"]}</p>

      <div class="legend">
        <div class="legend-item"><span class="legend-square automated"></span>{S["legend_automated"]}</div>
        <div class="legend-item"><span class="legend-square augmented"></span>{S["legend_augmented"]}</div>
        <div class="legend-item"><span class="legend-square assistive"></span>{S["legend_assistive"]}</div>
        <div class="legend-item"><span class="legend-square no-data"></span>{S["legend_no_data"]}</div>
      </div>
    </header>

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

    <div class="footer">{S["footer"]}</div>
  </div>

  <div class="modal-backdrop" id="modal-backdrop">
    <div class="modal" id="modal">
      <button class="modal-close" id="modal-close">×</button>
      <div id="modal-body"></div>
    </div>
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
  const dist = categoryDistribution(items);
  const description = AREA_DESCRIPTIONS[area];
  const descHtml = description
    ? `<div class="desc-label">${{S.area_description_label}}</div><div class="area-desc">${{escapeHtml(description)}}</div>`
    : '';
  const distLabel = `<div class="desc-label" style="margin-top:4px">${{S.task_distribution_label}}</div>`;
  // Optional commentary.
  const note = AREA_NOTES[area];
  let noteRendered = '';
  if (note) {{
    let safe = escapeHtml(note).replace(/\\n/g, '<br>');
    safe = safe.replace(/\\*([^*\\n]+?)\\*/g, '<em>$1</em>');
    noteRendered = `<div class="area-notes"><div class="area-notes-label">${{S.area_notes_label}}</div>${{safe}}</div>`;
  }}
  return `
    <div class="area-summary">
      ${{descHtml}}
      ${{distLabel}}
      ${{renderDistBar(dist.cats, dist.total)}}
      ${{renderDistLegend(dist.cats, dist.total)}}
      ${{noteRendered}}
    </div>`;
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
    const real = d.matches.slice(0, 25).map((m, idx) => ({{m, idx, cls: classifyMatch(m)}}));
    const order = {{automated: 0, augmented: 1, assistive: 2, 'no-data': 3}};
    real.sort((a, b) => order[a.cls] - order[b.cls]);
    const slots = real.slice();
    while (slots.length < 25) slots.push(null);
    squaresHtml = slots.map(s => {{
      if (!s) return '<div class="task-square no-data" style="opacity:0.2"></div>';
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
      const summaryHtml = renderAreaSummary(area, groups[area]);
      return `
        <div class="area-section">
          <h2>${{escapeHtml(area)}}</h2>
          ${{summaryHtml}}
          <div class="grid">${{cards}}</div>
        </div>`;
    }}).join('');
  }} else if (currentArea !== 'all') {{
    const summaryHtml = renderAreaSummary(currentArea, items);
    content.innerHTML = `${{summaryHtml}}<div class="grid">${{items.map(renderCard).join('')}}</div>`;
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

// Click on a task square → open modal with details
document.addEventListener('click', e => {{
  if (!e.target.classList.contains('task-square')) return;
  const aid = e.target.dataset.activity;
  const idx = parseInt(e.target.dataset.idx, 10);
  if (!aid || isNaN(idx)) return;
  const a = data.find(x => x.id === aid);
  if (!a) return;
  const m = a.matches[idx];
  if (!m) return;
  const cls = classifyMatch(m);
  const catLabel = CATS[cls] || cls;
  const countWarn = (m.count != null && m.count < SAMPLE_SMALL) ? ` <span style="color:var(--accent)">(${{S.modal_count_warn_small}})</span>` : '';
  const richInfo = m.ai_autonomy_mean != null
    ? `<div class="modal-stats">
         <div class="label">${{S.modal_autonomy}}</div><div>${{fmtNum(m.ai_autonomy_mean, 2)}} / 5</div>
         <div class="label">${{S.modal_count}}</div><div>${{m.count != null ? m.count : 0}}${{countWarn}}</div>
         <div class="label">${{S.modal_category}}</div><div>${{catLabel}}</div>
       </div>`
    : `<p style="color:var(--muted); font-size:14px">${{escapeHtml(S.modal_no_rich)}}</p>
       <div class="modal-stats">
         <div class="label">${{S.modal_category}}</div><div>${{catLabel}}</div>
       </div>`;
  const taskItHtml = m.task_it
    ? `<div class="modal-task">
         <strong>${{S.modal_task_it_label}}:</strong><br>
         ${{escapeHtml(m.task_it)}}
       </div>`
    : '';
  document.getElementById('modal-body').innerHTML = `
    <h3>${{escapeHtml(a._title || a.id)}}</h3>
    <div class="modal-id">${{escapeHtml(a.id)}} · ${{escapeHtml(a._area)}}</div>
    ${{taskItHtml}}
    <div class="modal-task">
      <strong>${{S.modal_task_label}}:</strong><br>
      ${{escapeHtml(m.task)}}
    </div>
    <div class="modal-stats">
      <div class="label">${{S.modal_confidence}}</div><div>${{fmtPct(m.similarity)}}</div>
    </div>
    <div style="margin-top:12px">${{richInfo}}</div>
    <div style="margin-top:18px; padding-top:14px; border-top:1px solid var(--line); font-size:12px; color:var(--muted); line-height:1.5">
      <strong style="color:var(--fg)">${{S.modal_chain}}.</strong> ${{escapeHtml(S.modal_chain_text)}}
    </div>
  `;
  document.getElementById('modal-backdrop').classList.add('open');
}});

document.getElementById('modal-close').addEventListener('click', () => {{
  document.getElementById('modal-backdrop').classList.remove('open');
}});

document.getElementById('modal-backdrop').addEventListener('click', e => {{
  if (e.target.id === 'modal-backdrop') {{
    document.getElementById('modal-backdrop').classList.remove('open');
  }}
}});

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
    args = parser.parse_args()

    matches = json.loads(Path(args.matches).read_text())
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

    html = render_html(
        matches, args.title, metadata, lang=args.lang,
        task_translations=translations, area_notes=area_notes,
        area_descriptions=area_descriptions, org_description=org_description,
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
