"""Evaluates refusal performance on 20 held-out unseen unanswerable queries,
and measures over-refusal rate on 50 answerable queries.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np

from generation.generator import RAGPipeline
from evaluation.evaluate_e2e import compute_faithfulness

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BENCHMARK_PATH = ROOT_DIR / "data" / "evaluation" / "benchmark_queries.json"
HELD_OUT_PATH = ROOT_DIR / "data" / "evaluation" / "held_out_unanswerable.json"
OUTPUT_PATH = ROOT_DIR / "data" / "evaluation" / "refusal_evaluation_results.json"


def check_is_refusal(text: str) -> bool:
    text_lower = text.lower()
    refusal_markers = [
        "không chứa thông tin",
        "nằm ngoài phạm vi",
        "không có thông tin",
        "không thể trả lời",
        "does not contain information",
        "not contain information",
        "outside the provided",
        "outside fastapi",
        "not documented",
        "does not provide",
        "doesn't provide",
        "cannot answer",
        "không tìm thấy",
        "không hỗ trợ",
    ]
    return any(m in text_lower for m in refusal_markers)


def main():
    logger.info("Initializing RAGPipeline (model=gemma2:2b)...")
    pipeline = RAGPipeline(model="gemma2:2b")

    # 1. Evaluate 20 held-out unanswerable queries
    held_out_queries = json.load(open(HELD_OUT_PATH, "r", encoding="utf-8"))
    logger.info(f"Evaluating {len(held_out_queries)} held-out unanswerable queries...")

    held_out_results = []
    for q in held_out_queries:
        rag_res = pipeline.answer(q["question"], top_k=5)
        ans = rag_res.answer
        is_refused = check_is_refusal(ans)
        held_out_results.append({
            "query_id": q["query_id"],
            "language": q["language"],
            "question": q["question"],
            "answer": ans,
            "refused": is_refused,
        })

    held_out_refusal_rate = float(np.mean([1.0 if r["refused"] else 0.0 for r in held_out_results]))
    en_held_out = [r for r in held_out_results if r["language"] == "en"]
    vi_held_out = [r for r in held_out_results if r["language"] == "vi"]
    en_refusal = float(np.mean([1.0 if r["refused"] else 0.0 for r in en_held_out]))
    vi_refusal = float(np.mean([1.0 if r["refused"] else 0.0 for r in vi_held_out]))

    # 2. Evaluate Over-refusal on 50 answerable queries
    benchmark_queries = json.load(open(BENCHMARK_PATH, "r", encoding="utf-8"))
    answerable_queries = [q for q in benchmark_queries if q["answerable"]]
    logger.info(f"Evaluating over-refusal on {len(answerable_queries)} answerable queries...")

    over_refusal_results = []
    for q in answerable_queries:
        rag_res = pipeline.answer(q["question"], top_k=5)
        ans = rag_res.answer
        is_refused = check_is_refusal(ans)
        over_refusal_results.append({
            "query_id": q["query_id"],
            "language": q["language"],
            "question": q["question"],
            "answer": ans,
            "falsely_refused": is_refused,
        })

    over_refusal_count = sum(1 for r in over_refusal_results if r["falsely_refused"])
    over_refusal_rate = float(over_refusal_count / len(answerable_queries))

    # Bootstrap CI for held-out refusal (10,000 resamples)
    boot_refusals = []
    ref_binary = [1.0 if r["refused"] else 0.0 for r in held_out_results]
    np.random.seed(42)
    for _ in range(10000):
        sample = np.random.choice(ref_binary, size=len(ref_binary), replace=True)
        boot_refusals.append(np.mean(sample))
    ci_ref_low = float(np.percentile(boot_refusals, 2.5))
    ci_ref_high = float(np.percentile(boot_refusals, 97.5))

    summary = {
        "held_out_unanswerable_n": len(held_out_queries),
        "held_out_overall_refusal_rate": round(held_out_refusal_rate * 100, 2),
        "held_out_refusal_95_ci": [round(ci_ref_low * 100, 2), round(ci_ref_high * 100, 2)],
        "held_out_english_refusal_rate": round(en_refusal * 100, 2),
        "held_out_vietnamese_refusal_rate": round(vi_refusal * 100, 2),
        "answerable_evaluated_n": len(answerable_queries),
        "over_refusal_count": over_refusal_count,
        "over_refusal_rate": round(over_refusal_rate * 100, 2),
        "detailed_held_out": held_out_results,
        "falsely_refused_queries": [r for r in over_refusal_results if r["falsely_refused"]],
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 75)
    print("REFUSAL & OVER-REFUSAL RIGOROUS EVALUATION RESULTS:")
    print("=" * 75)
    print(f" • Held-out Unanswerable Test Set (n={len(held_out_queries)} unseen queries):")
    print(f"   - Overall Refusal Rate: {summary['held_out_overall_refusal_rate']:.1f}% ({sum(1 for r in held_out_results if r['refused'])}/{len(held_out_queries)})")
    print(f"   - Bootstrap 95% Confidence Interval: [{summary['held_out_refusal_95_ci'][0]}%, {summary['held_out_refusal_95_ci'][1]}%]")
    print(f"   - English Refusal Rate (n=10): {summary['held_out_english_refusal_rate']:.1f}%")
    print(f"   - Vietnamese Refusal Rate (n=10): {summary['held_out_vietnamese_refusal_rate']:.1f}%")
    print("-" * 75)
    print(f" • Answerable Validation Set (n={len(answerable_queries)} queries):")
    print(f"   - Over-refusal Count: {over_refusal_count}/{len(answerable_queries)}")
    print(f"   - Over-refusal Rate (False Negatives): {summary['over_refusal_rate']:.2f}%")
    print("=" * 75)


if __name__ == "__main__":
    main()
