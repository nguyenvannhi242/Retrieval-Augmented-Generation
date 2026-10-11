"""Vector database indexing using SentenceTransformers (bge-small-en-v1.5) and ChromaDB."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from ingestion.schemas import DocumentChunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
DEFAULT_JSONL = PROCESSED_DATA_DIR / "corpus.jsonl"
DEFAULT_CHROMA_DIR = PROCESSED_DATA_DIR / "chroma_db"
COLLECTION_NAME = "fastapi_docs"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"


class VectorIndexer:
    """Manages embedding generation and indexing into ChromaDB."""

    def __init__(
        self,
        persist_directory: Path = DEFAULT_CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
        model_name: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.model_name = model_name

        logger.info(f"Loading embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        logger.info("Embedding model loaded successfully.")

        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def load_corpus(self, jsonl_path: Path = DEFAULT_JSONL) -> List[DocumentChunk]:
        """Loads normalized DocumentChunk items from a JSONL file."""
        if not jsonl_path.exists():
            raise FileNotFoundError(f"Corpus JSONL file not found at: {jsonl_path}")

        chunks: List[DocumentChunk] = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    chunks.append(DocumentChunk(**data))
        return chunks

    def index_corpus(
        self,
        jsonl_path: Path = DEFAULT_JSONL,
        batch_size: int = 128,
        reset_existing: bool = True,
    ) -> int:
        """Indexes all chunks into ChromaDB."""
        chunks = self.load_corpus(jsonl_path)
        logger.info(f"Loaded {len(chunks)} chunks from {jsonl_path}")

        if reset_existing:
            try:
                self.client.delete_collection(self.collection_name)
                logger.info(f"Deleted existing collection '{self.collection_name}'.")
            except Exception:
                pass
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        logger.info(f"Indexing {len(chunks)} chunks in batches of {batch_size}...")

        total_batches = (len(chunks) + batch_size - 1) // batch_size
        indexed_count = 0

        for i in tqdm(range(0, len(chunks), batch_size), total=total_batches, desc="Indexing"):
            batch = chunks[i : i + batch_size]
            ids = [chunk.chunk_id for chunk in batch]
            texts = [chunk.text for chunk in batch]

            # Generate normalized dense embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=len(texts),
                normalize_embeddings=True,
                show_progress_bar=False,
            ).tolist()

            metadatas = [
                {
                    "title": chunk.title,
                    "section": chunk.section or "",
                    "source": chunk.source,
                    "url": chunk.url,
                    "license": chunk.license,
                    "chunk_id": chunk.chunk_id,
                }
                for chunk in batch
            ]

            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            indexed_count += len(batch)

        logger.info(
            f"Indexing complete! Total items in collection '{self.collection_name}': {self.collection.count()}"
        )
        return indexed_count


if __name__ == "__main__":
    indexer = VectorIndexer()
    indexer.index_corpus()
