"""Integration and unit tests for FastAPI backend endpoints."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api.main import app
import api.main as api_module
from generation.generator import RAGAnswer, SourceCitation


class TestFastAPIBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("service", data)
        self.assertIn("endpoints", data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("chroma_db", data)
        self.assertIn("ollama", data)

    def test_chat_endpoint_structure(self):
        # Create a mock RAGAnswer
        mock_answer = RAGAnswer(
            question="How do I configure Docker for FastAPI?",
            answer="You can build a container image using Dockerfile [S1].",
            model="gemma2:2b",
            all_retrieved_sources=[
                {
                    "chunk_id": "fastapi_deployment_docker_001",
                    "title": "FastAPI in Containers - Docker",
                    "url": "https://fastapi.tiangolo.com/deployment/docker/",
                    "source": "fastapi/docs/en/docs/deployment/docker.md",
                    "score": 0.85,
                    "text": "When deploying FastAPI applications a common approach is to build a Linux container image.",
                }
            ],
            cited_sources=[
                SourceCitation(
                    source_id="S1",
                    index=1,
                    title="FastAPI in Containers - Docker",
                    url="https://fastapi.tiangolo.com/deployment/docker/",
                    source_file="fastapi/docs/en/docs/deployment/docker.md",
                    chunk_id="fastapi_deployment_docker_001",
                    score=0.85,
                    excerpt="When deploying FastAPI applications...",
                )
            ],
            hallucinated_citations=[],
            retrieval_count=1,
            retrieval_latency_ms=18.5,
            generation_latency_ms=850.2,
        )

        mock_pipeline = MagicMock()
        mock_pipeline.answer.return_value = mock_answer

        # Patch global pipeline
        original_pipeline = api_module.rag_pipeline
        api_module.rag_pipeline = mock_pipeline
        try:
            req_payload = {
                "question": "How do I configure Docker for FastAPI?",
                "top_k": 5,
            }
            response = self.client.post("/chat", json=req_payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()

            # Verify schema
            self.assertIn("answer", data)
            self.assertIn("sources", data)
            self.assertIn("retrieval_latency_ms", data)
            self.assertIn("generation_latency_ms", data)
            self.assertIn("retrieved_chunks", data)

            # Verify values
            self.assertEqual(len(data["sources"]), 1)
            self.assertEqual(data["sources"][0]["source_id"], "S1")
            self.assertEqual(data["sources"][0]["title"], "FastAPI in Containers - Docker")
            self.assertEqual(data["retrieval_latency_ms"], 18.5)
            self.assertEqual(data["generation_latency_ms"], 850.2)
        finally:
            api_module.rag_pipeline = original_pipeline

    def test_chat_invalid_request(self):
        # Empty question should fail validation (min_length=2)
        response = self.client.post("/chat", json={"question": ""})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
