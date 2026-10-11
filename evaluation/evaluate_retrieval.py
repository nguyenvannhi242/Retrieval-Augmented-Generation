"""Evaluation script to measure Recall@k, MRR@k, Hit Rate@k, and Latency against benchmark queries."""

from __future__ import annotations

import json
import logging
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from retrieval.search import DocumentRetriever, SearchResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
BENCHMARK_PATH = ROOT_DIR / "data" / "evaluation" / "benchmark_queries.json"
BASELINE_OUTPUT_PATH = ROOT_DIR / "data" / "evaluation" / "retrieval_baseline.json"
CORPUS_JSONL = PROCESSED_DATA_DIR / "corpus.jsonl"


def count_corpus_chunks(corpus_path: Path = CORPUS_JSONL) -> int:
    """Counts the total chunks in the processed corpus."""
    if not corpus_path.exists():
        return 0
    with open(corpus_path, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def evaluate_query(
    query_item: Dict[str, Any],
    retriever: DocumentRetriever,
    top_k: int = 5,
) -> Dict[str, Any]:
    """Runs a single query, calculates metrics at the source file level."""
    query_id = query_item["query_id"]
    question = query_item["question"]
    language = query_item["language"]
    category = query_item["category"]
    expected_sources: List[str] = query_item.get("relevant_sources", [])
    expected_set: Set[str] = set(expected_sources)

    # Measure latency precisely
    start_time = time.perf_counter()
    results: List[SearchResult] = retriever.search(question, top_k=top_k)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    retrieved_sources = [r.source for r in results]
    unique_retrieved_sources = list(dict.fromkeys(retrieved_sources))

    is_unanswerable = category == "unanswerable" or len(expected_sources) == 0

    if is_unanswerable:
        return {
            "query_id": query_id,
            "question": question,
            "language": language,
            "category": category,
            "is_unanswerable": True,
            "latency_ms": elapsed_ms,
            "retrieved_sources": retrieved_sources,
            "top_similarity": results[0].score if results else 0.0,
            "recall_at_5": None,
            "mrr_at_5": None,
            "hit_at_5": None,
        }

    # Evaluate at source level
    retrieved_source_set = set(retrieved_sources[:top_k])
    matched_sources = expected_set.intersection(retrieved_source_set)

    # Recall@k: fraction of expected sources present in retrieved sources
    recall = len(matched_sources) / len(expected_set) if expected_set else 0.0

    # Hit Rate@k: at least one expected source in top_k
    hit = 1.0 if len(matched_sources) > 0 else 0.0

    # MRR@k: 1 / rank of first relevant source in top_k
    first_rank: Optional[int] = None
    for idx, hit_res in enumerate(results[:top_k]):
        if hit_res.source in expected_set:
            first_rank = idx + 1
            break

    mrr = (1.0 / first_rank) if first_rank is not None else 0.0

    return {
        "query_id": query_id,
        "question": question,
        "language": language,
        "category": category,
        "is_unanswerable": False,
        "latency_ms": elapsed_ms,
        "expected_sources": expected_sources,
        "retrieved_sources": retrieved_sources,
        "unique_retrieved_sources": unique_retrieved_sources,
        "first_relevant_rank": first_rank,
        "recall_at_5": recall,
        "mrr_at_5": mrr,
        "hit_at_5": hit,
        "top_similarity": results[0].score if results else 0.0,
    }


def compute_aggregate_metrics(eval_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes summary statistics for a given group of evaluation records."""
    answerable = [r for r in eval_records if not r["is_unanswerable"]]
    if not answerable:
        return {"count": 0}

    recalls = [r["recall_at_5"] for r in answerable]
    mrrs = [r["mrr_at_5"] for r in answerable]
    hits = [r["hit_at_5"] for r in answerable]
    latencies = [r["latency_ms"] for r in eval_records]

    return {
        "count": len(answerable),
        "recall_at_5": round(statistics.mean(recalls), 4),
        "mrr_at_5": round(statistics.mean(mrrs), 4),
        "hit_rate_at_5": round(statistics.mean(hits), 4),
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 2),
            "median": round(statistics.median(latencies), 2),
            "p95": round(statistics.quantiles(latencies, n=20)[18], 2) if len(latencies) >= 20 else round(max(latencies), 2),
            "min": round(min(latencies), 2),
            "max": round(max(latencies), 2),
        },
    }


def run_benchmark(
    benchmark_file: Path = BENCHMARK_PATH,
    output_file: Path = BASELINE_OUTPUT_PATH,
    top_k: int = 5,
) -> Dict[str, Any]:
    """Loads benchmark queries, evaluates baseline retrieval, and exports baseline report."""
    if not benchmark_file.exists():
        raise FileNotFoundError(f"Benchmark file not found: {benchmark_file}")

    with open(benchmark_file, "r", encoding="utf-8") as f:
        queries: List[Dict[str, Any]] = json.load(f)

    logger.info(f"Loaded {len(queries)} benchmark queries.")
    total_indexed_chunks = count_corpus_chunks()

    logger.info("Initializing DocumentRetriever...")
    retriever = DocumentRetriever()

    # Warm-up model to exclude initial model compilation overhead from latency stats
    logger.info("Warming up retriever...")
    _ = retriever.search("warmup query", top_k=1)

    logger.info(f"Evaluating {len(queries)} queries...")
    eval_records: List[Dict[str, Any]] = []

    for item in queries:
        record = evaluate_query(item, retriever, top_k=top_k)
        eval_records.append(record)

    # Slice subgroups
    en_records = [r for r in eval_records if r["language"] == "en" and not r["is_unanswerable"]]
    vi_records = [r for r in eval_records if r["language"] == "vi" and not r["is_unanswerable"]]
    unanswerable_records = [r for r in eval_records if r["is_unanswerable"]]

    # Per-category aggregation
    categories = sorted(set(r["category"] for r in eval_records if not r["is_unanswerable"]))
    category_metrics = {}
    for cat in categories:
        cat_subset = [r for r in eval_records if r["category"] == cat]
        category_metrics[cat] = compute_aggregate_metrics(cat_subset)

    overall_metrics = compute_aggregate_metrics(eval_records)
    en_metrics = compute_aggregate_metrics(en_records)
    vi_metrics = compute_aggregate_metrics(vi_records)

    # Unanswerable analysis
    unans_top_sims = [r["top_similarity"] for r in unanswerable_records]
    unanswerable_analysis = {
        "count": len(unanswerable_records),
        "mean_top_similarity": round(statistics.mean(unans_top_sims), 4) if unans_top_sims else 0.0,
        "max_top_similarity": round(max(unans_top_sims), 4) if unans_top_sims else 0.0,
        "min_top_similarity": round(min(unans_top_sims), 4) if unans_top_sims else 0.0,
    }

    report = {
        "embedding_model": {
            "name": retriever.model_name,
            "architecture": "bge-small-en-v1.5",
            "distance_metric": "cosine",
            "vector_dimension": 384,
            "query_instruction": retriever.query_instruction,
        },
        "chunking_config": {
            "splitter": "MarkdownHeaderTextSplitter + RecursiveCharacterTextSplitter",
            "chunk_size": 750,
            "chunk_overlap": 100,
            "headers_split": ["#", "##", "###"],
        },
        "indexed_chunks_count": total_indexed_chunks,
        "benchmark_summary": {
            "total_queries": len(queries),
            "answerable_queries": len(queries) - len(unanswerable_records),
            "unanswerable_queries": len(unanswerable_records),
            "languages": {
                "en": sum(1 for q in queries if q["language"] == "en"),
                "vi": sum(1 for q in queries if q["language"] == "vi"),
            },
        },
        "metrics_overall_answerable": overall_metrics,
        "metrics_by_language": {
            "english": en_metrics,
            "vietnamese": vi_metrics,
        },
        "metrics_by_category": category_metrics,
        "unanswerable_analysis": unanswerable_analysis,
        "detailed_query_results": eval_records,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Baseline evaluation saved to: {output_file}")

    # Console display table
    print("\n" + "=" * 70)
    print(" 📊 RETRIEVAL BASELINE BENCHMARK RESULTS")
    print("=" * 70)
    print(f" • Model:                 {retriever.model_name}")
    print(f" • Chunks Indexed:        {total_indexed_chunks}")
    print(f" • Total Queries:         {len(queries)} ({overall_metrics['count']} answerable, {len(unanswerable_records)} negative)")
    print("─" * 70)
    print(f" • Overall Recall@5:      {overall_metrics['recall_at_5'] * 100:.2f}%")
    print(f" • Overall MRR@5:         {overall_metrics['mrr_at_5']:.4f}")
    print(f" • Overall Hit Rate@5:    {overall_metrics['hit_rate_at_5'] * 100:.2f}%")
    print(f" • Latency (Median):      {overall_metrics['latency_ms']['median']:.1f} ms")
    print(f" • Latency (Mean):        {overall_metrics['latency_ms']['mean']:.1f} ms")
    print("─" * 70)
    print(" 🌐 LANGUAGE COMPARISON:")
    print(f"   ► English (n={en_metrics['count']}):")
    print(f"       Recall@5:     {en_metrics['recall_at_5'] * 100:.2f}%")
    print(f"       MRR@5:        {en_metrics['mrr_at_5']:.4f}")
    print(f"       Hit Rate@5:   {en_metrics['hit_rate_at_5'] * 100:.2f}%")
    print(f"       Latency:      {en_metrics['latency_ms']['median']:.1f} ms")
    print(f"   ► Vietnamese (Cross-lingual, n={vi_metrics['count']}):")
    print(f"       Recall@5:     {vi_metrics['recall_at_5'] * 100:.2f}%")
    print(f"       MRR@5:        {vi_metrics['mrr_at_5']:.4f}")
    print(f"       Hit Rate@5:   {vi_metrics['hit_rate_at_5'] * 100:.2f}%")
    print(f"       Latency:      {vi_metrics['latency_ms']['median']:.1f} ms")
    print("─" * 70)
    print(" 🏷️ CATEGORY BREAKDOWN:")
    for cat, m in category_metrics.items():
        print(f"   ► {cat.upper()} (n={m['count']}): Recall@5={m['recall_at_5']*100:.1f}%, MRR@5={m['mrr_at_5']:.3f}, HitRate@5={m['hit_rate_at_5']*100:.1f}%")
    print("─" * 70)
    print(" 🚫 UNANSWERABLE / OUT-OF-DOMAIN QUERIES:")
    print(f"   ► Total Negative queries: {unanswerable_analysis['count']}")
    print(f"   ► Mean Top Cosine Similarity: {unanswerable_analysis['mean_top_similarity']:.4f}")
    print(f"   ► Max Top Cosine Similarity:  {unanswerable_analysis['max_top_similarity']:.4f}")
    print("=" * 70 + "\n")

    return report


if __name__ == "__main__":
    run_benchmark()
