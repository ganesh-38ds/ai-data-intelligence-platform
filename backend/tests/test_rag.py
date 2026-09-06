import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import rag_engine

def test_rag_document_indexing():
    """Verify that text is split into chunks and indexed in ChromaDB."""
    sample_doc = """
    # Introduction to Machine Learning
    Machine learning is a field of artificial intelligence that uses statistical techniques.
    
    ## Supervised Learning
    Supervised learning algorithms build a mathematical model of a set of data that contains inputs and desired outputs.
    
    ## Unsupervised Learning
    Unsupervised learning algorithms take a set of data that contains only inputs, and find structure in the data.
    """
    
    chunks_count = rag_engine.index_document(sample_doc, "test_ml_guide.md")
    assert chunks_count >= 1

def test_rag_query_retrieval():
    """Verify that querying ChromaDB retrieves the most relevant indexed chunks."""
    result = rag_engine.query_rag("What is Supervised learning?")
    
    assert "question" in result
    assert "retrieved_chunks" in result
    assert "generated_answer" in result
    assert len(result["retrieved_chunks"]) > 0
    assert any("Supervised" in c["text"] or "Learning" in c["text"] for c in result["retrieved_chunks"])
