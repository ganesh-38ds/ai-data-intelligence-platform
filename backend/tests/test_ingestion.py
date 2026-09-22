import pytest
import os
import sys
import io
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app

client = TestClient(app)

def test_root_and_status_endpoints():
    """Verify core API health check endpoints."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "AI Data Intelligence" in res_root.json()["message"]
    
    res_status = client.get("/api/status")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "success"

def test_csv_upload_and_profiling_endpoint():
    """Verify that uploading a CSV processes rows, columns, and saves structured metadata."""
    csv_content = b"Product,Price,Quantity\nLaptop,1200,5\nMouse,25,20\nKeyboard,75,10\n"
    
    response = client.post(
        "/api/upload",
        files={"file": ("unit_test_data.csv", io.BytesIO(csv_content), "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    analysis = data["analysis"]
    assert analysis["total_rows"] == 3
    assert analysis["total_columns"] == 3
    assert analysis["missing_values"] == 0
    # Clean up test upload files and test chunks immediately so user database is never polluted
    client.delete("/api/documents/unit_test_data.csv")

def test_invalid_file_extension():
    """Verify that unsupported file formats are rejected with 400 Bad Request."""
    invalid_content = b"print('Hello world')"
    response = client.post(
        "/api/upload",
        files={"file": ("malicious_script.py", io.BytesIO(invalid_content), "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_text_file_upload_and_indexing():
    """Verify that uploading a .txt file is parsed, indexed in ChromaDB, and can be queried."""
    txt_content = b"# Candidate CV\nName: Alice Johnson\nRole: Lead Data Scientist\nSkills: Python, Machine Learning, RAG, PyTorch\n"
    response = client.post(
        "/api/upload",
        files={"file": ("candidate_profile.txt", io.BytesIO(txt_content), "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"]["file_type"] == "text"
    assert data["analysis"]["chunk_count"] >= 1
    
    # Verify RAG can answer based on this uploaded text file
    rag_res = client.post(
        "/api/rag/ask",
        json={"question": "What is Alice Johnson's role and skills?", "document_filter": "candidate_profile.txt"}
    )
    assert rag_res.status_code == 200
    ans = rag_res.json()["generated_answer"]
    assert "Alice" in ans or "Data Scientist" in ans or "candidate_profile" in ans
    
    # Cleanup test upload
    client.delete("/api/documents/candidate_profile.txt")

