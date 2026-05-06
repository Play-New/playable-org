"""
Playable Org · design system

Single source of truth for the visual language of every playbook viewer.
Tokens, primitives, helper functions — all in one module.

Convention: viewers compose primitives, never write inline CSS. This module
is the only place where typography, spacing, color, and layout decisions
live. Update once, every viewer follows.

Public API:

    from design import (
        base_css,
        shell, header, rule, footer,
        section,
        stat_grid,
        pill,
        item_list, item,
        card_grid, card,
    )

The `base_css()` string already contains an `@font-face` block for Inter
Variable (with `opsz` axis), embedded as a base64 data URL so the rendered
HTML is fully offline-portable.
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
    """`@font-face` for Inter Variable with both `wght` and `opsz` axes.

    Falls back to system sans if the woff2 is not present (e.g. dev mode).
    """
    data_url = _font_data_url()
    if not data_url:
        return ""
    return f"""@font-face {{
  font-family: 'Inter';
  src: url('{data_url}') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
}}"""


# ----------------------------------------------------------------------
# Tokens + primitives CSS
# ----------------------------------------------------------------------

def _base_css() -> str:
    """Tokens + every primitive class. ~5KB once font is excluded."""
    return f"""{_font_face_block()}

:root {{
  /* Colour tokens — monochrome with state accents only */
  --fg: #1a1a1a;
  --muted: #6b6b6b;
  --soft: #999999;
  --line: #e5e5e5;
  --bg: #ffffff;
  --bg-soft: #fafafa;

  --warn: #c47558;
  --warn-bg: #fbf2eb;
  --error: #b91c1c;
  --error-bg: #fef2f2;
  --success: #047857;
  --success-bg: #ecfdf5;
  --info: #2563eb;
  --info-bg: #eff6ff;

  /* Spacing scale (4px base) */
  --s-1: 4px;
  --s-2: 8px;
  --s-3: 12px;
  --s-4: 16px;
  --s-5: 20px;
  --s-6: 24px;
  --s-7: 32px;
  --s-8: 40px;
  --s-9: 48px;
  --s-10: 64px;
  --s-11: 80px;
}}

* {{ box-sizing: border-box; }}

html, body {{
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-feature-settings: 'cv11', 'ss01';
  font-optical-sizing: auto;
  -webkit-font-smoothing: antialiased;
  line-height: 1.55;
  font-size: 15px;
}}

a {{ color: inherit; text-underline-offset: 2px; }}
a:hover {{ color: var(--muted); }}

button {{
  font-family: inherit;
  cursor: pointer;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--fg);
  padding: var(--s-2) var(--s-4);
  border-radius: 3px;
  font-size: 0.85rem;
}}
button:hover {{ background: var(--bg-soft); }}

:focus-visible {{ outline: 2px solid var(--fg); outline-offset: 2px; }}

/* ------------------------------------------------------------------
   Layout primitives
   ------------------------------------------------------------------ */

.pn-shell {{
  max-width: 1100px;
  margin: 0 auto;
  padding: var(--s-10) var(--s-8) var(--s-11);
}}

.pn-rule {{
  height: 1px;
  background: var(--line);
  border: none;
  margin: var(--s-9) 0 var(--s-7);
}}

/* ------------------------------------------------------------------
   Header
   ------------------------------------------------------------------ */

.pn-header {{ margin-bottom: var(--s-9); }}
.pn-header__eyebrow {{
  font-size: 0.72rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--soft);
  margin-bottom: var(--s-4);
}}
.pn-header__title {{
  font-size: 2.4rem;
  font-weight: 500;
  letter-spacing: -0.025em;
  line-height: 1.1;
  margin: 0;
}}
.pn-header__sub {{
  margin-top: var(--s-3);
  color: var(--muted);
  font-size: 0.95rem;
  max-width: 640px;
}}

/* ------------------------------------------------------------------
   Section header
   ------------------------------------------------------------------ */

.pn-section {{
  display: flex;
  align-items: baseline;
  gap: var(--s-5);
  margin-bottom: var(--s-7);
}}
.pn-section__num {{
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--soft);
  letter-spacing: 0.05em;
  font-variant-numeric: tabular-nums;
}}
.pn-section__title {{
  font-size: 0.78rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--fg);
}}
.pn-section__hint {{
  margin-left: auto;
  font-size: 0.78rem;
  color: var(--soft);
}}

/* ------------------------------------------------------------------
   Stat grid
   ------------------------------------------------------------------ */

.pn-stat {{
  padding: var(--s-7);
}}
.pn-stat__num {{
  font-size: 2.8rem;
  font-weight: 400;
  line-height: 1;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
  color: var(--fg);
  margin-bottom: var(--s-5);
}}
.pn-stat__lab {{
  font-size: 0.72rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--muted);
}}

.pn-stat-grid {{
  display: grid;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}}
.pn-stat-grid--4 {{ grid-template-columns: repeat(4, 1fr); }}
.pn-stat-grid--3 {{ grid-template-columns: repeat(3, 1fr); }}
.pn-stat-grid--2 {{ grid-template-columns: repeat(2, 1fr); }}

.pn-stat-grid > .pn-stat {{ border-right: 1px solid var(--line); }}
.pn-stat-grid--4 > .pn-stat:nth-child(4n+1) {{ padding-left: 0; }}
.pn-stat-grid--4 > .pn-stat:nth-child(4n)   {{ padding-right: 0; border-right: none; }}
.pn-stat-grid--3 > .pn-stat:nth-child(3n+1) {{ padding-left: 0; }}
.pn-stat-grid--3 > .pn-stat:nth-child(3n)   {{ padding-right: 0; border-right: none; }}
.pn-stat-grid--2 > .pn-stat:nth-child(2n+1) {{ padding-left: 0; }}
.pn-stat-grid--2 > .pn-stat:nth-child(2n)   {{ padding-right: 0; border-right: none; }}
.pn-stat-grid--4 > .pn-stat:nth-child(n+5) {{ border-top: 1px solid var(--line); }}
.pn-stat-grid--3 > .pn-stat:nth-child(n+4) {{ border-top: 1px solid var(--line); }}
.pn-stat-grid--2 > .pn-stat:nth-child(n+3) {{ border-top: 1px solid var(--line); }}

/* ------------------------------------------------------------------
   Pill / code
   ------------------------------------------------------------------ */

.pn-pill {{
  display: inline-flex;
  align-items: center;
  font-size: 0.66rem;
  font-weight: 500;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  padding: 2px var(--s-2);
  border-radius: 3px;
  line-height: 1.5;
}}
.pn-pill--neutral {{ background: var(--bg-soft);    color: var(--muted); }}
.pn-pill--error   {{ background: var(--error-bg);   color: var(--error); }}
.pn-pill--warn    {{ background: var(--warn-bg);    color: var(--warn); }}
.pn-pill--ok      {{ background: var(--success-bg); color: var(--success); }}
.pn-pill--info    {{ background: var(--info-bg);    color: var(--info); }}

.pn-code {{
  font-family: ui-monospace, 'SF Mono', Menlo, monospace;
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}}

/* ------------------------------------------------------------------
   Item list (issues / activities / signals)
   ------------------------------------------------------------------ */

.pn-item-list {{ display: flex; flex-direction: column; }}
.pn-item {{
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: var(--s-7);
  padding: var(--s-6) 0;
  border-bottom: 1px solid var(--line);
}}
.pn-item:last-child {{ border-bottom: none; }}
.pn-item__meta {{
  display: flex;
  align-items: flex-start;
  gap: var(--s-2);
  flex-wrap: wrap;
}}
.pn-item__head {{ font-size: 0.95rem; font-weight: 500; margin-bottom: var(--s-2); }}
.pn-item__body {{ font-size: 0.9rem; color: var(--muted); line-height: 1.6; }}
.pn-item__refs {{
  margin-top: var(--s-3);
  font-family: ui-monospace, 'SF Mono', Menlo, monospace;
  font-size: 0.78rem;
  color: var(--soft);
}}

/* ------------------------------------------------------------------
   Card grid (capabilities / components)
   ------------------------------------------------------------------ */

.pn-card-grid {{ display: grid; border-top: 1px solid var(--line); }}
.pn-card-grid--2 {{ grid-template-columns: repeat(2, 1fr); }}
.pn-card-grid--1 {{ grid-template-columns: 1fr; }}

.pn-card {{
  padding: var(--s-6) var(--s-7);
  border-bottom: 1px solid var(--line);
  border-right: 1px solid var(--line);
  cursor: pointer;
  transition: background 0.15s ease;
}}
.pn-card:hover {{ background: var(--bg-soft); }}
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
  font-family: ui-monospace, 'SF Mono', Menlo, monospace;
  font-size: 0.88rem;
  font-weight: 500;
  letter-spacing: -0.005em;
  color: var(--fg);
}}
.pn-card__tag {{
  font-size: 0.66rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}}
.pn-card__tag--accent {{ color: var(--warn); }}
.pn-card__desc {{
  font-size: 0.88rem;
  color: var(--muted);
  line-height: 1.55;
  margin-bottom: var(--s-3);
}}
.pn-card__meta {{
  display: flex;
  gap: var(--s-4);
  font-size: 0.74rem;
  color: var(--soft);
  font-variant-numeric: tabular-nums;
  flex-wrap: wrap;
}}

/* ------------------------------------------------------------------
   Footer
   ------------------------------------------------------------------ */

.pn-footer {{
  margin-top: var(--s-11);
  padding-top: var(--s-6);
  border-top: 1px solid var(--line);
  font-size: 0.78rem;
  color: var(--soft);
  display: flex;
  justify-content: space-between;
}}

/* ------------------------------------------------------------------
   Modal (used by playbook viewers for click-to-detail)
   ------------------------------------------------------------------ */

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
.pn-modal-backdrop.is-open {{ display: flex; }}

.pn-modal {{
  background: var(--bg);
  border: 1px solid var(--line);
  width: 100%;
  max-width: 720px;
  padding: var(--s-7) var(--s-8) var(--s-8);
}}
.pn-modal__close {{
  float: right;
  background: transparent;
  border: 0;
  font-size: 1.4rem;
  line-height: 1;
  color: var(--muted);
  padding: 0;
  margin-left: var(--s-3);
}}
.pn-modal__close:hover {{ color: var(--fg); background: transparent; }}
.pn-modal__title {{
  font-size: 1.4rem;
  font-weight: 500;
  letter-spacing: -0.02em;
  margin: 0 0 var(--s-4);
}}
.pn-modal__field {{ margin: var(--s-4) 0; }}
.pn-modal__field-label {{
  font-size: 0.72rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--soft);
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
