#!/usr/bin/env python3
"""
world-model / audit.py — Verify a world-model JSON.

Checks each capability against the five-property test (CAPABILITIES.md),
verifies substrate evidence exists, enforces the three-actors rule, and
checks failure signals are concrete and cited.

Usage:
    python3 audit.py --map <world-model.json> --org-dir <path>

Exit code:
    0 = audit passed
    1 = audit failed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_CONTRACT_FIELDS = ["input", "output", "slo_targets", "regulatory_constraints", "invocation_modality"]
ALLOWED_MOAT_GRADES = {"moat", "commodity"}
ALLOWED_MATURITY = {"high", "medium", "low"}


def audit_capabilities(caps: list[dict], org_dir: Path) -> list[str]:
    issues: list[str] = []
    seen_names: set[str] = set()
    for i, c in enumerate(caps):
        name = c.get("name", f"<unnamed {i}>")

        if name in seen_names:
            issues.append(f"  capability '{name}' duplicated")
        seen_names.add(name)

        # Required fields
        if not c.get("name"):
            issues.append(f"  capability[{i}] missing 'name' (verb-object form)")
        if not c.get("description"):
            issues.append(f"  capability[{i}] missing 'description'")

        # Contract: each field must be non-empty
        for field in REQUIRED_CONTRACT_FIELDS:
            v = c.get(field)
            if not v or (isinstance(v, list) and len(v) == 0):
                issues.append(f"  capability '{name}' missing or empty contract field '{field}'")

        # is_callable_by — three-actors rule
        callers = c.get("is_callable_by") or []
        if len(callers) < 3:
            issues.append(f"  capability '{name}' has only {len(callers)} stakeholder types in is_callable_by; rule requires at least 3")

        # composes_with — at least one composition (otherwise it's a standalone product, not a building block)
        composes = c.get("composes_with") or []
        if len(composes) == 0:
            issues.append(f"  capability '{name}' has empty composes_with; capabilities should compose with at least one other (otherwise it's a standalone product, not a building block)")

        # current_owners
        owners = c.get("current_owners") or []
        if len(owners) == 0:
            issues.append(f"  capability '{name}' has no current_owners; cite which substrate units host the activities composing it")

        # moat_grade
        mg = c.get("moat_grade")
        if mg not in ALLOWED_MOAT_GRADES:
            issues.append(f"  capability '{name}' moat_grade='{mg}' not in {sorted(ALLOWED_MOAT_GRADES)}")

        # _substrate_evidence — at least one path that exists
        ev = c.get("_substrate_evidence") or []
        if len(ev) == 0:
            issues.append(f"  capability '{name}' has no _substrate_evidence")
        else:
            for p in ev:
                # Tolerant path resolution: try as-is, then prefixed with org_dir parent
                candidates = [Path(p), org_dir.parent / p, org_dir / p]
                if not any(c.exists() for c in candidates):
                    issues.append(f"  capability '{name}' substrate evidence '{p}' not found")

    return issues


def audit_world_model(d: dict) -> list[str]:
    issues: list[str] = []

    company = d.get("world_model_company") or {}
    obs = company.get("observations") or []
    if not obs:
        issues.append("  world_model_company.observations is empty; cite at least one substrate observation feeding the company-side world model")
    for i, o in enumerate(obs):
        if not o.get("dimension"):
            issues.append(f"  world_model_company.observations[{i}] missing 'dimension'")
        if not o.get("lives_in"):
            issues.append(f"  world_model_company.observations[{i}] missing 'lives_in' (which substrate file or system)")
        if o.get("maturity") not in ALLOWED_MATURITY:
            issues.append(f"  world_model_company.observations[{i}] maturity='{o.get('maturity')}' not in {sorted(ALLOWED_MATURITY)}")

    customer = d.get("world_model_customer") or {}
    by_stake = customer.get("by_stakeholder") or []
    if not by_stake:
        issues.append("  world_model_customer.by_stakeholder is empty; map at least the main stakeholder types")
    for i, s in enumerate(by_stake):
        ref = f"world_model_customer.by_stakeholder[{i}]" + (f" ({s['type']})" if s.get("type") else "")
        if not s.get("type"):
            issues.append(f"  {ref} missing 'type'")
        if not s.get("description") or len(s.get("description", "")) < 20:
            issues.append(f"  {ref} missing or too-short 'description' (1-2 sentences explaining what kind of stakeholder this is)")
        if not s.get("what_they_get_from_org"):
            issues.append(f"  {ref} missing 'what_they_get_from_org' (the user side of the bidirectional relationship)")
        if not s.get("what_they_contribute_back"):
            issues.append(f"  {ref} missing 'what_they_contribute_back' (the contributor side, what signal or value they feed back)")
        if not s.get("honest_signal"):
            issues.append(f"  {ref} missing 'honest_signal'; what is the most observable, recorded signal for this stakeholder?")
        if s.get("current_maturity") not in ALLOWED_MATURITY:
            issues.append(f"  {ref} current_maturity='{s.get('current_maturity')}' not in {sorted(ALLOWED_MATURITY)}")
        if not s.get("fragmentation"):
            issues.append(f"  {ref} missing 'fragmentation'; explain which teams hold which slice (or say explicitly the representation is unified)")

    return issues


def audit_intelligence_layer(d: dict) -> list[str]:
    issues: list[str] = []
    il = d.get("intelligence_layer") or {}
    cur = il.get("current_human_compositions") or []
    pot = il.get("potential_compositions") or []
    if len(cur) == 0 and len(pot) == 0:
        issues.append("  intelligence_layer: both current_human_compositions and potential_compositions are empty; the analysis should surface at least 3 of either")

    for i, c in enumerate(cur):
        if not c.get("trigger"):
            issues.append(f"  intelligence_layer.current_human_compositions[{i}] missing 'trigger'")
        if not c.get("capabilities_composed"):
            issues.append(f"  intelligence_layer.current_human_compositions[{i}] missing 'capabilities_composed' (list of capability names)")

    for i, c in enumerate(pot):
        if not c.get("trigger"):
            issues.append(f"  intelligence_layer.potential_compositions[{i}] missing 'trigger'")
        if not c.get("capabilities"):
            issues.append(f"  intelligence_layer.potential_compositions[{i}] missing 'capabilities'")
        if not c.get("precondition"):
            issues.append(f"  intelligence_layer.potential_compositions[{i}] missing 'precondition' (which world-model maturity it requires)")

    return issues


def audit_failure_signals(d: dict, capability_names: set[str]) -> list[str]:
    issues: list[str] = []
    fs = d.get("failure_signals") or []
    if len(fs) < 3:
        issues.append(f"  failure_signals has only {len(fs)} entries; the section is the roadmap, surface at least 3")

    for i, f in enumerate(fs):
        if not f.get("trigger"):
            issues.append(f"  failure_signals[{i}] missing 'trigger'")
        if not f.get("composition_attempted"):
            issues.append(f"  failure_signals[{i}] missing 'composition_attempted'")
        if not f.get("missing_capability"):
            issues.append(f"  failure_signals[{i}] missing 'missing_capability' (verb-object name of the capability that doesn't exist)")
        if not f.get("substrate_evidence"):
            issues.append(f"  failure_signals[{i}] missing 'substrate_evidence' (citation that the request would actually arise)")
        # composition_attempted should reference existing capabilities
        comp = f.get("composition_attempted") or []
        if isinstance(comp, list):
            for cname in comp:
                if cname not in capability_names:
                    issues.append(f"  failure_signals[{i}] composition_attempted references '{cname}' which is not in capabilities")

    return issues


def audit_interfaces(d: dict, capability_names: set[str]) -> list[str]:
    issues: list[str] = []
    ifs = d.get("interfaces") or []
    for i, ifc in enumerate(ifs):
        if not ifc.get("name"):
            issues.append(f"  interfaces[{i}] missing 'name'")
        surfaces = ifc.get("surfaces_capabilities") or []
        for cname in surfaces:
            if cname not in capability_names:
                issues.append(f"  interfaces[{i}] surfaces_capabilities references '{cname}' which is not in capabilities")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a world-model JSON.")
    parser.add_argument("--map", required=True, help="World-model JSON path")
    parser.add_argument("--org-dir", required=True, help="Path to Org/")
    args = parser.parse_args()

    d = json.loads(Path(args.map).read_text(encoding="utf-8"))
    org_dir = Path(args.org_dir)

    caps = d.get("capabilities") or []
    if not caps:
        print("=== AUDIT FAIL ===\n  capabilities list is empty; identify at least the moat capabilities of the organization")
        return 1

    cap_names = {c.get("name") for c in caps if c.get("name")}

    issues: list[str] = []
    issues.extend(audit_capabilities(caps, org_dir))
    issues.extend(audit_world_model(d))
    issues.extend(audit_intelligence_layer(d))
    issues.extend(audit_failure_signals(d, cap_names))
    issues.extend(audit_interfaces(d, cap_names))

    # Distribution summary
    moat = sum(1 for c in caps if c.get("moat_grade") == "moat")
    commodity = sum(1 for c in caps if c.get("moat_grade") == "commodity")
    n_signals = len(d.get("failure_signals") or [])
    n_interfaces = len(d.get("interfaces") or [])

    print("=== World-model audit ===\n")
    print(f"  scope: {d.get('_scope', '?')}")
    print(f"  capabilities: {len(caps)} (moat={moat}, commodity={commodity})")
    print(f"  interfaces: {n_interfaces}")
    print(f"  failure signals: {n_signals}")
    print(f"  intelligence layer current human-mediated compositions: {len(d.get('intelligence_layer', {}).get('current_human_compositions', []))}")
    print(f"  intelligence layer potential automatable compositions: {len(d.get('intelligence_layer', {}).get('potential_compositions', []))}")
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
