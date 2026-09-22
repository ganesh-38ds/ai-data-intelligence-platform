# Product Requirements Document (PRD)
## AI Data Intelligence & RAG Evaluation Platform

- **Product Name:** AI Data Intelligence & RAG Evaluation Platform
- **Version:** 2.0.0
- **Author:** Gudla Ganesh
- **Status:** Complete & Production-Ready

---

## 1. Executive Summary
The **AI Data Intelligence & RAG Evaluation Platform** is an enterprise-grade AI system that enables:
1. Real-time tabular and unstructured document profiling (< 15ms).
2. Grounded, hallucination-free Question-Answering using Retrieval-Augmented Generation (RAG) with strict document scoping.
3. Automated benchmark evaluation (RAGAS-grade) measuring Faithfulness, Answer Relevance, Context Precision, and Context Recall.

---

## 2. Target Personas
- **Data Analysts & BI Leads:** Fast exploratory data analysis, KPI discovery, and interactive charts.
- **AI/ML Engineers:** Ground-truth benchmarking to eliminate LLM hallucinations and audit retrieval accuracy.
- **Decision Makers:** Precise, cited answers grounded strictly in enterprise documents.

---

## 3. Core Functional Requirements
- **Data Ingestion:** Upload CSV, Excel (.xlsx), and PDF files up to 50 MB.
- **Statistical Analytics:** Total rows, columns, null/duplicate counts, distributions, and AI insights.
- **Scoped RAG Engine:** Strict document filtering (`where={"source": doc}`) preventing cross-document pollution.
- **Synthetic QA Benchmark Generator:** Automated generation of 2, 3, or 5 test triples (Question, Ground Truth, Context).
- **RAGAS Evaluation Dashboard:** Dual-mode scoring (heuristic < 1s & LLM Judge) with configurable pass/fail thresholds.
- **Pytest Regression Harness:** 1-click test runner directly from the web interface.

---

## 4. Non-Functional Requirements
- **Low Latency:** Data profiling in under 15 milliseconds; end-to-end RAG answer synthesis in under 1.5 seconds.
- **Zero Hallucination:** Answers strictly anchored to retrieved document citations.
- **Offline ML Embeddings:** ChromaDB vector embeddings run locally with zero network dependency.