#!/usr/bin/env python3
"""
value-map / autoresearch.py — Score a value-map play on five dimensions.

Four are deterministic gates that catch the common failure modes a play
can ship with — jargon a leader can't read, decisions that are missing
or too thin, components that aren't grounded in the structure, prose
that doesn't actually mention the org by name.

The fifth (--llm) calls Claude Sonnet 4.6 as a judge and scores each
decision on actionable / distinctive / readable. Skipped (PASS) when no
ANTHROPIC_API_KEY is set so the gate stays usable offline.

Usage:
    python3 autoresearch.py --map <chain.json> [--org-dir <path>] [--llm]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Shared library
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from autoresearch_lib import (  # noqa: E402
    llm_judge,
    run_checks,
    score_decision_anchoring,
    score_plain_language,
    score_recognizability,
)


# ----------------------------------------------------------------------
# Playbook-specific deterministic checks
# ----------------------------------------------------------------------

# Vocabulary that should not appear in the decisions text. Two groups.
#
# (a) Wardley primitive names paraphrased into prose. The framework
#     stage labels (Genesis / Custom / Product / Commodity) are fine
#     when they are the label of a UI element; phrases like "genesis
#     stage" or "commodity tier" embedded in prose are not.
#
# (b) Universal style bans from STYLE.md (added 2026-05-18 after the
#     AIRC graph-decision iteration): em dashes, "Significa X, non Y"
#     / "Not X, but Y" formulas, meta-rhetorical "the data says /
#     la mappa dichiara" voice, repo and pipeline jargon leaking
#     into user prose.
WARDLEY_JARGON = re.compile(
    "|".join([
        # --- Wardley internals ---
        r"\bevolution\s+0\.\d+",
        r"\bvisibility\s+0\.\d+",
        r"\bevolution_target\b",
        r"\bai_effect\b",
        r"\bgenesis\s+stage\b",
        r"\bcommodity\s+tier\b",
        r"\bproduct\s+tier\b",
        # --- meta-rhetorical (the data speaks) ---
        r"\b(?:la\s+)?(?:mappa|catena|struttura)\s+(?:dichiar[ao]|mostr[ao]|dic[ea]|racconta)\b",
        r"\bthe\s+(?:map|chain|structure)\s+(?:declares?|says?|knows?|shows?\s+us)\b",
        # --- rhetorical formulas (in any language) ---
        r"\bsignifica\s+\w+(?:\s+\w+){0,2},\s+non\s+\w+",
        r"\bè\s+\w+(?:\s+\w+){0,2},\s+non\s+\w+",
        r"\bnot\s+\w+(?:\s+\w+){0,2},\s+but\s+\w+",
        r"\bisn'?t\s+\w+(?:\s+\w+){0,2},\s+it'?s\s+\w+",
        # --- repo / pipeline jargon leaking into prose ---
        r"\bpassata\s+di\s+ingest\b",
        r"\bingerit[oaie]\b",
        r"\bplaybook\b",
        r"\bfrontmatter\b",
        r"\b_path\b",
        r"\b_structure_id\b",
        r"\b_structure_evidence\b",
        # --- punctuation banned by STYLE.md ---
        r"—",
    ]),
    re.IGNORECASE,
)


def score_audit_grounded(map_data: dict, org_dir: Path | None) -> tuple[bool, str]:
    """Every non-is_new component has a _structure_id resolving to a file
    under org/. Skipped when no org-dir is supplied."""
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
# LLM-as-judge wiring (uses shared library)
# ----------------------------------------------------------------------

JUDGE_CONTEXT = """\
A value-map sits over a structure of named units, activities, and commitments. The map shows
which parts of the work are differentiated craft vs. competent practice the org shares with
every other shop, and where AI or competitive pressure is pushing each part."""


def score_llm_judge(map_data: dict) -> tuple[bool, str]:
    decisions = map_data.get("decisions") or []
    payload = {
        "anchor": {
            "title": (map_data.get("_anchor") or {}).get("title"),
            "kind":  (map_data.get("_anchor") or {}).get("kind"),
        },
        "components": [
            {"label": c.get("label"), "kind": c.get("_kind"), "structure_id": c.get("_structure_id")}
            for c in map_data.get("components", [])
            if not c.get("is_new")
        ],
    }
    return llm_judge(
        decisions,
        payload,
        artefact_kind="value-map",
        playbook_context=JUDGE_CONTEXT,
        user_message_intro="Score each decision in this value-map. Return one entry per decision, in the same order as the input.",
    )


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Score a value-map play on the autoresearch dimensions.")
    parser.add_argument("--map", required=True, help="Path to the value-map JSON")
    parser.add_argument("--org-dir", help="Path to org/ for audit-grounded check")
    parser.add_argument("--llm", action="store_true", help="Also run the LLM-as-judge dimension (Claude Sonnet 4.6, requires ANTHROPIC_API_KEY)")
    args = parser.parse_args()

    map_path = Path(args.map)
    if not map_path.exists():
        print(f"FAIL: map not found at {map_path}", file=sys.stderr)
        return 2

    map_data = json.loads(map_path.read_text(encoding="utf-8"))
    org_dir = Path(args.org_dir) if args.org_dir else None

    component_names: list[str] = []
    for c in map_data.get("components", []):
        sid = c.get("_structure_id") or c.get("id")
        if sid:
            component_names.append(sid)
        lab = c.get("label") or ""
        if lab:
            component_names.append(lab)

    checks: list[tuple[str, bool, str]] = [
        ("recognizability",      *score_recognizability(map_data, names=component_names, min_mentions=3)),
        ("plain language",       *score_plain_language(map_data, WARDLEY_JARGON)),
        ("decision anchoring",   *score_decision_anchoring(map_data)),
        ("audit grounded",       *score_audit_grounded(map_data, org_dir)),
    ]
    if args.llm:
        checks.append(("llm judge",      *score_llm_judge(map_data)))

    return run_checks(playbook="value-map", map_path=map_path, checks=checks)


if __name__ == "__main__":
    sys.exit(main())
