"""Script to evaluate:
1. Top-k ablation (k = 3, 5, 8) end-to-end (Retrieval Recall, F1, Citations, Tokens, Latency).
2. Model comparison: gemma2:2b vs qwen2.5:3b on RTX 5070 GPU (Tokens/sec, F1, Citations, Latency, Refusal).
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
import ollama

from generation.generator import RAGPipeline
from evaluation.evaluate_e2e import compute_token_f1, compute_faithfulness

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BENCHMARK_PATH = ROOT_DIR / "data" / "evaluation" / "benchmark_queries.json"
HELD_OUT_PATH = ROOT_DIR / "data" / "evaluation" / "held_out_unanswerable.json"
OUTPUT_PATH = ROOT_DIR / "data" / "evaluation" / "k_and_models_evaluation.json"


def evaluate_k_ablation(queries: List[Dict[str, Any]], k_values: List[int] = [3, 5, 8]) -> Dict[str, Any]:
    ans_queries = [q for q in queries if q["answerable"]]
    pipeline = RAGPipeline(model="gemma2:2b")
    results = {}

    for k in k_values:
        logger.info(f"Running End-to-End Evaluation for Top-k = {k}...")
        recalls, f1_scores, cit_accs, cit_precs, latencies, ctx_lengths = [], [], [], [], [], []

        for q in ans_queries:
            t0 = time.perf_counter()
            rag_res = pipeline.answer(q["question"], top_k=k)
            dur_ms = (time.perf_counter() - t0) * 1000.0

            # Retrieval recall
            expected_set = set(q.get("relevant_sources", []))
            retrieved_sources = set(c["source"] for c in rag_res.all_retrieved_sources[:k])
            matched = expected_set.intersection(retrieved_sources)
            rec = len(matched) / len(expected_set) if expected_set else 0.0
            recalls.append(rec)

            # Answer F1
            f1 = compute_token_f1(rag_res.answer, q.get("reference_answer", ""))
            f1_scores.append(f1)

            # Citations
            cited = rag_res.cited_sources
            if cited:
                correct_cit = sum(1 for c in cited if c.source_file in expected_set)
                prec = correct_cit / len(cited)
            else:
                prec = 0.0
            cit_precs.append(prec)
            acc = 1.0 if (prec > 0 and not rag_res.hallucinated_citations) else 0.0
            cit_accs.append(acc)

            # Context size
            ctx_chars = sum(len(c.get("text", "")) for c in rag_res.all_retrieved_sources[:k])
            ctx_lengths.append(ctx_chars)
            latencies.append(dur_ms)

        results[f"top_{k}"] = {
            "k": k,
            "retrieval_recall_at_k": round(float(np.mean(recalls)) * 100, 2),
            "answer_correctness_f1": round(float(np.mean(f1_scores)) * 100, 2),
            "citation_precision": round(float(np.mean(cit_precs)) * 100, 2),
            "citation_accuracy": round(float(np.mean(cit_accs)) * 100, 2),
            "mean_context_chars": round(float(np.mean(ctx_lengths)), 1),
            "estimated_context_tokens": round(float(np.mean(ctx_lengths)) / 4, 1),
            "mean_latency_ms": round(float(np.mean(latencies)), 1),
        }

    return results


def evaluate_models_comparison(
    queries: List[Dict[str, Any]],
    held_out_queries: List[Dict[str, Any]],
    models: List[str] = ["gemma2:2b", "qwen2.5:3b"],
) -> Dict[str, Any]:
    ans_queries = [q for q in queries if q["answerable"]]
    results = {}

    for model_name in models:
        logger.info(f"Evaluating Model Head-to-Head: {model_name}...")
        pipeline = RAGPipeline(model=model_name)

        # Warm up
        ollama.chat(model=model_name, messages=[{"role": "user", "content": "Hi"}], options={"temperature": 0.0})

        f1_scores, cit_precs, cit_recalls, cit_accs, tok_rates, latencies = [], [], [], [], [], []
        vi_f1_scores, en_f1_scores = [], []

        for q in ans_queries:
            t0 = time.perf_counter()
            rag_res = pipeline.answer(q["question"], top_k=5)
            dur_ms = (time.perf_counter() - t0) * 1000.0

            # Measure token throughput via ollama response metadata if possible
            expected_set = set(q.get("relevant_sources", []))
            f1 = compute_token_f1(rag_res.answer, q.get("reference_answer", ""))
            f1_scores.append(f1)
            if q["language"] == "vi":
                vi_f1_scores.append(f1)
            else:
                en_f1_scores.append(f1)

            cited = rag_res.cited_sources
            if cited:
                correct_cit = sum(1 for c in cited if c.source_file in expected_set)
                prec = correct_cit / len(cited)
                cited_files = set(c.source_file for c in cited)
                rec = len(expected_set.intersection(cited_files)) / len(expected_set) if expected_set else 0.0
            else:
                prec, rec = 0.0, 0.0
            cit_precs.append(prec)
            cit_recalls.append(rec)
            acc = 1.0 if (prec > 0 and not rag_res.hallucinated_citations) else 0.0
            cit_accs.append(acc)
            if rag_res.tokens_per_second > 0:
                tok_rates.append(rag_res.tokens_per_second)
            latencies.append(dur_ms)

        # Measure refusal on 20 held-out
        refusal_hits = 0
        refusal_markers = ["không chứa thông tin", "nằm ngoài", "does not contain", "outside the provided", "cannot answer"]
        for q in held_out_queries:
            rag_res = pipeline.answer(q["question"], top_k=5)
            ans_l = rag_res.answer.lower()
            if any(m in ans_l for m in refusal_markers):
                refusal_hits += 1
        refusal_rate = (refusal_hits / len(held_out_queries)) * 100

        results[model_name] = {
            "model": model_name,
            "overall_answer_f1": round(float(np.mean(f1_scores)) * 100, 2),
            "english_answer_f1": round(float(np.mean(en_f1_scores)) * 100, 2),
            "vietnamese_answer_f1": round(float(np.mean(vi_f1_scores)) * 100, 2),
            "citation_precision": round(float(np.mean(cit_precs)) * 100, 2),
            "citation_recall": round(float(np.mean(cit_recalls)) * 100, 2),
            "citation_accuracy": round(float(np.mean(cit_accs)) * 100, 2),
            "held_out_refusal_rate": round(refusal_rate, 2),
            "mean_tokens_per_second": round(float(np.mean(tok_rates)), 2) if tok_rates else 0.0,
            "mean_end_to_end_latency_ms": round(float(np.mean(latencies)), 1),
        }

    return results


def main():
    queries = json.load(open(BENCHMARK_PATH, encoding="utf-8"))
    held_out = json.load(open(HELD_OUT_PATH, encoding="utf-8"))

    # 1. Top-k Ablation
    k_res = evaluate_k_ablation(queries, k_values=[3, 5, 8])

    # 2. Models Comparison
    model_res = evaluate_models_comparison(queries, held_out, models=["gemma2:2b", "qwen2.5:3b"])

    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "top_k_ablation": k_res,
        "model_comparison": model_res,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 90)
    print("TOP-K END-TO-END ABLATION RESULTS (Gemma 2 2B on RTX 5070):")
    print("=" * 90)
    print(f"{'Top-k':<8} | {'Recall@k':<10} | {'Answer F1':<11} | {'Cit Prec':<10} | {'Cit Acc':<10} | {'Context Chars':<15} | {'Latency':<10}")
    print("-" * 90)
    for k_key, v in k_res.items():
        print(f"{v['k']:<8} | {v['retrieval_recall_at_k']:.2f}%{'':<3} | {v['answer_correctness_f1']:.2f}%{'':<4} | {v['citation_precision']:.2f}%{'':<3} | {v['citation_accuracy']:.2f}%{'':<3} | ~{v['mean_context_chars']} chars{'':<3} | {v['mean_latency_ms']:.1f}ms")

    print("\n" + "=" * 90)
    print("MODEL HEAD-TO-HEAD COMPARISON (Answerable n=50, Held-out Unanswerable n=20):")
    print("=" * 90)
    print(f"{'Model':<12} | {'Overall F1':<11} | {'EN F1':<9} | {'VI F1':<9} | {'Cit Prec':<10} | {'Cit Acc':<9} | {'Refusal':<9} | {'Tokens/s':<10} | {'Latency':<10}")
    print("-" * 105)
    for m_key, v in model_res.items():
        print(f"{v['model']:<12} | {v['overall_answer_f1']:.2f}%{'':<4} | {v['english_answer_f1']:.2f}%{'':<2} | {v['vietnamese_answer_f1']:.2f}%{'':<2} | {v['citation_precision']:.2f}%{'':<3} | {v['citation_accuracy']:.2f}%{'':<2} | {v['held_out_refusal_rate']:.1f}%{'':<2} | {v['mean_tokens_per_second']:.1f} t/s{'':<3} | {v['mean_end_to_end_latency_ms']:.1f}ms")
    print("=" * 105)


if __name__ == "__main__":
    main()
