"""Formatting utilities for lab-report DOCX template filling.

Shared constants and helper functions so all scripts use consistent formatting.
"""

from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import re

# ── 格式化常量 ────────────────────────────────────────────────────────────────────
FONT_TITLE = '黑体'
FONT_BODY = '宋体'
FONT_CODE = 'Courier New'

# 字号（pt）
SIZE_TABLE0_VALUE = 14      # 表0（学生信息）值单元格
SIZE_H1 = 12                # 一级标题（实验目的、实验要求等）
SIZE_H2 = 11                # 二级标题
SIZE_BODY = 12              # 正文
SIZE_CODE = 9               # 代码/图片提示
SIZE_IMAGE_HINT = 10        # 图片占位标签

# 首行缩进（2 字符，12pt 字号下 = 24pt）
INDENT_2CHAR = Pt(24)

# ── 段落角色识别 ──────────────────────────────────────────────────────────────────
_LIST_ITEM_PATTERNS = re.compile(
    r'^\s*('
    r'\d+[．\.、]'            # 1.  1、  １．
    r'|[a-zA-Z][\)\.]'       # a)  b.
    r'|[（\(][一二三四五六七八九十\d]+[）\)]'  # （1） (一)
    r'|[一二三四五六七八九十]+[、．\.]'         # 一、  二．
    r')\s*'
)


def is_list_item(text: str) -> bool:
    """Check if text looks like a numbered/bulleted list item."""
    return bool(_LIST_ITEM_PATTERNS.match(text.strip()))


def is_body_paragraph(text: str, min_len: int = 20) -> bool:
    """Check if text is a descriptive body paragraph (vs title/list/hint)."""
    t = text.strip()
    if not t:
        return False
    if is_list_item(t):
        return False
    if len(t) < min_len:
        return False
    if t.startswith('[') and t.endswith(']'):
        return False
    if t.startswith('{{') and t.endswith('}}'):
        return False
    return True


# ── Run 级格式设置 ────────────────────────────────────────────────────────────────

def set_run_font(run, font_name=None, font_size_pt=None, bold=None, east_asia=None):
    """Set font properties on a run. Only sets non-None values."""
    if font_name:
        run.font.name = font_name
    if font_size_pt:
        run.font.size = Pt(font_size_pt)
    if bold is not None:
        run.font.bold = bold
    if east_asia:
        rPr = run._element.find(qn('w:rPr'))
        if rPr is None:
            rPr = run._element.makeelement(qn('w:rPr'), {})
            run._element.insert(0, rPr)
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = rPr.makeelement(qn('w:rFonts'), {})
            rPr.append(rFonts)
        rFonts.set(qn('w:eastAsia'), east_asia)


def set_paragraph_alignment(para, alignment_str: str | None):
    """Map alignment string from inspect output to WD_ALIGN_PARAGRAPH."""
    if not alignment_str:
        return
    mapping = {
        'CENTER': WD_ALIGN_PARAGRAPH.CENTER,
        'LEFT': WD_ALIGN_PARAGRAPH.LEFT,
        'RIGHT': WD_ALIGN_PARAGRAPH.RIGHT,
        'JUSTIFY': WD_ALIGN_PARAGRAPH.JUSTIFY,
    }
    align = mapping.get(alignment_str.upper())
    if align is not None:
        para.alignment = align


def apply_first_line_indent(para, indent=INDENT_2CHAR):
    """Apply first-line indent if paragraph is a body paragraph."""
    text = para.text.strip()
    if is_body_paragraph(text):
        para.paragraph_format.first_line_indent = indent


# ── Cell/Paragraph 组织 ──────────────────────────────────────────────────────────

def clear_cell(cell):
    """Clear a cell's content, keeping the cell structure."""
    for p in cell.paragraphs:
        for r in p.runs:
            r.text = ''


def add_run(para, text, font_name=FONT_BODY, font_size_pt=SIZE_BODY,
            bold=False, east_asia=None):
    """Add a formatted run to a paragraph."""
    run = para.add_run(text)
    set_run_font(run, font_name=font_name, font_size_pt=font_size_pt,
                 bold=bold, east_asia=east_asia)
    return run


def heading_run(para, text, font_name=FONT_TITLE, font_size_pt=SIZE_H1):
    """Add a heading run (黑体, bold)."""
    return add_run(para, text, font_name=font_name, font_size_pt=font_size_pt,
                   bold=True, east_asia=font_name)


def body_run(para, text, font_name=FONT_BODY, font_size_pt=SIZE_BODY):
    """Add a body text run."""
    return add_run(para, text, font_name=font_name, font_size_pt=font_size_pt,
                   bold=False, east_asia=font_name)


def image_hint_run(para, label: str):
    """Add a styled image placeholder."""
    from docx.shared import Pt as PtSize
    run = add_run(para, f"\n[{label}]\n", font_name=FONT_BODY,
                  font_size_pt=SIZE_IMAGE_HINT, bold=False, east_asia=FONT_BODY)
    run.italic = True
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return run
