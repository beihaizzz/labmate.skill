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
        elif suffix in ['.md', '.txt', '.cs', '.py', '.cpp', '.h']:
            files["references"].append(file.name)
    
    # Scan subdirectories for reference code folders
    for sub in directory.iterdir():
        if not sub.is_dir():
            continue
        name_lower = sub.name.lower()
        if any(kw in name_lower for kw in ['供参考', '参考', 'reference', 'script', 'scripts', '资源']):
            count = len(list(sub.rglob('*')))
            if count > 0:
                files.setdefault("reference_dirs", [])
                files["reference_dirs"].append({"name": sub.name, "file_count": count})
    
    return files


TEMPLATE_FINGERPRINTS = [
    "课程名称", "学生姓名", "学号", "专业年级", "任课教师",
    "实验名称", "实验类型", "实验学时", "实验日期", "实验地点",
    "实验目的", "实验原理", "实验内容", "实验要求",
]


def _extract_text_from_doc(filepath: Path) -> str:
    """从 .doc (OLE2) 提取纯文本。（无 LibreOffice 降级方案）"""
    try:
        import olefile
        ole = olefile.OleFileIO(str(filepath))
        # 尝试读取 WordDocument 流
        if ole.exists('WordDocument'):
            stream = ole.openstream('WordDocument')
            raw = stream.read()
            # 过滤可读字符
            text = ''.join(chr(b) for b in raw if 0x20 <= b < 0x7f or 0x80 <= b <= 0xff)
            # 清理乱码序列
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
            return text
        ole.close()
    except ImportError:
        pass
    except Exception:
        pass
    return ""


def _detect_embedded_template(filepath: Path) -> dict | None:
    """检测 .doc 文件中是否嵌有报告模板。"""
    suffix = filepath.suffix.lower()
    
    if suffix == '.docx':
        try:
            from docx import Document
            doc = Document(filepath)
            text = " ".join([p.text for p in doc.paragraphs])
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += " " + cell.text
        except Exception:
            return None
    elif suffix == '.doc':
        text = _extract_text_from_doc(filepath)
    else:
        return None
    
    if not text:
        return None
    
    found = [fp for fp in TEMPLATE_FINGERPRINTS if fp in text]
    if len(found) >= 4:
        return {"source": filepath.name, "cells_detected": found,
                "type": "embedded_in_guide", "status": "detected"}
    return None


def _save_config(directory: Path, data: dict):
    """保存配置到 .lab-report/config.json"""
    config_dir = directory / ".lab-report"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    existing = {}
    if config_file.exists():
        try:
            existing = json.loads(config_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError):
            pass
    existing.update(data)
    config_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding='utf-8')

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
    
    # 2.5 检测 .doc 嵌入模板
    result["embedded_templates"] = []
    for file in directory.iterdir():
        if not file.is_file():
            continue
        detected = _detect_embedded_template(file)
        if detected:
            result["embedded_templates"].append(detected)
            result["discovered_files"].setdefault("templates_embedded", [])
            result["discovered_files"]["templates_embedded"].append(file.name)
    
    if result["embedded_templates"]:
        _save_config(directory, {"embedded_templates": result["embedded_templates"]})
    
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
