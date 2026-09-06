import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import MarkdownTextSplitter
from dotenv import load_dotenv

load_dotenv()

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
os.makedirs(DB_DIR, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=DB_DIR)

# Reuse persistent embedding function
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = chroma_client.get_or_create_collection(
    name="pdf_documents",
    embedding_function=sentence_transformer_ef
)

def index_document(markdown_text, filename):
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(markdown_text)
    
    if not chunks: 
        return 0
        
    documents, metadatas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append({"source": filename, "chunk_id": i})
        ids.append(f"{filename}_chunk_{i}")
        
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    return len(chunks)

def query_rag(question):
    # 1. RETRIEVAL from ChromaDB
    results = collection.query(query_texts=[question], n_results=3)
    
    retrieved_chunks = []
    context_text = ""
    
    if results["documents"] and len(results["documents"][0]) > 0:
        for i in range(len(results["documents"][0])):
            chunk_text = results["documents"][0][i]
            retrieved_chunks.append({
                "text": chunk_text,
                "source": results["metadatas"][0][i]["source"]
            })
            context_text += f"\n\n{chunk_text}"
            
    # 2. GENERATION with Gemini 3.6 Flash & Rate Limit Protection
    api_key = os.getenv("GEMINI_API_KEY")
    final_answer = ""
    
    if api_key and api_key != "paste_your_key_here_without_quotes":
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            
            prompt = f"""
You are a concise, helpful RAG intelligence assistant.
Use ONLY the following retrieved context to answer the user's question accurately in 2 or 3 clear sentences.
If the answer is not in the context, clearly state that the provided documents do not contain that information.

CONTEXT:
{context_text}

QUESTION:
{question}
"""
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt
            )
            final_answer = response.text.strip()
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                # Graceful extraction without displaying raw API errors
                if retrieved_chunks:
                    first_chunk = retrieved_chunks[0]["text"].replace("\n", " ").strip()
                    final_answer = f"Based on indexed record ({retrieved_chunks[0]['source']}): {first_chunk[:320]}..."
                else:
                    final_answer = "No matching records found in the indexed database."
            else:
                final_answer = f"Notice: {err_str}"
    else:
        if retrieved_chunks:
            final_answer = f"Retrieved {len(retrieved_chunks)} relevant chunks from {retrieved_chunks[0]['source']}."
        else:
            final_answer = "No matching context found."
        
    return {
        "question": question,
        "retrieved_chunks": retrieved_chunks,
        "generated_answer": final_answer
    }