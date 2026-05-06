# Template Patterns Reference

How to create and use DOCX templates with the LabMate skill. Covers placeholder syntax, common field names, table layouts, CJK font handling, and document structure.

---

## Placeholder Syntax

LabMate uses **Jinja2** template syntax, processed by `docxtpl` (which wraps `python-docx`).

### Standard Placeholder

```
{{placeholder}}
```

Double curly braces with the placeholder name inside. The name must match a key in the template data JSON exactly, including CJK characters.

### Example in a DOCX Paragraph

In the DOCX file, a paragraph might contain:

```
姓名：{{姓名}}    学号：{{学号}}    学院：{{学院}}
```

When rendered with `fill_template.py`, `{{姓名}}` is replaced with the actual value from the data JSON.

### Example in a Table Cell

Placeholders work inside table cells too:

| 项目 | 内容 |
|------|------|
| 实验名称 | {{实验名称}} |
| 实验日期 | {{实验日期}} |
| 实验地点 | {{实验地点}} |

### Important Rules

1. **No spaces inside braces**: `{{姓名}}` not `{{ 姓名 }}`. The parser uses the regex `\{\{([^}]+)\}\}`, which rejects `{{ 姓名 }}` because the space becomes part of the key.
2. **Exact key match**: The placeholder name must exactly match a key in `template-data.json`. `{{实验名称}}` requires a key `"实验名称"`, not `"实验名"` or `"experiment_name"`.
3. **No nested expressions**: Only simple variable substitution is supported. No `{% if %}` blocks, no `{% for %}` loops, no filters like `{{value|upper}}`.
4. **One placeholder per run**: Avoid splitting a placeholder across multiple DOCX runs. If Word breaks `{{姓名}}` into `{{姓` + `名}}`, the template engine won't find it. Type the placeholder in one go without editing mid-keystroke.

---

## Common Placeholders

### Student Information

| Placeholder | Description | Example Value |
|-------------|-------------|---------------|
| `{{姓名}}` | Student's full name | 张三 |
| `{{学号}}` | Student ID number | 2024001 |
| `{{学院}}` | College or faculty | 物理学院 |
| `{{专业}}` | Major or discipline | 应用物理 |
| `{{班级}}` | Class or tutor group | 物理2401 |

### Experiment Metadata

| Placeholder | Description | Example Value |
|-------------|-------------|---------------|
| `{{课程名}}` | Course name | 大学物理实验 |
| `{{实验名称}}` | Experiment title | 电阻的测量 |
| `{{实验日期}}` | Date of experiment | 2025-04-24 |
| `{{实验地点}}` | Lab room or location | 物理实验楼301 |

### Experiment Content

| Placeholder | Description | Example Value |
|-------------|-------------|---------------|
| `{{实验目的}}` | Objectives of the experiment | 掌握伏安法测电阻的原理和方法 |
| `{{实验原理}}` | Theoretical basis | 根据欧姆定律 R = U/I... |
| `{{实验器材}}` | Equipment and materials list | 直流稳压电源、电压表、电流表... |
| `{{实验步骤}}` | Step-by-step procedure | 1. 按电路图连接电路\n2. 调节电源... |
| `{{实验数据}}` | Raw measurement data | 电压/V: 3.0, 电流/mA: 15.2... |
| `{{实验结果}}` | Processed results | 测得电阻值为 197.4Ω |
| `{{实验结论}}` | Conclusions and analysis | 伏安法测电阻结果与标称值接近 |

---

## Table-Based Info Section Pattern

Most Chinese university lab report templates use a table at the top for student and experiment info. Here is the standard pattern:

```
┌──────────┬──────────────────┬──────────┬──────────────────┐
│   姓名   │    {{姓名}}      │   学号   │    {{学号}}       │
├──────────┼──────────────────┼──────────┼──────────────────┤
│   学院   │    {{学院}}      │   专业   │    {{专业}}       │
├──────────┼──────────────────┼──────────┼──────────────────┤
│   班级   │    {{班级}}      │ 实验日期 │    {{实验日期}}   │
├──────────┼──────────────────┼──────────┼──────────────────┤
│ 课程名   │    {{课程名}}    │ 实验地点 │    {{实验地点}}   │
└──────────┴──────────────────┴──────────┴──────────────────┘
```

### How to Create This in Word

1. Insert a table with 4 rows and 4 columns
2. Merge cells as needed for wider fields
3. Place labels in odd columns, placeholders in even columns
4. Set label cells to bold (黑体), value cells to regular (宋体)
5. Apply borders: all inner lines thin, outer border medium

### DOCX XML Structure (Simplified)

The table cells contain runs like:

```xml
<w:tc>
  <w:p>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
      </w:rPr>
      <w:t>{{姓名}}</w:t>
    </w:r>
  </w:p>
</w:tc>
```

The `w:eastAsia` attribute is critical. Without it, CJK characters may render in a fallback font.

---

## CJK Font Best Practices

### The Problem

Microsoft Word stores font information in `w:rFonts` with three attributes:

- `w:ascii`: Font for Latin characters (A-Z, 0-9)
- `w:hAnsi`: Font for high ANSI characters (extended Latin)
- `w:eastAsia`: Font for CJK characters (Chinese, Japanese, Korean)

If `w:eastAsia` is not set, Word falls back to a system default, which varies by OS and locale. This causes inconsistent rendering across machines.

### The Solution

The `fill_template.py` script automatically sets CJK fonts on all runs containing Chinese characters:

```python
def set_cjk_font(run, font_name='宋体'):
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
```

This sets both `w:ascii` and `w:eastAsia` to the same font, ensuring consistent rendering.

### Font Conventions

| Context | Font | Usage |
|---------|------|-------|
| Body text | 宋体 (SimSun) | Default for all paragraph content |
| Headings | 黑体 (SimHei) | Section titles: 实验目的, 实验原理, etc. |
| Labels | 黑体 (SimHei) | Table header cells: 姓名, 学号, etc. |
| Data | 宋体 (SimSun) | Measurement values, observations |
| Code/formulas | Times New Roman | Mathematical expressions, variable names |

### Template Creation Tips

1. Set the default font for the entire document to 宋体 before adding content
2. Apply 黑体 only to heading styles and label cells
3. Do not use Calibri or other Western fonts as the default, they produce poor CJK rendering
4. If mixing formulas with Chinese text, use Times New Roman for formula runs and 宋体 for Chinese runs in the same paragraph

---

## Common Template Structure

A standard Chinese university lab report follows this order:

### 1. Cover / Info Table

The top section with student and experiment metadata. Usually a bordered table (see Table-Based Info Section Pattern above).

### 2. 实验目的 (Experiment Purpose)

A short paragraph or numbered list stating what the experiment aims to achieve. Typically 2-4 objectives.

### 3. 实验原理 (Experiment Principles)

The theoretical background. May include:
- Formulas (use equation editor or plain text)
- Circuit diagrams (insert as images)
- Brief explanations of the underlying physics/chemistry

### 4. 实验器材 (Experiment Equipment)

A list or table of equipment used. Common format:

| 序号 | 器材名称 | 规格 | 数量 |
|------|----------|------|------|
| 1 | 直流稳压电源 | 0-30V | 1 |
| 2 | 电压表 | 0-3V | 1 |

### 5. 实验步骤 (Experiment Steps)

Numbered procedure. Each step should be a clear, actionable instruction. This section maps directly to the progress tracking in Guide Mode.

### 6. 实验数据 (Experiment Data)

Raw measurements, usually in a table:

| 测量次数 | 电压 U/V | 电流 I/mA | 电阻 R/Ω |
|----------|----------|-----------|-----------|
| 1 | 3.0 | 15.2 | 197.4 |
| 2 | 6.0 | 30.5 | 196.7 |

### 7. 实验结果 (Experiment Results)

Processed data: calculations, averages, error analysis. May include:
- Computed values
- Error percentages
- Comparison with theoretical values

### 8. 实验结论 (Experiment Conclusion)

A short paragraph summarizing findings. Should reference specific data points from the results section.

---

## Placeholder Detection

The `parse_docx.py` script detects placeholders using this regex:

```python
re.findall(r'\{\{([^}]+)\}\}', text)
```

It searches both paragraphs and table cells. The returned list is deduplicated.

### Running Placeholder Detection

```bash
python scripts/parse_docx.py --input template.docx
```

The `placeholders` field in the output lists all unique `{{...}}` patterns found. Use this to verify your template has all expected placeholders and to build the corresponding data JSON.

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Placeholder not detected | Split across runs in DOCX | Retype the placeholder in one go |
| Placeholder detected but not replaced | Key missing from data JSON | Add the key to `template-data.json` |
| Extra spaces in placeholder | `{{ 姓名 }}` instead of `{{姓名}}` | Remove spaces inside braces |
| Placeholder in header/footer | `parse_docx.py` only scans body | Move to body or handle separately |

---

## Template Data JSON Schema

The complete data structure (defined in `schemas.md` and `schemas.py`):

```json
{
  "姓名": "string",
  "学号": "string",
  "学院": "string",
  "专业": "string",
  "班级": "string",
  "课程名": "string",
  "实验名称": "string",
  "实验日期": "string",
  "实验地点": "string",
  "实验目的": "string",
  "实验原理": "string",
  "实验器材": "string",
  "实验步骤": "string",
  "实验数据": "string",
  "实验结果": "string",
  "实验结论": "string"
}
```

All fields are strings. For multi-line content (steps, data), use `\n` for line breaks. The template engine preserves these when rendering.

### Minimal Required Fields

Not every template uses every field. The minimum required set depends on the template's placeholders. Run `parse_docx.py` to discover which fields your template needs, then provide at least those.

### Fallback Values

If a field cannot be filled, use `"暂无"` rather than an empty string. Empty strings can collapse table cells and break layouts.