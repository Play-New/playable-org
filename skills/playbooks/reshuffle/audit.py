#!/usr/bin/env python3
"""
reshuffle / audit.py — Verify a reshuffle slice JSON before commit.

Deterministic gate. Catches missing classifications, evidence-less constraint
or engine claims, malformed rebundle proposals, schema-rule violations.

Usage:
    python3 audit.py --map <slice.json> --org-dir <path>

Exit code:
    0 = audit passed
    1 = audit failed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ALLOWED_CONSTRAINTS = {"scarcity", "risk", "coordination"}
ALLOWED_KM_COSTS = {"encoding", "organizing", "deploying", "none"}
ALLOWED_AI_CLASS = {"tool", "engine", "not-applicable"}
ALLOWED_MODES = {"see-saw", "flywheel"}


def has_rich_aei(c: dict) -> bool:
    aei = c.get("_aei") or {}
    top = aei.get("top_matches") or []
    return any(t.get("ai_autonomy_mean") is not None for t in top)


def audit_components(comps: list[dict]) -> list[str]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    for c in comps:
        cid = c.get("id", "?")
        label = c.get("label", "?")
        kind = c.get("_kind") or "activity"

        if cid in seen_ids:
            issues.append(f"  duplicate component id '{cid}'")
        seen_ids.add(cid)

        # Stakeholder components are descriptive only — no constraint required.
        if kind == "stakeholder":
            continue

        # 1. primary_constraint required and from closed set
        pc = c.get("primary_constraint")
        if not pc:
            issues.append(f"  [{cid} {label}] missing primary_constraint (must be one of {sorted(ALLOWED_CONSTRAINTS)})")
        elif pc not in ALLOWED_CONSTRAINTS:
            issues.append(f"  [{cid} {label}] primary_constraint='{pc}' not in allowed set {sorted(ALLOWED_CONSTRAINTS)}")
        else:
            # Evidence required for the chosen constraint
            ev = c.get("constraint_evidence") or []
            if not ev:
                issues.append(f"  [{cid} {label}] primary_constraint='{pc}' but no constraint_evidence cited")
            else:
                for e in ev:
                    if not isinstance(e, dict) or not e.get("source"):
                        issues.append(f"  [{cid} {label}] constraint_evidence entry malformed (must have 'source')")
                        break

        # 2. km_cost_dominant required and from closed set
        km = c.get("km_cost_dominant")
        if km is None:
            issues.append(f"  [{cid} {label}] missing km_cost_dominant (must be one of {sorted(ALLOWED_KM_COSTS)})")
        elif km not in ALLOWED_KM_COSTS:
            issues.append(f"  [{cid} {label}] km_cost_dominant='{km}' not in allowed set {sorted(ALLOWED_KM_COSTS)}")

        # 3. ai_classification required
        ac = c.get("ai_classification")
        if ac is None:
            issues.append(f"  [{cid} {label}] missing ai_classification (must be one of {sorted(ALLOWED_AI_CLASS)})")
        elif ac not in ALLOWED_AI_CLASS:
            issues.append(f"  [{cid} {label}] ai_classification='{ac}' not in allowed set {sorted(ALLOWED_AI_CLASS)}")
        elif ac == "engine":
            # engine requires either rich AEI match data embedded OR a
            # citation chain in ai_evidence pointing at the AEI source. The
            # citation itself is the evidence; the embedded match data is a
            # nice-to-have when running the play in the same context as
            # ai-exposure. Plus knowledge-management cost must be named.
            ev = c.get("ai_evidence") or []
            if not (has_rich_aei(c) or ev):
                issues.append(f"  [{cid} {label}] ai_classification='engine' must include either rich AEI match data in _aei or at least one citation in ai_evidence")
            if km == "none":
                issues.append(f"  [{cid} {label}] ai_classification='engine' requires km_cost_dominant != 'none' (must specify which knowledge-management cost it changes)")
        elif ac == "tool":
            # tool can be set without rich AEI (defaults are allowed) but the audit doesn't require evidence
            pass

    return issues


def audit_bundle_state(d: dict) -> list[str]:
    issues: list[str] = []
    bd = d.get("bundle_state") or {}
    mode = bd.get("current_mode")
    if not mode:
        issues.append("  bundle_state.current_mode missing (must be 'see-saw' or 'flywheel')")
    elif mode not in ALLOWED_MODES:
        issues.append(f"  bundle_state.current_mode='{mode}' not in {sorted(ALLOWED_MODES)}")
    me = bd.get("mode_evidence") or []
    if not me:
        issues.append("  bundle_state.mode_evidence missing (cite a structure document or commitment terms)")

    # If any component has tool but no engine, the play must acknowledge the coordination paradox
    comps = d.get("components") or []
    has_tool = any(c.get("ai_classification") == "tool" for c in comps)
    has_engine = any(c.get("ai_classification") == "engine" for c in comps)
    if has_tool and not has_engine:
        cpr = bd.get("coordination_paradox_risk")
        if not cpr or len(cpr.strip()) < 30:
            issues.append("  bundle has tool classifications but no engine — bundle_state.coordination_paradox_risk must be authored (string ≥ 30 chars) acknowledging the asymmetric-capabilities risk")
    return issues


def audit_engine_candidates(d: dict) -> list[str]:
    issues: list[str] = []
    comps_by_id = {c["id"]: c for c in (d.get("components") or [])}
    for i, eng in enumerate(d.get("engine_candidates") or []):
        cid = eng.get("component_id")
        if not cid or cid not in comps_by_id:
            issues.append(f"  engine_candidates[{i}] component_id='{cid}' not in components")
            continue
        c = comps_by_id[cid]
        if c.get("ai_classification") != "engine":
            issues.append(f"  engine_candidates[{i}] points to component {cid} which is not classified as 'engine'")
        if not eng.get("dissolves_constraint"):
            issues.append(f"  engine_candidates[{i}] missing dissolves_constraint (which constraint type AI dissolves)")
        elif eng["dissolves_constraint"] not in ALLOWED_CONSTRAINTS:
            issues.append(f"  engine_candidates[{i}] dissolves_constraint='{eng['dissolves_constraint']}' not in allowed set")
    return issues


def audit_rebundle_candidates(d: dict) -> list[str]:
    issues: list[str] = []
    comps_by_id = {c["id"]: c for c in (d.get("components") or [])}
    engine_ids = {e.get("component_id") for e in (d.get("engine_candidates") or [])}
    for i, rb in enumerate(d.get("rebundle_candidates") or []):
        if not rb.get("name"):
            issues.append(f"  rebundle_candidates[{i}] missing name")
        comp_ids = rb.get("activities") or []
        if not comp_ids:
            issues.append(f"  rebundle_candidates[{i}] has no activities")
        for ac in comp_ids:
            if ac not in comps_by_id:
                issues.append(f"  rebundle_candidates[{i}] activity '{ac}' not in components")
        # Must cite the engine that enables it
        ee = rb.get("enabled_by_engine")
        if not ee:
            issues.append(f"  rebundle_candidates[{i}] missing enabled_by_engine (cite which engine candidate enables this rebundle)")
        elif ee not in engine_ids:
            issues.append(f"  rebundle_candidates[{i}] enabled_by_engine='{ee}' not in engine_candidates")
        # Must name remaining binding constraint
        rc = rb.get("remaining_binding_constraint")
        if not rc:
            issues.append(f"  rebundle_candidates[{i}] missing remaining_binding_constraint (name which constraint still holds the new bundle)")
        elif rc not in ALLOWED_CONSTRAINTS:
            issues.append(f"  rebundle_candidates[{i}] remaining_binding_constraint='{rc}' not in allowed set")
        # Autonomy-coordination position
        acp = rb.get("autonomy_coordination_mode")
        if not acp:
            issues.append(f"  rebundle_candidates[{i}] missing autonomy_coordination_mode")
        elif acp not in ALLOWED_MODES:
            issues.append(f"  rebundle_candidates[{i}] autonomy_coordination_mode='{acp}' not in {sorted(ALLOWED_MODES)}")
    return issues


def audit_structure_existence(comps: list[dict], org_dir: Path) -> list[str]:
    issues: list[str] = []
    for c in comps:
        sid = c.get("_structure_id")
        if not sid:
            continue
        candidates = [
            org_dir / "nodes" / "units" / f"{sid}.md",
            org_dir / "nodes" / "activities" / f"{sid}.md",
            org_dir / "commitments" / f"{sid}.md",
            org_dir / "nodes" / "stakeholders" / f"{sid}.md",
        ]
        if not any(p.exists() for p in candidates):
            issues.append(f"  [{c.get('id')} {c.get('label')}] _structure_id '{sid}' not found")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a reshuffle slice JSON.")
    parser.add_argument("--map", required=True, help="Slice JSON path")
    parser.add_argument("--org-dir", required=True, help="Path to org/")
    args = parser.parse_args()

    d = json.loads(Path(args.map).read_text(encoding="utf-8"))
    org_dir = Path(args.org_dir)

    comps = d.get("components") or []
    if not comps:
        print("=== AUDIT FAIL ===\n  no components")
        return 1

    issues: list[str] = []
    issues.extend(audit_components(comps))
    issues.extend(audit_bundle_state(d))
    issues.extend(audit_engine_candidates(d))
    issues.extend(audit_rebundle_candidates(d))
    issues.extend(audit_structure_existence(comps, org_dir))

    # Constraint distribution summary
    dist = {"scarcity": 0, "risk": 0, "coordination": 0, "(unset)": 0}
    for c in comps:
        if c.get("_kind") == "stakeholder":
            continue
        pc = c.get("primary_constraint")
        if pc in dist:
            dist[pc] += 1
        else:
            dist["(unset)"] += 1

    print("=== Reshuffle slice audit ===\n")
    print(f"  anchor: {d.get('_anchor', {}).get('id', '?')}")
    print(f"  components: {len(comps)} (stakeholders={sum(1 for c in comps if c.get('_kind')=='stakeholder')})")
    print(f"  primary-constraint distribution: scarcity={dist['scarcity']} · risk={dist['risk']} · coordination={dist['coordination']} · unset={dist['(unset)']}")
    bd = d.get("bundle_state") or {}
    print(f"  bundle mode: {bd.get('current_mode', '(unset)')}")
    print(f"  engine candidates: {len(d.get('engine_candidates') or [])}")
    print(f"  rebundle candidates: {len(d.get('rebundle_candidates') or [])}")
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
