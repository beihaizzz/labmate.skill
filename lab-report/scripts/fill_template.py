#!/usr/bin/env python3
"""Template filling — uses inspect data for exact formatting (no guessing)."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.oxml.ns import qn
    from docxtpl import DocxTemplate
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# Import formatting utilities (outside try — fill_utils has its own import guards)
sys.path.insert(0, str(Path(__file__).parent))
import fill_utils

BANNED_WORDS = ['首先', '其次', '最后', '总而言之', '值得注意的是', '综上所述', '不可否认']


def _find_libreoffice() -> str | None:
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
    lo = _find_libreoffice()
    if not lo:
        return None
    try:
        result = subprocess.run(
            [lo, '--headless', '--convert-to', 'docx', '--outdir',
             str(filepath.parent), str(filepath)],
            capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            docx = filepath.with_suffix('.docx')
            if docx.exists():
                return docx
    except Exception:
        pass
    return None


def _verify_no_missing_placeholders(doc: Document) -> list:
    full_text = " ".join([p.text for p in doc.paragraphs])
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                full_text += " " + cell.text
    return re.findall(r'\{\{([^}]+)\}\}', full_text)


def _compare_with_inspect(output_doc: Document, inspect_data: dict) -> list:
    """Post-fill diff: detect overwritten label cells."""
    warnings = []
    out_tables = output_doc.tables
    for t_idx, table in enumerate(inspect_data.get("tables", [])):
        if t_idx >= len(out_tables):
            break
        for cell_info in table.get("cells", []):
            if not cell_info.get("is_label"):
                continue
            out_cell = out_tables[t_idx].rows[cell_info["row"]].cells[cell_info["column"]]
            out_text = out_cell.text.strip()
            in_text = cell_info.get("text", "").strip()
            if out_text and out_text != in_text and in_text:
                warnings.append(
                    f"LABEL R{cell_info['row']}C{cell_info['column']}: "
                    f"\"{in_text}\" overridden as \"{out_text[:50]}\""
                )
    return warnings


def _build_cell_index(inspect_data: dict):
    """From inspect JSON, build: cell_ref[(r,c)]=cell_info, label_cells set, placeholder_map."""
    cell_ref = {}
    label_cells = set()
    placeholder_map = {}
    if not inspect_data:
        return cell_ref, label_cells, placeholder_map
    for table in inspect_data.get("tables", []):
        for ci in table.get("cells", []):
            key = (ci["row"], ci["column"])
            cell_ref[key] = ci
            if ci.get("is_label"):
                label_cells.add(key)
            for p in ci.get("paragraphs", []):
                for rn in p.get("runs", []):
                    for ph in re.findall(r'\{\{[^}]+\}\}', rn.get("text_preview", "")):
                        if ph not in placeholder_map:
                            placeholder_map[ph] = key
    return cell_ref, label_cells, placeholder_map


def _get_fmt_from_ref(cell_ref_key, row, col, inspect_data):
    """Extract font_name, size_pt, bold, east_asia, alignment from the first non-empty run."""
    ci = None
    for table in inspect_data.get("tables", []):
        for c in table.get("cells", []):
            if c["row"] == row and c["column"] == col:
                ci = c
                break
        if ci:
            break
    if not ci:
        return None, None, None, None, None

    # Get alignment from first paragraph
    alignment = None
    for p in ci.get("paragraphs", []):
        if p.get("alignment"):
            alignment = p["alignment"]
            break

    # Get font info from first non-empty run
    for p in ci.get("paragraphs", []):
        for rn in p.get("runs", []):
            if rn.get("text_preview", "").strip():
                return (rn.get("font_name"),
                        rn.get("font_size_pt"),
                        rn.get("bold"),
                        rn.get("east_asia"),
                        alignment)

    return None, None, None, None, None


def fill_with_inspect(template_path: Path, data_path: Path, output_path: Path,
                      inspect_data: dict = None):
    """Fill template using inspect data for exact formatting."""
    if not HAS_DOCX:
        return {"error": "Missing dependencies: python-docx, docxtpl"}

    result = {
        "success": False, "template": str(template_path), "output": str(output_path),
        "placeholders_filled": [], "placeholders_missing": [], "warnings": [],
    }

    cell_ref, label_cells, placeholder_map = _build_cell_index(inspect_data)

    suffix = template_path.suffix.lower()
    if suffix == '.doc':
        conv = _convert_to_docx(template_path)
        if not conv:
            result["error"] = "Cannot process .doc. Install LibreOffice or save as .docx."
            return result
        template_path = conv

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        result["error"] = f"Cannot read data: {e}"
        return result

    try:
        shutil.copy(template_path, output_path)
        doc = DocxTemplate(output_path)
        doc.render(data)
        doc.save(output_path)
    except Exception as e:
        result["error"] = f"docxtpl render failed: {e}"
        return result

    try:
        final_doc = Document(output_path)

        for t_idx, table in enumerate(final_doc.tables):
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    key = (r_idx, c_idx)

                    # PRESERVE label cells — do NOT modify (fix 2)
                    if inspect_data and key in label_cells:
                        orig = cell_ref[key].get("text", "")
                        cur = cell.text.strip()
                        if cur and cur != orig:
                            # Label was overwritten — flag warning
                            # Attempt to restore original text
                            cell.paragraphs[0].clear()
                            run = cell.paragraphs[0].add_run(orig)
                        continue

                    # Apply template-correct formatting from inspect data (fix 1, 5)
                    ref = cell_ref.get(key)
                    if ref and inspect_data:
                        fname, fsize, fbold, fea, falign = _get_fmt_from_ref(
                            ref, r_idx, c_idx, inspect_data)
                        for para in cell.paragraphs:
                            # Apply paragraph alignment (fix 2.1)
                            fill_utils.set_paragraph_alignment(para, falign)
                            # Apply first-line indent for body paragraphs (fix 2.2)
                            fill_utils.apply_first_line_indent(para)
                            for run in para.runs:
                                fill_utils.set_run_font(
                                    run, font_name=fname, font_size_pt=fsize,
                                    bold=fbold, east_asia=fea)

        final_doc.save(output_path)

        # Post-fill diff check
        if inspect_data:
            check = Document(output_path)
            result["warnings"] = _compare_with_inspect(check, inspect_data)

        missing = _verify_no_missing_placeholders(Document(output_path))
        result["placeholders_missing"] = missing
        result["success"] = True

    except Exception as e:
        result["error"] = f"Post-processing failed: {e}"

    return result


def verify_original_unchanged(template_path: Path, original_hash: str) -> bool:
    with open(template_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest() == original_hash


# Backward-compatible alias for tests
fill_template = fill_with_inspect


def main():
    parser = argparse.ArgumentParser(description='Fill DOCX template (requires inspect data)')
    parser.add_argument('--template', '-t', required=True)
    parser.add_argument('--data', '-d', required=True)
    parser.add_argument('--output', '-o', required=True)
    parser.add_argument('--inspect', help='JSON from inspect_template.py (required for correct formatting)')
    parser.add_argument('--style', choices=['perfect', 'normal'], default='normal')
    args = parser.parse_args()

    template_path = Path(args.template)
    data_path = Path(args.data)
    output_path = Path(args.output)

    for p, label in [(template_path, 'Template'), (data_path, 'Data')]:
        if not p.exists():
            print(f"Error: {label} not found: {p}", file=sys.stderr); sys.exit(1)

    with open(template_path, 'rb') as f:
        original_hash = hashlib.sha256(f.read()).hexdigest()

    inspect_data = None
    if args.inspect:
        ip = Path(args.inspect)
        if ip.exists():
            with open(ip, 'r', encoding='utf-8') as f:
                inspect_data = json.load(f)
            if inspect_data.get("summary", {}).get("label_cells", 0) > 0:
                print(f"Preserving {inspect_data['summary']['label_cells']} label cells", file=sys.stderr)

    result = fill_with_inspect(template_path, data_path, output_path, inspect_data)

    if not verify_original_unchanged(template_path, original_hash):
        print("Error: Original template was modified!", file=sys.stderr); sys.exit(1)

    if result.get("warnings"):
        for w in result["warnings"]:
            print(f"WARNING: {w}", file=sys.stderr)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 1)


if __name__ == '__main__':
    main()
