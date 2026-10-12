"""Calculates AUROC (Area Under ROC Curve) for similarity thresholding
between Answerable (n=50) and Unanswerable (n=30: 10 original + 20 held-out).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
from sklearn.metrics import roc_auc_score
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CORPUS_PATH = ROOT_DIR / "data" / "processed" / "corpus.jsonl"
BENCHMARK_PATH = ROOT_DIR / "data" / "evaluation" / "benchmark_queries.json"
HELD_OUT_PATH = ROOT_DIR / "data" / "evaluation" / "held_out_unanswerable.json"


def main():
    corpus = [json.loads(line)["text"] for line in open(CORPUS_PATH, encoding="utf-8")]
    queries = json.load(open(BENCHMARK_PATH, encoding="utf-8"))
    held_out = json.load(open(HELD_OUT_PATH, encoding="utf-8"))
    all_queries = queries + held_out

    models = [
        ("BAAI/bge-small-en-v1.5", "Represent this sentence for searching relevant passages: ", ""),
        ("intfloat/multilingual-e5-small", "query: ", "passage: "),
    ]

    for model_name, prefix, p_prefix in models:
        logger.info(f"Loading {model_name}...")
        model = SentenceTransformer(model_name)
        passages = [f"{p_prefix}{t}" for t in corpus]
        embs = model.encode(passages, batch_size=128, show_progress_bar=False, normalize_embeddings=True)

        y_true, scores = [], []
        for q in all_queries:
            is_ans = 1 if q["answerable"] else 0
            q_text = f"{prefix}{q['question']}"
            q_emb = model.encode([q_text], normalize_embeddings=True)[0]
            sims = np.dot(embs, q_emb)
            top1_sim = float(np.max(sims))
            y_true.append(is_ans)
            scores.append(top1_sim)

        auc = roc_auc_score(y_true, scores)
        ans_scores = [s for s, y in zip(scores, y_true) if y == 1]
        unans_scores = [s for s, y in zip(scores, y_true) if y == 0]

        print("\n" + "=" * 65)
        print(f"AUROC SEPARATION ANALYSIS: {model_name}")
        print("=" * 65)
        print(f" • AUROC (Separating In-scope vs Out-of-scope): {auc:.4f}")
        print(f" • Answerable (n={len(ans_scores)}) Top-1 Cosine Sim: Mean={np.mean(ans_scores):.4f}, Std={np.std(ans_scores):.4f}, Min={np.min(ans_scores):.4f}, Max={np.max(ans_scores):.4f}")
        print(f" • Unanswerable (n={len(unans_scores)}) Top-1 Cosine Sim: Mean={np.mean(unans_scores):.4f}, Std={np.std(unans_scores):.4f}, Min={np.min(unans_scores):.4f}, Max={np.max(unans_scores):.4f}")
        
        # Check potential thresholds
        thresholds = np.linspace(np.min(unans_scores), np.max(ans_scores), 20)
        best_f1, best_th = 0.0, 0.0
        for th in thresholds:
            pred = [1 if s >= th else 0 for s in scores]
            tp = sum(1 for p, y in zip(pred, y_true) if p == 1 and y == 1)
            fp = sum(1 for p, y in zip(pred, y_true) if p == 1 and y == 0)
            fn = sum(1 for p, y in zip(pred, y_true) if p == 0 and y == 1)
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
            if f1 > best_f1:
                best_f1 = f1
                best_th = th
        print(f" • Optimal Fixed Similarity Threshold: ~{best_th:.4f} (Max Classification F1: {best_f1:.4f})")
        print("=" * 65)


if __name__ == "__main__":
    main()
