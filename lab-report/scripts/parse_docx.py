#!/usr/bin/env python3
"""DOCX parsing with placeholder detection."""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

def parse_docx(filepath: Path):
    """Parse DOCX and extract text, tables, placeholders."""
    if not HAS_DOCX:
        return {"error": "Missing dependency: python-docx"}
    
    result = {
        "filename": filepath.name,
        "paragraphs": [],
        "tables": [],
        "placeholders": [],
        "structure": {
            "paragraph_count": 0,
            "table_count": 0,
            "heading_count": 0
        }
    }
    
    try:
        doc = Document(filepath)
        
        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                result["paragraphs"].append({
                    "text": text,
                    "style": para.style.name if para.style else None
                })
                
                # Detect headings
                if para.style and "heading" in para.style.name.lower():
                    result["structure"]["heading_count"] += 1
        
        # Extract placeholders {{...}}
        full_text = "\n".join([p["text"] for p in result["paragraphs"]])
        placeholders = re.findall(r'\{\{([^}]+)\}\}', full_text)
        result["placeholders"] = list(set([f"{{{{{p}}}}}" for p in placeholders]))
        
        # Extract tables
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    row_data.append(cell_text)
                    # Also search for placeholders in table cells
                    cell_placeholders = re.findall(r'\{\{([^}]+)\}\}', cell_text)
                    for p in cell_placeholders:
                        ph = f"{{{{{p}}}}}"
                        if ph not in result["placeholders"]:
                            result["placeholders"].append(ph)
                table_data.append(row_data)
            result["tables"].append(table_data)
        
        # Update structure counts
        result["structure"]["paragraph_count"] = len(result["paragraphs"])
        result["structure"]["table_count"] = len(result["tables"])
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Parse DOCX file')
    parser.add_argument('--input', '-i', required=True, help='Input DOCX file')
    args = parser.parse_args()
    
    filepath = Path(args.input)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    
    result = parse_docx(filepath)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    sys.exit(0 if "error" not in result else 1)

if __name__ == '__main__':
    main()
