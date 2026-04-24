#!/usr/bin/env python3
"""Template filling with docxtpl, CJK support, and de-AI styles."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from docx import Document
    from docxtpl import DocxTemplate
    from docx.oxml.ns import qn
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# De-AI banned words
BANNED_WORDS = ['首先', '其次', '最后', '总而言之', '值得注意的是', '综上所述', '不可否认']


def _find_libreoffice() -> str | None:
    """Find LibreOffice executable."""
    for name in ['soffice', 'libreoffice', 'soffice.exe', 'libreoffice.exe']:
        found = shutil.which(name)
        if found:
            return found
    for base in [r'C:\Program Files\LibreOffice\program',
                 r'C:\Program Files (x86)\LibreOffice\program']:
        for exe in ['soffice.exe', 'swriter.exe']:
            cand = Path(base) / exe
            if cand.exists():
                return str(cand)
    return None


def _convert_to_docx(filepath: Path) -> Path | None:
    """Convert .doc to .docx via LibreOffice. Returns .docx path or None."""
    lo = _find_libreoffice()
    if not lo:
        return None
    try:
        result = subprocess.run(
            [lo, '--headless', '--convert-to', 'docx', '--outdir',
             str(filepath.parent), str(filepath)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            docx = filepath.with_suffix('.docx')
            if docx.exists():
                return docx
    except Exception:
        pass
    return None

def set_cjk_font(run, font_name='宋体'):
    """Set CJK font for a run to prevent tofu."""
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)

def apply_de_ai_style(text: str) -> str:
    """Apply de-AI style to text."""
    # This is a placeholder - actual de-AI would be done by the AI agent
    # We just verify no banned words exist
    for word in BANNED_WORDS:
        if word in text:
            print(f"Warning: Found banned AI word '{word}' in content", file=sys.stderr)
    return text

def fill_template(template_path: Path, data_path: Path, output_path: Path, style: str = "normal"):
    """Fill template with data."""
    if not HAS_DOCX:
        return {"error": "Missing dependencies: python-docx, docxtpl"}
    
    result = {
        "success": False,
        "template": str(template_path),
        "output": str(output_path),
        "placeholders_filled": [],
        "placeholders_missing": [],
        "style_applied": style
    }
    
    try:
        # Load data
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle .doc files — convert to .docx first
        suffix = template_path.suffix.lower()
        if suffix == '.doc':
            converted = _convert_to_docx(template_path)
            if converted is None:
                result["error"] = (
                    "Cannot process .doc template. Please:\n"
                    "1. Install LibreOffice (https://www.libreoffice.org/)\n"
                    "2. Or manually save as .docx in Word / WPS"
                )
                result["needs_conversion"] = True
                return result
            template_path = converted
        
        # Copy template (never modify original)
        shutil.copy(template_path, output_path)
        
        # Load and render template
        doc = DocxTemplate(output_path)
        
        # Render with Jinja2 context
        doc.render(data)
        
        # Save
        doc.save(output_path)
        
        # Verify CJK fonts
        verify_doc = Document(output_path)
        for para in verify_doc.paragraphs:
            for run in para.runs:
                if any('\u4e00' <= c <= '\u9fff' for c in run.text):
                    set_cjk_font(run)
        verify_doc.save(output_path)
        
        result["success"] = True
        
        # Check for unreplaced placeholders
        final_doc = Document(output_path)
        full_text = " ".join([p.text for p in final_doc.paragraphs])
        import re
        remaining = re.findall(r'\{\{([^}]+)\}\}', full_text)
        result["placeholders_missing"] = remaining
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def verify_original_unchanged(template_path: Path, original_hash: str) -> bool:
    """Verify original template wasn't modified."""
    with open(template_path, 'rb') as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()
    return current_hash == original_hash

def main():
    parser = argparse.ArgumentParser(description='Fill DOCX template')
    parser.add_argument('--template', '-t', required=True, help='Template DOCX file')
    parser.add_argument('--data', '-d', required=True, help='JSON data file')
    parser.add_argument('--output', '-o', required=True, help='Output DOCX file')
    parser.add_argument('--style', '-s', choices=['perfect', 'normal'], default='normal',
                       help='Report style (both use de-AI guidelines)')
    args = parser.parse_args()
    
    template_path = Path(args.template)
    data_path = Path(args.data)
    output_path = Path(args.output)
    
    if not template_path.exists():
        print(f"Error: Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)
    
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)
    
    # Get original hash before any operation
    with open(template_path, 'rb') as f:
        original_hash = hashlib.sha256(f.read()).hexdigest()
    
    result = fill_template(template_path, data_path, output_path, args.style)
    
    # Verify original unchanged
    if not verify_original_unchanged(template_path, original_hash):
        print("Error: Original template was modified!", file=sys.stderr)
        sys.exit(1)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 1)

if __name__ == '__main__':
    main()
