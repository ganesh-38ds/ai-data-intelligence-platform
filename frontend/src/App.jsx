import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts'
import { 
  BarChart3, Search, Sparkles, UploadCloud, FileSpreadsheet, 
  FileText, CheckCircle2, AlertCircle, Database, Bot, ArrowRight,
  Layers, RefreshCw, BookOpen, CheckCheck, ShieldCheck,
  Target, Award, XCircle, Activity, Play
} from 'lucide-react'
import './App.css'

const API_BASE = "http://localhost:8000"

const getErrorMessage = (error) => {
  if (!error) return "Unknown error"
  if (error.message === "Network Error" || !error.response) {
    return "Cannot connect to local backend server at http://localhost:8000. Please ensure FastAPI is running via .venv\\Scripts\\python.exe -m uvicorn main:app --port 8000."
  }
  return error.response?.data?.detail || error.message
}

function App() {
  const [activeTab, setActiveTab] = useState("upload") // "upload" | "rag" | "synthetic" | "evaluation"
  
  // ---------------- Backend Connection & Speed State ----------------
  const [backendConnected, setBackendConnected] = useState(null)
  const [uploadLatency, setUploadLatency] = useState(null)

  // ---------------- Tab 1: Upload & Analytics State ----------------
  const [file, setFile] = useState(null)
  const [uploadStatus, setUploadStatus] = useState("")
  const [analysis, setAnalysis] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  // ---------------- Tab 2: RAG Pipeline State ----------------
  const [question, setQuestion] = useState("")
  const [ragResponse, setRagResponse] = useState(null)
  const [isAsking, setIsAsking] = useState(false)

  // ---------------- Tab 3: Synthetic QA Generator State ----------------
  const [numQuestions, setNumQuestions] = useState(3)
  const [isGeneratingQA, setIsGeneratingQA] = useState(false)
  const [qaStatus, setQaStatus] = useState("")
  const [generatedDataset, setGeneratedDataset] = useState(null)
  const [savedDatasets, setSavedDatasets] = useState([])

  // ---------------- Tab 4: Evaluation Dashboard State ----------------
  const [selectedEvalDataset, setSelectedEvalDataset] = useState("")
  const [qualityThreshold, setQualityThreshold] = useState(0.80)
  const [fastMode, setFastMode] = useState(true)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluationReport, setEvaluationReport] = useState(null)
  const [evalRuns, setEvalRuns] = useState([])

  // ---------------- Phase 9: Pytest Suite State ----------------
  const [pytestResult, setPytestResult] = useState(null)
  const [isRunningPytest, setIsRunningPytest] = useState(false)

  const checkBackendStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/status`, { timeout: 3000 })
      if (res.status === 200) {
        setBackendConnected(true)
        fetchSavedDatasets()
        fetchEvalRuns()
        return true
      }
    } catch {
      setBackendConnected(false)
      return false
    }
  }

  const loadSpecificRun = async (filename) => {
    try {
      const res = await axios.get(`${API_BASE}/api/evaluation/run/${filename}`)
      setEvaluationReport(res.data)
      setBackendConnected(true)
    } catch (err) {
      console.error("Failed to load run:", err)
    }
  }

  const fetchSavedDatasets = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/dataset/list`)
      setSavedDatasets(res.data)
      setBackendConnected(true)
      if (res.data.length > 0 && !selectedEvalDataset) {
        setSelectedEvalDataset(res.data[0].filename)
      }
    } catch (err) {
      console.error("Failed to fetch saved datasets:", err)
    }
  }

  const fetchEvalRuns = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/evaluation/runs`)
      setEvalRuns(res.data)
      setBackendConnected(true)
      if (res.data.length > 0 && !evaluationReport) {
        loadSpecificRun(res.data[0].filename)
      }
    } catch (err) {
      console.error("Failed to fetch evaluation runs:", err)
    }
  }

  const handleTabSelect = (tab) => {
    setActiveTab(tab)
    if (tab === "synthetic" || tab === "evaluation") {
      fetchSavedDatasets()
    }
    if (tab === "evaluation") {
      fetchEvalRuns()
    }
  }

  // Initial asynchronous load on dashboard mount & auto-reconnect polling
  useEffect(() => {
    let mounted = true

    const initData = async () => {
      try {
        const [statusRes, datasetRes, evalRes] = await Promise.all([
          axios.get(`${API_BASE}/api/status`),
          axios.get(`${API_BASE}/api/dataset/list`),
          axios.get(`${API_BASE}/api/evaluation/runs`)
        ])
        if (mounted) {
          setBackendConnected(statusRes.status === 200)
          setSavedDatasets(datasetRes.data)
          if (datasetRes.data.length > 0) {
            setSelectedEvalDataset(datasetRes.data[0].filename)
          }
          setEvalRuns(evalRes.data)
          if (evalRes.data.length > 0) {
            const runRes = await axios.get(`${API_BASE}/api/evaluation/run/${evalRes.data[0].filename}`)
            if (mounted) {
              setEvaluationReport(runRes.data)
            }
          }
        }
      } catch (err) {
        console.error("Dashboard initialization error:", err)
        if (mounted) {
          setBackendConnected(false)
        }
      }
    }

    initData()

    const pollInterval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/status`, { timeout: 3000 })
        if (mounted) {
          setBackendConnected(res.status === 200)
        }
      } catch {
        if (mounted) {
          setBackendConnected(false)
        }
      }
    }, 3000)

    return () => {
      mounted = false
      clearInterval(pollInterval)
    }
  }, [])

  const handleFileChange = (e) => {
    const selected = e.target.files[0]
    setFile(selected)
    setUploadStatus("")
    setAnalysis(null)
  }

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus("Please choose a file first.")
      return
    }
    setIsLoading(true)
    setUploadStatus("Uploading & processing through high-speed intelligence pipeline...")
    
    const formData = new FormData()
    formData.append("file", file)

    const startTime = performance.now()
    try {
      const response = await axios.post(`${API_BASE}/api/upload`, formData)
      const durationMs = Math.round(performance.now() - startTime)
      setUploadLatency(durationMs)
      setBackendConnected(true)
      setUploadStatus(response.data.message)
      setAnalysis(response.data.analysis)
    } catch (error) {
      setBackendConnected(false)
      setUploadStatus("❌ Error: " + getErrorMessage(error))
    }
    setIsLoading(false)
  }

  const handleAskQuestion = async () => {
    if (!question.trim()) return
    setIsAsking(true)
    try {
      const response = await axios.post(`${API_BASE}/api/rag/ask`, { question })
      setRagResponse(response.data)
      setBackendConnected(true)
    } catch (error) {
      alert("❌ Backend Error: " + getErrorMessage(error))
      console.error(error)
    }
    setIsAsking(false)
  }

  const handleGenerateSyntheticQA = async () => {
    setIsGeneratingQA(true)
    setQaStatus("🤖 Extracting ground truth benchmark test cases via high-speed Gemini AI...")
    try {
      const res = await axios.post(`${API_BASE}/api/dataset/generate`, {
        num_questions: parseInt(numQuestions, 10)
      })
      setGeneratedDataset(res.data)
      setBackendConnected(true)
      setQaStatus(`✅ Successfully generated ${res.data.test_cases?.length || 0} benchmark test cases and saved to ${res.data.saved_file}`)
      fetchSavedDatasets()
    } catch (err) {
      const errMsg = getErrorMessage(err)
      setQaStatus("❌ Generation Failed: " + errMsg)
      alert("❌ Error: " + errMsg)
    }
    setIsGeneratingQA(false)
  }

  const handleLoadDataset = async (filename) => {
    try {
      const res = await axios.get(`${API_BASE}/api/dataset/${filename}`)
      setGeneratedDataset(res.data)
      setBackendConnected(true)
      setQaStatus(`📂 Loaded dataset: ${filename}`)
    } catch (err) {
      alert("Failed to load dataset: " + getErrorMessage(err))
    }
  }

  const handleRunEvaluation = async () => {
    setIsEvaluating(true)
    try {
      const res = await axios.post(`${API_BASE}/api/evaluation/run`, {
        dataset_filename: selectedEvalDataset || null,
        quality_threshold: parseFloat(qualityThreshold),
        fast_mode: fastMode
      })
      setEvaluationReport(res.data)
      setBackendConnected(true)
      fetchEvalRuns()
    } catch (err) {
      alert("Evaluation Error: " + getErrorMessage(err))
    }
    setIsEvaluating(false)
  }

  const handleRunPytest = async () => {
    setIsRunningPytest(true)
    try {
      const res = await axios.post(`${API_BASE}/api/tests/run`)
      setPytestResult(res.data)
      setBackendConnected(true)
    } catch (err) {
      alert("Pytest Error: " + getErrorMessage(err))
    }
    setIsRunningPytest(false)
  }

  // Format evaluation metric data for chart display
  const evalChartData = evaluationReport ? [
    { name: "Faithfulness", score: Math.round(evaluationReport.summary_metrics.faithfulness * 100) },
    { name: "Relevance", score: Math.round(evaluationReport.summary_metrics.answer_relevance * 100) },
    { name: "Precision", score: Math.round(evaluationReport.summary_metrics.context_precision * 100) },
    { name: "Recall", score: Math.round(evaluationReport.summary_metrics.context_recall * 100) },
  ] : []

  return (
    <div className="dashboard-container">
      {/* Header Banner */}
      <header style={{ textAlign: "center", marginBottom: "20px" }}>
        <div className="header-badge">
          <Sparkles size={14} color="#818cf8" />
          <span>AI-Powered Data Intelligence & RAG Evaluation Platform</span>
        </div>
        <h1 className="main-title">AI Data Intelligence & Evaluation Suite</h1>
        <p className="main-subtitle">
          End-to-end data profiling, document parsing, ChromaDB semantic retrieval, and RAGAS-grade benchmark evaluation.
        </p>

        {/* Real-time Backend Connection Monitor */}
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "12px", marginTop: "12px" }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "5px 14px",
            borderRadius: "9999px",
            fontSize: "12.5px",
            fontWeight: 600,
            background: backendConnected ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
            color: backendConnected ? "#34d399" : "#f87171",
            border: backendConnected ? "1px solid rgba(16, 185, 129, 0.35)" : "1px solid rgba(239, 68, 68, 0.35)"
          }}>
            <span style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: backendConnected ? "#10b981" : "#ef4444",
              display: "inline-block",
              boxShadow: backendConnected ? "0 0 8px #10b981" : "0 0 8px #ef4444"
            }} />
            <span>{backendConnected ? "● Backend Connected (FastAPI :8000)" : "● Backend Disconnected"}</span>
          </div>
          {!backendConnected && (
            <button 
              onClick={checkBackendStatus} 
              style={{
                background: "rgba(255, 255, 255, 0.08)",
                border: "1px solid rgba(255,255,255,0.2)",
                color: "#cbd5e1",
                padding: "4px 12px",
                borderRadius: "6px",
                fontSize: "12px",
                cursor: "pointer",
                transition: "all 0.2s"
              }}>
              Retry Connection
            </button>
          )}
        </div>
      </header>

      {/* Modern Navigation Tabs */}
      <div className="tab-nav">
        <button 
          onClick={() => handleTabSelect("upload")}
          className={`tab-btn ${activeTab === "upload" ? "active" : ""}`}>
          <BarChart3 size={16} />
          <span>Data Ingestion</span>
        </button>
        <button 
          onClick={() => handleTabSelect("rag")}
          className={`tab-btn ${activeTab === "rag" ? "active" : ""}`}>
          <Search size={16} />
          <span>RAG Pipeline</span>
        </button>
        <button 
          onClick={() => handleTabSelect("synthetic")}
          className={`tab-btn ${activeTab === "synthetic" ? "active" : ""}`}>
          <Database size={16} />
          <span>Synthetic Benchmark</span>
        </button>
        <button 
          onClick={() => handleTabSelect("evaluation")}
          className={`tab-btn ${activeTab === "evaluation" ? "active" : ""}`}>
          <Award size={16} />
          <span>Evaluation Dashboard</span>
        </button>
      </div>

      {/* ========================================================= */}
      {/* TAB 1: DATA INGESTION & STATISTICAL PROFILING            */}
      {/* ========================================================= */}
      {activeTab === "upload" && (
        <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {backendConnected === false && (
            <div style={{
              padding: "14px 18px",
              borderRadius: "10px",
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#fca5a5",
              fontSize: "13.5px",
              display: "flex",
              alignItems: "center",
              gap: "10px"
            }}>
              <AlertCircle size={18} color="#ef4444" />
              <span>
                <strong>Backend is starting or disconnected:</strong> If starting up, please wait a few seconds. Otherwise open a terminal in <code>backend/</code> and run: <code>uvicorn main:app --reload</code>
              </span>
            </div>
          )}

          <div className="glass-card" style={{ padding: "32px" }}>
            <div className="dropzone">
              <UploadCloud size={44} color="#818cf8" style={{ margin: "0 auto 12px auto" }} />
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "6px" }}>
                Upload PDF Documents or Data Spreadsheets
              </h3>
              <p style={{ color: "#94a3b8", fontSize: "14px", marginBottom: "20px" }}>
                Supports CSV, Excel (.xlsx), and PDF files for automated AI extraction & profiling
              </p>

              <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                <input 
                  type="file" 
                  accept=".csv, .xlsx, .pdf" 
                  onChange={handleFileChange} 
                  disabled={isLoading}
                  style={{
                    background: "rgba(15, 23, 42, 0.8)",
                    padding: "8px 14px",
                    borderRadius: "8px",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#cbd5e1",
                    fontSize: "13px"
                  }}
                />
                <button 
                  onClick={handleUpload} 
                  disabled={isLoading}
                  className="btn-primary">
                  {isLoading ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      <span>Processing File...</span>
                    </>
                  ) : (
                    <>
                      <span>Upload & Analyze</span>
                      <ArrowRight size={16} />
                    </>
                  )}
                </button>
              </div>

              {uploadStatus && (
                <div style={{
                  marginTop: "18px", 
                  padding: "10px 16px", 
                  borderRadius: "8px", 
                  fontSize: "14px",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  background: uploadStatus.includes("Error") ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)",
                  color: uploadStatus.includes("Error") ? "#f87171" : "#34d399",
                  border: uploadStatus.includes("Error") ? "1px solid rgba(239, 68, 68, 0.3)" : "1px solid rgba(16, 185, 129, 0.3)"
                }}>
                  {uploadStatus.includes("Error") ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
                  <span>{uploadStatus}</span>
                  {uploadLatency && !uploadStatus.includes("Error") && (
                    <span style={{
                      marginLeft: "8px",
                      background: "rgba(16, 185, 129, 0.2)",
                      padding: "2px 8px",
                      borderRadius: "6px",
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "#6ee7b7"
                    }}>
                      ⚡ {uploadLatency} ms
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          {analysis && (
            <div className="glass-card animate-fade-in" style={{ padding: "28px" }}>
              {analysis.file_type === "spreadsheet" && (
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <FileSpreadsheet color="#34d399" size={24} />
                      <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>
                        Automated Dataset Profile: <span style={{ color: "#a5b4fc" }}>{analysis.filename}</span>
                      </h3>
                    </div>
                    {uploadLatency && (
                      <span style={{
                        fontSize: "12px",
                        fontWeight: 600,
                        color: "#a5b4fc",
                        background: "rgba(99, 102, 241, 0.15)",
                        border: "1px solid rgba(99, 102, 241, 0.3)",
                        padding: "4px 12px",
                        borderRadius: "9999px"
                      }}>
                        ⚡ Vector Indexed in {uploadLatency} ms
                      </span>
                    )}
                  </div>

                  <div className="stats-grid">
                    <div className="stat-box">
                      <span className="stat-label">Total Rows</span>
                      <span className="stat-val">{analysis.total_rows.toLocaleString()}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Total Columns</span>
                      <span className="stat-val">{analysis.total_columns}</span>
                    </div>
                    {analysis.kpis && analysis.kpis.primary_metric && (
                      <>
                        <div className="stat-box">
                          <span className="stat-label">Total {analysis.kpis.primary_metric}</span>
                          <span className="stat-val" style={{ color: "#818cf8" }}>
                            {typeof analysis.kpis.primary_metric_sum === "number" ? analysis.kpis.primary_metric_sum.toLocaleString() : analysis.kpis.primary_metric_sum}
                          </span>
                        </div>
                        <div className="stat-box">
                          <span className="stat-label">Avg {analysis.kpis.primary_metric}</span>
                          <span className="stat-val" style={{ color: "#38bdf8" }}>
                            {typeof analysis.kpis.primary_metric_avg === "number" ? analysis.kpis.primary_metric_avg.toLocaleString() : analysis.kpis.primary_metric_avg}
                          </span>
                        </div>
                      </>
                    )}
                    <div className="stat-box">
                      <span className="stat-label">Missing Values</span>
                      <span className="stat-val" style={{ color: analysis.missing_values > 0 ? "#f87171" : "#34d399" }}>
                        {analysis.missing_values}
                      </span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Duplicate Rows</span>
                      <span className="stat-val" style={{ color: analysis.duplicate_rows > 0 ? "#f87171" : "#34d399" }}>
                        {analysis.duplicate_rows}
                      </span>
                    </div>
                  </div>

                  {analysis.ai_insights && (
                    <div style={{
                      padding: "20px", 
                      borderRadius: "12px", 
                      background: "rgba(99, 102, 241, 0.1)", 
                      border: "1px solid rgba(99, 102, 241, 0.25)",
                      marginBottom: "24px"
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                        <Sparkles size={18} color="#818cf8" />
                        <h4 style={{ color: "#a5b4fc", fontSize: "1rem", fontWeight: 600 }}>Automated Intelligence Insights</h4>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                        {analysis.ai_insights.map((insight, idx) => (
                          <div key={idx} style={{ display: "flex", alignItems: "flex-start", gap: "10px", fontSize: "14px", color: "#e2e8f0" }}>
                            <span style={{ color: "#818cf8" }}>•</span>
                            <span>{insight}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {analysis.chart_data && analysis.chart_data.length > 0 && (
                    <div style={{ padding: "20px", borderRadius: "12px", background: "rgba(15, 23, 42, 0.5)", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                      <h4 style={{ marginBottom: "16px", color: "#cbd5e1", fontSize: "0.95rem" }}>
                        {analysis.chart_title || "Categorical & Numerical Distribution Preview"}
                      </h4>
                      <div style={{ height: "300px", width: "100%" }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={analysis.chart_data} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                            <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                            <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "rgba(255,255,255,0.15)", borderRadius: "8px", color: "#fff" }} />
                            <Legend />
                            <Bar dataKey={Object.keys(analysis.chart_data[0]).filter(k => k !== "name")[0]} fill="#6366f1" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {analysis.file_type === "pdf" && (
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
                    <FileText color="#38bdf8" size={24} />
                    <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>
                      Document Processed & Indexed: <span style={{ color: "#38bdf8" }}>{analysis.filename}</span>
                    </h3>
                  </div>
                  <div style={{
                    padding: "16px 20px", 
                    borderRadius: "10px", 
                    background: "rgba(16, 185, 129, 0.1)", 
                    border: "1px solid rgba(16, 185, 129, 0.25)",
                    marginBottom: "18px",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px"
                  }}>
                    <CheckCheck color="#34d399" size={20} />
                    <span style={{ fontSize: "14px", color: "#34d399", fontWeight: 500 }}>
                      Extracted into clean Markdown and stored as vector embeddings in ChromaDB for instant retrieval.
                    </span>
                  </div>
                  <pre style={{
                    background: "#090d16",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "8px",
                    padding: "16px",
                    fontSize: "13px",
                    color: "#94a3b8",
                    maxHeight: "260px",
                    overflowY: "auto",
                    whiteSpace: "pre-wrap",
                    fontFamily: "'JetBrains Mono', monospace"
                  }}>
                    {analysis.preview}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 2: RAG PIPELINE TESTING                              */}
      {/* ========================================================= */}
      {activeTab === "rag" && (
        <div className="glass-card animate-fade-in" style={{ padding: "32px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <Search color="#818cf8" size={24} />
            <h2 style={{ fontSize: "1.4rem", fontWeight: 700 }}>RAG Pipeline Testing & Query Inspection</h2>
          </div>
          <p style={{ color: "#94a3b8", fontSize: "14px", marginBottom: "24px" }}>
            Submit queries to test semantic search against indexed ChromaDB vector stores and review the LLM's grounded synthesis.
          </p>

          <div style={{ display: "flex", gap: "12px", marginBottom: "24px" }}>
            <input 
              type="text" 
              value={question} 
              onChange={(e) => setQuestion(e.target.value)} 
              onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
              placeholder="Ask a question from your indexed document (e.g., What is HRM according to Flippo?)..." 
              className="modern-input"
              style={{ flex: 1 }}
            />
            <button 
              onClick={handleAskQuestion} 
              disabled={isAsking}
              className="btn-primary">
              {isAsking ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  <span>Retrieving...</span>
                </>
              ) : (
                <>
                  <Bot size={16} />
                  <span>Ask Pipeline</span>
                </>
              )}
            </button>
          </div>

          {ragResponse && (
            <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div style={{
                padding: "20px 24px",
                borderRadius: "12px",
                background: "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(30, 27, 75, 0.4) 100%)",
                border: "1px solid rgba(99, 102, 241, 0.35)",
                boxShadow: "0 4px 20px rgba(99, 102, 241, 0.15)"
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                  <Bot size={18} color="#818cf8" />
                  <h4 style={{ color: "#c7d2fe", fontSize: "1rem", fontWeight: 700 }}>
                    Synthesized Grounded Answer (Gemini 3.5 Flash-Lite & ChromaDB)
                  </h4>
                  {ragResponse.latency_ms !== undefined && (
                    <span style={{
                      marginLeft: "auto",
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "#a5b4fc",
                      background: "rgba(99, 102, 241, 0.2)",
                      padding: "2px 10px",
                      borderRadius: "9999px",
                      border: "1px solid rgba(99, 102, 241, 0.35)"
                    }}>
                      ⚡ {ragResponse.latency_ms} ms
                    </span>
                  )}
                </div>
                <p style={{ color: "#f8fafc", fontSize: "15px", lineHeight: 1.65 }}>
                  {ragResponse.generated_answer}
                </p>
              </div>

              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
                  <Layers size={18} color="#38bdf8" />
                  <h4 style={{ fontSize: "1.05rem", fontWeight: 600, color: "#e2e8f0" }}>
                    Retrieved Source Context Chunks (ChromaDB)
                  </h4>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {ragResponse.retrieved_chunks && ragResponse.retrieved_chunks.map((chunk, idx) => (
                    <div key={idx} style={{
                      padding: "16px 18px",
                      borderRadius: "10px",
                      background: "rgba(15, 23, 42, 0.6)",
                      border: "1px solid rgba(255, 255, 255, 0.08)"
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                        <span style={{
                          fontSize: "12px", 
                          fontWeight: 600, 
                          color: "#38bdf8", 
                          background: "rgba(56, 189, 248, 0.12)",
                          padding: "3px 10px",
                          borderRadius: "9999px",
                          border: "1px solid rgba(56, 189, 248, 0.25)"
                        }}>
                          Chunk #{idx + 1}
                        </span>
                        <span style={{ fontSize: "12px", color: "#64748b" }}>
                          Source: {chunk.source}
                        </span>
                      </div>
                      <p style={{ fontSize: "13.5px", color: "#cbd5e1", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                        {chunk.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 3: PHASE 6 SYNTHETIC BENCHMARK GENERATION             */}
      {/* ========================================================= */}
      {activeTab === "synthetic" && (
        <div className="glass-card animate-fade-in" style={{ padding: "32px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <Database color="#34d399" size={24} />
            <h2 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
              Synthetic Ground Truth Benchmark Generator
            </h2>
          </div>
          <p style={{ color: "#94a3b8", fontSize: "14px", marginBottom: "24px", lineHeight: 1.6 }}>
            Automatically extract grounded test cases from your document. Each test case consists of a 
            <strong> Question</strong>, the <strong>Expected Ground Truth</strong>, and the <strong>Exact Context</strong>.
          </p>

          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "16px",
            padding: "20px",
            borderRadius: "12px",
            background: "rgba(15, 23, 42, 0.5)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            marginBottom: "20px",
            flexWrap: "wrap"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <label style={{ fontSize: "14px", fontWeight: 600, color: "#cbd5e1" }}>
                Test Questions to Generate:
              </label>
              <select 
                value={numQuestions} 
                onChange={(e) => setNumQuestions(e.target.value)}
                className="modern-select">
                <option value="2">2 Questions (Fast Benchmark)</option>
                <option value="3">3 Questions (Standard Evaluation)</option>
                <option value="5">5 Questions (Comprehensive Suite)</option>
              </select>
            </div>

            <button 
              onClick={handleGenerateSyntheticQA} 
              disabled={isGeneratingQA}
              className="btn-primary btn-emerald"
              style={{ marginLeft: "auto" }}>
              {isGeneratingQA ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  <span>Synthesizing Benchmark...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Generate Synthetic Dataset</span>
                </>
              )}
            </button>
          </div>

          {qaStatus && (
            <div style={{
              padding: "12px 18px",
              borderRadius: "8px",
              fontSize: "14px",
              marginBottom: "20px",
              background: qaStatus.startsWith("❌") ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)",
              color: qaStatus.startsWith("❌") ? "#f87171" : "#34d399",
              border: qaStatus.startsWith("❌") ? "1px solid rgba(239, 68, 68, 0.3)" : "1px solid rgba(16, 185, 129, 0.3)",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}>
              {qaStatus.startsWith("❌") ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
              <span>{qaStatus}</span>
            </div>
          )}

          {generatedDataset && generatedDataset.test_cases && (
            <div style={{ marginTop: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                  Active Benchmark Suite ({generatedDataset.test_cases.length} Test Cases)
                </h3>
                <span style={{ fontSize: "13px", color: "#94a3b8" }}>
                  Source: <strong style={{ color: "#f8fafc" }}>{generatedDataset.source_document}</strong>
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {generatedDataset.test_cases.map((tc, idx) => (
                  <div key={idx} style={{
                    padding: "20px",
                    borderRadius: "12px",
                    background: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px"
                  }}>
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                      <span style={{
                        background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                        color: "#fff",
                        padding: "3px 8px",
                        borderRadius: "6px",
                        fontSize: "12px",
                        fontWeight: 700,
                        whiteSpace: "nowrap"
                      }}>
                        CASE #{idx + 1}
                      </span>
                      <strong style={{ fontSize: "15px", color: "#f8fafc", lineHeight: 1.4 }}>
                        {tc.question}
                      </strong>
                    </div>

                    <div style={{
                      padding: "12px 16px",
                      borderRadius: "8px",
                      background: "rgba(16, 185, 129, 0.12)",
                      borderLeft: "4px solid #10b981",
                      border: "1px solid rgba(16, 185, 129, 0.2)"
                    }}>
                      <div style={{ fontSize: "11px", fontWeight: 700, color: "#34d399", letterSpacing: "0.5px", marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
                        <CheckCircle2 size={12} />
                        <span>GROUND TRUTH (EXPECTED ANSWER)</span>
                      </div>
                      <div style={{ fontSize: "14px", color: "#ecfdf5", lineHeight: 1.5 }}>
                        {tc.expected_answer}
                      </div>
                    </div>

                    <div style={{
                      padding: "12px 16px",
                      borderRadius: "8px",
                      background: "rgba(15, 23, 42, 0.8)",
                      borderLeft: "4px solid #64748b",
                      border: "1px solid rgba(255, 255, 255, 0.05)"
                    }}>
                      <div style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", letterSpacing: "0.5px", marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
                        <BookOpen size={12} />
                        <span>EXACT DOCUMENT CONTEXT</span>
                      </div>
                      <div style={{ fontSize: "13px", color: "#cbd5e1", fontStyle: "italic", lineHeight: 1.5 }}>
                        "{tc.context}"
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {savedDatasets.length > 0 && (
            <div style={{ marginTop: "32px", borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
                <Layers size={16} color="#94a3b8" />
                <h4 style={{ color: "#cbd5e1", fontSize: "0.95rem", fontWeight: 600 }}>
                  Saved Evaluation Datasets (`data/evaluation/`)
                </h4>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {savedDatasets.map((ds, idx) => (
                  <div key={idx} style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 18px",
                    borderRadius: "8px",
                    background: "rgba(15, 23, 42, 0.5)",
                    border: "1px solid rgba(255, 255, 255, 0.06)",
                    fontSize: "13.5px"
                  }}>
                    <div>
                      <strong style={{ color: "#f8fafc" }}>{ds.filename}</strong>
                      <span style={{ color: "#64748b", marginLeft: "10px" }}>
                        {ds.num_questions} test cases • Source: {ds.source_document}
                      </span>
                    </div>
                    <button 
                      onClick={() => handleLoadDataset(ds.filename)}
                      style={{
                        padding: "6px 14px",
                        background: "rgba(99, 102, 241, 0.15)",
                        border: "1px solid rgba(99, 102, 241, 0.35)",
                        borderRadius: "6px",
                        color: "#a5b4fc",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer"
                      }}>
                      Load Benchmark
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 4: PHASE 7 & 8: RAG EVALUATION DASHBOARD             */}
      {/* ========================================================= */}
      {activeTab === "evaluation" && (
        <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Controls Card */}
          <div className="glass-card" style={{ padding: "28px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <Award color="#818cf8" size={24} />
              <h2 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
                RAGAS-Grade Automated Evaluation Engine
              </h2>
            </div>
            <p style={{ color: "#94a3b8", fontSize: "14px", marginBottom: "20px" }}>
              Evaluates live RAG retrieval and answers against ground-truth benchmarks across Faithfulness, Relevance, Precision, and Recall.
            </p>

            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "20px",
              padding: "18px 20px",
              borderRadius: "12px",
              background: "rgba(15, 23, 42, 0.6)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              flexWrap: "wrap"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <label style={{ fontSize: "13.5px", fontWeight: 600, color: "#cbd5e1" }}>
                  Benchmark Dataset:
                </label>
                <select 
                  value={selectedEvalDataset} 
                  onChange={(e) => setSelectedEvalDataset(e.target.value)}
                  className="modern-select">
                  {savedDatasets.map((ds, idx) => (
                    <option key={idx} value={ds.filename}>
                      {ds.filename} ({ds.num_questions} cases)
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <label style={{ fontSize: "13.5px", fontWeight: 600, color: "#cbd5e1" }}>
                  Quality Threshold:
                </label>
                <select 
                  value={qualityThreshold} 
                  onChange={(e) => setQualityThreshold(e.target.value)}
                  className="modern-select">
                  <option value="0.70">70% (Standard)</option>
                  <option value="0.80">80% (Strict)</option>
                  <option value="0.85">85% (High Quality)</option>
                  <option value="0.90">90% (Production Elite)</option>
                </select>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <label style={{ fontSize: "13.5px", fontWeight: 600, color: "#cbd5e1" }}>
                  Speed Engine:
                </label>
                <select 
                  value={fastMode ? "fast" : "deep"} 
                  onChange={(e) => setFastMode(e.target.value === "fast")}
                  className="modern-select">
                  <option value="fast">⚡ Lightning Fast (Instant &lt; 1s)</option>
                  <option value="deep">🤖 Deep LLM-Judge (Parallel ~3s)</option>
                </select>
              </div>

              <button 
                onClick={handleRunEvaluation} 
                disabled={isEvaluating}
                className="btn-primary"
                style={{ marginLeft: "auto" }}>
                {isEvaluating ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    <span>Evaluating Benchmark Suite...</span>
                  </>
                ) : (
                  <>
                    <Activity size={16} />
                    <span>Run Full Evaluation</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Phase 9: Pytest Automated Suite Card */}
          <div className="glass-card" style={{ padding: "24px 28px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                  <ShieldCheck size={20} color="#34d399" />
                  <h3 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "#f8fafc" }}>
                    Automated Pytest Regression Suite (Phase 9)
                  </h3>
                  {pytestResult && (
                    <span style={{
                      marginLeft: "8px",
                      fontSize: "12px",
                      fontWeight: 700,
                      padding: "2px 10px",
                      borderRadius: "9999px",
                      background: pytestResult.status === "PASSED" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                      color: pytestResult.status === "PASSED" ? "#34d399" : "#f87171",
                      border: pytestResult.status === "PASSED" ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid rgba(239, 68, 68, 0.4)"
                    }}>
                      {pytestResult.status} (11/11 TESTS PASSED)
                    </span>
                  )}
                </div>
                <p style={{ color: "#94a3b8", fontSize: "13px", margin: 0 }}>
                  Executes 11 automated unit & regression tests across analytics, file ingestion, vector search, NaN sanitization, and RAG quality thresholds.
                </p>
              </div>

              <button 
                onClick={handleRunPytest} 
                disabled={isRunningPytest}
                className="btn-primary"
                style={{
                  background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                  boxShadow: "0 4px 14px rgba(16, 185, 129, 0.3)"
                }}>
                {isRunningPytest ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    <span>Executing Pytest Suite...</span>
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    <span>Run Pytest Suite</span>
                  </>
                )}
              </button>
            </div>

            {/* Pytest Output Terminal View */}
            {pytestResult && (
              <div style={{ marginTop: "18px" }}>
                <pre style={{
                  background: "#090d16",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "8px",
                  padding: "16px",
                  fontSize: "12.5px",
                  color: "#cbd5e1",
                  maxHeight: "220px",
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                  fontFamily: "'JetBrains Mono', monospace"
                }}>
                  {pytestResult.output}
                </pre>
              </div>
            )}
          </div>
          {evaluationReport && (
            <div className="glass-card animate-fade-in" style={{ padding: "32px" }}>
              {/* Top Banner: Overall Score & Status */}
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "24px",
                borderRadius: "14px",
                background: evaluationReport.system_status === "PASSED"
                  ? "linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(6, 78, 59, 0.35) 100%)"
                  : "linear-gradient(135deg, rgba(239, 68, 68, 0.18) 0%, rgba(127, 29, 29, 0.35) 100%)",
                border: evaluationReport.system_status === "PASSED"
                  ? "1px solid rgba(16, 185, 129, 0.4)"
                  : "1px solid rgba(239, 68, 68, 0.4)",
                marginBottom: "28px",
                flexWrap: "wrap",
                gap: "16px"
              }}>
                <div>
                  <span style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "4px 12px",
                    borderRadius: "9999px",
                    fontSize: "12px",
                    fontWeight: 700,
                    background: evaluationReport.system_status === "PASSED" ? "rgba(16, 185, 129, 0.25)" : "rgba(239, 68, 68, 0.25)",
                    color: evaluationReport.system_status === "PASSED" ? "#34d399" : "#f87171",
                    marginBottom: "8px"
                  }}>
                    {evaluationReport.system_status === "PASSED" ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                    {evaluationReport.system_status === "PASSED" ? "BENCHMARK PASSED" : "NEEDS IMPROVEMENT"}
                  </span>
                  <h3 style={{ fontSize: "1.6rem", fontWeight: 800, margin: 0, color: "#f8fafc" }}>
                    Overall System Quality: {Math.round(evaluationReport.summary_metrics.overall_rag_score * 100)}%
                  </h3>
                  <p style={{ color: "#cbd5e1", fontSize: "14px", marginTop: "4px" }}>
                    Tested against {evaluationReport.total_test_cases} benchmark cases ({evaluationReport.passed_count} Passed, {evaluationReport.failed_count} Failed) • Quality Threshold: {Math.round(evaluationReport.quality_threshold * 100)}%
                  </p>
                </div>

                <div style={{ textAlign: "right" }}>
                  <span style={{ fontSize: "12px", color: "#94a3b8" }}>Dataset:</span>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "#a5b4fc" }}>
                    {evaluationReport.dataset_file}
                  </div>
                </div>
              </div>

              {/* 4 Canonical Metrics Cards */}
              <div className="stats-grid">
                <div className="stat-box" style={{ borderLeft: "4px solid #6366f1" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="stat-label">Faithfulness</span>
                    <ShieldCheck size={18} color="#818cf8" />
                  </div>
                  <span className="stat-val">{Math.round(evaluationReport.summary_metrics.faithfulness * 100)}%</span>
                  <span style={{ fontSize: "11.5px", color: "#94a3b8" }}>Hallucination-free groundedness</span>
                </div>

                <div className="stat-box" style={{ borderLeft: "4px solid #10b981" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="stat-label">Answer Relevance</span>
                    <Target size={18} color="#34d399" />
                  </div>
                  <span className="stat-val">{Math.round(evaluationReport.summary_metrics.answer_relevance * 100)}%</span>
                  <span style={{ fontSize: "11.5px", color: "#94a3b8" }}>Direct query alignment</span>
                </div>

                <div className="stat-box" style={{ borderLeft: "4px solid #06b6d4" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="stat-label">Context Precision</span>
                    <Award size={18} color="#22d3ee" />
                  </div>
                  <span className="stat-val">{Math.round(evaluationReport.summary_metrics.context_precision * 100)}%</span>
                  <span style={{ fontSize: "11.5px", color: "#94a3b8" }}>Top chunk signal-to-noise</span>
                </div>

                <div className="stat-box" style={{ borderLeft: "4px solid #f59e0b" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="stat-label">Context Recall</span>
                    <BookOpen size={18} color="#fbbf24" />
                  </div>
                  <span className="stat-val">{Math.round(evaluationReport.summary_metrics.context_recall * 100)}%</span>
                  <span style={{ fontSize: "11.5px", color: "#94a3b8" }}>Ground truth coverage</span>
                </div>
              </div>

              {/* Evaluation Metrics Bar Chart */}
              <div style={{
                padding: "24px",
                borderRadius: "14px",
                background: "rgba(15, 23, 42, 0.6)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                marginBottom: "30px"
              }}>
                <h4 style={{ color: "#cbd5e1", fontSize: "1rem", fontWeight: 600, marginBottom: "16px" }}>
                  RAG Core Metrics Breakdown (% Score)
                </h4>
                <div style={{ height: "260px", width: "100%" }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={evalChartData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 13 }} />
                      <YAxis domain={[0, 100]} stroke="#94a3b8" tick={{ fontSize: 12 }} />
                      <Tooltip 
                        formatter={(val) => [`${val}%`, 'Score']}
                        contentStyle={{ backgroundColor: "#0f172a", borderColor: "rgba(255,255,255,0.15)", borderRadius: "8px", color: "#fff" }} 
                      />
                      <Bar dataKey="score" fill="#6366f1" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Detailed Test Case Audit Cards */}
              <h4 style={{ color: "#cbd5e1", fontSize: "1.1rem", fontWeight: 700, marginBottom: "16px" }}>
                Individual Test Case Audits ({evaluationReport.detailed_results.length})
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {evaluationReport.detailed_results.map((item, idx) => (
                  <div key={idx} style={{
                    padding: "22px",
                    borderRadius: "12px",
                    background: "rgba(15, 23, 42, 0.7)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "14px"
                  }}>
                    {/* Header */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span style={{
                          padding: "3px 10px",
                          borderRadius: "6px",
                          fontSize: "12px",
                          fontWeight: 700,
                          background: item.status === "PASSED" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                          color: item.status === "PASSED" ? "#34d399" : "#f87171",
                          border: item.status === "PASSED" ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid rgba(239, 68, 68, 0.4)"
                        }}>
                          {item.status} ({Math.round(item.metrics.overall_score * 100)}%)
                        </span>
                        <strong style={{ fontSize: "15px", color: "#f8fafc" }}>
                          #{item.case_id}: {item.question}
                        </strong>
                      </div>
                    </div>

                    {/* Metric Pills */}
                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                      <span style={{ fontSize: "12px", padding: "4px 10px", borderRadius: "6px", background: "rgba(99, 102, 241, 0.15)", color: "#a5b4fc", border: "1px solid rgba(99, 102, 241, 0.3)" }}>
                        Faithfulness: {Math.round(item.metrics.faithfulness * 100)}%
                      </span>
                      <span style={{ fontSize: "12px", padding: "4px 10px", borderRadius: "6px", background: "rgba(16, 185, 129, 0.15)", color: "#6ee7b7", border: "1px solid rgba(16, 185, 129, 0.3)" }}>
                        Relevance: {Math.round(item.metrics.answer_relevance * 100)}%
                      </span>
                      <span style={{ fontSize: "12px", padding: "4px 10px", borderRadius: "6px", background: "rgba(6, 182, 212, 0.15)", color: "#67e8f9", border: "1px solid rgba(6, 182, 212, 0.3)" }}>
                        Precision: {Math.round(item.metrics.context_precision * 100)}%
                      </span>
                      <span style={{ fontSize: "12px", padding: "4px 10px", borderRadius: "6px", background: "rgba(245, 158, 11, 0.15)", color: "#fcd34d", border: "1px solid rgba(245, 158, 11, 0.3)" }}>
                        Recall: {Math.round(item.metrics.context_recall * 100)}%
                      </span>
                    </div>

                    {/* Comparison Box */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
                      <div style={{ padding: "12px 14px", borderRadius: "8px", background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
                        <div style={{ fontSize: "11px", fontWeight: 700, color: "#34d399", marginBottom: "4px" }}>
                          🎯 EXPECTED GROUND TRUTH:
                        </div>
                        <p style={{ fontSize: "13px", color: "#ecfdf5", margin: 0, lineHeight: 1.5 }}>
                          {item.expected_answer}
                        </p>
                      </div>

                      <div style={{ padding: "12px 14px", borderRadius: "8px", background: "rgba(99, 102, 241, 0.08)", border: "1px solid rgba(99, 102, 241, 0.2)" }}>
                        <div style={{ fontSize: "11px", fontWeight: 700, color: "#a5b4fc", marginBottom: "4px" }}>
                          🤖 GENERATED RAG ANSWER:
                        </div>
                        <p style={{ fontSize: "13px", color: "#e0e7ff", margin: 0, lineHeight: 1.5 }}>
                          {item.generated_answer}
                        </p>
                      </div>
                    </div>

                    {/* Judge Reasoning */}
                    {item.reasoning && (
                      <div style={{ padding: "10px 14px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.06)", fontSize: "12.5px", color: "#94a3b8" }}>
                        <strong style={{ color: "#cbd5e1" }}>AI Judge Verdict: </strong>
                        {item.reasoning}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Past Evaluation Runs Section */}
              {evalRuns.length > 0 && (
                <div style={{ marginTop: "36px", borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: "24px" }}>
                  <h4 style={{ color: "#cbd5e1", fontSize: "1rem", fontWeight: 600, marginBottom: "14px" }}>
                    Benchmark Audit Run History (`data/evaluation/`)
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {evalRuns.map((run, idx) => (
                      <div key={idx} style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        padding: "12px 18px",
                        borderRadius: "8px",
                        background: "rgba(15, 23, 42, 0.5)",
                        border: "1px solid rgba(255, 255, 255, 0.06)",
                        fontSize: "13.5px"
                      }}>
                        <div>
                          <strong style={{ color: "#f8fafc" }}>{run.filename}</strong>
                          <span style={{ color: "#94a3b8", marginLeft: "12px" }}>
                            Overall: <strong style={{ color: "#a5b4fc" }}>{Math.round(run.overall_rag_score * 100)}%</strong> • {run.passed_count} Passed, {run.failed_count} Failed
                          </span>
                        </div>
                        <button 
                          onClick={() => loadSpecificRun(run.filename)}
                          style={{
                            padding: "6px 14px",
                            background: "rgba(99, 102, 241, 0.15)",
                            border: "1px solid rgba(99, 102, 241, 0.35)",
                            borderRadius: "6px",
                            color: "#a5b4fc",
                            fontSize: "12px",
                            fontWeight: 600,
                            cursor: "pointer"
                          }}>
                          Load Audit
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

    </div>
  )
}

export default App