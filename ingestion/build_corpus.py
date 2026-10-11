"""Pipeline to fetch documents, parse, chunk, and export normalized JSONL corpus."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import List

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ingestion.chunker import DocumentChunker
from ingestion.fetch_docs import fetch_fastapi_docs
from ingestion.schemas import DocumentChunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
OUTPUT_JSONL_PATH = PROCESSED_DATA_DIR / "corpus.jsonl"


EXCLUDED_FILES = {
    "release-notes.md",
    "translations.md",
    "translation-banner.md",
    "newsletter.md",
    "fastapi-people.md",
    "help-fastapi.md",
}


def build_corpus(
    output_path: Path = OUTPUT_JSONL_PATH,
    chunk_size: int = 750,
    chunk_overlap: int = 100,
) -> List[DocumentChunk]:
    """Fetches FastAPI documentation, chunks it, and exports normalized corpus.jsonl."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    docs_root = fetch_fastapi_docs()
    logger.info(f"Scanning documentation files in {docs_root}...")

    md_files = [
        f
        for f in sorted(docs_root.glob("**/*.md"))
        if not f.name.startswith("_") and f.name not in EXCLUDED_FILES
    ]
    logger.info(f"Discovered {len(md_files)} technical documentation files in FastAPI docs.")

    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    all_chunks: List[DocumentChunk] = []

    for file_path in md_files:
        chunks = list(
            chunker.process_file(
                file_path=file_path,
                base_dir=docs_root,
                license_text="MIT License (Sebastián Ramírez)",
                source_prefix="fastapi/docs/en/docs",
            )
        )
        all_chunks.extend(chunks)

    logger.info(f"Generated {len(all_chunks)} normalized chunks from {len(md_files)} files.")

    # Write to JSONL
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

    logger.info(f"Exported corpus to: {output_path}")

    # Summary statistics
    total_chars = sum(len(c.text) for c in all_chunks)
    avg_chars = total_chars / len(all_chunks) if all_chunks else 0
    min_chars = min((len(c.text) for c in all_chunks), default=0)
    max_chars = max((len(c.text) for c in all_chunks), default=0)

    print("\n" + "=" * 60)
    print(" 📊 CORPUS SUMMARY STATISTICS")
    print("=" * 60)
    print(f" • Total source documents: {len(md_files)}")
    print(f" • Total normalized chunks: {len(all_chunks)}")
    print(f" • Average chunk length:   {avg_chars:.1f} characters (~{avg_chars/4:.0f} tokens)")
    print(f" • Min chunk length:       {min_chars} characters")
    print(f" • Max chunk length:       {max_chars} characters")
    print(f" • Output JSONL:           {output_path}")
    print("=" * 60)

    # Print first chunk verification
    if all_chunks:
        first = all_chunks[0]
        print("\n🔎 SAMPLE CHUNK VALIDATION:")
        print(f" • ID:      {first.chunk_id}")
        print(f" • Title:   {first.title}")
        print(f" • Section: {first.section}")
        print(f" • Source:  {first.source}")
        print(f" • URL:     {first.url}")
        print(f" • License: {first.license}")
        print(f" • Excerpt: {first.text[:160]}...\n")

    return all_chunks


if __name__ == "__main__":
    build_corpus()
