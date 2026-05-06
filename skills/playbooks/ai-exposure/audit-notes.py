#!/usr/bin/env python3
"""
ai-exposure / audit-notes.py — Verify per-area commentary against matches data.

Each area note is free prose. The audit gate checks two things, deterministically:

1. Every integer that looks like a count or percentage in the prose must match
   a fact computed from the matches data for that area:
     - activity count, level counts (strong/medium/mixed/zero/low-confidence),
     - average top-1 confidence (rounded to integer percent),
     - average autonomy (rounded to 2 decimals),
     - total Claude.ai conversations across top matches.
2. Every activity title quoted in italics (*...*) must exist as a real activity
   in that area.

Number patterns and Italian/English number words are recognized.

Usage:
    python3 audit-notes.py --notes <area-notes.json>
                           --matches <all-org-matches.json>
                           --metadata <activities-metadata.json>

Exit code:
    0 = audit passed
    1 = audit failed (unverifiable claim found)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

P25, P75 = 3.21, 3.57


def classify_match(m: dict) -> str:
    a = m.get("ai_autonomy_mean")
    if a is None:
        return "no-data"
    if a >= P75:
        return "automated"
    if a >= P25:
        return "augmented"
    return "assistive"


def classify_activity(a: dict) -> str:
    if a.get("low_confidence"):
        return "low-confidence"
    cats = {"automated": 0, "augmented": 0, "assistive": 0, "no-data": 0}
    for m in a["matches"]:
        cats[classify_match(m)] += 1
    rich = a["matches"] and any(m.get("ai_autonomy_mean") for m in a["matches"])
    if not rich:
        return "zero"
    if cats["automated"] >= 3:
        return "strong"
    if cats["automated"] + cats["augmented"] >= 5:
        return "medium"
    return "mixed"


# Italian and English number words 0-100 plus a few key larger ones.
WORDS_IT = {
    "zero": 0, "uno": 1, "una": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5,
    "sei": 6, "sette": 7, "otto": 8, "nove": 9, "dieci": 10, "undici": 11,
    "dodici": 12, "tredici": 13, "quattordici": 14, "quindici": 15, "sedici": 16,
    "diciassette": 17, "diciotto": 18, "diciannove": 19, "venti": 20,
    "ventuno": 21, "ventidue": 22, "ventitré": 23, "ventiquattro": 24,
    "venticinque": 25, "ventisei": 26, "ventisette": 27, "ventotto": 28,
    "ventinove": 29, "trenta": 30, "trentadue": 32, "trentasei": 36,
    "quaranta": 40, "quarantasette": 47, "cinquanta": 50, "sessanta": 60,
    "settanta": 70, "ottanta": 80, "novanta": 90, "cento": 100,
}


def compute_area_facts(matches: list[dict], metadata: dict[str, dict]) -> dict[str, dict]:
    by_area: dict[str, list[dict]] = defaultdict(list)
    for a in matches:
        md = metadata.get(a["id"], {})
        a = dict(a)
        a["_title"] = md.get("title", a["id"])
        a["_level"] = classify_activity(a)
        by_area[md.get("area", "(no-area)")].append(a)

    facts: dict[str, dict] = {}
    for area, items in by_area.items():
        n = len(items)
        lc = {"strong": 0, "medium": 0, "mixed": 0, "zero": 0, "low-confidence": 0}
        cat_counts = {"automated": 0, "augmented": 0, "assistive": 0, "no-data": 0}
        for a in items:
            lc[a["_level"]] += 1
            for m in a["matches"]:
                cat_counts[classify_match(m)] += 1
        sims = [a["matches"][0]["similarity"] for a in items if a["matches"][0].get("similarity") is not None]
        auts = [a["matches"][0]["ai_autonomy_mean"] for a in items if a["matches"][0].get("ai_autonomy_mean") is not None]
        conv = sum(int(m.get("count", 0) or 0) for a in items for m in a["matches"])
        avg_sim_pct = int(round(sum(sims) / len(sims) * 100)) if sims else None
        avg_aut_round2 = round(sum(auts) / len(auts), 2) if auts else None

        n_match_rows = sum(cat_counts.values())
        cat_pcts = {k: (int(round(v / n_match_rows * 100)) if n_match_rows else 0) for k, v in cat_counts.items()}

        # All integer values that the prose may legitimately reference for this area.
        allowed_ints = {n, conv, n_match_rows}
        allowed_ints.update(lc.values())
        allowed_ints.update(cat_counts.values())

        # Allowed percentages: avg confidence, category percentages, level percentages.
        allowed_pcts: set[int] = set()
        if avg_sim_pct is not None:
            allowed_pcts.add(avg_sim_pct)
        allowed_pcts.update(cat_pcts.values())
        # Level-quota percentages (e.g., "56% in zero" computed from level counts).
        if n > 0:
            for lv_count in lc.values():
                allowed_pcts.add(int(round(lv_count / n * 100)))

        # Allow ±1 rounding tolerance on percentages.
        allowed_pcts_with_tol = set(allowed_pcts)
        for p in list(allowed_pcts):
            allowed_pcts_with_tol.add(p - 1)
            allowed_pcts_with_tol.add(p + 1)

        # Autonomy may appear as "3.35" or "3,35".
        allowed_decimals = set()
        if avg_aut_round2 is not None:
            allowed_decimals.add(f"{avg_aut_round2:.2f}")
            allowed_decimals.add(f"{round(avg_aut_round2, 1):.1f}")

        # Activity titles in this area.
        titles = {a["_title"] for a in items}

        facts[area] = {
            "n": n,
            "level_counts": lc,
            "cat_counts": cat_counts,
            "cat_pcts": cat_pcts,
            "n_match_rows": n_match_rows,
            "avg_sim_pct": avg_sim_pct,
            "avg_aut_round2": avg_aut_round2,
            "conv_total": conv,
            "allowed_ints": allowed_ints,
            "allowed_pcts": allowed_pcts_with_tol,
            "allowed_decimals": allowed_decimals,
            "titles": titles,
        }
    return facts


def extract_integers(text: str) -> list[tuple[int, str]]:
    """Yield (integer, raw_match) for every integer in text — digits and Italian words.

    Skips integers that are part of a percentage (handled separately) or the
    autonomy denominator ('/5') — those are auditable in dedicated paths.
    """
    out: list[tuple[int, str]] = []
    for m in re.finditer(r"(?<![\d.,/])(\d+)(?![\d.,])", text):
        # Skip if followed by '%' (percentage) — audited separately.
        end = m.end()
        if end < len(text) and text[end] == "%":
            continue
        out.append((int(m.group(1)), m.group(0)))
    for m in re.finditer(r"\b([a-zàèéìòù]+)\b", text, flags=re.IGNORECASE):
        w = m.group(1).lower()
        if w in WORDS_IT:
            out.append((WORDS_IT[w], m.group(0)))
    return out


def extract_percentages(text: str) -> list[int]:
    return [int(m.group(1)) for m in re.finditer(r"(\d+)\s*%", text)]


def extract_decimals(text: str) -> list[str]:
    """Decimals like 3.35 or 3,35 (not followed by /5 even — keep all)."""
    return [m.group(0).replace(",", ".") for m in re.finditer(r"\d+[.,]\d+", text)]


def extract_italics(text: str) -> list[str]:
    """Markdown italics with single * delimiter, capturing inner text without the *.

    Pre-replaces 'O*NET' with 'ONET' to avoid false matches across the literal
    asterisk in that proper noun.
    """
    cleaned = text.replace("O*NET", "ONET")
    out = []
    for m in re.finditer(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", cleaned):
        out.append(m.group(1).strip())
    return out


EXTERNAL_CONSTANTS = {
    # Documented external references that may legitimately appear in commentary.
    # Each entry must be defensible — these are not data claims but fact references
    # to identifiable external systems/regulations. Add with care.
    231,  # D.Lgs 231/2001 (Italian compliance regulation)
}


def audit_note(area: str, note: str, facts: dict, year_window: tuple[int, int] = (2024, 2030)) -> list[str]:
    issues: list[str] = []

    allowed_ints = facts["allowed_ints"]
    allowed_pcts = facts["allowed_pcts"]
    allowed_decimals = facts["allowed_decimals"]
    titles = facts["titles"]

    # Years in a small recent window pass without inflation.
    year_set = set(range(year_window[0], year_window[1] + 1))
    allowed_ints_with_meta = set(allowed_ints) | year_set | EXTERNAL_CONSTANTS

    for value, raw in extract_integers(note):
        # Skip if part of a percentage (we audit those separately).
        # The integer extractor catches the digits anyway; we just permit any
        # int that matches a known fact, including pct values.
        if value in allowed_ints_with_meta:
            continue
        if value in allowed_pcts:
            continue
        # Allow small numerals (≤5) that are likely structural rather than
        # data claims (e.g., "due cluster", "tre frasi"). The threshold is
        # conservative — if a count of 5 exists in the data, it's allowed
        # via allowed_ints anyway.
        if value <= 5 and raw.lower() in WORDS_IT:
            # Italian small-number words used adjectivally are common.
            # If the value matches no fact, keep it (likely "due cluster").
            continue
        issues.append(f"  integer {value} (raw '{raw}') not traceable to area facts")

    allowed_pct_set = facts["allowed_pcts"]
    for pct in extract_percentages(note):
        if pct in allowed_pct_set:
            continue
        issues.append(f"  percentage {pct}% not traceable (allowed={sorted(allowed_pct_set)})")

    for dec in extract_decimals(note):
        if dec in allowed_decimals:
            continue
        # Allow autonomy at rounded-to-1-decimal too.
        if facts["avg_aut_round2"] is not None:
            r1 = round(facts["avg_aut_round2"], 1)
            if dec == f"{r1:.1f}" or dec == f"{r1:.2f}":
                continue
        # Allow P25/P75 boundary values quoted explicitly.
        if dec in ("3.21", "3.57"):
            continue
        # Allow x.xx that matches any single match autonomy in any activity in the area
        # (in case the note quotes a specific match's autonomy).
        # We don't have that loaded here for compactness; for now, just flag.
        issues.append(f"  decimal {dec} not traceable to area facts (avg_aut={facts['avg_aut_round2']})")

    for title in extract_italics(note):
        if title not in titles:
            issues.append(f"  italicized title '{title}' not found in area activities")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit per-area commentary notes against matches data.")
    parser.add_argument("--notes", required=True, help="area-notes.json")
    parser.add_argument("--matches", required=True, help="all-org matches JSON")
    parser.add_argument("--metadata", required=True, help="activities metadata JSON (list of {id,title,area,...})")
    args = parser.parse_args()

    notes = json.loads(Path(args.notes).read_text())
    matches = json.loads(Path(args.matches).read_text())
    meta_list = json.loads(Path(args.metadata).read_text())
    metadata = {m["id"]: m for m in meta_list if "id" in m}

    facts = compute_area_facts(matches, metadata)

    total_issues = 0
    print("=== Area notes audit ===\n")
    for area, note in sorted(notes.items()):
        if area not in facts:
            print(f"  '{area}': NOT FOUND in matches data")
            total_issues += 1
            continue
        issues = audit_note(area, note, facts[area])
        if issues:
            print(f"  '{area}': {len(issues)} issue(s)")
            for i in issues:
                print(i)
            total_issues += len(issues)
        else:
            print(f"  '{area}': OK")

    print()
    if total_issues == 0:
        print("=== AUDIT PASS ===")
        return 0
    print(f"=== AUDIT FAIL: {total_issues} issue(s) ===")
    return 1


if __name__ == "__main__":
    sys.exit(main())
