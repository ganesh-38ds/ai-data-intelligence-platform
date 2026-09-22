
---

### 2️⃣ Click `RULES.md` and paste:

```markdown
# Engineering Standards & Governance Rules

## 1. Zero Cross-Document Contamination Rule (CRITICAL)
- When querying a specific dataset, `where={"source": document_filter}` MUST be passed to ChromaDB.
- Unfiltered retrieval across all documents is ONLY allowed when the user explicitly chooses "All Documents".
- Spreadsheets are prioritized over resumes/CVs when queries ask for "dataset", "table", or "data".

## 2. Test Suite Isolation Rule
- Unit tests in `tests/` MUST NEVER persist test files in production databases or directories.
- Any test that calls `index_document()` or `upload_file()` must invoke cleanup teardowns upon completion.

## 3. Offline Model Stability Rule
- In `rag_engine.py`, `HF_HUB_OFFLINE` and `TRANSFORMERS_OFFLINE` must remain set to `"1"`.
- Embedding generation runs 100% locally from downloaded weights without remote HuggingFace network pings.

## 4. Sub-Second Server Startup Rule
- Heavy dependencies (`sentence_transformers`, `chromadb`) must NOT be loaded on the global import path.
- All heavy initializations use lazy proxies (`_LazyCollectionProxy`) or daemon thread warmup.

## 5. Reverse Proxy Consistency Rule
- Frontend API calls must use relative paths (`/api/...`) via `import.meta.env.VITE_API_BASE_URL || ""`.