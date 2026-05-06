#!/usr/bin/env python3
"""
value-map / audit.py — Verify a WardleyMap JSON before commit.

Deterministic gate: catches missing positions, broken edges, schema-rule
violations, components without structure evidence, and ai_effect / numerical
claims that don't trace to attached AEI matches.

Usage:
    python3 audit.py --map <chain.json> --org-dir <path>
                     [--ai-exposure-matches <path-to-matches.json>]

Exit code:
    0 = audit passed
    1 = audit failed (issues listed)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

P25, P75 = 3.21, 3.57

GENESIS_BAND = (0.00, 0.17)
CUSTOM_BAND = (0.17, 0.40)
PRODUCT_BAND = (0.40, 0.70)
COMMODITY_BAND = (0.70, 1.01)


def in_band(value: float, band: tuple[float, float]) -> bool:
    return band[0] <= value < band[1]


def stage_for(value: float) -> str:
    if in_band(value, GENESIS_BAND):
        return "genesis"
    if in_band(value, CUSTOM_BAND):
        return "custom"
    if in_band(value, PRODUCT_BAND):
        return "product"
    return "commodity"


def extract_numbers(text: str) -> list[str]:
    """Extract integers and decimals from text (preserving original form)."""
    return [m.group(0) for m in re.finditer(r"\d+(?:[.,]\d+)?", text)]


def numbers_match_aei(numbers: list[str], aei: dict | None) -> tuple[list[str], list[str]]:
    """Split (matched, unmatched) numbers against an _aei block."""
    if not aei or not aei.get("top_matches"):
        return [], numbers
    pool = set()
    for m in aei["top_matches"]:
        if m.get("ai_autonomy_mean") is not None:
            v = round(float(m["ai_autonomy_mean"]), 2)
            pool.add(f"{v:.2f}")
            pool.add(f"{round(v, 1):.1f}")
            pool.add(str(int(round(v))))
        if m.get("count") is not None:
            try:
                c = int(m["count"])
                pool.add(str(c))
            except (TypeError, ValueError):
                pass
        if m.get("similarity") is not None:
            s = round(float(m["similarity"]), 2)
            pool.add(f"{s:.2f}")
            pool.add(str(int(round(s * 100))))
    matched, unmatched = [], []
    for n in numbers:
        norm = n.replace(",", ".")
        if norm in pool or n in pool:
            matched.append(n)
        else:
            try:
                if int(norm) <= 5:
                    matched.append(n)  # benign small integer
                    continue
            except ValueError:
                try:
                    if 0 <= float(norm) <= 5.0:
                        matched.append(n)
                        continue
                except ValueError:
                    pass
            unmatched.append(n)
    return matched, unmatched


def audit_components(comps: list[dict]) -> list[str]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    for c in comps:
        cid = c.get("id", "")
        label = c.get("label", "?")
        # Schema rules.
        if "evolution" not in c:
            issues.append(f"  [{cid} {label}] missing 'evolution'")
        else:
            ev = c["evolution"]
            if not isinstance(ev, (int, float)) or not (0.0 <= ev <= 1.0):
                issues.append(f"  [{cid} {label}] 'evolution' out of range: {ev}")
        if "visibility" not in c:
            issues.append(f"  [{cid} {label}] missing 'visibility'")
        else:
            vis = c["visibility"]
            if not isinstance(vis, (int, float)) or not (0.0 <= vis <= 1.0):
                issues.append(f"  [{cid} {label}] 'visibility' out of range: {vis}")
        # is_new + evolution_target combo
        if c.get("is_new") and c.get("evolution_target") is not None:
            issues.append(f"  [{cid} {label}] is_new=true cannot combine with evolution_target")
        # evolution_target must be > evolution
        if c.get("evolution_target") is not None and c.get("evolution") is not None:
            if c["evolution_target"] < c["evolution"]:
                issues.append(
                    f"  [{cid} {label}] evolution_target ({c['evolution_target']}) "
                    f"< evolution ({c['evolution']})"
                )
        # Structure grounding
        if not c.get("_structure_id") and not c.get("is_new"):
            issues.append(
                f"  [{cid} {label}] has no _structure_id and is not is_new — "
                f"agent inserted a component without structure evidence"
            )
        # ai_effect must trace to AEI when present
        ai_eff = c.get("ai_effect", "")
        if ai_eff:
            nums = extract_numbers(ai_eff)
            if nums:
                _, unmatched = numbers_match_aei(nums, c.get("_aei"))
                if unmatched:
                    issues.append(
                        f"  [{cid} {label}] ai_effect cites numbers not in _aei: {unmatched}"
                    )
            if not c.get("_aei") and not c.get("is_new"):
                issues.append(
                    f"  [{cid} {label}] ai_effect set but no _aei attached — "
                    f"either remove ai_effect or attach AEI evidence"
                )
        # evolution_target evidence — require at least one rich AEI match
        et = c.get("evolution_target")
        if et is not None:
            aei = c.get("_aei") or {}
            top = aei.get("top_matches") or []
            rich = [t for t in top if t.get("ai_autonomy_mean") is not None]
            if not aei:
                issues.append(
                    f"  [{cid} {label}] evolution_target set but no _aei attached — "
                    f"either remove the target or attach AEI evidence"
                )
            elif not rich:
                issues.append(
                    f"  [{cid} {label}] evolution_target set but _aei has no rich matches — "
                    f"a rightward shift requires observed AEI evidence (autonomy data); "
                    f"only fallback matches available — remove evolution_target"
                )
        # id uniqueness
        if cid in seen_ids:
            issues.append(f"  duplicate component id '{cid}'")
        seen_ids.add(cid)
    return issues


def audit_anchors(anchors: list[dict]) -> list[str]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    for a in anchors:
        aid = a.get("id", "")
        label = a.get("label", "?")
        if "evolution" not in a:
            issues.append(f"  [anchor {aid} {label}] missing 'evolution'")
        if a.get("is_new") and a.get("evolution_target") is not None:
            issues.append(f"  [anchor {aid} {label}] is_new=true cannot combine with evolution_target")
        if a.get("evolution_target") is not None and a.get("evolution") is not None:
            if a["evolution_target"] < a["evolution"]:
                issues.append(
                    f"  [anchor {aid} {label}] evolution_target ({a['evolution_target']}) "
                    f"< evolution ({a['evolution']})"
                )
        if not a.get("label"):
            issues.append(f"  [anchor {aid}] missing 'label'")
        if aid in seen_ids:
            issues.append(f"  duplicate anchor id '{aid}'")
        seen_ids.add(aid)
    return issues


def audit_edges(edges: list[dict], anchors: list[dict], components: list[dict], end_users: list[str]) -> list[str]:
    issues: list[str] = []
    valid_ids = {a["id"] for a in anchors} | {c["id"] for c in components}
    # End-user pseudo-ids: __user_0__, __user_1__, ...
    for i in range(len(end_users)):
        valid_ids.add(f"__user_{i}__")
    for i, e in enumerate(edges):
        if "from" not in e or "to" not in e:
            issues.append(f"  edge[{i}] malformed (missing from/to)")
            continue
        if e["from"] not in valid_ids:
            issues.append(f"  edge[{i}] from '{e['from']}' not in anchors/components/users")
        if e["to"] not in valid_ids:
            issues.append(f"  edge[{i}] to '{e['to']}' not in anchors/components/users")
    return issues


def audit_structure_existence(components: list[dict], org_dir: Path) -> list[str]:
    """Check that _structure_id values point to real files."""
    issues: list[str] = []
    for c in components:
        sid = c.get("_structure_id")
        kind = c.get("_kind", "")
        if not sid:
            continue
        candidates = [
            org_dir / "nodes" / "units" / f"{sid}.md",
            org_dir / "nodes" / "activities" / f"{sid}.md",
            org_dir / "commitments" / f"{sid}.md",
            org_dir / "nodes" / "stakeholders" / f"{sid}.md",
        ]
        if not any(p.exists() for p in candidates):
            issues.append(
                f"  [{c.get('id')} {c.get('label')}] _structure_id '{sid}' not found in structure"
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a WardleyMap JSON before commit.")
    parser.add_argument("--map", required=True, help="WardleyMap JSON path")
    parser.add_argument("--org-dir", required=True, help="Path to Org/")
    parser.add_argument("--ai-exposure-matches", help="Optional matches.json (already attached as _aei in skeleton)")
    args = parser.parse_args()

    map_data = json.loads(Path(args.map).read_text(encoding="utf-8"))
    org_dir = Path(args.org_dir)

    # Schema sanity
    required_top = ["end_user", "anchors", "components", "edges"]
    missing_top = [k for k in required_top if k not in map_data]
    if missing_top:
        print(f"=== AUDIT FAIL ===\n  missing top-level keys: {missing_top}")
        return 1

    end_users = map_data["end_user"]
    if isinstance(end_users, str):
        end_users = [end_users] if end_users else []
    if not end_users:
        print("=== AUDIT FAIL ===\n  end_user is empty (set anchor's user need)")
        return 1

    anchors = map_data["anchors"]
    components = map_data["components"]
    edges = map_data["edges"]

    if not anchors:
        print("=== AUDIT FAIL ===\n  anchors list is empty (every map needs at least one user need)")
        return 1
    if not components:
        print("=== AUDIT FAIL ===\n  components list is empty")
        return 1

    issues: list[str] = []
    issues.extend(audit_components(components))
    issues.extend(audit_anchors(anchors))
    issues.extend(audit_edges(edges, anchors, components, end_users))
    issues.extend(audit_structure_existence(components, org_dir))

    # Component count warning
    n_comp = len(components)
    if n_comp < 8 or n_comp > 16:
        print(f"Note: {n_comp} components on the map — convention is 12-16. Not a failure.")

    print("=== Wardley map audit ===\n")
    print(f"  end_user(s): {end_users}")
    print(f"  anchors: {len(anchors)}")
    print(f"  components: {len(components)} "
          f"(units={sum(1 for c in components if c.get('_kind')=='unit')}, "
          f"activities={sum(1 for c in components if c.get('_kind')=='activity')}, "
          f"new={sum(1 for c in components if c.get('is_new'))})")
    print(f"  edges: {len(edges)}")
    print(f"  components with ai_effect: {sum(1 for c in components if c.get('ai_effect'))}")
    print(f"  components with evolution_target: {sum(1 for c in components if c.get('evolution_target') is not None)}")
    print()

    if issues:
        print(f"=== AUDIT FAIL: {len(issues)} issue(s) ===")
        for i in issues:
            print(i)
        return 1

    print("=== AUDIT PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
