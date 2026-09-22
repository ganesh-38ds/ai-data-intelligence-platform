import os
import json
import subprocess
import sys
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import analytics
import docling_parser 
import rag_engine
import synthetic_generator
import evaluation_engine

import asyncio
import threading
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up ChromaDB and SentenceTransformers in background thread without blocking server launch."""
    threading.Thread(target=rag_engine.get_collection, daemon=True).start()
    yield

app = FastAPI(title="AI Data Intelligence & RAG Platform API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation")
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(EVAL_DIR, exist_ok=True)

class QuestionRequest(BaseModel):
    question: str
    document_filter: str = None

class GenerateDatasetRequest(BaseModel):
    num_questions: int = 3
    filename: str = None

class RunEvaluationRequest(BaseModel):
    dataset_filename: str = None
    quality_threshold: float = 0.80
    fast_mode: bool = False


@app.get("/")
def read_root():
    return {"message": "AI Data Intelligence & RAG Evaluation Platform API"}

@app.get("/api/status")
def get_status():
    return {"status": "success", "message": "Backend connected successfully!"}

@app.get("/api/health")
def get_health():
    return {"status": "healthy", "service": "FastAPI", "version": "2.0.0"}

def _process_uploaded_file(file_path: str, safe_filename: str, file_ext: str):
    # 1. SPREADSHEET (CSV / EXCEL) PROCESSING & VECTOR INDEXING
    if file_ext in [".csv", ".xlsx"]:
        df = pd.read_csv(file_path) if file_ext == ".csv" else pd.read_excel(file_path)
        
        # Fast statistical profiling & zero-latency smart insights (< 15ms)
        summary_stats, sample_chart = analytics.get_advanced_analytics(df)
        kpis = analytics.get_dataset_kpis(df)
        agg_chart, chart_title = analytics.get_chart_aggregations(df)
        chart_data = agg_chart if agg_chart else sample_chart
        kpis["chart_title"] = chart_title
        ai_insights = analytics.get_ai_insights(df, summary_stats)
        
        col_list = df.columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns.tolist()
        
        breakdowns = []
        if cat_cols and num_cols:
            primary_metric = num_cols[0]
            for cat in cat_cols[:4]:
                try:
                    grp = df.groupby(cat).agg({primary_metric: ['sum', 'mean', 'count']}).round(2)
                    grp.columns = ['Total_' + primary_metric, 'Avg_' + primary_metric, 'Order_Count']
                    grp = grp.sort_values(by='Total_' + primary_metric, ascending=False).head(10)
                    breakdowns.append(f"### Performance Breakdown by {cat} (Top 10):\n{grp.to_markdown()}")
                except Exception:
                    pass
        
        breakdown_text = "\n\n".join(breakdowns) if breakdowns else "No categorical dimensions found."
        
        spreadsheet_md = f"""# Dataset Profile: {safe_filename}
- File Name: {safe_filename}
- Total Rows: {len(df):,}
- Total Columns: {len(df.columns)}
- Column Names: {', '.join(col_list)}
- Missing Values: {int(df.isnull().sum().sum())}
- Duplicate Rows: {int(df.duplicated().sum())}

## Executive Summary & KPIs:
- Primary Metric: {kpis.get('primary_metric')}
- Total Aggregate Sum: {kpis.get('primary_metric_sum'):,}
- Average Value: {kpis.get('primary_metric_avg'):,}

## Categorical Aggregations & Dimensional Totals:
{breakdown_text}

## Summary Statistics:
{df[num_cols].describe().round(2).to_markdown() if num_cols else 'No numeric columns.'}

## Sample Records (First 10 Rows):
{df.head(10).to_markdown()}
"""
        md_path = os.path.join(PROCESSED_DIR, f"{safe_filename}.md")
        with open(md_path, "w", encoding="utf-8") as fp:
            fp.write(spreadsheet_md)
            
        rag_engine.index_document(spreadsheet_md, safe_filename)
        
        return {
            "file_type": "spreadsheet", 
            "filename": safe_filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": col_list,
            "missing_values": int(df.isnull().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "chart_data": chart_data,
            "chart_title": kpis.get("chart_title", "Distribution Preview"),
            "kpis": kpis,
            "ai_insights": ai_insights      
        }
        
    # 2. PDF DOCUMENT PROCESSING & VECTOR INDEXING
    elif file_ext == ".pdf":
        markdown_content = docling_parser.parse_pdf(file_path, safe_filename)
        num_chunks = rag_engine.index_document(markdown_content, safe_filename)
        word_count = len(markdown_content.split())
        
        return {
            "file_type": "pdf",
            "filename": safe_filename,
            "preview": f"✅ SUCCESS: PDF parsed and split into {num_chunks} vector chunks, indexed in ChromaDB!\n\nWord Count: {word_count:,}\n\nPreview:\n" + markdown_content[:1200],
            "chunk_count": num_chunks,
            "word_count": word_count
        }

    # 3. WORD DOCUMENT (.docx, .doc) PROCESSING & VECTOR INDEXING
    elif file_ext in [".docx", ".doc"]:
        markdown_content = docling_parser.parse_docx(file_path, safe_filename)
        num_chunks = rag_engine.index_document(markdown_content, safe_filename)
        word_count = len(markdown_content.split())

        return {
            "file_type": "word",
            "filename": safe_filename,
            "preview": f"✅ SUCCESS: Word Document ({safe_filename}) parsed and split into {num_chunks} vector chunks, indexed in ChromaDB!\n\nWord Count: {word_count:,}\n\nPreview:\n" + markdown_content[:1200],
            "chunk_count": num_chunks,
            "word_count": word_count
        }

    # 4. TEXT & MARKDOWN (.txt, .md) PROCESSING & VECTOR INDEXING
    elif file_ext in [".txt", ".md"]:
        markdown_content = docling_parser.parse_text_file(file_path, safe_filename)
        num_chunks = rag_engine.index_document(markdown_content, safe_filename)
        word_count = len(markdown_content.split())

        return {
            "file_type": "text",
            "filename": safe_filename,
            "preview": f"✅ SUCCESS: Text File ({safe_filename}) parsed and split into {num_chunks} vector chunks, indexed in ChromaDB!\n\nWord Count: {word_count:,}\n\nPreview:\n" + markdown_content[:1200],
            "chunk_count": num_chunks,
            "word_count": word_count
        }
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    allowed_extensions = [".csv", ".xlsx", ".xls", ".pdf", ".docx", ".doc", ".txt", ".md"]
    safe_filename = os.path.basename(file.filename or "")
    file_ext = os.path.splitext(safe_filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, Word (.docx), Spreadsheets (.csv, .xlsx), and Text (.txt) are supported.")
    
    file_path = os.path.join(RAW_DATA_DIR, safe_filename)
    total_bytes = 0
    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)
            if total_bytes > MAX_UPLOAD_BYTES:
                buffer.close()
                os.remove(file_path)
                raise HTTPException(status_code=413, detail="File exceeds the 50 MB upload limit")
            buffer.write(chunk)
        
    try:
        analysis_result = await asyncio.to_thread(_process_uploaded_file, file_path, safe_filename, file_ext)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        
    return {"message": "File processed & indexed successfully!", "analysis": analysis_result}

@app.post("/api/rag/ask")
def ask_rag(request: QuestionRequest):
    try:
        return rag_engine.query_rag(request.question, request.document_filter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
def list_documents():
    """List all indexed documents in ChromaDB with their chunk counts and file types."""
    try:
        return rag_engine.list_indexed_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/content/{filename}")
def get_document_content(filename: str):
    """Returns markdown content for an indexed document so users can explore its full text in Tab 1."""
    safe_filename = os.path.basename(filename)
    base_name = os.path.splitext(safe_filename)[0]
    md_candidates = [
        os.path.join(PROCESSED_DIR, f"{safe_filename}.md"),
        os.path.join(PROCESSED_DIR, f"{base_name}.md"),
        os.path.join(PROCESSED_DIR, safe_filename),
    ]
    for p in md_candidates:
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "filename": safe_filename,
                "content": content,
                "length": len(content),
                "preview": content[:1500]
            }
    raise HTTPException(status_code=404, detail="Document content not found")

@app.delete("/api/documents/{filename}")
def delete_document_endpoint(filename: str):
    """Deletes a document from ChromaDB and removes raw/processed files if present."""
    safe_filename = os.path.basename(filename)
    try:
        rag_engine.delete_document(safe_filename)
        for folder in [RAW_DATA_DIR, PROCESSED_DIR]:
            for p in [os.path.join(folder, safe_filename), os.path.join(folder, f"{safe_filename}.md")]:
                if os.path.isfile(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
        return {"status": "success", "message": f"Document '{safe_filename}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/clear")
def clear_documents_endpoint():
    """Clear all documents from ChromaDB."""
    try:
        rag_engine.clear_all_documents()
        return {"status": "success", "message": "All indexed documents cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/sync")
def sync_documents_endpoint():
    """Force re-synchronize all processed markdown documents from disk into ChromaDB."""
    try:
        total = rag_engine.sync_processed_documents(force=True)
        return {"status": "success", "message": f"Successfully synchronized knowledge base ({total} vector chunks).", "total_chunks": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# PHASE 6: SYNTHETIC DATASET GENERATION APIS
# ==========================================
@app.post("/api/dataset/generate")
def generate_dataset(request: GenerateDatasetRequest):
    try:
        result = synthetic_generator.generate_synthetic_dataset(
            filename=request.filename,
            num_questions=request.num_questions
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dataset/list")
def list_datasets():
    try:
        return synthetic_generator.list_evaluation_datasets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dataset/{filename}")
def get_dataset(filename: str):
    safe_filename = os.path.basename(filename)
    if safe_filename != filename or not (safe_filename.startswith("synthetic_qa_") and safe_filename.endswith(".json")):
        raise HTTPException(status_code=400, detail="Invalid dataset filename")
    fpath = os.path.join(EVAL_DIR, safe_filename)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Dataset not found")
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========================================
# PHASE 7 & 8: RAG EVALUATION ENGINE APIS
# ==========================================
@app.post("/api/evaluation/run")
def run_evaluation(request: RunEvaluationRequest):
    try:
        report = evaluation_engine.evaluate_rag_pipeline(
            dataset_filename=request.dataset_filename,
            quality_threshold=request.quality_threshold,
            fast_mode=request.fast_mode
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/evaluation/runs")
def list_evaluation_runs():
    try:
        return evaluation_engine.list_evaluation_runs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/evaluation/run/{filename}")
def get_evaluation_run(filename: str):
    safe_filename = os.path.basename(filename)
    if safe_filename != filename or not safe_filename.startswith("eval_run_"):
        raise HTTPException(status_code=400, detail="Invalid evaluation run filename")
    path = os.path.join(EVAL_DIR, safe_filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


# ==========================================
# PHASE 9: AUTOMATED PYTEST SUITE API
# ==========================================
@app.post("/api/tests/run")
def run_tests():
    """Triggers the automated Pytest test suite across all modules."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "exit_code": result.returncode,
            "status": "PASSED" if result.returncode == 0 else "FAILED",
            "output": (result.stdout or "") + (result.stderr or ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))