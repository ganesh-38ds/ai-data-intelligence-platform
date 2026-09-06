import os
import json
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation")
os.makedirs(EVAL_DIR, exist_ok=True)

def generate_synthetic_dataset(filename=None, num_questions=3):
    """
    Generates synthetic evaluation test cases from processed document markdown.
    Each test case has:
      - question
      - context (ground truth source text)
      - expected_answer
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env")

    # Find a markdown file to generate from
    available_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".md")]
    if not available_files:
        raise ValueError("No processed document found in data/processed/. Please upload a PDF first.")

    target_file = filename if filename and filename in available_files else available_files[0]
    file_path = os.path.join(PROCESSED_DIR, target_file)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Take first ~4500 characters to keep prompt compact and representative
    sample_context = content[:4500]

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

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()

    test_cases = json.loads(raw_text)

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
