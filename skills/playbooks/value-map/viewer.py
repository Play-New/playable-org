#!/usr/bin/env python3
"""
value-map / viewer.py — Render a value-map JSON as an interactive HTML
(with companion static SVG for markdown embedding).

The HTML is the primary consumer artefact: top section explains how to read
the map, the SVG below has clickable nodes that open a modal with full info
(label, description, current/target evolution, AI effect, AEI evidence).

The standalone SVG is the secondary artefact for markdown plays (embedded via
![](data/...svg)) — labels are truncated at ~22 chars to keep the static
view readable.

Usage:
    python3 viewer.py --map <chain.json> --html <chain.html> [--svg <chain.svg>]

Internal fields prefixed with `_` (e.g., `_aei`, `_structure_id`) are
consumed by the modal but stripped from the visible SVG.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from html import escape
from pathlib import Path

# Import the shared Play New design system
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from design import base_css  # noqa: E402

# Layout constants
W = 1400
PAD = {"top": 130, "right": 80, "bottom": 70, "left": 120}
MIN_DIST_COMPONENT = 70
MIN_DIST_ANCHOR = 220       # anchors need more horizontal room for labels
NUDGE_PASSES = 5
USER_NODE_Y = 56            # bumped down so label isn't clipped
LABEL_TRUNCATE = 22

# Colors — these are SVG-attribute-injected hex values, kept in sync
# with the data-viz palette declared in skills/design.py (--ds-*).
# CSS in design.py owns the truth; these mirrors exist because SVG
# `fill="..."` attributes don't reliably resolve `var(--ds-sage)`
# across renderers (Chrome OK, Safari & static viewers patchy). When
# you edit the palette in design.py, copy the hex values across here.
FG = "#1a1a1a"        # foreground (rgba(0,0,0,0.9) on white in CSS)
MUTED = "#6b6b6b"     # legacy --muted; design.py uses rgba(0,0,0,0.5)
BG = "#faf9f6"        # paper-white surface
LINE = "#e6e3dd"      # legacy --line; design.py uses rgba(0,0,0,0.1)
ACCENT = "#c47558"    # = --ds-coral
GENESIS = "#88a884"   # = --ds-sage
CUSTOM = "#a5a3c8"    # = --ds-lilac
PRODUCT = "#99b3d4"   # = --ds-slate (was #c8d4e5; unified for consistency)
COMMODITY = "#d8cfb6" # = --ds-sand (was #e8dfc9; unified for consistency)


def truncate(s: str, n: int = LABEL_TRUNCATE) -> str:
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


def stage_name(evolution: float) -> str:
    if evolution < 0.17:
        return "genesis"
    if evolution < 0.40:
        return "custom"
    if evolution < 0.70:
        return "product"
    return "commodity"


def stage_color(evolution: float) -> str:
    return {"genesis": GENESIS, "custom": CUSTOM, "product": PRODUCT, "commodity": COMMODITY}[stage_name(evolution)]


def build_positions(map_data: dict) -> tuple[dict[str, dict], list[str], int]:
    end_users = map_data["end_user"]
    if isinstance(end_users, str):
        end_users = [end_users] if end_users else []

    anchors = map_data["anchors"]
    components = map_data["components"]
    H = 1100 if len(anchors) + len(components) > 14 else 900
    plot_w = W - PAD["left"] - PAD["right"]
    plot_h = H - PAD["top"] - PAD["bottom"]

    def xpos(ev: float) -> float:
        return PAD["left"] + max(0.0, min(1.0, ev)) * plot_w

    def ypos(vis: float) -> float:
        return PAD["top"] + (1 - max(0.0, min(1.0, vis))) * plot_h

    positions: dict[str, dict] = {}

    # End-user nodes spread across top.
    if len(end_users) == 1:
        eu_xs = [PAD["left"] + plot_w * 0.5]
    else:
        spacing = min(300, plot_w / (len(end_users) + 1))
        total = spacing * (len(end_users) - 1)
        start = PAD["left"] + plot_w * 0.5 - total / 2
        eu_xs = [start + i * spacing for i in range(len(end_users))]
    user_ids: list[str] = []
    for i, label in enumerate(end_users):
        uid = f"__user_{i}__"
        user_ids.append(uid)
        positions[uid] = {
            "px": eu_xs[i], "py": USER_NODE_Y,
            "label": label, "kind": "user", "is_new": False,
        }

    new_users = map_data.get("new_end_users") or []
    for j, eu in enumerate(new_users):
        uid = f"__new_user_{j}__"
        positions[uid] = {
            "px": eu_xs[-1] + 100 + j * 100, "py": USER_NODE_Y,
            "label": eu.get("label", ""), "kind": "user", "is_new": True,
        }

    for a in anchors:
        positions[a["id"]] = {
            "px": xpos(a.get("evolution", 0.5)),
            "py": ypos(1.0),
            "label": a.get("label", ""), "kind": "anchor",
            "is_new": bool(a.get("is_new")),
            "evolution_target": a.get("evolution_target"),
            "description": a.get("description", ""),
            "node": a,
        }

    for c in components:
        positions[c["id"]] = {
            "px": xpos(c.get("evolution", 0.5)),
            "py": ypos(c.get("visibility", 0.5)),
            "label": c.get("label", ""), "kind": "component",
            "is_new": bool(c.get("is_new")),
            "evolution_target": c.get("evolution_target"),
            "ai_effect": c.get("ai_effect", ""),
            "description": c.get("_description", ""),
            "node": c,
        }

    # Collision nudging — anchors get larger MIN_DIST.
    real_ids = [a["id"] for a in anchors] + [c["id"] for c in components]

    def dist_for(id_a: str, id_b: str) -> float:
        ka = positions[id_a]["kind"]
        kb = positions[id_b]["kind"]
        if ka == "anchor" or kb == "anchor":
            return MIN_DIST_ANCHOR
        return MIN_DIST_COMPONENT

    for _ in range(NUDGE_PASSES):
        for i in range(len(real_ids)):
            for j in range(i + 1, len(real_ids)):
                pa = positions[real_ids[i]]
                pb = positions[real_ids[j]]
                dx = pb["px"] - pa["px"]
                dy = pb["py"] - pa["py"]
                dist = math.sqrt(dx * dx + dy * dy)
                min_d = dist_for(real_ids[i], real_ids[j])
                if 0 < dist < min_d:
                    push = (min_d - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    pa["px"] -= ux * push
                    pa["py"] -= uy * push
                    pb["px"] += ux * push
                    pb["py"] += uy * push

    # Clamp inside plot.
    for pid, p in positions.items():
        if p["kind"] == "user":
            continue
        p["px"] = max(PAD["left"] + 20, min(W - PAD["right"] - 20, p["px"]))
        p["py"] = max(PAD["top"] + 5, min(H - PAD["bottom"] - 5, p["py"]))

    return positions, user_ids, H


def arc_path(x1: float, y1: float, x2: float, y2: float) -> str:
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return f"M{x1},{y1} L{x2},{y2}"
    bulge = min(length * 0.12, 40)
    nx = -dy / length * bulge
    ny = dx / length * bulge
    return f"M{x1:.1f},{y1:.1f} Q{mx + nx:.1f},{my + ny:.1f} {x2:.1f},{y2:.1f}"


def render_svg_inner(map_data: dict, interactive: bool = False) -> tuple[str, int]:
    """Return (svg_inner_xml, H). When interactive=True, nodes have data-node-id attrs."""
    positions, user_ids, H = build_positions(map_data)
    plot_w = W - PAD["left"] - PAD["right"]
    plot_h = H - PAD["top"] - PAD["bottom"]
    plot_x0 = PAD["left"]
    plot_y0 = PAD["top"]
    plot_x1 = PAD["left"] + plot_w
    plot_y1 = PAD["top"] + plot_h

    parts: list[str] = []

    # Plot frame
    parts.append(
        f'<rect x="{plot_x0}" y="{plot_y0}" width="{plot_w}" height="{plot_h}" '
        f'fill="none" stroke="{LINE}" stroke-width="1"/>'
    )

    # Stage bands
    band_x = lambda ev: plot_x0 + ev * plot_w
    bands = [(0.00, 0.17, GENESIS), (0.17, 0.40, CUSTOM), (0.40, 0.70, PRODUCT), (0.70, 1.00, COMMODITY)]
    for lo, hi, color in bands:
        x = band_x(lo)
        w = band_x(hi) - x
        parts.append(
            f'<rect x="{x:.1f}" y="{plot_y0}" width="{w:.1f}" height="{plot_h}" '
            f'fill="{color}" fill-opacity="0.08" stroke="none"/>'
        )

    # X axis stage labels
    stages = [("Genesis", 0.085), ("Custom", 0.285), ("Product", 0.55), ("Commodity", 0.85)]
    for label, x_frac in stages:
        x = plot_x0 + x_frac * plot_w
        parts.append(
            f'<text x="{x:.1f}" y="{plot_y1 + 28}" text-anchor="middle" '
            f'font-size="13" fill="{MUTED}">{escape(label)}</text>'
        )
    parts.append(
        f'<text x="{(plot_x0 + plot_x1) / 2:.1f}" y="{H - 14}" text-anchor="middle" '
        f'font-size="11" fill="{MUTED}" font-style="italic">evolution →</text>'
    )

    # Y axis label
    parts.append(
        f'<text x="{30}" y="{plot_y0 + plot_h / 2}" text-anchor="middle" '
        f'transform="rotate(-90 30 {plot_y0 + plot_h / 2})" '
        f'font-size="11" fill="{MUTED}" font-style="italic">visibility ↑ (utente) — invisibile ↓</text>'
    )

    # Arrow marker definition
    parts.append(
        f'<defs><marker id="arrow-accent" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{ACCENT}"/></marker></defs>'
    )

    # Edges
    edges = map_data.get("edges", [])
    end_users = map_data["end_user"]
    if isinstance(end_users, str):
        end_users = [end_users] if end_users else []
    for e in edges:
        a_id = e["from"]
        b_id = e["to"]
        if a_id == "__user__" and len(end_users) == 1:
            a_id = "__user_0__"
        if b_id == "__user__" and len(end_users) == 1:
            b_id = "__user_0__"
        pa = positions.get(a_id)
        pb = positions.get(b_id)
        if not pa or not pb:
            continue
        d = arc_path(pa["px"], pa["py"], pb["px"], pb["py"])
        parts.append(
            f'<path d="{d}" stroke="{MUTED}" stroke-opacity="0.4" stroke-width="1" fill="none"/>'
        )

    # End-user nodes
    for uid in user_ids:
        p = positions[uid]
        parts.append(
            f'<g class="node node-user" data-node-id="{uid}">'
            f'<title>{escape(p["label"])}</title>'
            f'<circle cx="{p["px"]:.1f}" cy="{p["py"]:.1f}" r="14" fill="{FG}"/>'
            f'<text x="{p["px"]:.1f}" y="{p["py"] - 26:.1f}" text-anchor="middle" '
            f'font-size="14" fill="{FG}" font-weight="600">{escape(truncate(p["label"]))}</text>'
            f'</g>'
        )

    # New end users
    for j, _ in enumerate(map_data.get("new_end_users") or []):
        p = positions.get(f"__new_user_{j}__")
        if not p:
            continue
        parts.append(
            f'<g class="node node-user node-new" data-node-id="__new_user_{j}__">'
            f'<title>{escape(p["label"])}</title>'
            f'<circle cx="{p["px"]:.1f}" cy="{p["py"]:.1f}" r="12" fill="{ACCENT}"/>'
            f'<text x="{p["px"]:.1f}" y="{p["py"] - 22:.1f}" text-anchor="middle" '
            f'font-size="13" fill="{ACCENT}" font-weight="600">{escape(truncate(p["label"]))} ★</text>'
            f'</g>'
        )

    # Anchors (diamonds)
    for a in map_data["anchors"]:
        p = positions[a["id"]]
        cx, cy = p["px"], p["py"]
        size = 12
        diamond = f"{cx},{cy - size} {cx + size},{cy} {cx},{cy + size} {cx - size},{cy}"
        fill = ACCENT if p["is_new"] else "#ffffff"
        stroke = ACCENT if p["is_new"] else FG
        et = a.get("evolution_target")
        et_arrow = ""
        if et is not None and not p["is_new"]:
            target_x = PAD["left"] + et * plot_w
            et_arrow = (
                f'<line x1="{cx + size + 2:.1f}" y1="{cy:.1f}" x2="{target_x - 4:.1f}" y2="{cy:.1f}" '
                f'stroke="{ACCENT}" stroke-width="1.2" stroke-dasharray="3,3" '
                f'marker-end="url(#arrow-accent)"/>'
            )
        # Label below diamond to avoid colliding with end-user labels above.
        label_y = cy + size + 18
        parts.append(
            f'<g class="node node-anchor" data-node-id="{a["id"]}" style="cursor:pointer">'
            f'<title>{escape(a.get("label", ""))}</title>'
            f'<polygon points="{diamond}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            f'{et_arrow}'
            f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            f'font-size="12" fill="{FG}" font-weight="500">{escape(truncate(p["label"], 26))}</text>'
            f'</g>'
        )

    # Components (circles)
    for c in map_data["components"]:
        p = positions[c["id"]]
        cx, cy = p["px"], p["py"]
        r = 7
        fill = ACCENT if p["is_new"] else "#ffffff"
        stroke = ACCENT if p["is_new"] else FG
        et = c.get("evolution_target")
        et_arrow = ""
        if et is not None and not p["is_new"]:
            target_x = PAD["left"] + et * plot_w
            et_arrow = (
                f'<line x1="{cx + r + 1:.1f}" y1="{cy:.1f}" x2="{target_x - 4:.1f}" y2="{cy:.1f}" '
                f'stroke="{ACCENT}" stroke-width="1.2" stroke-dasharray="3,3" '
                f'marker-end="url(#arrow-accent)"/>'
            )
        # Wrap label at 22 chars, max 2 lines.
        label = truncate(p["label"], 44)  # hard cap
        words = label.split()
        line1, line2 = "", ""
        for w in words:
            test = (line1 + " " + w).strip()
            if len(test) <= LABEL_TRUNCATE:
                line1 = test
            else:
                test2 = (line2 + " " + w).strip()
                if len(test2) <= LABEL_TRUNCATE:
                    line2 = test2
                else:
                    break
        if line2 and len(line2) > LABEL_TRUNCATE - 1:
            line2 = line2[: LABEL_TRUNCATE - 1] + "…"
        text_lines = f'<tspan x="{cx:.1f}" dy="0">{escape(line1)}</tspan>'
        if line2:
            text_lines += f'<tspan x="{cx:.1f}" dy="14">{escape(line2)}</tspan>'
        parts.append(
            f'<g class="node node-component" data-node-id="{c["id"]}" style="cursor:pointer">'
            f'<title>{escape(c.get("label", ""))}</title>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            f'{et_arrow}'
            f'<text x="{cx:.1f}" y="{cy + r + 14:.1f}" text-anchor="middle" '
            f'font-size="11" fill="{FG}">{text_lines}</text>'
            f'</g>'
        )

    inner = "\n".join(parts)
    return inner, H


def render_svg_standalone(map_data: dict) -> str:
    inner, H = render_svg_inner(map_data, interactive=False)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="100%" style="font-family: ui-serif, Georgia, serif; background: {BG};">\n'
        f'{inner}\n</svg>'
    )


EXTRA_CSS = """
:root {
  --bg: var(--bg-soft);
  --fg: var(--fg);
  --muted: var(--muted);
  --line: var(--line);
  --card: var(--bg);
  --accent: var(--fg);
}

body { background: var(--bg-soft); }

.container { max-width: 1480px; margin: 0 auto; padding: 48px 32px 80px; }
.anchor-line { font-size: 0.78rem; color: var(--muted); margin-bottom: 4px; font-family: ui-monospace, SF Mono, Menlo, monospace; text-transform: uppercase; letter-spacing: 0.04em; }
.description { font-size: 0.95rem; color: var(--fg); max-width: 900px; margin-bottom: 0; line-height: 1.65; }

header { padding-bottom: 24px; border-bottom: 1px solid var(--line); margin-bottom: 32px; }
header h1 { font-size: 1.9rem; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 6px; }

.intro { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 24px 28px; margin-bottom: 24px; max-width: 920px; }
.intro h2 { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); font-weight: 500; margin: 0 0 12px; }
.intro p { margin: 0 0 10px; font-size: 0.92rem; line-height: 1.65; color: var(--fg); }
.intro .legend-bullets { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 24px; font-size: 0.85rem; margin-top: 14px; color: var(--muted); }
.intro .legend-bullets strong { color: var(--fg); font-weight: 500; }
.intro .legend-shape { display: inline-block; width: 12px; height: 12px; vertical-align: middle; margin-right: 6px; }
.intro .legend-shape.user { background: var(--fg); border-radius: 50%; }
.intro .legend-shape.anchor { background: var(--card); border: 1.5px solid var(--fg); transform: rotate(45deg); }
.intro .legend-shape.component { background: var(--card); border: 1.5px solid var(--fg); border-radius: 50%; }
.intro .legend-shape.new { background: var(--fg); }
.intro .legend-shape.arrow { width: 18px; height: 1.5px; background: var(--fg); border: none; vertical-align: middle; margin-right: 6px; }

.map-wrap { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 28px; overflow-x: auto; }
.map-wrap svg .node-component circle:hover, .map-wrap svg .node-anchor polygon:hover { stroke-width: 2.5; filter: drop-shadow(0 0 4px rgba(23,23,23,0.18)); }
.map-wrap svg .node { cursor: pointer; }

.stages-fallback { max-width: 920px; }
.stage-section { margin-bottom: 28px; }
.stage-section h2 { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); font-weight: 500; margin: 0 0 12px; }
.comp-card { background: var(--card); border: 1px solid var(--line); border-left: 2px solid var(--soft); border-radius: 3px; padding: 14px 16px; margin-bottom: 10px; cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.comp-card:hover { border-color: var(--line); box-shadow: none; }
.comp-card.is-new { border-left-color: var(--fg); background: var(--bg-soft); }
.comp-label { font-weight: 500; font-size: 0.92rem; color: var(--fg); }
.comp-effect { color: var(--muted); font-size: 0.85rem; margin-top: 6px; line-height: 1.55; }
.comp-target { color: var(--fg); font-size: 0.78rem; margin-top: 6px; font-weight: 500; }

.modal-backdrop { position: fixed; inset: 0; background: rgba(23,23,23,0.32); display: none; align-items: flex-start; justify-content: center; padding: 60px 16px 16px; z-index: 100; overflow-y: auto; backdrop-filter: blur(4px); }
.modal-backdrop.open { display: flex; animation: pn-fade 0.2s ease; }
.modal { background: var(--card); border-radius: 4px; border: 1px solid var(--line); max-width: 720px; width: 100%; padding: 32px; box-shadow: none; animation: pn-pop 0.25s ease; }
.modal .close { float: right; background: transparent; border: 0; cursor: pointer; font-size: 1.5rem; color: var(--muted); margin: -10px -10px 0 0; padding: 0; }
.modal .close:hover { color: var(--fg); background: transparent; }
.modal h3 { margin: 0 0 4px; font-size: 1.4rem; font-weight: 600; letter-spacing: -0.01em; }
.modal .kind { font-size: 0.78rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 18px; }
.modal .desc { font-size: 0.92rem; line-height: 1.7; margin-bottom: 14px; color: var(--fg); }
.modal .section-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 500; margin-top: 18px; margin-bottom: 6px; }
.modal .placement { font-size: 0.9rem; line-height: 1.55; margin-bottom: 4px; color: var(--fg); }
.modal .placement .placement-nums { color: var(--muted); font-size: 0.78rem; font-family: ui-monospace, SF Mono, Menlo, monospace; }
.modal .row { display: grid; grid-template-columns: 180px 1fr; gap: 8px 20px; font-size: 0.85rem; margin-bottom: 8px; }
.modal .row .key { color: var(--muted); }
.modal .row strong { color: var(--fg); font-weight: 500; }
/* Stage pills route through the data-viz palette in design.py — one
   distinct hue per stage so the four bands read at a glance. */
.modal .stage-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.7rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; border: 1px solid; }
.modal .stage-pill.genesis   { background: var(--ds-sage-bg);  color: var(--fg); border-color: var(--ds-sage); }
.modal .stage-pill.custom    { background: var(--ds-lilac-bg); color: var(--fg); border-color: var(--ds-lilac); }
.modal .stage-pill.product   { background: var(--ds-slate-bg); color: var(--fg); border-color: var(--ds-slate); }
.modal .stage-pill.commodity { background: var(--ds-sand-bg);  color: var(--fg); border-color: var(--ds-sand); }
.modal .ai-effect { background: var(--bg-soft); border-left: 2px solid var(--fg); padding: 12px 18px; margin: 14px 0; border-radius: 0 3px 3px 0; font-size: 0.92rem; line-height: 1.65; }
.modal .ai-effect .label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; font-weight: 500; }
.modal .aei-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; margin-top: 12px; }
.modal .aei-table th, .modal .aei-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); }
.modal .aei-table th { color: var(--muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.7rem; background: var(--bg-soft); }
.modal .structure-ref { font-family: ui-monospace, SF Mono, Menlo, monospace; font-size: 0.75rem; color: var(--muted); margin-top: 14px; }
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
      <div class="anchor-line">{anchor_id} · {anchor_kind}</div>
      <p class="description">{description}</p>
    </header>

    <div class="intro">
      <h2>Come leggere questa mappa</h2>
      <p>Questa mappa serve a capire <strong>come funziona oggi un processo dell'organizzazione</strong> e dove si sta muovendo. Non serve conoscere l'organizzazione dall'interno: cliccando un qualsiasi nodo si legge cosa fa, perché si trova in quel punto della mappa, e cosa sta cambiando.</p>
      <p><strong>Cosa rappresentano i nodi.</strong> In alto il cerchio nero è l'<em>utente finale</em>, cioè chi riceve il valore alla fine della catena. Sotto, i diamanti sono i <em>bisogni dell'utente</em>: cosa sta cercando di ottenere. Sotto ancora, i cerchi bianchi sono i <em>componenti del processo</em> che producono valore per soddisfare quei bisogni. I cerchi arancioni indicano cose <em>nuove o emergenti</em>: non esistono oggi ma compaiono se il processo si trasforma.</p>
      <p><strong>Cosa significano le posizioni.</strong> L'asse orizzontale è l'<em>evoluzione del componente nel mercato</em>: a sinistra le cose ancora nuove o fatte su misura, a destra le cose standardizzate disponibili come servizio o commodity. La mappa è divisa in quattro fasce — territorio nuovo (genesis), su misura interna (custom), pratica diffusa con fornitori (product), standard di mercato (commodity). L'asse verticale è la <em>visibilità</em>: in alto i pezzi che l'utente percepisce direttamente, in basso l'infrastruttura che lavora dietro le quinte.</p>
      <p><strong>Cosa significa l'overlay AI</strong> (le frecce tratteggiate arancioni). Sono spostamenti attesi verso destra basati sul campione di conversazioni Claude raccolto da Anthropic. Quel campione osserva come gli utenti di Claude usano l'AI su mansioni del catalogo americano dei mestieri, registrando per ognuna quanta autonomia Claude aveva (su scala 1=solo aiuto, 5=lavoro autonomo). Quando un componente di questo processo corrisponde semanticamente a una mansione che il campione vede usata con autonomia alta, è verosimile che il componente si standardizzi: la freccia mostra dove e in quale fascia. Cliccando il nodo si vede il dato specifico (vicinanza in %, autonomia di Claude, numero di conversazioni) che giustifica lo spostamento.</p>
      <div class="legend-bullets">
        <div><span class="legend-shape user"></span><strong>Cerchio nero</strong> · utente finale</div>
        <div><span class="legend-shape anchor"></span><strong>Diamante</strong> · bisogno dell'utente</div>
        <div><span class="legend-shape component"></span><strong>Cerchio bianco</strong> · componente del processo</div>
        <div><span class="legend-shape new"></span><strong>Arancione</strong> · nuovo / emergente</div>
        <div><span class="legend-shape arrow"></span><strong>Freccia tratteggiata</strong> · spostamento atteso (AI overlay)</div>
        <div style="grid-column: span 2; margin-top: 6px; font-style: italic;">Click su qualsiasi nodo per il dettaglio: cosa è, dove sta sulla mappa, dove si sta spostando, dato Anthropic dietro.</div>
      </div>
    </div>

    <div class="map-wrap">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" style="font-family: ui-serif, Georgia, serif; background: {bg};">
{svg_inner}
      </svg>
    </div>

    <div class="stages-fallback">
      <h2 style="font-size: 18px; font-weight: 500; margin: 0 0 14px;">Componenti raggruppati per stage</h2>
      {stages_html}
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

function stageFor(ev) {{
  if (ev < 0.17) return 'genesis';
  if (ev < 0.40) return 'custom';
  if (ev < 0.70) return 'product';
  return 'commodity';
}}

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({{
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }})[c]);
}}

const STAGE_PLAIN = {{
  genesis:   'territorio nuovo, ancora da capire',
  custom:    'fatto su misura per l'organizzazione, non standardizzato',
  product:   'pratica diffusa, esistono fornitori e modelli',
  commodity: 'standard di mercato, indistinguibile fra fornitori',
}};

function renderModal(node) {{
  const isAnchor = node._kind === 'anchor';
  const isUser = node._kind === 'user';
  const stage = (node.evolution != null) ? stageFor(node.evolution) : null;

  let html = `<h3>${{escapeHtml(node.label || node.id)}}</h3>`;
  let kind = isAnchor ? 'Bisogno-anchor (cosa l\\'utente vuole)' : (isUser ? 'Utente finale' : 'Componente del processo');
  if (node._kind === 'unit') kind = 'Unità organizzativa';
  if (node._kind === 'activity') kind = 'Attività del processo';
  if (node._kind === 'stakeholder') kind = 'Stakeholder esterno (fornitore o controparte)';
  if (node.is_new) kind = 'Nuovo / emergente · ' + kind;
  html += `<div class="kind">${{escapeHtml(kind)}}</div>`;

  // 1. Cosa è — plain language
  const desc = node._body || node.description;
  if (desc) {{
    html += `<div class="section-label">Cosa è</div>`;
    html += `<div class="desc">${{escapeHtml(desc)}}</div>`;
  }}

  // 2. Dove sta sulla mappa — plain language explanation of position
  if (!isUser && node.evolution != null) {{
    const visText = (node.visibility != null)
      ? (node.visibility >= 0.7 ? 'molto visibile all\\'utente' : (node.visibility >= 0.4 ? 'a metà strada tra utente e infrastruttura' : 'profondamente nell\\'infrastruttura'))
      : '';
    html += `<div class="section-label">Dove sta sulla mappa</div>`;
    html += `<div class="placement"><span class="stage-pill ${{stage}}">${{stage}}</span>`;
    html += ` <span class="placement-text">${{STAGE_PLAIN[stage]}}</span>`;
    if (visText) html += `, <span class="placement-text">${{visText}}</span>`;
    html += ` <span class="placement-nums">(evolution ${{Number(node.evolution).toFixed(2)}}${{node.visibility != null ? ', visibility ' + Number(node.visibility).toFixed(2) : ''}})</span></div>`;
  }}

  // 3. Spostamento atteso — narrative
  if (node.evolution_target != null && !node.is_new) {{
    const ts = stageFor(node.evolution_target);
    const direction = (node.evolution_target > node.evolution + 0.05) ? 'a destra (verso più standardizzazione)' : 'movimento minimo';
    html += `<div class="section-label">Dove si sta spostando</div>`;
    html += `<div class="placement">→ <span class="stage-pill ${{ts}}">${{ts}}</span>`;
    html += ` <span class="placement-text">— ${{direction}}; ${{STAGE_PLAIN[ts]}}</span>`;
    html += ` <span class="placement-nums">(target ${{Number(node.evolution_target).toFixed(2)}})</span></div>`;
  }}
  if (node.is_new) {{
    html += `<div class="section-label">Stato</div>`;
    html += `<div class="placement"><strong>Componente nuovo</strong> — non esiste ancora oggi, ma emerge dal cambiamento del value chain. Le frecce in entrata indicano cosa ne abilita la nascita.</div>`;
  }}

  // 4. AI effect — narrative framing
  if (node.ai_effect) {{
    html += `<div class="ai-effect">`;
    html += `<div class="label">Effetto AI — cosa cambia secondo i dati Anthropic</div>`;
    html += `<div>${{escapeHtml(node.ai_effect)}}</div>`;
    html += `</div>`;
  }} else if (node.evolution_target != null) {{
    html += `<div class="ai-effect">`;
    html += `<div class="label">Effetto AI — cosa cambia secondo i dati Anthropic</div>`;
    html += `<div>Lo spostamento è inferito dal dato Anthropic (vedi tabella sotto), ma non c'è un commento testuale specifico per questo componente.</div>`;
    html += `</div>`;
  }}

  // 5. AEI evidence
  if (node._aei && node._aei.top_matches && node._aei.top_matches.length) {{
    html += `<div class="section-label" style="margin-top:18px">Dato Anthropic dietro</div>`;
    html += `<div style="font-size:13px;color:var(--muted);margin-bottom:8px;line-height:1.55">Per ogni componente di questo processo ho cercato la mansione più vicina nel catalogo americano dei mestieri (descritto in inglese sotto). Per quella mansione il campione Anthropic delle conversazioni Claude osserva quanto Claude è stato usato (numero di conversazioni) e con quale autonomia (su scala 1=solo aiuto, 5=lavoro autonomo). Sotto le 100 conversazioni il dato è fragile.</div>`;
    html += `<table class="aei-table"><thead><tr><th>Task O*NET (mansione US)</th><th>Sim.</th><th>Aut.</th><th>Conv.</th></tr></thead><tbody>`;
    for (const m of node._aei.top_matches) {{
      const sim = m.similarity != null ? Number(m.similarity).toFixed(2) : '—';
      const aut = m.ai_autonomy_mean != null ? Number(m.ai_autonomy_mean).toFixed(2) : '<span style="color:#999">—</span>';
      const cnt = m.count != null && m.count > 0 ? m.count : '<span style="color:#999">0</span>';
      html += `<tr><td>${{escapeHtml((m.task||'').slice(0,110))}}</td><td>${{sim}}</td><td>${{aut}}</td><td>${{cnt}}</td></tr>`;
    }}
    html += `</tbody></table>`;
  }}

  // 6. Structure ref
  if (node._structure_id) {{
    html += `<div class="structure-ref">Nodo struttura: <code>${{escapeHtml(node._structure_id)}}</code>${{node._kind ? ' (' + escapeHtml(node._kind) + ')' : ''}}</div>`;
  }}

  document.getElementById('modal-body').innerHTML = html;
  document.getElementById('modal-backdrop').classList.add('open');
}}

// Robust event delegation: closest() on SVG is unreliable across
// engines, so we walk up the DOM manually to find the .node or
// .comp-card ancestor.
document.addEventListener('click', (e) => {{
  let n = e.target;
  while (n && n.nodeType === 1) {{
    if (n.classList && (n.classList.contains('node') || n.classList.contains('comp-card'))) {{
      const id = n.dataset && (n.dataset.nodeId || n.dataset.id);
      if (id && NODES[id]) renderModal(NODES[id]);
      return;
    }}
    n = n.parentNode;
  }}
}});

document.getElementById('modal-close').addEventListener('click', () => {{
  document.getElementById('modal-backdrop').classList.remove('open');
}});
document.getElementById('modal-backdrop').addEventListener('click', (e) => {{
  if (e.target.id === 'modal-backdrop') document.getElementById('modal-backdrop').classList.remove('open');
}});
document.addEventListener('keydown', (e) => {{
  if (e.key === 'Escape') document.getElementById('modal-backdrop').classList.remove('open');
}});
</script>
</body>
</html>"""


def render_html(map_data: dict) -> str:
    inner, H = render_svg_inner(map_data, interactive=True)
    anchor = map_data.get("_anchor", {})
    title = anchor.get("title") or "Value map"
    anchor_id = anchor.get("id", "")
    anchor_kind = anchor.get("kind", "")
    description = anchor.get("description", "")

    # Build stages_html (text fallback grouped by stage)
    stages = [
        ("Genesis (0.00–0.17)", 0.00, 0.17),
        ("Custom (0.17–0.40)", 0.17, 0.40),
        ("Product (0.40–0.70)", 0.40, 0.70),
        ("Commodity (0.70–1.00)", 0.70, 1.01),
    ]
    blocks: list[str] = []
    for label, lo, hi in stages:
        comps = [c for c in map_data["components"] if lo <= c.get("evolution", 0) < hi]
        if not comps:
            continue
        cards = []
        for c in comps:
            new_class = " is-new" if c.get("is_new") else ""
            ai_eff = (
                f'<div class="comp-effect">{escape(c["ai_effect"])}</div>'
                if c.get("ai_effect") else ""
            )
            target = ""
            et = c.get("evolution_target")
            if et is not None and not c.get("is_new"):
                target = f'<div class="comp-target">→ shift verso evolution {et:.2f}</div>'
            cards.append(
                f'<div class="comp-card{new_class}" data-id="{escape(c["id"])}">'
                f'<div class="comp-label">{escape(c.get("label", ""))}</div>'
                f'{ai_eff}{target}'
                f'</div>'
            )
        blocks.append(f'<div class="stage-section"><h2>{escape(label)}</h2>{"".join(cards)}</div>')

    # Build nodes JSON for modal lookup.
    nodes: dict[str, dict] = {}
    end_users = map_data["end_user"]
    if isinstance(end_users, str):
        end_users = [end_users] if end_users else []
    for i, eu in enumerate(end_users):
        nodes[f"__user_{i}__"] = {"label": eu, "_kind": "user"}
    for j, eu in enumerate(map_data.get("new_end_users") or []):
        nodes[f"__new_user_{j}__"] = {**eu, "_kind": "user", "is_new": True}
    for a in map_data["anchors"]:
        nodes[a["id"]] = {**a, "_kind": "anchor"}
    for c in map_data["components"]:
        nodes[c["id"]] = c

    return HTML_TEMPLATE.format(
        css=base_css() + EXTRA_CSS,
        title=escape(title),
        anchor_id=escape(anchor_id),
        anchor_kind=escape(anchor_kind),
        description=escape(description),
        W=W,
        H=H,
        bg=BG,
        svg_inner=inner,
        stages_html="\n".join(blocks),
        nodes_json=json.dumps(nodes, ensure_ascii=False),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render value-map JSON as interactive HTML (and optional SVG).")
    parser.add_argument("--map", required=True, help="WardleyMap JSON path")
    parser.add_argument("--html", required=True, help="Output HTML path (primary artefact)")
    parser.add_argument("--svg", help="Optional standalone SVG path (for markdown embedding)")
    args = parser.parse_args()

    map_data = json.loads(Path(args.map).read_text(encoding="utf-8"))

    if not map_data.get("components") or not map_data.get("anchors"):
        print("Map has no components or no anchors; nothing to render.", file=sys.stderr)
        return 1

    html = render_html(map_data)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"Wrote {Path(args.html).resolve()} ({len(html):,} bytes)")

    if args.svg:
        svg = render_svg_standalone(map_data)
        Path(args.svg).write_text(svg, encoding="utf-8")
        print(f"Wrote {Path(args.svg).resolve()} ({len(svg):,} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
