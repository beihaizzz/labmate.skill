# Troubleshooting Guide

Common issues when generating lab report DOCX files, with symptom → diagnosis → fix flow.

## 表格溢出页面

**现象**：打开生成报告后，表格超出 Word 页面右侧边界，左侧文字被截断。

### 排查优先级（重要！先内容隔离再改结构）

1. **内容隔离**：逐段删除内容，定位问题文字
   - 每删除一段就刷新 Word 查看效果
   - 锁定具体段落或字符串后进入下一步
2. **检查 ASCII 字符串**：问题段落是否含连续 ≥50 字符无空格 ASCII 代码？
   - 使用 `fill_utils.detect_long_ascii_block(text)` 检测
   - 若是 → 将代码写成多行缩进格式（见 de-ai-style-guide.md 代码段落格式章节）
   - 若否 → 检查图片宽度、列宽设置
3. **生成后验证**：运行 `validate_docx.py --input report.docx` 检查 `long_line_check` 状态

**反面教材**：反复调整图片宽度（5.2in→4.5in）、修改表格列宽、缩短段落文字，而不定位问题内容 → 8+ 轮无用迭代。

## 图片图释位置异常

**现象**：图释文字堆到单元格末尾，而非紧跟在图片下方。

**诊断**：是否使用 `cell.add_paragraph()` 手动添加图释？

**修复**：使用 `fill_utils.insert_image_or_placeholder()`，其内部用 `insert_paragraph_after` 在图片段落后立即插入图释段落。

## 行首空段落

**现象**：clear_cell 后第一行出现空白段落。

**诊断**：是否手动调用 `cell.paragraphs[0].clear()` + `add_run()`？

**修复**：使用 `fill_utils.fill_cell_safe()` 或 `fill_utils.add_chinese_body_para()`，两者均复用第一个段落写内容，不会产生空首行。

## 通用原则

- **不要自写填充代码**：单元格填充/图片插入/正文写入均有现成 `fill_utils` 函数
- **先 inspect 再动手**：运行 `inspect_template.py` 并保存结果到 `.labmate/template-inspect.json`
- **确认范围**：多实验项目填充前联系用户确认本次改哪个实验