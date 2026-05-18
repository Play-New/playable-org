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


# Vocabulary that should not appear in the decisions text. Two groups
# overlap here.
#
# (a) Graph-theory and structure-of-the-data terms. The graph is the
#     most plumbing-flavoured of the playbooks, so the blacklist
#     focuses on words that read as code/topology to a non-technical
#     leader. Both English and Italian variants are listed, populated
#     incrementally from the failure modes seen on real fork plays
#     (most recently AIRC, May 2026).
#
# (b) Rhetorical formulas and meta-voice that STYLE.md bans across all
#     playbooks: em dashes, "Significa X, non Y" / "Not X, but Y"
#     constructions, "il grafo dichiara / la struttura mostra" agent-
#     voice, repo-internal jargon (`playbook`, `ingest`, `frontmatter`,
#     `_path`) that leaked from documentation into prose.
#
# The framework names of the *other* playbooks also leak here
# (capability stack, etc.); we forbid them so the graph stays the
# graph and doesn't quietly turn into a rerun of a different reading.
GRAPH_JARGON = re.compile(
    "|".join([
        # --- graph-theory (English) ---
        r"\bnode\s+degree\b",
        r"\bdegree\s+centrality\b",
        r"\bbetweenness\b",
        r"\bhub\s+node\b",
        r"\bgraph\s+density\b",
        r"\bclustering\s+coefficient\b",
        r"\bsubgraph\b",
        # --- graph-theory (Italian) ---
        r"\bgrado\s+di\s+centralit[àa]\b",
        r"\bdipendenze\s+documentate\b",
        r"\bedge\s+tipizzat[oaie]\b",
        r"\bnodi?\s+isolat[oaie]\b",
        r"\btopolog(?:ia|ical)\b",
        r"\bancorat[oaie]\s+(?:a|al|alla|alle|ai|agli)\b",
        # --- meta-rhetorical (the data speaks) ---
        r"\bil\s+grafo\s+(?:dichiar[ao]|mostr[ao]|dic[ea]|racconta|sa|sapeva)\b",
        r"\bla\s+struttura\s+(?:dichiar[ao]|mostr[ao]|dic[ea]|racconta)\b",
        r"\bthe\s+(?:graph|structure)\s+(?:declares?|says?|knows?|shows?\s+us)\b",
        # --- rhetorical formulas (in any language) ---
        # "Significa X, non Y" / "It's X, not Y"
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
        # --- punctuation banned by STYLE.md ---
        r"—",
        # --- other-playbook framework leakage: the graph is the graph ---
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


def score_linked_references(map_data: dict) -> tuple[bool, str]:
    """Every node id the agent lists in `decision.node_ids` must also
    appear as a markdown link ``[label](node-id)`` inside that
    decision's answer prose. Two complementary effects:

    - the inspect-panel-style link contract holds: nodes named in a
      decision are clickable; the reader can navigate the canvas
      directly from the analysis.
    - it pushes the agent to write decisions that reference nodes
      *in-context*, not just attached as metadata.

    A bare mention without a link counts as a failure: if the agent
    lists `divulgazione-di-missione` in `node_ids` but the answer
    only says "divulgazione di missione" in prose, the reader sees a
    name they can't click. Either link it, or drop it from `node_ids`.
    """
    decisions = map_data.get("decisions") or []
    if not decisions:
        return False, "no decisions to score"

    issues: list[str] = []
    checked = 0
    for i, dec in enumerate(decisions):
        node_ids = dec.get("node_ids") or []
        answer = dec.get("answer") or ""
        for nid in node_ids:
            checked += 1
            # Match `](node-id)` allowing whitespace / closing paren.
            if not re.search(rf"\]\(\s*{re.escape(nid)}\s*\)", answer):
                issues.append(
                    f"  decision[{i}]: node_ids lists '{nid}' but no markdown "
                    f"link [...]({nid}) appears in the answer"
                )

    if issues:
        return False, "missing in-prose links:\n" + "\n".join(issues[:10])
    return True, f"{checked} node id(s) in node_ids — every one linked in the answer"


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
        ("linked references",    *score_linked_references(map_data)),
        ("audit grounded",       *score_audit_grounded(map_data)),
    ]
    if args.llm:
        checks.append(("llm judge",      *score_llm_judge(map_data)))

    return run_checks(playbook="graph", map_path=map_path, checks=checks)


if __name__ == "__main__":
    sys.exit(main())
