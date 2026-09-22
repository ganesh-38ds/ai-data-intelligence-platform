# System Architecture & Technical Specifications

## 1. High-Level Architecture Diagram

```text
+-------------------------------------------------------------------------+
|                         Vite + React Frontend (Port 5173)              |
|  [Data Ingestion]   [RAG Pipeline]   [Synthetic QA]   [Evaluation Board]|
+------------------------------------+------------------------------------+
                                     | HTTP REST (Vite Proxy: /api/*)
                                     v
+-------------------------------------------------------------------------+
|                         FastAPI Backend (Port 8000)                     |
|  - main.py (Lifespan, CORS, Upload, Document Endpoints)                 |
|  - analytics.py (Pandas statistical engine & KPI extraction)            |
|  - docling_parser.py (Multi-format: PDF, DOCX, TXT, CSV -> Markdown)    |
|  - rag_engine.py (Lazy ChromaDB, Zero-Failure Local Synthesizer)        |
|  - synthetic_generator.py (Benchmark QA extraction)                    |
|  - evaluation_engine.py (RAGAS 4-metric scoring engine)                |
+-------------------+--------------------------------+--------------------+
                    |                                |
                    v                                v
+-----------------------------------+  +----------------------------------+
|      ChromaDB Vector Store        |  |        Google Gemini API         |
|  - Name: "pdf_documents"          |  |  - Primary: gemini-3.6-flash     |
|  - Model: all-MiniLM-L6-v2        |  |  - Fallback: Local Synthesizer   |
|  - Storage: data/chroma_db/       |  |  - Zero-temperature grounding    |
+-----------------------------------+  +----------------------------------+