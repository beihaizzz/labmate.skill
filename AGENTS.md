# PROJECT KNOWLEDGE BASE

## MISSION

"大学生时间拯救计划"不是一句玩笑。一个实验 4 学时，写报告却花 6 小时——这件事本身就是错的。

LabMate 做三件事来纠正它：

**一、消除机械劳动。** 姓名学号填八遍、字体字号逐格调、缩进对齐反复改——这些事情人不该做，AI 就该一次做对。inspect 前置、角色名填充、标签不覆盖，全部为了让机器理解模板，而不是让人理解机器。

**二、缩短反馈链。** 不是为了"写代码很快"，是为了"从打开文件夹到拿到可提交报告"这件事很快。一轮够用就不做两轮。猜错格式比没写代码更浪费时间。

**三、消除重复决策。** 同一个课程八个实验，不用每次重新扫目录、重新问课程名、重新确认风格。project.md 记住，学生信息.md 复用，init 一次管全部。

**优化目标**：让实验报告的边际时间趋近于零。第一个实验可能需要配置，到了第三个、第五个实验，用户只做一件事——描述实验内容，然后拿走报告。迭代轮次的目标不是"少"，是"1"。格式的目标不是"基本对"，是"不需要手动改"。

**硬约束**（所有优化必须服从）：
- 不覆盖标签单元格、不编造实验数据、不盲目设 eastAsia
- 猜是不可接受的——先 inspect 再动手
- 用户手上有什么就是什么——不从假设出发

---

**生成时间:** 2026-05-04
**最新提交:** 适配 v1.2.0
**分支:** main
**文件数:** 80+ (不含 venv/cache)

## OVERVIEW

LabMate skill — 兼容 OpenCode / Claude Code / Cursor 等 AI 编程助手，用 Python 脚本 + Markdown 工作流文档的形式帮助大学生完成实验报告。两种模式：Guide Mode（指导完成实验）和 Work Mode（生成报告）。支持 visual model 可获得更好的图片分析体验。

## STRUCTURE

```
lab-report/                         # LabMate Skill 包
├── SKILL.md                        # 主入口（YAML frontmatter + 使用说明）
├── pyproject.toml                  # uv 项目配置
├── assets/
│   ├── report_template.docx        # 通用实验报告模板
│   └── 学生信息模板.md
├── scripts/                        # 核心 Python 脚本（17个）
│   ├── fill_template.py            # 模板填充（placeholder/直填/角色模式）
│   ├── fill_utils.py               # 格式化工具库
│   ├── inspect_template.py         # 模板格式前置分析
│   ├── auto_prepare_template.py    # 自动注入 {{placeholder}}（v1.0.0）
│   ├── extract_template.py         # 成品报告反推模板结构
│   ├── role_aliases.py             # 共享角色映射 + 标签检测
│   ├── section_map.py              # 段落映射表生成（v1.2.0）
│   ├── validate_docx.py            # DOCX 结构验证（v1.1.0）
│   ├── init_project.py             # 项目初始化编排
│   ├── parse_pdf.py                # PDF（含 OCR 扫描件支持）
│   ├── parse_docx.py               # DOCX 解析
│   ├── parse_pptx.py               # PPTX（markitdown，v1.1.0）
│   ├── progress_manager.py         # JSON 进度管理
│   ├── student_info.py             # 学生信息发现/创建
│   ├── git_manager.py              # Git 管理
│   └── check_deps.py               # 依赖预检
├── references/                     # AI agent 参考文档
│   ├── guide-mode-workflow.md
│   ├── work-mode-workflow.md
│   ├── template-patterns.md
│   ├── de-ai-style-guide.md
│   ├── report-structure.md
│   └── schemas.md
└── tests/                          # pytest 39 tests, 10 文件
    └── fixtures/
```

## WHERE TO LOOK

| 任务 | 文件 | 备注 |
|------|------|------|
| 添加新脚本 | `scripts/` | 必须包含 `def main()` + `argparse.ArgumentParser` |
| 修改模板填充 | `scripts/fill_template.py` + `scripts/fill_utils.py` | fill_utils是共享工具库 |
| 修改工作流 | `references/*-mode-workflow.md` | 先改引用文档，再改脚本 |
| 修改进度协议 | `references/schemas.md` + `scripts/progress_manager.py` | Schema和实现必须同步 |
| 修改通用模板 | `scripts/generate_universal_template.py` | 运行此脚本生成 .docx |
| 自动准备模板 | `scripts/auto_prepare_template.py` | 无占位符模板自动注入 |
| 生成段落映射 | `scripts/section_map.py` | /lab -fix 依赖 |
| 验证报告 | `scripts/validate_docx.py` | 生成后检查 |
| 发版前检查 | `tests/` | `uv run --with <pkgs> pytest lab-report/tests/ -v` |

## CONVENTIONS

- **Python 环境**: uv + `--with <pkgs>` 模式，不预装全局依赖
- **脚本独立性**: 每个脚本 `def main()` + `argparse.ArgumentParser`，可独立运行
- **Git commit**: **中文提交信息**
- **文件修改**: 原始文件永远是只读的 — 所有操作在 `shutil.copy` 的副本上进行
- **占位符格式**: `{{字段名}}` Jinja2 语法
- **学生信息**: `学生信息.md` 格式 `key: value`，向上搜索最多3层目录
- **工作目录**: 新项目默认 `.labmate/`，旧项目 `.lab-report/` 仍兼容

## ANTI-PATTERNS (本项目的硬规则)

| 禁止 | 原因 |
|------|------|
| `as any` / `@ts-ignore` | TypeScript不适用，Python中同理不要用 bare except |
| 修改原始模板文件 | 所有操作 `shutil.copy` 到副本 |
| 编造实验数据 | 只填入用户提供的数据 |
| 支持 .doc 格式 | 通过 LibreOffice 自动转换 |
| OCR | v1.2.0 已支持 --ocr 标志，扫描 PDF 可降级提取 |
| LaTeX / pydantic | 不做，保持轻量 |
| SKILL.md > 5000词 | 详细流程放 references/ |
| 硬编码字体/字号 | 用 `fill_utils.py` 常量，或者 inspect 数据 |
| 无差别设置 eastAsia | 仅在模板明确有 eastAsia 的 cell 才设置 |
| 标签单元格覆盖 | inspect 输出中 is_label=true 的不可写 |
| 同一方案连续3次失败后继续 | 必须提出至少2种替代方案 |

## UNIQUE STYLES

- **fill_template.py 双模式**: `--data` (placeholder填充) / `--cells` (直接表格填充)
- **工作流强制前置**: Work Mode 必须先 `inspect_template.py` 再 `fill_template.py`
- **Git 默认仅 stage**: 文件出现在 OpenCode 审查侧边栏，用户手动 commit。加 `--commit` 跳过审查
- **去AI味默认化**: 所有输出默认融入去AI味（无首先其次最后、分段叙述）
- **风格定义注意**: `normal`=标准报告90+分（日常首选），`perfect`=极尽详尽（特殊场景）。注意不要反
- **/lab -fix 精确重写**: 用户指定逻辑ID修改单个单元格，不影响其他内容

## COMMANDS

```bash
# 测试
uv run --with python-docx --with docxtpl --with pdfplumber \
       --with pymupdf4llm --with markitdown \
       --directory lab-report pytest -v

# 模板分析
uv run --with python-docx python lab-report/scripts/inspect_template.py \
  --input template.docx --format human

# 模板填充（placeholder模式）
uv run --with python-docx --with docxtpl python lab-report/scripts/fill_template.py \
  -t template.docx -d data.json -o output.docx --inspect inspect.json

# 模板填充（直填模式）
uv run --with python-docx python lab-report/scripts/fill_template.py \
  -t template.docx --cells cells.json -o output.docx

# 自动准备模板
uv run --with python-docx python lab-report/scripts/auto_prepare_template.py \
  --input blank_template.docx --output prepared.docx

# 段落映射
uv run --with python-docx python lab-report/scripts/section_map.py \
  --input report.docx --output section-map.json

# 报告验证
uv run --with python-docx python lab-report/scripts/validate_docx.py \
  --input report.docx --inspect inspect.json

# Git 初始化
uv run python lab-report/scripts/git_manager.py --init

# 生成通用模板
uv run --with python-docx python lab-report/scripts/generate_universal_template.py
```

## NOTES

- **docxtpl 与 python-docx**: 始终优先用 docxtpl（Jinja2 模板引擎），它处理 run-splitting 问题
- **模板 merge cells**: 用 `table.rows[r].cells[c]` 而非 `table.cell(r, c)` 避免索引偏移
- **pymupdf4llm**: 可能因 ONNX 版本问题抛出异常，已做降级处理（纯文本拼接）
- **LibreOffice**: 用于 `.doc` → `.docx` 转换，非强制依赖
- **`test_data.json`**: 在 `tests/fixtures/` 中，由 `test_fill_template.py` 使用
- **encode 问题**: PowerShell 下 inspect 脚本的 emoji 输出需 UTF-8 编码
