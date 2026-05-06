#!/usr/bin/env python3
"""
world-model / build.py — Build a structure skeleton for the four-part analysis.

Walks org/ and emits a JSON skeleton that the agent fills with capability
contracts, world-model observations, intelligence-layer compositions, and
failure signals. The builder does not invent capabilities — it surfaces
candidates and provides the structure paths the agent will use as evidence.

Usage:
    python3 build.py --org-dir <path>
                     [--ai-exposure-matches <matches.json>]
                     [--scope <unit-id>]   # optional: scope to one Direzione
                     --out <skeleton.json>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
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


def collect_structure(org_dir: Path, scope_unit: str | None) -> dict[str, Any]:
    """Walk the structure and emit summary structures the agent will use."""
    units: list[dict] = []
    for f in sorted((org_dir / "nodes" / "units").glob("*.md")):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        units.append({
            "id": fm.get("id", f.stem),
            "title": get_title(f.read_text()) or fm.get("id", f.stem),
            "level": fm.get("level", ""),
            "parent": fm.get("parent", ""),
            "description": fm.get("description", ""),
            "_path": str(f.relative_to(org_dir.parent if org_dir.parent != Path('.') else org_dir)),
        })

    activities: list[dict] = []
    for f in sorted((org_dir / "nodes" / "activities").glob("*.md")):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        activities.append({
            "id": fm.get("id", f.stem),
            "title": get_title(f.read_text()) or fm.get("id", f.stem),
            "unit": fm.get("unit", ""),
            "description": fm.get("description", ""),
            "inputs": fm.get("inputs") if isinstance(fm.get("inputs"), list) else [],
            "outputs": fm.get("outputs") if isinstance(fm.get("outputs"), list) else [],
            "_path": str(f.relative_to(org_dir.parent if org_dir.parent != Path('.') else org_dir)),
        })

    stakeholders: list[dict] = []
    if (org_dir / "nodes" / "stakeholders").exists():
        for f in sorted((org_dir / "nodes" / "stakeholders").glob("*.md")):
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            stakeholders.append({
                "id": fm.get("id", f.stem),
                "title": get_title(f.read_text()) or fm.get("id", f.stem),
                "description": fm.get("description", ""),
                "_path": str(f.relative_to(org_dir.parent if org_dir.parent != Path('.') else org_dir)),
            })

    commitments: list[dict] = []
    if (org_dir / "commitments").exists():
        for f in sorted((org_dir / "commitments").glob("*.md")):
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            commitments.append({
                "id": fm.get("id", f.stem),
                "title": get_title(f.read_text()) or fm.get("id", f.stem),
                "level": fm.get("level", ""),
                "parties_committing": fm.get("parties_committing") if isinstance(fm.get("parties_committing"), list) else [],
                "parties_benefiting": fm.get("parties_benefiting") if isinstance(fm.get("parties_benefiting"), list) else [],
                "description": fm.get("description", ""),
                "state": fm.get("state", ""),
                "_path": str(f.relative_to(org_dir.parent if org_dir.parent != Path('.') else org_dir)),
            })

    # Activities by unit
    by_unit = defaultdict(list)
    for a in activities:
        if a["unit"]:
            by_unit[a["unit"]].append(a["id"])

    return {
        "units": units,
        "activities": activities,
        "stakeholders": stakeholders,
        "commitments": commitments,
        "activity_count_by_unit": dict(by_unit),
    }


def aei_summary(matches_path: Path | None, activities: list[dict]) -> dict[str, Any]:
    """Summarize AEI signal at the org level — feeds the intelligence-layer section."""
    if not matches_path or not matches_path.exists():
        return {"available": False}
    matches = json.loads(matches_path.read_text(encoding="utf-8"))
    rich_count = 0
    autonomy_high = 0
    autonomy_med = 0
    by_act = {}
    for m in matches:
        top = m.get("matches", [])
        rich_top = [t for t in top if t.get("ai_autonomy_mean") is not None]
        if rich_top:
            rich_count += 1
            max_aut = max(t["ai_autonomy_mean"] for t in rich_top)
            if max_aut >= 3.57:
                autonomy_high += 1
            elif max_aut >= 3.21:
                autonomy_med += 1
            by_act[m["id"]] = {"max_autonomy": round(max_aut, 2), "rich_count": len(rich_top)}
    return {
        "available": True,
        "activities_with_rich_aei": rich_count,
        "activities_high_autonomy": autonomy_high,
        "activities_medium_autonomy": autonomy_med,
        "activities_total": len(matches),
        "_per_activity": by_act,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build world-model structure skeleton.")
    parser.add_argument("--org-dir", required=True, help="Path to org/")
    parser.add_argument("--ai-exposure-matches", help="Optional matches.json from skills/playbooks/ai-exposure")
    parser.add_argument("--scope", help="Optional unit id to scope analysis (default: whole org)")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    org_dir = Path(args.org_dir)
    if not org_dir.exists():
        print(f"org directory not found: {org_dir}", file=sys.stderr)
        return 1

    structure = collect_structure(org_dir, args.scope)
    aei = aei_summary(Path(args.ai_exposure_matches) if args.ai_exposure_matches else None, structure["activities"])

    skeleton = {
        "_scope": args.scope or "whole-org",
        "_structure_summary": {
            "units_total": len(structure["units"]),
            "activities_total": len(structure["activities"]),
            "stakeholders_total": len(structure["stakeholders"]),
            "commitments_total": len(structure["commitments"]),
            "divisions": [u["id"] for u in structure["units"] if u.get("level") == "division"],
            "areas": [u["id"] for u in structure["units"] if u.get("level") == "area"],
        },
        "_aei_summary": aei,
        "_structure": structure,
        # Agent fills these:
        "capabilities": [],          # list of capability dicts
        "world_model_company": {     # how the org understands itself
            "observations": [],      # list of {dimension, lives_in, maturity, gaps}
            "overall_maturity": "",  # high|medium|low
        },
        "world_model_customer": {    # per-stakeholder representation
            "by_stakeholder": [],    # list of {type, honest_signal, current_maturity, fragmentation}
            "is_unified": False,     # whether a unified per-stakeholder view exists
        },
        "intelligence_layer": {
            "exists": False,
            "current_human_compositions": [],   # list of {trigger, capabilities_composed, failure_modes}
            "potential_compositions": [],       # list of {trigger, capabilities, precondition}
        },
        "interfaces": [],            # list of {name, surfaces_capabilities, _structure}
        "failure_signals": [],       # list of {trigger, composition_attempted, missing_capability, structure_evidence}
    }

    Path(args.out).write_text(json.dumps(skeleton, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {Path(args.out).resolve()} "
        f"(units={skeleton['_structure_summary']['units_total']}, "
        f"activities={skeleton['_structure_summary']['activities_total']}, "
        f"stakeholders={skeleton['_structure_summary']['stakeholders_total']}, "
        f"commitments={skeleton['_structure_summary']['commitments_total']}, "
        f"aei_available={aei['available']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
