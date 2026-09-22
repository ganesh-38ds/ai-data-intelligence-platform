# Project Memory & Troubleshooting Runbook

## 1. Critical Solved Issues

### Issue 1: Unscoped Retrieval Crowding Out Target Documents
- **Symptom:** Querying a dataset returned chunks from old CVs or test notes.
- **Solution:** Added `document_filter` in `rag_engine.py` and `main.py` executing `collection.query(where={"source": document_filter})`.

### Issue 2: Hugging Face Remote Network Glitches
- **Symptom:** `httpx.RemoteProtocolError: Server disconnected` during model load.
- **Solution:** Added `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` at top of `rag_engine.py`.

### Issue 3: Windows CP1252 Terminal Emoji Crash
- **Symptom:** `UnicodeEncodeError` when printing files with emojis.
- **Solution:** Purged emoji filenames from disk and sanitized console encoding.

### Issue 4: Pytest Polluting Live ChromaDB
- **Symptom:** `unit_test_data.csv` and `test_ml_guide.md` remained in the search index after tests.
- **Solution:** Added explicit cleanup teardowns in `test_rag.py` and `test_ingestion.py`.

## 2. Operational Cheatsheet
- **Start Platform (1-Click):** Run `.\run.bat`
- **Run Pytest Suite:** `python -m pytest tests/ -v --tb=short`
- **Reset Vector DB:** Click "Clear All" in the RAG tab or run `Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/documents/clear" -Method Post`