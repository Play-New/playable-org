#!/usr/bin/env python3
"""
autoresearch_lib.py — Shared scoring infrastructure for playbook
autoresearch loops.

Each playbook (value-map, world-model, reshuffle, ai-exposure) ships its
own `autoresearch.py` that composes:

  * playbook-specific deterministic checks (jargon blacklist, schema
    grounding, etc.)  These stay local to the playbook because they
    inspect the playbook's own JSON shape.

  * the shared `llm_judge` dimension defined here, which scores any
    `decisions[]` array (question / answer / source) on three axes the
    deterministic checks can't see — actionable, distinctive, readable.

  * the shared `run_checks` driver, which prints results in the same
    layout across every playbook so a fork can read any of them at a
    glance.

The LLM-as-judge dimension is opt-in (--llm flag) and skipped (PASS)
when no ANTHROPIC_API_KEY is set, so the gate stays usable offline.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable

# Re-export for callers
JUDGE_MODEL = "claude-sonnet-4-6"

# The three-axis judge prompt is generic across playbooks. Each playbook
# passes its own `playbook_context` string that explains what the artefact
# is, so the model knows what to score against.
_JUDGE_RUBRIC_TEMPLATE = """\
You are reviewing the interpretive 'decisions' attached to a {artefact_kind} of a real
organization.

{playbook_context}

Each decision is a question the leader of the organization should be able to answer after
reading the artefact, plus the answer the play asserts.

Score each decision on three independent axes. Be strict — the point of the review is to
catch decisions that read fine in isolation but don't actually help the leader.

  actionable  — "yes" if the answer names a concrete move the leader could make on Monday
                (a re-allocation, a new role, a pricing change, a structural shift,
                a hire, a divestiture, a product call). "no" if the answer is descriptive
                only ("X is commoditizing", "Y is fragile") with no implication for action.

  distinctive — "high" if the framing reads as something only this organization could have
                arrived at — it uses the org's named units, named people, named commitments,
                and its specific mix. "medium" if it's plausible but could apply to a similar
                shop with the names swapped. "low" if it's consultant-generic — true of any
                comparable firm in the category.

  readable    — "yes" if a smart non-technical leader of this org would track the prose
                without hitting jargon (framework vocabulary, abstract management speak,
                paraphrased jargon like "high judgment density"). "no" if they would stop
                and ask what a sentence means.

Add a one-sentence note per decision explaining the scores. Be specific about which
sentence or move triggered the score, not generic praise."""


def llm_judge(
    decisions: list[dict],
    payload: dict,
    *,
    artefact_kind: str,
    playbook_context: str,
    user_message_intro: str,
) -> tuple[bool, str]:
    """Sonnet 4.6 scores each decision on actionable / distinctive / readable.

    Returns (ok, detail). Skipped (ok=True) when no key/SDK so callers can
    keep the gate green offline. `payload` is whatever JSON context the
    judge needs to see beyond the decisions themselves — e.g. the anchor
    + components for a value-map, the stack + capabilities for a
    world-model.
    """
    if not decisions:
        return False, "no decisions to judge"

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return True, "skipped (no ANTHROPIC_API_KEY in environment)"

    try:
        import anthropic
    except ImportError:
        return True, "skipped (anthropic SDK not installed)"

    client = anthropic.Anthropic()

    rubric = _JUDGE_RUBRIC_TEMPLATE.format(
        artefact_kind=artefact_kind,
        playbook_context=playbook_context.strip(),
    )

    schema = {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "actionable":  {"type": "string", "enum": ["yes", "no"]},
                        "distinctive": {"type": "string", "enum": ["high", "medium", "low"]},
                        "readable":    {"type": "string", "enum": ["yes", "no"]},
                        "note":        {"type": "string"},
                    },
                    "required": ["actionable", "distinctive", "readable", "note"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["decisions"],
        "additionalProperties": False,
    }

    full_payload = {**payload, "decisions": decisions}

    try:
        response = client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=4096,
            system=[{
                "type": "text",
                "text": rubric,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{
                "role": "user",
                "content": (
                    user_message_intro.strip() + "\n\n"
                    + json.dumps(full_payload, ensure_ascii=False, indent=2)
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
# Generic deterministic checks reusable across playbooks
# ----------------------------------------------------------------------

def score_decision_anchoring(
    map_data: dict,
    *,
    min_decisions: int = 3,
    min_answer_chars: int = 60,
) -> tuple[bool, str]:
    """≥ N decisions, each with substantive answer + non-empty source."""
    decisions = map_data.get("decisions") or []
    n = len(decisions)
    if n < min_decisions:
        return False, f"only {n} decision(s); need ≥ {min_decisions}"

    issues: list[str] = []
    for i, d in enumerate(decisions):
        if not d.get("question", "").strip():
            issues.append(f"  decision[{i}]: empty question")
        ans = d.get("answer", "").strip()
        if len(ans) < min_answer_chars:
            issues.append(f"  decision[{i}]: answer too short ({len(ans)} chars; need ≥ {min_answer_chars})")
        if not d.get("source", "").strip():
            issues.append(f"  decision[{i}]: empty source citation")

    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{n} decisions, all substantive and cited"


def score_plain_language(
    map_data: dict,
    jargon_re: re.Pattern,
) -> tuple[bool, str]:
    """No jargon hits in any of the decisions text."""
    decisions = map_data.get("decisions") or []
    if not decisions:
        return False, "no decisions to score"

    findings: list[str] = []
    for i, d in enumerate(decisions):
        text = d.get("question", "") + "\n" + d.get("answer", "")
        for m in jargon_re.finditer(text):
            findings.append(f"  decision[{i}]: {m.group(0)!r}")

    if findings:
        return False, "jargon hits:\n" + "\n".join(findings[:10])
    return True, "no jargon hits in decisions"


def score_recognizability(
    map_data: dict,
    *,
    names: list[str],
    min_mentions: int = 3,
) -> tuple[bool, str]:
    """At least N of the supplied names appear in the decisions text."""
    decisions = map_data.get("decisions") or []
    if not decisions:
        return False, "no decisions to score"

    haystack = " ".join(d.get("answer", "") + " " + d.get("question", "") for d in decisions)
    haystack_lower = haystack.lower()
    mentioned = {n for n in names if n and len(n) >= 4 and n.lower() in haystack_lower}

    n = len(mentioned)
    if n >= min_mentions:
        return True, f"{n} name(s) mentioned in decisions ({', '.join(sorted(mentioned))[:200]})"
    return False, (
        f"only {n} name(s) mentioned; need ≥ {min_mentions}. "
        f"The decisions read as generic — the org should be able to recognize itself in them."
    )


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------

def run_checks(
    *,
    playbook: str,
    map_path: Any,
    checks: list[tuple[str, bool, str]],
) -> int:
    """Print a uniform results block and return an exit code.

    Each tuple is (dimension name, ok, detail). `detail` may contain
    embedded newlines for multi-line judge output; we indent the
    continuation lines so the output stays readable.
    """
    print(f"=== Autoresearch · {playbook} · {map_path.name if hasattr(map_path, 'name') else map_path} ===\n")

    width = max(len(name) for name, _, _ in checks)
    fails = 0
    for name, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        first, _, rest = detail.partition("\n")
        print(f"  [{mark}]  {name:<{width}}  —  {first}")
        if rest:
            for line in rest.split("\n"):
                if line.startswith("    ") or line.startswith("        "):
                    print(line)
                else:
                    print(f"          {line}")
        if not ok:
            fails += 1

    print()
    if fails == 0:
        print("=== AUTORESEARCH PASS ===")
        return 0
    print(f"=== AUTORESEARCH FAIL: {fails}/{len(checks)} dimension(s) ===")
    return 1
