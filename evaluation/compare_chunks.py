"""Chunk Size Ablation Experiment:
Compares chunk_size=400, 750, and 1200 using the exact DocumentChunker pipeline.
Measures total chunks, mean character length, token counts, broken code block rate,
and Retrieval Recall@5 / Hit Rate@5 on 50 answerable benchmark queries.
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

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ingestion.build_corpus import EXCLUDED_FILES
from ingestion.chunker import DocumentChunker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DOCS_DIR = ROOT_DIR / "data" / "raw" / "fastapi_docs"
BENCHMARK_PATH = ROOT_DIR / "data" / "evaluation" / "benchmark_queries.json"
OUTPUT_PATH = ROOT_DIR / "data" / "evaluation" / "chunk_ablation_results.json"


def get_filtered_md_files() -> List[Path]:
    return [
        f for f in sorted(RAW_DOCS_DIR.glob("**/*.md"))
        if not f.name.startswith("_") and f.name not in EXCLUDED_FILES
    ]


def evaluate_chunk_config(
    chunk_size: int,
    chunk_overlap: int,
    embed_model: SentenceTransformer,
    queries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    md_files = get_filtered_md_files()
    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    chunks = []
    for f in md_files:
        chunks.extend(list(chunker.process_file(f, RAW_DOCS_DIR)))

    lengths = [len(c.text) for c in chunks]
    # Check broken code fences (odd count of ```)
    broken_fences = sum(1 for c in chunks if c.text.count("```") % 2 != 0)
    broken_pct = (broken_fences / len(chunks) * 100) if chunks else 0.0

    # Evaluate retrieval on 50 answerable queries
    logger.info(f"Encoding {len(chunks)} chunks for chunk_size={chunk_size}...")
    passages = [c.text for c in chunks]
    embs = embed_model.encode(passages, batch_size=128, show_progress_bar=False, normalize_embeddings=True)

    ans_queries = [q for q in queries if q["answerable"]]
    recalls, hits = [], []
    prefix = "Represent this sentence for searching relevant passages: "

    for q in ans_queries:
        q_emb = embed_model.encode([f"{prefix}{q['question']}"], normalize_embeddings=True)[0]
        sims = np.dot(embs, q_emb)
        top5_idx = np.argsort(sims)[::-1][:5]
        retrieved_sources = set(chunks[i].source for i in top5_idx)
        expected = set(q["relevant_sources"])
        matched = expected.intersection(retrieved_sources)
        recalls.append(len(matched) / len(expected) if expected else 0.0)
        hits.append(1.0 if matched else 0.0)

    return {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "total_chunks": len(chunks),
        "mean_length_chars": round(float(np.mean(lengths)), 1) if lengths else 0,
        "estimated_tokens": round(float(np.mean(lengths)) / 4, 1) if lengths else 0,
        "broken_code_blocks": broken_fences,
        "broken_code_block_rate": round(broken_pct, 2),
        "recall_at_5": round(float(np.mean(recalls)), 4),
        "hit_rate_at_5": round(float(np.mean(hits)), 4),
    }


def main():
    queries = json.load(open(BENCHMARK_PATH, "r", encoding="utf-8"))
    logger.info("Loading BGE-small embedding model for chunk evaluation...")
    embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    configs = [
        (400, 60),
        (750, 100),
        (1200, 150),
    ]

    results = []
    for c_size, c_overlap in configs:
        logger.info(f"Evaluating chunk_size={c_size}, chunk_overlap={c_overlap}...")
        res = evaluate_chunk_config(c_size, c_overlap, embed_model, queries)
        results.append(res)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 90)
    print("VERIFIED CHUNK SIZE ABLATION RESULTS (FastAPI Technical Documentation):")
    print("=" * 90)
    print(f"{'Chunk Size':<12} | {'Chunks':<8} | {'Avg Chars':<10} | {'Tokens':<8} | {'Broken Code %':<14} | {'Recall@5':<10} | {'Hit Rate@5':<10}")
    print("-" * 90)
    for r in results:
        sel_tag = " (Selected)" if r["chunk_size"] == 750 else ""
        print(f"{str(r['chunk_size']) + sel_tag:<12} | {r['total_chunks']:<8} | {r['mean_length_chars']:<10} | ~{r['estimated_tokens']:<7} | {r['broken_code_block_rate']:.2f}%{'':<8} | {r['recall_at_5']*100:.2f}%{'':<3} | {r['hit_rate_at_5']*100:.2f}%")
    print("=" * 90)


if __name__ == "__main__":
    main()
