#!/usr/bin/env python3
"""
graph / autoresearch.py — Score a graph play on five dimensions.

Four deterministic gates: the decisions read as written for this org
(named units / activities / stakeholders), no jargon paraphrase, the
decisions array is substantive, every cited node id resolves to an
actual node in the graph. The fifth (--llm) calls Claude Sonnet 4.6
to score actionable / distinctive / readable per decision.

The graph itself is mechanically built from the structure, so the
"audit grounded" check here is on the decisions referencing real node
ids — not on re-walking org/, which build.py already did.

Usage:
    python3 autoresearch.py --map <graph.json> [--org-dir <path>] [--llm]
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


# Vocabulary that should not appear in the decisions text — the
# graph is the most plumbing-flavoured of the playbooks, so the
# blacklist focuses on graph-theory terms that read as jargon to a
# non-technical leader. The framework names of the *other* playbooks
# also leak here (capability stack, etc.); we forbid them so the
# graph stays the graph and doesn't quietly turn into a rerun of a
# different reading.
GRAPH_JARGON = re.compile(
    "|".join([
        r"\bnode\s+degree\b",
        r"\bdegree\s+centrality\b",
        r"\bbetweenness\b",
        r"\bhub\s+node\b",
        r"\bgraph\s+density\b",
        r"\bclustering\s+coefficient\b",
        r"\bsubgraph\b",
        # Other-playbook framework leakage — the graph is the graph.
        r"\bworld\s*model\b",
        r"\bcapability\s+stack\b",
        r"\bintelligence\s+layer\b",
        r"\bvalue\s+chain\b",
        r"\bevolution\s+axis\b",
        r"\bbundle\b",
        r"\bmoat\b",
        r"\bcommodity\s+capability\b",
    ]),
    re.IGNORECASE,
)


def score_audit_grounded(map_data: dict) -> tuple[bool, str]:
    """Each decision that names a node id (in `source` or `node_ids`)
    must reference a node that exists in the graph."""
    nodes = map_data.get("nodes") or []
    node_ids = {n.get("id") for n in nodes if n.get("id")}
    if not node_ids:
        return False, "no nodes in graph; nothing to ground decisions against"

    decisions = map_data.get("decisions") or []
    issues: list[str] = []
    checked = 0
    for i, dec in enumerate(decisions):
        ids_field = dec.get("node_ids") or []
        for nid in ids_field:
            checked += 1
            if nid not in node_ids:
                issues.append(f"  decision[{i}] references node id '{nid}' not in graph")
        # Also try to spot bare ids in `source` like "outline-charter-2024".
        src = dec.get("source", "") or ""
        for token in re.findall(r"\b[a-z][a-z0-9-]{4,}\b", src):
            if token in node_ids:
                checked += 1
    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{checked} node id reference(s) checked, all resolve"


JUDGE_CONTEXT = """\
A graph artefact is the whole organization rendered as nodes (units, activities, people,
stakeholders, commitments, sources) and the relations declared between them in the
structure. The decisions are the leader-facing reading of the topology: which nodes are
load-bearing, which regions of the structure are sparse or thin, where the documentation
is missing, what the cluster structure suggests about the org's seams."""


def score_llm_judge(map_data: dict) -> tuple[bool, str]:
    decisions = map_data.get("decisions") or []
    payload = {
        "scope":     map_data.get("_scope"),
        "topology":  map_data.get("_topology"),
        "node_kinds": sorted({n.get("kind") for n in (map_data.get("nodes") or [])}),
    }
    return llm_judge(
        decisions,
        payload,
        artefact_kind="graph",
        playbook_context=JUDGE_CONTEXT,
        user_message_intro="Score each decision in this graph play. Return one entry per decision, in the same order as the input.",
    )


def _gather_names(map_data: dict) -> list[str]:
    names: list[str] = []
    for n in map_data.get("nodes") or []:
        names.extend([n.get("id") or "", n.get("label") or ""])
    return [n for n in names if n]


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a graph play on the autoresearch dimensions.")
    parser.add_argument("--map", required=True, help="Path to the graph JSON")
    parser.add_argument("--org-dir", help="(reserved for symmetry with the other playbooks; not used today)")
    parser.add_argument("--llm", action="store_true", help="Also run the LLM-as-judge dimension (Claude Sonnet 4.6, requires ANTHROPIC_API_KEY)")
    args = parser.parse_args()

    map_path = Path(args.map)
    if not map_path.exists():
        print(f"FAIL: map not found at {map_path}", file=sys.stderr)
        return 2

    map_data = json.loads(map_path.read_text(encoding="utf-8"))

    checks: list[tuple[str, bool, str]] = [
        ("recognizability",      *score_recognizability(map_data, names=_gather_names(map_data), min_mentions=3)),
        ("plain language",       *score_plain_language(map_data, GRAPH_JARGON)),
        ("decision anchoring",   *score_decision_anchoring(map_data)),
        ("audit grounded",       *score_audit_grounded(map_data)),
    ]
    if args.llm:
        checks.append(("llm judge",      *score_llm_judge(map_data)))

    return run_checks(playbook="graph", map_path=map_path, checks=checks)


if __name__ == "__main__":
    sys.exit(main())
