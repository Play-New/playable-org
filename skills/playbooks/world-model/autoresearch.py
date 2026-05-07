#!/usr/bin/env python3
"""
world-model / autoresearch.py — Score a world-model play on five dimensions.

Four are deterministic gates: jargon density (capability-stack vocabulary
should not leak), decisions present and substantive, every cited
capability / interface / failure-signal grounded in the structure, and
the play's interpretation actually mentions named units / activities /
stakeholders of the org.

The fifth (--llm) calls Claude Sonnet 4.6 to score each decision on
actionable / distinctive / readable. Skipped (PASS) without
ANTHROPIC_API_KEY so the gate stays usable offline.

Usage:
    python3 autoresearch.py --map <world-model.json> [--org-dir <path>] [--llm]
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


# Vocabulary that should not appear in the decisions text — when it
# does, the agent has paraphrased framework terms rather than
# translating them into the org's language.
WORLD_MODEL_JARGON = re.compile(
    "|".join([
        r"\bworld\s*model\b",          # the framework name itself
        r"\bcapability\s+stack\b",
        r"\bintelligence\s+layer\b",
        r"\binterface\s+layer\b",
        r"\bfailure\s+signal\b",       # the JSON field name
        r"\bmoat\b",                   # leaking jargon
        r"\bcommodity\s+capability\b",
        r"\bjudgment\s+density\b",
    ]),
    re.IGNORECASE,
)


def score_audit_grounded(map_data: dict, org_dir: Path | None) -> tuple[bool, str]:
    """Every named capability / interface / failure-signal that claims a
    structure id resolves to a real file under org/."""
    if org_dir is None:
        return True, "skipped (no --org-dir provided)"

    issues: list[str] = []

    def _check(item: dict, kind: str, idx: int) -> None:
        sid = item.get("_structure_id") or item.get("structure_id")
        if not sid:
            return  # missing structure_id is allowed for emerging items
        candidates = [
            org_dir / "nodes" / "units" / f"{sid}.md",
            org_dir / "nodes" / "activities" / f"{sid}.md",
            org_dir / "nodes" / "stakeholders" / f"{sid}.md",
            org_dir / "nodes" / "people" / f"{sid}.md",
            org_dir / "commitments" / f"{sid}.md",
        ]
        if not any(p.exists() for p in candidates):
            label = item.get("name") or item.get("trigger") or item.get("label") or "<unnamed>"
            issues.append(f"  {kind}[{idx}] '{label}': _structure_id '{sid}' not found in org/")

    for i, c in enumerate(map_data.get("capabilities") or []):
        _check(c, "capability", i)
    for i, iface in enumerate(map_data.get("interfaces") or []):
        _check(iface, "interface", i)
    for i, s in enumerate(map_data.get("failure_signals") or []):
        _check(s, "failure-signal", i)

    grounded = (len(map_data.get("capabilities") or [])
                + len(map_data.get("interfaces") or [])
                + len(map_data.get("failure_signals") or []))

    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{grounded} item(s) checked, every claimed structure id resolves"


JUDGE_CONTEXT = """\
A world-model artefact maps an organization as a layered stack — stakeholders, interfaces,
intelligence layer, world model, capabilities — and a list of failure-signals that name
where today's composition breaks. The decisions are the leader-facing reading of this
stack: which capabilities are moat vs. commodity, which interfaces are real vs.
aspirational, which failure-signals indicate a missing capability the org should build."""


def score_llm_judge(map_data: dict) -> tuple[bool, str]:
    decisions = map_data.get("decisions") or []
    payload = {
        "scope": map_data.get("_scope"),
        "structure_summary": map_data.get("_structure_summary"),
        "capabilities": [
            {"name": c.get("name"), "kind": c.get("kind"), "moat": c.get("moat")}
            for c in (map_data.get("capabilities") or [])
        ],
        "failure_signals": [
            {"trigger": s.get("trigger"), "missing_capability": s.get("missing_capability")}
            for s in (map_data.get("failure_signals") or [])
        ],
    }
    return llm_judge(
        decisions,
        payload,
        artefact_kind="world-model",
        playbook_context=JUDGE_CONTEXT,
        user_message_intro="Score each decision in this world-model play. Return one entry per decision, in the same order as the input.",
    )


def _gather_names(map_data: dict) -> list[str]:
    names: list[str] = []
    summary = map_data.get("_structure_summary") or {}
    structure = map_data.get("_structure") or {}
    for u in structure.get("units") or []:
        names.extend([u.get("id") or "", u.get("title") or ""])
    for a in structure.get("activities") or []:
        names.extend([a.get("id") or "", a.get("title") or ""])
    for s in structure.get("stakeholders") or []:
        names.extend([s.get("id") or "", s.get("title") or ""])
    for c in map_data.get("capabilities") or []:
        names.append(c.get("name") or "")
    return [n for n in names if n]


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a world-model play on the autoresearch dimensions.")
    parser.add_argument("--map", required=True, help="Path to the world-model JSON")
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
        ("plain language",       *score_plain_language(map_data, WORLD_MODEL_JARGON)),
        ("decision anchoring",   *score_decision_anchoring(map_data)),
        ("audit grounded",       *score_audit_grounded(map_data, org_dir)),
    ]
    if args.llm:
        checks.append(("llm judge",      *score_llm_judge(map_data)))

    return run_checks(playbook="world-model", map_path=map_path, checks=checks)


if __name__ == "__main__":
    sys.exit(main())
