Decisions:
- Use pdfplumber for robust text extraction across PDF pages.
- Detect scanned PDFs by checking if total extracted text is empty; set is_scanned flag and warning SCANNED_PDF_DETECTED.
- Use pymupdf4llm to convert extracted PDF to Markdown; fallback to error message if conversion fails.
