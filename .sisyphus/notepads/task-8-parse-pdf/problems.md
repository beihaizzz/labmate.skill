Problems / Technical debt:
- If dependencies (pdfplumber, pymupdf4llm) are unavailable, the script returns an error object instead of performing extraction.
- Edge cases: PDFs with unusual encodings or encrypted PDFs may require additional handling.
