import os
import json
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation")
os.makedirs(EVAL_DIR, exist_ok=True)

def extract_fallback_test_cases(markdown_text, target_filename, num_questions=3):
    """
    Extracts grounded Q&A test cases directly from document structure
    if external LLM API experiences rate limits or network issues.
    """
    lines = [line.strip() for line in markdown_text.split("\n") if line.strip()]
    test_cases = []
    
    sections = []
    current_title = "Document Overview"
    current_body = []
    
    for line in lines:
        if line.startswith("#"):
            if current_body:
                sections.append((current_title, " ".join(current_body)))
                current_body = []
            current_title = line.lstrip("#").strip()
        else:
            if len(line) > 25:
                current_body.append(line)
                
    if current_body:
        sections.append((current_title, " ".join(current_body)))
        
    for title, body in sections[:num_questions]:
        if len(body) > 30:
            test_cases.append({
                "question": f"What does the document state regarding {title}?",
                "context": body[:350],
                "expected_answer": body[:200].rstrip(".") + "."
            })
            
    while len(test_cases) < num_questions:
        idx = len(test_cases) + 1
        excerpt = markdown_text[:250].replace("\n", " ").strip()
        test_cases.append({
            "question": f"What key information is highlighted in Section {idx} of {target_filename}?",
            "context": excerpt,
            "expected_answer": excerpt[:150].rstrip(".") + "."
        })
        
    return test_cases[:num_questions]

def generate_synthetic_dataset(filename=None, num_questions=3):
    """
    Generates synthetic evaluation test cases from processed document markdown.
    Each test case has:
      - question
      - context (ground truth source text)
      - expected_answer
    """
    api_key = os.getenv("GEMINI_API_KEY")

    # Find a markdown file to generate from
    available_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".md")]
    if not available_files:
        raise ValueError("No processed document found in data/processed/. Please upload a PDF or CSV first.")

    target_file = filename if filename and filename in available_files else available_files[0]
    file_path = os.path.join(PROCESSED_DIR, target_file)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Stratified Multi-Region Sampling across entire document (beginning, middle, end)
    if len(content) > 6000:
        mid_start = len(content) // 2
        sample_context = (
            content[:2000] 
            + "\n\n[... Middle Section Excerpt ...]\n\n" 
            + content[mid_start:mid_start+1500] 
            + "\n\n[... Concluding Section Excerpt ...]\n\n" 
            + content[-1200:]
        )
    else:
        sample_context = content[:4500]

    test_cases = None

    if api_key and api_key != "paste_your_key_here_without_quotes":
        try:
            from google.genai import types
            client = genai.Client(api_key=api_key)

            prompt = f"""
You are an AI benchmark engineer building an evaluation dataset for a RAG system.
Based on the following document excerpt, generate EXACTLY {num_questions} distinct question-answer test cases.

DOCUMENT EXCERPT:
{sample_context}

RULES:
1. Each test case MUST have:
   - "question": A realistic question a user would ask about this document.
   - "context": The exact sentence or paragraph from the document that answers the question.
   - "expected_answer": A clear, accurate, concise answer based strictly on that context.
2. Return ONLY valid JSON as a list of objects with keys: "question", "context", "expected_answer".
3. Do not include markdown code fence formatting (like ```json), return raw JSON only.
"""
            candidate_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]
            raw_text = ""
            for m in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.0)
                    )
                    if response and response.text:
                        raw_text = response.text.strip()
                        break
                except Exception:
                    continue

            if raw_text:
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                parsed = json.loads(raw_text)
                if isinstance(parsed, list) and len(parsed) > 0:
                    test_cases = parsed[:num_questions]
        except Exception as e:
            print(f"Notice: Synthetic QA generation fallback triggered: {e}")

    # If API quota is exhausted or unconfigured, smoothly generate structured benchmark
    if not test_cases:
        test_cases = extract_fallback_test_cases(content, target_file, num_questions)

    # Save to data/evaluation
    timestamp = int(time.time())
    output_filename = f"synthetic_qa_{timestamp}.json"
    output_path = os.path.join(EVAL_DIR, output_filename)

    record = {
        "source_document": target_file,
        "created_at": timestamp,
        "num_questions": len(test_cases),
        "test_cases": test_cases
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    return {
        "saved_file": output_filename,
        "source_document": target_file,
        "test_cases": test_cases
    }

def list_evaluation_datasets():
    """Lists all saved synthetic datasets in data/evaluation."""
    if not os.path.exists(EVAL_DIR):
        return []
    files = [f for f in os.listdir(EVAL_DIR) if f.endswith(".json")]
    datasets = []
    for f in sorted(files, reverse=True):
        fpath = os.path.join(EVAL_DIR, f)
        try:
            with open(fpath, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                datasets.append({
                    "filename": f,
                    "source_document": data.get("source_document", "Unknown"),
                    "num_questions": data.get("num_questions", len(data.get("test_cases", []))),
                    "created_at": data.get("created_at", 0)
                })
        except Exception:
            continue
    return datasets
