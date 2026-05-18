"""
Playable Org · design system

Single source of truth for the visual language of every playbook viewer.
Tokens, primitives, helper functions — all in one module.

Convention: viewers compose primitives, never write inline CSS. This module
is the only place where typography, spacing, color, and layout decisions
live. Update once, every viewer follows.

Visual version: 5
- v1: Inter Variable + monochrome-with-state-accents (#1a1a1a / #e5e5e5).
- v2: Mirage variable + Play New pure monochrome. Rolled back —
  Klim Type Foundry's standard Mirage license does not permit public
  redistribution; the public template ships with the open-licensed
  Inter Variable instead, and forks can swap in their own brand font
  by replacing `_assets/fonts/inter-variable.woff2`.
- v3: Inter Variable + Play New monochrome + a small pastel data-viz
  palette for heatmaps, stage bands, category swatches.
- v4: editorial direction with Italianate masthead, numbered-section
  register, marginalia, 5-stop colour scales per hue with glow
  variants, surface tokens (paper / inset-dark / raised), motion
  tokens, colophon footer pattern. v3 tokens preserved.
- v5 (current): "Carta sbiadita" App-pure shell, ported from the May
  2026 graph viewer redesign. Cream paper palette (`#f4eee2` ground,
  `#1c1a16` ink), Inter Variable with `ss01` + `cv11` features active,
  six load-bearing kind colours (slate · sage · ink · sand · lilac ·
  terracotta) plus four ambient ones, mobile-app baseline (safe-area
  insets, viewport-fit=cover, theme-color, apple-mobile-web-app meta,
  no tap highlight, no user-select on chrome, touch-action: none on
  canvases), inline SVG favicon (three dots in operational kind
  colours), Pointer Events for mouse + touch through one path, two-
  finger pinch zoom on canvas-mode viewers, floating chrome (dateline
  top-left, date + Analysis CTA top-right, hint bottom-center, kinds
  ribbon and tools bottom-flanks for canvas viewers, colophon for
  scroll viewers), Inspect card sliding in from the right on focus
  (canvas viewers), Analysis modal (`<kicker> / <h1> / <dateline> /
  <lede> / <ol class="decisions"> / <foot>`), `?focus=<id>` URL
  permalink. The five viewers split between two layout modes: graph
  and value-map are *canvas-first*, ai-exposure and reshuffle and
  world-model are *scroll-on-paper*; both modes share palette,
  typography, mobile baseline, modal, favicon, theme-color. v4 helpers
  remain available during the migration and are removed once every
  viewer is on v5.

License note: `_assets/fonts/inter-variable.woff2` is Inter Variable
by Rasmus Andersson, SIL Open Font License v1.1, freely
redistributable. If a fork wants to ship a different brand font, drop
in a replacement woff2 at the same path and update the
@font-face family name below. Per-instance branding is the deployment
model.

Public API:

    from design import (
        base_css,
        shell, header, rule, footer,
        section,
        stat_grid,
        pill,
        item_list, item,
        card_grid, card,
        modal_shell, modal_script, modal_field,
    )

The `base_css()` string already contains an `@font-face` block for
Inter Variable, embedded as a base64 data URL so the rendered HTML is
fully offline-portable.
"""

from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path
from typing import Iterable

_FONT_PATH = Path(__file__).resolve().parent / "_assets" / "fonts" / "inter-variable.woff2"


# ----------------------------------------------------------------------
# Font embedding
# ----------------------------------------------------------------------

def _font_data_url() -> str:
    """Inter Variable as a base64 data URL. Empty if the woff2 is missing."""
    if not _FONT_PATH.is_file():
        return ""
    encoded = base64.b64encode(_FONT_PATH.read_bytes()).decode("ascii")
    return f"data:font/woff2;base64,{encoded}"


def _font_face_block() -> str:
    """`@font-face` for Inter Variable.

    Falls back to system-ui / -apple-system if the woff2 is not present
    (e.g. an instance fork that swapped in its own brand font under a
    different file name).
    """
    data_url = _font_data_url()
    if not data_url:
        return ""
    return f"""@font-face {{
  font-family: 'Inter';
  src: url('{data_url}') format('woff2');
  font-weight: 100 900;
  font-display: swap;
}}"""


# ----------------------------------------------------------------------
# Tokens + primitives CSS
# ----------------------------------------------------------------------

def _base_css() -> str:
    """Tokens + every primitive class. Loaded once per viewer page."""
    return f"""{_font_face_block()}

:root {{
  /* ==================================================================
     COLOR — Play New monochrome. Opacity-layered black on white.
     Zero chromatic colors. All "color" comes from imagery, opacity
     layers, and hairline borders. The brand has one accent: black.
     ================================================================== */

  /* Backgrounds */
  --bg:               #FFFFFF;
  --bg-alt:           rgba(0, 0, 0, 0.04);   /* card / section tint */
  --bg-muted:         rgba(0, 0, 0, 0.06);   /* slightly stronger tint */
  --bg-dark:          #1A1A1A;               /* inverted sections */

  /* Foregrounds (black-on-white). Contrast bumped 2026-05-07 — the
     0.1 / 0.5 hairline + muted layer felt washed-out on page; nudged
     to 0.18 / 0.6 for visible borders and readable secondary labels. */
  --fg:               rgba(0, 0, 0, 0.92);   /* body / primary */
  --fg-muted:         rgba(0, 0, 0, 0.6);    /* labels, secondary */
  --fg-light:         rgba(0, 0, 0, 0.42);   /* tertiary */
  --fg-faint:         rgba(0, 0, 0, 0.3);    /* disabled, captions */
  --fg-hairline:      rgba(0, 0, 0, 0.18);   /* borders, separators */

  /* Inverse (on dark surfaces) */
  --fg-inverse:       #FAFAFA;
  --fg-inverse-90:    rgba(255, 255, 255, 0.9);
  --fg-inverse-70:    rgba(255, 255, 255, 0.7);
  --fg-inverse-50:    rgba(255, 255, 255, 0.5);
  --fg-inverse-15:    rgba(255, 255, 255, 0.15);
  --fg-inverse-08:    rgba(255, 255, 255, 0.08);

  /* Accent — there is only one. */
  --accent:           rgba(0, 0, 0, 0.9);

  /* Selection */
  --selection-bg:     rgba(0, 0, 0, 0.9);
  --selection-fg:     #FFFFFF;

  /* ------------------------------------------------------------------
     Backward-compat aliases — existing viewer EXTRA_CSS uses these.
     Phase 2 will migrate viewers to the canonical names above and
     these aliases will be dropped.
     ------------------------------------------------------------------ */
  --bg-soft:          rgba(0, 0, 0, 0.04);   /* alias of --bg-alt */
  --muted:            rgba(0, 0, 0, 0.6);    /* alias of --fg-muted */
  --soft:             rgba(0, 0, 0, 0.42);   /* alias of --fg-light */
  --line:             rgba(0, 0, 0, 0.18);   /* alias of --fg-hairline */

  /* ------------------------------------------------------------------
     Data-viz palette — pastel secondary. Used only where category
     differentiation is necessary (AEI heatmaps, value-map stage
     bands, world-model moat/commodity, reshuffle constraint colours).
     Brand surfaces stay monochrome; pastels live in viz only.
     Five hues + soft-tint companions. Saturation is uniformly low
     for Play New editorial restraint. The warm anchor (coral) is the
     same #c47558 the brand uses as the "principio condiviso" backdrop.
     ------------------------------------------------------------------ */
  --ds-sage:          #88a884;     /* genesis · automated · success */
  --ds-sage-bg:       #ecf2ea;
  --ds-lilac:         #a5a3c8;     /* custom · augmented */
  --ds-lilac-bg:      #efeef5;
  --ds-slate:         #99b3d4;     /* product · assistive · info */
  --ds-slate-bg:      #ebf0f7;
  --ds-sand:          #d8cfb6;     /* commodity · no-data */
  --ds-sand-bg:       #f7f3ea;
  --ds-coral:         #c47558;     /* warn · moat · brand accent */
  --ds-coral-bg:      #fbf2eb;

  /* ------------------------------------------------------------------
     v4 — Five-stop colour scales per hue (50 / 200 / 400 / 600 / 900)
     plus a `-glow` token for drop-shadow / focus halos. The 400 stop
     equals the original flat token (--ds-sage etc.) for backward
     compatibility. Use cases:
       50  — background tint
       200 — secondary fill
       400 — primary fill (today's flat token)
       600 — strong accent
       900 — text on light bg, ornaments
       glow — focus halo (rgba with alpha for filter)
     ------------------------------------------------------------------ */
  --ds-sage-50:       #f3f7f1;
  --ds-sage-200:      #c9d8c5;
  --ds-sage-400:      #88a884;
  --ds-sage-600:      #5b8055;
  --ds-sage-900:      #2c4628;
  --ds-sage-glow:     rgba(136, 168, 132, 0.55);

  --ds-lilac-50:      #f6f5fa;
  --ds-lilac-200:     #d6d4e6;
  --ds-lilac-400:     #a5a3c8;
  --ds-lilac-600:     #756fa3;
  --ds-lilac-900:     #3b365e;
  --ds-lilac-glow:    rgba(165, 163, 200, 0.55);

  --ds-slate-50:      #f3f6fa;
  --ds-slate-200:     #cad7e8;
  --ds-slate-400:     #99b3d4;
  --ds-slate-600:     #5d80b0;
  --ds-slate-900:     #28456b;
  --ds-slate-glow:    rgba(153, 179, 212, 0.55);

  --ds-sand-50:       #fbf8f1;
  --ds-sand-200:      #ece4cc;
  --ds-sand-400:      #d8cfb6;
  --ds-sand-600:      #9c8d68;
  --ds-sand-900:      #4d4225;
  --ds-sand-glow:     rgba(216, 207, 182, 0.55);

  --ds-coral-50:      #fbf2ec;
  --ds-coral-200:     #ecc6b1;
  --ds-coral-400:     #c47558;
  --ds-coral-600:     #8c4a30;
  --ds-coral-900:     #4a2412;
  --ds-coral-glow:    rgba(196, 117, 88, 0.6);

  /* ------------------------------------------------------------------
     v4 — Surface tokens. "Paper" is the default editorial white
     surface with a faint warm tint and subtle ruling. "Paper-grain"
     adds a noise overlay via background-image (for hero blocks).
     "Inset-dark" is the deep slate the graph viewer uses. "Raised"
     is for hovered cards.
     ------------------------------------------------------------------ */
  --surf-paper:       #FFFFFF;
  --surf-paper-tint:  #FCFCFA;          /* hairline-warm white */
  --surf-paper-rule:  rgba(0,0,0,0.04); /* faint horizontal ruling */
  --surf-inset-dark:  #14171c;          /* graph canvas */
  --surf-inset-side:  #1a1d24;          /* panel attached to inset */
  --surf-raised-shadow: 0 4px 32px rgba(0,0,0,0.10);
  --surf-paper-shadow:  0 2px 18px rgba(0,0,0,0.06);

  /* ------------------------------------------------------------------
     v4 — Editorial typography registers (additive over v3 type scale).
     The display sizes are big — for hero / masthead use only.
     ------------------------------------------------------------------ */
  --t-display-1:      clamp(3.4rem, 8vw, 6rem);     /* hero */
  --t-display-2:      clamp(2.4rem, 5vw, 3.6rem);   /* viewer h1 */
  --t-kicker:         0.74rem;                      /* italic small caps eyebrow */
  --t-dateline:       0.78rem;                      /* italic dateline below display */
  --t-body-lede:      1.125rem;                     /* lede paragraph */
  --t-marginalia:     0.78rem;                      /* annotation aside */
  --t-section-num:    0.84rem;                      /* "0.1" numbered section */
  --t-colophon:       0.74rem;                      /* footer */

  --w-light:          200;
  --w-extrabold:      800;

  /* ------------------------------------------------------------------
     v4 — Motion tokens for cascading entry + restrained hover.
     ------------------------------------------------------------------ */
  --anim-entry:       0.5s cubic-bezier(0.16, 1, 0.3, 1);
  --anim-hover:       0.18s cubic-bezier(0.16, 1, 0.3, 1);
  --anim-stagger:     50ms;

  /* ------------------------------------------------------------------
     State semantic — re-points to the data-viz palette so brand and
     viz stay in sync. --error stays a deeper red: true emphasis
     (broken commitment, audit fail), not a category.
     ------------------------------------------------------------------ */
  --warn:             var(--ds-coral);
  --warn-bg:          var(--ds-coral-bg);
  --success:          var(--ds-sage);
  --success-bg:       var(--ds-sage-bg);
  --info:             var(--ds-slate);
  --info-bg:          var(--ds-slate-bg);
  --error:            #b91c1c;
  --error-bg:         #fef2f2;

  /* ==================================================================
     TYPE — Inter Variable. One family, weight 100..900.
     Display, body, and the historical "mono" role all alias to Inter
     (Play New convention: a single family across all roles). Forks
     that swap in a different brand font replace the woff2 at
     `_assets/fonts/inter-variable.woff2` and update the family name
     in the three tokens below.
     ================================================================== */

  --font-display:     'Inter', system-ui, -apple-system, sans-serif;
  --font-body:        'Inter', system-ui, -apple-system, sans-serif;
  --font-mono:        'Inter', ui-monospace, 'SF Mono', Menlo, monospace;

  --w-regular:        400;
  --w-medium:         500;
  --w-semibold:       600;
  --w-bold:           700;

  /* Scale (rem, 16px base) */
  --t-xs:             0.75rem;
  --t-sm:             0.8125rem;
  --t-base:           1rem;
  --t-lg:             1.25rem;
  --t-xl:             1.5rem;
  --t-2xl:            1.75rem;
  --t-3xl:            2rem;
  --t-4xl:            2.5rem;
  --t-5xl:            4rem;
  --t-hero:           clamp(3rem, 12vw, 10rem);
  --t-block:          clamp(2.5rem, 6vw, 4rem);
  --t-quote:          clamp(1.5rem, 3vw, 2rem);

  /* Line heights — TIGHT for display, airy for body */
  --lh-tight:         0.9;
  --lh-display:       1.1;
  --lh-snug:          1.25;
  --lh-normal:        1.5;
  --lh-relaxed:       1.7;

  /* Letter-spacing — display is always negative */
  --ls-hero:          -0.05em;
  --ls-h1:            -0.04em;
  --ls-h2:            -0.03em;
  --ls-tight:         -0.02em;
  --ls-wide:          0.04em;       /* uppercase eyebrow */
  --ls-uppercase:     0.10em;

  /* ==================================================================
     SPACING — 4px grid.
     Two parallel naming conventions: --s-* (legacy) and --sp-* (Play
     New). Same values, kept for compatibility during phase 1.
     ================================================================== */

  --s-1:              4px;
  --s-2:              8px;
  --s-3:              12px;
  --s-4:              16px;
  --s-5:              20px;
  --s-6:              24px;
  --s-7:              32px;
  --s-8:              40px;
  --s-9:              48px;
  --s-10:             64px;
  --s-11:             80px;

  --sp-1:             0.25rem;
  --sp-2:             0.5rem;
  --sp-3:             0.75rem;
  --sp-4:             1rem;
  --sp-5:             1.25rem;
  --sp-6:             1.5rem;
  --sp-8:             2rem;
  --sp-10:            2.5rem;
  --sp-12:            3rem;
  --sp-16:            4rem;
  --sp-20:            5rem;

  /* ==================================================================
     RADII — 4px (controls), 8px (chrome), 12px (images), 16-24px (cards),
     full (pills/avatars). No 16 in light surfaces.
     ================================================================== */

  --r-sm:             0.25rem;       /* 4px   */
  --r-md:             0.5rem;        /* 8px   */
  --r-lg:             0.75rem;       /* 12px  */
  --r-xl:             1rem;          /* 16px  */
  --r-2xl:            1.25rem;       /* 20px  */
  --r-3xl:            1.5rem;        /* 24px  */
  --r-full:           9999px;

  /* ==================================================================
     SHADOWS — used sparingly. Paper cards, banner overlays only.
     ================================================================== */

  --shadow-paper:     0 4px 24px rgba(0, 0, 0, 0.08);
  --shadow-banner:    0 4px 24px rgba(0, 0, 0, 0.2);

  /* ==================================================================
     MOTION — fast, understated.
     ================================================================== */

  --dur-fast:         0.2s;
  --dur-base:         0.3s;
  --dur-slow:         0.5s;
  --dur-entry:        0.8s;
  --ease-out:         ease-out;
  --ease-in:          ease-in;
}}

* {{ box-sizing: border-box; }}

::selection {{ background: var(--selection-bg); color: var(--selection-fg); }}

html, body {{
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-body);
  font-optical-sizing: auto;
  -webkit-font-smoothing: antialiased;
  line-height: var(--lh-normal);
  font-size: 15px;
}}

a {{ color: inherit; text-underline-offset: 2px; }}
a:hover {{ color: var(--fg-muted); }}

button {{
  font-family: inherit;
  cursor: pointer;
  background: var(--bg);
  border: 1px solid var(--fg-hairline);
  color: var(--fg);
  padding: var(--s-2) var(--s-4);
  border-radius: var(--r-sm);
  font-size: 0.85rem;
  transition: background var(--dur-fast) var(--ease-out);
}}
button:hover {{ background: var(--bg-alt); }}

:focus-visible {{ outline: 2px solid var(--fg); outline-offset: 2px; }}

@keyframes pn-fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes pn-pop  {{ from {{ opacity: 0; transform: translateY(8px); }}
                       to   {{ opacity: 1; transform: translateY(0);   }} }}
@keyframes ed-rise {{ from {{ opacity: 0; transform: translateY(14px); }}
                       to   {{ opacity: 1; transform: translateY(0);    }} }}

/* ==================================================================
   v4 — EDITORIAL register (Italianate masthead, numbered sections,
   marginalia, colophon). Drop these classes anywhere — they assume
   the surrounding container provides width.
   ================================================================== */

.ed-masthead {{
  margin: 0 auto var(--s-9);
  max-width: 820px;
  padding-top: var(--s-7);
  position: relative;
}}
.ed-masthead::before {{
  /* Italianate column-rule — a thin vertical line on the left, seen
     from old print-page anatomy. Disappears on narrow viewports. */
  content: "";
  position: absolute;
  left: -22px; top: var(--s-7); bottom: 8px;
  width: 1px;
  background: var(--fg-hairline);
}}
@media (max-width: 920px) {{
  .ed-masthead::before {{ display: none; }}
}}

.ed-kicker {{
  font-family: var(--font-display);
  font-style: italic;
  font-weight: var(--w-medium);
  font-size: var(--t-kicker);
  text-transform: lowercase;
  letter-spacing: 0.06em;
  color: var(--fg-muted);
  margin: 0 0 var(--s-4) 0;
  display: flex; gap: 14px; align-items: baseline;
}}
.ed-kicker .sep {{ font-style: normal; color: var(--fg-light); }}
.ed-kicker .num {{ font-weight: var(--w-bold); font-style: normal; color: var(--fg); font-variant-numeric: tabular-nums; }}

.ed-display {{
  font-family: var(--font-display);
  font-weight: var(--w-extrabold);
  font-size: var(--t-display-2);
  line-height: 0.96;
  letter-spacing: -0.04em;
  color: var(--fg);
  margin: 0 0 var(--s-5) 0;
}}
.ed-display em {{ font-style: italic; font-weight: var(--w-light); letter-spacing: -0.02em; color: var(--fg); }}

.ed-lede {{
  font-family: var(--font-body);
  font-size: var(--t-body-lede);
  line-height: 1.55;
  color: var(--fg);
  margin: 0 0 var(--s-5) 0;
  max-width: 660px;
}}

.ed-dateline {{
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--t-dateline);
  color: var(--fg-light);
  margin: var(--s-3) 0 0 0;
  display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap;
}}
.ed-dateline .tag {{
  font-style: normal;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  background: var(--bg-alt);
  color: var(--fg-muted);
  padding: 2px 8px;
  border-radius: 999px;
}}

.ed-section-head {{
  display: flex; align-items: baseline; gap: 14px;
  margin: var(--s-9) 0 var(--s-6) 0;
  font-family: var(--font-display);
  letter-spacing: -0.02em;
}}
.ed-section-head .num {{
  font-weight: var(--w-light);
  font-style: italic;
  color: var(--fg-light);
  font-size: var(--t-section-num);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}}
.ed-section-head .rule {{
  flex: 0 0 24px;
  height: 1px;
  background: var(--fg-hairline);
  align-self: center;
  margin-top: 4px;
}}
.ed-section-head .title {{
  font-weight: var(--w-medium);
  font-size: 1.4rem;
  color: var(--fg);
}}

.ed-marginalia {{
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--t-marginalia);
  color: var(--fg-muted);
  line-height: 1.55;
  border-left: 1px solid var(--fg-hairline);
  padding-left: 12px;
  margin: var(--s-3) 0;
  max-width: 280px;
}}

.ed-colophon {{
  margin: var(--s-11) auto 0;
  max-width: 820px;
  padding: var(--s-6) 0 var(--s-3);
  border-top: 1px solid var(--fg-hairline);
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--t-colophon);
  color: var(--fg-light);
  line-height: 1.65;
  text-align: right;
}}
.ed-colophon .line {{ display: block; margin-bottom: 4px; }}
.ed-colophon code {{ font-style: normal; font-size: 0.72rem; background: transparent; padding: 0; color: var(--fg-muted); }}

/* Disclosed grid — faint vertical column guides shown on hero blocks. */
.ed-disclosed-grid {{
  position: relative;
}}
.ed-disclosed-grid::after {{
  content: "";
  position: absolute; inset: 0;
  background-image:
    linear-gradient(to right, var(--fg-hairline) 1px, transparent 1px);
  background-size: 20% 100%;
  background-position: 0 0;
  opacity: 0.35;
  pointer-events: none;
}}

/* Cascading entry: any direct child gets a small staggered fade-in */
.ed-cascade > * {{ animation: ed-rise var(--anim-entry) both; }}
.ed-cascade > *:nth-child(2) {{ animation-delay: calc(var(--anim-stagger) * 1); }}
.ed-cascade > *:nth-child(3) {{ animation-delay: calc(var(--anim-stagger) * 2); }}
.ed-cascade > *:nth-child(4) {{ animation-delay: calc(var(--anim-stagger) * 3); }}
.ed-cascade > *:nth-child(5) {{ animation-delay: calc(var(--anim-stagger) * 4); }}
.ed-cascade > *:nth-child(6) {{ animation-delay: calc(var(--anim-stagger) * 5); }}

/* ==================================================================
   SEMANTIC TYPE classes — drop onto any element for one-line styling.
   Mirror the Play New design system's colors_and_type.css.
   ================================================================== */

.pn-hero {{
  font-family: var(--font-display);
  font-weight: var(--w-medium);
  font-size: var(--t-hero);
  line-height: var(--lh-tight);
  letter-spacing: var(--ls-hero);
  color: var(--fg);
}}

.pn-h1 {{
  font-family: var(--font-display);
  font-weight: var(--w-medium);
  font-size: var(--t-5xl);
  line-height: 0.95;
  letter-spacing: var(--ls-h1);
  color: var(--fg);
}}

.pn-h2 {{
  font-family: var(--font-display);
  font-weight: var(--w-medium);
  font-size: var(--t-block);
  line-height: var(--lh-display);
  letter-spacing: var(--ls-h2);
  color: var(--fg);
}}

.pn-h3 {{
  font-family: var(--font-display);
  font-weight: var(--w-medium);
  font-size: var(--t-2xl);
  line-height: 1.2;
  color: var(--fg);
}}

/* Big statement — used as "fig-text" / compare list items */
.pn-statement {{
  font-family: var(--font-display);
  font-weight: var(--w-medium);
  font-size: var(--t-xl);
  line-height: var(--lh-snug);
  color: var(--fg-muted);
}}
.pn-statement strong {{ color: var(--fg); font-weight: var(--w-medium); }}

/* Pull quote — editorial */
.pn-quote {{
  font-family: var(--font-display);
  font-weight: var(--w-medium);
  font-size: var(--t-quote);
  line-height: 1.3;
  color: var(--fg);
}}

/* Body */
.pn-body {{
  font-family: var(--font-body);
  font-size: var(--t-base);
  line-height: var(--lh-relaxed);
  color: var(--fg);
}}

/* Lead / subtitle */
.pn-lead {{
  font-family: var(--font-body);
  font-size: var(--t-lg);
  line-height: var(--lh-normal);
  color: var(--fg-muted);
}}

/* Nav / column link */
.pn-link {{
  font-family: var(--font-body);
  font-size: var(--t-base);
  line-height: 1.6;
  color: var(--fg);
  text-decoration: none;
}}
.pn-link:hover {{ text-decoration: underline; text-underline-offset: 3px; }}

/* Small caps-style label — UPPERCASE eyebrow */
.pn-eyebrow {{
  font-family: var(--font-display);
  font-weight: var(--w-medium);
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--fg-muted);
  text-transform: uppercase;
  letter-spacing: var(--ls-wide);
}}

/* Big number — "01." "85%" "€240K" */
.pn-num {{
  font-family: var(--font-display);
  font-weight: var(--w-bold);
  font-size: var(--t-4xl);
  line-height: 1;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}}

/* Footer / legal */
.pn-legal {{
  font-family: var(--font-body);
  font-size: var(--t-sm);
  line-height: var(--lh-normal);
  color: var(--fg-muted);
}}

/* ==================================================================
   COMPONENT PRIMITIVES
   ================================================================== */

/* Layout */

.pn-shell {{
  max-width: 1100px;
  margin: 0 auto;
  padding: var(--s-10) var(--s-8) var(--s-11);
}}

.pn-rule {{
  height: 1px;
  background: var(--fg-hairline);
  border: none;
  margin: var(--s-9) 0 var(--s-7);
}}

/* Header */

.pn-header {{ margin-bottom: var(--s-9); }}
.pn-header__eyebrow {{
  font-size: 0.72rem;
  font-weight: var(--w-medium);
  text-transform: uppercase;
  letter-spacing: var(--ls-uppercase);
  color: var(--fg-light);
  margin-bottom: var(--s-4);
}}
.pn-header__title {{
  font-family: var(--font-display);
  font-size: 2.4rem;
  font-weight: var(--w-medium);
  letter-spacing: var(--ls-tight);
  line-height: 1.1;
  margin: 0;
}}
.pn-header__sub {{
  margin-top: var(--s-3);
  color: var(--fg-muted);
  font-size: 0.95rem;
  max-width: 640px;
  line-height: var(--lh-normal);
}}

/* Section header */

.pn-section {{
  display: flex;
  align-items: baseline;
  gap: var(--s-5);
  margin-bottom: var(--s-7);
}}
.pn-section__num {{
  font-size: 0.78rem;
  font-weight: var(--w-medium);
  color: var(--fg-light);
  letter-spacing: 0.05em;
  font-variant-numeric: tabular-nums;
}}
.pn-section__title {{
  font-size: 0.78rem;
  font-weight: var(--w-medium);
  text-transform: uppercase;
  letter-spacing: var(--ls-uppercase);
  color: var(--fg);
}}
.pn-section__hint {{
  margin-left: auto;
  font-size: 0.78rem;
  color: var(--fg-light);
}}

/* Stat grid */

.pn-stat {{ padding: var(--s-7); }}
.pn-stat__num {{
  font-family: var(--font-display);
  font-size: 2.8rem;
  font-weight: var(--w-regular);
  line-height: 1;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
  color: var(--fg);
  margin-bottom: var(--s-5);
}}
.pn-stat__lab {{
  font-size: 0.72rem;
  font-weight: var(--w-medium);
  text-transform: uppercase;
  letter-spacing: var(--ls-uppercase);
  color: var(--fg-muted);
}}

.pn-stat-grid {{
  display: grid;
  border-top: 1px solid var(--fg-hairline);
  border-bottom: 1px solid var(--fg-hairline);
}}
.pn-stat-grid--4 {{ grid-template-columns: repeat(4, 1fr); }}
.pn-stat-grid--3 {{ grid-template-columns: repeat(3, 1fr); }}
.pn-stat-grid--2 {{ grid-template-columns: repeat(2, 1fr); }}

.pn-stat-grid > .pn-stat {{ border-right: 1px solid var(--fg-hairline); }}
.pn-stat-grid--4 > .pn-stat:nth-child(4n+1) {{ padding-left: 0; }}
.pn-stat-grid--4 > .pn-stat:nth-child(4n)   {{ padding-right: 0; border-right: none; }}
.pn-stat-grid--3 > .pn-stat:nth-child(3n+1) {{ padding-left: 0; }}
.pn-stat-grid--3 > .pn-stat:nth-child(3n)   {{ padding-right: 0; border-right: none; }}
.pn-stat-grid--2 > .pn-stat:nth-child(2n+1) {{ padding-left: 0; }}
.pn-stat-grid--2 > .pn-stat:nth-child(2n)   {{ padding-right: 0; border-right: none; }}
.pn-stat-grid--4 > .pn-stat:nth-child(n+5) {{ border-top: 1px solid var(--fg-hairline); }}
.pn-stat-grid--3 > .pn-stat:nth-child(n+4) {{ border-top: 1px solid var(--fg-hairline); }}
.pn-stat-grid--2 > .pn-stat:nth-child(n+3) {{ border-top: 1px solid var(--fg-hairline); }}

/* Pill / code */

.pn-pill {{
  display: inline-flex;
  align-items: center;
  font-size: 0.66rem;
  font-weight: var(--w-medium);
  letter-spacing: var(--ls-uppercase);
  text-transform: uppercase;
  padding: 2px var(--s-2);
  border-radius: var(--r-sm);
  line-height: 1.5;
}}
.pn-pill--neutral {{ background: var(--bg-alt);     color: var(--fg-muted); }}
.pn-pill--error   {{ background: var(--error-bg);   color: var(--error); }}
.pn-pill--warn    {{ background: var(--warn-bg);    color: var(--warn); }}
.pn-pill--ok      {{ background: var(--success-bg); color: var(--success); }}
.pn-pill--info    {{ background: var(--info-bg);    color: var(--info); }}

.pn-code, code {{
  font-family: var(--font-mono);
  font-size: 0.875em;
}}
code {{
  background: var(--bg-alt);
  padding: 0.125em 0.375em;
  border-radius: var(--r-sm);
}}
.pn-code {{
  font-weight: var(--w-medium);
  letter-spacing: 0.02em;
  color: var(--fg-muted);
  font-variant-numeric: tabular-nums;
  font-size: 0.72rem;
}}

/* Item list */

.pn-item-list {{ display: flex; flex-direction: column; }}
.pn-item {{
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: var(--s-7);
  padding: var(--s-6) 0;
  border-bottom: 1px solid var(--fg-hairline);
}}
.pn-item:last-child {{ border-bottom: none; }}
.pn-item__meta {{
  display: flex;
  align-items: flex-start;
  gap: var(--s-2);
  flex-wrap: wrap;
}}
.pn-item__head {{ font-size: 0.95rem; font-weight: var(--w-medium); margin-bottom: var(--s-2); }}
.pn-item__body {{ font-size: 0.9rem; color: var(--fg-muted); line-height: 1.6; }}
.pn-item__refs {{
  margin-top: var(--s-3);
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--fg-light);
}}

/* Card grid */

.pn-card-grid {{ display: grid; border-top: 1px solid var(--fg-hairline); }}
.pn-card-grid--2 {{ grid-template-columns: repeat(2, 1fr); }}
.pn-card-grid--1 {{ grid-template-columns: 1fr; }}

.pn-card {{
  padding: var(--s-6) var(--s-7);
  border-bottom: 1px solid var(--fg-hairline);
  border-right: 1px solid var(--fg-hairline);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}}
.pn-card:hover {{ background: var(--bg-alt); }}
.pn-card-grid--2 > .pn-card:nth-child(2n+1) {{ padding-left: 0; }}
.pn-card-grid--2 > .pn-card:nth-child(2n)   {{ padding-right: 0; border-right: none; }}
.pn-card-grid--1 > .pn-card                 {{ padding-left: 0; padding-right: 0; border-right: none; }}

.pn-card__head {{
  display: flex;
  align-items: baseline;
  gap: var(--s-3);
  margin-bottom: var(--s-3);
  flex-wrap: wrap;
}}
.pn-card__name {{
  font-family: var(--font-mono);
  font-size: 0.88rem;
  font-weight: var(--w-medium);
  letter-spacing: -0.005em;
  color: var(--fg);
}}
.pn-card__tag {{
  font-size: 0.66rem;
  font-weight: var(--w-medium);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--fg-muted);
}}
.pn-card__tag--accent {{ color: var(--warn); }}
.pn-card__desc {{
  font-size: 0.88rem;
  color: var(--fg-muted);
  line-height: 1.55;
  margin-bottom: var(--s-3);
}}
.pn-card__meta {{
  display: flex;
  gap: var(--s-4);
  font-size: 0.74rem;
  color: var(--fg-light);
  font-variant-numeric: tabular-nums;
  flex-wrap: wrap;
}}

/* Footer */

.pn-footer {{
  margin-top: var(--s-11);
  padding-top: var(--s-6);
  border-top: 1px solid var(--fg-hairline);
  font-size: 0.78rem;
  color: var(--fg-light);
  display: flex;
  justify-content: space-between;
}}

/* Modal */

.pn-modal-backdrop {{
  position: fixed;
  inset: 0;
  background: rgba(26, 26, 26, 0.32);
  display: none;
  align-items: flex-start;
  justify-content: center;
  padding: 60px 16px 16px;
  z-index: 100;
  overflow-y: auto;
  backdrop-filter: blur(4px);
}}
.pn-modal-backdrop.is-open {{ display: flex; animation: pn-fade var(--dur-fast) var(--ease-out); }}

.pn-modal {{
  background: var(--bg);
  border: 1px solid var(--fg-hairline);
  border-radius: var(--r-md);
  width: 100%;
  max-width: 720px;
  padding: var(--s-7) var(--s-8) var(--s-8);
  animation: pn-pop var(--dur-base) var(--ease-out);
}}
.pn-modal__close {{
  float: right;
  background: transparent;
  border: 0;
  font-size: 1.4rem;
  line-height: 1;
  color: var(--fg-muted);
  padding: 0;
  margin-left: var(--s-3);
}}
.pn-modal__close:hover {{ color: var(--fg); background: transparent; }}
.pn-modal__title {{
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: var(--w-medium);
  letter-spacing: var(--ls-tight);
  margin: 0 0 var(--s-4);
}}
.pn-modal__field {{ margin: var(--s-4) 0; }}
.pn-modal__field-label {{
  font-size: 0.72rem;
  font-weight: var(--w-medium);
  text-transform: uppercase;
  letter-spacing: var(--ls-uppercase);
  color: var(--fg-light);
  margin-bottom: var(--s-2);
}}
.pn-modal__field-value {{
  font-size: 0.92rem;
  color: var(--fg);
  line-height: 1.6;
}}

@media print {{
  .pn-modal-backdrop {{ display: none !important; }}
  .pn-card:hover {{ background: transparent; }}
}}
"""


_CSS_CACHE: str | None = None


def base_css() -> str:
    """Return the full Playable Org CSS as a string (font embedded)."""
    global _CSS_CACHE
    if _CSS_CACHE is None:
        _CSS_CACHE = _base_css()
    return _CSS_CACHE


# ----------------------------------------------------------------------
# Inline markdown (for agent-authored prose in plays)
# ----------------------------------------------------------------------

def inline_md(s: str, *, link_resolver=None) -> str:
    """Render a single paragraph of inline markdown safely.

    Supports four inline forms the agent reaches for in decision bodies
    and node descriptions:

    - ``**bold**``    → ``<strong>``
    - ``*italic*``    → ``<em>``
    - ``` `code` ```  → ``<code>``
    - ``[label](target)`` → ``<a>`` (clickable link)

    Anything else is left as escaped plain text. Block-level markdown
    (headings, lists, blockquotes) is not supported on purpose: callers
    split paragraphs at blank lines, and the inline forms above are all
    a leader-facing prose needs.

    Link handling depends on the optional ``link_resolver`` callable:

    - If provided, it's called with each link target. When it returns a
      non-empty string (a node id), the link renders as
      ``<a class="anchor" data-focus="<id>" href="#"><label></a>``,
      hooking into the viewer's existing focus-on-canvas JS.
    - When ``link_resolver`` returns falsy (external URL, unresolvable
      target), the link renders as a plain ``<a href="<target>">``.
    - If ``link_resolver`` is ``None``, every link renders as plain
      ``<a href="<target>">`` (legacy callers stay XSS-safe).

    The renderer is XSS-safe: links are stashed before HTML escape, the
    rest of the string is escaped, the inline forms are applied, and
    the links are restored last with both label and target escaped at
    insertion time.
    """
    # 1. Stash markdown links behind NUL-delimited placeholders so the
    #    HTML escape on the body text doesn't mangle the brackets.
    stashed_links: list[tuple[str, str]] = []

    def _stash_link(m: 're.Match[str]') -> str:
        stashed_links.append((m.group(1), m.group(2)))
        return f"\x00LINK{len(stashed_links) - 1}\x00"

    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _stash_link, s)

    # 2. Escape everything else.
    s = escape(s)

    # 3. Apply inline emphasis on the escaped text.
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)

    # 4. Restore links as either focus anchors (internal nodes) or
    #    plain hrefs (external / unresolvable).
    def _restore_link(m: 're.Match[str]') -> str:
        idx = int(m.group(1))
        label, target = stashed_links[idx]
        label_html = escape(label)
        if link_resolver is not None:
            node_id = link_resolver(target)
            if node_id:
                return (
                    f'<a class="anchor" data-focus="{escape(node_id)}" '
                    f'href="#">{label_html}</a>'
                )
        return f'<a href="{escape(target)}">{label_html}</a>'

    s = re.sub(r'\x00LINK(\d+)\x00', _restore_link, s)
    return s


# ----------------------------------------------------------------------
# Primitive builders
# ----------------------------------------------------------------------

def shell(body: str) -> str:
    """Wrap body in the centred page shell."""
    return f'<main class="pn-shell">{body}</main>'


def header(eyebrow: str = "", title: str = "", sub: str = "") -> str:
    eb = f'<div class="pn-header__eyebrow">{escape(eyebrow)}</div>' if eyebrow else ""
    sb = f'<p class="pn-header__sub">{escape(sub)}</p>' if sub else ""
    return f"""<header class="pn-header">
  {eb}
  <h1 class="pn-header__title">{escape(title)}</h1>
  {sb}
</header>"""


def rule() -> str:
    return '<hr class="pn-rule">'


def footer(left: str = "", right: str = "") -> str:
    return f"""<footer class="pn-footer">
  <span>{escape(left)}</span>
  <span>{escape(right)}</span>
</footer>"""


# ----------------------------------------------------------------------
# v4 — editorial primitives (Italianate masthead, colophon, sections)
# ----------------------------------------------------------------------

def masthead(
    *,
    kicker_left: str = "",
    kicker_num: str = "",
    kicker_right: str = "",
    title: str,
    lede: str = "",
    dateline: str = "",
    tags: Iterable[str] = (),
) -> str:
    """Italianate masthead, à la Accurat / La Lettura.

    Drop in at the very top of a viewer body. Provides the kicker
    (italic small caps with optional issue-number ornament), the
    display title, the lede paragraph, and a dateline with tag chips.

    `title` may contain HTML — pass `<em>...</em>` for italic accent
    on a word in the display.

    Visual reference: docs/design-direction.md (Accurat masthead rule).
    """
    tags_html = "".join(
        f'<span class="tag">{escape(t)}</span>' for t in tags
    )
    kicker_parts = []
    if kicker_left:
        kicker_parts.append(f'<span>{escape(kicker_left)}</span>')
    if kicker_num:
        kicker_parts.append(f'<span class="num">{escape(kicker_num)}</span>')
    if kicker_right:
        kicker_parts.append(f'<span class="sep">·</span>')
        kicker_parts.append(f'<span>{escape(kicker_right)}</span>')
    kicker_html = (
        f'<div class="ed-kicker">{"".join(kicker_parts)}</div>'
        if kicker_parts else ""
    )
    lede_html = f'<p class="ed-lede">{lede}</p>' if lede else ""
    dl_inner = ""
    if dateline:
        dl_inner += f'<span>{escape(dateline)}</span>'
    if tags_html:
        dl_inner += tags_html
    dateline_html = f'<div class="ed-dateline">{dl_inner}</div>' if dl_inner else ""
    return f"""<header class="ed-masthead ed-cascade">
  {kicker_html}
  <h1 class="ed-display">{title}</h1>
  {lede_html}
  {dateline_html}
</header>"""


def section_head(num: str, title: str) -> str:
    """Numbered editorial section header: "0.1 ── Title"."""
    return (
        f'<div class="ed-section-head">'
        f'<span class="num">{escape(num)}</span>'
        f'<span class="rule"></span>'
        f'<span class="title">{escape(title)}</span>'
        f'</div>'
    )


def marginalia(text: str) -> str:
    """A small italic aside set in the margin of a hero block."""
    return f'<aside class="ed-marginalia">{escape(text)}</aside>'


def colophon(
    *,
    citations: int | None = None,
    sources: int | None = None,
    generator: str = "",
    generated_on: str = "",
    audit: str = "pass",
    autoresearch: str = "",
    extra_lines: Iterable[str] = (),
) -> str:
    """Magazine-grade footer at the bottom of a viewer.

    All fields optional — passing none renders an empty colophon.
    `audit` and `autoresearch` are status strings ("pass", "skipped").
    `generator` is e.g. "skills/playbooks/graph/build.py".
    """
    lines = []
    if citations is not None and sources is not None:
        lines.append(
            f'<span class="line">Built from <code>{citations}</code> citations '
            f'across <code>{sources}</code> source documents.</span>'
        )
    if generator:
        gen = f'<code>{escape(generator)}</code>'
        when = f' on <code>{escape(generated_on)}</code>' if generated_on else ''
        lines.append(f'<span class="line">Generated by {gen}{when}.</span>')
    status_bits = []
    if audit:
        status_bits.append(f'audit <code>{escape(audit)}</code>')
    if autoresearch:
        status_bits.append(f'autoresearch <code>{escape(autoresearch)}</code>')
    if status_bits:
        lines.append(f'<span class="line">' + ' · '.join(status_bits) + '.</span>')
    for ln in extra_lines:
        lines.append(f'<span class="line">{ln}</span>')
    if not lines:
        return ""
    return f'<footer class="ed-colophon">{"".join(lines)}</footer>'


def section(num: str = "", title: str = "", hint: str = "") -> str:
    n = f'<div class="pn-section__num">{escape(num)}</div>' if num else ""
    h = f'<div class="pn-section__hint">{escape(hint)}</div>' if hint else ""
    return f"""<div class="pn-section">
  {n}
  <div class="pn-section__title">{escape(title)}</div>
  {h}
</div>"""


def stat_grid(stats: Iterable[tuple[str, str]], cols: int = 4) -> str:
    """`stats`: iterable of (number, label). `cols`: 2, 3, or 4."""
    if cols not in (2, 3, 4):
        cols = 4
    cells = "".join(
        f'<div class="pn-stat"><div class="pn-stat__num">{escape(str(n))}</div>'
        f'<div class="pn-stat__lab">{escape(str(l))}</div></div>'
        for n, l in stats
    )
    return f'<section class="pn-stat-grid pn-stat-grid--{cols}">{cells}</section>'


def pill(label: str, kind: str = "neutral") -> str:
    """`kind` in: neutral, error, warn, ok, info."""
    if kind not in {"neutral", "error", "warn", "ok", "info"}:
        kind = "neutral"
    return f'<span class="pn-pill pn-pill--{kind}">{escape(label)}</span>'


def code(text: str) -> str:
    return f'<span class="pn-code">{escape(text)}</span>'


def item(meta_html: str, head: str, body_html: str = "", refs: str = "") -> str:
    """Single row in an item list. `meta_html` is composed (e.g., code() + pill())."""
    body_div = f'<div class="pn-item__body">{body_html}</div>' if body_html else ""
    refs_div = f'<div class="pn-item__refs">{escape(refs)}</div>' if refs else ""
    return f"""<article class="pn-item">
  <div class="pn-item__meta">{meta_html}</div>
  <div>
    <div class="pn-item__head">{escape(head)}</div>
    {body_div}
    {refs_div}
  </div>
</article>"""


def item_list(items_html: Iterable[str]) -> str:
    return f'<div class="pn-item-list">{"".join(items_html)}</div>'


def card(name: str, tag: str = "", desc: str = "", meta: Iterable[str] = (), tag_accent: bool = False, on_click: str = "") -> str:
    tag_cls = "pn-card__tag pn-card__tag--accent" if tag_accent else "pn-card__tag"
    tag_html = f'<div class="{tag_cls}">{escape(tag)}</div>' if tag else ""
    meta_html = ""
    meta_list = list(meta)
    if meta_list:
        spans = "".join(f"<span>{escape(m)}</span>" for m in meta_list)
        meta_html = f'<div class="pn-card__meta">{spans}</div>'
    onclick_attr = f' onclick="{escape(on_click)}"' if on_click else ""
    return f"""<div class="pn-card"{onclick_attr}>
  <div class="pn-card__head">
    <div class="pn-card__name">{escape(name)}</div>
    {tag_html}
  </div>
  <div class="pn-card__desc">{escape(desc)}</div>
  {meta_html}
</div>"""


def card_grid(cards_html: Iterable[str], cols: int = 2) -> str:
    if cols not in (1, 2):
        cols = 2
    return f'<section class="pn-card-grid pn-card-grid--{cols}">{"".join(cards_html)}</section>'


# ----------------------------------------------------------------------
# Modal helpers (caller wires content via `pnOpenModal(title, html)`)
# ----------------------------------------------------------------------

def modal_shell(modal_id: str = "pn-modal") -> str:
    return f"""<div id="{modal_id}" class="pn-modal-backdrop" onclick="if(event.target===this)pnCloseModal()">
  <div class="pn-modal">
    <button class="pn-modal__close" onclick="pnCloseModal()" aria-label="Close">×</button>
    <h3 class="pn-modal__title" id="{modal_id}-title"></h3>
    <div id="{modal_id}-body"></div>
  </div>
</div>"""


def modal_script(modal_id: str = "pn-modal") -> str:
    return f"""<script>
const pnModalEl    = document.getElementById('{modal_id}');
const pnModalTitle = document.getElementById('{modal_id}-title');
const pnModalBody  = document.getElementById('{modal_id}-body');
window.pnOpenModal = function(title, bodyHtml) {{
  pnModalTitle.textContent = title;
  pnModalBody.innerHTML = bodyHtml;
  pnModalEl.classList.add('is-open');
  document.body.style.overflow = 'hidden';
}};
window.pnCloseModal = function() {{
  pnModalEl.classList.remove('is-open');
  document.body.style.overflow = '';
}};
document.addEventListener('keydown', e => {{ if(e.key === 'Escape') pnCloseModal(); }});
</script>"""


def modal_field(label: str, value_html: str) -> str:
    return f"""<div class="pn-modal__field">
  <div class="pn-modal__field-label">{escape(label)}</div>
  <div class="pn-modal__field-value">{value_html}</div>
</div>"""


# ======================================================================
# v5 — App-pure shell
#
# Shared visual language across all five playbook viewers, ported from
# the May 2026 graph viewer redesign (Carta sbiadita palette, Inter
# Variable with ss01 + cv11, mobile-app feel: safe-area-inset, Pointer
# Events, no tap highlight, inline SVG favicon, embedded font, theme
# color, viewport-fit=cover).
#
# Two layout modes a viewer can opt into:
#
#   - canvas-first (graph, value-map): <canvas> or <svg> fills the
#     viewport; chrome floats on the paper. Inspect card slides in from
#     the right when the user focuses a node.
#
#   - scroll-on-paper (ai-exposure, reshuffle, world-model): vertical
#     scroll over the same paper palette, with the same dateline + date
#     + Analysis CTA on top, the same colophon at the bottom, the same
#     Analysis modal pattern. Inspect card and tooltip are not part of
#     this mode.
#
# Both modes share: palette, typography, mobile baseline, Analysis modal
# shape, favicon, theme-color. They differ in body-level layout only.
# ======================================================================


# Palette: "Carta sbiadita". Six load-bearing operational kinds (used by
# graph and value-map for category swatches); paper / ink / hairline
# tokens for surfaces and editorial chrome; modal scrim alpha.
APP_PURE_PALETTE = {
    "paper":       "#f4eee2",
    "paper_2":     "#ece5d4",
    "paper_3":     "#e2d9c3",
    "hairline":    "rgba(28, 26, 22, 0.14)",
    "hairline_2":  "rgba(28, 26, 22, 0.06)",
    "ink":         "#1c1a16",
    "ink_95":      "rgba(28, 26, 22, 0.95)",
    "ink_80":      "rgba(28, 26, 22, 0.78)",
    "ink_60":      "rgba(28, 26, 22, 0.58)",
    "ink_40":      "rgba(28, 26, 22, 0.38)",
    "ink_25":      "rgba(28, 26, 22, 0.25)",
    "modal_scrim": "rgba(28, 26, 22, 0.42)",
    # Operational kind colours
    "k_unit":              "#6b7d8c",
    "k_activity":          "#8a9d6b",
    "k_person":            "#1c1a16",
    "k_role":              "#bca787",
    "k_stakeholder":       "#9b8aa3",
    "k_commitment":        "#b87b5e",
    "k_financial_summary": "#7e8a6b",
    "k_identity":          "#b89b94",
    "k_language_term":     "#8c8a83",
    "k_source":            "#a09a8e",
}


def app_pure_favicon_href() -> str:
    """Inline SVG favicon as a data URL — three dots in operational
    kind colours (slate · sage · terracotta), a miniature graph
    fragment. Transparent background so the icon sits well on both
    light and dark browser chrome."""
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
        "<circle cx='16' cy='9' r='4.5' fill='%236b7d8c'/>"
        "<circle cx='9' cy='22' r='4' fill='%238a9d6b'/>"
        "<circle cx='23' cy='22' r='4' fill='%23b87b5e'/>"
        "</svg>"
    )
    return f"data:image/svg+xml;utf8,{svg}"


def app_pure_head_meta(title: str) -> str:
    """<head> meta + favicon link. Drop into every App-pure viewer's
    HTML between <head> and <style>.

    - viewport-fit=cover for iPhone notch
    - theme-color matches the paper background
    - apple-mobile-web-app-* for "Add to Home Screen" full-screen mode
    """
    return (
        '<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />\n'
        f'<meta name="theme-color" content="{APP_PURE_PALETTE["paper"]}" />\n'
        '<meta name="apple-mobile-web-app-capable" content="yes" />\n'
        '<meta name="apple-mobile-web-app-status-bar-style" content="default" />\n'
        f'<title>{escape(title)}</title>\n'
        f'<link rel="icon" type="image/svg+xml" href="{app_pure_favicon_href()}" />'
    )


def app_pure_css(*, layout: str = "canvas") -> str:
    """Shared CSS for App-pure viewers.

    `layout` selects body-level rules:
      - `"canvas"`: fixed full-bleed canvas/svg under floating chrome.
      - `"scroll"`: vertical scroll on paper, chrome stays sticky/floating.

    Each viewer should concatenate its own playbook-specific CSS after
    this block (kinds-pills swatches, axis labels, card grids, etc).
    """
    p = APP_PURE_PALETTE
    body_overflow = "hidden" if layout == "canvas" else "auto"
    body_height = "100%" if layout == "canvas" else "auto"
    body_touch = "none" if layout == "canvas" else "manipulation"
    # On scroll layouts the chrome (dateline, date-tr, analysis,
    # help-btn) is position:fixed with a transparent background;
    # scrolling content would otherwise paint directly onto it and
    # the text becomes unreadable. A paper-coloured strip behind the
    # chrome (z-index just below the chrome's 5) keeps the top zone
    # readable while preserving the editorial appearance. Canvas
    # layouts don't scroll, so the body::before stays inert.
    chrome_backdrop = "" if layout == "canvas" else f"""
body::before {{
  content: "";
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 54px;
  background: var(--paper);
  z-index: 4;
  pointer-events: none;
}}
body::after {{
  /* Soft fade-out below the strip so the edge isn't a hard line. */
  content: "";
  position: fixed;
  top: 54px; left: 0; right: 0;
  height: 18px;
  background: linear-gradient(to bottom, {p['paper']} 0%, {p['paper']}00 100%);
  z-index: 4;
  pointer-events: none;
}}
"""
    return f"""{_font_face_block()}

:root {{
  --paper:      {p['paper']};
  --paper-2:    {p['paper_2']};
  --paper-3:    {p['paper_3']};
  --hairline:   {p['hairline']};
  --hairline-2: {p['hairline_2']};
  --ink:        {p['ink']};
  --ink-95:     {p['ink_95']};
  --ink-80:     {p['ink_80']};
  --ink-60:     {p['ink_60']};
  --ink-40:     {p['ink_40']};
  --ink-25:     {p['ink_25']};

  --k-unit:              {p['k_unit']};
  --k-activity:          {p['k_activity']};
  --k-person:            {p['k_person']};
  --k-role:              {p['k_role']};
  --k-stakeholder:       {p['k_stakeholder']};
  --k-commitment:        {p['k_commitment']};
  --k-financial-summary: {p['k_financial_summary']};
  --k-identity:          {p['k_identity']};
  --k-language-term:     {p['k_language_term']};
  --k-source:            {p['k_source']};

  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
  font-feature-settings: "ss01", "cv11";
  font-variant-numeric: tabular-nums;
}}
* {{ box-sizing: border-box; }}
html, body {{ height: {body_height}; margin: 0; }}
body {{
  background: var(--paper);
  color: var(--ink);
  overflow: {body_overflow};
  overscroll-behavior: none;
  font-size: 13px;
  letter-spacing: -0.005em;
  -webkit-font-smoothing: antialiased;
  -webkit-tap-highlight-color: transparent;
  -webkit-user-select: none;
  user-select: none;
  touch-action: {body_touch};
}}
::selection {{ background: var(--ink); color: var(--paper); }}
.inspect, .modal, .scroll-paper {{ -webkit-user-select: text; user-select: text; }}
{chrome_backdrop}

/* ─── DATELINE — top-left, no border, hangs in space ──────────── */
.dateline {{
  position: fixed;
  top: max(22px, env(safe-area-inset-top));
  left: max(28px, calc(env(safe-area-inset-left) + 16px));
  z-index: 5;
  display: flex; align-items: baseline;
  gap: 12px;
  font-size: 13px;
  pointer-events: none;
  white-space: nowrap;
  max-width: calc(100vw - 260px);
  /* overflow:hidden + italic on .what was clipping the last glyph at the
     sub-pixel edge (italics extend slightly past their nominal box).
     Content is always short — no need to clip. */
  padding-right: 4px;
}}
.dateline > * {{ white-space: nowrap; }}
.dateline .org {{
  font-weight: 540;
  letter-spacing: -0.012em;
  font-size: 14px;
  color: var(--ink);
}}
.dateline .sep {{ color: var(--ink-25); }}
.dateline .what {{
  font-style: italic;
  color: var(--ink-60);
  font-weight: 380;
}}
.dateline .what em {{ font-style: normal; color: var(--ink-80); font-weight: 460; }}

.date-tr {{
  position: fixed;
  top: max(24px, calc(env(safe-area-inset-top) + 2px));
  /* Right offset reserves room for the optional "?" help button
     between the date and the Analysis CTA. When the help button is
     not rendered the slot stays empty — small visual gap, harmless. */
  right: calc(max(180px, env(safe-area-inset-right) + 170px));
  z-index: 5;
  font-size: 12px;
  font-style: italic;
  color: var(--ink-40);
  letter-spacing: -0.005em;
  white-space: nowrap;
}}
.date-tr em {{ font-style: normal; color: var(--ink-80); }}

/* ─── ANALYSIS BUTTON — top-right, the editorial CTA ──────────── */
.analysis {{
  position: fixed;
  top: max(16px, env(safe-area-inset-top));
  right: max(22px, calc(env(safe-area-inset-right) + 12px));
  z-index: 5;
  display: inline-flex; align-items: center;
  gap: 8px;
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--ink);
  cursor: pointer;
  padding: 8px 14px 9px;
  font: inherit;
  font-size: 13px;
  font-weight: 540;
  letter-spacing: -0.012em;
  border-radius: 4px;
  transition: background 0.15s ease, color 0.15s ease;
}}
.analysis:hover {{ background: var(--ink); color: var(--paper); }}
.analysis .arrow {{ font-size: 13px; color: var(--ink-60); transition: color 0.15s ease; }}
.analysis:hover .arrow {{ color: var(--paper); }}

/* ─── HELP "?" button — sits between date and Analysis CTA ────── */
.help-btn {{
  position: fixed;
  top: max(16px, env(safe-area-inset-top));
  /* Position inside the gap reserved by date-tr (which now sits at
     right ~ 180+) — Analysis is at right ~ 22-30; 132 lands us
     between them with breathing room. */
  right: calc(max(22px, env(safe-area-inset-right) + 12px) + 110px);
  z-index: 5;
  width: 30px; height: 30px;
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent;
  border: 1px solid var(--hairline);
  border-radius: 50%;
  color: var(--ink-60);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 540;
  font-family: ui-rounded, system-ui, sans-serif;
  line-height: 1;
  padding: 0;
  transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
}}
.help-btn:hover {{
  border-color: var(--ink);
  color: var(--ink);
  background: var(--paper-2);
}}
@media (max-width: 760px) {{
  /* Date-tr is hidden on phones (from the shared media query
     elsewhere in this file). Move the help button into its slot. */
  .help-btn {{
    right: calc(max(14px, env(safe-area-inset-right) + 8px) + 100px);
    top: max(14px, env(safe-area-inset-top));
  }}
}}

/* ─── ABOUT modal — opened by the "?" button ──────────────────── */
.about-scrim {{
  position: fixed; inset: 0;
  background: {p['modal_scrim']};
  display: none;
  align-items: flex-start; justify-content: center;
  z-index: 100;
  padding: 60px 20px;
  overflow-y: auto;
}}
.about-scrim.open {{ display: flex; }}
.about-card {{
  background: var(--paper);
  width: min(720px, 100%);
  border: 1px solid var(--hairline);
  border-radius: 3px;
  padding: 40px 56px 48px;
  position: relative;
}}
@media (max-width: 900px) {{
  .about-card {{ padding: 32px 28px 36px; }}
}}
.about-card .close {{
  position: absolute;
  top: 14px; right: 16px;
  background: transparent; border: 0;
  font: inherit; font-size: 18px;
  color: var(--ink-40);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 3px;
}}
.about-card .close:hover {{ background: var(--paper-2); color: var(--ink); }}
.about-card .kicker {{
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-60);
  font-weight: 500;
  margin-bottom: 14px;
}}
.about-card h1 {{
  font-size: 26px;
  font-weight: 540;
  letter-spacing: -0.022em;
  line-height: 1.15;
  margin: 0 0 16px;
  text-wrap: balance;
}}
.about-card .lede {{
  font-size: 15.5px;
  font-style: italic;
  color: var(--ink-95);
  line-height: 1.55;
  letter-spacing: -0.012em;
  margin: 0 0 22px;
  text-wrap: pretty;
}}
.about-card h2 {{
  font-size: 16px;
  font-weight: 540;
  letter-spacing: -0.014em;
  margin: 24px 0 8px;
}}
.about-card p {{
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--ink-95);
  margin: 0 0 12px;
  text-wrap: pretty;
}}

/* ─── TOOLTIP (hover, mouse-only) ─────────────────────────────── */
.tooltip {{
  position: fixed;
  pointer-events: none;
  background: var(--ink);
  color: var(--paper);
  font-size: 11px;
  padding: 4px 8px 5px;
  border-radius: 2px;
  letter-spacing: -0.005em;
  transform: translate(-50%, calc(-100% - 12px));
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.12s ease;
  z-index: 6;
}}
.tooltip.show {{ opacity: 1; }}
.tooltip .meta {{ font-style: italic; opacity: 0.55; margin-left: 6px; }}

/* ─── HINT — bottom-center primer, fades on first interaction ── */
.hint {{
  position: fixed;
  bottom: 64px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 4;
  font-size: 11.5px;
  font-style: italic;
  color: var(--ink-40);
  letter-spacing: -0.005em;
  white-space: nowrap;
  pointer-events: none;
  transition: opacity 0.5s ease;
}}
.hint.gone {{ opacity: 0; }}
.hint em {{ font-style: normal; color: var(--ink-60); }}

/* ─── COLOPHON — bottom strip, sits on the paper ──────────────── */
.colophon {{
  position: fixed;
  left: 0; right: 0; bottom: 0;
  z-index: 5;
  padding: 14px max(24px, env(safe-area-inset-right))
           max(18px, calc(env(safe-area-inset-bottom) + 12px))
           max(24px, env(safe-area-inset-left));
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 24px;
  pointer-events: none;
  background: linear-gradient(to bottom, transparent, var(--paper) 55%);
}}
.colophon > * {{ pointer-events: auto; }}
.colophon-meta {{
  font-size: 11px;
  font-style: italic;
  color: var(--ink-40);
  letter-spacing: -0.005em;
}}
.colophon-meta strong {{
  font-style: normal;
  color: var(--ink-80);
  font-weight: 540;
  font-variant-numeric: tabular-nums;
}}

/* ─── INSPECT — floating from right on focus (canvas mode) ────── */
.inspect {{
  position: fixed;
  top: 64px; right: 22px; bottom: 60px;
  width: 340px;
  max-width: calc(100vw - 44px);
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: 3px;
  padding: 22px 24px 24px;
  z-index: 6;
  overflow-y: auto;
  transform: translateX(calc(100% + 30px));
  opacity: 0;
  transition: transform 0.32s cubic-bezier(.2,.7,.2,1), opacity 0.2s ease;
}}
.inspect.open {{ transform: translateX(0); opacity: 1; }}
.inspect-head {{
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 4px;
}}
.inspect-eyebrow {{
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-60);
  font-weight: 500;
}}
.inspect-close {{
  margin-left: auto;
  background: transparent; border: 0;
  font: inherit; font-size: 16px;
  color: var(--ink-40);
  cursor: pointer;
  padding: 0 4px; line-height: 1;
}}
.inspect-close:hover {{ color: var(--ink); }}
.inspect .kind-tag {{
  display: inline-flex; align-items: center; gap: 7px;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-60);
  margin-top: 14px; margin-bottom: 6px;
}}
.inspect .kind-tag .swatch {{
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--tagcolor, var(--ink-40));
}}
.inspect h2 {{
  font-size: 21px;
  font-weight: 540;
  letter-spacing: -0.022em;
  line-height: 1.15;
  margin: 0 0 6px;
  text-wrap: pretty;
}}
.inspect .path {{
  font-size: 11px;
  color: var(--ink-40);
  font-style: italic;
  margin: 0 0 12px;
  word-break: break-all;
}}
.inspect .path em {{ font-style: normal; color: var(--ink-60); }}
.inspect .blurb {{
  font-size: 13px;
  color: var(--ink-95);
  line-height: 1.55;
  margin: 0 0 16px;
  text-wrap: pretty;
}}
.inspect .blurb p {{ margin: 0 0 8px; }}
.inspect .blurb p:last-child {{ margin-bottom: 0; }}
/* Inline links inside the blurb (from inline_md() at build time). Same
   register as the Analysis-modal anchors: subtle hairline underline,
   ink on hover. The data-focus variant clicks back to setFocus on the
   canvas. Plain hrefs (external URLs) inherit the same look so the
   blurb reads consistently. */
.inspect .blurb a {{
  color: var(--ink-60);
  text-decoration: none;
  border-bottom: 0.5px solid var(--ink-25);
  cursor: pointer;
}}
.inspect .blurb a:hover {{
  color: var(--ink);
  border-bottom-color: var(--ink);
}}
.inspect .blurb strong {{ font-weight: 500; color: var(--ink); }}
.inspect .blurb em {{ font-style: italic; }}
.inspect .blurb code {{
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--surface-2);
  padding: 1px 4px;
  border-radius: 3px;
}}
.rel-group {{
  margin-top: 14px;
  border-top: 1px solid var(--hairline-2);
  padding-top: 12px;
}}
.rel-group h3 {{
  margin: 0 0 6px;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-60);
  font-weight: 500;
  display: flex; align-items: baseline; gap: 6px;
}}
.rel-group h3 .count {{
  font-size: 10px;
  color: var(--ink-25);
  letter-spacing: 0;
  text-transform: none;
  font-style: italic;
}}
.rel-verb {{
  display: flex; align-items: baseline; justify-content: space-between;
  font-size: 11px;
  font-style: italic;
  color: var(--ink-60);
  padding: 12px 0 4px;
  letter-spacing: -0.005em;
}}
.rel-verb:first-of-type {{ padding-top: 6px; }}
.rel-verb-count {{
  font-size: 10px;
  color: var(--ink-25);
  font-variant-numeric: tabular-nums;
  font-style: italic;
}}
.rel {{
  display: grid;
  grid-template-columns: 14px 1fr;
  align-items: center;
  gap: 8px;
  padding: 4px 4px 4px 0;
  border-radius: 2px;
  cursor: pointer;
  font-size: 12.5px;
}}
.rel:hover {{ background: var(--paper-2); }}
.rel .swatch {{ width: 7px; height: 7px; border-radius: 50%; margin-left: 4px; }}
.rel .name {{
  color: var(--ink-95);
  letter-spacing: -0.005em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.rel-empty {{
  font-size: 11px;
  color: var(--ink-25);
  font-style: italic;
  padding: 4px 0;
}}

/* ─── MODAL — Analysis (editorial, single column) ─────────────── */
.modal-scrim {{
  position: fixed; inset: 0;
  background: {p['modal_scrim']};
  display: none;
  align-items: flex-start; justify-content: center;
  z-index: 100;
  padding: 60px 20px;
  overflow-y: auto;
}}
.modal-scrim.open {{ display: flex; }}
.modal {{
  background: var(--paper);
  width: min(720px, 100%);
  border: 1px solid var(--hairline);
  border-radius: 3px;
  padding: 40px 56px 48px;
  position: relative;
}}
.modal .close {{
  position: absolute;
  top: 14px; right: 16px;
  background: transparent; border: 0;
  font: inherit; font-size: 18px;
  color: var(--ink-40);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 3px;
}}
.modal .close:hover {{ background: var(--paper-2); color: var(--ink); }}
.modal .kicker {{
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-60);
  font-weight: 500;
  margin-bottom: 14px;
}}
.modal h1 {{
  font-size: 30px;
  font-weight: 540;
  letter-spacing: -0.025em;
  line-height: 1.12;
  margin: 0 0 12px;
  text-wrap: balance;
}}
.modal .dateline-modal {{
  font-style: italic;
  color: var(--ink-40);
  font-size: 12px;
  margin-bottom: 24px;
}}
.modal .dateline-modal em {{ font-style: normal; color: var(--ink-60); }}
.modal .lede {{
  font-size: 17px;
  font-style: italic;
  color: var(--ink-95);
  line-height: 1.5;
  letter-spacing: -0.012em;
  margin: 0 0 28px;
  text-wrap: pretty;
}}
.modal .lede em {{ font-style: normal; color: var(--ink); font-weight: 540; }}
.decisions {{ list-style: none; padding: 0; margin: 0 0 8px; counter-reset: dec; }}
.decisions li {{
  counter-increment: dec;
  padding: 20px 0 22px 64px;
  border-top: 1px solid var(--hairline-2);
  position: relative;
}}
.decisions li::before {{
  content: counter(dec, decimal-leading-zero);
  position: absolute;
  left: 0; top: 22px;
  font-size: 12px;
  color: var(--ink-40);
  font-style: italic;
}}
.decisions h3 {{
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 540;
  letter-spacing: -0.012em;
  color: var(--ink);
  line-height: 1.3;
  text-wrap: pretty;
}}
.decisions p {{
  margin: 0 0 10px;
  color: var(--ink-95);
  font-size: 14px;
  line-height: 1.6;
  text-wrap: pretty;
}}
.decisions .source {{
  font-size: 11px;
  color: var(--ink-40);
  font-style: italic;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  margin: 0 0 8px;
  word-break: break-all;
}}
.decisions .anchor {{
  display: inline-block;
  font-size: 12px;
  color: var(--ink-60);
  font-style: italic;
  cursor: pointer;
  border-bottom: 0.5px solid var(--ink-25);
  padding-bottom: 1px;
}}
.decisions .anchor:hover {{ color: var(--ink); border-bottom-color: var(--ink); }}
.decisions .anchor em {{ font-style: normal; color: var(--ink); font-weight: 500; }}
/* Catchall: any <a> inside a decision answer paragraph wears the
   editorial register, never the browser default blue underline. The
   .anchor class arrives when inline_md() resolved an internal node;
   the plain <a> arrives when the link target was an external URL or
   an unresolved internal one. Both render the same way visually so
   readers don't see an inconsistent "some links are blue, some
   aren't" pattern. */
.decisions p a,
.decisions p a.anchor {{
  display: inline;
  font-size: inherit;
  font-style: normal;
  color: var(--ink-60);
  text-decoration: none;
  border-bottom: 0.5px solid var(--ink-25);
  padding-bottom: 0;
  cursor: pointer;
}}
.decisions p a:hover,
.decisions p a.anchor:hover {{
  color: var(--ink);
  border-bottom-color: var(--ink);
}}
.modal-foot {{
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--hairline-2);
  font-size: 11.5px;
  color: var(--ink-60);
  font-style: italic;
  line-height: 1.55;
}}
.modal-foot em {{ font-style: normal; color: var(--ink-80); }}

/* ─── SCROLL-ON-PAPER — for ai-exposure / reshuffle / world-model ── */
.scroll-paper {{
  max-width: 720px;
  margin: 0 auto;
  padding: max(80px, calc(env(safe-area-inset-top) + 64px))
           max(28px, env(safe-area-inset-right))
           max(96px, calc(env(safe-area-inset-bottom) + 80px))
           max(28px, env(safe-area-inset-left));
}}
.scroll-paper h1 {{
  font-size: 30px;
  font-weight: 540;
  letter-spacing: -0.025em;
  line-height: 1.12;
  margin: 0 0 12px;
  text-wrap: balance;
}}
.scroll-paper h2 {{
  font-size: 19px;
  font-weight: 540;
  letter-spacing: -0.018em;
  line-height: 1.2;
  margin: 36px 0 10px;
  text-wrap: pretty;
}}
.scroll-paper h3 {{
  font-size: 14.5px;
  font-weight: 540;
  letter-spacing: -0.012em;
  margin: 22px 0 6px;
}}
.scroll-paper p {{
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-95);
  margin: 0 0 12px;
  text-wrap: pretty;
}}
.scroll-paper .lede {{
  font-style: italic;
  font-size: 17px;
  color: var(--ink-95);
  line-height: 1.5;
  margin: 0 0 28px;
}}
.scroll-paper .lede em {{ font-style: normal; color: var(--ink); font-weight: 540; }}
.scroll-paper .kicker {{
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-60);
  font-weight: 500;
  margin-bottom: 14px;
}}
.scroll-paper hr {{
  border: 0;
  border-top: 1px solid var(--hairline-2);
  margin: 28px 0;
}}

/* ─── RESPONSIVE squeeze ──────────────────────────────────────── */
@media (max-width: 900px) {{
  .inspect {{ width: calc(100vw - 44px); top: 56px; }}
  .modal {{ padding: 32px 28px 36px; }}
  .modal h1 {{ font-size: 24px; }}
  .scroll-paper {{ padding-left: 22px; padding-right: 22px; }}
  .scroll-paper h1 {{ font-size: 24px; }}
}}
@media (max-width: 760px) {{
  .dateline {{
    left: max(18px, calc(env(safe-area-inset-left) + 12px));
    top: max(18px, env(safe-area-inset-top));
    max-width: calc(100vw - 170px);
    font-size: 12px;
  }}
  .dateline .org {{ font-size: 13px; }}
  .dateline .what {{ display: none; }}
  .analysis {{
    right: max(14px, calc(env(safe-area-inset-right) + 8px));
    top: max(14px, env(safe-area-inset-top));
    padding: 9px 13px 10px;
    font-size: 12.5px;
  }}
  .colophon {{
    padding: 10px max(12px, env(safe-area-inset-right))
             max(14px, calc(env(safe-area-inset-bottom) + 8px))
             max(12px, env(safe-area-inset-left));
    gap: 10px;
  }}
  .date-tr {{ display: none; }}
  .hint {{
    font-size: 11px;
    bottom: calc(96px + env(safe-area-inset-bottom));
    white-space: normal;
    max-width: calc(100vw - 32px);
    line-height: 1.4;
    text-align: center;
    left: 16px; right: 16px;
    transform: none;
  }}
  .inspect {{
    top: max(58px, calc(env(safe-area-inset-top) + 50px));
    bottom: calc(72px + env(safe-area-inset-bottom));
    right: 14px; left: 14px;
    width: auto;
    max-width: none;
    padding: 18px 18px 20px;
  }}
  .inspect h2 {{ font-size: 19px; }}
  .inspect-close {{ padding: 8px 10px; font-size: 20px; }}
}}
"""


def app_pure_dateline_html(org_name: str, what: str = "the operational <em>structure</em>") -> str:
    """Top-left dateline. `what` accepts inline HTML (italic + emphasis)."""
    return (
        f'<div class="dateline">\n'
        f'  <span class="org">{escape(org_name)}</span>\n'
        f'  <span class="sep">/</span>\n'
        f'  <span class="what">{what}</span>\n'
        f'</div>'
    )


def app_pure_top_right_html(
    dated: str,
    *,
    show_analysis: bool = True,
    show_help: bool = False,
    analysis_label: str = "Analysis",
    help_label: str = "What is this map?",
) -> str:
    """Top-right: italic date + optional outline `?` help button +
    optional outline Analysis CTA. Click handlers are wired in JS
    (button ids: `open-help`, `open-analysis`).

    `analysis_label` and `help_label` exist so viewers can localize
    the chrome (the public template defaults are English; AIRC and
    other Italian forks pass the Italian equivalent)."""
    out = f'<div class="date-tr"><em>{escape(dated)}</em></div>'
    if show_help:
        out += (
            '\n<button class="help-btn" id="open-help" type="button" '
            f'aria-label="{escape(help_label)}" title="{escape(help_label)}">'
            '?'
            '</button>'
        )
    if show_analysis:
        out += (
            '\n<button class="analysis" id="open-analysis" type="button">'
            f'{escape(analysis_label)}'
            '<span class="arrow">→</span>'
            '</button>'
        )
    return out


def app_pure_about_modal_html(
    *,
    kicker: str,
    headline: str,
    lede: str,
    body_html: str,
) -> str:
    """About / "what is this map" modal. Triggered by the `?` button
    (id: `open-help`). Renders kicker + headline + lede + caller's
    body HTML. Closed by clicking the scrim, the × button, or Esc.

    `body_html` accepts inline HTML — typically the playbook's
    intro paragraphs, legend, and any orientation aids."""
    return f"""<div class="about-scrim" id="about-scrim">
  <article class="about-card" role="dialog" aria-modal="true" aria-labelledby="about-title">
    <button class="close" id="about-close" aria-label="Close">×</button>
    <p class="kicker">{escape(kicker)}</p>
    <h1 id="about-title">{escape(headline)}</h1>
    {f'<p class="lede">{lede}</p>' if lede else ''}
    {body_html}
  </article>
</div>"""


def app_pure_inspect_aside_html(
    *,
    eyebrow_label: str = "Inspect",
    close_title: str = "Reset focus",
) -> str:
    """Floating Inspect card (right side). Body is empty — populated
    by the playbook's JS via document.getElementById('inspect-body').

    `eyebrow_label` and `close_title` exist so localized viewers can
    pass the right strings."""
    return (
        '<aside class="inspect" id="inspect">\n'
        '  <div class="inspect-head">\n'
        f'    <span class="inspect-eyebrow">{escape(eyebrow_label)}</span>\n'
        f'    <button class="inspect-close" id="inspect-close" title="{escape(close_title)}">×</button>\n'
        '  </div>\n'
        '  <div id="inspect-body"></div>\n'
        '</aside>'
    )


def app_pure_modal_html(
    *,
    headline: str,
    org_name: str,
    dated: str,
    decisions_html: str,
    kicker: str = "Reading the structure",
    lede: str = "",
    body_html: str = "",
    foot_text: str = "",
) -> str:
    """Analysis modal. `decisions_html` is the contents of an <ol class='decisions'>;
    each <li> typically has <h3>question</h3><p>answer</p><span class='anchor'
    data-focus='node-id'>show <em>X</em> on the canvas →</span>.

    `lede` accepts inline HTML for emphasis (`<em>...</em>` becomes the
    "named" register inside the lede paragraph).

    `body_html` is rendered between the lede and the <ol> of decisions —
    used by viewers (e.g. reshuffle) that want to put a section of named
    candidates above the decisions list.

    `foot_text` accepts inline HTML; defaults to a generic provenance line.
    """
    if not foot_text:
        foot_text = (
            f"Read from the artefact at <em>{escape(dated)}</em>. "
            "Each decision points to the part of the structure that produced it; "
            "click an anchor to dim the rest of the picture and see the local "
            "neighbourhood."
        )
    # Build the article body as a list of non-empty sections so empty
    # parameters (lede or body_html) don't leak blank indented lines into
    # the output. Output is deterministic — same inputs produce the same
    # bytes — which the design-regression suite relies on.
    sections: list[str] = [
        f'<button class="close" id="modal-close" aria-label="Close">×</button>',
        f'<p class="kicker">{escape(kicker)}</p>',
        f'<h1 id="analysis-title">{escape(headline)}</h1>',
        f'<p class="dateline-modal"><em>{escape(org_name)}</em> · structure dated {escape(dated)}</p>',
    ]
    if lede:
        sections.append(f'<p class="lede">{lede}</p>')
    if body_html:
        sections.append(body_html)
    if decisions_html:
        sections.append(f'<ol class="decisions">{decisions_html}</ol>')
    sections.append(f'<p class="modal-foot">{foot_text}</p>')
    article_body = "\n    ".join(sections)
    return f"""<div class="modal-scrim" id="modal-scrim">
  <article class="modal" role="dialog" aria-modal="true" aria-labelledby="analysis-title">
    {article_body}
  </article>
</div>"""


def app_pure_baseline_js() -> str:
    """Shared JS: modal open/close + Esc + ?-shortcut + ?focus URL
    permalink. Each viewer concatenates its playbook-specific JS
    (force simulation, hover handlers, etc) after this baseline.

    Expects in the DOM: `#open-analysis`, `#modal-scrim`, `#modal-close`,
    optionally a `setFocus(id)` function defined by the playbook (used
    by the modal's "show on canvas →" anchors).
    """
    return r"""
// ── About modal: open / close / Esc ────────────────────────────
// Triggered by the "?" button (id: open-help). Holds the
// "what is this map / how to read it" content the viewer used
// to put inline at the top of the page.
(function() {
  const scrim = document.getElementById('about-scrim');
  const openBtn = document.getElementById('open-help');
  const closeBtn = document.getElementById('about-close');
  if (!scrim) return;
  function open()  { scrim.classList.add('open');    scrim.setAttribute('aria-hidden', 'false'); }
  function close() { scrim.classList.remove('open'); scrim.setAttribute('aria-hidden', 'true'); }
  if (openBtn)  openBtn.addEventListener('click', open);
  if (closeBtn) closeBtn.addEventListener('click', close);
  scrim.addEventListener('click', (ev) => { if (ev.target === scrim) close(); });
  window.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && scrim.classList.contains('open')) close();
  });
})();

// ── Analysis modal: open / close / Esc / "?" shortcut ──────────
(function() {
  const scrim = document.getElementById('modal-scrim');
  const openBtn = document.getElementById('open-analysis');
  const closeBtn = document.getElementById('modal-close');
  if (!scrim) return;
  function open()  { scrim.classList.add('open');    scrim.setAttribute('aria-hidden', 'false'); }
  function close() { scrim.classList.remove('open'); scrim.setAttribute('aria-hidden', 'true'); }
  if (openBtn)  openBtn.addEventListener('click', open);
  if (closeBtn) closeBtn.addEventListener('click', close);
  scrim.addEventListener('click', (ev) => { if (ev.target === scrim) close(); });
  window.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' && scrim.classList.contains('open')) { close(); return; }
    if (ev.key === '?' || (ev.shiftKey && ev.key === '/')) { if (openBtn) openBtn.click(); }
  });
  // "show on canvas →" anchors: close the modal, then call setFocus
  // if the viewer defined it. Some viewers (scroll-on-paper) don't.
  scrim.querySelectorAll('.anchor[data-focus]').forEach((a) => {
    a.addEventListener('click', () => {
      close();
      if (typeof window.setFocus === 'function') window.setFocus(a.dataset.focus);
    });
  });
  // ?focus=<id> URL parameter — permalink to a focused node. Run on
  // load with a small delay so the playbook's force sim has time to
  // settle before we recentre.
  try {
    const params = new URLSearchParams(location.search);
    const initial = params.get('focus');
    if (initial) {
      setTimeout(() => {
        if (typeof window.setFocus === 'function') window.setFocus(initial);
      }, 200);
    }
  } catch (_) { /* URL parsing failure → ignore */ }
})();
"""
