#!/usr/bin/env python3
"""
value-map / autoresearch.py — Score a value-map play on four dimensions
that the SKILL.md's autoresearch loop iterates against.

This is a deterministic gate, not an LLM-as-judge. It catches the common
failure modes a play can ship with: jargon that the leader can't read,
decisions that are missing or too thin, components that aren't grounded
in the structure, prose that doesn't actually mention the org by name.

Usage:
    python3 autoresearch.py --map <chain.json> [--org-dir <path>]

Exit code:
    0 = all four dimensions pass
    1 = one or more dimensions fail (script prints which)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# ----------------------------------------------------------------------
# Jargon blacklist — terms that should not appear in the agent-authored
# decisions text without being plainly translated.
# ----------------------------------------------------------------------

WARDLEY_JARGON_STANDALONE = [
    # Wardley vocabulary used as a label, not as plain English
    r'\bevolution\s+0\.\d+',           # "evolution 0.32"
    r'\bvisibility\s+0\.\d+',          # "visibility 0.85"
    r'\bevolution_target\b',           # the JSON field name
    r'\bai_effect\b',                  # the JSON field name
    r'\bgenesis\s+stage\b',            # raw stage label
    r'\bcommodity\s+tier\b',           # too jargon-y
    r'\bproduct\s+tier\b',             # same
]

JARGON_RE = re.compile('|'.join(WARDLEY_JARGON_STANDALONE), re.IGNORECASE)


# ----------------------------------------------------------------------
# Recognizability — heuristic: at least N component labels appear by
# name in the decisions text. The map sits over real structure nodes;
# the interpretation should call them out.
# ----------------------------------------------------------------------

MIN_COMPONENT_MENTIONS = 3


def score_recognizability(map_data: dict) -> tuple[bool, str]:
    """The decisions text mentions at least MIN_COMPONENT_MENTIONS specific
    component labels or _structure_ids by name."""
    decisions = map_data.get("decisions") or []
    if not decisions:
        return False, "no decisions to score"

    component_ids = [c.get("_structure_id") or c.get("id") for c in map_data.get("components", [])]
    component_labels = [c.get("label", "") for c in map_data.get("components", [])]
    haystack = " ".join(d.get("answer", "") + " " + d.get("question", "") for d in decisions)

    mentioned = set()
    for cid in component_ids:
        if cid and cid.lower() in haystack.lower():
            mentioned.add(cid)
    for lab in component_labels:
        if lab and len(lab) >= 4 and lab.lower() in haystack.lower():
            mentioned.add(lab)

    n = len(mentioned)
    if n >= MIN_COMPONENT_MENTIONS:
        return True, f"{n} component name(s) mentioned in decisions ({', '.join(sorted(mentioned))[:200]})"
    return False, (
        f"only {n} component name(s) mentioned; need ≥ {MIN_COMPONENT_MENTIONS}. "
        f"The decisions read as generic — the org should be able to recognize itself in them."
    )


# ----------------------------------------------------------------------
# Plain language — jargon density in decisions text.
# ----------------------------------------------------------------------

def score_plain_language(map_data: dict) -> tuple[bool, str]:
    """No jargon hits in the decisions text (Wardley standalone terms,
    JSON field names leaking, "evolution 0.X" numbers)."""
    decisions = map_data.get("decisions") or []
    if not decisions:
        return False, "no decisions to score"

    findings: list[str] = []
    for i, d in enumerate(decisions):
        text = d.get("question", "") + "\n" + d.get("answer", "")
        for m in JARGON_RE.finditer(text):
            findings.append(f"  decision[{i}]: {m.group(0)!r}")

    if findings:
        return False, "jargon hits:\n" + "\n".join(findings[:10])
    return True, "no jargon hits in decisions"


# ----------------------------------------------------------------------
# Decision anchoring — ≥ 3 decisions, each with substantive answer +
# non-empty source.
# ----------------------------------------------------------------------

MIN_DECISIONS = 3
MIN_ANSWER_CHARS = 60


def score_decision_anchoring(map_data: dict) -> tuple[bool, str]:
    decisions = map_data.get("decisions") or []
    n = len(decisions)
    if n < MIN_DECISIONS:
        return False, f"only {n} decision(s); need ≥ {MIN_DECISIONS}"

    issues: list[str] = []
    for i, d in enumerate(decisions):
        if not d.get("question", "").strip():
            issues.append(f"  decision[{i}]: empty question")
        ans = d.get("answer", "").strip()
        if len(ans) < MIN_ANSWER_CHARS:
            issues.append(f"  decision[{i}]: answer too short ({len(ans)} chars; need ≥ {MIN_ANSWER_CHARS})")
        if not d.get("source", "").strip():
            issues.append(f"  decision[{i}]: empty source citation")

    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{n} decisions, all substantive and cited"


# ----------------------------------------------------------------------
# Audit grounded — every non-is_new component has a _structure_id that
# resolves to a real file under org/.
# ----------------------------------------------------------------------

def score_audit_grounded(map_data: dict, org_dir: Path | None) -> tuple[bool, str]:
    if org_dir is None:
        return True, "skipped (no --org-dir provided)"

    components = map_data.get("components") or []
    issues: list[str] = []

    for c in components:
        if c.get("is_new"):
            continue
        sid = c.get("_structure_id")
        if not sid:
            issues.append(f"  {c.get('id')} '{c.get('label')}': missing _structure_id")
            continue
        # Try the standard locations
        candidates = [
            org_dir / "nodes" / "units" / f"{sid}.md",
            org_dir / "nodes" / "activities" / f"{sid}.md",
            org_dir / "nodes" / "stakeholders" / f"{sid}.md",
            org_dir / "nodes" / "people" / f"{sid}.md",
            org_dir / "commitments" / f"{sid}.md",
        ]
        if not any(p.exists() for p in candidates):
            issues.append(f"  {c.get('id')} '{c.get('label')}': _structure_id '{sid}' not found in org/")

    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{len(components)} components, every non-is_new has a resolvable _structure_id"


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Score a value-map play on four autoresearch dimensions.")
    parser.add_argument("--map", required=True, help="Path to the value-map JSON")
    parser.add_argument("--org-dir", help="Path to org/ for audit-grounded check")
    args = parser.parse_args()

    map_path = Path(args.map)
    if not map_path.exists():
        print(f"FAIL: map not found at {map_path}", file=sys.stderr)
        return 2

    map_data = json.loads(map_path.read_text(encoding="utf-8"))
    org_dir = Path(args.org_dir) if args.org_dir else None

    print(f"=== Autoresearch · value-map · {map_path.name} ===\n")

    checks: list[tuple[str, bool, str]] = [
        ("recognizability",      *score_recognizability(map_data)),
        ("plain language",       *score_plain_language(map_data)),
        ("decision anchoring",   *score_decision_anchoring(map_data)),
        ("audit grounded",       *score_audit_grounded(map_data, org_dir)),
    ]

    width = max(len(name) for name, _, _ in checks)
    fails = 0
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}]  {name:<{width}}  —  {detail}")
        if not ok:
            fails += 1

    print()
    if fails == 0:
        print("=== AUTORESEARCH PASS ===")
        return 0
    print(f"=== AUTORESEARCH FAIL: {fails}/{len(checks)} dimension(s) ===")
    return 1


if __name__ == "__main__":
    sys.exit(main())
