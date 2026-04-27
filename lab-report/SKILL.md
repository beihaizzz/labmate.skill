---
name: lab-report
description: |
  Lab Report skill for university students. Helps complete lab experiments with two modes.
  Trigger: `/lab` command. Subcommands: `-init`, `-work`, `-guide`, `-update`, `-help`.
  Keywords: lab report, 实验报告, experiment report, /lab-report, /lab,
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
4. Run `/lab -init` to initialize
5. Start Guide Mode or Work Mode

## Commands

所有命令以 `/lab` 触发：

| 命令 | 作用 |
|------|------|
| `/lab -init` | 初始化项目。自动发现资料、创建 project.md、配置环境。`/lab -init --git` 启用版本管理 |
| `/lab -work` | 强制进入 Work Mode。直接生成实验报告 |
| `/lab -guide` | 强制进入 Guide Mode。开始指导实验 |
| `/lab -update` | 重新扫描项目目录。用于新增实验或大量文件变更后，刷新 project.md 和 .lab-report/config.json |
| `/lab -help` | 显示所有命令和简要说明 |

## Session Startup Protocol

每次会话开始时（无论 Guide Mode 还是 Work Mode）：

1. **Read `project.md`** — 了解课程信息、实验进度、通用配置
2. **Read `学生信息.md`** — 获取个人信息
3. **Verify key paths** — 检查 project.md 中引用的文件是否还存在
4. If paths stale → 告知用户并更新 project.md

project.md 是 session 的"快速上下文"——读它即可了解整个项目状态，无需重新扫描整个目录。

## /lab -init
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

## PowerShell 编码规则（Windows 必读）

**绝对禁止以下模式**（在 PowerShell 下含中文的 inline Python 会崩溃）：

```powershell
# ❌ 会导致编码错误，浪费 token
uv run python -c "print('中文')"
uv run python -c "with open('实验.txt') as f: ..."
```

**必须写成文件再执行**：

```powershell
# ✅ 正确做法
Set-Content script.py "print('中文')" -Encoding UTF8
uv run python script.py
```

**原因**: PowerShell 下 `python -c` 的引号嵌套 + UTF-8 编码有已知 bug，中文必炸。写成文件零成本避免，省去每次重试 + 排查的 token 开销。