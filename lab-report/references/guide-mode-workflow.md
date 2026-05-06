# Guide Mode Workflow

Guide Mode walks a student through an experiment step by step, tracking progress and prompting screenshots at the right moments.

---

## Step 0: Pre-Flight Checks (MANDATORY)（旧项目兼容 `.labmate/`）

### 0.0 Read project.md

If `project.md` exists in the project root, read it first. It contains course info (course name, code, teacher) and experiment progress — no need to scan the entire directory or ask the user for these.

### 0.1 Scan Reference Resources

Before parsing the guide, scan the project directory for **pre-existing code and reference files**:

```bash
glob("**/供参考/*")        # Common naming: 供参考, 参考, reference
glob("**/*.cs")             # C# scripts (Unity)
glob("**/Scripts/*.cs")     # Unity Scripts folder
```

List ALL found files to the student and flag them:
```
📂 发现以下可参考资源（可能已有可用方案）：
- Scripts/RespawnScript.cs (2.1 KB)
- 实验1-相关资源(供参考)/Step1_基础移动.cs
💡 这些代码可以直接阅读参考，避免从零实现。
```

### 0.2 Environment Compatibility Check

When the experiment guide was written for an older environment version and mentions **specific APIs, library functions, or tool features**, check compatibility BEFORE executing:

```
⚠️ 兼容性检查提醒：
- MeshCollider.IsTrigger → 2020+ 中 Plane 的 MeshCollider 不能设为 Trigger。替代：BoxCollider 或坐标检测。
- WWW 类 → 2018.3 已废弃。替代：UnityWebRequest。
- 如果 API 不确定 → 先查官方文档（unity_docs lookup）再动手。
```

### 0.3 Git Savepoint (Strongly Recommended)

If git is enabled, create a savepoint **before each code modification**:

```bash
python scripts/git_manager.py --commit --message "savepoint: before step N"
```

This allows instant rollback if a modification breaks existing functionality.

---

## Step 1: Parse the Experiment Guide

### Input Sources

The experiment guide can arrive as:

- A **PDF** file, parsed by `scripts/parse_pdf.py`
- A **PPTX** file, parsed by `scripts/parse_pptx.py`

### Parsing PDF

```bash
python scripts/parse_pdf.py --input path/to/guide.pdf --format json
```

Returns a JSON structure with `text_by_page` and `markdown` fields. If `is_scanned` is `true`, warn the student that OCR quality may be low and ask them to describe unclear steps.

### Parsing PPTX

```bash
python scripts/parse_pptx.py --input path/to/guide.pptx --format json
```

Returns a JSON structure with `slides`, each containing `title` and `content` arrays.

### Step Extraction Heuristics

After parsing, extract steps from the raw text using these patterns:

1. **Numbered lists**: Lines starting with `1.`, `2.`, `3.` or `（1）`, `（2）`, `（3）`
2. **Imperative sentences**: Lines containing verbs like 连接, 测量, 观察, 记录, 调节, 设置, 安装, 拍摄
3. **Procedure sections**: Content under headings like 实验步骤, 操作步骤, 实验过程
4. **Sequential instructions**: Sentences joined by 然后, 接着, 之后

Group extracted steps into a numbered list. Each step should be a single actionable instruction, not a paragraph.

### ⭐ Extracting Content for the Report

When the experiment guide contains sections matching standard report sections, **extract and preserve the original text verbatim**:

| If guide contains... | → Store for Work Mode as... |
|---------------------|---------------------------|
| 实验目的 section | Report 实验目的 content (use exactly) |
| 实验原理 section | Report 实验原理 content (use exactly) |
| 实验器材/设备 section | Report 实验器材 content (use exactly) |
| 实验步骤 section | Report 实验步骤 content (use as base, add observations) |
| 实验要求 section | Report 实验要求 content (use exactly) |

**Rules**:
- Do NOT paraphrase, summarize, or "improve" the guide's own text for these sections
- Only add content for sections the guide does NOT cover
- Record which sections came from the guide vs were AI-generated
- Save extracted content to `.labmate/guide-content.json` for Work Mode to pick up

---

## Step 2: Identify Screenshot-Worthy Steps

Scan each extracted step for these keywords:

| Keyword | Reason |
|---------|--------|
| 测量 | Measurement readings need visual proof |
| 连接 | Circuit or apparatus setup must be documented |
| 观察 | Observable phenomena should be captured |
| 记录 | Recorded data often comes from instrument displays |
| 拍摄 | Explicit instruction to take a photo |

Mark any step containing these keywords as `screenshot_required: true` in the progress data.

---

## Step 3: Initialize Progress Tracking

Use `scripts/progress_manager.py` to create the progress file:

```bash
python scripts/progress_manager.py --init --experiment "实验名称" --total-steps N
```

This creates `.labmate/progress.json` with the structure defined in `schemas.md`.

For each screenshot-worthy step, register it:

```bash
python scripts/progress_manager.py --screenshot --step 3 --description "测量电压表读数"
```

---

## Step 4: Present All Steps to the Student

Display the full step list at once in a clear format:

```
📋 实验名称: 电阻的测量
共 6 个步骤:

1. 连接电路（📸 需要截图）
2. 调节电源电压至 3V
3. 测量并记录电压表读数（📸 需要截图）
4. 测量并记录电流表读数（📸 需要截图）
5. 断开电路，更换电阻
6. 观察并记录实验现象（📸 需要截图）

说"继续"开始第一步，或询问任何步骤的详细说明。
```

### Presentation Rules

- Show **all steps at once**, not one at a time
- Mark screenshot steps with 📸
- Tell the student they can ask about any specific step at any time
- Include the total step count so the student knows the scope

---

## Step 5: Progress Sync Protocol

The student drives progress. The AI responds to these triggers:

### Student says "继续"

1. Read current progress: `python scripts/progress_manager.py`
2. Determine the next incomplete step (smallest step number not in `completed_steps`)
3. Mark it as `in_progress`:
   ```bash
   python scripts/progress_manager.py --step N --status in_progress
   ```
4. Present the step with any relevant tips
5. If the step requires a screenshot, remind the student (see Step 6)

### Student says a step is done

1. Mark the step as `completed`:
   ```bash
   python scripts/progress_manager.py --step N --status completed
   ```
2. If the step had a screenshot requirement, ask if they captured it
3. Show remaining steps count

### Student asks about a specific step

1. Look up the step in the parsed guide content
2. Provide detailed explanation, tips, and common mistakes
3. Do **not** advance the progress counter
4. Remind about screenshots if applicable

### Student says "跳过" (skip)

1. Mark the step as `skipped`:
   ```bash
   python scripts/progress_manager.py --step N --status skipped
   ```
2. Note the skip in progress notes:
   ```bash
   python scripts/progress_manager.py --step N --note "学生跳过了此步骤"
   ```

### ⚠️ Hard Rule: 3 Failures Per Approach = Change Strategy

When debugging or implementing a step, if the SAME solution approach has failed 3 times:

1. **STOP** immediately — do NOT continue the same approach
2. **Record** the failures in debug_history
3. **Propose** at least 2 alternative approaches
4. **Ask** the student which alternative to try
5. **Switch** to the chosen alternative

```
❌ 同一方案已失败 3 次！不再继续调参。
📋 已记录的失败原因： {列出每一次失败的具体报错}

🔀 替代方案：
A) {方案 A — 不同 API/不同架构}
B) {方案 B — 完全不同的思路}
C) 先回退到步骤 N 之前，重新开始

请选择替代方案：
```

### Recording Debug History

When a modification fails with an error, record it:

```bash
python scripts/progress_manager.py --debug --step N --error "error message" --attempt 1
```

This appends to `debug_history` in progress.json:

```json
{
  "debug_history": [
    {
      "step": 5,
      "attempt": 1,
      "timestamp": "2026-04-25T14:30:00",
      "error": "NullReferenceException: MeshCollider on Plane cannot be set to IsTrigger",
      "approach": "MeshCollider.IsTrigger on Plane"
    }
  ]
}
```

### ⚠️ Minimum-Change Principle

When modifying code to fix an issue:
1. Change only ONE thing at a time
2. Test immediately after the single change
3. If it fixes the issue, stop — don't "clean up" or make additional changes
4. If it doesn't fix, revert that change before trying another

Avoid: "I'll fix the Trigger AND adjust the player position AND change the GameControl... now let me test."

---

## Step 6: Screenshot Reminders

### When to Remind

- **Before** a screenshot-worthy step begins (not after)
- Format: `📸 提醒: 这一步需要拍照记录 [description]`

### What to Capture — Be Specific

Instead of generic "请拍照", tell the student exactly what to photograph:

| Experiment Phase | Specific photo guidance |
|-----------------|------------------------|
| 硬件连接完成后 | 📸 拍摄完整接线图（确保所有端口清晰可见） |
| 第一次上电时 | 📸 拍摄初始状态（LED 亮灭情况、屏幕显示数据） |
| 修改参数后 | 📸 拍摄修改后的现象对比 |
| 测量数据时 | 📸 拍摄仪器读数、示波器波形、万用表数值 |
| 代码界面 | 📸 拍摄代码截图或拍照（确保延时值、引脚号清晰） |
| 实验结束 | 📸 拍摄最终实验成果（如流水灯完整效果） |

### After the Step

- If the step was screenshot-worthy and the student marks it complete, ask:
  `这一步的截图拍好了吗？如果拍了，可以告诉我截图的文件名。`

### Recording Screenshots

When the student provides a screenshot path:

```bash
python scripts/progress_manager.py --screenshot --step N --path "screenshots/step_N.jpg"
```

This sets `captured: true` in the progress data.

---

## Step 7: Post-Experiment Photo Collection Review

⚠️ AI 无法自动验证截图内容的正确性。以下分析仅作参考，请自行确认所有截图与实际实验内容一致。

After all steps are completed but before transitioning to Work Mode, **actively review the captured screenshots/photos directory**.

### Discovery

Check for common screenshot directories:
```bash
glob("**/screenshots/*")
glob("**/实验一照片/*")
glob("**/*.jpg")  
glob("**/*.png")
```

### Analysis

For each detected photo, delegate `read` or `look_at` to extract:

1. **Code screenshots**: Read actual delay values, GPIO pins, loop structures
2. **Hardware photos**: Confirm wiring matches described connections
3. **Phenomenon photos**: Confirm described LED states match images

### Cross-check

Compare extracted photo data against what was recorded during Guide Mode:

- If photo shows `delay_ms(2500)` but student said "500ms" → flag inconsistency
- If photo shows LED on pin PB0 but guide says PA1 → flag for confirmation

### Report for Work Mode

Save the photo analysis findings to use in Work Mode:

```json
{
  "photos_analyzed": 9,
  "code_values_extracted": {"delay_ms": 2500, "gpio_port": "PB0"},
  "wiring_confirmed": true,
  "inconsistencies": []
}
```

---

## Step 8: Completion

When all steps are done (`status` becomes `completed`):

1. Summarize what was accomplished
2. List any skipped steps
3. List any missing screenshots
4. Suggest transitioning to **Work Mode** to generate the lab report

```
✅ 实验完成！

完成步骤: 5/6
跳过步骤: 1 (步骤2)
缺失截图: 1 (步骤4)

建议: 现在可以切换到 Work Mode 生成实验报告了。
```

---

## Step 8.5: Auto-Commit Before Transition

When the user explicitly indicates they are moving to the next task — such as saying **"开始下一个实验"、"下一步"、"继续实验二"** etc. — **commit the current work first**:

```bash
python scripts/git_manager.py --commit --message "实验一完成：{要点}"
```

**Why**: This creates a named savepoint that can be reverted to if needed. Future agents loading the session can see exactly what was done in each experiment.

**When to trigger**:
- User says "开始下一个实验" / "继续实验二" / "下一步"
- User says "生成实验报告" after Guide Mode completes
- Any explicit transition intent

**Don't trigger on**: casual conversation, step-by-step progress updates during the same experiment.

---

## Error Handling

| Situation | Response |
|-----------|----------|
| PDF is scanned | Warn student, ask them to describe unclear parts |
| No steps detected | Ask student to describe the experiment procedure in their own words |
| Progress file corrupted | Re-initialize with `--reset` and ask student to confirm step count |
| Student provides wrong step number | List current steps and ask them to clarify |
| Student asks about a step not in the guide | Use the parsed content to provide context; if unavailable, say so honestly |
| Photo shows different values than described | Flag the inconsistency: "照片显示延时=2500ms，你之前说的是500ms，请问实际是哪个？" |
| Student did not take required screenshots | Remind before transitioning to Work Mode; suggest taking photos now |
| Video file found | Use `read` tool to extract duration and visual content; describe phenomenon from video |

---

## Quick Reference: CLI Commands

```bash
# Initialize progress
python scripts/progress_manager.py --init --experiment "名称" --total-steps N

# Check current progress
python scripts/progress_manager.py

# Mark step in progress
python scripts/progress_manager.py --step N --status in_progress

# Mark step completed
python scripts/progress_manager.py --step N --status completed

# Skip a step
python scripts/progress_manager.py --step N --status skipped

# Add screenshot requirement
python scripts/progress_manager.py --screenshot --step N --description "描述"

# Record screenshot path
python scripts/progress_manager.py --screenshot --step N --path "path/to/file.jpg"

# Add a note
python scripts/progress_manager.py --step N --note "备注内容"

# Record debug failure
python scripts/progress_manager.py --debug --step N --error "error message" --attempt 1 --approach "approach name"

# Reset progress
python scripts/progress_manager.py --reset --experiment "名称" --total-steps N

# Git — 默认仅报告（文件保留在 Changes 面板）
python scripts/git_manager.py

# Git — 暂存（文件进入 Staged Changes）
python scripts/git_manager.py --stage

# Git — 直接提交
python scripts/git_manager.py --commit --message "实验完成"
```