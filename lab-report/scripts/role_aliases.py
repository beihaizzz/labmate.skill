# -*- coding: utf-8 -*-
"""Shared label-role mapping and cell classification utilities."""

import re
from pathlib import Path

# Make imports work when this file is used standalone or from same-directory scripts
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
except Exception:
    pass

# 常见标签文本 → 标准化角色名
ROLE_ALIASES = {
    "课程名称": "课程名称",
    "课程": "课程名称",
    "课程代码": "课程代码",
    "任课教师": "任课教师",
    "教师": "任课教师",
    "指导教师": "任课教师",
    "学生姓名": "学生姓名",
    "姓名": "学生姓名",
    "年级": "专业年级",
    "专业年级": "专业年级",
    "专业": "专业年级",
    "班级": "专业年级",
    "学号": "学号",
    "实验名称": "实验名称",
    "实验项目": "实验名称",
    "实验类型": "实验类型",
    "实验学时": "实验学时",
    "实验日期": "实验日期",
    "实验地点": "实验地点",
    "实验环境": "实验环境",
    "实验设备": "实验设备",
    "提交文档": "提交文档说明",
    "实验成绩": "实验成绩",
}

# Hint/placeholder text patterns
HINT_PATTERNS = [
    r'_{3,}',          # _____, _______
    r'（请填写）',      # （请填写）
    r'\(请填写\)',      # (请填写)
    r'待定',            # 待定
    r'待填',            # 待填
    r'\[请填写\]',       # [请填写]
    r'请在此处填写.*',   # 请在此处填写...
]


def is_hint_text(text: str) -> bool:
    """Return True if text matches any hint/placeholder pattern."""
    t = text.strip()
    for pattern in HINT_PATTERNS:
        if re.search(pattern, t):
            return True
    return False


def _contains_cjk(text: str) -> bool:
    """Check if text contains any CJK characters (Unicode range U+4E00-U+9FFF)."""
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)


def is_label_cell_v2(text: str) -> bool:
    """Enhanced label cell classification with stricter heuristics.

    Returns True only if ALL conditions are met:
    - Text is not empty after stripping
    - Length ≤ 12 characters
    - Contains mostly CJK characters
    - Does NOT start with digits or bullet patterns (1., （1）, ①)
    - Does NOT match hint/placeholder patterns
    """
    t = text.strip()
    if not t:
        return False

    # Must be ≤ 12 characters (stricter than old 20)
    if len(t) > 12:
        return False

    # Must contain CJK characters
    if not _contains_cjk(t):
        return False

    # Must NOT start with digits or bullet patterns
    bullet_patterns = (r'^\d+\.', r'^（\d+）', r'^[①-⑨]')
    for pattern in bullet_patterns:
        if re.match(pattern, t):
            return False

    # Must NOT be hint/placeholder text
    if is_hint_text(t):
        return False

    return True


def _normalize_role(text: str) -> str:
    """Standardize label text to a known role name."""
    t = text.strip().replace("：", "").replace(":", "").replace(" ", "").replace("\n", "")
    for key, value in ROLE_ALIASES.items():
        if key in t:
            return value
    return t


if __name__ == '__main__':
    # Quick test when run directly
    test_cases = [
        ("姓名", True),
        ("姓名：", True),
        ("1. 连接电路", False),
        ("_____", False),
        ("学号：", True),
        ("这是一个很长的标签文本超过12字", False),
        ("实验成绩", True),
        ("待定", False),
        ("请在此处填写实验结果", False),
    ]

    print("is_label_cell_v2 tests:")
    for text, expected in test_cases:
        result = is_label_cell_v2(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{text}' -> {result} (expected {expected})")

    print("\nis_hint_text tests:")
    for text, expected in [
        ("_____", True),
        ("（请填写）", True),
        ("待定", True),
        ("姓名", False),
    ]:
        result = is_hint_text(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{text}' -> {result}")