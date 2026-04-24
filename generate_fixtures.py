# -*- coding: utf-8 -*-
"""Generate sample PDF fixtures for testing."""

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
import os

FIXTURES_DIR = "lab-report/tests/fixtures"

class ChinesePDF(FPDF):
    """FPDF with UTF-8 support."""
    def __init__(self):
        super().__init__()
        self.add_font('NotoSansCJK', '', 'C:/Windows/Fonts/msyh.ttc', uni=True)
        # Fallback to default if CJK font not available
        try:
            self.set_font('NotoSansCJK', '', 10)
        except Exception:
            self.set_font('Helvetica', '', 10)

def create_sample_guide():
    """Create a 2-page Chinese experiment guide PDF."""
    pdf = ChinesePDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1: 实验概述
    pdf.add_page()
    pdf.set_font('NotoSansCJK', '', 16)
    pdf.cell(0, 12, '大学物理实验报告', ln=True, align='C')
    pdf.ln(5)

    pdf.set_font('NotoSansCJK', '', 12)
    pdf.cell(0, 10, '实验名称：霍尔效应实验', ln=True)
    pdf.ln(3)
    pdf.cell(0, 10, '实验目的：', ln=True)
    pdf.set_font('NotoSansCJK', '', 10)
    pdf.multi_cell(0, 7, '1. 理解霍尔效应的工作原理\n2. 掌握测量霍尔系数的方法\n3. 了解霍尔元件在磁场测量中的应用')
    pdf.ln(3)
    pdf.set_font('NotoSansCJK', '', 12)
    pdf.cell(0, 10, '实验原理：', ln=True)
    pdf.set_font('NotoSansCJK', '', 10)
    pdf.multi_cell(0, 7, '当导体或半导体置于磁场中，且电流垂直于磁场方向通过时，在导体两侧会产生横向电势差，这种现象称为霍尔效应。霍尔电压 VH 与电流 I 和磁感应强度 B 的乘积成正比，比例系数即为霍尔系数。')

    # Page 2: 实验步骤
    pdf.add_page()
    pdf.set_font('NotoSansCJK', '', 12)
    pdf.cell(0, 10, '实验步骤：', ln=True)
    pdf.set_font('NotoSansCJK', '', 10)
    pdf.multi_cell(0, 7, '步骤1：按图连接电路，确认接线无误后通电\n步骤2：调节直流稳压电源，使电流表读数为设定值\n步骤3：将霍尔元件置于磁场中心位置\n步骤4：记录电压表读数，改变磁场方向再次测量\n步骤5：重复测量5次，计算霍尔系数平均值\n步骤6：绘制 VH-I 和 VH-B 关系曲线\n步骤7：整理数据，完成实验报告')

    pdf.ln(5)
    pdf.set_font('NotoSansCJK', '', 12)
    pdf.cell(0, 10, '注意事项：', ln=True)
    pdf.set_font('NotoSansCJK', '', 10)
    pdf.multi_cell(0, 7, '1. 电流不得超过额定值，以免损坏霍尔元件\n2. 测量时应保持磁场方向与霍尔元件片法线方向垂直\n3. 环境温度变化会影响测量结果，应在恒温条件下进行')

    pdf.ln(3)
    pdf.set_font('NotoSansCJK', '', 12)
    pdf.cell(0, 10, '截图要求说明：', ln=True)
    pdf.set_font('NotoSansCJK', '', 10)
    pdf.multi_cell(0, 7, '实验过程中需要截图记录：电路连接图、仪器读数界面、数据曲线图。请使用截图工具或按 PrintScreen 键获取图像，保存为 PNG 格式备用。')

    output_path = os.path.join(FIXTURES_DIR, "sample_guide.pdf")
    pdf.output(output_path)
    print(f"Created: {output_path}")
    return output_path

def create_scanned_pdf():
    """Create a scanned-style PDF (image only, no text)."""
    # Create a simple grayscale image with text rendered as image
    width, height = 595, 842  # A4 size in pixels at 72 DPI
    img = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(img)

    # Try to use a font, fallback to default
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
        small_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw text as image (simulating scanned content)
    y = 80
    draw.text((72, y), "大学物理实验报告", fill=0, font=font)
    y += 50
    draw.text((72, y), "实验名称：霍尔效应实验", fill=0, font=small_font)
    y += 30
    draw.text((72, y), "实验目的：", fill=0, font=small_font)
    y += 25
    draw.text((72, y), "1. 理解霍尔效应的工作原理", fill=0, font=small_font)
    y += 20
    draw.text((72, y), "2. 掌握测量霍尔系数的方法", fill=0, font=small_font)
    y += 20
    draw.text((72, y), "3. 了解霍尔元件在磁场测量中的应用", fill=0, font=small_font)

    # Save as PDF using Pillow's PDF save
    output_path = os.path.join(FIXTURES_DIR, "sample_guide_scanned.pdf")
    img.save(output_path, "PDF", resolution=72)
    print(f"Created: {output_path}")
    return output_path

def test_extraction(pdf_path, expected_min_chars):
    """Test that pdfplumber can extract text."""
    import pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text
            char_count = len(text.strip())
            return char_count, char_count >= expected_min_chars
    except Exception as e:
        return 0, False

if __name__ == "__main__":
    os.makedirs(FIXTURES_DIR, exist_ok=True)

    print("=== Generating PDF fixtures ===")
    guide_path = create_sample_guide()
    scanned_path = create_scanned_pdf()

    print("\n=== Verification ===")
    # Test sample_guide.pdf
    count, passed = test_extraction(guide_path, 50)
    result = "PASS" if passed else "FAIL"
    print(f"sample_guide.pdf: {count} chars extracted [{result}] (expected >= 50)")

    # Test sample_guide_scanned.pdf
    count, passed = test_extraction(scanned_path, 50)
    result = "PASS" if passed else "FAIL (expected 0 chars - scanned document)"
    print(f"sample_guide_scanned.pdf: {count} chars extracted [{result}]")

    print("\nDone!")