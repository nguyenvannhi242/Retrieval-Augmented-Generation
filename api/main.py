"""FastAPI backend application for the RAG Documentation Assistant."""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import ollama
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    RetrievedChunkItem,
    ServiceHealth,
    SourceItem,
)
from generation.generator import DEFAULT_MODEL, RAGPipeline
from retrieval.search import DocumentRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Global singleton pipeline instance
rag_pipeline: Optional[RAGPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize resources once on startup."""
    global rag_pipeline
    logger.info("Initializing RAG Pipeline (DocumentRetriever + Ollama)...")
    try:
        retriever = DocumentRetriever()
        default_model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        rag_pipeline = RAGPipeline(retriever=retriever, model=default_model)
        logger.info(f"RAG Pipeline successfully initialized with model: {default_model}")
    except Exception as e:
        logger.error(f"Failed to initialize RAG Pipeline: {e}", exc_info=True)
        rag_pipeline = None
    yield
    logger.info("Shutting down RAG Pipeline resources.")


app = FastAPI(
    title="FastAPI Documentation RAG API",
    description="Production-grade API providing semantic retrieval and citation-grounded answers for FastAPI documentation.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend clients (e.g., Streamlit, React, Vue)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    """Root entrypoint with API discovery links."""
    return {
        "service": "FastAPI Documentation RAG API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "health": "GET /health",
            "documentation": "GET /docs",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Health check endpoint validating vector database and Ollama LLM readiness."""
    global rag_pipeline

    # 1. Check ChromaDB
    chroma_health = ServiceHealth(status="down")
    if rag_pipeline and rag_pipeline.retriever:
        try:
            count = rag_pipeline.retriever.collection.count()
            chroma_health = ServiceHealth(
                status="healthy",
                details={
                    "collection": rag_pipeline.retriever.collection.name,
                    "chunk_count": count,
                },
            )
        except Exception as e:
            chroma_health = ServiceHealth(status="unhealthy", details={"error": str(e)})

    # 2. Check Ollama
    ollama_health = ServiceHealth(status="down")
    try:
        models_response = ollama.list()
        # Handle both dict-like and object-like responses from ollama-python
        models_list = models_response.get("models", []) if isinstance(models_response, dict) else getattr(models_response, "models", [])
        model_names = [
            m.get("name") if isinstance(m, dict) else getattr(m, "model", str(m))
            for m in models_list
        ]
        target_model = rag_pipeline.model if rag_pipeline else DEFAULT_MODEL
        is_model_present = any(target_model in name for name in model_names)

        ollama_health = ServiceHealth(
            status="healthy" if is_model_present else "warning",
            details={
                "target_model": target_model,
                "model_available": is_model_present,
                "available_models": model_names[:5],
            },
        )
    except Exception as e:
        ollama_health = ServiceHealth(status="unhealthy", details={"error": str(e)})

    overall_status = "healthy"
    if chroma_health.status != "healthy" or ollama_health.status not in ("healthy", "warning"):
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        chroma_db=chroma_health,
        ollama=ollama_health,
        version="1.0.0",
    )


@app.post("/chat", response_model=ChatResponse, tags=["RAG"])
async def chat_endpoint(request: ChatRequest):
    """Answers technical questions using documentation retrieval and Ollama generation."""
    global rag_pipeline
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline is not initialized. Check ChromaDB and embedding models.",
        )

    try:
        rag_answer = rag_pipeline.answer(
            question=request.question,
            top_k=request.top_k,
            model=request.model,
        )

        # Format sources
        sources = [
            SourceItem(
                source_id=cit.source_id,
                title=cit.title,
                url=cit.url,
                source_file=cit.source_file,
                score=cit.score,
            )
            for cit in rag_answer.cited_sources
        ]

        # Format retrieved chunks for optional inspection
        retrieved_chunks = [
            RetrievedChunkItem(
                chunk_id=chunk.get("chunk_id", ""),
                title=chunk.get("title", ""),
                url=chunk.get("url", ""),
                source=chunk.get("source", ""),
                score=round(float(chunk.get("score", 0.0)), 4),
                text=chunk.get("text", ""),
            )
            for chunk in rag_answer.all_retrieved_sources
        ]

        return ChatResponse(
            answer=rag_answer.answer,
            sources=sources,
            retrieved_chunks=retrieved_chunks,
            retrieval_latency_ms=rag_answer.retrieval_latency_ms,
            generation_latency_ms=rag_answer.generation_latency_ms,
            total_latency_ms=round(
                rag_answer.retrieval_latency_ms + rag_answer.generation_latency_ms, 2
            ),
        )

    except Exception as e:
        logger.error(f"Error processing chat query '{request.question}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
