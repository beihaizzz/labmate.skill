#!/usr/bin/env python3
"""Git auto-commit manager."""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def is_git_repo(directory: Path) -> bool:
    """Check if directory is a git repository."""
    git_dir = directory / ".git"
    return git_dir.exists()

def get_git_status(directory: Path) -> tuple:
    """Get git status - returns (untracked, modified)."""
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
            elif status.startswith(' M') or status.startswith('M '):
                modified.append(filename)

        return untracked, modified
    except subprocess.CalledProcessError:
        return [], []

def generate_commit_message(untracked: list, modified: list, custom_msg: str = None) -> str:
    """Generate commit message."""
    if custom_msg:
        return custom_msg

    files = untracked + modified
    if not files:
        return "Auto-commit: no changes"

    if len(files) == 1:
        return f"Auto-commit: update {files[0]}"
    else:
        return f"Auto-commit: update {len(files)} files"

def git_commit(directory: Path, message: str, dry_run: bool = False) -> bool:
    """Stage and commit changes."""
    try:
        # Get status first
        untracked, modified = get_git_status(directory)

        if not untracked and not modified:
            print("No changes to commit")
            return True

        if dry_run:
            print("Dry run - would commit:")
            for f in untracked:
                print(f"  [new] {f}")
            for f in modified:
                print(f"  [mod] {f}")
            print(f"Message: {message}")
            return True

        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=directory,
            capture_output=True,
            check=True
        )

        # Commit
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
    parser = argparse.ArgumentParser(description='Git auto-commit manager')
    parser.add_argument('--dir', type=Path, default=Path.cwd(), help='Target directory')
    parser.add_argument('--message', '-m', help='Custom commit message')
    parser.add_argument('--dry-run', action='store_true', help='Preview without committing')
    args = parser.parse_args()

    # Check if git repo
    if not is_git_repo(args.dir):
        # Silently exit if not a git repo
        sys.exit(0)

    # Generate commit message
    untracked, modified = get_git_status(args.dir)
    message = generate_commit_message(untracked, modified, args.message)

    # Commit
    success = git_commit(args.dir, message, args.dry_run)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()