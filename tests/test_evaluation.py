"""Unit tests for RAG evaluation metrics and logic."""

from __future__ import annotations

import unittest
from evaluation.evaluate_e2e import (
    tokenize_clean,
    compute_token_f1,
    compute_faithfulness,
    compute_metrics_summary,
)


class TestEvaluationMetrics(unittest.TestCase):
    def test_tokenize_clean(self):
        text = "FastAPI is fast! Let's declare query params: ?skip=0&limit=10"
        tokens = tokenize_clean(text)
        self.assertIn("fastapi", tokens)
        self.assertIn("query", tokens)
        self.assertIn("params", tokens)

    def test_compute_token_f1(self):
        pred = "FastAPI uses Pydantic to validate data and OpenAPI schemas."
        ref = "FastAPI validates incoming data using Pydantic and generates OpenAPI."
        score = compute_token_f1(pred, ref)
        self.assertGreater(score, 0.4)
        self.assertLessEqual(score, 1.0)

        # Disjoint strings should score 0.0
        self.assertEqual(compute_token_f1("apple banana", "car truck"), 0.0)

    def test_faithfulness_answerable(self):
        chunks = [
            {"text": "FastAPI provides dependency injection using Depends function."},
            {"text": "Dependencies can be shared across multiple routes."},
        ]
        answer = "You can use Depends for dependency injection in routes."
        score = compute_faithfulness(answer, chunks, is_unanswerable=False)
        self.assertGreater(score, 0.5)

    def test_faithfulness_unanswerable_refusal(self):
        # Good refusal
        ans_refusal = "The provided documentation does not contain information about Django ORM."
        self.assertEqual(compute_faithfulness(ans_refusal, [], is_unanswerable=True), 1.0)

        # Vietnamese refusal
        ans_refusal_vi = "Tài liệu này không có thông tin về Apache Kafka."
        self.assertEqual(compute_faithfulness(ans_refusal_vi, [], is_unanswerable=True), 1.0)

        # Bad answer (hallucinated content without refusal)
        ans_bad = "Here is how to configure Django ORM models and migrations in settings.py."
        self.assertEqual(compute_faithfulness(ans_bad, [], is_unanswerable=True), 0.0)

    def test_compute_metrics_summary(self):
        sample_results = [
            {
                "query_id": "q1",
                "answerable": True,
                "recall_at_5": 1.0,
                "hit_at_5": 1.0,
                "citation_precision": 1.0,
                "citation_recall": 1.0,
                "citation_accuracy": 1.0,
                "faithfulness": 0.8,
                "rag_correctness": 0.5,
                "no_rag_correctness": 0.2,
                "retrieval_latency_ms": 15.0,
                "generation_latency_ms": 500.0,
                "total_latency_ms": 515.0,
            },
            {
                "query_id": "q2",
                "answerable": False,
                "recall_at_5": None,
                "hit_at_5": None,
                "citation_precision": 1.0,
                "citation_recall": 1.0,
                "citation_accuracy": 1.0,
                "faithfulness": 1.0,
                "rag_correctness": 1.0,
                "no_rag_correctness": 0.0,
                "retrieval_latency_ms": 20.0,
                "generation_latency_ms": 300.0,
                "total_latency_ms": 320.0,
            },
        ]
        summary = compute_metrics_summary(sample_results)
        self.assertEqual(summary["total_evaluated"], 2)
        self.assertEqual(summary["answerable_count"], 1)
        self.assertEqual(summary["unanswerable_count"], 1)
        self.assertEqual(summary["retrieval_recall_at_5"], 1.0)
        self.assertEqual(summary["rag_uplift"], 0.65)


if __name__ == "__main__":
    unittest.main()
