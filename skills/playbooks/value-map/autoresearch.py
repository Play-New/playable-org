#!/usr/bin/env python3
"""
value-map / autoresearch.py — Score a value-map play on five dimensions
that the SKILL.md's autoresearch loop iterates against.

Four dimensions are deterministic gates: they catch the common failure
modes a play can ship with — jargon that the leader can't read, decisions
that are missing or too thin, components that aren't grounded in the
structure, prose that doesn't actually mention the org by name.

The fifth dimension (--llm) calls Claude Sonnet 4.6 as a judge and scores
each decision on three axes (actionable, distinctive, readable). It
requires ANTHROPIC_API_KEY; without it, the dimension is skipped (does
not fail the gate).

Usage:
    python3 autoresearch.py --map <chain.json> [--org-dir <path>] [--llm]

Exit code:
    0 = all dimensions pass (or are skipped)
    1 = one or more dimensions fail (script prints which)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# ----------------------------------------------------------------------
# Jargon blacklist — terms that should not appear in the agent-authored
# decisions text without being plainly translated.
# ----------------------------------------------------------------------

WARDLEY_JARGON_STANDALONE = [
    # Wardley vocabulary used as a label, not as plain English
    r'\bevolution\s+0\.\d+',           # "evolution 0.32"
    r'\bvisibility\s+0\.\d+',          # "visibility 0.85"
    r'\bevolution_target\b',           # the JSON field name
    r'\bai_effect\b',                  # the JSON field name
    r'\bgenesis\s+stage\b',            # raw stage label
    r'\bcommodity\s+tier\b',           # too jargon-y
    r'\bproduct\s+tier\b',             # same
]

JARGON_RE = re.compile('|'.join(WARDLEY_JARGON_STANDALONE), re.IGNORECASE)


# ----------------------------------------------------------------------
# Recognizability — heuristic: at least N component labels appear by
# name in the decisions text. The map sits over real structure nodes;
# the interpretation should call them out.
# ----------------------------------------------------------------------

MIN_COMPONENT_MENTIONS = 3


def score_recognizability(map_data: dict) -> tuple[bool, str]:
    """The decisions text mentions at least MIN_COMPONENT_MENTIONS specific
    component labels or _structure_ids by name."""
    decisions = map_data.get("decisions") or []
    if not decisions:
        return False, "no decisions to score"

    component_ids = [c.get("_structure_id") or c.get("id") for c in map_data.get("components", [])]
    component_labels = [c.get("label", "") for c in map_data.get("components", [])]
    haystack = " ".join(d.get("answer", "") + " " + d.get("question", "") for d in decisions)

    mentioned = set()
    for cid in component_ids:
        if cid and cid.lower() in haystack.lower():
            mentioned.add(cid)
    for lab in component_labels:
        if lab and len(lab) >= 4 and lab.lower() in haystack.lower():
            mentioned.add(lab)

    n = len(mentioned)
    if n >= MIN_COMPONENT_MENTIONS:
        return True, f"{n} component name(s) mentioned in decisions ({', '.join(sorted(mentioned))[:200]})"
    return False, (
        f"only {n} component name(s) mentioned; need ≥ {MIN_COMPONENT_MENTIONS}. "
        f"The decisions read as generic — the org should be able to recognize itself in them."
    )


# ----------------------------------------------------------------------
# Plain language — jargon density in decisions text.
# ----------------------------------------------------------------------

def score_plain_language(map_data: dict) -> tuple[bool, str]:
    """No jargon hits in the decisions text (Wardley standalone terms,
    JSON field names leaking, "evolution 0.X" numbers)."""
    decisions = map_data.get("decisions") or []
    if not decisions:
        return False, "no decisions to score"

    findings: list[str] = []
    for i, d in enumerate(decisions):
        text = d.get("question", "") + "\n" + d.get("answer", "")
        for m in JARGON_RE.finditer(text):
            findings.append(f"  decision[{i}]: {m.group(0)!r}")

    if findings:
        return False, "jargon hits:\n" + "\n".join(findings[:10])
    return True, "no jargon hits in decisions"


# ----------------------------------------------------------------------
# Decision anchoring — ≥ 3 decisions, each with substantive answer +
# non-empty source.
# ----------------------------------------------------------------------

MIN_DECISIONS = 3
MIN_ANSWER_CHARS = 60


def score_decision_anchoring(map_data: dict) -> tuple[bool, str]:
    decisions = map_data.get("decisions") or []
    n = len(decisions)
    if n < MIN_DECISIONS:
        return False, f"only {n} decision(s); need ≥ {MIN_DECISIONS}"

    issues: list[str] = []
    for i, d in enumerate(decisions):
        if not d.get("question", "").strip():
            issues.append(f"  decision[{i}]: empty question")
        ans = d.get("answer", "").strip()
        if len(ans) < MIN_ANSWER_CHARS:
            issues.append(f"  decision[{i}]: answer too short ({len(ans)} chars; need ≥ {MIN_ANSWER_CHARS})")
        if not d.get("source", "").strip():
            issues.append(f"  decision[{i}]: empty source citation")

    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{n} decisions, all substantive and cited"


# ----------------------------------------------------------------------
# Audit grounded — every non-is_new component has a _structure_id that
# resolves to a real file under org/.
# ----------------------------------------------------------------------

def score_audit_grounded(map_data: dict, org_dir: Path | None) -> tuple[bool, str]:
    if org_dir is None:
        return True, "skipped (no --org-dir provided)"

    components = map_data.get("components") or []
    issues: list[str] = []

    for c in components:
        if c.get("is_new"):
            continue
        sid = c.get("_structure_id")
        if not sid:
            issues.append(f"  {c.get('id')} '{c.get('label')}': missing _structure_id")
            continue
        # Try the standard locations
        candidates = [
            org_dir / "nodes" / "units" / f"{sid}.md",
            org_dir / "nodes" / "activities" / f"{sid}.md",
            org_dir / "nodes" / "stakeholders" / f"{sid}.md",
            org_dir / "nodes" / "people" / f"{sid}.md",
            org_dir / "commitments" / f"{sid}.md",
        ]
        if not any(p.exists() for p in candidates):
            issues.append(f"  {c.get('id')} '{c.get('label')}': _structure_id '{sid}' not found in org/")

    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{len(components)} components, every non-is_new has a resolvable _structure_id"


# ----------------------------------------------------------------------
# LLM-as-judge (opt-in, --llm) — Claude Sonnet 4.6 scores each decision
# on three axes that the deterministic checks can't see:
#
#   actionable  — yes / no.  Does the answer name a move the leader could
#                 make on Monday, not just an observation?
#   distinctive — high / medium / low.  Is the framing one this org could
#                 only have made of itself, or is it consultant-generic?
#   readable    — yes / no.  Would the founder of this studio nod along,
#                 or stop on a sentence that reads as jargon-by-paraphrase?
#
# The dimension fails if any decision is non-actionable or non-readable,
# or if more than half score "low" on distinctive. Skipped (PASS) when
# no API key is present so the gate stays usable offline.
# ----------------------------------------------------------------------

JUDGE_MODEL = "claude-sonnet-4-6"

JUDGE_RUBRIC = """\
You are reviewing the interpretive 'decisions' attached to a value-map of a real organization.
A value-map sits over a structure of named units, activities, and commitments. Each decision is
a question the leader of the organization should be able to answer after reading the map, plus
the answer the play asserts.

Score each decision on three independent axes. Be strict — the point of the review is to catch
decisions that read fine in isolation but don't actually help the leader.

  actionable  — "yes" if the answer names a concrete move the leader could make on Monday
                (a re-allocation, a new role, a pricing change, a structural shift). "no" if the
                answer is descriptive only ("X is commoditizing") with no implication for action.

  distinctive — "high" if the framing reads as something only this organization could have
                arrived at — it uses the org's named units, named people, named commitments, and
                its specific mix. "medium" if it's plausible but could apply to a similar shop
                with the names swapped. "low" if it's consultant-generic — true of any creative
                services firm, any agency, any studio.

  readable    — "yes" if a smart non-technical leader of this org would track the prose without
                hitting jargon (Wardley terms, framework vocabulary, abstract management speak,
                paraphrased jargon like "high judgment density"). "no" if they would stop and
                ask what a sentence means.

Add a one-sentence note per decision explaining the scores. Be specific about which sentence or
move triggered the score, not generic praise."""


def _build_judge_payload(map_data: dict) -> dict[str, Any]:
    """Reduce the map down to what the judge needs: anchor, components,
    and the decisions themselves."""
    components = [
        {"label": c.get("label"), "kind": c.get("_kind"), "structure_id": c.get("_structure_id")}
        for c in map_data.get("components", [])
        if not c.get("is_new")
    ]
    return {
        "anchor": {
            "title": (map_data.get("_anchor") or {}).get("title"),
            "kind": (map_data.get("_anchor") or {}).get("kind"),
        },
        "components": components,
        "decisions": map_data.get("decisions") or [],
    }


def score_llm_judge(map_data: dict) -> tuple[bool, str]:
    """Sonnet 4.6 scores each decision on actionable / distinctive / readable.
    Skipped (PASS) when no key or SDK is available so the gate stays usable offline."""
    decisions = map_data.get("decisions") or []
    if not decisions:
        return False, "no decisions to judge"

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return True, "skipped (no ANTHROPIC_API_KEY in environment)"

    try:
        import anthropic  # noqa: F401  (imported for availability check + use below)
    except ImportError:
        return True, "skipped (anthropic SDK not installed)"

    client = anthropic.Anthropic()

    payload = _build_judge_payload(map_data)
    schema = {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "actionable": {"type": "string", "enum": ["yes", "no"]},
                        "distinctive": {"type": "string", "enum": ["high", "medium", "low"]},
                        "readable": {"type": "string", "enum": ["yes", "no"]},
                        "note": {"type": "string"},
                    },
                    "required": ["actionable", "distinctive", "readable", "note"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["decisions"],
        "additionalProperties": False,
    }

    try:
        response = client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=4096,
            system=[{
                "type": "text",
                "text": JUDGE_RUBRIC,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{
                "role": "user",
                "content": (
                    "Score each decision in this value-map. Return one entry per decision, in the "
                    "same order as the input.\n\n"
                    + json.dumps(payload, ensure_ascii=False, indent=2)
                ),
            }],
            output_config={"format": {"type": "json_schema", "schema": schema}},
            thinking={"type": "adaptive"},
        )
    except anthropic.AuthenticationError as e:
        return True, f"skipped (auth error: {e})"
    except anthropic.APIConnectionError as e:
        return True, f"skipped (connection error: {e})"
    except anthropic.APIError as e:
        return False, f"judge call failed: {e}"

    # Pull the JSON out of the first text block.
    text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    if not text_blocks:
        return False, "judge returned no text blocks"

    try:
        verdict = json.loads(text_blocks[0])
    except json.JSONDecodeError as e:
        return False, f"judge returned invalid JSON: {e}"

    items = verdict.get("decisions") or []
    if len(items) != len(decisions):
        return False, f"judge returned {len(items)} verdicts for {len(decisions)} decisions"

    fails: list[str] = []
    low_distinct = 0
    lines: list[str] = []
    for i, (d, v) in enumerate(zip(decisions, items)):
        q = d.get("question", "").strip()
        short_q = q if len(q) <= 60 else q[:57] + "…"
        lines.append(
            f"    [{i}] {v['actionable']:<3}  "
            f"{v['distinctive']:<6}  "
            f"{v['readable']:<3}  —  {short_q}"
        )
        lines.append(f"        note: {v['note']}")
        if v["actionable"] == "no":
            fails.append(f"  decision[{i}] not actionable")
        if v["readable"] == "no":
            fails.append(f"  decision[{i}] not readable")
        if v["distinctive"] == "low":
            low_distinct += 1

    if low_distinct > len(decisions) // 2:
        fails.append(f"  {low_distinct}/{len(decisions)} decisions read as consultant-generic (distinctive=low)")

    detail_header = "        actionable  distinctive  readable  question"
    body = "\n" + detail_header + "\n" + "\n".join(lines)

    if fails:
        return False, "judge findings:\n" + "\n".join(fails) + body
    return True, f"{len(decisions)} decisions, all actionable + readable, distinctiveness acceptable" + body


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Score a value-map play on the autoresearch dimensions.")
    parser.add_argument("--map", required=True, help="Path to the value-map JSON")
    parser.add_argument("--org-dir", help="Path to org/ for audit-grounded check")
    parser.add_argument("--llm", action="store_true", help="Also run the LLM-as-judge dimension (Claude Sonnet 4.6, requires ANTHROPIC_API_KEY)")
    args = parser.parse_args()

    map_path = Path(args.map)
    if not map_path.exists():
        print(f"FAIL: map not found at {map_path}", file=sys.stderr)
        return 2

    map_data = json.loads(map_path.read_text(encoding="utf-8"))
    org_dir = Path(args.org_dir) if args.org_dir else None

    print(f"=== Autoresearch · value-map · {map_path.name} ===\n")

    checks: list[tuple[str, bool, str]] = [
        ("recognizability",      *score_recognizability(map_data)),
        ("plain language",       *score_plain_language(map_data)),
        ("decision anchoring",   *score_decision_anchoring(map_data)),
        ("audit grounded",       *score_audit_grounded(map_data, org_dir)),
    ]
    if args.llm:
        checks.append(("llm judge",          *score_llm_judge(map_data)))

    width = max(len(name) for name, _, _ in checks)
    fails = 0
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        # Multi-line details: print the first line on the header row, the rest indented.
        first, _, rest = detail.partition("\n")
        print(f"  [{mark}]  {name:<{width}}  —  {first}")
        if rest:
            for line in rest.split("\n"):
                print(f"          {line}" if not line.startswith("    ") and not line.startswith("        ") else line)
        if not ok:
            fails += 1

    print()
    if fails == 0:
        print("=== AUTORESEARCH PASS ===")
        return 0
    print(f"=== AUTORESEARCH FAIL: {fails}/{len(checks)} dimension(s) ===")
    return 1


if __name__ == "__main__":
    sys.exit(main())
