#!/usr/bin/env python3
"""Git stage manager. Default: stage only (shows in review sidebar)."""

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

# 实验截图（属于实验数据，不忽略）
# screenshots/
# 实验照片/

# IDE
.vscode/
.idea/
*.swp
*.swo
"""


def is_git_repo(directory: Path) -> bool:
    git_dir = directory / ".git"
    return git_dir.exists()


def get_git_status(directory: Path) -> tuple:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory,
            capture_output=True,
            text=True,
            check=True
        )

        untracked = []
        modified = []

        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            status = line[:2]
            filename = line[3:]

            if status.startswith('??'):
                untracked.append(filename)
            elif status.startswith(' M') or status.startswith('M ') or status.startswith('A'):
                modified.append(filename)

        return untracked, modified
    except subprocess.CalledProcessError:
        return [], []


def git_init(directory: Path) -> bool:
    """Initialize git repo and create .gitignore."""
    try:
        if (directory / ".git").exists():
            print("Git 仓库已存在")
            return True

        subprocess.run(["git", "init"], cwd=directory, capture_output=True, check=True)

        gitignore = directory / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(GITIGNORE_CONTENT.strip(), encoding='utf-8')
            print("已创建 .gitignore")
            subprocess.run(["git", "add", ".gitignore"], cwd=directory, capture_output=True)
            subprocess.run(["git", "commit", "-m", "初始配置：添加 .gitignore"],
                           cwd=directory, capture_output=True)

        subprocess.run(["git", "add", "-A"], cwd=directory, capture_output=True)
        subprocess.run(["git", "commit", "-m", "初始提交"],
                       cwd=directory, capture_output=True)
        print(f"Git 仓库初始化完成: {directory}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git 初始化失败: {e}", file=sys.stderr)
        return False


def generate_commit_message(untracked: list, modified: list, custom_msg: str = None) -> str:
    if custom_msg:
        return custom_msg

    files = untracked + modified
    if not files:
        return "Auto-commit: no changes"
    if len(files) == 1:
        return f"Auto-commit: update {files[0]}"
    return f"Auto-commit: update {len(files)} files"


def git_stage(directory: Path, dry_run: bool = False) -> bool:
    """Stage all changes (git add) without committing.
    
    Files appear in OpenCode Desktop review sidebar for user to inspect.
    """
    try:
        untracked, modified = get_git_status(directory)
        if not untracked and not modified:
            print("No changes to stage")
            return True

        if dry_run:
            print("Dry run — would stage:")
            for f in untracked:
                print(f"  [new] {f}")
            for f in modified:
                print(f"  [mod] {f}")
            return True

        subprocess.run(
            ["git", "add", "-A"],
            cwd=directory,
            capture_output=True,
            check=True
        )

        untracked2, modified2 = get_git_status(directory)
        staged = [f for f in (untracked2 + modified2)]
        print(f"Staged {len(staged)} file(s). They now appear in the review sidebar.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        return False


def git_stage_and_commit(directory: Path, message: str, dry_run: bool = False) -> bool:
    """Stage all changes and commit (old behavior, bypasses review sidebar)."""
    try:
        untracked, modified = get_git_status(directory)
        if not untracked and not modified:
            print("No changes to commit")
            return True

        if dry_run:
            print("Dry run — would commit:")
            for f in untracked:
                print(f"  [new] {f}")
            for f in modified:
                print(f"  [mod] {f}")
            print(f"Message: {message}")
            return True

        subprocess.run(
            ["git", "add", "-A"],
            cwd=directory,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=directory,
            capture_output=True,
            check=True
        )
        print(f"Committed: {message}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Git manager — stages by default (review sidebar friendly). '
                    'Use --commit to skip review and commit directly.'
    )
    parser.add_argument('--dir', type=Path, default=Path.cwd(), help='Target directory')
    parser.add_argument('--message', '-m', help='Commit message (only used with --commit)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--commit', action='store_true',
                        help='Stage AND commit (bypasses review sidebar). '
                             'Omit this flag to only stage (visible in review sidebar).')
    parser.add_argument('--init', action='store_true',
                        help='初始化 Git 仓库并创建 .gitignore')
    args = parser.parse_args()

    if args.init:
        success = git_init(args.dir)
        sys.exit(0 if success else 1)

    if not is_git_repo(args.dir):
        sys.exit(0)

    untracked, modified = get_git_status(args.dir)

    if args.commit:
        # Old behavior: auto-commit (files won't appear in review sidebar)
        message = generate_commit_message(untracked, modified, args.message)
        success = git_stage_and_commit(args.dir, message, args.dry_run)
    else:
        # New default: stage only (files appear in review sidebar)
        success = git_stage(args.dir, args.dry_run)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
