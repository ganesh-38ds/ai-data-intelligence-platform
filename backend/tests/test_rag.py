import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import rag_engine

def test_rag_document_indexing_and_cleanup():
    """Verify that text is split into chunks and indexed in ChromaDB, then cleaned up."""
    sample_doc = """
    # Introduction to Machine Learning
    Machine learning is a field of artificial intelligence that uses statistical techniques.
    
    ## Supervised Learning
    Supervised learning algorithms build a mathematical model of a set of data that contains inputs and desired outputs.
    
    ## Unsupervised Learning
    Unsupervised learning algorithms take a set of data that contains only inputs, and find structure in the data.
    """
    
    test_doc_name = "test_temp_doc_for_unit_tests.md"
    chunks_count = rag_engine.index_document(sample_doc, test_doc_name)
    assert chunks_count >= 1

    docs = rag_engine.list_indexed_documents()
    assert any(d["source"] == test_doc_name for d in docs)

    # Scoped query test
    result = rag_engine.query_rag("What is Supervised learning?", document_filter=test_doc_name)
    assert "retrieved_chunks" in result
    assert len(result["retrieved_chunks"]) > 0
    assert result["target_document"] == test_doc_name
    assert all(c["source"] == test_doc_name for c in result["retrieved_chunks"])

    # Teardown: delete test document immediately so production DB is not polluted
    deleted = rag_engine.delete_document(test_doc_name)
    assert deleted is True
    post_docs = rag_engine.list_indexed_documents()
    assert not any(d["source"] == test_doc_name for d in post_docs)
