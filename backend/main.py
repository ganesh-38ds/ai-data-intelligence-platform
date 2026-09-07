import os
import json
import subprocess
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import analytics
import docling_parser 
import rag_engine
import synthetic_generator
import evaluation_engine

app = FastAPI(title="AI Data Intelligence & RAG Platform API")

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
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(EVAL_DIR, exist_ok=True)

class QuestionRequest(BaseModel):
    question: str

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

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    allowed_extensions = [".csv", ".xlsx", ".pdf"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV, XLSX, and PDF are supported.")
    
    file_path = os.path.join(RAW_DATA_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    analysis_result = None
    
    # -------------------------------------------------------------
    # 1. SPREADSHEET (CSV / EXCEL) PROCESSING & VECTOR INDEXING
    # -------------------------------------------------------------
    if file_ext in [".csv", ".xlsx"]:
        try:
            df = pd.read_csv(file_path) if file_ext == ".csv" else pd.read_excel(file_path)
            
            # Fast statistical profiling & zero-latency smart insights (< 15ms)
            summary_stats, sample_chart = analytics.get_advanced_analytics(df)
            kpis = analytics.get_dataset_kpis(df)
            agg_chart, chart_title = analytics.get_chart_aggregations(df)
            chart_data = agg_chart if agg_chart else sample_chart
            kpis["chart_title"] = chart_title
            ai_insights = analytics.get_ai_insights(df, summary_stats)
            
            # Prepare rich, multi-dimensional markdown for high-accuracy RAG retrieval
            col_list = df.columns.tolist()
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns.tolist()
            
            # Build dimension breakdowns (e.g. Sales by Category, Sales by Region)
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
            
            spreadsheet_md = f"""# Dataset Profile: {file.filename}
- File Name: {file.filename}
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
            # Save markdown representation
            md_path = os.path.join(PROCESSED_DIR, f"{file.filename}.md")
            with open(md_path, "w", encoding="utf-8") as fp:
                fp.write(spreadsheet_md)
                
            # Index into ChromaDB so user can ask questions about this spreadsheet!
            rag_engine.index_document(spreadsheet_md, file.filename)
            
            analysis_result = {
                "file_type": "spreadsheet", 
                "filename": file.filename,
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
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error profiling spreadsheet: {str(e)}")
            
    # -------------------------------------------------------------
    # 2. PDF DOCUMENT PROCESSING & VECTOR INDEXING
    # -------------------------------------------------------------
    elif file_ext == ".pdf":
        try:
            markdown_content = docling_parser.parse_pdf(file_path, file.filename)
            num_chunks = rag_engine.index_document(markdown_content, file.filename)
            
            analysis_result = {
                "file_type": "pdf",
                "filename": file.filename,
                "preview": f"✅ SUCCESS: PDF parsed and split into {num_chunks} chunks, indexed in ChromaDB!\n\nPreview:\n" + markdown_content[:1000]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")
            
    return {"message": "File processed & indexed successfully!", "analysis": analysis_result}

@app.post("/api/rag/ask")
def ask_rag(request: QuestionRequest):
    try:
        return rag_engine.query_rag(request.question)
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
    fpath = os.path.join(EVAL_DIR, filename)
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
def list_runs():
    try:
        return evaluation_engine.list_evaluation_runs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluation/run/{filename}")
def get_run(filename: str):
    fpath = os.path.join(EVAL_DIR, filename)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========================================
# PHASE 9: AUTOMATED PYTEST SUITE API
# ==========================================
@app.post("/api/tests/run")
def run_pytest_suite():
    """Triggers the automated Pytest test suite across all modules."""
    try:
        venv_python = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")
        backend_dir = os.path.dirname(__file__)
        cmd = [venv_python, "-m", "pytest", "tests/", "-v", "--tb=short"]
        proc = subprocess.run(cmd, cwd=backend_dir, capture_output=True, text=True, timeout=90)
        return {
            "exit_code": proc.returncode,
            "status": "PASSED" if proc.returncode == 0 else "FAILED",
            "output": proc.stdout or proc.stderr
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))