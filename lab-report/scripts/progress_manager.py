#!/usr/bin/env python3
"""JSON progress state manager."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from schemas import ProgressState
    HAS_SCHEMAS = True
except ImportError:
    HAS_SCHEMAS = False
    ProgressState = None

def _get_working_dir(base_path: Path = Path.cwd()) -> str:
    """Determine working directory, checking config first then falling back.
    
    Priority:
    1. Read working_dir from .labmate/config.json if it exists
    2. Return ".labmate" if .labmate/ directory exists
    3. Return ".lab-report" if .lab-report/ directory exists
    4. Default: ".labmate"
    """
    labmate_config = base_path / ".labmate" / "config.json"
    if labmate_config.exists():
        try:
            config = json.loads(labmate_config.read_text(encoding='utf-8'))
            if "working_dir" in config:
                return config["working_dir"]
        except (json.JSONDecodeError, IOError):
            pass
    
    if (base_path / ".labmate").exists():
        return ".labmate"
    if (base_path / ".lab-report").exists():
        return ".lab-report"
    return ".labmate"

def get_progress_path() -> Path:
    """Get the path to progress.json."""
    working_dir = _get_working_dir()
    return Path(working_dir) / "progress.json"

def load_progress() -> dict:
    """Load progress from file or return default."""
    path = get_progress_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError):
            pass

    # Default state
    return {
        "experiment_name": "",
        "total_steps": 0,
        "current_step": 0,
        "completed_steps": [],
        "screenshots_required": [],
        "notes": {},
        "debug_history": [],
        "last_updated": datetime.now().isoformat(),
        "status": "not_started"
    }

def save_progress(data: dict):
    """Save progress to file."""
    path = get_progress_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def init_progress(experiment_name: str, total_steps: int):
    """Initialize new progress."""
    data = load_progress()
    data["experiment_name"] = experiment_name
    data["total_steps"] = total_steps
    data["current_step"] = 0
    data["completed_steps"] = []
    data["screenshots_required"] = []
    data["notes"] = {}
    data["status"] = "not_started"
    save_progress(data)
    return data

def update_step(step: int, status: str):
    """Update step status."""
    data = load_progress()

    if status == "completed":
        if step not in data["completed_steps"]:
            data["completed_steps"].append(step)
        data["current_step"] = max(data["current_step"], step)
    elif status == "in_progress":
        data["current_step"] = step
        data["status"] = "in_progress"
    elif status == "skipped":
        if step not in data["completed_steps"]:
            data["completed_steps"].append(step)

    # Check if all steps completed
    if len(data["completed_steps"]) >= data["total_steps"]:
        data["status"] = "completed"

    save_progress(data)
    return data

def add_screenshot(step: int, description: str = "", path: str = None):
    """Add screenshot requirement."""
    data = load_progress()

    screenshot = {
        "step": step,
        "description": description,
        "captured": path is not None,
        "path": path
    }

    # Update existing or add new
    existing = [s for s in data["screenshots_required"] if s["step"] == step]
    if existing:
        existing[0].update(screenshot)
    else:
        data["screenshots_required"].append(screenshot)

    save_progress(data)
    return data

def add_note(step: int, note: str):
    """Add note for a step."""
    data = load_progress()
    key = f"step_{step}"
    data["notes"][key] = note
    save_progress(data)
    return data

def add_debug_history(step: int, error: str, attempt: int, approach: str = ""):
    """Record a debug failure in history."""
    data = load_progress()
    data.setdefault("debug_history", [])
    data["debug_history"].append({
        "step": step,
        "attempt": attempt,
        "timestamp": datetime.now().isoformat(),
        "error": error,
        "approach": approach,
    })
    save_progress(data)
    return data

def reset_progress(experiment_name: str = None, total_steps: int = None):
    """Reset progress to initial state."""
    data = load_progress()
    data["current_step"] = 0
    data["completed_steps"] = []
    data["screenshots_required"] = []
    data["notes"] = {}
    data["status"] = "not_started"

    if experiment_name:
        data["experiment_name"] = experiment_name
    if total_steps:
        data["total_steps"] = total_steps

    save_progress(data)
    return data

def main():
    parser = argparse.ArgumentParser(description='Progress state manager')
    parser.add_argument('--init', action='store_true', help='Initialize progress')
    parser.add_argument('--experiment', help='Experiment name')
    parser.add_argument('--total-steps', type=int, help='Total number of steps')
    parser.add_argument('--step', type=int, help='Step number')
    parser.add_argument('--status', choices=['completed', 'in_progress', 'skipped'], help='Step status')
    parser.add_argument('--screenshot', action='store_true', help='Add screenshot record')
    parser.add_argument('--description', help='Screenshot description')
    parser.add_argument('--path', help='Screenshot path')
    parser.add_argument('--note', help='Add note for step')
    parser.add_argument('--debug', action='store_true', help='Record debug failure')
    parser.add_argument('--error', help='Debug error message')
    parser.add_argument('--attempt', type=int, default=1, help='Debug attempt number')
    parser.add_argument('--approach', default='', help='Debug approach description')
    parser.add_argument('--reset', action='store_true', help='Reset progress')

    args = parser.parse_args()

    if args.init:
        if not args.experiment or not args.total_steps:
            print("Error: --init requires --experiment and --total-steps", file=sys.stderr)
            sys.exit(1)
        data = init_progress(args.experiment, args.total_steps)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.step and args.status:
        data = update_step(args.step, args.status)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.screenshot:
        if not args.step:
            print("Error: --screenshot requires --step", file=sys.stderr)
            sys.exit(1)
        data = add_screenshot(args.step, args.description or "", args.path)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.note:
        if not args.step:
            print("Error: --note requires --step", file=sys.stderr)
            sys.exit(1)
        data = add_note(args.step, args.note)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.debug:
        if not args.step or not args.error:
            print("Error: --debug requires --step and --error", file=sys.stderr)
            sys.exit(1)
        data = add_debug_history(args.step, args.error, args.attempt, args.approach)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.reset:
        data = reset_progress(args.experiment, args.total_steps)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    else:
        # Just show current progress
        data = load_progress()
        print(json.dumps(data, indent=2, ensure_ascii=False))

    sys.exit(0)

if __name__ == '__main__':
    main()