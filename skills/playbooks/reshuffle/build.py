#!/usr/bin/env python3
"""
reshuffle / build.py — Build a slice skeleton with constraint signals.

Walks structure edges starting from the slice anchor, enumerates activities
in scope, and emits a JSON skeleton ready for the agent to classify each
activity by primary constraint, dominant knowledge-management cost, and
tool/engine. Optionally attaches AEI matches and value-map positions.

Usage:
    python3 build.py --slice <id> --kind commitment|unit --org-dir <path>
                     [--ai-exposure-matches <matches.json>]
                     [--value-map <map.json>]
                     --out <skeleton.json>
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
                fm[key] = [] if not inner else [x.strip().strip('"').strip("'") for x in inner.split(",")]
            else:
                fm[key] = val.strip('"').strip("'")
    return fm


def get_title(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def get_body_text(text: str, max_chars: int = 600) -> str:
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    body = re.sub(r"^#\s+.*\n", "", body, count=1)
    parts = re.split(r"\n##\s+", body, maxsplit=1)
    body = parts[0]
    body = re.sub(r"^>.*\n", "", body, flags=re.M)
    body = body.strip()
    if len(body) > max_chars:
        cut = body[:max_chars].rsplit(". ", 1)[0]
        body = cut + "."
    return body


def find_activities_for_unit(org_dir: Path, unit_id: str) -> list[dict]:
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
                "performer": fm.get("performer", ""),
                "inputs": fm.get("inputs") if isinstance(fm.get("inputs"), list) else [],
                "outputs": fm.get("outputs") if isinstance(fm.get("outputs"), list) else [],
                "_path": str(f.relative_to(org_dir.parent if org_dir.parent != Path('.') else org_dir)),
            })
    return out


def find_child_units(org_dir: Path, parent_id: str) -> list[str]:
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
    units_dir = org_dir / "nodes" / "units"
    f = units_dir / f"{unit_id}.md"
    if not f.exists():
        return [unit_id]
    fm = parse_frontmatter(f.read_text(encoding="utf-8"))
    if fm.get("level") == "division" and not find_activities_for_unit(org_dir, unit_id):
        children = find_child_units(org_dir, unit_id)
        if children:
            return children
    return [unit_id]


def resolve_party_kind(org_dir: Path, party_id: str) -> str:
    if (org_dir / "nodes" / "units" / f"{party_id}.md").exists():
        return "unit"
    if (org_dir / "nodes" / "stakeholders" / f"{party_id}.md").exists():
        return "stakeholder"
    return "unknown"


def load_node(org_dir: Path, kind: str, node_id: str) -> tuple[dict, str]:
    candidates = {
        "commitment": [org_dir / "commitments" / f"{node_id}.md"],
        "unit": [org_dir / "nodes" / "units" / f"{node_id}.md"],
    }
    for path in candidates.get(kind, []):
        if path.exists():
            text = path.read_text(encoding="utf-8")
            return parse_frontmatter(text), get_title(text)
    raise FileNotFoundError(f"{kind} '{node_id}' not found in {org_dir}")


# Structure signals that hint at a constraint type (suggestions, not facts).
# The agent decides; the audit verifies citation.

CONSTRAINT_HINTS = {
    "risk": [
        "codice civile", "codice etico", "modello 231", "ordinamento forense",
        "delibera cda", "statuto", "compliance", "audit", "accountability",
        "atto notarile", "certif", "rischio",
    ],
    "scarcity": [
        "albo", "abilitazione", "iscrizione", "competenza specialistica",
        "lead", "ruolo unico", "responsabile", "expertise",
    ],
    "coordination": [
        "trasversale", "cross-area", "cross-direzione", "matriciale",
        "handover", "passaggio", "coordinamento", "sinergia",
        "sub-team", "stream", "borrowed",
    ],
}


def hint_constraint(text: str) -> list[str]:
    """Return constraint types whose hint terms appear in the text. Suggestions only."""
    t = text.lower()
    out = []
    for ctype, terms in CONSTRAINT_HINTS.items():
        for term in terms:
            if term in t:
                out.append(ctype)
                break
    return out


def attach_aei(components: list[dict], matches_path: Path) -> int:
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


def attach_value_map(components: list[dict], vmap_path: Path) -> int:
    vmap = json.loads(vmap_path.read_text(encoding="utf-8"))
    by_sid = {c.get("_structure_id"): c for c in vmap.get("components", []) if c.get("_structure_id")}
    attached = 0
    for c in components:
        sid = c.get("_structure_id")
        if sid and sid in by_sid:
            v = by_sid[sid]
            c["_value_map"] = {
                "evolution": v.get("evolution"),
                "evolution_target": v.get("evolution_target"),
                "visibility": v.get("visibility"),
                "ai_effect": v.get("ai_effect"),
            }
            attached += 1
    return attached


def main() -> int:
    parser = argparse.ArgumentParser(description="Build reshuffle slice skeleton from structure.")
    parser.add_argument("--slice", required=True, help="Slice id (commitment or unit)")
    parser.add_argument("--kind", required=True, choices=["commitment", "unit"], help="Slice anchor type")
    parser.add_argument("--org-dir", required=True, help="Path to org/")
    parser.add_argument("--ai-exposure-matches", help="Optional matches.json from skills/playbooks/ai-exposure")
    parser.add_argument("--value-map", help="Optional value-map JSON to overlay positions")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    org_dir = Path(args.org_dir)
    if not org_dir.exists():
        print(f"org directory not found: {org_dir}", file=sys.stderr)
        return 1

    anchor_fm, anchor_title = load_node(org_dir, args.kind, args.slice)

    # Determine in-scope parties (mirror value-map logic).
    if args.kind == "commitment":
        raw_parties = anchor_fm.get("parties_committing") or anchor_fm.get("parties_benefiting") or []
        if isinstance(raw_parties, str):
            raw_parties = [raw_parties]
    else:
        raw_parties = [args.slice]

    scope_units: list[str] = []
    scope_stakeholders: list[str] = []
    for p in raw_parties:
        k = resolve_party_kind(org_dir, p)
        if k == "unit":
            scope_units.extend(expand_unit_scope(org_dir, p))
        elif k == "stakeholder":
            scope_stakeholders.append(p)
        else:
            print(f"Warning: party '{p}' not found in structure", file=sys.stderr)

    seen: set[str] = set()
    scope_units = [u for u in scope_units if not (u in seen or seen.add(u))]

    # Cross-direzione handover hint: walk up parent chain to root direzione.
    def walk_to_direzione(unit_id: str) -> str | None:
        seen_walk: set[str] = set()
        current = unit_id
        while current and current not in seen_walk:
            seen_walk.add(current)
            f = org_dir / "nodes" / "units" / f"{current}.md"
            if not f.exists():
                return None
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            if current.startswith("direzione-") or fm.get("level") == "division":
                return current
            current = fm.get("parent")
        return None

    cross_direzione = set()
    for u in scope_units:
        d = walk_to_direzione(u)
        if d:
            cross_direzione.add(d)

    activities: list[dict] = []
    for u in scope_units:
        activities.extend(find_activities_for_unit(org_dir, u))

    components: list[dict] = []
    next_id = 1

    # Bundle-level signals from the anchor itself.
    # For commitments: terms + consequences_if_broken.
    # For units: description + scope text from the body (read from file).
    anchor_text_parts = [
        anchor_fm.get("terms", ""),
        anchor_fm.get("description", ""),
        " ".join(anchor_fm.get("consequences_if_broken") or []),
    ]
    if args.kind == "unit":
        f = org_dir / "nodes" / "units" / f"{args.slice}.md"
        if f.exists():
            anchor_text_parts.append(get_body_text(f.read_text(encoding="utf-8"), max_chars=1200))
    anchor_text = " ".join(anchor_text_parts)
    bundle_hints = hint_constraint(anchor_text)

    for a in activities:
        cid = f"a{next_id}"; next_id += 1
        sig_text = a["description"] + " " + a["body"] + " " + " ".join(a["inputs"] + a["outputs"])
        components.append({
            "id": cid,
            "label": a["title"],
            "_structure_id": a["id"],
            "_unit": a["unit"],
            "_description": a["description"],
            "_body": a["body"],
            "_constraint_hints": hint_constraint(sig_text),
            # Agent fills these in step 3:
            # "primary_constraint": "scarcity"|"risk"|"coordination",
            # "constraint_evidence": [{"source": "...", "claim": "..."}],
            # "km_cost_dominant": "encoding"|"organizing"|"deploying"|"none",
            # "ai_classification": "tool"|"engine"|"not-applicable",
            # "ai_evidence": [...],
        })

    # Stakeholders as external actors in the bundle.
    for s in scope_stakeholders:
        f = org_dir / "nodes" / "stakeholders" / f"{s}.md"
        text = f.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        cid = f"s{next_id}"; next_id += 1
        components.append({
            "id": cid,
            "label": get_title(text) or s,
            "_structure_id": s,
            "_kind": "stakeholder",
            "_description": fm.get("description", ""),
        })

    aei_attached = 0
    if args.ai_exposure_matches:
        aei_attached = attach_aei(components, Path(args.ai_exposure_matches))

    vmap_attached = 0
    if args.value_map:
        vmap_attached = attach_value_map(components, Path(args.value_map))

    skeleton = {
        "_anchor": {
            "id": args.slice,
            "kind": args.kind,
            "title": anchor_title,
            "description": anchor_fm.get("description", ""),
            "terms": anchor_fm.get("terms", ""),
        },
        "_dated": date.today().isoformat(),
        "_scope": {
            "units": scope_units,
            "stakeholders": scope_stakeholders,
            "direzioni_spanned": sorted(cross_direzione),
            "bundle_constraint_hints_from_anchor": bundle_hints,
        },
        "components": components,
        # Agent fills in step 4-5:
        "bundle_state": {
            # "current_mode": "see-saw"|"flywheel",
            # "mode_evidence": [...],
            # "constraint_distribution": {...},  # filled by audit summary
            # "coordination_paradox_risk": "..." (string, agent-authored),
        },
        "engine_candidates": [],   # filled in step 5: list of {ai_use, dissolves_constraint, evidence}
        "rebundle_candidates": [], # filled in step 5
    }

    Path(args.out).write_text(json.dumps(skeleton, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {Path(args.out).resolve()} "
        f"(units={len(scope_units)}, activities={len(activities)}, stakeholders={len(scope_stakeholders)}, "
        f"direzioni_spanned={len(cross_direzione)}, components={len(components)}, "
        f"aei_attached={aei_attached}, value_map_attached={vmap_attached})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
