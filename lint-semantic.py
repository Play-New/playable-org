#!/usr/bin/env python3
"""
Tier 2 semantic lint for playable-org.

4 metrics:
  M1: Commitment structural integrity
  M2: Unit↔activity referential closure
  M3: Language term usage (inbound links)
  M4: Body stub detection (<30 words)

Defaults to linting `<repo-root>/org/`. Pass `--org-dir <path>` to lint a
different directory. Output: `lint-semantic-report-<date>.md` at repo root
unless `--report` is passed.
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent

# Resolved from CLI args at the bottom of the file. Default lower-case
# (was `Org` — silently masked on case-insensitive filesystems).
ORG: Path = ROOT / "org"
REPORT: Path = ROOT / f"lint-semantic-report-{date.today().isoformat()}.md"

STUB_THRESHOLD_WORDS = 30


def parse_frontmatter(text):
    """Return (frontmatter_dict, body) or (None, text) if no frontmatter."""
    if not text.startswith("---\n"):
        return None, text
    try:
        end = text.index("\n---\n", 4)
    except ValueError:
        return None, text
    fm_text = text[4:end]
    body = text[end + 5:]
    fm = {}
    current_key = None
    for line in fm_text.split("\n"):
        if not line.strip():
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            value = m.group(2).strip()
            if value.startswith("["):
                # inline list
                items = re.findall(r"[\w\-]+", value)
                fm[current_key] = items
            elif value.startswith('"') and value.endswith('"'):
                fm[current_key] = value[1:-1]
            elif value:
                fm[current_key] = value
            else:
                fm[current_key] = []
        elif line.strip().startswith("-") and current_key and isinstance(fm.get(current_key), list):
            item = line.strip().lstrip("-").strip().strip('"')
            fm[current_key].append(item)
    return fm, body


def collect_nodes():
    """Return dict id → {path, type, fm, body, words}."""
    nodes = {}
    for md in ORG.rglob("*.md"):
        if md.name in ("README.md", "AGENTS.md", "log.md", "index.md"):
            continue
        text = md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        if fm is None or "id" not in fm:
            continue
        # Strip markdown headers, blockquotes, frontmatter from word count
        body_words = re.findall(r"\b\w+\b", body)
        nodes[fm["id"]] = {
            "path": md,
            "type": fm.get("type", "unknown"),
            "fm": fm,
            "body": body,
            "words": len(body_words),
            "rel": md.relative_to(ROOT),
        }
    return nodes


def collect_inbound_links(nodes):
    """For each node id, who links to it (markdown links)."""
    inbound = defaultdict(set)
    link_re = re.compile(r"\]\(([^)]+\.md)\)")
    fm_id_arrays = ("sources", "parties_committing", "parties_benefiting", "related",
                    "authority_basis", "performer", "unit", "parent", "head_role",
                    "reports_to")
    for node_id, n in nodes.items():
        # Body links
        for match in link_re.finditer(n["body"]):
            target_path = match.group(1)
            stem = Path(target_path).stem
            if stem in nodes and stem != node_id:
                inbound[stem].add(node_id)
        # Frontmatter id references
        for key in fm_id_arrays:
            value = n["fm"].get(key)
            if not value:
                continue
            if isinstance(value, list):
                for ref in value:
                    if ref in nodes and ref != node_id:
                        inbound[ref].add(node_id)
            elif isinstance(value, str) and value in nodes and value != node_id:
                inbound[value].add(node_id)
    return inbound


# ============================================================================
# M1: Commitment integrity
# ============================================================================

def check_m1(nodes, inbound):
    issues = []
    for node_id, n in nodes.items():
        if n["type"] != "commitment":
            continue
        fm = n["fm"]
        # Required: parties non-empty
        for k in ("parties_committing", "parties_benefiting"):
            if not fm.get(k):
                issues.append((node_id, f"missing or empty `{k}`"))
            else:
                bad = [p for p in fm[k] if p not in nodes]
                if bad:
                    issues.append((node_id, f"`{k}` references non-existent nodes: {bad}"))
        # If state ≠ active → failure_mode + state_evidence required
        state = fm.get("state", "active")
        if state in ("degraded", "broken"):
            if not fm.get("failure_mode"):
                issues.append((node_id, f"state={state} but `failure_mode` missing"))
            if not fm.get("state_evidence") or fm.get("state_evidence") in ("", '""'):
                issues.append((node_id, f"state={state} but `state_evidence` empty"))
        # Connectivity: body links ≥1 commitment OR is referenced by ≥1 unit/activity
        body_targets = set(re.findall(r"\]\(([^)]+\.md)\)", n["body"]))
        body_target_stems = {Path(t).stem for t in body_targets}
        body_target_types = {nodes[s]["type"] for s in body_target_stems if s in nodes}
        inbound_types = {nodes[i]["type"] for i in inbound.get(node_id, set()) if i in nodes}
        connected = (
            "commitment" in body_target_types
            or "unit" in inbound_types
            or "activity" in inbound_types
        )
        if not connected:
            issues.append((node_id, "orphan: body links no commitment AND not referenced by any unit/activity body"))
    return issues


# ============================================================================
# M2: Unit↔activity referential closure
# ============================================================================

def check_m2(nodes):
    issues = []
    # Build map: unit body links to which activities
    unit_links_to_activities = defaultdict(set)
    for node_id, n in nodes.items():
        if n["type"] != "unit":
            continue
        for m in re.finditer(r"\]\(\.\./activities/([\w-]+)\.md\)", n["body"]):
            target = m.group(1)
            if target in nodes:
                unit_links_to_activities[node_id].add(target)

    # Check 1: each activity with unit: X is linked from X body
    for node_id, n in nodes.items():
        if n["type"] != "activity":
            continue
        unit_id = n["fm"].get("unit")
        if not unit_id:
            issues.append((node_id, "activity missing `unit:` in frontmatter"))
            continue
        if unit_id not in nodes:
            issues.append((node_id, f"activity `unit: {unit_id}` not a valid node"))
            continue
        if node_id not in unit_links_to_activities.get(unit_id, set()):
            issues.append((node_id, f"activity not linked from unit `{unit_id}` body"))

    # Check 2: each link in unit body to activity → activity has unit: X
    for unit_id, activities in unit_links_to_activities.items():
        for act_id in activities:
            act = nodes[act_id]
            if act["type"] != "activity":
                continue
            act_unit = act["fm"].get("unit")
            if act_unit != unit_id:
                # Acceptable if linked unit is different and activity unit makes sense (cross-area mention)
                # But we flag if unit body links to activity NOT under it
                # Acceptable case: unit body links to cross-area activity for context
                # We flag only if it's clearly broken (act_unit doesn't exist)
                if act_unit and act_unit not in nodes:
                    issues.append((act_id, f"linked from unit `{unit_id}` but its declared `unit: {act_unit}` is invalid"))
    return issues


# ============================================================================
# M3: Language term usage
# ============================================================================

def check_m3(nodes, inbound):
    issues = []
    for node_id, n in nodes.items():
        if n["type"] != "language-term":
            continue
        in_count = len(inbound.get(node_id, set()))
        if in_count == 0:
            issues.append((node_id, "DEAD: 0 inbound links — never referenced"))
        elif in_count == 1:
            ref = list(inbound[node_id])[0]
            issues.append((node_id, f"BORDERLINE: only 1 inbound link (from `{ref}`)"))
    return issues


# ============================================================================
# M4: Stub detection
# ============================================================================

def check_m4(nodes):
    """Stub detection with per-type thresholds.

    Skipped (minimal body is by design / source-limited):
    - language-term: glossary entries, short by nature
    - person: the organization's role-description documents describe roles, not people; biographical detail not in sources
    - role: responsibility described in the unit body, role file is a pointer

    Per-type thresholds (words):
    - activity: 20 — minimum useful = quote + cross-ref/elaboration sentence
    - unit: 30 — should describe scope, sub-team, attività, cross-area
    - stakeholder: 30 — should describe interaction mode
    - commitment: 30 — covered by M1 too
    - identity: 30
    """
    thresholds = {
        "activity": 20,
        "unit": 30,
        "stakeholder": 30,
        "commitment": 30,
        "identity": 30,
    }
    issues = []
    for node_id, n in nodes.items():
        t = n["type"]
        if t not in thresholds:
            continue
        thr = thresholds[t]
        if n["words"] < thr:
            issues.append((node_id, f"stub: {n['words']} words in body (threshold {thr} for {t})"))
    return issues


# ============================================================================
# Main
# ============================================================================

def main():
    nodes = collect_nodes()
    inbound = collect_inbound_links(nodes)

    m1 = check_m1(nodes, inbound)
    m2 = check_m2(nodes)
    m3 = check_m3(nodes, inbound)
    m4 = check_m4(nodes)

    by_type = defaultdict(int)
    for n in nodes.values():
        by_type[n["type"]] += 1

    lines = [
        f"# Lint Semantic Report — {date.today().isoformat()}",
        "",
        f"Nodes scanned: **{len(nodes)}**",
        "",
        "## Coverage",
        "",
        "| Type | Count |",
        "|---|---|",
    ]
    for t in sorted(by_type):
        lines.append(f"| {t} | {by_type[t]} |")
    lines += [
        "",
        "## Summary",
        "",
        "| Check | Issues |",
        "|---|---|",
        f"| M1 — Commitment integrity | {len(m1)} |",
        f"| M2 — Unit↔activity closure | {len(m2)} |",
        f"| M3 — Language term usage | {len(m3)} |",
        f"| M4 — Body stubs (<{STUB_THRESHOLD_WORDS} words) | {len(m4)} |",
        "",
        "---",
        "",
        "## M1 — Commitment integrity",
        "",
    ]
    if m1:
        for nid, msg in m1:
            lines.append(f"- `{nid}`: {msg}")
    else:
        lines.append("(none)")
    lines += ["", "## M2 — Unit↔activity referential closure", ""]
    if m2:
        for nid, msg in m2[:50]:
            lines.append(f"- `{nid}`: {msg}")
        if len(m2) > 50:
            lines.append(f"… and {len(m2) - 50} more")
    else:
        lines.append("(none)")
    lines += ["", "## M3 — Language term usage", ""]
    if m3:
        for nid, msg in m3:
            lines.append(f"- `{nid}`: {msg}")
    else:
        lines.append("(none)")
    lines += ["", f"## M4 — Body stubs (<{STUB_THRESHOLD_WORDS} words)", ""]
    if m4:
        # Group by type
        by_t = defaultdict(list)
        for nid, msg in m4:
            by_t[nodes[nid]["type"]].append((nid, msg))
        for t in sorted(by_t):
            lines.append(f"### {t} ({len(by_t[t])})")
            for nid, msg in by_t[t][:30]:
                lines.append(f"- `{nid}`: {msg}")
            if len(by_t[t]) > 30:
                lines.append(f"… and {len(by_t[t]) - 30} more")
            lines.append("")
    else:
        lines.append("(none)")

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Report: {REPORT}")
    print(f"Nodes: {len(nodes)}")
    print(f"M1 commitment integrity: {len(m1)}")
    print(f"M2 unit↔activity closure: {len(m2)}")
    print(f"M3 language term usage: {len(m3)}")
    print(f"M4 stubs (<{STUB_THRESHOLD_WORDS} words): {len(m4)}")
    return 0


def _resolve_paths_from_argv() -> None:
    """Apply --org-dir / --report to the module-level ORG and REPORT
    before main() walks the filesystem."""
    global ORG, REPORT
    parser = argparse.ArgumentParser(
        description="Tier-2 semantic lint of an org/ directory.",
    )
    parser.add_argument(
        "--org-dir",
        type=Path,
        default=ROOT / "org",
        help="Directory to lint (default: <repo-root>/org).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Where to write the markdown report (default: <repo-root>/lint-semantic-report-<date>.md).",
    )
    args = parser.parse_args()
    ORG = args.org_dir.resolve()
    if not ORG.is_dir():
        sys.stderr.write(f"lint-semantic: org dir not found: {ORG}\n")
        sys.exit(2)
    REPORT = (
        args.report.resolve()
        if args.report
        else ROOT / f"lint-semantic-report-{date.today().isoformat()}.md"
    )


if __name__ == "__main__":
    _resolve_paths_from_argv()
    sys.exit(main())
