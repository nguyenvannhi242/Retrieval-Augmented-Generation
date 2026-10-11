"""Semantic search module for retrieving relevant document chunks from ChromaDB."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import chromadb
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
DEFAULT_CHROMA_DIR = PROCESSED_DATA_DIR / "chroma_db"
COLLECTION_NAME = "fastapi_docs"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"


@dataclass
class SearchResult:
    """Represents a single retrieved passage with metadata and relevance score."""

    rank: int
    score: float
    chunk_id: str
    text: str
    title: str
    section: str
    url: str
    source: str
    license: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "score": round(self.score, 4),
            "chunk_id": self.chunk_id,
            "title": self.title,
            "section": self.section,
            "url": self.url,
            "source": self.source,
            "license": self.license,
            "text": self.text,
        }


class DocumentRetriever:
    """Retriever for querying ChromaDB with BGE embeddings."""

    def __init__(
        self,
        persist_directory: Path = DEFAULT_CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
        model_name: str = EMBEDDING_MODEL_NAME,
        query_instruction: str = "Represent this sentence for searching relevant passages: ",
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.model_name = model_name
        self.query_instruction = query_instruction

        self.model = SentenceTransformer(self.model_name)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_collection(name=self.collection_name)

    def search(
        self,
        query: str,
        top_k: int = 5,
        use_instruction: bool = True,
    ) -> List[SearchResult]:
        """Performs semantic similarity search against the indexed corpus."""
        formatted_query = (
            f"{self.query_instruction}{query}" if use_instruction else query
        )

        query_embedding = self.model.encode(
            formatted_query,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        search_results: List[SearchResult] = []
        if not results["ids"] or not results["ids"][0]:
            return search_results

        ids = results["ids"][0]
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for idx, (cid, doc, meta, dist) in enumerate(zip(ids, documents, metadatas, distances)):
            # Cosine distance to similarity: similarity = 1 - distance
            similarity = 1.0 - float(dist)
            search_results.append(
                SearchResult(
                    rank=idx + 1,
                    score=similarity,
                    chunk_id=cid,
                    text=doc,
                    title=meta.get("title", ""),
                    section=meta.get("section", ""),
                    url=meta.get("url", ""),
                    source=meta.get("source", ""),
                    license=meta.get("license", ""),
                )
            )

        return search_results


def print_search_results(query: str, results: List[SearchResult]) -> None:
    """Pretty prints search results to stdout."""
    print("\n" + "=" * 80)
    print(f" 🔍 QUERY: '{query}'")
    print(f" 🎯 FOUND: {len(results)} relevant passages")
    print("=" * 80)

    for res in results:
        section_display = f" > {res.section}" if res.section else ""
        print(f"\n[#{res.rank}] Score: {res.score:.4f} | {res.title}{section_display}")
        print(f"🔗 URL:     {res.url}")
        print(f"📄 Source:  {res.source}")
        print(f"⚖️  License: {res.license}")
        print("─" * 80)
        # Indented text snippet
        snippet_lines = res.text.strip().splitlines()
        preview = "\n".join(f"    {line}" for line in snippet_lines[:12])
        if len(snippet_lines) > 12:
            preview += "\n    ..."
        print(preview)
        print("─" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query FastAPI Documentation ChromaDB Index")
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default="How to define query parameters in FastAPI?",
        help="Search query (Vietnamese or English)",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=5,
        help="Number of chunks to return (default: 5)",
    )
    args = parser.parse_args()

    retriever = DocumentRetriever()
    hits = retriever.search(query=args.query, top_k=args.top_k)
    print_search_results(args.query, hits)
