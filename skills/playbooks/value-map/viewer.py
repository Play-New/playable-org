#!/usr/bin/env python3
"""
value-map / viewer.py — Render a value-map JSON as an interactive HTML
(with companion static SVG for markdown embedding).

App-pure layout (canvas-first, shared with graph): the SVG Wardley map
is the page (`100vw × 100vh`), with floating editorial chrome on the
*Carta sbiadita* paper — dateline + Analysis CTA + bottom-left stage
legend. Clicking a component slides the Inspect card in from the
right with the component's label, kind, placement, AI effect, and
(for emerging items) the rationale. Decisions live in the Analysis
modal; "show on canvas →" anchors close the modal and focus the
referenced component.

The standalone SVG (--svg) is the secondary artefact for markdown
plays (embedded via `![](data/...svg)`) — labels truncated at ~22
chars to keep the static view readable.

Usage:
    python3 viewer.py --map <chain.json> --html <chain.html> [--svg <chain.svg>]

Internal fields prefixed with `_` (e.g., `_aei`, `_structure_id`) are
consumed by the inspect card but stripped from the visible SVG.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from html import escape
from pathlib import Path

# Shared App-pure shell — palette, body, mobile baseline, chrome
# helpers, modal, favicon, font. The viewer composes on top.
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


# Layout constants
W = 1400
# Bottom pad bumped from 90 to 130 so the two-line stage labels
# (Genesis / new territory) don't run into the "evolution →" hint.
PAD = {"top": 130, "right": 80, "bottom": 130, "left": 110}
MIN_DIST_COMPONENT = 110
MIN_DIST_ANCHOR    = 260
NUDGE_PASSES       = 14
USER_NODE_Y        = 56
LABEL_TRUNCATE     = 22

# Colors — Carta sbiadita palette (v5). SVG-attribute hex values
# mirror the CSS tokens declared by skills/design.py app_pure_css().
# When the palette moves there, copy the hex values across here so
# the static SVG (-svg flag) stays in sync.
FG        = "#1c1a16"          # ink
MUTED     = "rgba(28,26,22,0.6)"   # ink-60 (SVG `fill` accepts rgba)
LINE      = "rgba(28,26,22,0.14)"  # hairline
PAPER     = "#f4eee2"
ACCENT    = "#b87b5e"          # commitment terracotta (emerging marker)
GENESIS   = "#8a9d6b"          # activity sage
CUSTOM    = "#9b8aa3"          # stakeholder lilac
PRODUCT   = "#6b7d8c"          # unit slate
COMMODITY = "#bca787"          # role sand


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


def _normalize_end_users(raw) -> list[str]:
    """Coerce the user-facing end_user field to a list of label strings.

    Three legitimate input shapes:
      - str: a single label, e.g. "Ricercatori finanziati".
      - list[str]: multiple labels.
      - dict {id, label}: a single user with extra metadata; the
        renderer only needs the human-readable label.

    A dict was a real defect-to-test on the first AIRC value-map
    render (2026-05-18): the agent set `end_user = {'id': 'c21',
    'label': '...'}` and the viewer, treating dicts as iterables of
    keys, drew two black disks labelled "id" and "label" at the top
    of the chain. Coercing here makes the bug impossible.
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw] if raw else []
    if isinstance(raw, dict):
        label = raw.get("label") or raw.get("id") or ""
        return [label] if label else []
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            if isinstance(item, str) and item:
                out.append(item)
            elif isinstance(item, dict):
                lab = item.get("label") or item.get("id") or ""
                if lab:
                    out.append(lab)
        return out
    return []


def build_positions(map_data: dict) -> tuple[dict[str, dict], list[str], int]:
    end_users = _normalize_end_users(map_data.get("end_user"))

    anchors = map_data["anchors"]
    components = map_data["components"]
    H = 1100 if len(anchors) + len(components) > 14 else 900
    plot_w = W - PAD["left"] - PAD["right"]
    plot_h = H - PAD["top"] - PAD["bottom"]

    positions: dict[str, dict] = {}

    # End user(s) at the top, evenly spread
    user_ids: list[str] = []
    for i, label in enumerate(end_users):
        uid = f"__user_{i}__"
        x = PAD["left"] + plot_w * (0.5 if len(end_users) == 1 else i / max(1, len(end_users) - 1) * 0.8 + 0.1)
        positions[uid] = {"label": label, "px": x, "py": USER_NODE_Y, "_kind": "user"}
        user_ids.append(uid)

    # New end users — extra circles, coral filled, placed slightly
    # below the existing end-users to avoid collision.
    for j, eu in enumerate(map_data.get("new_end_users") or []):
        label = eu.get("label", "") if isinstance(eu, dict) else str(eu)
        nuid = f"__new_user_{j}__"
        positions[nuid] = {
            "label": label, "px": PAD["left"] + plot_w * (0.78 + 0.05 * j),
            "py": USER_NODE_Y + 26, "_kind": "user", "is_new": True,
            "rationale": eu.get("rationale", "") if isinstance(eu, dict) else "",
        }

    # Anchors — centered horizontally, just below the user nodes.
    anchor_y = USER_NODE_Y + 100
    for i, a in enumerate(anchors):
        x = PAD["left"] + plot_w * (
            0.5 if len(anchors) == 1 else i / max(1, len(anchors) - 1) * 0.8 + 0.1
        )
        positions[a["id"]] = {
            "label": a.get("label", ""),
            "px": x, "py": anchor_y,
            "_kind": "anchor",
            "is_new": bool(a.get("is_new")),
        }

    # Components — positioned by evolution × visibility on the plot.
    for c in components:
        ev = c.get("evolution", 0.5)
        vis = c.get("visibility", 0.5)
        # x: evolution. y: 1-visibility (visibility 1.0 = top, near user).
        px = PAD["left"] + ev * plot_w
        # Visibility band is from anchor_y + 60 down to plot_y1 - 30 to
        # avoid overlapping anchors and the X axis.
        band_top = anchor_y + 60
        band_bot = PAD["top"] + plot_h - 30
        py = band_top + (1 - vis) * (band_bot - band_top)
        positions[c["id"]] = {
            "label": c.get("label", ""),
            "px": px, "py": py,
            "_kind": c.get("_kind", ""),
            "is_new": bool(c.get("is_new")),
        }

    # Anti-overlap nudge passes — push components apart if they're closer
    # than MIN_DIST_COMPONENT, push anchors apart MIN_DIST_ANCHOR.
    for _ in range(NUDGE_PASSES):
        ids = list(positions.keys())
        for i in range(len(ids)):
            a = positions[ids[i]]
            for j in range(i + 1, len(ids)):
                b = positions[ids[j]]
                dx = b["px"] - a["px"]
                dy = b["py"] - a["py"]
                d = math.hypot(dx, dy) or 1
                ka = a.get("_kind") == "anchor"
                kb = b.get("_kind") == "anchor"
                ua = a.get("_kind") == "user"
                ub = b.get("_kind") == "user"
                if ua or ub:
                    continue  # users stay put at the top
                min_d = MIN_DIST_ANCHOR if (ka or kb) else MIN_DIST_COMPONENT
                if d < min_d:
                    push = (min_d - d) / 2
                    ux, uy = dx / d, dy / d
                    # Don't move users or anchors via this pass either.
                    if not ka:
                        a["px"] -= ux * push * 0.5
                        a["py"] -= uy * push * 0.5
                    if not kb:
                        b["px"] += ux * push * 0.5
                        b["py"] += uy * push * 0.5

    return positions, user_ids, H


def arc_path(x1: float, y1: float, x2: float, y2: float) -> str:
    """Quadratic bezier with a small bow so parallel edges separate."""
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy) or 1
    nx = -dy / length
    ny = dx / length
    bow = min(40, length * 0.08)
    cx = mx + nx * bow
    cy = my + ny * bow
    return f"M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}"


def render_svg_inner(map_data: dict, interactive: bool) -> tuple[str, int]:
    positions, user_ids, H = build_positions(map_data)
    plot_w = W - PAD["left"] - PAD["right"]
    plot_h = H - PAD["top"] - PAD["bottom"]
    plot_x0 = PAD["left"]
    plot_y0 = PAD["top"]
    plot_x1 = PAD["left"] + plot_w
    plot_y1 = PAD["top"] + plot_h

    parts: list[str] = []

    # Plot axes — only the left (Y) and bottom (X) edges, no full rectangle.
    parts.append(
        f'<line x1="{plot_x0}" y1="{plot_y0}" x2="{plot_x0}" y2="{plot_y1}" '
        f'stroke="{LINE}" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{plot_x0}" y1="{plot_y1}" x2="{plot_x1}" y2="{plot_y1}" '
        f'stroke="{LINE}" stroke-width="1"/>'
    )

    # Stage divisions — tiny tick marks on the X axis at the boundaries
    band_x = lambda ev: plot_x0 + ev * plot_w
    for boundary in (0.17, 0.40, 0.70):
        x = band_x(boundary)
        parts.append(
            f'<line x1="{x:.1f}" y1="{plot_y1 - 6:.1f}" x2="{x:.1f}" y2="{plot_y1 + 6:.1f}" '
            f'stroke="{LINE}" stroke-width="1"/>'
        )

    # X axis stage labels — bigger now so they read at a glance.
    # Plain-language second line ("new territory" / "built in-house"
    # / "buyable" / "market standard") explains each stage in chiaro.
    stages = [
        ("Genesis", "new territory", 0.085),
        ("Custom", "built in-house", 0.285),
        ("Product", "buyable", 0.55),
        ("Commodity", "market standard", 0.85),
    ]
    for label, sub, x_frac in stages:
        x = plot_x0 + x_frac * plot_w
        parts.append(
            f'<text x="{x:.1f}" y="{plot_y1 + 34}" text-anchor="middle" '
            f'font-size="19" fill="{FG}" font-weight="540" letter-spacing="-0.012em">{escape(label)}</text>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{plot_y1 + 56}" text-anchor="middle" '
            f'font-size="14" fill="{MUTED}" font-style="italic">{escape(sub)}</text>'
        )
    parts.append(
        f'<text x="{(plot_x0 + plot_x1) / 2:.1f}" y="{H - 14}" text-anchor="middle" '
        f'font-size="14" fill="{MUTED}" font-style="italic">evolution →</text>'
    )

    # Y axis labels — split into two separate strings, top and bottom
    # of the axis, so the reading is "visible up here, invisible down
    # there" rather than one rotated phrase to parse. Anchored at the
    # axis line (end-aligned just to its left) and short enough to fit
    # within the left margin of the viewBox at any viewport width.
    parts.append(
        f'<text x="{plot_x0 - 10:.1f}" y="{plot_y0 - 6:.1f}" text-anchor="end" '
        f'font-size="14" fill="{FG}" font-weight="540" letter-spacing="-0.008em">visible ↑</text>'
    )
    parts.append(
        f'<text x="{plot_x0 - 10:.1f}" y="{plot_y1 + 18:.1f}" text-anchor="end" '
        f'font-size="14" fill="{MUTED}" font-style="italic">↓ invisible</text>'
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
    end_users = _normalize_end_users(map_data.get("end_user"))
    components = map_data.get("components") or []
    anchors = map_data.get("anchors") or []

    # Implicit user → anchor edges
    new_user_ids = [f"__new_user_{j}__" for j in range(len(map_data.get("new_end_users") or []))]
    for uid in list(user_ids) + new_user_ids:
        for a in anchors:
            edges.append({"from": uid, "to": a["id"], "_implicit": True})

    # Implicit anchor → top-level-component edges
    unit_ids = [c["id"] for c in components if c.get("_kind") == "unit"]
    if not unit_ids:
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

    on_click = ' onclick="pnNodeClick(this)"' if interactive else ""
    cursor = ' style="cursor:pointer"' if interactive else ""

    # End-user nodes
    for uid in user_ids:
        p = positions[uid]
        parts.append(
            f'<g class="node node-user" data-node-id="{uid}"{on_click}{cursor}>'
            f'<title>{escape(p["label"])}</title>'
            f'<circle cx="{p["px"]:.1f}" cy="{p["py"]:.1f}" r="16" fill="{FG}"/>'
            f'<text x="{p["px"]:.1f}" y="{p["py"] - 28:.1f}" text-anchor="middle" '
            f'font-size="16" fill="{FG}" font-weight="540" letter-spacing="-0.012em">{escape(truncate(p["label"]))}</text>'
            f'</g>'
        )

    # New end users
    for j, _ in enumerate(map_data.get("new_end_users") or []):
        p = positions.get(f"__new_user_{j}__")
        if not p:
            continue
        parts.append(
            f'<g class="node node-user node-new" data-node-id="__new_user_{j}__"{on_click}{cursor}>'
            f'<title>{escape(p["label"])}</title>'
            f'<circle cx="{p["px"]:.1f}" cy="{p["py"]:.1f}" r="16" fill="{ACCENT}"/>'
            f'<text x="{p["px"]:.1f}" y="{p["py"] - 28:.1f}" text-anchor="middle" '
            f'font-size="16" fill="{ACCENT}" font-weight="540" letter-spacing="-0.012em">{escape(truncate(p["label"]))} ★</text>'
            f'</g>'
        )

    # Anchors (diamonds) — larger so they read at a distance.
    for a in map_data["anchors"]:
        p = positions[a["id"]]
        cx, cy = p["px"], p["py"]
        size = 16
        diamond = f"{cx},{cy - size} {cx + size},{cy} {cx},{cy + size} {cx - size},{cy}"
        fill = ACCENT if p["is_new"] else PAPER
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
        label_y = cy + size + 20
        parts.append(
            f'<g class="node node-anchor" data-node-id="{a["id"]}"{on_click}{cursor}>'
            f'<title>{escape(a.get("label", ""))}</title>'
            f'<polygon points="{diamond}" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
            f'{et_arrow}'
            f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            f'font-size="14" fill="{FG}" font-weight="540" letter-spacing="-0.012em">{escape(truncate(p["label"], 26))}</text>'
            f'</g>'
        )

    # Components — circles. Stage colour as fill, ACCENT for emerging.
    # Larger radius (10 from 7) so the swatches read at typical
    # screen distance and don't disappear against the labels.
    for c in map_data["components"]:
        p = positions[c["id"]]
        cx, cy = p["px"], p["py"]
        r = 10
        fill = ACCENT if p["is_new"] else stage_color(c.get("evolution", 0.5))
        stroke = ACCENT if p["is_new"] else FG
        shape = (
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
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
        label = truncate(p["label"], 44)
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
            text_lines += f'<tspan x="{cx:.1f}" dy="18">{escape(line2)}</tspan>'
        is_new_class = " node-new" if p["is_new"] else ""
        parts.append(
            f'<g class="node node-component{is_new_class}" data-node-id="{c["id"]}"{on_click}{cursor}>'
            f'<title>{escape(c.get("label", ""))}</title>'
            f'{shape}'
            f'{et_arrow}'
            f'<text x="{cx:.1f}" y="{cy + r + 18:.1f}" text-anchor="middle" '
            f'font-size="14" fill="{FG}" font-weight="460" letter-spacing="-0.008em">{text_lines}</text>'
            f'</g>'
        )

    inner = "\n".join(parts)
    return inner, H


def render_svg_standalone(map_data: dict) -> str:
    """Static SVG for markdown embedding. Same content, no `onclick`,
    no JS — just a portable image."""
    inner, H = render_svg_inner(map_data, interactive=False)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="100%" style="font-family: \'Inter\', system-ui, sans-serif; background: {PAPER};">\n'
        f'{inner}\n</svg>'
    )


# ----------------------------------------------------------------------
# Value-map-specific CSS — composes on top of design.app_pure_css(layout="canvas").
# Only the bits that don't generalise to the other viewers live here:
# the SVG full-bleed positioning, the node hover affordance, the bottom
# stages legend, and the inspect "placement" copy.
# ----------------------------------------------------------------------
EXTRA_CSS = r"""
/* Map SVG: positioned to leave room for the floating chrome — the
   dateline + Analysis CTA take ~62px at the top; the symbol key takes
   ~70px at the bottom; the Y axis labels need ~80px on the left. The
   SVG uses preserveAspectRatio="xMidYMid meet" inside, so the viewBox
   scales without distortion within whatever space is allocated. */
.map-wrap {
  position: fixed;
  top: max(62px, calc(env(safe-area-inset-top) + 56px));
  bottom: max(70px, calc(env(safe-area-inset-bottom) + 60px));
  left: max(20px, env(safe-area-inset-left));
  right: max(20px, env(safe-area-inset-right));
  z-index: 1;
}
.map-wrap svg {
  width: 100%;
  height: 100%;
  display: block;
}
.map-wrap svg .node { cursor: pointer; }
.map-wrap svg .node:hover circle,
.map-wrap svg .node:hover polygon { stroke-width: 2.2; }
.map-wrap svg .node.focused circle,
.map-wrap svg .node.focused polygon { stroke: var(--ink); stroke-width: 2.4; }

/* Symbol key — the system that distinguishes the four element types
   on the map. Bottom-centered, paper-coloured, hairline border. The
   X-axis labels Genesis/Custom/Product/Commodity are inside the SVG. */
.map-key {
  position: fixed;
  bottom: max(20px, calc(env(safe-area-inset-bottom) + 16px));
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  display: flex; flex-wrap: nowrap; align-items: center;
  gap: 22px;
  padding: 10px 18px;
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  font-size: 13px;
  color: var(--ink-80);
  letter-spacing: -0.005em;
  white-space: nowrap;
  pointer-events: none;
  max-width: calc(100vw - 32px);
  overflow-x: auto;
  scrollbar-width: none;
}
.map-key::-webkit-scrollbar { display: none; }
.map-key .key {
  display: inline-flex; align-items: center; gap: 8px;
  font-style: italic;
  color: var(--ink-40);
}
.map-key .key em {
  font-style: normal;
  color: var(--ink-80);
  font-weight: 460;
}
.map-key .glyph {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px;
}
.map-key .glyph.stakeholder { background: var(--ink); border-radius: 50%; width: 12px; height: 12px; }
.map-key .glyph.value {
  width: 14px; height: 14px;
  background: var(--paper);
  border: 1.5px solid var(--ink);
  transform: rotate(45deg);
}
.map-key .glyph.node {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--paper);
  border: 1.2px solid var(--ink);
}
.map-key .glyph.new {
  width: 12px; height: 12px;
  border-radius: 50%;
}
.map-key .glyph.arrow svg { width: 26px; height: 10px; }
@media (max-width: 900px) {
  .map-wrap {
    top: max(54px, calc(env(safe-area-inset-top) + 50px));
    bottom: max(110px, calc(env(safe-area-inset-bottom) + 100px));
    left: 8px; right: 8px;
  }
}
.map-key .key small {
  font-size: inherit;
  font-style: italic;
  color: var(--ink-25);
  margin-left: 2px;
}
@media (max-width: 760px) {
  .map-key {
    flex-wrap: wrap;
    justify-content: center;
    overflow-x: visible;
    gap: 6px 14px;
    padding: 8px 14px;
    font-size: 12px;
    border-radius: 14px;
    max-width: calc(100vw - 24px);
  }
  /* Drop the secondary phrase on phones — keep only the glyph + main label. */
  .map-key small { display: none; }
}

/* Inspect "placement" copy — italic, ink-60. Used inside the inspect
   card body for the genesis/custom/product/commodity description. */
.inspect .placement {
  font-style: italic;
  color: var(--ink-60);
  font-size: 12.5px;
  margin: 0 0 8px;
  line-height: 1.5;
}
.inspect .placement em { font-style: normal; color: var(--ink-80); }
.inspect .ai-effect {
  font-size: 13px;
  color: var(--ink-95);
  line-height: 1.55;
  margin: 0 0 10px;
}
.inspect .emerging-why {
  margin-top: 12px;
  padding: 10px 12px;
  background: var(--paper-2);
  border-left: 2px solid {ACCENT_COLOR};
  border-radius: 3px;
}
.inspect .emerging-why-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: {ACCENT_COLOR};
  margin-bottom: 4px;
}
.inspect .emerging-why p {
  font-size: 12.5px;
  line-height: 1.5;
  margin: 0;
}

@media (max-width: 760px) {
  .stages { gap: 6px 6px; max-width: 60vw; }
  .stage-pill { padding: 7px 11px; font-size: 11.5px; }
}
""".replace("{ACCENT_COLOR}", ACCENT)


# ----------------------------------------------------------------------
# Value-map-specific JavaScript. Modal open/close + ?focus permalink
# come from app_pure_baseline_js. window.setFocus opens the inspect
# card with the component's content; the shared baseline calls it for
# anchors and ?focus.
# ----------------------------------------------------------------------
JS_TEMPLATE = r"""
(() => {
  const NODES = JSON.parse(document.getElementById('nodes-data').textContent);
  const S = JSON.parse(document.getElementById('strings-data').textContent);
  const inspect = document.getElementById('inspect');
  const inspectBody = document.getElementById('inspect-body');
  const STAGE_COLORS = {
    genesis: 'GENESIS_HEX', custom: 'CUSTOM_HEX',
    product: 'PRODUCT_HEX', commodity: 'COMMODITY_HEX'
  };
  const STAGE_PLAIN = {
    genesis:   S.stage_genesis,
    custom:    S.stage_custom,
    product:   S.stage_product,
    commodity: S.stage_commodity,
  };
  function stageFor(ev) {
    if (ev < 0.17) return 'genesis';
    if (ev < 0.40) return 'custom';
    if (ev < 0.70) return 'product';
    return 'commodity';
  }
  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    })[c]);
  }
  function kindLabel(node) {
    if (node.is_new) return S.kind_emerging;
    if (node._kind === 'anchor') return S.kind_anchor;
    if (node._kind === 'user') return S.kind_user;
    if (node._kind === 'unit') return S.kind_unit;
    if (node._kind === 'activity') return S.kind_activity;
    if (node._kind === 'stakeholder') return S.kind_stakeholder;
    return S.kind_generic;
  }
  function kindSwatch(node) {
    if (node.is_new) return 'ACCENT_HEX';
    const ev = node.evolution;
    if (ev != null) return STAGE_COLORS[stageFor(ev)];
    if (node._kind === 'user') return 'INK_HEX';
    return 'INK_HEX';
  }

  function renderInspectFor(id) {
    const node = NODES[id];
    if (!node) { inspect.classList.remove('open'); return; }
    inspect.classList.add('open');
    const isUser = node._kind === 'user';
    const stage = node.evolution != null ? stageFor(node.evolution) : null;
    const swatch = kindSwatch(node);

    let html = `<div class="kind-tag" style="--tagcolor:${swatch}"><span class="swatch"></span><span>${escapeHtml(kindLabel(node))}</span></div>`;
    html += `<h2>${escapeHtml(node.label || id)}</h2>`;
    // Description: pre-rendered HTML from inline_md() at build time.
    // innerHTML is safe because the source markdown was escaped before
    // the inline forms were applied; internal links resolve to focus
    // anchors that re-focus the canvas on click.
    if (node.blurb_html) {
      html += `<div class="blurb">${node.blurb_html}</div>`;
    }
    if (!isUser && node.evolution != null) {
      const visText = node.visibility != null
        ? (node.visibility >= 0.7 ? ' ' + S.visibility_high
           : node.visibility >= 0.4 ? ' ' + S.visibility_mid
           : ' ' + S.visibility_low)
        : '';
      html += `<p class="placement">${STAGE_PLAIN[stage]}${visText}</p>`;
    }
    if (node.evolution_target != null && !node.is_new) {
      html += `<p class="placement">${S.evolution_target_lead} <em>${STAGE_PLAIN[stageFor(node.evolution_target)]}</em></p>`;
    }
    if (node.ai_effect && !node.is_new) {
      const aiKey = 'ai_effect_' + node.ai_effect;
      const aiPhrase = S[aiKey] || node.ai_effect;
      html += `<p class="ai-effect"><em>${S.ai_effect_lead}</em> ${escapeHtml(aiPhrase)}</p>`;
    }
    if (node.is_new) {
      const why = node.ai_effect || node.rationale;
      if (why) {
        html += `<div class="emerging-why"><div class="emerging-why-label">${S.emerging_label}</div><p>${escapeHtml(why)}</p></div>`;
      } else {
        html += `<p class="placement">${S.emerging_default}</p>`;
      }
    }
    inspectBody.innerHTML = html;
    // Wire focus anchors inside the rendered blurb. Same shape as the
    // Analysis modal anchors (graph viewer pattern).
    inspectBody.querySelectorAll('.anchor[data-focus]').forEach(a => {
      a.addEventListener('click', (ev) => {
        ev.preventDefault();
        const tid = a.dataset.focus;
        if (tid && NODES[tid]) {
          if (typeof window.setFocus === 'function') window.setFocus(tid);
          else renderInspectFor(tid);
        }
      });
    });

    // Highlight the focused node in the SVG.
    document.querySelectorAll('.map-wrap g.node').forEach(g => g.classList.toggle('focused', g.dataset.nodeId === id));
  }

  // Click / tap a node anywhere in the SVG.
  window.pnNodeClick = function(el) {
    const id = el.dataset && el.dataset.nodeId;
    if (id) renderInspectFor(id);
  };

  // Belt-and-suspenders: a document-level click listener in case inline
  // onclick is stripped by some sanitizer.
  document.addEventListener('click', function(e) {
    let g = e.target;
    while (g && !(g.classList && g.classList.contains('node'))) g = g.parentNode;
    if (g && g.dataset && g.dataset.nodeId) {
      renderInspectFor(g.dataset.nodeId);
    }
  }, true);

  // Inspect close button + Esc clear focus (modal Esc handled by baseline).
  document.getElementById('inspect-close').addEventListener('click', () => {
    inspect.classList.remove('open');
    document.querySelectorAll('.map-wrap g.node.focused').forEach(g => g.classList.remove('focused'));
  });
  window.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Escape') return;
    const scrim = document.getElementById('modal-scrim');
    if (scrim && scrim.classList.contains('open')) return;  // baseline handled it
    inspect.classList.remove('open');
    document.querySelectorAll('.map-wrap g.node.focused').forEach(g => g.classList.remove('focused'));
  });

  // Expose for the shared modal's "show on canvas →" anchors and ?focus permalink.
  window.setFocus = function(id) { if (id) renderInspectFor(id); };
})();
""".replace("GENESIS_HEX", GENESIS).replace("CUSTOM_HEX", CUSTOM).replace("PRODUCT_HEX", PRODUCT).replace("COMMODITY_HEX", COMMODITY).replace("ACCENT_HEX", ACCENT).replace("INK_HEX", FG)


# ----------------------------------------------------------------------
# HTML template
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

<div class="map-wrap">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" style="font-family: 'Inter', system-ui, sans-serif;">
{svg_inner}
  </svg>
</div>

<!-- Symbol key (bottom-center). Four element types on the map plus
     the AI-pressure arrow. Stages (genesis / custom / product /
     commodity) are labelled inside the SVG along the X axis. -->
<div class="map-key">
  <span class="key"><span class="glyph stakeholder"></span> <em>stakeholder</em></span>
  <span class="key"><span class="glyph value"></span> <em>value</em><small> (user need)</small></span>
  <span class="key"><span class="glyph node"></span> <em>node</em><small> (part of the chain)</small></span>
  <span class="key"><span class="glyph new" style="background:{ACCENT}"></span> <em>new</em><small> / emerging</small></span>
  <span class="key"><span class="glyph arrow"><svg viewBox="0 0 26 10"><line x1="0" y1="5" x2="22" y2="5" stroke="{ACCENT}" stroke-width="1.5" stroke-dasharray="3,3"/><path d="M18,1 L22,5 L18,9" stroke="{ACCENT}" stroke-width="1.5" fill="none"/></svg></span> <em>where AI is pushing</em></span>
</div>

{inspect_aside}

{modal_html}

<script type="application/json" id="nodes-data">{nodes_json}</script>
<script type="application/json" id="strings-data">{strings_json}</script>
<script>
{baseline_js}
{js}
</script>
</body>
</html>
"""


# ----------------------------------------------------------------------
# Adapter — pull every clickable node from the map JSON into a flat
# {id: node-data} object the JS can index.
# ----------------------------------------------------------------------
def _build_nodes_index(map_data: dict) -> dict[str, dict]:
    """Build the per-node lookup that powers the inspect panel.

    Two things happen here that didn't before:
    - Descriptions are pre-rendered to safe HTML via `inline_md`. The
      panel's JS sets innerHTML on the rendered string, so internal
      `[label](node-id)` markdown links become focus anchors that
      re-focus the canvas. Both `_description` (build-time) and any
      agent-authored `description` are routed through the same helper.
    - The link resolver knows both value-map component ids (c1, c2)
      and the underlying org-side node ids (peer-review, ...) so the
      agent can write whichever feels natural.
    """
    components = map_data.get("components") or []
    component_ids = {c["id"] for c in components}
    structure_to_component: dict[str, str] = {
        c["_structure_id"]: c["id"] for c in components if c.get("_structure_id")
    }

    def _resolver(target: str) -> str | None:
        if target in component_ids:
            return target
        if target in structure_to_component:
            return structure_to_component[target]
        return None

    def _render_blurb(raw: str) -> str:
        if not raw:
            return ""
        return "".join(
            f"<p>{inline_md(p, link_resolver=_resolver)}</p>"
            for p in raw.split("\n\n") if p.strip()
        )

    index: dict[str, dict] = {}
    end_users = _normalize_end_users(map_data.get("end_user"))
    for i, label in enumerate(end_users):
        uid = f"__user_{i}__"
        index[uid] = {"id": uid, "_kind": "user", "label": label}
    for j, eu in enumerate(map_data.get("new_end_users") or []):
        nuid = f"__new_user_{j}__"
        index[nuid] = {
            "id": nuid, "_kind": "user", "is_new": True,
            "label": eu.get("label", "") if isinstance(eu, dict) else str(eu),
            "rationale": eu.get("rationale", "") if isinstance(eu, dict) else "",
        }
    for a in map_data.get("anchors") or []:
        node = {**a, "_kind": "anchor"}
        raw = a.get("rationale") or a.get("description") or ""
        if raw:
            node["blurb_html"] = _render_blurb(raw)
        index[a["id"]] = node
    for c in components:
        node = dict(c)
        raw = c.get("description") or c.get("_description") or c.get("rationale") or ""
        if raw:
            node["blurb_html"] = _render_blurb(raw)
        index[c["id"]] = node
    return index


def _build_modal_html(map_data: dict, org_name: str, dated: str, *, S: dict) -> str:
    decisions = map_data.get("decisions") or []
    if not decisions:
        return ""
    nodes_idx = _build_nodes_index(map_data)
    node_ids_set = set(nodes_idx.keys())
    # Reverse lookup org-side node id → value-map component id. Lets
    # the agent write `[peer-review](peer-review)` and have the link
    # focus the corresponding component on the canvas, instead of
    # falling through to a plain blue href because `peer-review` is
    # the org id, not the component id `c1`.
    structure_to_component: dict[str, str] = {}
    for c in map_data.get("components") or []:
        sid = c.get("_structure_id")
        if sid:
            structure_to_component[sid] = c.get("id", "")

    def _link_resolver(target: str) -> str | None:
        if target in node_ids_set:
            return target
        if target in structure_to_component:
            return structure_to_component[target]
        return None

    items = []
    for dec in decisions:
        question = (dec.get("question") or "").strip()
        answer_paragraphs = [
            p.strip() for p in (dec.get("answer") or "").split("\n\n") if p.strip()
        ]
        # Per-decision list. Renamed from the corpus-wide `node_ids`
        # used by the link_resolver closure (graph viewer pattern).
        dec_node_ids = dec.get("node_ids") or []
        anchor_html = ""
        if dec_node_ids:
            first = dec_node_ids[0]
            label = (nodes_idx.get(first) or {}).get("label") or first
            anchor_html = (
                f'<span class="anchor" data-focus="{escape(first)}">'
                f'{S["show_on_map"].format(label=escape(label))}'
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
    n = len(decisions)
    if n == 1:
        default_headline = S["headline_one"]
    else:
        default_headline = S["headline_n"].format(n=n)
    headline = map_data.get("_headline") or default_headline
    lede_text = map_data.get("_lede") or ""
    return app_pure_modal_html(
        headline=headline,
        org_name=org_name,
        dated=dated,
        decisions_html="".join(items),
        kicker=S["analysis_kicker"],
        lede=escape(lede_text) if lede_text else "",
    )


# ----------------------------------------------------------------------
# Localized UI strings — same pattern as graph and ai-exposure.
# Decisions, source citations, and any prose written by the agent stay
# in whatever language the agent wrote them; this dict is for the
# chrome + About modal scaffolding only.
# ----------------------------------------------------------------------
STRINGS = {
    "en": {
        "analysis_btn": "Analysis",
        "help_btn_label": "What is this map?",
        "analysis_kicker": "Reading the chain",
        "show_on_map": "show <em>{label}</em> on the map →",
        "headline_n": "{n} decisions surface from the value map.",
        "headline_one": "1 decision surfaces from the value map.",
        "what_anchored": "the chain anchored on <em>{label}</em>",
        "what_generic": "the chain",
        "default_org": "Value map",
        "about_lede": (
            "A read of the chain that fulfills this user need. "
            "Every component placed by how mature it is and how visible "
            "it is to the user, with the direction AI is pushing it."
        ),
        # Inspect panel — kind labels
        "kind_anchor": "User need",
        "kind_user": "End user",
        "kind_unit": "Unit",
        "kind_activity": "Activity",
        "kind_stakeholder": "External stakeholder",
        "kind_emerging": "New / emerging",
        "kind_generic": "Part of the chain",
        # Inspect panel — stage explanations
        "stage_genesis": "New territory. Nobody knows yet how to do this well.",
        "stage_custom": "Built in-house. Every shop figures it out their own way.",
        "stage_product": "Common practice. Vendors and patterns exist, you can buy it.",
        "stage_commodity": "Market standard. Indistinguishable across providers.",
        # Inspect panel — visibility hints
        "visibility_high": "Visible to the user.",
        "visibility_mid": "Mid-chain.",
        "visibility_low": "Behind the scenes.",
        # Inspect panel — AI effect + emerging
        "ai_effect_lead": "Where AI sits today:",
        "ai_effect_automated": "Claude reliably worked alone on tasks like this in the public sample.",
        "ai_effect_augmented": "Claude and a human worked together on tasks like this in the public sample.",
        "ai_effect_assistive": "Claude helped on tasks like this; the human stayed in the lead.",
        "evolution_target_lead": "Heading toward:",
        "emerging_label": "Why it's on the map",
        "emerging_default": "Emerging. Does not exist today as such.",
        # Inspect panel — chrome
        "inspect_eyebrow": "Inspect",
        "inspect_close_title": "Reset focus",
    },
    "it": {
        "analysis_btn": "Analisi",
        "help_btn_label": "Cos'è questa mappa?",
        "analysis_kicker": "Lettura della catena del valore",
        "show_on_map": "mostra <em>{label}</em> sulla mappa →",
        "headline_n": "{n} decisioni emergono dalla mappa del valore.",
        "headline_one": "1 decisione emerge dalla mappa del valore.",
        "what_anchored": "la catena ancorata su <em>{label}</em>",
        "what_generic": "la catena",
        "default_org": "Mappa del valore",
        "about_lede": (
            "Una lettura della catena che soddisfa questo bisogno utente. "
            "Ogni componente è posizionato per quanto è maturo e per quanto è "
            "visibile all'utente, con la direzione verso cui l'AI lo sta spingendo."
        ),
        # Inspect panel — kind labels
        "kind_anchor": "Bisogno utente",
        "kind_user": "Utente",
        "kind_unit": "Unità",
        "kind_activity": "Attività",
        "kind_stakeholder": "Stakeholder esterno",
        "kind_emerging": "Nuovo / emergente",
        "kind_generic": "Parte della catena",
        # Inspect panel — stage explanations
        "stage_genesis": "Territorio nuovo. Nessuno sa ancora come si fa bene.",
        "stage_custom": "Costruito in casa. Ognuno lo inventa a modo suo.",
        "stage_product": "Pratica diffusa. Fornitori e pattern esistono, si può comprare.",
        "stage_commodity": "Standard di mercato. Indistinguibile fra fornitori.",
        # Inspect panel — visibility hints
        "visibility_high": "Visibile all'utente.",
        "visibility_mid": "A metà catena.",
        "visibility_low": "Dietro le quinte.",
        # Inspect panel — AI effect + emerging
        "ai_effect_lead": "Dove sta l'AI oggi:",
        "ai_effect_automated": "Nel campione pubblico Claude ha lavorato in autonomia su mansioni simili.",
        "ai_effect_augmented": "Nel campione pubblico Claude e una persona hanno lavorato insieme su mansioni simili.",
        "ai_effect_assistive": "Nel campione pubblico Claude ha dato una mano; la persona è rimasta in guida.",
        "evolution_target_lead": "Sta scivolando verso:",
        "emerging_label": "Perché è sulla mappa",
        "emerging_default": "Emergente. Oggi non esiste in questa forma.",
        # Inspect panel — chrome
        "inspect_eyebrow": "Ispeziona",
        "inspect_close_title": "Reimposta focus",
    },
}


def _build_about_body(lang: str) -> str:
    """About-modal body for the value-map viewer. Hand-written for each
    language. No em dashes, no 'X, non Y' rhetorical formulas (STYLE.md
    bans both in user-visible prose)."""
    if lang == "it":
        return """
  <p>La figura qui sopra è una <strong>mappa del valore</strong> della catena che soddisfa un bisogno utente. Si legge dall'alto verso il basso: in cima sta l'utente, sotto i pezzi della catena che gli consegnano valore.</p>

  <h2>I quattro stadi di evoluzione</h2>
  <p><strong>Genesis, territorio nuovo.</strong> Nessuno sa ancora come si fa bene. Ogni organizzazione lo inventa da zero, il lavoro è esplorativo, il costo di sbagliare è soprattutto tempo di ricerca.</p>
  <p><strong>Custom, costruito in casa.</strong> Ognuno fa la sua versione. La competenza esiste, ma è artigianato: ogni implementazione è su misura, richiede una persona senior, e non è riusabile altrove.</p>
  <p><strong>Prodotto, comprabile.</strong> Esistono pattern e fornitori. Si può assumere chi l'ha già fatto, oppure comprarlo come prodotto. Le diverse organizzazioni producono output comparabili.</p>
  <p><strong>Commodity, standard di mercato.</strong> Indistinguibile fra fornitori. Il valore di farlo in casa è sceso quasi a zero; la mossa razionale è comprare la versione più economica e affidabile.</p>
  <p>Nel tempo ogni componente scivola verso destra. Quello che era custom ieri diventa prodotto oggi; quello che è prodotto oggi diventa standard di mercato domani. La mappa dice dove ogni componente sta <em>ora</em>, e una freccia tratteggiata coral segnala dove l'AI lo sta spingendo.</p>

  <h2>I simboli</h2>
  <p><strong>● Stakeholder</strong>: le persone che la catena serve in ultima istanza (disco pieno nero in cima).</p>
  <p><strong>◇ Valore (bisogno utente)</strong>: la promessa che la catena deve consegnare, espressa come bisogno (rombo vuoto).</p>
  <p><strong>○ Nodo (pezzo della catena)</strong>: un componente che contribuisce a consegnare il valore (cerchio vuoto, colorato per stadio).</p>
  <p><strong>● Nuovo / emergente</strong>: un pezzo che non esiste ancora in questa forma; nominato in voce condizionale (pieno terracotta).</p>
  <p><strong>--→ Dove l'AI sta spingendo</strong>: una freccia tratteggiata coral su un componente indica la direzione della pressione: verso destra significa "diventa più standardizzato, più in fretta".</p>

  <h2>Cosa vuol dire l'asse verticale</h2>
  <p>L'asse verticale è la <strong>visibilità</strong>: i componenti in alto sono visibili all'utente (modellano direttamente la sua esperienza); quelli in basso sono infrastruttura invisibile (necessari, ma l'utente non li vede mai).</p>

  <h2>Da dove viene</h2>
  <p>Il framework è di Simon Wardley, dalla sua pratica di value-mapping. Click su qualunque componente per la motivazione del posizionamento e le citazioni alle fonti.</p>
"""
    return """
  <p>The picture above is a <strong>value-mapping</strong> of the chain that fulfills one user need. Read it bottom-up: the user sits at the top, the parts of the chain that deliver value sit below.</p>

  <h2>The four evolution stages</h2>
  <p><strong>Genesis, new territory.</strong> Nobody knows yet how to do this well. Each shop figures it out from scratch, the work is exploratory, and the cost of getting it wrong is mostly research time.</p>
  <p><strong>Custom, built in-house.</strong> Every shop builds its own version. The skill exists, but it's craft: each implementation is bespoke, takes a senior person, and isn't reusable across organisations.</p>
  <p><strong>Product, buyable.</strong> Patterns and vendors exist. You can hire someone who's done it before, or you can purchase it as a product. Different shops produce roughly comparable outputs.</p>
  <p><strong>Commodity, market standard.</strong> Indistinguishable across providers. The value of doing it in-house has dropped to near zero; the rational move is to buy the cheapest reliable version.</p>
  <p>Over time, every component drifts rightward. What was custom yesterday becomes a product today, and what was a product today becomes market-standard tomorrow. The map says where each component sits <em>now</em>, and a dashed coral arrow marks where AI is pushing it.</p>

  <h2>The visual system</h2>
  <p><strong>● Stakeholder</strong>: the people the chain ultimately serves (filled black disk at the top).</p>
  <p><strong>◇ Value (user need)</strong>: the promise the chain has to deliver, stated as a need (outline diamond).</p>
  <p><strong>○ Node (part of the chain)</strong>: a piece of the chain that contributes to delivering the value (outline circle, coloured by stage).</p>
  <p><strong>● New / emerging</strong>: a piece that doesn't yet exist as such; named in conditional voice (terracotta fill).</p>
  <p><strong>--→ Where AI is pushing</strong>: a dashed coral arrow on a component shows the direction of pressure: rightward means "becoming standardised, faster".</p>

  <h2>What the Y axis means</h2>
  <p>The vertical axis is <strong>visibility</strong>: components at the top are visible to the user (they shape what the user actually experiences); components at the bottom are invisible plumbing (necessary, but the user never sees them).</p>

  <h2>Where it comes from</h2>
  <p>The framework is from Simon Wardley's value-mapping practice. Click any component for its placement rationale and the cited evidence behind it.</p>
"""


# ----------------------------------------------------------------------
# render_html
# ----------------------------------------------------------------------
def render_html(map_data: dict, *, org_name: str = "", lang: str = "en") -> str:
    S = STRINGS.get(lang, STRINGS["en"])
    inner, H = render_svg_inner(map_data, interactive=True)
    anchor = map_data.get("_anchor") or {}
    anchor_label = anchor.get("title") or anchor.get("label") or anchor.get("id") or ""
    # The dateline org slot. Falls back to JSON `_org` if the caller
    # didn't pass --org-name. Generic "Value map" as last resort so
    # the chrome never collapses.
    if not org_name:
        org_name = map_data.get("_org") or S["default_org"]
    # Fallback to today's date so the chrome never renders the literal
    # em dash placeholder STYLE.md bans.
    from datetime import date as _date
    dated = map_data.get("_dated") or _date.today().isoformat()
    nodes_index = _build_nodes_index(map_data)
    nodes_json = json.dumps(nodes_index, ensure_ascii=False).replace("</", "<\\/")
    # Ship only the keys JS actually reads. Python-side keys with
    # `.format()` placeholders (show_on_map, what_anchored, headline_*,
    # about_*) stay in Python; they'd otherwise leak into the JSON as
    # `{label}` and trip the orphan-placeholder regression test.
    JS_STRING_KEYS = {
        "kind_anchor", "kind_user", "kind_unit", "kind_activity",
        "kind_stakeholder", "kind_emerging", "kind_generic",
        "stage_genesis", "stage_custom", "stage_product", "stage_commodity",
        "visibility_high", "visibility_mid", "visibility_low",
        "ai_effect_lead", "ai_effect_automated", "ai_effect_augmented",
        "ai_effect_assistive",
        "evolution_target_lead", "emerging_label", "emerging_default",
    }
    js_strings = {k: v for k, v in S.items() if k in JS_STRING_KEYS}
    strings_json = json.dumps(js_strings, ensure_ascii=False).replace("</", "<\\/")
    modal_html = _build_modal_html(map_data, org_name, dated, S=S)
    has_decisions = bool(map_data.get("decisions"))

    title = f"value-map · {anchor_label}" if anchor_label else "value-map"
    what_html = (
        S["what_anchored"].format(label=escape(anchor_label))
        if anchor_label
        else S["what_generic"]
    )

    # About modal — plain-language explanation of the four stages and
    # the visual system. Same shape as the other viewers' "?" content,
    # localized via the STRINGS dict.
    n_components = len(map_data.get("components") or [])
    about_body = _build_about_body(lang)
    about_modal_html_str = app_pure_about_modal_html(
        kicker=f"№ {n_components:02d} · value map",
        headline=anchor_label or title,
        lede=S["about_lede"],
        body_html=about_body,
    )

    return HTML_TEMPLATE.format(
        head_meta=app_pure_head_meta(title),
        css=app_pure_css(layout="canvas") + EXTRA_CSS,
        dateline=app_pure_dateline_html(org_name, what=what_html),
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
        modal_html=(modal_html or "") + about_modal_html_str,
        W=W, H=H,
        svg_inner=inner,
        nodes_json=nodes_json,
        strings_json=strings_json,
        baseline_js=app_pure_baseline_js(),
        js=JS_TEMPLATE,
        GENESIS=GENESIS, CUSTOM=CUSTOM, PRODUCT=PRODUCT, COMMODITY=COMMODITY,
        ACCENT=ACCENT,
    )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Render a value-map JSON as an interactive App-pure HTML viewer (and an optional standalone SVG).")
    parser.add_argument("--map", required=True, help="value-map JSON")
    parser.add_argument("--html", required=True, help="HTML out")
    parser.add_argument("--svg", help="standalone SVG out (optional, for markdown embedding)")
    parser.add_argument("--org-name", default="", help="Organization name for the dateline (default: JSON `_org`, else 'Value map')")
    parser.add_argument("--lang", default="en", choices=["en", "it"],
                        help="Language for chrome + About modal copy. Default en.")
    args = parser.parse_args()

    map_data = json.loads(Path(args.map).read_text(encoding="utf-8"))
    html = render_html(map_data, org_name=args.org_name, lang=args.lang)
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"Wrote {Path(args.html).resolve()} ({len(html):,} bytes)")
    if args.svg:
        svg = render_svg_standalone(map_data)
        Path(args.svg).write_text(svg, encoding="utf-8")
        print(f"Wrote {Path(args.svg).resolve()} ({len(svg):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
