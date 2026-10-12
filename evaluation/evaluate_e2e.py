"""End-to-end RAG evaluation script measuring Retrieval Recall@5, Answer Correctness,
Faithfulness, Citation Accuracy, and Latency — comparing RAG against a No-RAG baseline.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import ollama

from generation.generator import RAGPipeline, SourceCitation
from retrieval.search import DocumentRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
BENCHMARK_PATH = ROOT_DIR / "data" / "evaluation" / "benchmark_queries.json"
JSON_OUTPUT_PATH = ROOT_DIR / "data" / "evaluation" / "rag_e2e_results.json"
CSV_OUTPUT_PATH = ROOT_DIR / "data" / "evaluation" / "rag_e2e_results.csv"


def tokenize_clean(text: str) -> List[str]:
    """Tokenizes and normalizes text for overlap and F1 calculations."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return [w for w in text.split() if len(w) > 1]


def compute_token_f1(prediction: str, reference: str) -> float:
    """Computes token-level F1 score between prediction and reference answer."""
    pred_tokens = tokenize_clean(prediction)
    ref_tokens = tokenize_clean(reference)

    if not pred_tokens or not ref_tokens:
        return 0.0

    pred_set = set(pred_tokens)
    ref_set = set(ref_tokens)
    common = pred_set.intersection(ref_set)

    if not common:
        return 0.0

    precision = len(common) / len(pred_set)
    recall = len(common) / len(ref_set)
    return round((2 * precision * recall) / (precision + recall), 4)


def compute_faithfulness(
    answer: str,
    context_chunks: List[Dict[str, Any]],
    is_unanswerable: bool,
) -> float:
    """Measures if the answer is grounded in retrieved context or correctly refuses unanswerable queries."""
    answer_lower = answer.lower()

    if is_unanswerable:
        refusal_markers = [
            "not found",
            "not mentioned",
            "does not mention",
            "does not contain",
            "does not provide",
            "doesn't provide",
            "doesn't contain",
            "doesn't mention",
            "doesn't offer",
            "does not offer",
            "outside",
            "insufficient",
            "could not find",
            "not documented",
            "cannot answer",
            "không có",
            "không được đề cập",
            "nằm ngoài",
            "chưa có thông tin",
            "không tìm thấy",
            "không hỗ trợ",
            "không chứa thông tin",
            "không thể trả lời",
        ]
        return 1.0 if any(m in answer_lower for m in refusal_markers) else 0.0

    # For answerable queries: check fraction of non-trivial words grounded in context
    combined_context = " ".join(c.get("text", "") for c in context_chunks).lower()
    context_tokens = set(tokenize_clean(combined_context))
    ans_tokens = tokenize_clean(answer)

    if not ans_tokens:
        return 0.0

    supported_count = sum(1 for t in ans_tokens if t in context_tokens)
    return round(supported_count / len(ans_tokens), 4)


def generate_no_rag_answer(question: str, model: str = "gemma2:2b") -> str:
    """Generates direct answer without retrieved documents (closed-book baseline)."""
    system_prompt = (
        "You are a technical assistant. Answer the user's question directly to the best of your knowledge. "
        "Answer in the same language as the user's question. If you do not know or if the topic is outside "
        "FastAPI, state that clearly."
    )
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            options={"temperature": 0.0, "num_predict": 384},
        )
        return response["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Error generating no-rag answer: {e}")
        return f"Error generating answer: {e}"


def evaluate_single_query(
    query_item: Dict[str, Any],
    pipeline: RAGPipeline,
    top_k: int = 5,
    include_no_rag: bool = True,
) -> Dict[str, Any]:
    """Evaluates a single query through both RAG and No-RAG pipelines."""
    query_id = query_item["query_id"]
    question = query_item["question"]
    language = query_item["language"]
    category = query_item["category"]
    expected_sources: List[str] = query_item.get("relevant_sources", [])
    expected_set = set(expected_sources)
    reference_answer = query_item.get("reference_answer", "")
    is_answerable = query_item.get("answerable", True)

    # Execute full RAG pipeline once (retrieval + generation)
    rag_result = pipeline.answer(question, top_k=top_k)

    # Use latency measurements from RAGPipeline.answer() directly
    retrieval_ms = rag_result.retrieval_latency_ms
    generation_ms = rag_result.generation_latency_ms
    total_rag_latency_ms = round(retrieval_ms + generation_ms, 2)

    answer_text = rag_result.answer
    retrieved_chunks = rag_result.all_retrieved_sources
    cited_sources: List[SourceCitation] = rag_result.cited_sources
    hallucinated: List[str] = rag_result.hallucinated_citations

    # 3. Retrieval Recall@5 & Hit Rate@5
    retrieved_source_set = set(c["source"] for c in retrieved_chunks[:top_k])
    if is_answerable and expected_set:
        matched = expected_set.intersection(retrieved_source_set)
        recall_at_5 = round(len(matched) / len(expected_set), 4)
        hit_at_5 = 1.0 if len(matched) > 0 else 0.0
    else:
        recall_at_5 = None
        hit_at_5 = None

    # 4. Citation Accuracy (Precision and Recall)
    if is_answerable:
        if cited_sources:
            correct_citations = sum(1 for c in cited_sources if c.source_file in expected_set)
            citation_precision = round(correct_citations / len(cited_sources), 4)
            # Citation Recall: how many expected sources were cited
            cited_files = set(c.source_file for c in cited_sources)
            citation_recall = round(len(expected_set.intersection(cited_files)) / len(expected_set), 4)
        else:
            citation_precision = 0.0
            citation_recall = 0.0
        # Citation Accuracy metric: 1.0 if cited valid source without hallucination, else proportional
        citation_accuracy = 1.0 if (citation_precision > 0 and not hallucinated) else 0.0
    else:
        # For unanswerable queries: correct behavior is NOT citing anything
        citation_precision = 1.0 if not cited_sources else 0.0
        citation_recall = 1.0 if not cited_sources else 0.0
        citation_accuracy = 1.0 if not cited_sources else 0.0

    # 5. Faithfulness
    faithfulness = compute_faithfulness(
        answer=answer_text,
        context_chunks=retrieved_chunks,
        is_unanswerable=not is_answerable,
    )

    # 6. RAG Answer Correctness (Token F1 vs reference)
    if is_answerable:
        rag_correctness = compute_token_f1(answer_text, reference_answer)
    else:
        rag_correctness = faithfulness  # For unanswerable: refusal score

    # 7. No-RAG Baseline Execution & Correctness (if enabled)
    no_rag_answer = ""
    no_rag_correctness = 0.0
    no_rag_latency_ms = 0.0
    if include_no_rag:
        t_norag_start = time.perf_counter()
        no_rag_answer = generate_no_rag_answer(question, model=pipeline.model)
        no_rag_latency_ms = (time.perf_counter() - t_norag_start) * 1000.0

        if is_answerable:
            no_rag_correctness = compute_token_f1(no_rag_answer, reference_answer)
        else:
            # Check refusal on closed-book
            no_rag_correctness = compute_faithfulness(no_rag_answer, [], is_unanswerable=True)

    return {
        "query_id": query_id,
        "question": question,
        "language": language,
        "category": category,
        "answerable": is_answerable,
        "expected_sources": expected_sources,
        "retrieved_sources": [c["source"] for c in retrieved_chunks],
        "cited_sources": [c.source_file for c in cited_sources],
        "citation_count": len(cited_sources),
        "hallucinated_citations": hallucinated,
        "recall_at_5": recall_at_5,
        "hit_at_5": hit_at_5,
        "citation_precision": citation_precision,
        "citation_recall": citation_recall,
        "citation_accuracy": citation_accuracy,
        "faithfulness": faithfulness,
        "rag_correctness": rag_correctness,
        "no_rag_correctness": no_rag_correctness,
        "retrieval_latency_ms": round(retrieval_ms, 2),
        "generation_latency_ms": round(generation_ms, 2),
        "total_latency_ms": round(total_rag_latency_ms, 2),
        "no_rag_latency_ms": round(no_rag_latency_ms, 2),
        "rag_answer": answer_text,
        "no_rag_answer": no_rag_answer,
        "reference_answer": reference_answer,
    }


def compute_metrics_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregates metrics across evaluated queries."""
    answerable_res = [r for r in results if r["answerable"]]
    unanswerable_res = [r for r in results if not r["answerable"]]

    recalls = [r["recall_at_5"] for r in answerable_res if r["recall_at_5"] is not None]
    hits = [r["hit_at_5"] for r in answerable_res if r["hit_at_5"] is not None]
    citation_precs = [r["citation_precision"] for r in results]
    citation_recalls = [r["citation_recall"] for r in results]
    citation_accuracies = [r["citation_accuracy"] for r in results]
    faithfulness_scores = [r["faithfulness"] for r in results]
    rag_correctness_scores = [r["rag_correctness"] for r in results]
    no_rag_correctness_scores = [r["no_rag_correctness"] for r in results]

    retrieval_latencies = [r["retrieval_latency_ms"] for r in results]
    gen_latencies = [r["generation_latency_ms"] for r in results]
    total_latencies = [r["total_latency_ms"] for r in results]

    rag_corr_mean = round(statistics.mean(rag_correctness_scores), 4) if rag_correctness_scores else 0.0
    no_rag_corr_mean = round(statistics.mean(no_rag_correctness_scores), 4) if no_rag_correctness_scores else 0.0
    uplift = round(rag_corr_mean - no_rag_corr_mean, 4)

    rag_refusal = round(statistics.mean([r["faithfulness"] for r in unanswerable_res]), 4) if unanswerable_res else 0.0
    no_rag_refusal = round(statistics.mean([r["no_rag_correctness"] for r in unanswerable_res]), 4) if unanswerable_res else 0.0

    return {
        "total_evaluated": len(results),
        "answerable_count": len(answerable_res),
        "unanswerable_count": len(unanswerable_res),
        "refusal_rate_rag": rag_refusal,
        "refusal_rate_no_rag": no_rag_refusal,
        "retrieval_recall_at_5": round(statistics.mean(recalls), 4) if recalls else 0.0,
        "hit_rate_at_5": round(statistics.mean(hits), 4) if hits else 0.0,
        "citation_precision": round(statistics.mean(citation_precs), 4) if citation_precs else 0.0,
        "citation_recall": round(statistics.mean(citation_recalls), 4) if citation_recalls else 0.0,
        "citation_accuracy": round(statistics.mean(citation_accuracies), 4) if citation_accuracies else 0.0,
        "faithfulness": round(statistics.mean(faithfulness_scores), 4) if faithfulness_scores else 0.0,
        "rag_correctness": rag_corr_mean,
        "no_rag_correctness": no_rag_corr_mean,
        "rag_uplift": uplift,
        "retrieval_latency_ms": {
            "mean": round(statistics.mean(retrieval_latencies), 2) if retrieval_latencies else 0.0,
            "median": round(statistics.median(retrieval_latencies), 2) if retrieval_latencies else 0.0,
        },
        "generation_latency_ms": {
            "mean": round(statistics.mean(gen_latencies), 2) if gen_latencies else 0.0,
            "median": round(statistics.median(gen_latencies), 2) if gen_latencies else 0.0,
        },
        "total_latency_ms": {
            "mean": round(statistics.mean(total_latencies), 2) if total_latencies else 0.0,
            "median": round(statistics.median(total_latencies), 2) if total_latencies else 0.0,
            "min": round(min(total_latencies), 2) if total_latencies else 0.0,
            "max": round(max(total_latencies), 2) if total_latencies else 0.0,
        },
    }


def run_e2e_benchmark(
    sample_size: Optional[int] = None,
    output_json: Path = JSON_OUTPUT_PATH,
    output_csv: Path = CSV_OUTPUT_PATH,
    model: str = "gemma2:2b",
    include_no_rag: bool = True,
) -> Dict[str, Any]:
    """Runs complete end-to-end evaluation pipeline."""
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"Benchmark file not found at: {BENCHMARK_PATH}")

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        queries: List[Dict[str, Any]] = json.load(f)

    if sample_size and sample_size < len(queries):
        logger.info(f"Selecting balanced sample of {sample_size} queries from {len(queries)}...")
        categories = sorted(set(q["category"] for q in queries))
        per_cat = max(1, sample_size // len(categories))
        selected: List[Dict[str, Any]] = []
        for cat in categories:
            subset = [q for q in queries if q["category"] == cat]
            selected.extend(subset[:per_cat])
        queries = selected[:sample_size]

    logger.info(f"Initializing RAGPipeline with model: {model}...")
    pipeline = RAGPipeline(model=model)

    logger.info(f"Evaluating {len(queries)} benchmark queries (RAG vs No-RAG)...")
    results: List[Dict[str, Any]] = []

    for idx, q in enumerate(queries, start=1):
        q_text = q["question"][:45] + "..." if len(q["question"]) > 45 else q["question"]
        logger.info(f"[{idx:02d}/{len(queries):02d}] {q['query_id']} ({q['language']}|{q['category']}): {q_text}")
        eval_record = evaluate_single_query(
            q, pipeline, top_k=5, include_no_rag=include_no_rag
        )
        results.append(eval_record)

    # Compute aggregate metrics
    overall_summary = compute_metrics_summary(results)
    en_results = [r for r in results if r["language"] == "en"]
    vi_results = [r for r in results if r["language"] == "vi"]
    en_summary = compute_metrics_summary(en_results)
    vi_summary = compute_metrics_summary(vi_results)

    # Try resolving git commit hash
    git_hash = "unknown"
    try:
        import subprocess
        git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        pass

    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
    date_compact = time.strftime("%Y%m%d")

    final_report = {
        "metadata": {
            "evaluation_timestamp": timestamp_str,
            "git_commit": git_hash,
            "llm_model": model,
            "temperature": 0.0,
            "top_k": 5,
            "chunk_size": 750,
            "chunk_overlap": 100,
            "embedding_model": "BAAI/bge-small-en-v1.5",
        },
        "model": model,
        "evaluation_timestamp": timestamp_str,
        "total_queries": len(results),
        "overall_summary": overall_summary,
        "english_summary": en_summary,
        "vietnamese_summary": vi_summary,
        "detailed_results": results,
    }

    # Save to canonical JSON
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved evaluation JSON report to: {output_json}")

    # Also save to versioned timestamped JSON file for reproducibility
    versioned_json = output_json.parent / f"rag_e2e_results_{date_compact}_git{git_hash}.json"
    with open(versioned_json, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved versioned evaluation JSON report to: {versioned_json}")

    # Save to CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "query_id",
            "language",
            "category",
            "answerable",
            "recall_at_5",
            "hit_at_5",
            "citation_precision",
            "citation_recall",
            "citation_accuracy",
            "faithfulness",
            "rag_correctness",
            "no_rag_correctness",
            "retrieval_latency_ms",
            "generation_latency_ms",
            "total_latency_ms",
            "no_rag_latency_ms",
            "citation_count",
            "question",
            "rag_answer",
            "no_rag_answer",
            "reference_answer",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    logger.info(f"Saved evaluation CSV report to: {output_csv}")

    # Print comprehensive terminal report
    print("\n" + "=" * 80)
    print(" 📊 END-TO-END RAG EVALUATION BENCHMARK RESULTS")
    print("=" * 80)
    print(f" • Model:                     {model}")
    print(f" • Total Queries Evaluated:   {overall_summary['total_evaluated']} (Answerable: {overall_summary['answerable_count']}, Unanswerable: {overall_summary['unanswerable_count']})")
    print("─" * 80)
    print(" 🎯 CORE METRICS:")
    print(f" • Retrieval Recall@5:        {overall_summary['retrieval_recall_at_5'] * 100:.2f}%")
    print(f" • Retrieval Hit Rate@5:      {overall_summary['hit_rate_at_5'] * 100:.2f}%")
    print(f" • Citation Precision:        {overall_summary['citation_precision'] * 100:.2f}%")
    print(f" • Citation Recall:           {overall_summary['citation_recall'] * 100:.2f}%")
    print(f" • Citation Accuracy:         {overall_summary['citation_accuracy'] * 100:.2f}%")
    print(f" • Faithfulness:              {overall_summary['faithfulness'] * 100:.2f}%")
    print("─" * 80)
    print(" ⚔️ RAG VS NO-RAG (ABLATION COMPARISON):")
    print(f" • RAG Answer Correctness:    {overall_summary['rag_correctness'] * 100:.2f}%")
    print(f" • No-RAG Answer Correctness: {overall_summary['no_rag_correctness'] * 100:.2f}%")
    uplift_sign = "+" if overall_summary['rag_uplift'] >= 0 else ""
    print(f" • RAG Quality Uplift:        {uplift_sign}{overall_summary['rag_uplift'] * 100:.2f}%")
    print("─" * 80)
    print(" ⏱️ LATENCY BREAKDOWN (Median / Mean):")
    print(f" • Retrieval Latency:         Median = {overall_summary['retrieval_latency_ms']['median']:.1f} ms | Mean = {overall_summary['retrieval_latency_ms']['mean']:.1f} ms")
    print(f" • LLM Generation Latency:   Median = {overall_summary['generation_latency_ms']['median']:.1f} ms | Mean = {overall_summary['generation_latency_ms']['mean']:.1f} ms")
    print(f" • Total End-to-End Latency:  Median = {overall_summary['total_latency_ms']['median']:.1f} ms | Mean = {overall_summary['total_latency_ms']['mean']:.1f} ms")
    print("─" * 80)
    print(" 🌐 LANGUAGE COMPARISON:")
    print(f"   ► English (n={en_summary['total_evaluated']}):")
    print(f"       Recall@5:              {en_summary['retrieval_recall_at_5'] * 100:.2f}%")
    print(f"       Citation Precision:    {en_summary['citation_precision'] * 100:.2f}%")
    print(f"       Faithfulness:          {en_summary['faithfulness'] * 100:.2f}%")
    print(f"       RAG vs No-RAG:         {en_summary['rag_correctness'] * 100:.2f}% vs {en_summary['no_rag_correctness'] * 100:.2f}% (Uplift: {en_summary['rag_uplift'] * 100:+.2f}%)")
    print(f"       Latency (Median):      {en_summary['total_latency_ms']['median']:.1f} ms")
    print(f"   ► Vietnamese Cross-lingual (n={vi_summary['total_evaluated']}):")
    print(f"       Recall@5:              {vi_summary['retrieval_recall_at_5'] * 100:.2f}%")
    print(f"       Citation Precision:    {vi_summary['citation_precision'] * 100:.2f}%")
    print(f"       Faithfulness:          {vi_summary['faithfulness'] * 100:.2f}%")
    print(f"       RAG vs No-RAG:         {vi_summary['rag_correctness'] * 100:.2f}% vs {vi_summary['no_rag_correctness'] * 100:.2f}% (Uplift: {vi_summary['rag_uplift'] * 100:+.2f}%)")
    print(f"       Latency (Median):      {vi_summary['total_latency_ms']['median']:.1f} ms")
    print("=" * 80 + "\n")

    return final_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline end-to-end")
    parser.add_argument("--sample", type=int, default=None, help="Sample size (default: all)")
    parser.add_argument("--model", type=str, default="gemma2:2b", help="Model name")
    parser.add_argument("--no-norag", action="store_true", help="Skip No-RAG comparison to speed up evaluation")
    args = parser.parse_args()

    run_e2e_benchmark(
        sample_size=args.sample,
        model=args.model,
        include_no_rag=not args.no_norag,
    )
