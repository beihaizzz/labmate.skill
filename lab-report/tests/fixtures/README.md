# Test Fixtures

This directory contains sample PDF files for testing the lab-report application's PDF processing capabilities.

## Fixtures

### `sample_guide.pdf`
A 2-page Chinese experiment guide PDF generated using `fpdf2`. Contains:
- **Page 1**: 实验名称, 实验目的, 实验原理
- **Page 2**: 实验步骤 (7 steps), 注意事项, 截图要求说明

**Purpose**: Tests text extraction from standard PDF documents.
**pdfplumber extraction**: ~490 characters of text

### `sample_guide_scanned.pdf`
A simulated scanned document PDF containing only an image (no text layer). Created using PIL to render text as image and save as PDF.

**Purpose**: Tests detection of scanned documents (image-only PDFs with no extractable text).
**pdfplumber extraction**: 0 characters (correctly identified as scanned)

## Usage

```python
import pdfplumber

# Test standard PDF
with pdfplumber.open("lab-report/tests/fixtures/sample_guide.pdf") as pdf:
    text = "".join(page.extract_text() or "" for page in pdf.pages)

# Test scanned PDF (should detect 0 chars)
with pdfplumber.open("lab-report/tests/fixtures/sample_guide_scanned.pdf") as pdf:
    text = "".join(page.extract_text() or "" for page in pdf.pages)
    is_scanned = len(text.strip()) == 0
```

## Generation

The fixtures were generated using `generate_fixtures.py` in the project root. Run it with:
```bash
python generate_fixtures.py
```