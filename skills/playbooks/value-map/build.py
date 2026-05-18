#!/usr/bin/env python3
"""
value-map / build.py — Build a value-chain skeleton from structure edges.

Reads the anchor (a commitment or a unit), walks structure edges, and emits
a WardleyMap JSON skeleton with components extracted from structure activities
and the dependency edges derived from activity input/output frontmatter.

The skeleton is deterministic. The agent positions components and writes
ai_effect / evolution_target in a follow-up step (see SKILL.md §3).

Usage:
    python3 build.py --anchor <id> --kind commitment|unit --org-dir <path>
                     [--ai-exposure-matches <path-to-matches.json>]
                     --out <chain.json>

The optional --ai-exposure-matches attaches the matched O*NET tasks (top-K
from match.py) to each activity component as a hidden `_aei` field, so the
agent can consult AEI evidence when filling ai_effect / evolution_target.
The audit gate later strips `_aei` from the final JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


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
        # List continuation: "  - item"
        cont = re.match(r"^\s*-\s*(.+)$", line)
        if cont and current_key:
            v = cont.group(1).strip().strip('"').strip("'")
            fm.setdefault(current_key, [])
            if isinstance(fm[current_key], list):
                fm[current_key].append(v)
            continue
        # key: value
        kv = re.match(r"^([\w_]+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            current_key = key
            if val == "":
                fm[key] = []  # tentative; may stay empty or be list-filled
            elif val.startswith("[") and val.endswith("]"):
                # inline list
                inner = val[1:-1].strip()
                if not inner:
                    fm[key] = []
                else:
                    items = [x.strip().strip('"').strip("'") for x in inner.split(",")]
                    fm[key] = items
            else:
                fm[key] = val.strip('"').strip("'")
    return fm


def get_title(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def _clean_title(raw: str) -> str:
    """Strip markdown link syntax from a node title.

    AIRC commitment titles often inline a markdown link to the other
    party: `AIRC ↔ [ricercatori-finanziati](../nodes/stakeholders/
    ricercatori-finanziati.md), grant agreement`. The bracket-and-
    parens leaked into the dateline as visible characters. Reduce to
    the label and let the chrome treat it as plain text.
    """
    return _MD_LINK_RE.sub(r"\1", raw).strip()


def load_node(org_dir: Path, kind: str, node_id: str) -> tuple[dict, str]:
    """Return (frontmatter, title) for a structure node. Title is
    normalised to plain text (markdown link syntax stripped)."""
    candidates = {
        "commitment": [org_dir / "commitments" / f"{node_id}.md"],
        "unit": [org_dir / "nodes" / "units" / f"{node_id}.md"],
        "activity": [org_dir / "nodes" / "activities" / f"{node_id}.md"],
    }
    for path in candidates.get(kind, []):
        if path.exists():
            text = path.read_text(encoding="utf-8")
            return parse_frontmatter(text), _clean_title(get_title(text))
    raise FileNotFoundError(f"{kind} '{node_id}' not found in {org_dir}")


def get_body_text(text: str, max_chars: int = 600) -> str:
    """Extract the first informative paragraph after the title.

    Skips the frontmatter and the title heading. Stops at the first ##
    sub-heading or after max_chars, whichever comes first. Strips block
    quotes and verbatim role-description cites — keeps the substantive prose.
    """
    # Strip frontmatter.
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    # Drop leading whitespace then drop the title heading. Without the
    # lstrip the regex `^#` doesn't match because the string starts with
    # the blank line following the closing `---`.
    body = body.lstrip()
    body = re.sub(r"^#\s+.*\n", "", body, count=1)
    body = body.lstrip()
    # Truncate at first sub-heading.
    parts = re.split(r"\n##\s+", body, maxsplit=1)
    body = parts[0]
    # Drop blockquote prefixes (verbatim quotes from funzionigrammi).
    body = re.sub(r"^>.*\n", "", body, flags=re.M)
    body = body.strip()
    if len(body) > max_chars:
        # Trim at sentence boundary if possible.
        cut = body[:max_chars].rsplit(". ", 1)[0]
        body = cut + "."
    return body


def find_activities_for_unit(org_dir: Path, unit_id: str) -> list[dict]:
    """Scan activities/ for files whose frontmatter unit == unit_id."""
    out: list[dict] = []
    activities_dir = org_dir / "nodes" / "activities"
    if not activities_dir.exists():
        return out
    for f in sorted(activities_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm.get("unit") == unit_id:
            out.append({
                "id": fm.get("id", f.stem),
                "title": get_title(text) or fm.get("id", f.stem),
                "description": fm.get("description", ""),
                "body": get_body_text(text),
                "unit": unit_id,
                "inputs": fm.get("inputs") if isinstance(fm.get("inputs"), list) else [],
                "outputs": fm.get("outputs") if isinstance(fm.get("outputs"), list) else [],
                "performer": fm.get("performer", ""),
                "_path": str(f.relative_to(org_dir.parent if org_dir.parent != Path('.') else org_dir)),
            })
    return out


def find_child_units(org_dir: Path, parent_id: str) -> list[str]:
    """Return ids of units whose parent == parent_id."""
    out: list[str] = []
    units_dir = org_dir / "nodes" / "units"
    if not units_dir.exists():
        return out
    for f in sorted(units_dir.glob("*.md")):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        if fm.get("parent") == parent_id:
            out.append(fm.get("id", f.stem))
    return out


def expand_unit_scope(org_dir: Path, unit_id: str) -> list[str]:
    """If the unit is a division (level=division) with no direct activities,
    expand to its child units. Otherwise return [unit_id]."""
    units_dir = org_dir / "nodes" / "units"
    f = units_dir / f"{unit_id}.md"
    if not f.exists():
        return [unit_id]
    fm = parse_frontmatter(f.read_text(encoding="utf-8"))
    level = fm.get("level", "")
    direct_activities = find_activities_for_unit(org_dir, unit_id)
    if level == "division" and not direct_activities:
        children = find_child_units(org_dir, unit_id)
        if children:
            return children
    return [unit_id]


def resolve_party_kind(org_dir: Path, party_id: str) -> str:
    """Return 'unit' | 'stakeholder' | 'unknown' based on structure location."""
    if (org_dir / "nodes" / "units" / f"{party_id}.md").exists():
        return "unit"
    if (org_dir / "nodes" / "stakeholders" / f"{party_id}.md").exists():
        return "stakeholder"
    return "unknown"


def build_io_edges(activities: list[dict], component_id_by_structure: dict[str, str]) -> list[dict]:
    """Edge from A to B when output of A overlaps with input of B."""
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for a in activities:
        for b in activities:
            if a["id"] == b["id"]:
                continue
            outs = set(a["outputs"])
            ins = set(b["inputs"])
            if outs & ins:
                ca = component_id_by_structure[a["id"]]
                cb = component_id_by_structure[b["id"]]
                key = (ca, cb)
                if key not in seen:
                    edges.append({"from": ca, "to": cb})
                    seen.add(key)
    return edges


def build_unit_to_activity_edges(activities: list[dict], unit_component_id: dict[str, str], component_id_by_structure: dict[str, str]) -> list[dict]:
    """Edge from each unit container to its activities."""
    edges: list[dict] = []
    for a in activities:
        if a["unit"] in unit_component_id:
            edges.append({"from": unit_component_id[a["unit"]], "to": component_id_by_structure[a["id"]]})
    return edges


def attach_aei(components: list[dict], matches_path: Path) -> int:
    """Attach `_aei` to each component whose structure id matches an entry in matches.json."""
    matches = json.loads(matches_path.read_text(encoding="utf-8"))
    by_id = {m["id"]: m for m in matches}
    attached = 0
    for c in components:
        sid = c.get("_structure_id")
        if sid and sid in by_id:
            mm = by_id[sid]
            top = mm.get("matches", [])[:3]
            c["_aei"] = {
                "low_confidence": mm.get("low_confidence", False),
                "top_matches": [
                    {
                        "task": t.get("task"),
                        "similarity": round(t.get("similarity", 0), 3),
                        "ai_autonomy_mean": t.get("ai_autonomy_mean"),
                        "count": t.get("count"),
                        "in_rich": t.get("ai_autonomy_mean") is not None,
                    }
                    for t in top
                ],
            }
            attached += 1
    return attached


def _read_org_name(org_dir: Path) -> str:
    """Pull the organisation's display name from `identity/mission.md`
    frontmatter (key: `org_name`) — same convention as graph/build.py.
    Falls back to a title-cased version of the org-dir basename."""
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
    return org_dir.name.replace("-", " ").replace("_", " ").title()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build WardleyMap skeleton from structure.")
    parser.add_argument("--anchor", required=True, help="Anchor id (commitment or unit)")
    parser.add_argument("--kind", required=True, choices=["commitment", "unit"], help="Anchor type")
    parser.add_argument("--org-dir", required=True, help="Path to org/")
    parser.add_argument("--ai-exposure-matches", help="Optional matches.json from skills/playbooks/ai-exposure")
    parser.add_argument("--out", required=True, help="Output JSON path for the skeleton")
    args = parser.parse_args()

    org_dir = Path(args.org_dir)
    if not org_dir.exists():
        print(f"org directory not found: {org_dir}", file=sys.stderr)
        return 1

    anchor_fm, anchor_title = load_node(org_dir, args.kind, args.anchor)

    # 1. Determine in-scope parties.
    if args.kind == "commitment":
        raw_parties = anchor_fm.get("parties_committing") or anchor_fm.get("parties_benefiting") or []
        if isinstance(raw_parties, str):
            raw_parties = [raw_parties]
    else:  # unit anchor — only the unit itself
        raw_parties = [args.anchor]

    # Split parties into units and stakeholders, expand divisions.
    scope_units: list[str] = []
    scope_stakeholders: list[str] = []
    for p in raw_parties:
        kind = resolve_party_kind(org_dir, p)
        if kind == "unit":
            expanded = expand_unit_scope(org_dir, p)
            scope_units.extend(expanded)
        elif kind == "stakeholder":
            scope_stakeholders.append(p)
        else:
            print(f"Warning: party '{p}' not found in structure (units or stakeholders)", file=sys.stderr)

    # De-dup units while preserving order.
    seen_u: set[str] = set()
    scope_units = [u for u in scope_units if not (u in seen_u or seen_u.add(u))]

    # 2. Load unit records and find activities.
    unit_records: dict[str, tuple[dict, str]] = {}
    for u in scope_units:
        try:
            unit_records[u] = load_node(org_dir, "unit", u)
        except FileNotFoundError:
            print(f"Warning: unit '{u}' not found in structure", file=sys.stderr)
            continue

    stakeholder_records: dict[str, tuple[dict, str]] = {}
    for s in scope_stakeholders:
        text = (org_dir / "nodes" / "stakeholders" / f"{s}.md").read_text(encoding="utf-8")
        stakeholder_records[s] = (parse_frontmatter(text), get_title(text))

    activities: list[dict] = []
    for u in scope_units:
        activities.extend(find_activities_for_unit(org_dir, u))

    # 3. Build components. One per unit (kind=unit) + one per activity (kind=activity).
    components: list[dict] = []
    component_id_by_structure: dict[str, str] = {}
    unit_component_id: dict[str, str] = {}

    next_id = 1

    for u, (fm, title) in unit_records.items():
        cid = f"c{next_id}"; next_id += 1
        components.append({
            "id": cid,
            "label": title or u,
            "_structure_id": u,
            "_kind": "unit",
            "_description": fm.get("description", ""),
        })
        unit_component_id[u] = cid
        component_id_by_structure[u] = cid

    for a in activities:
        cid = f"c{next_id}"; next_id += 1
        components.append({
            "id": cid,
            "label": a["title"],
            "_structure_id": a["id"],
            "_kind": "activity",
            "_unit": a["unit"],
            "_description": a["description"],
            "_body": a["body"],
            "_inputs": a["inputs"],
            "_outputs": a["outputs"],
        })
        component_id_by_structure[a["id"]] = cid

    # Stakeholders as external components (no activities, just nodes).
    for s, (fm, title) in stakeholder_records.items():
        cid = f"c{next_id}"; next_id += 1
        components.append({
            "id": cid,
            "label": title or s,
            "_structure_id": s,
            "_kind": "stakeholder",
            "_description": fm.get("description", ""),
        })
        component_id_by_structure[s] = cid

    # 4. Build edges.
    edges: list[dict] = []
    edges.extend(build_unit_to_activity_edges(activities, unit_component_id, component_id_by_structure))
    edges.extend(build_io_edges(activities, component_id_by_structure))
    # De-dup
    seen_edges = set()
    deduped_edges = []
    for e in edges:
        key = (e["from"], e["to"])
        if key not in seen_edges:
            deduped_edges.append(e)
            seen_edges.add(key)
    edges = deduped_edges

    # 5. Attach AEI if available.
    aei_attached = 0
    if args.ai_exposure_matches:
        aei_attached = attach_aei(components, Path(args.ai_exposure_matches))

    # 6. Emit skeleton.
    skeleton = {
        "_anchor": {
            "id": args.anchor,
            "kind": args.kind,
            "title": anchor_title,
            "description": anchor_fm.get("description", ""),
            "terms": anchor_fm.get("terms", ""),
        },
        "_dated": date.today().isoformat(),
        "_org": _read_org_name(Path(args.org_dir)),
        "_scope_units": scope_units,
        "end_user": "",  # agent fills
        "new_end_users": [],
        "anchors": [],   # agent fills
        "components": components,
        "edges": edges,
        "new_value": [],
    }

    Path(args.out).write_text(json.dumps(skeleton, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {Path(args.out).resolve()} "
        f"(units={len(unit_records)}, activities={len(activities)}, "
        f"stakeholders={len(stakeholder_records)}, components={len(components)}, "
        f"edges={len(edges)}, aei_attached={aei_attached})"
    )

    if len(components) > 16:
        print(
            f"Note: {len(components)} components in skeleton. "
            f"Wardley convention is 12-16 per map. "
            f"Agent should prune to the value-chain core in step 3.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
