#!/usr/bin/env python3
"""Git 管理 — 默认仅报告文件位置（不做 stage，保留在 Changes 面板可见）。"""

import argparse
import subprocess
import sys
from pathlib import Path

GITIGNORE_CONTENT = """# Python
__pycache__/
*.pyc
*.pyo
.venv/
uv.lock
# IDE
.vscode/
.idea/
*.swp
*.swo
"""


def is_git_repo(directory: Path) -> bool:
    return (directory / ".git").exists()


def get_git_status(directory: Path) -> tuple:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory, capture_output=True, text=True, check=True)
        untracked = []
        modified = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            status = line[:2]
            filename = line[3:]
            if status.startswith('??'):
                untracked.append(filename)
            elif status.startswith((' M', 'M ', 'A ')):
                modified.append(filename)
        return untracked, modified
    except subprocess.CalledProcessError:
        return [], []


def git_init(directory: Path) -> bool:
    """初始化 git 仓库并创建 .gitignore"""
    try:
        if (directory / ".git").exists():
            print("Git 仓库已存在")
            return True
        subprocess.run(["git", "init"], cwd=directory, capture_output=True, check=True)
        gitignore = directory / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(GITIGNORE_CONTENT.strip(), encoding='utf-8')
            subprocess.run(["git", "add", ".gitignore"], cwd=directory, capture_output=True)
            subprocess.run(["git", "commit", "-m", "初始配置：添加 .gitignore"],
                           cwd=directory, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=directory, capture_output=True)
        subprocess.run(["git", "commit", "-m", "初始提交"], cwd=directory, capture_output=True)
        print(f"Git 仓库初始化完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git 初始化失败: {e}", file=sys.stderr)
        return False


def report_status(directory: Path):
    """默认：仅报告文件状态，不做任何 git 操作。"""
    untracked, modified = get_git_status(directory)
    all_files = untracked + modified
    if not all_files:
        print("没有待处理的文件")
        return
    print(f"\n📂 以下文件已生成/修改（可在 Changes 面板查看）：")
    for f in untracked:
        print(f"  [新文件] {f}")
    for f in modified:
        print(f"  [已修改] {f}")
    print(f"\n💡 确认无误后运行: python scripts/git_manager.py --stage  # 暂存")
    print(f"   或直接提交: python scripts/git_manager.py --commit -m \"提交说明\"")
    return all_files


def git_stage(directory: Path):
    """执行 git add（文件进入 Staged Changes，可能默认折叠）。"""
    try:
        untracked, modified = get_git_status(directory)
        if not untracked and not modified:
            print("没有可暂存的文件")
            return True
        subprocess.run(["git", "add", "-A"], cwd=directory, capture_output=True, check=True)
        print(f"已暂存 {len(untracked) + len(modified)} 个文件")
        print("⚠️  注意：暂存后文件从 Changes 移到 Staged Changes（默认折叠）")
        print("   在 VSCode 中展开 Source Control 面板的 'Staged Changes' 查看")
        return True
    except subprocess.CalledProcessError as e:
        print(f"暂存失败: {e}", file=sys.stderr)
        return False


def git_stage_and_commit(directory: Path, message: str):
    """执行 git add + git commit"""
    try:
        untracked, modified = get_git_status(directory)
        if not untracked and not modified:
            print("没有可提交的文件")
            return True
        subprocess.run(["git", "add", "-A"], cwd=directory, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=directory, capture_output=True, check=True)
        print(f"已提交: {message}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"提交失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Git 管理 — 默认仅报告状态（文件保留在 Changes 面板可见）')
    parser.add_argument('--dir', type=Path, default=Path.cwd(), help='目标目录')
    parser.add_argument('--message', '-m', help='提交信息（仅与 --commit 一起使用）')
    parser.add_argument('--stage', action='store_true',
                        help='执行 git add（文件进入 Staged Changes）')
    parser.add_argument('--commit', action='store_true',
                        help='执行 git add + git commit')
    parser.add_argument('--init', action='store_true',
                        help='初始化 Git 仓库并创建 .gitignore')
    args = parser.parse_args()

    if args.init:
        sys.exit(0 if git_init(args.dir) else 1)

    if not is_git_repo(args.dir):
        # 非 git 仓库 → 仅报告文件位置
        print("当前目录不是 Git 仓库")
        print("使用 --init 初始化，或直接在文件管理器中查看生成的文件")
        sys.exit(0)

    if args.commit:
        msg = args.message or "自动提交"
        sys.exit(0 if git_stage_and_commit(args.dir, msg) else 1)
    elif args.stage:
        sys.exit(0 if git_stage(args.dir) else 1)
    else:
        # 默认：仅报告
        report_status(args.dir)
        sys.exit(0)


if __name__ == '__main__':
    main()
