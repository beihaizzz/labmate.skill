---
name: lab-report
description: |
  Lab Report skill for university students. Helps complete lab experiments with two modes: 
  Guide Mode (walk through experiment steps, remind screenshots) and Work Mode (fill templates, 
  generate reports). Triggers on: lab report, 实验报告, experiment report, /lab-report,
  实验指导, .docx template, .pdf guide, experiment writeup.
metadata:
  openclaw:
    emoji: "📝"
    requires:
      bins: ["python3"]
    install:
      - id: "python-docx"
        kind: "pip"
        package: "python-docx"
      - id: "docxtpl"
        kind: "pip"
        package: "docxtpl"
---

# Lab Report Skill

## Overview
Lab Report helps university students complete experiments and write reports. Two modes:
- **Guide Mode**: AI reads your experiment guide (PDF/DOCX/PPTX), shows all steps, tracks your progress via `.lab-report/progress.json`, reminds you to take screenshots at key points, and provides step-by-step help when stuck. Say "继续" to sync progress.
- **Work Mode**: AI reads your report template (DOCX with `{{placeholders}}`), extracts experiment content from Guide Mode progress OR your description, fills the template using docxtpl, and generates a new Word file. Original template is NEVER modified.

## Quick Start
1. Create a folder for your course experiment
2. Place all materials in it (experiment guide PDF/DOCX/PPTX, report template DOCX)
3. Open OpenCode in that folder
4. Run `/lab-report init` to initialize
5. Start Guide Mode or Work Mode

## /lab-report init
Initializes the project. Auto-discovers course materials, finds/creates `学生信息.md`, creates `.lab-report/` directory. Supports `--git` for automatic version control.

## Guide Mode Workflow
See `references/guide-mode-workflow.md` for detailed workflow.

Summary:
1. Parse experiment guide → extract all steps
2. Display all steps with notes and screenshot reminders
3. Student completes steps independently
4. AI syncs progress when student says "继续"
5. When student has questions about a step → step-by-step guidance
6. Progress saved to `.lab-report/progress.json`

## Work Mode Workflow
See `references/work-mode-workflow.md` for detailed workflow.

Summary:
1. **Confirm metadata**: AI asks for experiment date, location, teacher, group members using `question` tool
2. **Ask style**: Offer `perfect` (detail) or `normal` (standard, 90+)
3. Check if `.lab-report/progress.json` exists (from Guide Mode)
4. Extract experiment data from progress OR ask student to describe
5. **Analyze photos**: Scan directory for experiment photos/videos → `read`/`look_at` each to extract code values, wiring details, phenomenon
6. **⭐ Inspect template FIRST**: Run `scripts/inspect_template.py --input template.docx --format human` — dump exact cell-level formatting (font/size/bold/eastAsia/alignment) before writing any code
7. Parse template DOCX → identify `{{placeholders}}`
8. Build JSON data context from student info + experiment metadata + photo analysis + inspect data
9. Call `scripts/fill_template.py --inspect .lab-report/template-inspect.json` to generate report
   - Script auto-preserves label cells (does NOT overwrite "提交文档" etc.)
   - Script applies formatting from inspect data only (no guessing font/size/eastAsia)
   - Post-fill diff check detects accidental overwrites
10. Generate new Word file (original template untouched)
11. **Git 管理**：默认仅报告文件位置（留在 Changes 面板）。`--stage` 暂存、`--commit` 提交

## File Format Support
| Format | Read | Script |
|--------|------|--------|
| PDF | pdfplumber + pymupdf4llm | `scripts/parse_pdf.py` |
| DOCX | python-docx | `scripts/parse_docx.py` |
| PPTX | python-pptx | `scripts/parse_pptx.py` |

Scanned PDFs (image-only) are detected and reported. Ask user whether to skip, attempt OCR, or enter text manually.

## Student Info Management
`学生信息.md` stores reusable student info:
- 姓名, 学号, 学院, 专业, 班级
- Auto-discovered from CWD upward (up to 3 parent dirs)
- Found? → Auto-load. Not found? → Ask user or create with `scripts/student_info.py --create`
- Copy this file to other course folders for reuse

## Report Styles
Two styles, both apply de-AI guidelines:
- `normal`: 标准实验报告。内容完整、结构清晰、语言规范，老师看了能给 90+ 分。日常使用的主要风格。
- `perfect`: 极少数场景使用。尽最大可能详尽，覆盖所有细节和可能情况，适合特别重要的提交。
- Both: No AI signature words (首先, 其次, 最后...), natural paragraph flow, no bullet lists

## Scripts Reference
Run scripts via `uv run --with <pkgs> python scripts/<name>.py`:

| Script | Purpose |
|--------|---------|
| `check_deps.py` | Check uv, Python, packages |
| `student_info.py` | Discover/create 学生信息.md |
| `parse_pdf.py` | Extract text from PDF |
| `parse_docx.py` | Parse DOCX + placeholders |
| `parse_pptx.py` | Extract text from PPTX |
| `init_project.py` | Orchestrate initialization |
| `fill_template.py` | Fill DOCX template |
| `progress_manager.py` | Manage progress.json |
| `git_manager.py` | Git management (default: report status) |

## Troubleshooting
- **Chinese text shows as boxes**: CJK font not set. Scripts auto-set `w:eastAsia` but verify with `python -c "from docx import Document; ..."`
- **Scanned PDF detected**: PDF has no text layer. Ask user to provide text version or manually enter content.
- **Placeholders not replaced**: Check that template uses `{{placeholder}}` syntax. `scripts/parse_docx.py` lists all detected placeholders.
- **uv not found**: Install from https://github.com/astral-sh/uv