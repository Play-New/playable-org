#!/usr/bin/env python3
"""
reshuffle / autoresearch.py — Score a reshuffle play on five dimensions.

Four are deterministic gates: jargon density (platform-reshuffle
vocabulary should not leak), decisions present and substantive, every
component grounded in the structure, and the play's interpretation
mentions named units / activities / stakeholders of the org.

The fifth (--llm) calls Claude Sonnet 4.6 to score each decision on
actionable / distinctive / readable. Skipped (PASS) without
ANTHROPIC_API_KEY so the gate stays usable offline.

Usage:
    python3 autoresearch.py --map <reshuffle.json> [--org-dir <path>] [--llm]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from autoresearch_lib import (  # noqa: E402
    llm_judge,
    run_checks,
    score_decision_anchoring,
    score_plain_language,
    score_recognizability,
)


# Vocabulary that should not appear in the decisions text — these are
# the framework's terms; if the agent writes them straight into the
# decisions, the leader is being asked to read jargon.
RESHUFFLE_JARGON = re.compile(
    "|".join([
        r"\bsee[-\s]saw\b",
        r"\bflywheel\b",
        r"\bcoordination\s+paradox\b",
        r"\bbundle\s+state\b",
        r"\bengine\s+candidate\b",
        r"\brebundle\b",
        r"\brebundling\b",
        r"\bconstraint\s+distribution\b",
        r"\bdissolves?\s+(the\s+)?constraint\b",
    ]),
    re.IGNORECASE,
)


def score_audit_grounded(map_data: dict, org_dir: Path | None) -> tuple[bool, str]:
    """Every component with a structure id resolves to a real file under
    org/. Engine candidates and rebundle candidates are interpretive and
    not required to ground."""
    if org_dir is None:
        return True, "skipped (no --org-dir provided)"

    components = map_data.get("components") or []
    issues: list[str] = []

    for c in components:
        sid = c.get("_structure_id") or c.get("structure_id")
        if not sid:
            continue
        candidates = [
            org_dir / "nodes" / "units" / f"{sid}.md",
            org_dir / "nodes" / "activities" / f"{sid}.md",
            org_dir / "nodes" / "stakeholders" / f"{sid}.md",
            org_dir / "nodes" / "people" / f"{sid}.md",
            org_dir / "commitments" / f"{sid}.md",
        ]
        if not any(p.exists() for p in candidates):
            issues.append(f"  '{c.get('label') or c.get('id')}': _structure_id '{sid}' not found in org/")

    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{len(components)} components, every claimed structure id resolves"


JUDGE_CONTEXT = """\
A reshuffle play asks how AI changes the bundle the org delivers — which capability becomes
the new constraint, where a see-saw of trade-offs becomes a flywheel, which previously-
separate activities should now be one. The decisions are the leader-facing reading: what
the org should now do, hire, divest, or reorganise around. Engine candidates and rebundle
candidates are the interpretive surfaces; the decisions translate them for action."""


def score_llm_judge(map_data: dict) -> tuple[bool, str]:
    decisions = map_data.get("decisions") or []
    payload = {
        "anchor": {
            "title": (map_data.get("_anchor") or {}).get("title"),
            "kind":  (map_data.get("_anchor") or {}).get("kind"),
        },
        "scope": map_data.get("_scope"),
        "components": [
            {"label": c.get("label"), "structure_id": c.get("_structure_id") or c.get("structure_id")}
            for c in map_data.get("components") or []
        ],
        "engine_candidates": map_data.get("engine_candidates") or [],
        "rebundle_candidates": map_data.get("rebundle_candidates") or [],
    }
    return llm_judge(
        decisions,
        payload,
        artefact_kind="reshuffle",
        playbook_context=JUDGE_CONTEXT,
        user_message_intro="Score each decision in this reshuffle play. Return one entry per decision, in the same order as the input.",
    )


def _gather_names(map_data: dict) -> list[str]:
    names: list[str] = []
    for c in map_data.get("components") or []:
        names.extend([c.get("label") or "", c.get("_structure_id") or c.get("structure_id") or ""])
    anchor = map_data.get("_anchor") or {}
    if anchor.get("title"):
        names.append(anchor["title"])
    return [n for n in names if n]


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a reshuffle play on the autoresearch dimensions.")
    parser.add_argument("--map", required=True, help="Path to the reshuffle JSON")
    parser.add_argument("--org-dir", help="Path to org/ for audit-grounded check")
    parser.add_argument("--llm", action="store_true", help="Also run the LLM-as-judge dimension (Claude Sonnet 4.6, requires ANTHROPIC_API_KEY)")
    args = parser.parse_args()

    map_path = Path(args.map)
    if not map_path.exists():
        print(f"FAIL: map not found at {map_path}", file=sys.stderr)
        return 2

    map_data = json.loads(map_path.read_text(encoding="utf-8"))
    org_dir = Path(args.org_dir) if args.org_dir else None

    checks: list[tuple[str, bool, str]] = [
        ("recognizability",      *score_recognizability(map_data, names=_gather_names(map_data), min_mentions=3)),
        ("plain language",       *score_plain_language(map_data, RESHUFFLE_JARGON)),
        ("decision anchoring",   *score_decision_anchoring(map_data)),
        ("audit grounded",       *score_audit_grounded(map_data, org_dir)),
    ]
    if args.llm:
        checks.append(("llm judge",      *score_llm_judge(map_data)))

    return run_checks(playbook="reshuffle", map_path=map_path, checks=checks)


if __name__ == "__main__":
    sys.exit(main())
