#!/usr/bin/env python3
"""Project initialization orchestration."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Import other scripts
sys.path.insert(0, str(Path(__file__).parent))

def run_check_deps():
    """Run dependency check."""
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "check_deps.py")],
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def discover_files(directory: Path) -> dict:
    """Discover course materials in directory."""
    files = {
        "guides": [],
        "templates": [],
        "references": []
    }
    
    for file in directory.iterdir():
        if not file.is_file():
            continue
        
        suffix = file.suffix.lower()
        
        if suffix == '.pdf':
            files["guides"].append(file.name)
        elif suffix in ['.docx', '.doc']:
            files["templates"].append(file.name)
        elif suffix == '.pptx':
            files["guides"].append(file.name)
        elif suffix in ['.md', '.txt']:
            files["references"].append(file.name)
    
    return files

def init_project(directory: Path, use_git: bool = False, experiment_name: str = None):
    """Initialize project."""
    result = {
        "success": True,
        "directory": str(directory),
        "discovered_files": {},
        "student_info": None,
        "progress_initialized": False,
        "git_initialized": False,
        "errors": []
    }
    
    # 1. Check dependencies
    deps_ok, deps_output = run_check_deps()
    if not deps_ok:
        result["errors"].append(f"Dependency check failed: {deps_output}")
        result["success"] = False
        return result
    
    # 2. Discover files
    result["discovered_files"] = discover_files(directory)
    
    if not any(result["discovered_files"].values()):
        result["errors"].append("No course materials found in directory")
        result["success"] = False
        return result
    
    # 3. Check student info
    try:
        from student_info import find_student_info
        info_path, info_data = find_student_info(directory)
        result["student_info"] = {
            "found": info_path is not None,
            "path": str(info_path) if info_path else None,
            "data": info_data
        }
    except Exception as e:
        result["errors"].append(f"Student info check failed: {e}")
    
    # 4. Create .lab-report directory
    lab_report_dir = directory / ".lab-report"
    lab_report_dir.mkdir(exist_ok=True)
    
    # 5. Initialize progress if experiment name provided
    if experiment_name:
        try:
            # Count steps from PDF if available
            total_steps = 5  # Default
            
            from progress_manager import init_progress
            import os
            os.chdir(directory)
            init_progress(experiment_name, total_steps)
            result["progress_initialized"] = True
        except Exception as e:
            result["errors"].append(f"Progress init failed: {e}")
    
    # 6. Initialize git if requested
    if use_git:
        try:
            git_dir = directory / ".git"
            if not git_dir.exists():
                subprocess.run(
                    ["git", "init"],
                    cwd=directory,
                    capture_output=True,
                    check=True
                )
                subprocess.run(
                    ["git", "add", "."],
                    cwd=directory,
                    capture_output=True
                )
                subprocess.run(
                    ["git", "commit", "-m", "Initial commit"],
                    cwd=directory,
                    capture_output=True
                )
                result["git_initialized"] = True
        except Exception as e:
            result["errors"].append(f"Git init failed: {e}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Initialize lab-report project')
    parser.add_argument('--dir', type=Path, default=Path.cwd(), help='Target directory')
    parser.add_argument('--git', action='store_true', help='Initialize git repository')
    parser.add_argument('--name', help='Experiment name')
    args = parser.parse_args()
    
    if not args.dir.exists():
        print(f"Error: Directory not found: {args.dir}", file=sys.stderr)
        sys.exit(1)
    
    result = init_project(args.dir, args.git, args.name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    sys.exit(0 if result["success"] else 1)

if __name__ == '__main__':
    main()
