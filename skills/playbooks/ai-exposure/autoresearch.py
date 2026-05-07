#!/usr/bin/env python3
"""
ai-exposure / autoresearch.py — Score an ai-exposure play on five
dimensions.

Four are deterministic: jargon density (Anthropic-Economic-Index
vocabulary should not leak), decisions present and substantive, every
referenced activity grounded in the structure, and the play's
interpretation actually mentions named units / activities of the org.

The fifth (--llm) calls Claude Sonnet 4.6 to score each decision on
actionable / distinctive / readable. Skipped (PASS) without
ANTHROPIC_API_KEY so the gate stays usable offline.

Unlike the other playbooks, ai-exposure's primary build output is a
*list* of activity matches with no top-level wrapper. The
autoresearch script therefore consumes a separate **play file** that
wraps the matches with the agent's interpretation:

    {
      "_scope": { ... },
      "matches": [ ... raw activity → O*NET task matches ... ],
      "decisions": [ {question, answer, source}, ... ]
    }

Usage:
    python3 autoresearch.py --play <ai-exposure-play.json> [--org-dir <path>] [--llm]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from autoresearch_lib import (  # noqa: E402
    llm_judge,
    run_checks,
    score_decision_anchoring,
    score_plain_language,
    score_recognizability,
)


# Vocabulary that should not appear in the decisions text. AEI numbers
# are useful internally but shouldn't be quoted in leader-facing prose
# without translation.
AEI_JARGON = re.compile(
    "|".join([
        r"\bO\*NET\b",
        r"\bai_autonomy_mean\b",
        r"\bai_education_years_mean\b",
        r"\bhuman_education_years_mean\b",
        r"\bpenetration\b",            # AEI-specific use of the term
        r"\btop1?_similarity\b",
        r"\bcosine\s+similarity\b",
        r"\bembedding\b",
    ]),
    re.IGNORECASE,
)


def score_audit_grounded(play_data: dict, org_dir: Path | None) -> tuple[bool, str]:
    """Every activity in matches[] resolves to a real file under
    org/nodes/activities/. The matches are the cited evidence base; the
    decisions can only stand if their underlying activities exist."""
    if org_dir is None:
        return True, "skipped (no --org-dir provided)"

    matches = play_data.get("matches") or []
    if not matches:
        return False, "matches[] is empty — no evidence to ground decisions in"

    activities_dir = org_dir / "nodes" / "activities"
    issues: list[str] = []
    for m in matches:
        aid = m.get("id")
        if not aid:
            issues.append("  match without id")
            continue
        # An id like 'unit-id/activity-id' or just 'activity-id'
        candidate = activities_dir / f"{aid.split('/')[-1]}.md"
        if not candidate.exists():
            issues.append(f"  activity '{aid}' not found under nodes/activities/")

    if issues:
        return False, "issues:\n" + "\n".join(issues[:10])
    return True, f"{len(matches)} activity match(es), every id resolves"


JUDGE_CONTEXT = """\
An ai-exposure play maps each activity in the org against the Anthropic Economic Index — a
public dataset of how AI is being used across O*NET tasks today, with autonomy and
education-equivalent signals. The decisions are the leader-facing reading: which activities
are most exposed (and how), where the displacement vs. augmentation pattern lands, which
roles or units should reallocate hours, and which capabilities the org should build to stay
ahead of the curve."""


def score_llm_judge(play_data: dict) -> tuple[bool, str]:
    decisions = play_data.get("decisions") or []
    matches_summary = []
    for m in play_data.get("matches") or []:
        top = (m.get("matches") or [])[:1]
        matches_summary.append({
            "id": m.get("id"),
            "top_task": top[0]["task"] if top else None,
            "top_similarity": top[0]["similarity"] if top else None,
            "top_autonomy": top[0].get("ai_autonomy_mean") if top else None,
        })
    payload = {
        "scope": play_data.get("_scope"),
        "matches_summary": matches_summary[:80],  # keep the prompt bounded
        "match_count": len(play_data.get("matches") or []),
    }
    return llm_judge(
        decisions,
        payload,
        artefact_kind="ai-exposure",
        playbook_context=JUDGE_CONTEXT,
        user_message_intro="Score each decision in this ai-exposure play. Return one entry per decision, in the same order as the input.",
    )


def _gather_names(play_data: dict) -> list[str]:
    names: list[str] = []
    for m in play_data.get("matches") or []:
        if m.get("id"):
            names.append(m["id"])
        # the readable text of the activity
        if m.get("text"):
            # only keep short labels — the full text is too long to be a "name"
            t = m["text"]
            if len(t) <= 60:
                names.append(t)
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description="Score an ai-exposure play on the autoresearch dimensions.")
    parser.add_argument("--play", required=True, help="Path to the ai-exposure play JSON (matches[] + decisions[])")
    parser.add_argument("--org-dir", help="Path to org/ for audit-grounded check")
    parser.add_argument("--llm", action="store_true", help="Also run the LLM-as-judge dimension (Claude Sonnet 4.6, requires ANTHROPIC_API_KEY)")
    args = parser.parse_args()

    play_path = Path(args.play)
    if not play_path.exists():
        print(f"FAIL: play not found at {play_path}", file=sys.stderr)
        return 2

    raw = json.loads(play_path.read_text(encoding="utf-8"))

    # Tolerate the bare-list shape (just matches, no decisions yet) by
    # wrapping it. The decision-anchoring check will then fail with a
    # clear message: "0 decisions, need ≥ 3".
    if isinstance(raw, list):
        play_data = {"matches": raw, "decisions": []}
    else:
        play_data = raw

    org_dir = Path(args.org_dir) if args.org_dir else None

    checks: list[tuple[str, bool, str]] = [
        ("recognizability",      *score_recognizability(play_data, names=_gather_names(play_data), min_mentions=3)),
        ("plain language",       *score_plain_language(play_data, AEI_JARGON)),
        ("decision anchoring",   *score_decision_anchoring(play_data)),
        ("audit grounded",       *score_audit_grounded(play_data, org_dir)),
    ]
    if args.llm:
        checks.append(("llm judge",      *score_llm_judge(play_data)))

    return run_checks(playbook="ai-exposure", map_path=play_path, checks=checks)


if __name__ == "__main__":
    sys.exit(main())
