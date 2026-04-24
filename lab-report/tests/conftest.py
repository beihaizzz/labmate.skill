"""Pytest configuration and fixtures for lab-report tests."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add the lab-report package to the path for imports
LAB_REPORT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(LAB_REPORT_ROOT))

# Also add root-level scripts (E:\lab-report\scripts\) for imports like
# progress_manager, student_info, git_manager, parse_pptx
ROOT_SCRIPTS = LAB_REPORT_ROOT.parent / "scripts"
if ROOT_SCRIPTS.exists():
    sys.path.insert(0, str(ROOT_SCRIPTS))

# Project root (E:\lab-report\)
PROJECT_ROOT = LAB_REPORT_ROOT.parent


@pytest.fixture
def project_root():
    """Return the lab-report package root directory."""
    return LAB_REPORT_ROOT


@pytest.fixture
def test_data_dir():
    """Return the test fixtures directory."""
    return LAB_REPORT_ROOT / "tests" / "fixtures"


@pytest.fixture
def references_dir():
    """Return the references directory."""
    return LAB_REPORT_ROOT / "references"


@pytest.fixture
def fixtures_dir():
    """Return the test fixtures directory (alias)."""
    return LAB_REPORT_ROOT / "tests" / "fixtures"


@pytest.fixture
def template_path():
    """Return path to the report_template.docx."""
    p = LAB_REPORT_ROOT / "assets" / "report_template.docx"
    if not p.exists():
        pytest.skip("report_template.docx not found")
    return p


@pytest.fixture
def sample_pdf():
    """Return path to sample_guide.pdf fixture."""
    return LAB_REPORT_ROOT / "tests" / "fixtures" / "sample_guide.pdf"


@pytest.fixture
def sample_scanned_pdf():
    """Return path to sample_guide_scanned.pdf fixture."""
    return LAB_REPORT_ROOT / "tests" / "fixtures" / "sample_guide_scanned.pdf"


@pytest.fixture
def sample_pptx():
    """Return path to sample_guide.pptx fixture."""
    return LAB_REPORT_ROOT / "tests" / "fixtures" / "sample_guide.pptx"


@pytest.fixture
def temp_dir():
    """Create a temporary directory, cleaned up after test."""
    d = tempfile.mkdtemp(prefix="labreport_test_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def temp_cwd(temp_dir):
    """Change to temp directory during test, restore after."""
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(old_cwd)


@pytest.fixture
def student_info_file(tmp_path):
    """Create a temporary 学生信息.md with test data."""
    content = """# 学生信息

姓名: 张三
学号: 20240001
学院: 物理学院
专业: 物理学
班级: 物理2101
"""
    filepath = tmp_path / "学生信息.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath
