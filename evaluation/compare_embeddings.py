"""Script to compare embedding models (BAAI/bge-small-en-v1.5 vs intfloat/multilingual-e5-small)
across English, Vietnamese cross-lingual, and Unanswerable queries.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT_DIR / "data" / "processed" / "corpus.jsonl"
BENCHMARK_PATH = ROOT_DIR / "data" / "evaluation" / "benchmark_queries.json"
OUTPUT_PATH = ROOT_DIR / "data" / "evaluation" / "embedding_comparison.json"


def load_corpus() -> List[Dict[str, Any]]:
    chunks = []
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def load_benchmark() -> List[Dict[str, Any]]:
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_embedding_model(
    model_name: str,
    query_prefix: str,
    passage_prefix: str,
    chunks: List[Dict[str, Any]],
    queries: List[Dict[str, Any]],
    top_k: int = 5,
) -> Dict[str, Any]:
    logger.info(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)

    logger.info(f"Encoding {len(chunks)} corpus passages with {model_name}...")
    t0 = time.perf_counter()
    passages = [f"{passage_prefix}{c['text']}" for c in chunks]
    passage_embs = model.encode(passages, batch_size=128, show_progress_bar=False, normalize_embeddings=True)
    encode_time = time.perf_counter() - t0
    logger.info(f"Corpus encoded in {encode_time:.2f}s.")

    chunk_sources = [c["source"] for c in chunks]

    answerable_queries = [q for q in queries if q["answerable"]]
    unanswerable_queries = [q for q in queries if not q["answerable"]]

    # Evaluate queries
    results_by_query = []
    latencies = []

    for q in queries:
        q_text = f"{query_prefix}{q['question']}"
        t_start = time.perf_counter()
        q_emb = model.encode([q_text], normalize_embeddings=True)[0]
        # Cosine similarities
        sims = np.dot(passage_embs, q_emb)
        top_indices = np.argsort(sims)[::-1][:top_k]
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        latencies.append(elapsed_ms)

        retrieved_sources = [chunk_sources[i] for i in top_indices]
        top_scores = [float(sims[i]) for i in top_indices]
        expected_set = set(q.get("relevant_sources", []))

        is_ans = q["answerable"]
        if is_ans:
            matched = expected_set.intersection(set(retrieved_sources))
            recall = len(matched) / len(expected_set) if expected_set else 0.0
            hit = 1.0 if matched else 0.0
            first_rank = None
            for r_idx, s in enumerate(retrieved_sources, start=1):
                if s in expected_set:
                    first_rank = r_idx
                    break
            mrr = 1.0 / first_rank if first_rank is not None else 0.0
        else:
            recall, hit, mrr = None, None, None

        results_by_query.append({
            "query_id": q["query_id"],
            "language": q["language"],
            "answerable": is_ans,
            "recall_at_5": recall,
            "hit_at_5": hit,
            "mrr_at_5": mrr,
            "top_similarity": top_scores[0],
            "latency_ms": elapsed_ms,
        })

    def calc_group(group: List[Dict[str, Any]]) -> Dict[str, Any]:
        ans = [r for r in group if r["answerable"]]
        return {
            "count": len(group),
            "answerable_count": len(ans),
            "recall_at_5": round(float(np.mean([r["recall_at_5"] for r in ans])), 4) if ans else 0.0,
            "mrr_at_5": round(float(np.mean([r["mrr_at_5"] for r in ans])), 4) if ans else 0.0,
            "hit_rate_at_5": round(float(np.mean([r["hit_at_5"] for r in ans])), 4) if ans else 0.0,
            "mean_latency_ms": round(float(np.mean([r["latency_ms"] for r in group])), 2),
        }

    en_queries = [r for r in results_by_query if r["language"] == "en"]
    vi_queries = [r for r in results_by_query if r["language"] == "vi"]
    unans_results = [r for r in results_by_query if not r["answerable"]]

    summary = {
        "model_name": model_name,
        "overall_answerable": calc_group([r for r in results_by_query if r["answerable"]]),
        "english_answerable": calc_group([r for r in en_queries if r["answerable"]]),
        "vietnamese_answerable": calc_group([r for r in vi_queries if r["answerable"]]),
        "unanswerable_mean_similarity": round(float(np.mean([r["top_similarity"] for r in unans_results])), 4),
        "unanswerable_max_similarity": round(float(max(r["top_similarity"] for r in unans_results)), 4),
        "corpus_encode_time_sec": round(encode_time, 2),
    }

    return summary


def main():
    chunks = load_corpus()
    queries = load_benchmark()
    logger.info(f"Loaded {len(chunks)} chunks and {len(queries)} queries.")

    # 1. Baseline: BAAI/bge-small-en-v1.5
    bge_summary = evaluate_embedding_model(
        model_name="BAAI/bge-small-en-v1.5",
        query_prefix="Represent this sentence for searching relevant passages: ",
        passage_prefix="",
        chunks=chunks,
        queries=queries,
        top_k=5,
    )

    # 2. Multilingual: intfloat/multilingual-e5-small
    e5_summary = evaluate_embedding_model(
        model_name="intfloat/multilingual-e5-small",
        query_prefix="query: ",
        passage_prefix="passage: ",
        chunks=chunks,
        queries=queries,
        top_k=5,
    )

    output = {
        "comparison_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bge_small_en": bge_summary,
        "multilingual_e5_small": e5_summary,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("EMBEDDING MODEL COMPARISON RESULTS:")
    print("=" * 70)
    print(f"{'Metric':<30} | {'BGE-small-en-v1.5':<18} | {'Multilingual-E5-small':<20}")
    print("-" * 75)
    print(f"{'Overall Recall@5 (n=50)':<30} | {bge_summary['overall_answerable']['recall_at_5']*100:.2f}%{'':<11} | {e5_summary['overall_answerable']['recall_at_5']*100:.2f}%")
    print(f"{'Overall MRR@5 (n=50)':<30} | {bge_summary['overall_answerable']['mrr_at_5']:.4f}{'':<12} | {e5_summary['overall_answerable']['mrr_at_5']:.4f}")
    print(f"{'Overall Hit Rate@5 (n=50)':<30} | {bge_summary['overall_answerable']['hit_rate_at_5']*100:.2f}%{'':<11} | {e5_summary['overall_answerable']['hit_rate_at_5']*100:.2f}%")
    print("-" * 75)
    print(f"{'English Recall@5 (n=30)':<30} | {bge_summary['english_answerable']['recall_at_5']*100:.2f}%{'':<11} | {e5_summary['english_answerable']['recall_at_5']*100:.2f}%")
    print(f"{'English MRR@5 (n=30)':<30} | {bge_summary['english_answerable']['mrr_at_5']:.4f}{'':<12} | {e5_summary['english_answerable']['mrr_at_5']:.4f}")
    print("-" * 75)
    print(f"{'Vietnamese Recall@5 (n=20)':<30} | {bge_summary['vietnamese_answerable']['recall_at_5']*100:.2f}%{'':<11} | {e5_summary['vietnamese_answerable']['recall_at_5']*100:.2f}%")
    print(f"{'Vietnamese MRR@5 (n=20)':<30} | {bge_summary['vietnamese_answerable']['mrr_at_5']:.4f}{'':<12} | {e5_summary['vietnamese_answerable']['mrr_at_5']:.4f}")
    print(f"{'Vietnamese Hit Rate@5 (n=20)':<30} | {bge_summary['vietnamese_answerable']['hit_rate_at_5']*100:.2f}%{'':<11} | {e5_summary['vietnamese_answerable']['hit_rate_at_5']*100:.2f}%")
    print("-" * 75)
    print(f"{'Unanswerable Mean Sim':<30} | {bge_summary['unanswerable_mean_similarity']:.4f}{'':<12} | {e5_summary['unanswerable_mean_similarity']:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
