import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import evaluation_engine

QUALITY_THRESHOLD = float(os.getenv("RAG_QUALITY_THRESHOLD", "0.80"))

def test_heuristic_scoring_accuracy():
    """Verify that heuristic fallback accurately scores grounded responses."""
    question = "What is Human Resource Management?"
    expected_answer = "Human Resource Management is the strategic management of people."
    ground_truth_context = "Human Resource Management is the process of managing people in an organization."
    retrieved_chunks = [{"text": ground_truth_context, "source": "test.pdf"}]
    generated_answer = "Human Resource Management is the management of people in an organization."

    scores = evaluation_engine.compute_heuristic_scores(
        question, expected_answer, ground_truth_context, retrieved_chunks, generated_answer
    )

    assert scores["faithfulness"] >= 0.75
    assert scores["answer_relevance"] >= 0.70
    assert scores["context_precision"] >= 0.70
    assert scores["context_recall"] >= 0.75

def test_rag_quality_threshold_evaluation():
    """
    Executes the full evaluation pipeline and enforces that RAG quality
    meets or exceeds the configurable quality threshold (e.g. 0.80).
    """
    report = evaluation_engine.evaluate_rag_pipeline(quality_threshold=QUALITY_THRESHOLD, fast_mode=True)
    
    summary = report["summary_metrics"]
    overall_score = summary["overall_rag_score"]
    faithfulness = summary["faithfulness"]
    relevance = summary["answer_relevance"]
    precision = summary["context_precision"]
    recall = summary["context_recall"]

    # Benchmark Assertions against Quality Thresholds
    assert faithfulness >= QUALITY_THRESHOLD, f"Faithfulness {faithfulness} below threshold {QUALITY_THRESHOLD}"
    assert relevance >= QUALITY_THRESHOLD, f"Answer Relevance {relevance} below threshold {QUALITY_THRESHOLD}"
    assert precision >= (QUALITY_THRESHOLD - 0.10), f"Context Precision {precision} below relaxed threshold"
    assert recall >= QUALITY_THRESHOLD, f"Context Recall {recall} below threshold {QUALITY_THRESHOLD}"
    assert overall_score >= QUALITY_THRESHOLD, f"Overall RAG Score {overall_score} below threshold {QUALITY_THRESHOLD}"
    assert report["system_status"] == "PASSED", "RAG Pipeline evaluation did not achieve PASSED status"
