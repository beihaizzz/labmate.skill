#!/usr/bin/env python3
"""Generate section-map.json from filled DOCX — logical ID to cell coordinate mapping."""

import argparse
import json
import sys
from pathlib import Path

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def generate_section_map(input_path: Path, inspect_data: dict = None) -> dict:
    """Map every content block to its table cell coordinates."""
    if not HAS_DOCX:
        return {"error": "Missing dependency: python-docx"}

    result = {
        "report": input_path.name,
        "sections": []
    }

    try:
        doc = Document(str(input_path))
        current_heading = None
        content_counter = {}

        for t_idx, table in enumerate(doc.tables):
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    text = cell.text.strip()
                    if not text:
                        continue

                    if len(text) < 20:
                        # Short text = heading node
                        heading_id = text
                        current_heading = heading_id
                        content_counter = {}  # Reset per heading
                        result["sections"].append({
                            "id": heading_id,
                            "type": "heading",
                            "cells": [{"table": t_idx, "row": r_idx, "col": c_idx}]
                        })
                    else:
                        # Long text = content node
                        if current_heading is None:
                            current_heading = "未分类"
                        n = content_counter.get(current_heading, 0) + 1
                        content_counter[current_heading] = n
                        content_id = f"{current_heading}_{n}"
                        result["sections"].append({
                            "id": content_id,
                            "type": "content",
                            "cells": [{"table": t_idx, "row": r_idx, "col": c_idx}],
                            "text_preview": text[:80]
                        })

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description='Generate section-map.json from filled DOCX')
    parser.add_argument('--input', '-i', required=True, help='Filled DOCX report')
    parser.add_argument('--inspect', help='Inspect JSON (optional, for future use)')
    parser.add_argument('--output', '-o', help='Output JSON path (default: stdout)')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    inspect_data = None
    if args.inspect:
        with open(args.inspect, 'r', encoding='utf-8') as f:
            inspect_data = json.load(f)

    result = generate_section_map(input_path, inspect_data)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"Saved to {args.output}")
    else:
        print(output)

    sys.exit(0 if "error" not in result else 1)


if __name__ == '__main__':
    main()
