import os
import pymupdf4llm 

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def parse_pdf(file_path, original_filename):
    """Lightning fast PDF to Markdown converter."""
    # This takes 1 second instead of 2 minutes!
    markdown_text = pymupdf4llm.to_markdown(file_path)
    
    base_name = os.path.splitext(original_filename)[0]
    save_path = os.path.join(PROCESSED_DIR, f"{base_name}.md")
    
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)
        
    return markdown_text