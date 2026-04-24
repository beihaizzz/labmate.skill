# lab-report — 实验报告助手 Skill

## TL;DR

> **Quick Summary**: 构建一个 OpenCode Skill，帮助大学生完成实验报告。提供两种模式：Guide Mode（指导学生完成实验）和 Work Mode（自动生成实验报告）。
>
> **Deliverables**:
> - `lab-report/SKILL.md` — 主 Skill 文件
> - `lab-report/scripts/` — 8 个 Python 脚本（文件解析、模板填充、进度管理、Git 集成）
> - `lab-report/references/` — 5 个参考文档（工作流、模板规范、去AI风格指南）
> - `lab-report/assets/` — 2 个资产文件（学生信息模板、默认报告模板）
> - 完整的自动化测试套件 + 测试 fixtures
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES — 5 Waves
> **Critical Path**: T1 → T2 → T8/T9/T10 → T12 → T13 → T15 → T23-T25 → FINAL

---

## Context

### Original Request
构建 lab-report 项目，以 OpenCode Skill 形式帮助大学生完成实验报告。两种使用模式：指导模式（Guide Mode）和工作模式（Work Mode）。通过 `/lab-report init` 初始化，自动发现课程资料，使用 `学生信息.md` 跨课程复用个人信息。

### Interview Summary
**Key Discussions**:
- **Skill 格式**: OpenCode Skill（SKILL.md + scripts/ + references/ + assets/），非 Plugin
- **Guide Mode**: AI 一次性展示所有步骤和注意事项 → 学生自助完成 → 关键步骤提醒截图 → 遇问题逐步引导 → 学生说"继续"时同步进度
- **Work Mode**: 模板填空式 — 读取 `{{placeholder}}` 标记 → docxtpl 填入内容 → 生成新 Word 文件（不修改原始文件）→ 格式完全一致
- **内容来源**: 优先 Guide 模式进度文件，无进度文件则由学生自由描述
- **报告风格**: 完美 / 普通（两种风格均默认融入去 AI 味：减少 AI 特征词、分段叙述不分条）
- **初始化**: `/lab-report init` 斜杠命令 → 自动发现资料 → 信息不足时确认 → `学生信息.md` 复用
- **Git**: 可选功能，自动 `git add` + `git commit` 每次文件变更
- **学生信息 Schema**: 姓名、学号、学院、专业、班级
- **进度持久化**: JSON 状态文件 (`.lab-report/progress.json`)
- **扫描 PDF**: 先尝试文本提取 → 失败则询问用户（跳过/OCR/手动输入）

**Research Findings**:
- **OpenCode Skill 架构**: 渐进式三级加载（元数据 → 正文 → 资源），SKILL.md 正文 <5k 词
- **Word 模板核心问题**: python-docx 无法处理被格式拆分的 run → 必须使用 **docxtpl** (Jinja2 模板引擎)
- **CJK 字体**: 必须设置 `w:eastAsia` 属性，否则中文显示为方框
- **模板安全**: 必须 `shutil.copy` 后操作副本，绝不可修改原始文件
- **路径解析 Bug (#17101)**: Skill 内脚本引用必须使用 CWD 相对路径
- **依赖管理**: 使用 `uv run --with <pkg>` 模式，无需全局安装

### Metis Review
**Identified Gaps** (已解决):
- 模板占位符格式 → 确认为双花括号 `{{}}`，使用 docxtpl
- Work Mode 内容来源 → 两者都支持
- 进度持久化机制 → JSON 状态文件
- 学生信息 Schema → 基础版（5 字段）
- 扫描 PDF 处理 → 混合模式（提取→失败→询问）

**技术纠正**:
- 替换原始 python-docx 为 docxtpl 进行模板渲染
- 新增 `check_deps.py` 预检脚本确保 uv 和依赖可用
- 所有脚本统一 CWD 相对路径约定

---

## Work Objectives

### Core Objective
构建一个完整的、可工作的 OpenCode Skill `lab-report`，学生通过 `/lab-report init` 初始化后，可进入 Guide Mode 完成实验或 Work Mode 生成实验报告。

### Concrete Deliverables
- `lab-report/SKILL.md` — 完整的 Skill 定义文件
- 8 个 Python 脚本：`init_project.py`, `parse_pdf.py`, `parse_docx.py`, `parse_pptx.py`, `fill_template.py`, `progress_manager.py`, `student_info.py`, `git_manager.py`, `check_deps.py`
- 5 个 reference 文档
- 2 个 asset 文件
- 测试套件：覆盖所有核心脚本
- 测试 fixtures：示例 PDF / DOCX / PPTX 文件

### Definition of Done
- [ ] `/lab-report init` 在含课程资料的文件夹中成功初始化
- [ ] Guide Mode 完整流程可走通（步骤展示→进度同步→截图提醒→问题引导）
- [ ] Work Mode 从模板生成格式正确的 Word 报告
- [ ] 中文渲染正确（无方框）
- [ ] 原始模板文件未被修改
- [ ] 所有 Python 脚本测试通过
- [ ] `学生信息.md` 可跨课程复用
- [ ] Git 自动提交正常工作（可选功能）

### Must Have
- Guide Mode：步骤指导 + 进度同步 + 截图提醒
- Work Mode：模板填空 + docxtpl 渲染 + 格式保留
- 初始化自动发现课程资料
- `学生信息.md` 自动发现与复用
- JSON 进度文件持久化
- Python 脚本独立性（每个脚本可单独运行）
- CJK 字体正确处理

### Must NOT Have (Guardrails)
- **绝不修改原始文件** — 所有输出为新文件
- **绝不编造实验数据** — 只填入学生提供的内容
- **不支持 .doc 格式** — v1 仅 .docx
- **不做 OCR** — v1 不集成 Tesseract，扫描 PDF 报告后询问用户
- **不做 LaTeX 支持** — v1 仅 Word
- **不做协同功能** — 单人使用
- **不做自动评分** — 只生成报告，不评价质量
- **不过度工程化去AI** — 用 prompt 指南，不做后处理管道
- **SKILL.md 正文 <5k 词** — 详细流程放 references/
- **不使用 skill 相对路径引用脚本** — 全部 CWD 相对路径

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO（需从零搭建）
- **Automated tests**: YES（TDD for all Python scripts）
- **Framework**: `pytest`（Python 标准测试框架）
- **TDD Workflow**: Each script task follows RED（failing test）→ GREEN（minimal impl）→ REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Python scripts**: Use Bash (`uv run python script.py` + `uv run pytest tests/`) — validate exit codes, stdout/stderr, output file existence
- **Word output**: Use Bash (`uv run --with python-docx python -c "..."`) — verify document structure, placeholder replacement, CJK fonts
- **Skill integration**: Use OpenCode skill loading mechanism — verify skill discovery and invocation

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation + scaffolding, 7 tasks):
├── T1: Project scaffolding + pyproject.toml [quick]
├── T2: JSON schemas（progress, student-info, template-data）[quick]
├── T3: Test fixture — sample PDF guide [quick]
├── T4: Test fixture — sample DOCX template [quick]
├── T5: Test fixture — sample PPT [quick]
├── T6: check_deps.py — 依赖预检脚本 [quick]
└── T7: student_info.py — 学生信息发现/创建 [quick]

Wave 2 (After Wave 1 — file parsers, 4 parallel tasks):
├── T8: parse_pdf.py — PDF 文本提取 [deep]
├── T9: parse_docx.py — Word 文档解析 [deep]
├── T10: parse_pptx.py — PPT 文本提取 [quick]
└── T11: progress_manager.py — JSON 进度管理 [quick]

Wave 3 (After Wave 2 — core logic, 3 parallel tasks):
├── T12: init_project.py — 项目初始化主逻辑 [deep]
├── T13: fill_template.py — docxtpl 模板填空 [deep]
└── T14: git_manager.py — Git 自动提交 [quick]

Wave 4 (After Wave 3 — documentation, 6 parallel tasks):
├── T15: SKILL.md — 主 Skill 文件 [writing]
├── T16: references/guide-mode-workflow.md [writing]
├── T17: references/work-mode-workflow.md [writing]
├── T18: references/template-patterns.md [writing]
├── T19: references/de-ai-style-guide.md [writing]
└── T20: references/report-structure.md [writing]

Wave 5 (After Wave 4 — assets + tests, 5 parallel tasks):
├── T21: assets/学生信息模板.md [quick]
├── T22: assets/report_template.docx [quick]
├── T23: Unit tests — parse_* scripts [unspecified-high]
├── T24: Unit tests — fill_template.py [unspecified-high]
└── T25: Unit tests — progress_manager.py + student_info.py [unspecified-high]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── F1: Plan Compliance Audit (oracle)
├── F2: Code Quality Review (unspecified-high)
├── F3: Real Manual QA (unspecified-high)
└── F4: Scope Fidelity Check (deep)
→ Present results → Get explicit user okay
```

**Critical Path**: T1 → T2 → T8/T9/T10 → T12 → T13 → T15 → T23-T25 → FINAL
**Parallel Speedup**: ~65% faster than sequential
**Max Concurrent**: 7 (Wave 1), 6 (Wave 4)

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.

- [x] 1. Project scaffolding + pyproject.toml

  **What to do**:
  - 创建 `lab-report/` 目录结构：`SKILL.md`, `scripts/`, `references/`, `assets/`, `tests/`, `tests/fixtures/`
  - 创建 `pyproject.toml`，配置 pytest、依赖声明（python-docx, docxtpl, pdfplumber, python-pptx, pymupdf4llm）
  - 创建 `.lab-report/` 作为运行时状态目录（在脚本中动态创建，此处只定义约定）
  - 创建 `.gitignore`（排除 `__pycache__/`, `.pytest_cache/`, `.lab-report/progress.json` 等）
  - 创建 `conftest.py`（pytest 基础配置，fixture 路径定义）

  **Must NOT do**:
  - 不要创建 .doc 格式相关配置
  - 不要引入 Tesseract/OCR 依赖
  - 不要使用 Poetry 或其他包管理器 — 仅 uv + pyproject.toml

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 纯目录结构创建，配置文件模板化，无复杂逻辑
  - **Skills**: [`dev-workflow`]
    - `dev-workflow`: 遵循结构化开发流程，确保项目初始化的规范性

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1（与 T2-T7 并行）
  - **Blocks**: T8, T9, T10, T12, T13（所有后续任务依赖此目录结构）
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `lab-report/` 目录存在且包含所有子目录
  - [ ] `pyproject.toml` 存在且包含正确的依赖声明
  - [ ] `uv run pytest` 可执行（即使 0 tests collected）

  **QA Scenarios**:
  ```
  Scenario: Directory structure verification
    Tool: Bash
    Preconditions: None
    Steps:
      1. ls lab-report/
      2. Assert: SKILL.md exists
      3. Assert: scripts/ directory exists
      4. Assert: references/ directory exists
      5. Assert: assets/ directory exists
      6. Assert: tests/ directory exists
      7. Assert: tests/fixtures/ directory exists
    Expected Result: All directories and SKILL.md placeholder exist
    Evidence: .sisyphus/evidence/task-1-structure.txt

  Scenario: pyproject.toml dependency validation
    Tool: Bash
    Preconditions: Task 1 structure created
    Steps:
      1. cat lab-report/pyproject.toml | grep -E "(docxtpl|pdfplumber|python-docx|python-pptx|pymupdf4llm)"
      2. Assert: all 5 dependencies found in output
    Expected Result: All required dependencies declared in pyproject.toml
    Evidence: .sisyphus/evidence/task-1-deps.txt
  ```

  **Commit**: YES
  - Message: `scaffold: initialize lab-report skill project structure`
  - Files: `lab-report/`, `pyproject.toml`, `.gitignore`, `conftest.py`

- [x] 2. JSON schemas — 定义数据结构

  **What to do**:
  - 创建 `lab-report/references/schemas.md` 定义所有 JSON 数据结构的规范
  - 定义 `progress.json` schema：
    ```json
    {
      "experiment_name": "string",
      "total_steps": "int",
      "current_step": "int",
      "completed_steps": ["int"],
      "screenshots_required": [{"step": "int", "description": "string", "captured": "bool", "path": "string|null"}],
      "notes": {"step_N": "string"},
      "last_updated": "ISO8601 datetime",
      "status": "not_started | in_progress | completed"
    }
    ```
  - 定义 `student-info.json` schema（对应 `学生信息.md` 解析结果）
  - 定义 `template-data.json` schema（填充模板时使用的数据格式）
  - 创建 `lab-report/scripts/schemas.py` — Python dataclass/pydantic 定义，供脚本引用

  **Must NOT do**:
  - 不要用 YAML 作为状态文件格式 — 必须是 JSON
  - 不要引入 pydantic 等重型验证库 — 使用 dataclass + 手动验证

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Schema 定义是纯数据结构设计，无复杂算法
  - **Skills**: [`dev-workflow`]
    - `dev-workflow`: 结构化的开发流程

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1（与 T1, T3-T7 并行）
  - **Blocks**: T8, T9, T11, T12, T13（解析和填充脚本依赖 Schema）
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `references/schemas.md` 包含 3 个完整的 JSON schema 定义
  - [ ] `scripts/schemas.py` 包含对应的 Python dataclass 定义
  - [ ] `uv run python -c "from lab_report.scripts.schemas import ProgressState; print('OK')"` 成功

  **QA Scenarios**:
  ```
  Scenario: Schema import validation
    Tool: Bash
    Preconditions: Task 2 implemented
    Steps:
      1. uv run python -c "
      from pathlib import Path
      import sys
      sys.path.insert(0, 'lab-report/scripts')
      from schemas import ProgressState, StudentInfo, TemplateData
      print('ProgressState fields:', ProgressState.__annotations__)
      print('StudentInfo fields:', StudentInfo.__annotations__)
      print('TemplateData fields:', TemplateData.__annotations__)
      "
      2. Assert: All three classes imported successfully
      3. Assert: ProgressState has expected fields (experiment_name, total_steps, current_step, completed_steps, screenshots_required, notes, last_updated, status)
    Expected Result: All dataclasses import and have correct annotations
    Evidence: .sisyphus/evidence/task-2-schemas.txt
  ```

  **Commit**: YES
  - Message: `feat(schema): define JSON schemas for progress, student info, and template data`
  - Files: `references/schemas.md`, `scripts/schemas.py`

- [x] 3. Test fixture — sample PDF experiment guide

  **What to do**:
  - 创建 `tests/fixtures/sample_guide.pdf` — 模拟实验指导书 PDF
  - 内容（中文）：实验名称、实验目的、实验原理、实验步骤（5-7 步）、注意事项、截图要求
  - 使用 `fpdf2` 或手动创建合法 PDF，确保 pdfplumber 可提取文本
  - 创建 `tests/fixtures/sample_guide_scanned.pdf` — 模拟扫描版 PDF（仅图片，无文本层）
  - 创建 `tests/fixtures/README.md` 说明 fixture 内容和用途

  **Must NOT do**:
  - 不要从网络下载真实实验指导书（版权问题）
  - 扫描版 PDF 只需包含一张图片即可，无需真正扫描

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 创建测试数据，Python PDF 生成
  - **Skills**: [`dev-workflow`]
    - `dev-workflow`: 结构化创建测试资产

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1（与 T1-T2, T4-T7 并行）
  - **Blocks**: T8, T12（parse_pdf 和 init 依赖测试 fixture）
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `tests/fixtures/sample_guide.pdf` 存在且 pdfplumber 可提取 >0 个字符文本
  - [ ] `tests/fixtures/sample_guide_scanned.pdf` 存在且 pdfplumber 提取文本为空
  - [ ] `tests/fixtures/README.md` 存在

  **QA Scenarios**:
  ```
  Scenario: PDF text extraction verification
    Tool: Bash
    Preconditions: Task 3 fixtures created
    Steps:
      1. uv run --with pdfplumber python -c "
      import pdfplumber
      with pdfplumber.open('tests/fixtures/sample_guide.pdf') as pdf:
          text = pdf.pages[0].extract_text()
          print(f'Text length: {len(text) if text else 0}')
          assert text and len(text) > 50, 'Expected >50 chars of extractable text'
      print('PASS: Text extraction successful')
      "
      2. Assert: exit code 0, output contains "PASS"
    Expected Result: Text extracted successfully from sample guide PDF
    Evidence: .sisyphus/evidence/task-3-pdf-text.txt

  Scenario: Scanned PDF detection
    Tool: Bash
    Preconditions: Task 3 fixtures created
    Steps:
      1. uv run --with pdfplumber python -c "
      import pdfplumber
      with pdfplumber.open('tests/fixtures/sample_guide_scanned.pdf') as pdf:
          text = pdf.pages[0].extract_text()
          print(f'Text length: {len(text) if text else 0}')
          assert not text or len(text) == 0, 'Expected empty text (scanned PDF)'
      print('PASS: Scanned PDF correctly yields no text')
      "
      2. Assert: exit code 0, output contains "PASS"
    Expected Result: Scanned PDF yields no extractable text
    Evidence: .sisyphus/evidence/task-3-scanned.txt
  ```

  **Commit**: YES
  - Message: `test(fixtures): add sample PDF experiment guide and scanned variant`
  - Files: `tests/fixtures/sample_guide.pdf`, `tests/fixtures/sample_guide_scanned.pdf`, `tests/fixtures/README.md`

- [x] 4. Test fixture — sample DOCX template

  **What to do**:
  - 创建 `tests/fixtures/sample_template.docx` — 模拟实验报告模板
  - 使用 python-docx 创建，包含 Jinja2 占位符：
    - `{{姓名}}`, `{{学号}}`, `{{学院}}`, `{{专业}}`, `{{班级}}`
    - `{{实验名称}}`, `{{实验日期}}`, `{{实验地点}}`
    - `{{实验目的}}`, `{{实验原理}}`, `{{实验步骤}}`
    - `{{实验数据}}`, `{{实验结果}}`, `{{实验结论}}`
  - 模板需包含：表格（个人信息区域）、段落（实验内容区域）、不同字体/字号
  - 包含至少一个含格式的占位符（如粗体 `{{实验名称}}`），验证 docxtpl 处理格式化占位符能力

  **Must NOT do**:
  - 不要使用 .doc 格式
  - 不要包含 macro/VBA

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 使用 python-docx 生成模板，纯脚本操作
  - **Skills**: [`dev-workflow`]
    - `dev-workflow`: 结构化创建测试资产

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1（与 T1-T3, T5-T7 并行）
  - **Blocks**: T9, T13, T24（parse_docx 和 fill_template 依赖测试 fixture）
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `tests/fixtures/sample_template.docx` 存在
  - [ ] python-docx 可打开并读取段落
  - [ ] 至少包含 10 个 `{{...}}` 占位符
  - [ ] 至少包含一个表格

  **QA Scenarios**:
  ```
  Scenario: Template placeholder verification
    Tool: Bash
    Preconditions: Task 4 fixture created
    Steps:
      1. uv run --with python-docx python -c "
      from docx import Document
      doc = Document('tests/fixtures/sample_template.docx')
      found = []
      for p in doc.paragraphs:
          for r in p.runs:
              found.append(r.text)
      for t in doc.tables:
          for row in t.rows:
              for cell in row.cells:
                  for p in cell.paragraphs:
                      for r in p.runs:
                          found.append(r.text)
      full_text = ' '.join(found)
      placeholders = ['{{姓名}}', '{{学号}}', '{{实验名称}}', '{{实验目的}}', '{{实验步骤}}']
      for p in placeholders:
          assert p in full_text, f'Missing placeholder: {p}'
      print(f'PASS: All {len(placeholders)} required placeholders found')
      "
      2. Assert: exit code 0, output contains "PASS"
    Expected Result: All required placeholders present in template
    Evidence: .sisyphus/evidence/task-4-placeholders.txt
  ```

  **Commit**: YES
  - Message: `test(fixtures): add sample DOCX report template with Jinja2 placeholders`
  - Files: `tests/fixtures/sample_template.docx`

- [x] 5. Test fixture — sample PPT experiment guide

  **What to do**:
  - 创建 `tests/fixtures/sample_guide.pptx` — 模拟 PPT 格式实验指导书
  - 包含 5-7 张幻灯片：实验名称、实验目的、实验原理、实验步骤（分步）、注意事项
  - 使用 python-pptx 创建，确保 python-pptx 可提取文本
  - 幻灯片中包含文本、标题、至少一张图片占位符

  **Must NOT do**:
  - 不要使用 PPT 动画/过渡效果
  - 不要嵌入视频/音频

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 使用 python-pptx 生成测试 PPT，纯脚本操作
  - **Skills**: [`dev-workflow`]
    - `dev-workflow`: 结构化创建测试资产

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1（与 T1-T4, T6-T7 并行）
  - **Blocks**: T10, T12（parse_pptx 和 init 依赖测试 fixture）
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `tests/fixtures/sample_guide.pptx` 存在
  - [ ] python-pptx 可打开并提取文本
  - [ ] 包含 >=5 张幻灯片

  **QA Scenarios**:
  ```
  Scenario: PPT text extraction verification
    Tool: Bash
    Preconditions: Task 5 fixture created
    Steps:
      1. uv run --with python-pptx python -c "
      from pptx import Presentation
      prs = Presentation('tests/fixtures/sample_guide.pptx')
      total_text = ''
      for slide in prs.slides:
          for shape in slide.shapes:
              if shape.has_text_frame:
                  total_text += shape.text_frame.text
      print(f'Slides: {len(prs.slides)}, Total text length: {len(total_text)}')
      assert len(prs.slides) >= 5, 'Expected >=5 slides'
      assert len(total_text) > 100, 'Expected >100 chars of extractable text'
      print('PASS: PPT extraction verified')
      "
      2. Assert: exit code 0, output contains "PASS"
    Expected Result: PPT has >=5 slides with extractable text
    Evidence: .sisyphus/evidence/task-5-pptx.txt
  ```

  **Commit**: YES
  - Message: `test(fixtures): add sample PPT experiment guide`
  - Files: `tests/fixtures/sample_guide.pptx`

- [x] 6. check_deps.py — 依赖预检脚本

  **What to do**:
  - 创建 `lab-report/scripts/check_deps.py`
  - 检查项：
    1. `uv` 是否已安装（运行 `uv --version`）
    2. Python >= 3.10 是否可用
    3. 关键 Python 包是否可通过 uv 导入（pdfplumber, docx, docxtpl, pptx）
  - 输出：漂亮的检查报告（✅/❌ 每项状态）
  - 退出码：全部通过 = 0，有任何缺失 = 1
  - 包含 `--json` 标志输出 JSON 格式报告供脚本解析

  **Must NOT do**:
  - 不要自动安装缺失的包（只检查不修改环境）
  - 不要检查非必需的包

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 简单脚本，检查环境状态，只有一个文件
  - **Skills**: [`dev-workflow`]
    - `dev-workflow`: 结构化开发

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1（与 T1-T5, T7 并行）
  - **Blocks**: T12（init 脚本应首先调用 check_deps）
  - **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] `uv run python lab-report/scripts/check_deps.py` 退出码 0（当 uv 可用时）
  - [ ] `uv run python lab-report/scripts/check_deps.py --json` 输出合法 JSON
  - [ ] 缺失 uv 时退出码 1

  **QA Scenarios**:
  ```
  Scenario: All dependencies available
    Tool: Bash
    Preconditions: uv and Python installed
    Steps:
      1. uv run python lab-report/scripts/check_deps.py
      2. Assert: exit code 0
      3. Assert: output contains "✅" for uv, Python, pdfplumber, docx
    Expected Result: All checks pass with exit 0
    Evidence: .sisyphus/evidence/task-6-deps-pass.txt

  Scenario: JSON output format
    Tool: Bash
    Preconditions: uv and Python installed
    Steps:
      1. uv run python lab-report/scripts/check_deps.py --json > /tmp/deps.json
      2. uv run python -c "import json; d=json.load(open('/tmp/deps.json')); assert 'uv' in d; assert 'python' in d; print('JSON valid, fields:', list(d.keys()))"
      3. Assert: exit code 0
    Expected Result: Valid JSON with expected fields
    Evidence: .sisyphus/evidence/task-6-deps-json.json
  ```

  **Commit**: YES
  - Message: `feat(scripts): add dependency pre-flight check script`
  - Files: `scripts/check_deps.py`

- [x] 7. student_info.py — 学生信息发现/创建

  **What to do**:
  - 创建 `lab-report/scripts/student_info.py`
  - 功能：
    1. 从 CWD 向上搜索 `学生信息.md`（当前目录 → 父目录 → 祖父目录）
    2. 解析 Markdown 格式的学生信息字段：`姓名:`, `学号:`, `学院:`, `专业:`, `班级:`
    3. 未找到时返回 None + 提示创建
    4. 提供 `--create` 标志：从 `assets/学生信息模板.md` 复制模板到当前目录
    5. 输出 JSON 格式的学生信息（供其他脚本消费）
  - 使用 `schemas.py` 中定义的 `StudentInfo` dataclass

  **Must NOT do**:
  - 不要修改已有的学生信息.md（只读）
  - 不要在创建时覆盖已存在的文件（`--create` 时先检查）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 简单的文件搜索 + Markdown 解析，单文件脚本
  - **Skills**: [`dev-workflow`]
    - `dev-workflow`: 结构化开发

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1（与 T1-T6 并行）
  - **Blocks**: T12（init_project 调用 student_info）
  - **Blocked By**: T2（依赖 schemas.py）

  **Acceptance Criteria**:
  - [ ] 在包含 `学生信息.md` 的目录中运行，成功解析并输出 JSON
  - [ ] 在不含 `学生信息.md` 的目录中运行，返回空 + 提示
  - [ ] `--create` 标志正确复制模板文件
  - [ ] 不会覆盖已存在的 `学生信息.md`

  **QA Scenarios**:
  ```
  Scenario: Discover existing student info
    Tool: Bash
    Preconditions: Create test dir with 学生信息.md
    Steps:
      1. mkdir -p /tmp/test-student && cp tests/fixtures/学生信息.md /tmp/test-student/
      2. cd /tmp/test-student && uv run python .../lab-report/scripts/student_info.py
      3. Assert: exit code 0
      4. Assert: stdout contains valid JSON with 姓名, 学号 fields
    Expected Result: Student info discovered and output as JSON
    Evidence: .sisyphus/evidence/task-7-discover.json

  Scenario: Not found fallback
    Tool: Bash
    Preconditions: Empty temp directory
    Steps:
      1. cd /tmp && mkdir -p test-empty && cd test-empty
      2. uv run python .../lab-report/scripts/student_info.py
      3. Assert: exit code 0
      4. Assert: stdout contains null or empty JSON, stderr suggests creating file
    Expected Result: Graceful fallback with guidance message
    Evidence: .sisyphus/evidence/task-7-notfound.txt
  ```

  **Commit**: YES
  - Message: `feat(scripts): add student info discovery and creation script`
  - Files: `scripts/student_info.py`

- [ ] 8. parse_pdf.py — PDF 文本提取脚本

  **What to do**:
  - 创建 `lab-report/scripts/parse_pdf.py`
  - 功能：使用 pdfplumber 提取 PDF 所有页面文本 + pymupdf4llm 转换 Markdown
  - 检测扫描 PDF（所有页面文本为空 → 输出 `"warning": "SCANNED_PDF_DETECTED"`）
  - 输出结构化 JSON：`{filename, page_count, text_by_page, markdown, is_scanned}`
  - CLI：`uv run --with pdfplumber --with pymupdf4llm python parse_pdf.py --input <file> [--format json|markdown]`

  **Must NOT do**:
  - 不做 OCR — 扫描 PDF 只报告，不尝试识别
  - 不修改原始 PDF

  **Recommended Agent Profile**:
  - **Category**: `deep` — Reason: PDF 格式复杂性、边界条件、两种提取模式
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | **Parallel Group**: Wave 2（与 T9-T11 并行）
  - **Blocks**: T12 | **Blocked By**: T2（schemas）, T3（fixture）

  **Acceptance Criteria**:
  - [ ] `parse_pdf.py --input sample_guide.pdf` → exit 0 + JSON.page_count > 0 + JSON.is_scanned == false
  - [ ] 扫描 PDF 输入 → `is_scanned: true`, `warning: "SCANNED_PDF_DETECTED"`
  - [ ] Markdown 输出包含标题和段落

  **QA Scenarios**:
  ```
  Scenario: Parse text-based PDF
    Tool: Bash
    Steps:
      1. uv run --with pdfplumber --with pymupdf4llm python lab-report/scripts/parse_pdf.py --input tests/fixtures/sample_guide.pdf --format json
      2. Assert: exit code 0, stdout is valid JSON
      3. Assert: JSON.page_count > 0, JSON.is_scanned == false, JSON.markdown length > 50
    Expected Result: Structured JSON with text and markdown
    Evidence: .sisyphus/evidence/task-8-parse.json

  Scenario: Detect scanned PDF
    Tool: Bash
    Steps:
      1. uv run --with pdfplumber --with pymupdf4llm python lab-report/scripts/parse_pdf.py --input tests/fixtures/sample_guide_scanned.pdf --format json
      2. Assert: exit code 0, JSON.is_scanned == true, JSON contains "warning" key
    Expected Result: Scanned PDF detected and reported without crashing
    Evidence: .sisyphus/evidence/task-8-scanned.json
  ```

  **Commit**: YES | Message: `feat(scripts): add PDF text extraction and scanned detection`

- [ ] 9. parse_docx.py — Word 文档解析脚本

  **What to do**:
  - 创建 `lab-report/scripts/parse_docx.py`
  - 使用 python-docx 提取段落、表格文本，识别 `{{placeholder}}` 列表
  - 输出 JSON：`{filename, paragraphs, tables, placeholders, structure}`
  - CLI：`uv run --with python-docx python parse_docx.py --input <file>`

  **Must NOT do**: 不提取图片、不处理 .doc 格式

  **Recommended Agent Profile**:
  - **Category**: `deep` — Reason: Word XML 结构、表格遍历、占位符模式匹配
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | **Parallel Group**: Wave 2（与 T8, T10-T11 并行）
  - **Blocks**: T12, T13 | **Blocked By**: T2, T4

  **Acceptance Criteria**:
  - [ ] 识别 >=10 个 `{{placeholder}}`
  - [ ] 表格内容提取为二维数组

  **QA Scenarios**:
  ```
  Scenario: Parse template DOCX
    Tool: Bash
    Steps:
      1. uv run --with python-docx python lab-report/scripts/parse_docx.py --input tests/fixtures/sample_template.docx
      2. Assert: JSON.placeholders includes "{{姓名}}", "{{学号}}", "{{实验名称}}"
      3. Assert: JSON.tables has >=1 entry
    Evidence: .sisyphus/evidence/task-9-parse.json
  ```

  **Commit**: YES | Message: `feat(scripts): add DOCX parsing with placeholder detection`

- [ ] 10. parse_pptx.py — PPT 文本提取脚本

  **What to do**:
  - 创建 `lab-report/scripts/parse_pptx.py`
  - 使用 python-pptx 提取所有幻灯片文本，按编号组织
  - 输出 JSON/Markdown：`{filename, slide_count, slides}`
  - CLI：`uv run --with python-pptx python parse_pptx.py --input <file> [--format json|markdown]`

  **Must NOT do**: 不提取图片/图表、不处理 .ppt 格式

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: 简单文本提取，API 直观
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | **Parallel Group**: Wave 2（与 T8-T9, T11 并行）
  - **Blocks**: T12 | **Blocked By**: T5

  **Acceptance Criteria**:
  - [ ] 正确提取 >=5 张幻灯片文本
  - [ ] JSON 包含 slide_count + slides 数组

  **QA Scenarios**:
  ```
  Scenario: Parse PPT experiment guide
    Tool: Bash
    Steps:
      1. uv run --with python-pptx python lab-report/scripts/parse_pptx.py --input tests/fixtures/sample_guide.pptx --format json
      2. Assert: exit code 0, JSON.slide_count >= 5, JSON.slides[0] has content
    Evidence: .sisyphus/evidence/task-10-parse.json
  ```

  **Commit**: YES | Message: `feat(scripts): add PPTX text extraction script`

- [ ] 11. progress_manager.py — JSON 进度管理脚本

  **What to do**:
  - 创建 `lab-report/scripts/progress_manager.py`
  - CRUD `.lab-report/progress.json`：初始化、更新步骤、添加截图、添加笔记、查询、重置
  - 使用 `schemas.py` 的 `ProgressState` dataclass
  - CLI：`--init`, `--step N --status completed|in_progress`, `--screenshot`, `--note`, `--reset`

  **Must NOT do**: 不创建 `.lab-report/` 以外的目录，不存绝对路径

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: 简单 JSON CRUD 操作
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | **Parallel Group**: Wave 2（与 T8-T10 并行）
  - **Blocks**: T12, T15 | **Blocked By**: T2

  **Acceptance Criteria**:
  - [ ] 首次运行创建初始 `progress.json`
  - [ ] `--step N --status completed` 正确更新
  - [ ] `--screenshot` 和 `--reset` 正确工作

  **QA Scenarios**:
  ```
  Scenario: Full CRUD cycle
    Tool: Bash
    Preconditions: Clean temp directory
    Steps:
      1. cd /tmp && mkdir test-progress && cd test-progress
      2. uv run python .../lab-report/scripts/progress_manager.py --init --experiment "RC实验" --total-steps 5
      3. Assert: .lab-report/progress.json exists, status == "not_started"
      4. uv run python .../lab-report/scripts/progress_manager.py --step 1 --status completed
      5. Assert: JSON.current_step == 1, completed_steps includes 1
    Expected Result: Full CRUD cycle works
    Evidence: .sisyphus/evidence/task-11-progress.json
  ```

  **Commit**: YES | Message: `feat(scripts): add JSON progress state manager`

- [ ] 12. init_project.py — 项目初始化主逻辑

  **What to do**:
  - 创建 `lab-report/scripts/init_project.py`
  - 编排整个初始化流程：
    1. 调用 `check_deps.py` 预检环境
    2. 扫描当前目录发现课程资料（PDF/DOCX/PPTX）→ 向用户确认分类
    3. 调用 `student_info.py` 发现/创建学生信息
    4. 创建 `.lab-report/` 运行时目录
    5. 初始化 `progress.json`（如有实验步骤）
    6. 如果启用 Git → `git init` + 首次提交
    7. 输出初始化摘要 JSON
  - CLI：`uv run python init_project.py [--git] [--name "实验名称"]`
  - 交互式确认：材料分类不确定时询问用户

  **Must NOT do**:
  - 不修改原文件
  - 不在无材料时强行初始化（至少需要一个可识别的文件）

  **Recommended Agent Profile**:
  - **Category**: `deep` — Reason: 编排多个子系统，错误处理，用户交互逻辑
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | **Parallel Group**: Wave 3（与 T13-T14 并行）
  - **Blocks**: T15（SKILL.md 引用 init 流程）| **Blocked By**: T6, T7, T8, T9, T10, T11

  **Acceptance Criteria**:
  - [ ] 在 test/fixtures 目录运行，发现所有材料 → 输出正确分类的 JSON
  - [ ] 无材料目录运行 → 优雅提示
  - [ ] `--git` 标志正确初始化 Git 仓库
  - [ ] 扫描 PDF 时正确处理（报告 warning 不崩溃）

  **QA Scenarios**:
  ```
  Scenario: Full init with all materials
    Tool: Bash
    Preconditions: Copy fixtures to temp dir
    Steps:
      1. cd /tmp && mkdir test-init && cd test-init
      2. cp .../tests/fixtures/sample_guide.pdf .
      3. cp .../tests/fixtures/sample_template.docx .
      4. uv run python .../lab-report/scripts/init_project.py
      5. Assert: exit code 0
      6. Assert: .lab-report/ 目录已创建
      7. Assert: stdout JSON contains discovered files list
    Expected Result: All materials discovered, .lab-report created
    Evidence: .sisyphus/evidence/task-12-init.json

  Scenario: Init with Git
    Tool: Bash
    Preconditions: Clean temp dir with materials
    Steps:
      1. cd /tmp && mkdir test-init-git && cd test-init-git
      2. cp .../tests/fixtures/sample_guide.pdf .
      3. uv run python .../lab-report/scripts/init_project.py --git
      4. Assert: .git/ 目录存在
      5. Assert: git log --oneline shows initial commit
    Expected Result: Git repo initialized with first commit
    Evidence: .sisyphus/evidence/task-12-git.txt
  ```

  **Commit**: YES | Message: `feat(scripts): add project initialization orchestration script`

- [ ] 13. fill_template.py — docxtpl 模板填空脚本

  **What to do**:
  - 创建 `lab-report/scripts/fill_template.py`
  - 使用 **docxtpl**（非原始 python-docx）进行模板渲染：
    1. `shutil.copy` 模板 → 新文件（永不修改原始模板）
    2. 加载 Jinja2 上下文（从 JSON 数据文件）
    3. `DocxTemplate.render(context)` 替换所有 `{{placeholder}}`
    4. 保存输出文件
  - CJK 字体处理：设置 `w:eastAsia` 确保中文不显示为方框
  - 包含 `--style` 标志支持报告风格：
    - `perfect`: 完整填充，专业表述
    - `normal`: 标准填充
    - **两种风格均默认融入去 AI 味**（减少特征词、分段叙述、禁用词检查）
  - CLI：`uv run --with python-docx --with docxtpl python fill_template.py --template <file> --data <json> --output <file> [--style perfect|normal]`

  **Must NOT do**:
  - 绝不修改原始模板文件
  - 不编造数据（data JSON 中无数据 → 保留占位符或留空）
  - 不使用 .doc 格式

  **Recommended Agent Profile**:
  - **Category**: `deep` — Reason: docxtpl 集成、CJK 字体、格式保留、多风格支持
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | **Parallel Group**: Wave 3（与 T12, T14 并行）
  - **Blocks**: T15, T23（SKILL.md 和测试依赖）| **Blocked By**: T2, T4, T9

  **Acceptance Criteria**:
  - [ ] 填充后 `{{姓名}}` → 实际姓名
  - [ ] 原始模板 sha256 未改变
  - [ ] 中文段落不显示方框（验证 `w:eastAsia` 已设置）
  - [ ] `--style` 输出默认融入去 AI 味（不含特征词：首先、其次、总而言之等）

  **QA Scenarios**:
  ```
  Scenario: Basic template filling
    Tool: Bash
    Preconditions: sample_template.docx + test_data.json
    Steps:
      1. uv run --with python-docx --with docxtpl python lab-report/scripts/fill_template.py \
         --template tests/fixtures/sample_template.docx \
         --data tests/fixtures/test_data.json \
         --output /tmp/filled.docx
      2. Assert: exit code 0, /tmp/filled.docx exists
      3. uv run --with python-docx python -c "
         from docx import Document
         d = Document('/tmp/filled.docx')
         text = ' '.join([p.text for p in d.paragraphs])
         assert '{{姓名}}' not in text, 'Placeholder not replaced'
         print('PASS: No unreplaced placeholders')
         "
    Expected Result: All placeholders replaced
    Evidence: .sisyphus/evidence/task-13-filled.docx

  Scenario: Original preserved
    Tool: Bash
    Preconditions: Run fill_template
    Steps:
      1. python -c "import hashlib; h1=hashlib.sha256(open('tests/fixtures/sample_template.docx','rb').read()).hexdigest()"
      2. uv run ... fill_template.py --template ... --data ... --output /tmp/out.docx
      3. python -c "import hashlib; h2=hashlib.sha256(open('tests/fixtures/sample_template.docx','rb').read()).hexdigest(); assert h1==h2; print('PASS: Original unchanged')"
    Expected Result: Template SHA256 matches before and after
    Evidence: .sisyphus/evidence/task-13-preserved.txt

  Scenario: All output is de-AI style
    Tool: Bash
    Preconditions: Run fill_template with any style
    Steps:
      1. uv run ... fill_template.py ... --style normal --output /tmp/normal.docx
      2. uv run --with python-docx python -c "
         from docx import Document
         for path in ['/tmp/normal.docx']:
             d = Document(path)
             text = ' '.join([p.text for p in d.paragraphs])
             banned = ['首先', '其次', '最后', '总而言之', '值得注意的是']
             for w in banned:
                 assert w not in text, f'Banned word found in {path}: {w}'
         print('PASS: All styles are de-AI compliant')
         "
    Expected Result: No banned AI phrases in any output
    Evidence: .sisyphus/evidence/task-13-deai.txt
  ```

  **Commit**: YES | Message: `feat(scripts): add docxtpl-based template filling with CJK and de-AI support`

- [ ] 14. git_manager.py — Git 自动提交脚本

  **What to do**:
  - 创建 `lab-report/scripts/git_manager.py`
  - 功能：
    1. 检查 `.git/` 是否存在
    2. 自动检测未跟踪和修改的文件
    3. `git add` 所有变更
    4. `git commit` 带自动生成的描述性消息（基于变更文件）
    5. 支持 `--message` 自定义提交信息
    6. 支持 `--dry-run` 预览
  - CLI：`uv run python git_manager.py [--message "msg"] [--dry-run]`

  **Must NOT do**:
  - 不做 `git push`（仅本地提交）
  - 不做 force push 或 destructive 操作
  - 不在 .git 不存在时报错（静默跳过）

  **Recommended Agent Profile**:
  - **Category**: `quick` — Reason: 简单 git 命令包装
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | **Parallel Group**: Wave 3（与 T12-T13 并行）
  - **Blocks**: None | **Blocked By**: None

  **Acceptance Criteria**:
  - [ ] 在 Git 仓库中运行 → `git add` + `git commit` 成功
  - [ ] 在非 Git 目录运行 → 静默跳过，exit 0
  - [ ] `--dry-run` 只预览不提交

  **QA Scenarios**:
  ```
  Scenario: Auto-commit on changes
    Tool: Bash
    Preconditions: Git repo with modified file
    Steps:
      1. cd /tmp && mkdir test-git && cd test-git && git init
      2. echo "test" > test.txt
      3. uv run python .../lab-report/scripts/git_manager.py
      4. Assert: exit code 0
      5. Assert: git log --oneline -1 shows auto-commit
    Expected Result: Modified file auto-committed
    Evidence: .sisyphus/evidence/task-14-commit.txt
  ```

  **Commit**: YES | Message: `feat(scripts): add git auto-commit manager`

- [ ] 15. SKILL.md — 主 Skill 定义文件

  **What to do**:
  - 创建 `lab-report/SKILL.md`
  - YAML 头信息：
    - `name: lab-report`
    - `description`: 详细描述触发场景（实验报告、lab report、实验指导、/lab-report 命令等）
    - `metadata`: emoji 📝, 触发关键词
  - 正文（<5k 词）：
    - **Overview**: Skill 简介和两种模式
    - **Quick Start**: `/lab-report init` → 初始化 → Guide/Work
    - **Guide Mode 工作流**: 概要（详细见 references/）
    - **Work Mode 工作流**: 概要（详细见 references/）
    - **文件格式支持**: PDF/DOCX/PPTX 说明
    - **学生信息管理**: `学生信息.md` 机制
    - **脚本参考**: 列出所有脚本 + CLI 用法
    - **故障排除**: 常见问题
  - 渐进式加载：核心流程在正文，详细步骤引用 references/

  **Must NOT do**:
  - 正文不超过 5k 词（使用 references/ 分担）
  - 不包含具体 Python 代码（放 scripts/）

  **Recommended Agent Profile**:
  - **Category**: `writing` — Reason: 技术文档撰写，面向 Agent 和用户
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | **Parallel Group**: Wave 4（与 T16-T20 并行）
  - **Blocks**: None（文档层）| **Blocked By**: T12, T13, T14（需要 API 知识）

  **Acceptance Criteria**:
  - [ ] YAML 头信息包含 name 和 description
  - [ ] 总字数 <5k 词
  - [ ] 包含 Guide Mode 和 Work Mode 入口说明
  - [ ] 引用了所有 scripts/ 和 references/ 文件

  **QA Scenarios**:
  ```
  Scenario: SKILL.md validity check
    Tool: Bash
    Preconditions: SKILL.md created
    Steps:
      1. python -c "
      import yaml, re
      with open('lab-report/SKILL.md') as f:
          content = f.read()
      frontmatter = content.split('---')[1]
      meta = yaml.safe_load(frontmatter)
      assert 'name' in meta and meta['name'] == 'lab-report'
      assert 'description' in meta and len(meta['description']) > 50
      words = len(content.split())
      print(f'Word count: {words}')
      assert words < 5000, f'Too long: {words} words'
      print('PASS: SKILL.md valid')
      "
      2. Assert: exit code 0
    Expected Result: Valid YAML frontmatter, word count under 5k
    Evidence: .sisyphus/evidence/task-15-skill.md
  ```

  **Commit**: YES | Message: `docs: add main SKILL.md with Guide and Work mode workflows`

- [ ] 16. references/guide-mode-workflow.md

  **What to do**:
  - 创建 `lab-report/references/guide-mode-workflow.md`
  - 详细 Guide Mode 工作流文档（Agent 参考用）：
    1. 读取实验指导书 → 提取步骤列表
    2. 一次性展示所有步骤 + 注意事项
    3. 标记截图关键点（哪些步骤需要拍照/截图）
    4. 等待学生"继续"信号 → 更新进度
    5. 学生提问时 → 在该步骤上下文中逐步引导
    6. 同步 `progress.json` 状态
  - 包含：步骤数据结构、进度更新协议、截图提醒触发条件

  **Recommended Agent Profile**:
  - **Category**: `writing` — Reason: 技术工作流文档
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | Wave 4 | **Blocked By**: T11, T12

  **Commit**: YES | Message: `docs: add Guide Mode detailed workflow reference`

- [ ] 17. references/work-mode-workflow.md

  **What to do**:
  - 创建 `lab-report/references/work-mode-workflow.md`
  - 详细 Work Mode 工作流文档：
    1. 检查是否存在 `progress.json`（Guide 模式产物）
    2. 有进度 → 提取实验数据和笔记
    3. 无进度 → 询问学生描述实验过程
    4. 解析模板 → 识别所需字段
    5. 构建填充数据 JSON
    6. 调用 `fill_template.py` 生成报告
    7. （可选）调用 `git_manager.py` 提交
  - 包含：模板字段映射逻辑、内容生成策略、风格选择指南

  **Recommended Agent Profile**:
  - **Category**: `writing` | **Skills**: [`dev-workflow`]
  - **Parallelization**: YES | Wave 4 | **Blocked By**: T13

  **Commit**: YES | Message: `docs: add Work Mode detailed workflow reference`

- [ ] 18. references/template-patterns.md

  **What to do**:
  - 创建 `lab-report/references/template-patterns.md`
  - 记录常见实验报告模板占位符模式：
    - 标准 `{{placeholder}}` Jinja2
    - 变体处理（如无占位符的空白段落）
  - 报告结构约定：章节命名、表格使用规范
  - CJK 字体最佳实践：宋体/黑体/楷体在 python-docx 中的设置方法

  **Recommended Agent Profile**:
  - **Category**: `writing` | **Skills**: [`dev-workflow`]
  - **Parallelization**: YES | Wave 4 | **Blocked By**: T9, T13

  **Commit**: YES | Message: `docs: add template pattern and CJK font reference`

- [ ] 19. references/de-ai-style-guide.md

  **What to do**:
  - 创建 `lab-report/references/de-ai-style-guide.md`
  - 去 AI 味写作风格指南（**适用于所有风格**）：
    - **禁用词汇**: 首先、其次、最后、总而言之、值得注意的是、综上所述、不可否认
    - **禁用结构**: 编号列表（一、二、三）、markdown 分条（- xxx）
    - **推荐风格**: 自然段落叙述、连接词多样化、偶尔口语化表达
    - **示例**: 对比 AI 风格 vs 学生风格段落
  - 使用指南：Agent 在填写所有内容时参考此文档，无论选择哪种风格

  **Recommended Agent Profile**:
  - **Category**: `writing` | **Skills**: [`dev-workflow`]
  - **Parallelization**: YES | Wave 4 | **Blocked By**: None

  **Commit**: YES | Message: `docs: add de-AI writing style guide`

- [ ] 20. references/report-structure.md

  **What to do**:
  - 创建 `lab-report/references/report-structure.md`
  - 标准实验报告结构参考：
    - 封面信息（课程名、实验名、姓名、学号、日期、地点）
    - 实验目的
    - 实验原理
    - 实验器材
    - 实验步骤
    - 实验数据
    - 实验结果与分析
    - 实验结论
  - 每个章节的写作要点和常见错误

  **Recommended Agent Profile**:
  - **Category**: `writing` | **Skills**: [`dev-workflow`]
  - **Parallelization**: YES | Wave 4 | **Blocked By**: None

  **Commit**: YES | Message: `docs: add standard lab report structure reference`

- [ ] 21. assets/学生信息模板.md

  **What to do**:
  - 创建 `lab-report/assets/学生信息模板.md`
  - 内容：Markdown 格式的学生信息模板
    ```markdown
    # 学生信息
    
    姓名: 
    学号: 
    学院: 
    专业: 
    班级: 
    ```
  - 供 `student_info.py --create` 复制使用
  - 包含注释说明各字段含义

  **Recommended Agent Profile**:
  - **Category**: `quick` | **Skills**: [`dev-workflow`]
  - **Parallelization**: YES | Wave 5 | **Blocked By**: T7

  **Commit**: YES | Message: `feat(assets): add student info markdown template`

- [ ] 22. assets/report_template.docx

  **What to do**:
  - 创建 `lab-report/assets/report_template.docx` — 默认实验报告模板
  - 使用 python-docx 生成，包含常用实验报告结构
  - 占位符：`{{姓名}}`, `{{学号}}`, `{{学院}}`, `{{专业}}`, `{{班级}}`, `{{课程名}}`, `{{实验名称}}`, `{{实验日期}}`, `{{实验地点}}`, `{{实验目的}}`, `{{实验原理}}`, `{{实验器材}}`, `{{实验步骤}}`, `{{实验数据}}`, `{{实验结果}}`, `{{实验结论}}`
  - 包含：封面表格（信息区）+ 正文段落（各章节）
  - CJK 字体已预设

  **Must NOT do**: 不使用 .doc 格式

  **Recommended Agent Profile**:
  - **Category**: `quick` | **Skills**: [`dev-workflow`]
  - **Parallelization**: YES | Wave 5 | **Blocked By**: T4, T13（参考 fill_template 格式）

  **QA Scenarios**:
  ```
  Scenario: Default template validation
    Tool: Bash
    Steps:
      1. uv run --with python-docx python -c "
      from docx import Document
      d = Document('lab-report/assets/report_template.docx')
      text = ' '.join([p.text for p in d.paragraphs])
      placeholders = ['{{姓名}}', '{{学号}}', '{{实验名称}}', '{{实验目的}}']
      for p in placeholders:
          assert p in text, f'Missing: {p}'
      print(f'PASS: {len(placeholders)} placeholders found')
      "
    Expected Result: All required placeholders present
    Evidence: .sisyphus/evidence/task-22-template.txt
  ```

  **Commit**: YES | Message: `feat(assets): add default lab report DOCX template`

- [ ] 23. Unit tests — parse_* scripts

  **What to do**:
  - 创建 `tests/test_parse_pdf.py`, `tests/test_parse_docx.py`, `tests/test_parse_pptx.py`
  - 测试内容：
    - `test_parse_pdf.py`: 正常 PDF 提取文本、扫描 PDF 检测、Markdown 输出、JSON 输出、文件不存在错误
    - `test_parse_docx.py`: 占位符检测、表格提取、段落提取、不存在文件错误
    - `test_parse_pptx.py`: 幻灯片计数、文本提取、JSON/Markdown 输出、不存在文件错误
  - 使用 pytest fixtures 引用 `tests/fixtures/`
  - TDD：先写测试 → 确认 FAIL → 确保实现通过

  **Must NOT do**: 不修改 fixtures 文件

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` — Reason: 多模块测试，需要全面覆盖
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | Wave 5（与 T21-T22, T24-T25 并行）
  - **Blocks**: None | **Blocked By**: T3, T4, T5, T8, T9, T10

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/test_parse_pdf.py -v` → ALL PASS
  - [ ] `uv run pytest tests/test_parse_docx.py -v` → ALL PASS
  - [ ] `uv run pytest tests/test_parse_pptx.py -v` → ALL PASS
  - [ ] 测试覆盖率 >80%（parse 相关代码）

  **QA Scenarios**:
  ```
  Scenario: All parse tests pass
    Tool: Bash
    Steps:
      1. uv run pytest tests/test_parse_*.py -v --tb=short
      2. Assert: exit code 0
      3. Assert: all tests show PASS
    Expected Result: >=15 tests, all passing
    Evidence: .sisyphus/evidence/task-23-tests.txt
  ```

  **Commit**: YES | Message: `test: add unit tests for PDF, DOCX, and PPTX parsers`

- [ ] 24. Unit tests — fill_template.py + init_project.py

  **What to do**:
  - 创建 `tests/test_fill_template.py`, `tests/test_init_project.py`
  - `test_fill_template.py`:
    - 占位符替换验证
    - 原始模板未修改（SHA256 对比）
    - CJK 字体设置验证
    - 两种风格输出检查（均须通过 de-AI）
    - De-AI 禁用词检查
    - 不存在的模板错误
    - 无效 JSON 数据错误
  - `test_init_project.py`:
    - 材料发现和分类
    - `.lab-report/` 目录创建
    - Git 初始化
    - 空目录处理
    - 学生信息发现

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` — Reason: 核心逻辑测试，需要全面覆盖
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | Wave 5 | **Blocked By**: T12, T13

  **QA Scenarios**:
  ```
  Scenario: All core logic tests pass
    Tool: Bash
    Steps:
      1. uv run pytest tests/test_fill_template.py tests/test_init_project.py -v --tb=short
      2. Assert: exit code 0, all tests PASS
    Expected Result: >=20 tests, all passing
    Evidence: .sisyphus/evidence/task-24-tests.txt
  ```

  **Commit**: YES | Message: `test: add unit tests for template filling and project init`

- [ ] 25. Unit tests — progress_manager.py + student_info.py + git_manager.py

  **What to do**:
  - 创建 `tests/test_progress_manager.py`, `tests/test_student_info.py`, `tests/test_git_manager.py`
  - `test_progress_manager.py`:
    - 初始化创建进度文件
    - CRUD 操作（更新步骤、截图、笔记）
    - 重置功能
    - 无效输入处理
  - `test_student_info.py`:
    - 发现 `学生信息.md` 并解析
    - 向上搜索
    - 未找到场景
    - `--create` 功能
    - 不覆盖已存在文件
  - `test_git_manager.py`:
    - Git 仓库中自动提交
    - 非 Git 目录静默跳过
    - `--dry-run` 预览
    - 自定义 message

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` — Reason: 多模块测试
  - **Skills**: [`dev-workflow`]

  **Parallelization**:
  - **Can Run In Parallel**: YES | Wave 5 | **Blocked By**: T7, T11, T14

  **QA Scenarios**:
  ```
  Scenario: All utility tests pass
    Tool: Bash
    Steps:
      1. uv run pytest tests/test_progress_manager.py tests/test_student_info.py tests/test_git_manager.py -v --tb=short
      2. Assert: exit code 0, all tests PASS
    Expected Result: >=15 tests, all passing
    Evidence: .sisyphus/evidence/task-25-tests.txt
  ```

  **Commit**: YES | Message: `test: add unit tests for progress, student info, and git managers`

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
>
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `uv run pytest tests/`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp).
  Output: `Build [PASS/FAIL] | Lint [N/A Python] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (init → parse → fill flow). Test edge cases: empty directory, missing files, scanned PDF, CJK fonts. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: Per-task commits (see each task)
- **Wave 2**: Per-task commits
- **Wave 3**: Per-task commits
- **Wave 4**: Per-task commits
- **Wave 5**: Per-task commits

---

## Success Criteria

### Verification Commands
```bash
# 初始化验证
uv run python lab-report/scripts/init_project.py --dir tests/fixtures/

# PDF 解析验证
uv run --with pdfplumber python lab-report/scripts/parse_pdf.py --input tests/fixtures/sample_guide.pdf

# 模板填充验证
uv run --with python-docx --with docxtpl python lab-report/scripts/fill_template.py \
  --template tests/fixtures/sample_template.docx \
  --data tests/fixtures/test_data.json \
  --output .sisyphus/evidence/filled_output.docx

# 测试套件
uv run pytest tests/ -v
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] `/lab-report init` 端到端可用
- [ ] Guide Mode 流程走通
- [ ] Work Mode 生成报告格式正确
- [ ] 中文无方框
- [ ] 原始文件未被修改

