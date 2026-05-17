#!/usr/bin/env python3
"""
graph / build.py — Walk org/ and emit the whole graph as nodes + edges.

The other four playbooks read the structure through a specific frame
(activity-grain AEI, value chain, bundle, capability stack). This one
reads the structure as itself: every node, every relation declared in
the frontmatter or the body, no interpretive layer in between.

Node kinds (collected verbatim from the structure, mirroring the
folder layout in `org/AGENTS.md`):
  identity, language-term, unit, activity, person, role,
  stakeholder, commitment, financial-summary, source.

Edge kinds (typed by the relation that carries them). The labels in
parentheses are how the graph viewer renders each kind — keep them
plain-English; never let YAML field names leak through:
  parent           — unit → unit                 ("is part of"     / "contains")
  unit             — person/activity/role → unit ("in"             / "hosts")
  performer        — activity → person           ("performed by"   / "performs")
  head_role        — unit → role                 ("led by"         / "leads")
  holds_role       — person → role               ("as"             / "filled by")
  covers           — role → activity             ("responsible for"/ "owned by")
  party_committing — commitment → unit/stakeholder/person  ("binds"   / "bound by")
  party_benefiting — commitment → unit/stakeholder/person  ("for"     / "for")
  touches          — activity → stakeholder      ("involves"       / "involved in")
  cite             — any → source                ("cites"          / "cited by")
  link             — any → any                   ("mentions"       / "mentioned by")

The agent fills the top-level `decisions[]` after build, reading the
graph in the viewer (clusters, isolates, bridge nodes). Build does not
interpret — it surfaces the topology.

Usage:
    python3 build.py --org-dir <path> --out <graph.json>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


# ----------------------------------------------------------------------
# Frontmatter parser — same shape as the other build.py scripts so the
# tolerance to YAML quirks is consistent across the playbook suite.
# ----------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict[str, Any]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    block = m.group(1)
    fm: dict[str, Any] = {}
    current_key: str | None = None
    for line in block.split("\n"):
        if not line.strip():
            continue
        cont = re.match(r"^\s*-\s*(.+)$", line)
        if cont and current_key:
            v = cont.group(1).strip().strip('"').strip("'")
            fm.setdefault(current_key, [])
            if isinstance(fm[current_key], list):
                fm[current_key].append(v)
            continue
        kv = re.match(r"^([\w_]+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            current_key = key
            if val == "":
                fm[key] = []
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                fm[key] = [] if not inner else [
                    x.strip().strip('"').strip("'") for x in inner.split(",")
                ]
            else:
                fm[key] = val.strip('"').strip("'")
    return fm


def get_title(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def strip_frontmatter(text: str) -> str:
    """Return the body of a markdown file (everything after the closing ---)."""
    m = re.match(r"^---\n.*?\n---\n", text, re.S)
    return text[m.end():] if m else text


# Strip leading and trailing whitespace from a paragraph, collapse internal
# runs of whitespace (newlines inside the paragraph) into single spaces so
# the description renders on a single visual line if the original was wrapped.
_WS = re.compile(r"\s+")


def extract_description(text: str, *, max_chars: int = 480) -> str:
    """Pull a short narrative description from a node markdown file.

    Strategy: walk the body after the frontmatter, skip the first H1 (the
    title — already captured by `get_title`), then take the first paragraph
    that follows. Skip blockquotes (lines starting with `>`) and any other
    non-prose blocks (lists, code, sub-headings) until we find prose. Inline
    markdown is preserved as-is so the viewer can render links + emphasis.

    A node without a written-out paragraph (e.g. an early stub or a
    governance-body file that only declares frontmatter and a title) yields
    an empty string; the viewer falls back to the bare label in that case.

    `max_chars` caps the length so the inspect card stays scannable.
    Truncation happens at the last whole word before the cap, with an
    ellipsis appended.
    """
    body = strip_frontmatter(text)

    # Drop the leading H1 line if present so we start reading prose.
    body = re.sub(r"^#\s+.+?\n", "", body, count=1).lstrip()

    # Split on blank lines into blocks; first prose block wins.
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    for block in blocks:
        first_line = block.splitlines()[0].lstrip()
        # Skip non-prose blocks: sub-headings, lists, code fences, blockquotes,
        # tables, horizontal rules.
        if first_line.startswith(("#", "-", "*", "+", "1.", "```", ">", "|", "---")):
            continue
        # Skip frontmatter-style key:value lines if any leaked through.
        if re.match(r"^[A-Za-z_]+:\s", first_line):
            continue
        # Collapse internal whitespace so the paragraph fits one visual line.
        paragraph = _WS.sub(" ", block).strip()
        if len(paragraph) <= max_chars:
            return paragraph
        # Truncate at the last whole word inside the cap.
        cut = paragraph[: max_chars + 1]
        last_space = cut.rfind(" ")
        if last_space > 0:
            cut = cut[:last_space]
        return cut.rstrip(",.;:—-") + "…"

    return ""


# ----------------------------------------------------------------------
# Node collection — one pass over org/ produces the node table and a
# filename → id map so edges can resolve markdown links to ids.
# ----------------------------------------------------------------------

NODE_KINDS = [
    ("identity",          "identity",          "*.md"),
    ("language-term",     "language",          "*.md"),
    ("unit",              "nodes/units",       "*.md"),
    ("activity",          "nodes/activities",  "*.md"),
    ("person",            "nodes/people",      "*.md"),
    ("role",              "nodes/roles",       "*.md"),
    ("stakeholder",       "nodes/stakeholders","*.md"),
    ("commitment",        "commitments",       "*.md"),
    ("financial-summary", "financials",        "*.md"),
    ("source",            "sources",           "*.md"),
]


def collect_nodes(org_dir: Path) -> tuple[list[dict], dict[Path, str]]:
    """Walk org/ and produce (nodes, path_to_id).

    `path_to_id` maps the absolute file path of each node to its id, used
    later when resolving `[text](relative-path.md)` links in node bodies.
    """
    nodes: list[dict] = []
    path_to_id: dict[Path, str] = {}

    for kind, subdir, glob in NODE_KINDS:
        d = org_dir / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob(glob)):
            # Skip folder-doc stubs (each org/<subdir>/README.md is template
            # documentation, not a node). Without this filter every kind gets
            # one extra pseudo-node with id="README" and the audit fails on
            # duplicate ids.
            if f.name == "README.md":
                continue
            text = f.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            node_id = fm.get("id") or f.stem
            label = get_title(text) or node_id

            # State / kind-specific badge fields surfaced for the viewer.
            state = ""
            if kind == "commitment":
                state = fm.get("state", "")
            elif kind == "person":
                state = fm.get("status", "")

            # Description: frontmatter `description` wins (curated). Falls
            # back to the first prose paragraph of the body (extracted so
            # markdown links + emphasis survive into the inspect panel).
            description = ""
            if isinstance(fm.get("description"), str):
                description = fm["description"]
            else:
                description = extract_description(text)

            unit = fm.get("unit") if isinstance(fm.get("unit"), str) else ""
            performer = fm.get("performer") if isinstance(fm.get("performer"), str) else ""

            nodes.append({
                "id": node_id,
                "kind": kind,
                "label": label,
                "description": description,
                "_source_dir": str(f.parent.relative_to(org_dir)),
                "state": state,
                "unit": unit,
                "performer": performer,
                "_path": str(f.relative_to(org_dir)),
            })
            path_to_id[f.resolve()] = node_id

    # Second pass: rewrite each description's markdown link targets from
    # relative file paths (e.g. `../units/foo.md`) to bare node ids
    # (`foo`) when the target resolves to a node in the corpus. External
    # URLs and unresolvable targets stay as-is. This lets the viewer use
    # a trivial link_resolver (`lambda t: t if t in node_ids else None`)
    # without having to replicate path arithmetic at render time.
    node_ids = {n["id"] for n in nodes}
    for n in nodes:
        if not n["description"]:
            n.pop("_source_dir", None)
            continue
        source_dir = org_dir / n["_source_dir"]

        def _rewrite_target(m: re.Match) -> str:
            label, target = m.group(1), m.group(2)
            # External URLs and anchors pass through unchanged.
            if target.startswith(("http://", "https://", "//", "mailto:", "#")):
                return f"[{label}]({target})"
            # Resolve relative to the source file's directory.
            try:
                resolved = (source_dir / target).resolve()
            except (OSError, ValueError):
                return f"[{label}]({target})"
            target_id = path_to_id.get(resolved)
            if target_id and target_id in node_ids:
                return f"[{label}]({target_id})"
            return f"[{label}]({target})"

        n["description"] = LINK_RE.sub(_rewrite_target, n["description"])
        n.pop("_source_dir", None)

    return nodes, path_to_id


# ----------------------------------------------------------------------
# Edge collection — typed edges. Every edge cites its source kind so the
# viewer can colour or filter by relation.
# ----------------------------------------------------------------------

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
SOURCE_CITE_RE = re.compile(r"\(([a-z][a-z0-9-]+-\d{4}(?:-\d{2}-\d{2})?)\)", re.IGNORECASE)


def _add_edge(edges: list[dict], frm: str, to: str, kind: str, *, ids: set[str]) -> None:
    if not frm or not to or frm == to:
        return
    if frm not in ids or to not in ids:
        return
    edges.append({"from": frm, "to": to, "kind": kind})


def collect_edges(
    org_dir: Path,
    nodes: list[dict],
    path_to_id: dict[Path, str],
) -> list[dict]:
    edges: list[dict] = []
    ids = {n["id"] for n in nodes}
    seen: set[tuple[str, str, str]] = set()

    def add(frm: str, to: str, kind: str) -> None:
        key = (frm, to, kind)
        if key in seen:
            return
        seen.add(key)
        _add_edge(edges, frm, to, kind, ids=ids)

    for kind, subdir, glob in NODE_KINDS:
        d = org_dir / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob(glob)):
            # Same skip as in `collect_nodes` above — folder-doc README.md
            # stubs are not nodes and have no edges to declare.
            if f.name == "README.md":
                continue
            text = f.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            node_id = fm.get("id") or f.stem
            body = strip_frontmatter(text)

            # ---- frontmatter typed relations ----
            if kind == "unit":
                parent = fm.get("parent")
                if isinstance(parent, str) and parent and parent != "null":
                    add(node_id, parent, "parent")
                head = fm.get("head_role")
                if isinstance(head, str) and head and head != "null":
                    add(node_id, head, "head_role")

            elif kind == "person":
                u = fm.get("unit")
                if isinstance(u, str) and u and u != "null":
                    add(node_id, u, "unit")
                r = fm.get("role")
                if isinstance(r, str) and r and r != "null":
                    add(node_id, r, "holds_role")

            elif kind == "role":
                # Roles can list the activities they cover (per AGENTS.md).
                for a in (fm.get("activities") or []):
                    if isinstance(a, str) and a:
                        add(node_id, a, "covers")
                u = fm.get("unit")
                if isinstance(u, str) and u and u != "null":
                    add(node_id, u, "unit")

            elif kind == "activity":
                u = fm.get("unit")
                if isinstance(u, str) and u and u != "null":
                    add(node_id, u, "unit")
                p = fm.get("performer")
                if isinstance(p, str) and p and p != "null":
                    add(node_id, p, "performer")
                touched = fm.get("stakeholders_touched") or []
                if isinstance(touched, list):
                    for s in touched:
                        if isinstance(s, str) and s:
                            add(node_id, s, "touches")

            elif kind == "commitment":
                for party in (fm.get("parties_committing") or []):
                    if isinstance(party, str) and party:
                        add(node_id, party, "party_committing")
                for party in (fm.get("parties_benefiting") or []):
                    if isinstance(party, str) and party:
                        add(node_id, party, "party_benefiting")

            # ---- citations: frontmatter sources + body (source-id) ----
            for s in (fm.get("sources") or []):
                if isinstance(s, str) and s:
                    add(node_id, s, "cite")
            for m in SOURCE_CITE_RE.finditer(body):
                add(node_id, m.group(1), "cite")

            # ---- body markdown links resolving to another node ----
            for m in LINK_RE.finditer(body):
                target = m.group(2).strip()
                # Skip external links and anchors-only.
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                # Resolve relative to the file's directory.
                target_path = (f.parent / target).resolve()
                if target_path in path_to_id:
                    add(node_id, path_to_id[target_path], "link")

    return edges


# ----------------------------------------------------------------------
# Topology summary — surfaced in the build output so the agent has
# something to anchor decisions on without round-tripping the viewer.
# ----------------------------------------------------------------------

def topology_summary(nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    for n in nodes:
        by_kind[n["kind"]] = by_kind.get(n["kind"], 0) + 1

    by_edge_kind: dict[str, int] = {}
    for e in edges:
        by_edge_kind[e["kind"]] = by_edge_kind.get(e["kind"], 0) + 1

    # Degree per node (undirected; the leader cares about connectedness,
    # not direction). Surfaces the most-connected nodes and the isolates.
    deg: dict[str, int] = {n["id"]: 0 for n in nodes}
    for e in edges:
        deg[e["from"]] = deg.get(e["from"], 0) + 1
        deg[e["to"]]   = deg.get(e["to"], 0) + 1

    sorted_deg = sorted(deg.items(), key=lambda kv: kv[1], reverse=True)
    top_connected = [{"id": i, "degree": d} for i, d in sorted_deg[:8]]
    isolated = [i for i, d in sorted_deg if d == 0]

    return {
        "nodes_total": len(nodes),
        "edges_total": len(edges),
        "by_node_kind": by_kind,
        "by_edge_kind": by_edge_kind,
        "top_connected": top_connected,
        "isolated": isolated,
    }


def _read_org_name(org_dir: Path) -> str:
    """Pull the organisation's display name from `identity/mission.md`
    frontmatter (key: `org_name`). The viewer's dateline reads this.

    Looks at all `identity/*.md` files in case the convention drifts;
    the first `org_name` value wins. Falls back to a title-cased
    version of the org-dir basename when no frontmatter key is found
    so the chrome never collapses to a generic placeholder."""
    identity_dir = org_dir / "identity"
    if identity_dir.is_dir():
        for f in sorted(identity_dir.glob("*.md")):
            try:
                fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            name = (fm.get("org_name") or "").strip()
            if name:
                return name
    # Fallback: directory name, "kebab-case" → "Title Case".
    return org_dir.name.replace("-", " ").replace("_", " ").title()


def main() -> int:
    parser = argparse.ArgumentParser(description="Walk org/ and emit the whole graph.")
    parser.add_argument("--org-dir", required=True, help="Path to org/")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--scope", help="(reserved for future per-unit scoping; ignored today)")
    args = parser.parse_args()

    org_dir = Path(args.org_dir)
    if not org_dir.exists():
        print(f"org directory not found: {org_dir}", file=sys.stderr)
        return 1

    nodes, path_to_id = collect_nodes(org_dir)
    edges = collect_edges(org_dir, nodes, path_to_id)
    summary = topology_summary(nodes, edges)

    # Pull the org's display name out of identity/mission.md frontmatter
    # (key: `org_name`). Used by the viewer's dateline. Falls back to
    # the dataDir's basename, lightly cleaned, so the chrome never
    # collapses to "Value map" or similar generic placeholder.
    org_name = _read_org_name(org_dir)

    skeleton = {
        "_scope": args.scope or "whole-org",
        "_dated": date.today().isoformat(),
        "_org": org_name,
        "_topology": summary,
        "nodes": nodes,
        "edges": edges,
        # Agent fills these after reading the graph in the viewer.
        "decisions": [],
    }

    Path(args.out).write_text(json.dumps(skeleton, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {Path(args.out).resolve()} "
        f"(nodes={summary['nodes_total']}, edges={summary['edges_total']}, "
        f"isolates={len(summary['isolated'])})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
