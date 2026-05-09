"""
Playable Org · design system

Single source of truth for the visual language of every playbook viewer.
Tokens, primitives, helper functions — all in one module.

Convention: viewers compose primitives, never write inline CSS. This module
is the only place where typography, spacing, color, and layout decisions
live. Update once, every viewer follows.

Visual version: 4
- v1: Inter Variable + monochrome-with-state-accents (#1a1a1a / #e5e5e5).
- v2: Mirage variable + Play New pure monochrome. Rolled back —
  Klim Type Foundry's standard Mirage license does not permit public
  redistribution; the public template ships with the open-licensed
  Inter Variable instead, and forks can swap in their own brand font
  by replacing `_assets/fonts/inter-variable.woff2`.
- v3: Inter Variable + Play New monochrome + a small pastel data-viz
  palette (--ds-sage / --ds-lilac / --ds-slate / --ds-sand / --ds-coral)
  for heatmaps, stage bands, category swatches, category differentiation.
- v4 (current): editorial direction taken from Giorgia Lupi / Accurat /
  Federica Fragapane / Density Design — Italianate masthead pattern,
  numbered-section register, disclosed grid, marginalia, custom
  geometric marks per data kind, 5-stop colour scales per hue with
  glow variants, surface tokens (paper / inset-dark / raised), motion
  tokens for cascading entry, and a colophon footer pattern. See
  `docs/design-direction.md` for the brief and references.
  All v3 tokens remain; v4 is additive.

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
