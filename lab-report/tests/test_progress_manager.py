"""Tests for progress_manager.py."""
import json
from pathlib import Path

import pytest

# progress_manager is at root-level scripts, conftest adds it to sys.path
import progress_manager


@pytest.fixture(autouse=True)
def isolate_progress(tmp_path, monkeypatch):
    """Isolate progress.json to a temp directory."""
    working_dir = str(tmp_path / ".labmate")
    monkeypatch.setattr(progress_manager, "_get_working_dir", lambda base_path=Path.cwd(): working_dir)
    progress_file = Path(working_dir) / "progress.json"
    yield tmp_path
    # Cleanup
    if progress_file.exists():
        progress_file.unlink(missing_ok=True)


class TestInitProgress:
    def test_init_progress(self):
        data = progress_manager.init_progress("test-exp", 5)
        assert data["experiment_name"] == "test-exp"
        assert data["total_steps"] == 5
        assert data["current_step"] == 0
        assert data["completed_steps"] == []
        assert data["status"] == "not_started"
        assert "last_updated" in data

        # Verify file was created
        path = progress_manager.get_progress_path()
        assert path.exists(), "progress.json should be created"
        saved = json.loads(path.read_text(encoding="utf-8"))
        assert saved["experiment_name"] == "test-exp"


class TestUpdateStep:
    def test_update_step(self):
        progress_manager.init_progress("test-update", 5)
        data = progress_manager.update_step(1, "completed")
        assert 1 in data["completed_steps"], "step 1 should be in completed_steps"

        data = progress_manager.update_step(2, "completed")
        assert 2 in data["completed_steps"]


class TestReset:
    def test_reset(self):
        progress_manager.init_progress("test-reset", 5)
        progress_manager.update_step(1, "completed")
        progress_manager.update_step(2, "completed")

        data = progress_manager.reset_progress("new-exp", 10)
        assert data["current_step"] == 0
        assert data["completed_steps"] == []
        assert data["status"] == "not_started"
        assert data["experiment_name"] == "new-exp"
        assert data["total_steps"] == 10
