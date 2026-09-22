import os
import pymupdf
import rag_engine

PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "processed"))
os.makedirs(PROCESSED_DIR, exist_ok=True)

def parse_pdf(file_path: str, original_filename: str) -> str:
    """Lightning fast PDF to Markdown converter with Scanned PDF Multimodal OCR fallback."""
    base_name = os.path.splitext(original_filename)[0]
    save_path = os.path.join(PROCESSED_DIR, f"{base_name}.md")
    alt_save_path = os.path.join(PROCESSED_DIR, f"{original_filename}.md")
    
    # 1. Try ultra-fast digital text extraction (< 0.1s)
    markdown_text = ""
    try:
        doc = pymupdf.open(file_path)
        pages_text = [f"## Page {i+1}\n" + p.get_text("text").strip() for i, p in enumerate(doc) if p.get_text("text").strip()]
        total_text = "\n\n".join(pages_text)
        
        if len(total_text) > 150:
            markdown_text = f"# {base_name}\n\n" + total_text
    except Exception:
        pass
        
    # 2. If scanned image-only PDF (no digital text), use Gemini Multimodal Vision OCR!
    if not markdown_text or len(markdown_text.strip()) < 150:
        try:
            client = rag_engine._get_gemini_client()
            if client:
                file_ref = client.files.upload(file=file_path)
                resp = client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
                    contents=[file_ref, f"Transcribe and extract the full content of this document ({original_filename}) into clean, structured Markdown notes with headers, bullet points, and key definitions."]
                )
                if resp and resp.text:
                    markdown_text = resp.text
        except Exception as e:
            print(f"Notice: Gemini OCR fallback failed: {e}")
            
    if not markdown_text:
        markdown_text = f"# {base_name}\n\nDocument uploaded successfully."
        
    for p in [save_path, alt_save_path]:
        with open(p, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        
    return markdown_text

def parse_docx(file_path: str, original_filename: str) -> str:
    """Extract headings, paragraphs, and tables from Word (.docx) documents into clean Markdown."""
    base_name = os.path.splitext(original_filename)[0]
    save_path = os.path.join(PROCESSED_DIR, f"{base_name}.md")
    alt_save_path = os.path.join(PROCESSED_DIR, f"{original_filename}.md")
    
    lines = [f"# {base_name}\n"]
    try:
        import docx
        doc = docx.Document(file_path)
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style_name = para.style.name.lower() if para.style else ""
            if "heading 1" in style_name:
                lines.append(f"\n## {text}\n")
            elif "heading 2" in style_name:
                lines.append(f"\n### {text}\n")
            elif "heading 3" in style_name:
                lines.append(f"\n#### {text}\n")
            elif "list" in style_name or "bullet" in style_name:
                lines.append(f"- {text}")
            else:
                lines.append(f"{text}\n")
                
        # Parse tables if present
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                table_rows.append(cells)
            if table_rows:
                headers = table_rows[0]
                lines.append("\n| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for row in table_rows[1:]:
                    lines.append("| " + " | ".join(row) + " |")
                lines.append("\n")
                
    except Exception as e:
        print(f"Error parsing DOCX {original_filename}: {e}")
        lines.append(f"\nDocument text extracted with basic reader: {e}\n")
        
    markdown_text = "\n".join(lines).strip()
    if not markdown_text or len(markdown_text) < 50:
        markdown_text = f"# {base_name}\n\nDocument uploaded successfully."
        
    for p in [save_path, alt_save_path]:
        with open(p, "w", encoding="utf-8") as f:
            f.write(markdown_text)
            
    return markdown_text

def parse_text_file(file_path: str, original_filename: str) -> str:
    """Read TXT or MD files with multi-encoding fallback and save to processed Markdown."""
    base_name = os.path.splitext(original_filename)[0]
    save_path = os.path.join(PROCESSED_DIR, f"{base_name}.md")
    alt_save_path = os.path.join(PROCESSED_DIR, f"{original_filename}.md")
    
    content = ""
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            if content:
                break
        except Exception:
            continue
            
    if not content:
        content = f"# {base_name}\n\nDocument uploaded successfully."
    elif not content.strip().startswith("#"):
        content = f"# {base_name}\n\n" + content
        
    for p in [save_path, alt_save_path]:
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
            
    return content