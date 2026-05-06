#!/usr/bin/env python3
"""
ai-exposure / audit.py — Verify a play does not invent numbers or unverifiable claims.

Deterministic check on a play markdown file. Compares every numerical claim
against the matches JSON. Flags external regulatory/legal claims that don't
cite a specific article number, requiring them to be acknowledged in a
dedicated review section.

Usage:
    python3 audit.py --play <path-to-play.md> --matches <path-to-matches.json>
                     [--legal-source "Civil Code"] [--legal-source "Bar Regulations"]

Exit code:
    0 = audit passed
    1 = audit failed (numerical claims unverifiable, or legal claims unacknowledged)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_per_activity_sections(play_text: str) -> dict[str, str]:
    """Split the play into per-activity sections (### activity-id ...)."""
    sections: dict[str, str] = {}
    parts = re.split(r'^### ([\w-]+)$', play_text, flags=re.M)
    for i in range(1, len(parts), 2):
        aid = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        next_h2 = body.find("\n## ")
        if next_h2 > 0:
            body = body[:next_h2]
        sections[aid] = body.strip()
    return sections


def build_match_data(matches: list[dict]) -> dict[str, dict]:
    """For each activity, collect all autonomy/count/similarity values from JSON."""
    data: dict[str, dict] = {}
    for a in matches:
        aid = a["id"]
        rich = [m for m in a["matches"] if m.get("ai_autonomy_mean")]
        autonomies = [round(float(m["ai_autonomy_mean"]), 2) for m in rich]
        counts = [int(m.get("count") or 0) for m in rich]
        sims = [round(m["similarity"], 4) for m in a["matches"]]
        data[aid] = {
            "autonomies": autonomies,
            "mean_autonomy": round(sum(autonomies) / len(autonomies), 2) if autonomies else None,
            "max_autonomy": max(autonomies) if autonomies else None,
            "min_autonomy": min(autonomies) if autonomies else None,
            "counts": counts,
            "max_count": max(counts) if counts else None,
            "n_rich": len(rich),
            "sims": sims,
        }
    return data


def audit_numerical_claims(sections: dict[str, str], data: dict[str, dict]) -> list[tuple[str, str, float]]:
    """Verify each numerical claim in per-activity section is traceable in JSON."""
    issues: list[tuple[str, str, float]] = []

    for aid, body in sections.items():
        d = data.get(aid, {})

        for m in re.finditer(r'autonomy[\s=]+(\d+\.\d+)', body, re.IGNORECASE):
            val = round(float(m.group(1)), 2)
            ok = (
                val in d.get("autonomies", [])
                or val == d.get("mean_autonomy")
                or val == d.get("max_autonomy")
                or val == d.get("min_autonomy")
            )
            if not ok:
                issues.append((aid, "autonomy", val))

        for m in re.finditer(r'\bcount[\s=]+(\d+)', body, re.IGNORECASE):
            val = int(m.group(1))
            ok = (val in d.get("counts", [])) or (val == d.get("max_count"))
            if not ok:
                issues.append((aid, "count", val))

        for m in re.finditer(r'sim(?:ilarity)?[\s=]+(\d+\.\d+)', body, re.IGNORECASE):
            val = float(m.group(1))
            ok = any(abs(val - s) < 0.005 for s in d.get("sims", []))
            if not ok:
                issues.append((aid, "similarity", val))

    return issues


def audit_unverified_legal_claims(play_text: str, legal_sources: list[str]) -> dict[str, list[str]]:
    """Flag mentions of named legal sources that lack a specific article number.

    Args:
        play_text: full play markdown
        legal_sources: list of legal source names to check (e.g. ["Codice Civile", "Civil Code"])

    Returns: {source_name: [list of mentions without article reference]}
    """
    findings: dict[str, list[str]] = {src: [] for src in legal_sources}

    for src in legal_sources:
        pattern = re.compile(re.escape(src) + r'[^\n.]*', re.IGNORECASE)
        for m in pattern.finditer(play_text):
            ctx = m.group()
            # Considered cited if it includes "art. NNN" / "article NNN" / "§ NNN" / "art NNN"
            has_article = re.search(r'(?:art\.?|article|§)\s*\d', ctx, re.IGNORECASE)
            if not has_article:
                findings[src].append(ctx[:150])

    return findings


def check_review_section_present(play_text: str) -> bool:
    """A play with unverified legal claims must include a dedicated review section.

    Looks for a heading containing 'review' / 'verify' / 'validate' / 'unverified' /
    'da validare' / 'non verifi' / 'claims to'.
    """
    return bool(
        re.search(
            r'^##\s+.*(?:review|verify|validate|unverified|da\s+valid|non\s*verifi|claims?\s+to)',
            play_text,
            re.IGNORECASE | re.M,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a play against its matches JSON.")
    parser.add_argument("--play", required=True, help="Play markdown file")
    parser.add_argument("--matches", required=True, help="match.py output JSON")
    parser.add_argument(
        "--legal-source",
        action="append",
        default=[],
        help="Name of a legal/regulatory source to check for unverified citations. Repeatable. "
             "Example: --legal-source 'Civil Code' --legal-source 'Bar Regulations'. "
             "If empty, the legal-claims audit is skipped.",
    )
    args = parser.parse_args()

    play_text = Path(args.play).read_text()
    matches = json.loads(Path(args.matches).read_text())

    sections = parse_per_activity_sections(play_text)
    data = build_match_data(matches)

    print(f"Per-activity sections: {len(sections)}")
    print(f"Activities in matches: {len(data)}")
    print()

    num_issues = audit_numerical_claims(sections, data)
    print("=== Numerical claims ===")
    if num_issues:
        print(f"  {len(num_issues)} issue(s):")
        for aid, kind, val in num_issues:
            d = data.get(aid, {})
            print(f"    {aid}: {kind}={val} not in JSON")
            print(f"      JSON has: autonomies={d.get('autonomies')}, mean={d.get('mean_autonomy')}, counts={d.get('counts')}")
    else:
        print("  ALL CLAIMS VERIFIABLE.")

    legal_pass = True
    if args.legal_source:
        legal_findings = audit_unverified_legal_claims(play_text, args.legal_source)
        total_legal = sum(len(v) for v in legal_findings.values())
        print(f"\n=== Legal claims without article reference ===")
        if total_legal:
            for src, items in legal_findings.items():
                if items:
                    print(f"  '{src}': {len(items)} citation(s) without specific article")
            section_present = check_review_section_present(play_text)
            print(f"\n  Review/validation section present in play: {section_present}")
            if not section_present:
                print("  → AUDIT FAIL: Play has unverified legal claims but no section listing them for review.")
                legal_pass = False
            else:
                print("  → OK: Unverified claims acknowledged in dedicated section.")
        else:
            print("  None.")

    if num_issues or not legal_pass:
        print("\n=== AUDIT FAIL ===")
        return 1

    print("\n=== AUDIT PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
