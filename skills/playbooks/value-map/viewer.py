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
MIN_DIST_COMPONENT = 110     # bumped from 70 for better spread / no overlap
MIN_DIST_ANCHOR    = 260     # anchors need horizontal room for labels
NUDGE_PASSES       = 14      # bumped from 5 — more passes converge to clean layout
USER_NODE_Y        = 56      # bumped down so label isn't clipped
LABEL_TRUNCATE     = 22

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
    # New end users sit 200px to the right of the last existing user so
    # their labels don't collide horizontally with the existing user labels.
    for j, eu in enumerate(new_users):
        uid = f"__new_user_{j}__"
        positions[uid] = {
            "px": eu_xs[-1] + 220 + j * 200, "py": USER_NODE_Y,
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

    # Plot axes — only the left (Y) and bottom (X) edges, no full rectangle.
    # Play New convention: hairlines, white space, no boxes around boxes.
    parts.append(
        f'<line x1="{plot_x0}" y1="{plot_y0}" x2="{plot_x0}" y2="{plot_y1}" '
        f'stroke="{LINE}" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{plot_x0}" y1="{plot_y1}" x2="{plot_x1}" y2="{plot_y1}" '
        f'stroke="{LINE}" stroke-width="1"/>'
    )

    # Stage divisions — tiny tick marks on the X axis at the boundaries
    # (no full vertical lines, no fills behind).
    band_x = lambda ev: plot_x0 + ev * plot_w
    for boundary in (0.17, 0.40, 0.70):
        x = band_x(boundary)
        parts.append(
            f'<line x1="{x:.1f}" y1="{plot_y1 - 6:.1f}" x2="{x:.1f}" y2="{plot_y1 + 6:.1f}" '
            f'stroke="{LINE}" stroke-width="1"/>'
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

    # Edges. The JSON only carries component→component dependency edges
    # (built from activity input/output and unit→activity relationships).
    # The Wardley chain user→anchor→top-level-components is logical and
    # should always render; we infer those edges here so the value-map
    # is connected even if the agent forgot them.
    edges = list(map_data.get("edges") or [])
    end_users = map_data["end_user"]
    if isinstance(end_users, str):
        end_users = [end_users] if end_users else []
    components = map_data.get("components") or []
    anchors = map_data.get("anchors") or []

    # Implicit user → anchor edges: every end-user (existing and new)
    # connects to every anchor (the user need the org promises to
    # fulfill). Without this, new stakeholders would float disconnected.
    new_user_ids = [f"__new_user_{j}__" for j in range(len(map_data.get("new_end_users") or []))]
    for uid in list(user_ids) + new_user_ids:
        for a in anchors:
            edges.append({"from": uid, "to": a["id"], "_implicit": True})

    # Implicit anchor → unit-level component edges. Top-level components
    # are anything with `_kind: "unit"` — these are the entry points of
    # the chain that delivers the user need. (Activities sit under units.)
    unit_ids = [c["id"] for c in components if c.get("_kind") == "unit"]
    if not unit_ids:
        # Fallback: components with no incoming dependency edges.
        incoming = {e.get("to") for e in (map_data.get("edges") or [])}
        unit_ids = [c["id"] for c in components if c["id"] not in incoming]
    for a in anchors:
        for cid in unit_ids:
            edges.append({"from": a["id"], "to": cid, "_implicit": True})

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
            f'<g class="node node-user" data-node-id="{uid}" onclick="pnNodeClick(this)">'
            f'<title>{escape(p["label"])}</title>'
            f'<circle cx="{p["px"]:.1f}" cy="{p["py"]:.1f}" r="14" fill="{FG}"/>'
            f'<text x="{p["px"]:.1f}" y="{p["py"] - 26:.1f}" text-anchor="middle" '
            f'font-size="14" fill="{FG}" font-weight="600">{escape(truncate(p["label"]))}</text>'
            f'</g>'
        )

    # New end users — squares (matching the is_new component shape) so
    # everything emerging shares the same visual code: square = new.
    for j, _ in enumerate(map_data.get("new_end_users") or []):
        p = positions.get(f"__new_user_{j}__")
        if not p:
            continue
        sq = 14  # half-side; total side = 28, slightly larger than r=12 for visual parity
        parts.append(
            f'<g class="node node-user node-new" data-node-id="__new_user_{j}__" onclick="pnNodeClick(this)">'
            f'<title>{escape(p["label"])}</title>'
            f'<rect x="{p["px"] - sq:.1f}" y="{p["py"] - sq:.1f}" width="{sq * 2}" height="{sq * 2}" fill="{ACCENT}"/>'
            f'<text x="{p["px"]:.1f}" y="{p["py"] - sq - 8:.1f}" text-anchor="middle" '
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
            f'<g class="node node-anchor" data-node-id="{a["id"]}" onclick="pnNodeClick(this)" style="cursor:pointer">'
            f'<title>{escape(a.get("label", ""))}</title>'
            f'<polygon points="{diamond}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            f'{et_arrow}'
            f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            f'font-size="12" fill="{FG}" font-weight="500">{escape(truncate(p["label"], 26))}</text>'
            f'</g>'
        )

    # Components — circles for existing, squares for is_new (so the
    # leader's eye separates "what shifts" from "what emerges" at a glance).
    for c in map_data["components"]:
        p = positions[c["id"]]
        cx, cy = p["px"], p["py"]
        r = 7
        fill = ACCENT if p["is_new"] else "#ffffff"
        stroke = ACCENT if p["is_new"] else FG
        if p["is_new"]:
            shape = (
                f'<rect x="{cx - r:.1f}" y="{cy - r:.1f}" width="{r * 2}" height="{r * 2}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            )
        else:
            shape = (
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            )
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
            f'<g class="node node-component{" node-new" if p["is_new"] else ""}" data-node-id="{c["id"]}" onclick="pnNodeClick(this)" style="cursor:pointer">'
            f'<title>{escape(c.get("label", ""))}</title>'
            f'{shape}'
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
/* Value-map viewer — Play New design.
   Pure white surface, editorial typography, hairlines, single accent. */

body { background: #FFFFFF; color: var(--fg); }

.container { max-width: 1240px; margin: 0 auto; padding: 80px 40px 96px; }

header { margin: 0 auto 48px; max-width: 820px; }
header .eyebrow { font-family: var(--font-display); font-size: 0.74rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; color: var(--fg-muted); margin-bottom: 16px; }
header h1 { font-family: var(--font-display); font-size: clamp(1.9rem, 3.5vw, 2.6rem); font-weight: 500; letter-spacing: -0.025em; line-height: 1.1; margin: 0 0 16px; color: var(--fg); }
header .lead { font-size: 1.0rem; color: var(--fg-muted); line-height: 1.65; margin: 0; max-width: 720px; }

.map-wrap { padding: 24px 0; margin: 24px 0; overflow-x: auto; }
.map-wrap svg { display: block; }
.map-wrap svg .node { cursor: pointer; }
.map-wrap svg .node:hover circle, .map-wrap svg .node:hover polygon { stroke-width: 2; }

.legend-wrap { max-width: 820px; margin: 8px auto 0; }
.legend { display: flex; gap: 28px; flex-wrap: wrap; font-size: 0.82rem; color: var(--fg-muted); margin: 0; align-items: center; }
.legend .item { display: flex; align-items: center; gap: 8px; }
.legend .shape { display: inline-block; width: 12px; height: 12px; }
.legend .shape.user { background: var(--fg); border-radius: 50%; }
.legend .shape.anchor { background: transparent; border: 1.5px solid var(--fg); transform: rotate(45deg); }
.legend .shape.component { background: transparent; border: 1.5px solid var(--fg); border-radius: 50%; }
.legend .shape.new { background: var(--ds-coral); }
.legend .shape.arrow { width: 22px; height: 1.5px; background: var(--ds-coral); }

.section { margin: 96px auto 0; padding-top: 40px; border-top: 1px solid var(--fg-hairline); max-width: 820px; }
.section h2 { font-family: var(--font-display); font-size: 1.5rem; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 20px; }
.section p { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 14px; max-width: 720px; }
.section .lead { font-size: 0.95rem; color: var(--fg-muted); line-height: 1.65; max-width: 720px; margin: 0 0 28px; }

.no-overlay { font-size: 0.9rem; color: var(--fg-muted); padding: 18px 22px; background: var(--bg-alt); border-radius: 4px; max-width: 720px; line-height: 1.6; }
.no-overlay code { font-size: 0.85em; }

.decision { margin-bottom: 32px; }
.decision .question { font-family: var(--font-display); font-size: 1.05rem; font-weight: 500; color: var(--fg); margin: 0 0 8px; letter-spacing: -0.01em; }
.decision .answer { font-size: 0.95rem; line-height: 1.7; color: var(--fg); margin: 0 0 6px; max-width: 720px; }
.decision .source { font-size: 0.78rem; color: var(--fg-muted); font-family: ui-monospace, SF Mono, Menlo, monospace; }

/* Popover — small floating card next to the clicked node. Replaces the
   full-screen modal: pop-overs read as 'a tooltip you can read', not 'a
   page you have to dismiss'. */
.popover { position: absolute; display: none; max-width: 320px; min-width: 220px; padding: 14px 18px 16px; background: #FFFFFF; border: 1px solid var(--fg-hairline); border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); z-index: 100; animation: pn-pop 0.18s ease; }
.popover.open { display: block; }
.popover .close { position: absolute; top: 6px; right: 8px; background: transparent; border: 0; cursor: pointer; font-size: 1.1rem; color: var(--fg-muted); padding: 0; line-height: 1; }
.popover .close:hover { color: var(--fg); background: transparent; }
.popover .eyebrow { font-family: var(--font-display); font-size: 0.62rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px; color: var(--fg-muted); }
.popover .eyebrow.is-new { color: var(--ds-coral); }
.popover h3 { font-family: var(--font-display); font-size: 1rem; font-weight: 500; letter-spacing: -0.015em; margin: 0 0 8px; line-height: 1.25; color: var(--fg); padding-right: 18px; }
.popover .body p { font-size: 0.84rem; line-height: 1.55; color: var(--fg); margin: 0 0 8px; }
.popover .body p:last-child { margin-bottom: 0; }
.popover .body em.placement { color: var(--fg-muted); font-style: normal; }
.popover .citation { font-size: 0.7rem; color: var(--fg-muted); padding-top: 8px; margin-top: 10px; border-top: 1px solid var(--fg-hairline); font-family: ui-monospace, SF Mono, Menlo, monospace; }
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title} · value map</title>
<style>{css}</style>
</head>
<body>
  <div class="container">
    <header>
      <div class="eyebrow">value map</div>
      <h1>{title}</h1>
      <p class="lead">{description}</p>
    </header>

    <div class="map-wrap">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" style="font-family: var(--font-display);">
{svg_inner}
      </svg>
    </div>

    <div class="legend-wrap">
      <div class="legend">
        <div class="item"><span class="shape user"></span><span>End user</span></div>
        <div class="item"><span class="shape anchor"></span><span>User need</span></div>
        <div class="item"><span class="shape component"></span><span>Part of the chain</span></div>
        <div class="item"><span class="shape new"></span><span>New / emerging</span></div>
        <div class="item"><span class="shape arrow"></span><span>Where AI is pushing</span></div>
      </div>
    </div>

    {ai_overlay_section}

    {decisions_section}
  </div>

  <div class="popover" id="popover">
    <button class="close" id="popover-close" aria-label="Close">×</button>
    <div id="popover-body"></div>
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
  genesis:   'new territory — nobody knows yet how to do this well',
  custom:    'built in-house — every shop figures it out their own way',
  product:   'common practice — vendors and patterns exist, you can buy it',
  commodity: 'market standard — indistinguishable across providers',
}};

function kindLabel(node) {{
  if (node.is_new) return 'New / emerging';
  if (node._kind === 'anchor') return 'User need';
  if (node._kind === 'user') return 'End user';
  if (node._kind === 'unit') return 'Unit';
  if (node._kind === 'activity') return 'Activity';
  if (node._kind === 'stakeholder') return 'External stakeholder';
  return 'Part of the chain';
}}

function renderPopoverContent(node) {{
  const isUser = node._kind === 'user';
  const stage = node.evolution != null ? stageFor(node.evolution) : null;
  const eyebrowCls = node.is_new ? 'eyebrow is-new' : 'eyebrow';

  let html = `<div class="${{eyebrowCls}}">${{escapeHtml(kindLabel(node))}}</div>`;
  html += `<h3>${{escapeHtml(node.label || node.id)}}</h3>`;
  html += '<div class="body">';

  // Prefer the short frontmatter description for popover punch; fall
  // through to longer extracts only if it's missing.
  const desc = node.description || node._description || node._body;
  if (desc) {{
    html += `<p>${{escapeHtml(desc)}}</p>`;
  }}

  if (!isUser && node.evolution != null) {{
    const visText = node.visibility != null
      ? (node.visibility >= 0.7 ? ' Visible to the client.'
         : node.visibility >= 0.4 ? ' Mid-chain.'
         : ' Behind the scenes.')
      : '';
    html += `<p><em class="placement">${{STAGE_PLAIN[stage]}}.${{visText}}</em></p>`;
  }}

  if (node.evolution_target != null && !node.is_new) {{
    html += `<p><em class="placement">→ Heading toward ${{STAGE_PLAIN[stageFor(node.evolution_target)]}}.</em></p>`;
  }}

  if (node.ai_effect) {{
    html += `<p>${{escapeHtml(node.ai_effect)}}</p>`;
  }}

  if (node.is_new) {{
    html += `<p><em class="placement">Emerging — does not exist today.</em></p>`;
  }}

  html += '</div>';

  if (node._structure_id) {{
    html += `<div class="citation">${{escapeHtml(node._structure_id)}}</div>`;
  }}

  return html;
}}

const popoverEl   = document.getElementById('popover');
const popoverBody = document.getElementById('popover-body');

function showPopover(node, anchorRect) {{
  popoverBody.innerHTML = renderPopoverContent(node);
  // Position to the right of the node, vertically aligned to the top.
  const margin = 12;
  // Step 1: place at preferred position (right of node), measure.
  popoverEl.style.left = '0px';
  popoverEl.style.top = '0px';
  popoverEl.classList.add('open');
  const popRect = popoverEl.getBoundingClientRect();
  const popW = popRect.width;
  const popH = popRect.height;

  // Right of node by default
  let x = anchorRect.right + margin;
  let y = anchorRect.top;

  // Flip to left if it would overflow the right edge
  const viewportRight = window.scrollX + window.innerWidth;
  if (x + popW > viewportRight - margin) {{
    x = anchorRect.left - margin - popW;
  }}
  // Clamp into viewport horizontally
  if (x < window.scrollX + margin) x = window.scrollX + margin;

  // Clamp into viewport vertically (so it never falls off-screen)
  const viewportBottom = window.scrollY + window.innerHeight;
  if (y + popH > viewportBottom - margin) {{
    y = viewportBottom - popH - margin;
  }}
  if (y < window.scrollY + margin) y = window.scrollY + margin;

  popoverEl.style.left = x + 'px';
  popoverEl.style.top  = y + 'px';
}}

function hidePopover() {{
  popoverEl.classList.remove('open');
}}

// Inline onclick="pnNodeClick(this)" on every <g class="node"> in the
// SVG calls this. Reliable across renderers; no event delegation gymnastics.
window.pnNodeClick = function(el) {{
  const id = el.dataset && el.dataset.nodeId;
  if (id && NODES[id]) {{
    const rect = el.getBoundingClientRect();
    // Convert to absolute coords (positions live in the document, not
    // the viewport).
    const absRect = {{
      left:   rect.left   + window.scrollX,
      right:  rect.right  + window.scrollX,
      top:    rect.top    + window.scrollY,
      bottom: rect.bottom + window.scrollY,
    }};
    showPopover(NODES[id], absRect);
  }}
}};

// Belt-and-suspenders: a document-level click listener in case inline
// onclick is stripped by some sanitizer or doesn't bind on a given
// renderer. Walks up parentNode manually (closest() on SVG is uneven).
document.addEventListener('click', function(e) {{
  // Close on click outside the popover and outside any node.
  let n = e.target;
  let onNode = false, onPopover = false;
  while (n && n.nodeType === 1) {{
    if (n.classList && n.classList.contains('node')) {{ onNode = true; break; }}
    if (n.id === 'popover') {{ onPopover = true; break; }}
    n = n.parentNode;
  }}
  if (onNode) {{
    // pnNodeClick already handled it via inline onclick, but also do it
    // here for renderers that strip inline onclick.
    let g = e.target;
    while (g && !(g.classList && g.classList.contains('node'))) g = g.parentNode;
    if (g) {{
      const id = g.dataset && g.dataset.nodeId;
      if (id && NODES[id]) {{
        const rect = g.getBoundingClientRect();
        showPopover(NODES[id], {{
          left:   rect.left   + window.scrollX,
          right:  rect.right  + window.scrollX,
          top:    rect.top    + window.scrollY,
          bottom: rect.bottom + window.scrollY,
        }});
      }}
    }}
  }} else if (!onPopover) {{
    hidePopover();
  }}
}}, true);

document.getElementById('popover-close').addEventListener('click', hidePopover);
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') hidePopover(); }});
</script>
</body>
</html>"""


def render_html(map_data: dict) -> str:
    inner, H = render_svg_inner(map_data, interactive=True)
    anchor = map_data.get("_anchor", {})
    title = anchor.get("title") or "Value map"
    # Lead paragraph fallback chain: anchor.description -> anchor.terms ->
    # commitment terms field if build.py preserved it. The page header
    # needs SOMETHING substantive under the H1.
    description = (
        anchor.get("description")
        or anchor.get("terms")
        or ""
    )

    # AI overlay — surface a clear notice when no component carries either
    # `evolution_target` or `ai_effect`. The arrows on the map carry the
    # signal when present; when absent the reader needs to know it's a
    # gap, not a "no AI shift expected here" claim.
    components = map_data.get("components", [])
    has_ai = any(c.get("ai_effect") or c.get("evolution_target") is not None for c in components)
    if has_ai:
        ai_overlay_section = ""
    else:
        ai_overlay_section = (
            '<div class="section">'
            '<h2>Where AI is pushing</h2>'
            '<div class="no-overlay">'
            "This map shows where each piece of the chain sits today, but it "
            "doesn't yet show where AI is pushing it. The dashed arrows that "
            "would normally appear on each node, pointing to the right toward "
            "more standardization, need observed AI-usage data to be drawn. "
            "Run the <em>ai-exposure</em> playbook first; the result is a set "
            "of matches between the studio's activities and observed AI usage "
            "in the world. Then re-render this map with that overlay on."
            '</div></div>'
        )

    # Decisions enabled — the load-bearing interpretive section. If the
    # JSON carries a `decisions` array (each item: {question, answer,
    # source}), render it; otherwise prompt for one.
    decisions = map_data.get("decisions") or []
    if decisions:
        items: list[str] = []
        for d in decisions:
            q = escape(d.get("question", ""))
            a = escape(d.get("answer", ""))
            src = d.get("source", "") or d.get("citation", "")
            src_div = f'<div class="source">{escape(src)}</div>' if src else ""
            items.append(
                f'<div class="decision">'
                f'<div class="question">{q}</div>'
                f'<div class="answer">{a}</div>'
                f'{src_div}'
                f'</div>'
            )
        decisions_section = (
            '<div class="section">'
            '<h2>How to read this map</h2>'
            '<p class="lead">'
            'The map alone is just positions. Below are the questions someone '
            'looking at it should be asking, and what the positions suggest as '
            'an answer. Each is a move you could make on Monday morning.'
            '</p>'
            f'{"".join(items)}'
            '</div>'
        )
    else:
        decisions_section = (
            '<div class="section">'
            '<h2>How to read this map</h2>'
            '<div class="no-overlay">'
            "The map shows where each piece of the work sits today. What to "
            "do with that — which moves it suggests, what it tells you about "
            "where the value is and where it's heading — is the next step. "
            "It hasn't been authored yet for this map."
            '</div></div>'
        )

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
        description=escape(description),
        W=W,
        H=H,
        svg_inner=inner,
        ai_overlay_section=ai_overlay_section,
        decisions_section=decisions_section,
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
