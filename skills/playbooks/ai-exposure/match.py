#!/usr/bin/env python3
"""
ai-exposure / match.py — Match organizational activities to O*NET tasks via embeddings.

Reproducible, auditable, cross-language (multilingual sentence-transformer).
No manual judgment in the matching step.

Usage:
    python3 match.py --activities <activities.json> --top-k 5 [--threshold 0.3] [--out matches.json]

Input: a JSON file with a list of {id, text} where text is the activity description
(any language; Italian, English, French, etc. — multilingual model handles them).

Output: JSON with per-activity ranked matches, each including similarity score and
the Anthropic Economic Index metrics (ai_autonomy_mean, count, edu_gap, ...).

Requirements: sentence-transformers (pip install sentence-transformers)
Model: paraphrase-multilingual-MiniLM-L12-v2 (cross-lingual, 50 languages)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed. Run: pip3 install --user sentence-transformers", file=sys.stderr)
    sys.exit(1)

import numpy as np


HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
RICH_CSV = DATA_DIR / "anthropic-aei-onet-2026-03-24.csv"
PEN_CSV = DATA_DIR / "anthropic-task-penetration.csv"
EMBED_CACHE = HERE / ".embeddings-cache.npz"

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def load_onet_tasks() -> list[dict]:
    """Load all O*NET tasks (rich subset + penetration fallback) into a unified list."""
    tasks: dict[str, dict] = {}
    with RICH_CSV.open() as f:
        for row in csv.DictReader(f):
            tasks[row["task"].lower()] = {
                "task": row["task"],
                "in_rich": True,
                "count": float(row.get("count") or 0),
                "pct": float(row.get("pct") or 0),
                "ai_autonomy_mean": float(row.get("ai_autonomy_mean") or 0) or None,
                "ai_education_years_mean": float(row.get("ai_education_years_mean") or 0) or None,
                "human_education_years_mean": float(row.get("human_education_years_mean") or 0) or None,
            }
    with PEN_CSV.open() as f:
        for row in csv.DictReader(f):
            key = row["task"].lower()
            if key not in tasks:
                tasks[key] = {
                    "task": row["task"],
                    "in_rich": False,
                    "count": 0,
                    "pct": 0,
                    "penetration": float(row.get("penetration") or 0),
                    "ai_autonomy_mean": None,
                    "ai_education_years_mean": None,
                    "human_education_years_mean": None,
                }
            else:
                tasks[key]["penetration"] = float(row.get("penetration") or 0)
    return list(tasks.values())


def embed_tasks(model: SentenceTransformer, tasks: list[dict]) -> np.ndarray:
    """Embed all task statements; cache to disk."""
    if EMBED_CACHE.exists():
        cached = np.load(EMBED_CACHE, allow_pickle=True)
        if len(cached["embeddings"]) == len(tasks):
            return cached["embeddings"]
    print(f"Embedding {len(tasks)} O*NET tasks (one-time, cached afterwards)...", file=sys.stderr)
    texts = [t["task"] for t in tasks]
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)
    np.savez(EMBED_CACHE, embeddings=embeddings, n=len(tasks))
    return embeddings


def match_activities(
    activities: list[dict],
    tasks: list[dict],
    task_embeddings: np.ndarray,
    model: SentenceTransformer,
    top_k: int = 5,
    threshold: float = 0.0,
    min_top1: float = 0.0,
) -> list[dict]:
    """For each activity, return ranked O*NET task matches with similarity scores.

    If `min_top1 > 0` and the best match has similarity below `min_top1`, the
    activity is returned with `matches=[]` and `low_confidence=True`. This
    prevents the downstream pipeline from over-classifying activities whose
    top-1 alignment is too weak to be useful.
    """
    activity_texts = [a["text"] for a in activities]
    activity_embeddings = model.encode(activity_texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)

    # Cosine similarity (vectors are normalized, so dot product = cosine)
    similarities = activity_embeddings @ task_embeddings.T

    results = []
    for i, activity in enumerate(activities):
        sims = similarities[i]
        top_indices = np.argsort(-sims)[:top_k]
        top1_sim = float(sims[top_indices[0]]) if len(top_indices) else 0.0
        if min_top1 > 0 and top1_sim < min_top1:
            results.append({
                "id": activity["id"],
                "text": activity["text"],
                "matches": [],
                "low_confidence": True,
                "top1_similarity_observed": round(top1_sim, 4),
                "min_top1_threshold": min_top1,
            })
            continue
        matches = []
        for idx in top_indices:
            score = float(sims[idx])
            if score < threshold:
                continue
            t = tasks[idx]
            matches.append({
                "task": t["task"],
                "similarity": round(score, 4),
                "in_rich": t["in_rich"],
                "count": t.get("count"),
                "ai_autonomy_mean": t.get("ai_autonomy_mean"),
                "ai_education_years_mean": t.get("ai_education_years_mean"),
                "human_education_years_mean": t.get("human_education_years_mean"),
                "penetration": t.get("penetration"),
            })
        results.append({
            "id": activity["id"],
            "text": activity["text"],
            "matches": matches,
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Match activities to O*NET tasks via multilingual embeddings.")
    parser.add_argument("--activities", required=True, help="JSON file with [{id, text}, ...]")
    parser.add_argument("--top-k", type=int, default=5, help="Top K matches per activity")
    parser.add_argument("--threshold", type=float, default=0.0, help="Minimum cosine similarity (0-1) to include a single match")
    parser.add_argument(
        "--min-top1",
        type=float,
        default=0.0,
        help="If the best match has similarity below this value, return empty matches and flag the activity as low_confidence. "
             "Recommended: 0.55. Activities scoring below this typically reflect domain-specific concepts the embedding model cannot map reliably.",
    )
    parser.add_argument("--out", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    activities = json.loads(Path(args.activities).read_text())
    if not isinstance(activities, list):
        print("ERROR: activities file must be a JSON list", file=sys.stderr)
        return 1

    tasks = load_onet_tasks()
    print(f"Loaded {len(tasks)} O*NET tasks ({sum(1 for t in tasks if t['in_rich'])} in rich subset).", file=sys.stderr)

    print(f"Loading model {MODEL_NAME}...", file=sys.stderr)
    model = SentenceTransformer(MODEL_NAME)

    task_embeddings = embed_tasks(model, tasks)

    results = match_activities(
        activities, tasks, task_embeddings, model,
        top_k=args.top_k, threshold=args.threshold, min_top1=args.min_top1,
    )
    n_low_conf = sum(1 for r in results if r.get("low_confidence"))
    if args.min_top1 > 0:
        print(f"Low-confidence activities (top-1 < {args.min_top1}): {n_low_conf} / {len(results)}", file=sys.stderr)

    output = json.dumps(results, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(output)
        print(f"Wrote {len(results)} activity matches → {args.out}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
