# -*- coding: utf-8 -*-
"""Verify PDF fixtures."""

import pdfplumber

# Test sample_guide.pdf
p1 = 'lab-report/tests/fixtures/sample_guide.pdf'
t1 = ''.join(pg.extract_text() or '' for pg in pdfplumber.open(p1).pages)
print(f'sample_guide.pdf: {len(t1)} chars extracted - {"PASS" if len(t1) > 50 else "FAIL"} (expected >50)')

# Test sample_guide_scanned.pdf
p2 = 'lab-report/tests/fixtures/sample_guide_scanned.pdf'
t2 = ''.join(pg.extract_text() or '' for pg in pdfplumber.open(p2).pages)
print(f'sample_guide_scanned.pdf: {len(t2)} chars extracted - {"PASS" if len(t2) == 0 else "FAIL"} (expected 0)')
print(f'Scanned detection works: {len(t2.strip()) == 0}')