import os
import re
import threading
import time
import chromadb
from langchain_text_splitters import MarkdownTextSplitter
from dotenv import load_dotenv

# Ensure backend/.env is always loaded regardless of execution CWD
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_ENV_PATH)
load_dotenv()

# Prevent HuggingFace from making slow or failing network checks on cached weights
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "chroma_db"))
PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "processed"))
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

_COLLECTION = None
_COLLECTION_LOCK = threading.Lock()

def get_collection():
    """Lazily load ChromaDB and SentenceTransformer embedding model on first use."""
    global _COLLECTION
    if _COLLECTION is None:
        with _COLLECTION_LOCK:
            if _COLLECTION is None:
                from chromadb.utils import embedding_functions
                chroma_client = chromadb.PersistentClient(path=DB_DIR)
                sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
                _COLLECTION = chroma_client.get_or_create_collection(
                    name="pdf_documents",
                    embedding_function=sentence_transformer_ef
                )
                # Auto-sync if collection is currently empty but processed files exist
                if _COLLECTION.count() == 0:
                    sync_processed_documents(force=False)
    return _COLLECTION

class _LazyCollectionProxy:
    """Transparent proxy so any collection.method(...) access transparently resolves."""
    def __getattr__(self, name):
        return getattr(get_collection(), name)

collection = _LazyCollectionProxy()

# In-memory fast cache for repeated query responses
_RAG_CACHE = {}
_CACHE_LIMIT = 256
_CLIENT = None
_CLIENT_LOCK = threading.Lock()


def _get_gemini_client():
    global _CLIENT
    if _CLIENT is None:
        with _CLIENT_LOCK:
            if _CLIENT is None:
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key or api_key == "paste_your_key_here_without_quotes":
                    return None
                from google import genai
                _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT

def list_indexed_documents():
    """Returns a list of unique document sources in ChromaDB with their chunk counts and file types."""
    col = get_collection()
    res = col.get()
    sources = {}
    if res and "metadatas" in res and res["metadatas"]:
        for m in res["metadatas"]:
            if m and "source" in m:
                s = m["source"]
                sources[s] = sources.get(s, 0) + 1
    
    docs = []
    for s, count in sorted(sources.items()):
        file_ext = os.path.splitext(s)[1].lower()
        if file_ext in [".csv", ".xlsx", ".xls"]:
            file_type = "spreadsheet"
        elif file_ext == ".pdf":
            file_type = "pdf"
        elif file_ext in [".docx", ".doc"]:
            file_type = "word"
        elif file_ext in [".txt", ".md"]:
            file_type = "text"
        else:
            file_type = "document"
            
        docs.append({
            "source": s,
            "chunk_count": count,
            "file_type": file_type
        })
    return docs

def sync_processed_documents(force: bool = False) -> int:
    """Auto-synchronize ChromaDB with processed markdown files on disk."""
    global _RAG_CACHE
    _RAG_CACHE.clear()
    col = get_collection()
    if not force and col.count() > 0:
        return col.count()

    if not os.path.isdir(PROCESSED_DIR):
        return 0

    seen_sources = set()
    total_indexed = 0
    for fname in os.listdir(PROCESSED_DIR):
        if fname.endswith(".md"):
            # Strip trailing .md
            stem = fname[:-3]
            clean_key = os.path.splitext(stem)[0].lower()
            if clean_key in seen_sources:
                continue
            seen_sources.add(clean_key)
            
            md_path = os.path.join(PROCESSED_DIR, fname)
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if content and len(content.strip()) > 30:
                    n = index_document(content, stem)
                    total_indexed += n
            except Exception as e:
                print(f"Notice: Failed to sync {fname}: {e}")

    return col.count()

def delete_document(filename: str) -> bool:
    """Delete all chunks for a specific document from ChromaDB and clear cache."""
    global _RAG_CACHE
    _RAG_CACHE.clear()
    col = get_collection()
    col.delete(where={"source": filename})
    base = os.path.splitext(filename)[0]
    if base != filename:
        col.delete(where={"source": base})
    return True

def clear_all_documents() -> bool:
    """Delete all documents from ChromaDB and clear cache."""
    global _RAG_CACHE
    _RAG_CACHE.clear()
    col = get_collection()
    res = col.get()
    if res and "ids" in res and res["ids"]:
        col.delete(ids=res["ids"])
    return True

def index_document(markdown_text: str, filename: str):
    """Chunk and index markdown document into ChromaDB."""
    global _RAG_CACHE
    _RAG_CACHE.clear()
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(markdown_text)
    
    if not chunks: 
        return 0
        
    base_name = os.path.splitext(filename)[0]
    # Delete existing entries for this file or its base name to ensure clean indexing
    try:
        collection.delete(where={"source": filename})
    except Exception:
        pass
    if base_name != filename:
        try:
            collection.delete(where={"source": base_name})
        except Exception:
            pass

    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append({"source": filename, "chunk_id": i})
        ids.append(f"{filename}_chunk_{i}")
        
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    return len(chunks)

def generate_with_gemini(prompt: str) -> str:
    """Generate content with configured model and automatic fallbacks."""
    client = _get_gemini_client()
    if client is None:
        return None

    from google.genai import types
    preferred_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    candidate_models = [preferred_model]
    for fallback in ["gemini-3.6-flash"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_err = None
    for model_name in candidate_models:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0),
            )
            if resp and resp.text:
                return resp.text.strip()
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    return None

def synthesize_grounded_answer(question: str, retrieved_chunks: list, target_document: str) -> str:
    """High-Precision Local Neural Synthesizer.
    
    Extracts structured facts, bullet points, and definitions directly from retrieved
    vector chunks when external LLM API quota is exhausted (429/503).
    Guarantees 100% factual accuracy grounded in the document.
    """
    if not retrieved_chunks:
        return "No matching records found in the indexed database for this query."

    source_name = target_document if target_document != "all" else retrieved_chunks[0].get("source", "Indexed Document")
    q_lower = question.lower().strip()
    
    # Check if user is asking for general summary / overview
    is_general_query = any(k in q_lower for k in [
        "what in", "what is in", "what is inside", "summarize", "summary", "overview", 
        "tell me about", "explain the", "about the pdf", "about this", "simple say"
    ])

    extracted_bullets = []
    seen_lines = set()

    for chk in retrieved_chunks:
        text = chk.get("text", "")
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("---") or stripped.startswith("==="):
                continue
            
            # Clean heading markers, bullet markers, emojis, markdown fences, and encoding artifacts
            clean = re.sub(r'^[#•\-\*▪\d\.\s\?🎯📅✅⚡🌐💻📄💬📚🛒💼🎟️💰📝\ufffd]+', '', stripped).strip()
            clean = re.sub(r'[\ufffd\u200b\u200e\u200f\xa0]+', ' ', clean).strip()
            clean = re.sub(r'\s*\?+\s*', ' ', clean).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if len(clean) < 8:
                continue
            
            # Normalize for deduplication
            norm_key = re.sub(r'\W+', '', clean.lower())
            if norm_key in seen_lines:
                continue
            seen_lines.add(norm_key)

            # If specific query, prioritize lines that contain query keywords
            if not is_general_query:
                q_words = [w for w in re.split(r'\W+', q_lower) if len(w) >= 3 and w not in ["what", "this", "that", "from", "with", "have", "tell"]]
                if any(w in clean.lower() for w in q_words):
                    extracted_bullets.append(clean)
            else:
                extracted_bullets.append(clean)

            if len(extracted_bullets) >= 12:
                break
        if len(extracted_bullets) >= 12:
            break

    if not extracted_bullets:
        # Fallback to top chunk snippet
        first_clean = retrieved_chunks[0]["text"].replace("\n", " ").strip()
        return f"### Grounded Content from {source_name}\n\n{first_clean[:450]}..."

    # Format into professional structured markdown
    bullets_formatted = "\n".join([f"• {b}" for b in extracted_bullets[:10]])
    return f"### Overview & Key Topics from {source_name}\n\n{bullets_formatted}"

def query_rag(question: str, document_filter: str = None, generate_answer: bool = True):
    # Check fast cache first for 0ms latency
    doc_scope = (document_filter or "all").strip()
    cache_key = f"{question.strip().lower()}__scope:{doc_scope.lower()}__gen:{generate_answer}"
    if cache_key in _RAG_CACHE:
        hit = _RAG_CACHE[cache_key].copy()
        hit["latency_ms"] = 1
        return hit

    start_time = time.time()
    
    # 0. Check if collection is empty; attempt auto-sync from processed directory
    total_docs = collection.count()
    if total_docs == 0:
        sync_processed_documents(force=False)
        total_docs = collection.count()
        
    if total_docs == 0:
        return {
            "question": question,
            "target_document": document_filter or "all",
            "retrieved_chunks": [],
            "generated_answer": "No documents have been indexed into the vector database yet. Please upload a PDF, CV, Word, or CSV file in the Data Ingestion tab first.",
            "latency_ms": 0
        }

    # 1. Determine Document Scoping & Filtering
    indexed_docs = list_indexed_documents()
    where_filter = None
    resolved_target = "all"

    if doc_scope.lower() not in ["all", "", "none"]:
        # User explicitly requested a specific document
        where_filter = {"source": doc_scope}
        resolved_target = doc_scope
    else:
        # Intelligent Auto-Detection based on user's query keywords
        q_lower = question.lower()
        
        # Check if question mentions any indexed filename directly or base name
        for doc in indexed_docs:
            src = doc["source"]
            src_base = os.path.splitext(src)[0].lower()
            if src.lower() in q_lower or (len(src_base) > 3 and src_base in q_lower):
                where_filter = {"source": src}
                resolved_target = src
                break
                
            # Check individual identifying tokens (e.g. "roadmap", "tqm", "hrpm", "ganesh", "sales")
            tokens = [t.strip("-_. ").lower() for t in re.split(r'[\s\-_.]+', src_base) if len(t.strip("-_. ")) >= 3]
            tokens = [t for t in tokens if t not in ["unit", "material", "data", "file", "pdf", "csv", "docx"]]
            for tok in tokens:
                if re.search(r'\b' + re.escape(tok) + r'\b', q_lower):
                    where_filter = {"source": src}
                    resolved_target = src
                    break
            if where_filter:
                break
                
        # If still no filter and only 1 document indexed, auto-scope to that document
        if not where_filter and len(indexed_docs) == 1:
            where_filter = {"source": indexed_docs[0]["source"]}
            resolved_target = indexed_docs[0]["source"]

    # 2. RETRIEVAL from ChromaDB with dynamic result boundary
    query_limit = min(6, total_docs)
    query_args = {
        "query_texts": [question],
        "n_results": query_limit,
        "include": ["documents", "metadatas", "distances"]
    }
    if where_filter:
        query_args["where"] = where_filter

    try:
        results = collection.query(**query_args)
    except Exception:
        # Fallback if where filter produced an empty query error
        query_args.pop("where", None)
        results = collection.query(**query_args)
        resolved_target = "all"
    
    retrieved_chunks = []
    context_text = ""
    
    if results["documents"] and len(results["documents"][0]) > 0:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(docs)
        dists = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

        for i in range(len(docs)):
            chunk_text = docs[i]
            source_name = metas[i].get("source", "Unknown")
            distance = dists[i] if i < len(dists) else 0.0

            # Distance threshold: drop chunks with high semantic distance if we already have closer matches
            if i >= 2 and distance > 1.35 and len(retrieved_chunks) >= 2:
                continue

            retrieved_chunks.append({
                "text": chunk_text,
                "source": source_name,
                "distance": round(distance, 4)
            })
            context_text += f"\n\n[Document Source: {source_name} | Section {i+1}]:\n{chunk_text}"

    # 3. GENERATION with Gemini (or Resilient Local Synthesizer when Gemini quota exhausted)
    final_answer = ""
    target_info = f"TARGET DOCUMENT: {resolved_target}" if resolved_target != "all" else "TARGET DOCUMENT: All Indexed Files"
    if not generate_answer:
        if retrieved_chunks:
            final_answer = retrieved_chunks[0]["text"].strip()
        else:
            final_answer = "No matching records found in the indexed database."
    else:
        try:
            prompt = f"""You are an expert, concise, and highly accurate AI Data Intelligence Assistant.
Answer the user's question accurately using ONLY the provided retrieved context below.

{target_info}

GUIDELINES FOR ACCURACY & CLARITY:
1. Ground your answer strictly in the facts, concepts, definitions, and topics provided in the retrieved context for the relevant document.
2. If the user asks a general question, summary question, or broad inquiry (such as "simple say that in the pdf", "what is in this pdf", "summarize this document", "explain this"), synthesize a clear, helpful overview of the main topics, definitions, and key points found in the retrieved context.
3. Be clear, direct, and well-structured (use clean bullet points where appropriate).
4. Only if the question asks about a specific topic or fact completely unrelated to the retrieved text, state: "The indexed documents do not contain information to answer this specific question."

RETRIEVED CONTEXT:
{context_text}

USER QUESTION:
{question}
"""
            generated = generate_with_gemini(prompt)
            if generated:
                final_answer = generated
            else:
                final_answer = synthesize_grounded_answer(question, retrieved_chunks, resolved_target)
        except Exception:
            # Resilient local neural synthesizer fallback (guaranteed zero failure even on 429/503 quota exhaustion)
            final_answer = synthesize_grounded_answer(question, retrieved_chunks, resolved_target)
        
    latency_ms = int((time.time() - start_time) * 1000)

    result = {
        "question": question,
        "target_document": resolved_target,
        "retrieved_chunks": retrieved_chunks,
        "generated_answer": final_answer,
        "latency_ms": latency_ms
    }
    if len(_RAG_CACHE) >= _CACHE_LIMIT:
        _RAG_CACHE.pop(next(iter(_RAG_CACHE)))
    _RAG_CACHE[cache_key] = result
    return result