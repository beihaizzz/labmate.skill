#!/usr/bin/env python3
"""PDF text extraction and scanned detection."""

import argparse
import json
import sys
from pathlib import Path

try:
    import pdfplumber
    import pymupdf4llm
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

def parse_pdf(filepath: Path, output_format: str = "json"):
    """Parse PDF and extract text."""
    if not HAS_DEPS:
        return {"error": "Missing dependencies: pdfplumber, pymupdf4llm"}
    
    result = {
        "filename": filepath.name,
        "page_count": 0,
        "text_by_page": [],
        "markdown": "",
        "is_scanned": False,
        "warning": None
    }
    
    try:
        # Extract with pdfplumber
        with pdfplumber.open(filepath) as pdf:
            result["page_count"] = len(pdf.pages)
            
            total_text = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                result["text_by_page"].append({
                    "page": i + 1,
                    "content": text
                })
                total_text += text + "\n"
            
            # Check if scanned (no extractable text)
            if not total_text.strip():
                result["is_scanned"] = True
                result["warning"] = "SCANNED_PDF_DETECTED"
        
        # Convert to markdown with pymupdf4llm
        try:
            result["markdown"] = pymupdf4llm.to_markdown(str(filepath))
        except Exception as e:
            result["markdown"] = f"# Error converting to markdown: {e}"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Parse PDF file')
    parser.add_argument('--input', '-i', required=True, help='Input PDF file')
    parser.add_argument('--format', '-f', choices=['json', 'markdown'], default='json')
    args = parser.parse_args()
    
    filepath = Path(args.input)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    
    result = parse_pdf(filepath, args.format)
    
    if args.format == "markdown":
        print(result.get("markdown", ""))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    sys.exit(0 if "error" not in result else 1)

if __name__ == '__main__':
    main()
