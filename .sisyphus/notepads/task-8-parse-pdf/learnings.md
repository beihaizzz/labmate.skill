Learnings from T8: parse_pdf.py implementation.
- Used pdfplumber for text extraction and scanned detection via empty total text.
- Used pymupdf4llm for Markdown conversion; added graceful error handling for conversion.
- Output schema includes filename, page_count, text_by_page, markdown, is_scanned, warning.
