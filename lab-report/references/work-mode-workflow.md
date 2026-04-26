# Work Mode Workflow

Work Mode generates a completed lab report DOCX from a template and experiment data. It pulls student info, experiment progress, and student descriptions together, fills a template, and verifies the output.

---

## Overview

Work Mode is the second mode, activated after Guide Mode completes (or directly if the student already has experiment data). It produces a finished lab report by:

1. Collecting all available data sources
2. Parsing the template DOCX to discover placeholders
3. Building a complete data JSON
4. Rendering the template
5. Verifying no placeholders remain

---

## Step 1: Detect Existing Progress

Check for `.lab-report/progress.json`:

```bash
python scripts/progress_manager.py
```

### If progress exists

Extract experiment data from the progress file:

- `experiment_name` maps to `实验名称`
- `notes` contains step-by-step observations the student recorded
- `screenshots_required` lists captured screenshot paths
- `status` tells you if the experiment is complete

Combine this with student info (Step 2) and any additional description the student provides.

### If no progress exists

Ask the student to describe the experiment in natural language:

```
没有找到实验进度记录。请描述你的实验：
- 实验名称是什么？
- 实验目的和原理是什么？
- 你做了哪些步骤？
- 观察到了什么数据？
```

Collect the student's response and use it as the primary data source. You can still initialize progress retroactively if the student wants to track things.

---

## Step 1.5: Confirm Experiment Metadata (fix 1.1)

**Before generating content, actively ask the student for experimental metadata** using the `question` tool.

Required metadata to confirm:

- 实验日期: （如 2025年4月21日）
- 实验地点: （实验室名称 / 机房编号，如 实验楼B301）
- 实验学时: （如 2学时 / 4学时）
- 指导教师: （姓名）
- 同组人员及分工: （可选）

**If `学生信息.md` already exists**, auto-fill 姓名/学号/学院/专业/班级, but still confirm the per-experiment fields (日期、地点、学时、教师).

### ⚠️ Critical: confirm student info before generating (fix 3 — no guessing grade/class)

When loading student info, ALWAYS show the user a confirmation prompt:

```
检测到学生信息：
  姓名：张啸瑞
  学号：3120230901104
  班级：计科1班
  ⚠️ 年级：未明确（从"计科1班"推测为2023级，请确认）

以上信息是否正确？
```

Rules:
- **Never infer** grade/class/year without user confirmation
- Show the raw data from `学生信息.md` exactly as-is
- If any field seems ambiguous (e.g., "计科1班" — which year?), flag it as `⚠️ 待确认`
- After user confirms, save to `.lab-report/config.json` so subsequent runs skip re-asking

### Example prompt:

```
在生成报告前，请确认以下实验信息：

实验日期：2025年4月21日
实验地点：_________
指导教师：_________
同组人员及分工：_________（选填）

另外，你希望报告采用哪种风格？
1）perfect（极尽详尽：覆盖所有细节，特殊场景使用）
2）normal（标准报告：内容完整规范，日常使用首选）
```

Save confirmed metadata to `.lab-report/config.json` for reuse across re-generations.

---

## Step 1.6: Offer Style Selection (fix 1.2)

After confirming metadata, explicitly ask the student which report style they want:

| Style | When to recommend |
|-------|-------------------|
| `normal` | **日常首选**。标准实验报告，内容完整、结构规范，老师看了能给 90+ 分 |
| `perfect` | **极少数场景**。尽最大可能详尽，覆盖所有细节和可能情况 |

Both styles apply de-AI guidelines (no 首先/其次/最后, natural paragraphs).

---

## Step 2: Collect Student Info

Run the student info discovery script:

```bash
python scripts/student_info.py --json
```

This searches for `学生信息.md` in the current directory and up to 3 parent directories.

### If found

The script returns a JSON object with `姓名`, `学号`, `学院`, `专业`, `班级`. Use these values directly in the template data.

### If not found

Create the template file:

```bash
python scripts/student_info.py --create
```

Then ask the student to fill in their information in the created `学生信息.md` file. The file format is:

```markdown
# 学生信息

姓名: 张三
学号: 2024001
学院: 物理学院
专业: 应用物理
班级: 物理2401
```

---

## Step 3: Parse the Template DOCX

Identify the template file (usually a `.docx` in the project directory or provided by the student), then parse it:

```bash
python scripts/parse_docx.py --input path/to/template.docx
```

This returns a JSON structure containing:

- `paragraphs`: All text paragraphs with their styles
- `tables`: All table data as nested arrays
- `placeholders`: List of all `{{placeholder}}` patterns found in the document
- `structure`: Counts of paragraphs, tables, and headings

### Placeholder Discovery

The parser uses the regex `\{\{([^}]+)\}\}` to find Jinja2-style placeholders in both paragraphs and table cells. The returned `placeholders` list is your data contract: every item in this list must have a corresponding value in the template data JSON.

## Step 3.5: ⭐ Mandatory — Inspect Template Formatting (fix 1)

**Before writing ANY fill code, run inspect_template.py to see the exact template formatting.**

This is the single most important step. Never guess font/size/alignment.

```bash
# Dump full formatting map
python scripts/inspect_template.py --input path/to/template.docx --format human
```

Also save the JSON for the fill script:
```bash
python scripts/inspect_template.py --input path/to/template.docx --format json > .lab-report/template-inspect.json
```

### What the inspect output tells you

| Field | What it means | Your action |
|-------|---------------|-------------|
| `is_label: true` | This cell is a fixed label (like "提交文档", "实验名称"). | **PRESERVE** — do NOT overwrite. |
| `is_placeholder: true` | This cell has `{{placeholder}}` | Replace only this cell's value, keep formatting. |
| `font_name`, `font_size_pt` | Exact font and size used in each cell | **Use EXACTLY these values** — no guessing. |
| `east_asia` | CJK font override (e.g. "黑体") | **Only set eastAsia where template has it.** |
| `bold` | Whether this run is bold | Match exactly. |

### ⚠️ Critical rules derived from inspect data

1. **LABEL CELLS are sacred.** The inspect output marks them with `is_label: true`. Never overwrite them. If a template has "提交文档" in R2C3, keep it there.
2. **Font sizes and alignment are template-dictated.** Match font name, size, bold, AND alignment exactly.
3. **eastAsia is template-dictated.** Only set `w:eastAsia` on runs where the template already has it. If the template uses eastAsia=NULL on body text, do NOT add it there.
4. **Row 3 may be a merged header row.** Some templates have a large title cell spanning columns — preserve it.
5. **Alignment matters.** Table 0 (student info) value cells are typically `CENTER` aligned — match this. Check the `align=` field in inspect output.
6. **First-line indent for body paragraphs.** Chinese academic reports indent the first line of each body paragraph by 2 characters (~24pt at 12pt font). Use `fill_utils.is_body_paragraph()` to auto-detect which paragraphs need indent.
7. **Merged cell access.** When writing to cells in merged tables, **always use `table.rows[r].cells[c]`** (visual index) rather than `table.cell(r, c)` (grid index). The grid index can be offset by 1+ cells in merged tables. If you hit an IndexError, dump the table layout first to understand the merge structure.

---

### Example: building the data JSON after inspect

After reading the inspect output, you know exactly what each cell expects. Build the data JSON accordingly, using the placeholder names found by the script.

---

Each placeholder maps to one of three data sources:

| Source | Fields | How to obtain |
|--------|--------|---------------|
| Student info | 姓名, 学号, 学院, 专业, 班级 | `scripts/student_info.py` |
| Experiment progress | 实验名称, 实验步骤, 实验数据 | `.lab-report/progress.json` |
| Student description | 实验目的, 实验原理, 实验器材, 实验结果, 实验结论 | Ask the student or infer from guide content |

### Mapping Table

| Placeholder | Primary source | Fallback |
|-------------|---------------|----------|
| `{{姓名}}` | student_info | Ask student |
| `{{学号}}` | student_info | Ask student |
| `{{学院}}` | student_info | Ask student |
| `{{专业}}` | student_info | Ask student |
| `{{班级}}` | student_info | Ask student |
| `{{课程名}}` | Ask student | From guide title |
| `{{实验名称}}` | progress.experiment_name | Ask student |
| `{{实验日期}}` | Ask student | Today's date |
| `{{实验地点}}` | Ask student | From guide |
| `{{实验目的}}` | Parsed guide content | Ask student |
| `{{实验原理}}` | Parsed guide content | Ask student |
| `{{实验器材}}` | Parsed guide content | Ask student |
| `{{实验步骤}}` | progress.notes + completed steps | Ask student |
| `{{实验数据}}` | progress.notes + screenshots | Ask student |
| `{{实验结果}}` | Ask student | Infer from data |
| `{{实验结论}}` | Ask student | Infer from results |

### Missing Data Handling

If a placeholder has no data source and the student cannot provide it:

- Use `"暂无"` as the value (not an empty string, which would break table layouts)
- Flag the placeholder as incomplete in the output summary

---

## Step 4.5: Analyze Experiment Photos (fix 3.1 / 3.2)

**Before building the template data JSON, scan the project directory for experiment photos/videos and analyze them.**

### Discovery

```bash
glob("**/*.jpg")  # or .png, .jpeg, .mp4, .gif
```

Common folder names: `实验一照片/`, `实验图片/`, `screenshots/`, `实验现象/`

### Required Analysis

For **every image or video file found**, invoke the `read` or `look_at` tool to visually analyze its content:

| Photo Type | What to extract |
|------------|----------------|
| **Code screenshots** | Actual delay values, GPIO pin numbers, loop logic, register names |
| **Hardware wiring** | Port connections, breadboard layout, LED positions |
| **LED/display status** | Which LEDs are lit, color, brightness, timing sequence |
| **Measurement results** | Oscilloscope readings, multimeter values, signal waveforms |
| **Videos** | Playback duration, LED flow direction, blink frequency (estimate) |

### Cross-Validation

Compare extracted information against the experiment guide requirements:

- Are the timing values in the code consistent with what the guide asks for?
- Is the wiring diagram consistent with the described pin connections?
- If inconsistencies found, flag them to the student for confirmation:
  ```
  照片中显示延时为 2500ms，但实验指导书要求 500ms。请确认：你实际使用了哪个值？
  ```

### Integration into Report Content

Use the information extracted from photos to make report content accurate:

- **实验原理**: Describe the **actual** code logic observed, not just generic theory
- **实验数据**: Record actual timing values, LED states from photos
- **实验结果**: Reference specific photo observations
- **实验现象**: Describe what the photos/videos actually show

### Image Placeholder Insertion

After analysis, create an image placeholder instruction file (`.lab-report/image-placeholders.json`) so `fill_template.py` can mark where photos should go:

```json
[
  {
    "placeholder": "[insert_image_wiring]",
    "label": "请在此处粘贴：硬件接线照片"
  },
  {
    "placeholder": "[insert_image_led_flow]",
    "label": "请在此处粘贴：LED流水灯现象视频截图"
  }
]
```

In the report content, add these markers at appropriate locations. The `fill_template.py --image-placeholders` flag will replace them with styled placeholders.

### Image Insertion into the Report (Step 4.5b)

**If the project directory contains experiment screenshots/photos**, scan and insert them.

#### Scan for images
```bash
glob("**/*.jpg"); glob("**/*.png"); glob("**/screenshots/*"); glob("**/实验照片/*")
```

#### For each image, analyze with `read`/`look_at`, then build config:
```json
[
  {"match": "实验步骤", "path": "screenshots/wiring.jpg", "caption": "硬件接线图"},
  {"match": "实验现象", "path": null,                    "caption": "此处插入LED流水灯照片"}
]
```
- `match`: Text in a paragraph to find insertion point
- `path`: Image path. **null** → styled placeholder `[此处插入照片]`
- `caption`: Image caption or placeholder label

#### Fill with images
```bash
python scripts/fill_template.py \
  -t template.docx -d data.json -o output.docx \
  --inspect inspect.json \
  --images .lab-report/image-config.json
```

**Result**: Valid images → centered, 5.2in wide, caption below. Missing → grey italic placeholder.

---

Create a JSON file (e.g., `.lab-report/template-data.json`) with all required fields:

```json
{
  "姓名": "张三",
  "学号": "2024001",
  "学院": "物理学院",
  "专业": "应用物理",
  "班级": "物理2401",
  "课程名": "大学物理实验",
  "实验名称": "电阻的测量",
  "实验日期": "2025-04-24",
  "实验地点": "物理实验楼301",
  "实验目的": "掌握伏安法测电阻的原理和方法...",
  "实验原理": "根据欧姆定律 R = U/I...",
  "实验器材": "直流稳压电源、电压表、电流表、电阻箱...",
  "实验步骤": "1. 按电路图连接电路\n2. 调节电源电压至3V\n...",
  "实验数据": "电压/V: 3.0, 电流/mA: 15.2...",
  "实验结果": "测得电阻值为 197.4Ω...",
  "实验结论": "伏安法测电阻结果与标称值接近..."
}
```

### Content Quality Guidelines

When generating content for placeholders from student descriptions or guide content:

- Write in **first person plural** (我们) for experiment steps and observations
- Use **past tense** for completed actions (连接了, 测量了)
- Keep data sections factual and numerical
- Conclusions should reference specific data points
- Avoid banned AI phrases (see `fill_template.py` BANNED_WORDS): 首先, 其次, 最后, 总而言之, 值得注意的是, 综上所述, 不可否认

---

## Step 6: Fill the Template

**Always pass the inspect JSON** so the script preserves labels and uses correct formatting:

```bash
python scripts/fill_template.py \
  --template path/to/template.docx \
  --data .lab-report/template-data.json \
  --inspect .lab-report/template-inspect.json \
  --output output/实验报告.docx \
  --style normal
```

### Style Options

| Style | Behavior | When to use |
|-------|----------|-------------|
| `normal` | 标准实验报告，内容完整规范，90+分水平。日常使用首选。 | 日常提交 |
| `perfect` | 极尽详尽，覆盖所有细节。用于特别重要的场景。 | 特殊场景 |

Both styles apply CJK font fixes (宋体 for body text, 黑体 for headings) via the `w:eastAsia` attribute.

### What the Script Does (Inspect-based)

1. Copies the template to the output path (never modifies the original)
2. Loads the **inspect data** — knows exactly which cells are labels (preserved), which are placeholders
3. Renders all `{{placeholder}}` fields via docxtpl
4. **Restores any accidentally overwritten label cells** (safety net — fix 2)
5. **Applies formatting from inspect data** — font/size/bold/eastAsia/alignment all matched exactly (fix 1, 5)
6. **Applies paragraph alignment** from template (CENTER for table 0 value cells — fix 2.1)
7. **Applies first-line indent** for body paragraphs (list items auto-detected and skipped — fix 2.2)
8. Sets CJK font (`eastAsia`) **only** where template explicitly had it (fix 5)
9. **Post-fill diff check** — detects any label cells that got overwritten and warns
10. Checks for unreplaced placeholders
11. Returns JSON with `success`, `warnings`, `placeholders_missing`

---

## Step 7: Verify Output

After filling, check the result JSON for:

### Unreplaced Placeholders

If `placeholders_missing` is non-empty, the template has unfilled fields. For each missing placeholder:

1. Check if the data JSON has the corresponding key
2. If the key exists but is empty, the value was likely blank
3. If the key is missing, add it to the data JSON and re-run

### CJK Font Verification

The script automatically sets CJK fonts, but verify manually if the output looks wrong:

- Body text should use 宋体 (SimSun)
- Headings should use 黑体 (SimHei)
- The `w:eastAsia` attribute on `w:rFonts` ensures CJK characters render correctly

---

## Step 8: Git 文件管理

### 默认：仅报告（文件保留在 Changes 面板）

```bash
python scripts/git_manager.py
```

输出示例：
```
📂 以下文件已生成/修改（可在 Changes 面板查看）：
  [新文件] 实验一 - 陈虹宇.docx
💡 确认无误后运行: python scripts/git_manager.py --stage
```

### 暂存（git add）

```bash
python scripts/git_manager.py --stage
```
⚠️ 暂存后文件从 Changes 移到 Staged Changes（VSCode 默认折叠）

### 直接提交（跳过审查）

```bash
python scripts/git_manager.py --commit --message "生成实验报告"
```

---

## Complete Workflow Diagram

```
[Start Work Mode]
       │
       ▼
  Confirm experiment metadata (date/location/teacher/group) ← NEW
       │
       ▼
  Ask style (normal / perfect)
       │
       ▼
  Progress exists? ──No──► Ask student to describe experiment
       │                         │
      Yes                        │
       │                         │
       ▼                         ▼
  Read progress.json        Collect description
       │                         │
       └─────────┬───────────────┘
                  │
                  ▼
         Collect student info
         (student_info.py)
                  │
                  ▼
         ⭐ Inspect template ← NEW: MANDATORY
         (inspect_template.py --format json)
                  │
                  ▼
         Map placeholders → data sources
                  │
                  ▼
         Build template-data.json
                  │
                  ▼
         Fill template (with --inspect data)
         (fill_template.py --inspect inspect.json)
                  │
                  ▼
         Post-fill diff check ← NEW: auto detect label overwrites
                  │
                  ▼
         Verify: no unreplaced placeholders?
            │              │
           Yes             No ──► Fix data, re-fill
            │
            ▼
         Stage for review (default — visible in sidebar)
         (git_manager.py)
                  │
                  ▼
            [Done]
```

---

## Error Handling

| Situation | Response |
|-----------|----------|
| No template DOCX found | Ask student to provide one; list available `.docx` and `.doc` files in the directory |
| Template has no placeholders | The template may use a different syntax; ask student to confirm |
| Data JSON missing keys | Prompt student for missing values; use "暂无" as fallback |
| `fill_template.py` fails | Check error message; common causes: missing dependency, corrupted template |
| Unreplaced placeholders remain | Identify which ones, ask student for values, rebuild data JSON |
| CJK characters display as tofu | Check if template had eastAsia set; if not, don't add it — the issue is elsewhere |
| Student info file not found | Create template with `student_info.py --create`, ask student to fill it in |
| Photos/videos found but not analyzed | Delegate `read` or `look_at` for each image; extract code values and wiring details |
| **Label cell overwritten** | Revert to template, re-run with `--inspect` flag. The script now auto-restores labels. |
| **Font/size mismatch** | Did you run `inspect_template.py` before filling? The inspect output has exact values. |
| **eastAsia over-applied** | Did you use `--inspect`? Without it, the script falls back to old behavior. Always use `--inspect`. |

---

## Quick Reference: CLI Commands

```bash
# Check for existing progress
python scripts/progress_manager.py

# Get student info
python scripts/student_info.py --json

# ⭐ MANDATORY: Inspect template before fill
python scripts/inspect_template.py --input template.docx --format human
python scripts/inspect_template.py --input template.docx --format json > .lab-report/template-inspect.json

# Create student info template
python scripts/student_info.py --create

# Parse template DOCX (optional — inspect does this too)
python scripts/parse_docx.py --input template.docx

# Fill template with inspect data
python scripts/fill_template.py \
  -t template.docx \
  -d .lab-report/template-data.json \
  --inspect .lab-report/template-inspect.json \
  -o output.docx --style normal

# Fill template (perfect style)
python scripts/fill_template.py \
  -t template.docx -d .lab-report/template-data.json \
  --inspect .lab-report/template-inspect.json \
  -o output.docx --style perfect

# Git — 默认仅报告（文件保留在 Changes 面板）
python scripts/git_manager.py

# Git — 暂存（文件进入 Staged Changes）
python scripts/git_manager.py --stage

# Git — 直接提交
python scripts/git_manager.py --commit --message "生成实验报告"

# Git — 初始化仓库
python scripts/git_manager.py --init

# Init git repo
python scripts/git_manager.py --init
```


---

## 附录：常见高校实验报告模板类型