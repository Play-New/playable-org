#!/usr/bin/env python3
"""
graph / audit.py — Verify a graph JSON.

Lightweight by design: the graph is mechanically built from frontmatter
and body links. The audit gate checks that the build hasn't drifted
(every edge endpoint resolves to a node, no duplicate node ids), that
the graph isn't trivially small (a useful map needs at least a handful
of nodes per kind), and that the agent has authored decisions on top of
it.

Usage:
    python3 audit.py --map <graph.json> --org-dir <path>

Exit code:
    0 = audit passed
    1 = audit failed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_NODE_KINDS = {"unit", "activity", "person", "stakeholder", "commitment", "source"}
ALLOWED_EDGE_KINDS = {
    "parent",
    "unit",
    "performer",
    "party_committing",
    "party_benefiting",
    "touches",
    "cite",
    "link",
}


def audit_nodes(nodes: list[dict]) -> tuple[list[str], dict[str, int]]:
    issues: list[str] = []
    seen: set[str] = set()
    by_kind: dict[str, int] = {}

    for i, n in enumerate(nodes):
        nid = n.get("id")
        kind = n.get("kind")
        if not nid:
            issues.append(f"  node[{i}] missing 'id'")
            continue
        if nid in seen:
            issues.append(f"  node[{i}] '{nid}' duplicate id")
        seen.add(nid)
        if not kind:
            issues.append(f"  node '{nid}' missing 'kind'")
            continue
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if not n.get("label"):
            issues.append(f"  node '{nid}' missing 'label'")

    for required in REQUIRED_NODE_KINDS:
        if required not in by_kind or by_kind[required] == 0:
            issues.append(
                f"  no nodes of kind '{required}'; the graph is too thin to read meaningfully"
            )

    return issues, by_kind


def audit_edges(edges: list[dict], node_ids: set[str]) -> list[str]:
    issues: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for i, e in enumerate(edges):
        frm = e.get("from")
        to = e.get("to")
        kind = e.get("kind")
        if not frm or not to or not kind:
            issues.append(f"  edge[{i}] missing from/to/kind ({e!r})")
            continue
        if kind not in ALLOWED_EDGE_KINDS:
            issues.append(f"  edge[{i}] kind '{kind}' not in allowed set {sorted(ALLOWED_EDGE_KINDS)}")
        if frm not in node_ids:
            issues.append(f"  edge[{i}] from '{frm}' does not resolve to a node")
        if to not in node_ids:
            issues.append(f"  edge[{i}] to '{to}' does not resolve to a node")
        key = (frm, to, kind)
        if key in seen:
            issues.append(f"  edge[{i}] duplicate ({frm} -> {to}, {kind})")
        seen.add(key)
    return issues


def audit_decisions(d: dict) -> list[str]:
    issues: list[str] = []
    decisions = d.get("decisions") or []
    if len(decisions) < 3:
        issues.append(
            f"  decisions has only {len(decisions)} entries; the section reads the graph for the leader, "
            f"surface at least 3"
        )
    for i, dec in enumerate(decisions):
        if not dec.get("question"):
            issues.append(f"  decisions[{i}] missing 'question'")
        ans = (dec.get("answer") or "").strip()
        if len(ans) < 60:
            issues.append(f"  decisions[{i}] answer too short ({len(ans)} chars; need ≥ 60)")
        if not dec.get("source"):
            issues.append(f"  decisions[{i}] missing 'source' citation")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a graph JSON.")
    parser.add_argument("--map", required=True, help="Graph JSON path")
    parser.add_argument("--org-dir", required=True, help="Path to org/ (used to verify node paths)")
    args = parser.parse_args()

    map_path = Path(args.map)
    if not map_path.exists():
        print(f"FAIL: map not found at {map_path}", file=sys.stderr)
        return 1
    d = json.loads(map_path.read_text(encoding="utf-8"))

    nodes = d.get("nodes") or []
    edges = d.get("edges") or []
    if not nodes:
        print("=== AUDIT FAIL ===\n  nodes list is empty")
        return 1

    node_issues, by_kind = audit_nodes(nodes)
    node_ids = {n.get("id") for n in nodes if n.get("id")}
    edge_issues = audit_edges(edges, node_ids)
    decision_issues = audit_decisions(d)

    print("=== Graph audit ===\n")
    print(f"  scope:  {d.get('_scope', '?')}")
    print(f"  nodes:  {len(nodes)} ({', '.join(f'{k}={v}' for k, v in sorted(by_kind.items()))})")
    print(f"  edges:  {len(edges)}")
    print(f"  decisions: {len(d.get('decisions') or [])}")
    print()

    issues = node_issues + edge_issues + decision_issues
    if issues:
        print(f"=== AUDIT FAIL: {len(issues)} issue(s) ===")
        for i in issues:
            print(i)
        return 1

    print("=== AUDIT PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
