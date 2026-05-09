#!/usr/bin/env python3
"""
tools/screenshot-viewers.py — capture hero PNGs of every sample-org
viewer, for embedding in README.md.

Usage:
    python3 tools/screenshot-viewers.py

Outputs:
    docs/screenshots/{graph,value-map,reshuffle,world-model,ai-exposure}.png

Requires:
    pip install playwright && playwright install chromium
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print(
        "Playwright not installed. Run: pip install playwright && "
        "playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data"
OUT_DIR = REPO_ROOT / "docs" / "screenshots"

# Each tuple: (filename without extension, source HTML, viewport, full_page)
SHOTS = [
    ("graph",        "graph-outline-2026-05-09.html",                                 (1440, 1100), False),
    ("value-map",    "value-map-studio-mid-market-baseline-2026-05-07.html",          (1440, 1200), False),
    ("reshuffle",    "reshuffle-outline-2026-05-07.html",                             (1440, 1200), False),
    ("world-model",  "world-model-outline-2026-05-07.html",                           (1440, 1400), False),
    ("ai-exposure",  "ai-exposure-outline-2026-05-07.html",                           (1440, 1100), False),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, src, (vw, vh), full_page in SHOTS:
            html_path = DATA_DIR / src
            if not html_path.exists():
                print(f"skip {name}: {html_path} missing", file=sys.stderr)
                continue
            ctx = browser.new_context(viewport={"width": vw, "height": vh},
                                      device_scale_factor=2)
            page = ctx.new_page()
            page.goto(f"file://{html_path}")
            # Give JS layouts (force simulation, etc.) a moment to settle.
            page.wait_for_timeout(800)
            out = OUT_DIR / f"{name}.png"
            page.screenshot(path=str(out), full_page=full_page)
            ctx.close()
            print(f"  wrote {out.relative_to(REPO_ROOT)} ({vw}×{vh}@2x)")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
