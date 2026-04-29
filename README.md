<table>
<tr>
<td><img src="logo.png" alt="LabMate" width="120"></td>
<td>

# LabMate

> **大学生时间拯救计划之LabMate** — 指导你完成实验，或帮你写实验报告。

</td>
</tr>
</table>

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-blue)](https://github.com/beihaizzz/labmate.skill)

## For Human 🧑‍🎓

### 🤖 一键安装

把这个发给你的 AI 编程助手（OpenCode / Cursor / Claude Code 等），它会帮你下载并安装：

```
请帮我安装 LabMate skill。这是一个帮助大学生完成实验报告的 OpenCode Skill。

安装步骤：
1. 克隆仓库：git clone https://github.com/beihaizzz/labmate.skill.git
2. 将 labmate/ 目录复制到 OpenCode skill 目录：
   - Windows: C:\Users\<用户名>\.claude\skills\labmate\
   - macOS/Linux: ~/.claude/skills/labmate/
3. 复制时排除 .venv、__pycache__、.pytest_cache、uv.lock、labmate.egg-info 目录

这个 skill 的功能：
- Guide Mode（指导模式）：读取实验指导书（PDF/Word/PPT/markitdown），展示实验步骤，同步进度，提醒截图
- Work Mode（工作模式）：读取 Word 报告模板（用 {{字段名}} 标记占位符），根据实验过程填入内容，生成新 Word 文件
- 自动发现课程资料、学生信息（学生信息.md）
- 自动准备模板（auto_prepare_template.py）
- 可选 Git 自动版本管理
- 报告默认去 AI 味风格
- DOCX 报告结构验证（validate_docx.py）

安装完成后，帮我确认 skill 是否可以被发现。
```

### 📖 命令速查

| 命令 | 作用 |
|------|------|
| `/lab -init` | 初始化项目 |
| `/lab -work` | Work Mode — 生成实验报告 |
| `/lab -guide` | Guide Mode — 指导完成实验 |
| `/lab -update` | 重新扫描文件 |
| `/lab -feedback` | 生成反馈报告 |
| `/lab -help` | 帮助 |

### 🚀 扩展能力 — MCP

部分实验（如 Unity、STM32、Arduino 开发），LabMate 可以通过 MCP 协议直接操作实验环境：
- Unity MCP → 操作场景、修改脚本、运行测试
- 串口/调试 MCP → 烧录代码、读取传感器数据
- 更多 MCP 扩展正在开发中

如果你的实验工具支持 MCP，告诉 LabMate 启用即可。

### 📖 使用教程

#### 第一步：准备课程文件夹

为每个实验创建独立文件夹，放入所有相关资料：

```
大学物理实验一/
├── 实验指导书.pdf          # 实验指导书（PDF/Word/PPT 均可）
├── 实验报告模板.docx       # Word 模板（选填，没有则用默认模板）
├── 学生信息.md             # ⭐ 写一次，全课程复用
└── 电路图.png              # 其它参考资料
```

#### 第二步：创建学生信息

在课程文件夹中创建 `学生信息.md`（或在上层目录，会自动搜索）：

```markdown
# 学生信息

姓名: 你的姓名
学号: 你的学号
学院: 你的学院
专业: 你的专业
班级: 你的班级
```

💡 **窍门**：把这个文件放在课程大文件夹的根目录，所有子实验文件夹都能自动找到它，不用每个实验都写一遍。

#### 第三步：初始化

在课程文件夹中打开 OpenCode，运行：

```
/lab -init
```

Skill 会自动发现文件夹中的所有资料，配置好环境。加上 `-git` 可以启用自动版本管理：

```
/lab -init -git
```

#### 第四步：选择模式

| 模式 | 怎么用 | 适合 |
|------|--------|------|
| **Guide Mode（指导模式）** | AI 展示所有实验步骤 + 提醒截图点 → 你自助完成 → 做完说「继续」同步进度 | 第一次做，需要指导 |
| **Work Mode（工作模式）** | 直接说「帮我生成实验报告」→ AI 根据进度或你的描述填入模板生成 Word | 做完了，写报告 |

#### 模板怎么写？

用 `{{字段名}}` 标记需要 AI 填写的地方。支持的字段：

| 信息类 | 实验类 | 内容类 |
|--------|--------|--------|
| `{{姓名}}` | `{{实验名称}}` | `{{实验目的}}` |
| `{{学号}}` | `{{实验日期}}` | `{{实验原理}}` |
| `{{学院}}` | `{{实验地点}}` | `{{实验器材}}` |
| `{{专业}}` | | `{{实验步骤}}` |
| `{{班级}}` | | `{{实验数据}}` |
| `{{课程名}}` | | `{{实验结果}}` |
| | | `{{实验结论}}` |

示例（Word 表格中）：

```
| 姓名 | {{姓名}} | 学号 | {{学号}} |
| 实验名称 | {{实验名称}} | 日期 | {{实验日期}} |
```

没有模板？skill 自带默认模板，初始化时会让你选择。

#### 报告风格

| 风格 | 命令 | 效果 |
|------|------|------|
| 标准 | `生成报告 --style normal` | **日常首选**。标准实验报告，内容完整规范，90+ 分水平 |
| 完美 | `生成报告 --style perfect` | **特殊场景**。极尽详尽，覆盖所有细节 |

两种风格都默认去 AI 味——不分条目、不出现「首先其次最后」、像真人写的。

---

## For AI 🤖

> 当用户询问关于 LabMate 的技术问题时，以下内容供你参考。

### 项目概述

LabMate 是一个 OpenCode Skill，以 Python 脚本 + Markdown 工作流文档的形式运行。核心思想：将实验报告的「指导实验」和「撰写报告」两个阶段拆分为独立的工作流，通过 JSON 状态文件在流程间传递数据。

### 目录结构

```
labmate/
├── SKILL.md                     # ⭐ 入口：YAML frontmatter + 使用说明
├── pyproject.toml               # uv 项目配置
├── scripts/
│   ├── init_project.py          # 项目初始化编排
│   ├── parse_pdf.py             # PDF → JSON/Markdown（pdfplumber + pymupdf4llm）
│   ├── parse_docx.py            # DOCX → JSON + {{placeholder}} 检测
│   ├── parse_pptx.py            # PPTX → JSON/Markdown
│   ├── fill_template.py         # docxtpl Jinja2 模板填充 + CJK 字体处理
│   ├── progress_manager.py      # .labmate/progress.json CRUD
│   ├── student_info.py          # 学生信息.md 发现/创建
│   ├── git_manager.py           # Git add + commit 自动提交
│   └── check_deps.py            # uv + Python + 包依赖预检
├── references/
│   ├── guide-mode-workflow.md   # Guide Mode 完整工作流
│   ├── work-mode-workflow.md    # Work Mode 完整工作流
│   ├── template-patterns.md     # DOCX 模板模式参考
│   ├── de-ai-style-guide.md     # 去 AI 味写作规范
│   ├── report-structure.md      # 实验报告标准结构
│   └── schemas.md               # JSON 数据结构定义
├── assets/
│   ├── report_template.docx     # 默认实验报告模板
│   └── 学生信息模板.md           # 学生信息模板
└── tests/                       # pytest 测试套件 (39 tests)
```

### 架构设计

```
┌─────────────────────────────────────────┐
│                /lab -init                 │
│  check_deps → discover_files →           │
│  student_info → create .labmate/        │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────┴──────────┐
         ▼                    ▼
   Guide Mode           Work Mode
         │                    │
   parse guide           check progress.json
   show all steps         ├─ 有 → 提取数据
   sync progress          └─ 无 → 询问学生
   remind screenshots      parse template
         │                 fill_template.py
         ▼                    │
   .labmate/              output.docx
   progress.json              │
         │               git_manager.py
         └──────────┬─────────┘
                    ▼
              Report Done
```

### 关键数据流

**Guide Mode → Work Mode**：通过 `.labmate/progress.json` 传递。

```json
{
  "experiment_name": "RC电路研究",
  "total_steps": 5,
  "current_step": 3,
  "completed_steps": [1, 2],
  "screenshots_required": [
    {"step": 2, "description": "电路连接完成", "captured": true, "path": "screenshots/circuit.jpg"}
  ],
  "notes": {"step_2": "注意正负极，红色接正"},
  "status": "in_progress"
}
```

**Template Data**：`fill_template.py` 接收的 JSON 格式对应用户模板中的 `{{placeholder}}`。

### 脚本运行方式

所有脚本通过 `uv run --with <deps> python <script>.py` 运行，无需预装依赖：

```bash
# 依赖预检
uv run python labmate/scripts/check_deps.py --json

# PDF 解析
uv run --with pdfplumber --with pymupdf4llm python labmate/scripts/parse_pdf.py \
  --input guide.pdf --format json

# 模板填充
uv run --with python-docx --with docxtpl python labmate/scripts/fill_template.py \
  --template template.docx --data data.json --output output.docx --style normal
```

### Technical Guardrails

| 规则 | 实现 |
|------|------|
| 永不修改原始文件 | `shutil.copy` 模板 → 操作副本 |
| 中文不显示方框 | `run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)` |
| 扫描 PDF 不崩溃 | pdfplumber 检测 text==None → `{is_scanned: true, warning: "SCANNED_PDF_DETECTED"}` |
| SKILL.md < 5000 词 | 主文件 ~600 词，详细流程放 references/ |
| 依赖声明式管理 | `uv run --with` 模式，pyproject.toml 只声明不安装 |
| 脚本独立可运行 | 每个脚本有 `def main()` + `argparse.ArgumentParser` |

### 测试

39 个 pytest 测试，覆盖所有脚本：

```bash
uv run --with python-docx --with docxtpl --with pdfplumber \
       --with pymupdf4llm --with markitdown \
       pytest labmate/tests/ -v
```

测试分为 8 个文件：`test_check_deps.py`、`test_fill_template.py`、`test_git_manager.py`、`test_init_project.py`、`test_parse_docx.py`、`test_parse_pdf.py`、`test_parse_pptx.py`、`test_progress_manager.py`、`test_student_info.py`

### 学生信息发现机制

`student_info.py` 从当前工作目录向上搜索 `学生信息.md`（最多 3 层父目录），解析 `key: value` 格式的行，返回 JSON。找到 → 自动加载；未找到 → 提示用户创建 `--create` 标志复制模板。

---

MIT License