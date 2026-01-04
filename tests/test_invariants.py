"""
Tests for scripts/check_invariants.py (repository structural invariants).
"""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path so we can import check_invariants
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_invariants import (
    check_no_generated_artifacts,
    check_no_parallel_implementations,
    check_no_workspace_state,
    check_package_name,
    run_all_checks,
)


@pytest.fixture
def mock_repo_root(tmp_path, monkeypatch):
    """Mock REPO_ROOT to use a temporary directory."""
    import check_invariants
    monkeypatch.setattr(check_invariants, "REPO_ROOT", tmp_path)
    return tmp_path


def test_check_package_name_passes_with_correct_name(mock_repo_root):
    """Test that package name check passes when pyproject.toml has name='kie'."""
    # Create valid pyproject.toml
    (mock_repo_root / "pyproject.toml").write_text('[project]\nname = "kie"')

    # Create kie/ directory
    (mock_repo_root / "kie").mkdir()

    violations = check_package_name()
    assert len(violations) == 0


def test_check_package_name_fails_missing_pyproject(mock_repo_root):
    """Test that package name check fails when pyproject.toml is missing."""
    violations = check_package_name()
    assert len(violations) > 0
    assert any("pyproject.toml not found" in v for v in violations)


def test_check_package_name_fails_wrong_name(mock_repo_root):
    """Test that package name check fails when package name is not 'kie'."""
    # Create pyproject.toml with wrong name
    (mock_repo_root / "pyproject.toml").write_text('[project]\nname = "kie-v3"')

    violations = check_package_name()
    assert len(violations) > 0
    assert any("package name is not 'kie'" in v for v in violations)


def test_check_package_name_fails_wrong_directory(mock_repo_root):
    """Test that package name check fails when package directory is named incorrectly."""
    # Create valid pyproject.toml but wrong directory name
    (mock_repo_root / "pyproject.toml").write_text('[project]\nname = "kie"')
    (mock_repo_root / "kie-v3").mkdir()

    violations = check_package_name()
    assert len(violations) > 0
    assert any("kie/" in v and "does not exist" in v for v in violations)
    assert any("kie-v3/" in v for v in violations)


def test_check_package_name_detects_old_imports(mock_repo_root):
    """Test that package name check detects imports from old package names."""
    # Create valid structure
    (mock_repo_root / "pyproject.toml").write_text('[project]\nname = "kie"')
    kie_dir = mock_repo_root / "kie"
    kie_dir.mkdir()

    # Create a file with old import
    (kie_dir / "test.py").write_text("from core import something")

    violations = check_package_name()
    assert len(violations) > 0
    assert any("old import" in v and "from core import" in v for v in violations)


def test_check_no_workspace_state_passes_clean_repo(mock_repo_root):
    """Test that workspace state check passes when no workspace folders exist."""
    violations = check_no_workspace_state()
    assert len(violations) == 0


def test_check_no_workspace_state_fails_with_project_state(mock_repo_root):
    """Test that workspace state check fails when project_state/ exists."""
    (mock_repo_root / "project_state").mkdir()

    violations = check_no_workspace_state()
    assert len(violations) > 0
    assert any("project_state/" in v for v in violations)


def test_check_no_workspace_state_fails_with_workspace_folders(mock_repo_root):
    """Test that workspace state check fails when workspace folders exist."""
    # Create workspace folders
    for folder in ["data", "outputs", "exports"]:
        (mock_repo_root / folder).mkdir()

    violations = check_no_workspace_state()
    assert len(violations) >= 3
    assert any("data/" in v for v in violations)
    assert any("outputs/" in v for v in violations)
    assert any("exports/" in v for v in violations)


def test_check_no_generated_artifacts_passes_clean_repo(mock_repo_root):
    """Test that generated artifacts check passes when no artifacts exist."""
    violations = check_no_generated_artifacts()
    assert len(violations) == 0


def test_check_no_generated_artifacts_detects_pycache(mock_repo_root):
    """Test that generated artifacts check detects __pycache__ directories."""
    (mock_repo_root / "__pycache__").mkdir()

    violations = check_no_generated_artifacts()
    assert len(violations) > 0
    assert any("__pycache__" in v for v in violations)


def test_check_no_generated_artifacts_detects_egg_info(mock_repo_root):
    """Test that generated artifacts check detects .egg-info directories."""
    (mock_repo_root / "kie.egg-info").mkdir()

    violations = check_no_generated_artifacts()
    assert len(violations) > 0
    assert any("kie.egg-info" in v for v in violations)


def test_check_no_generated_artifacts_detects_ds_store(mock_repo_root):
    """Test that generated artifacts check detects .DS_Store files."""
    (mock_repo_root / ".DS_Store").touch()

    violations = check_no_generated_artifacts()
    assert len(violations) > 0
    assert any(".DS_Store" in v for v in violations)


def test_check_no_generated_artifacts_detects_build_dirs(mock_repo_root):
    """Test that generated artifacts check detects build/dist directories."""
    (mock_repo_root / "build").mkdir()
    (mock_repo_root / "dist").mkdir()

    violations = check_no_generated_artifacts()
    assert len(violations) >= 2
    assert any("build/" in v for v in violations)
    assert any("dist/" in v for v in violations)


def test_check_no_parallel_implementations_passes_clean_repo(mock_repo_root):
    """Test that parallel implementations check passes when no duplicates exist."""
    # Create kie directory (but not the parallel implementations)
    (mock_repo_root / "kie").mkdir()

    violations = check_no_parallel_implementations()
    assert len(violations) == 0


def test_check_no_parallel_implementations_detects_slides(mock_repo_root):
    """Test that parallel implementations check detects kie/slides/."""
    kie_dir = mock_repo_root / "kie"
    kie_dir.mkdir()
    (kie_dir / "slides").mkdir()

    violations = check_no_parallel_implementations()
    assert len(violations) > 0
    assert any("kie/slides" in v for v in violations)


def test_check_no_parallel_implementations_detects_migrate(mock_repo_root):
    """Test that parallel implementations check detects kie/migrate/."""
    kie_dir = mock_repo_root / "kie"
    kie_dir.mkdir()
    (kie_dir / "migrate").mkdir()

    violations = check_no_parallel_implementations()
    assert len(violations) > 0
    assert any("kie/migrate" in v for v in violations)


def test_run_all_checks_passes_clean_repo(mock_repo_root):
    """Test that run_all_checks passes when all invariants are satisfied."""
    # Set up a clean repo structure
    (mock_repo_root / "pyproject.toml").write_text('[project]\nname = "kie"')
    (mock_repo_root / "kie").mkdir()

    passed, violations = run_all_checks()
    assert passed is True
    assert len(violations) == 0


def test_run_all_checks_fails_with_violations(mock_repo_root):
    """Test that run_all_checks fails when violations exist."""
    # Create violations
    (mock_repo_root / "project_state").mkdir()  # Workspace state violation
    (mock_repo_root / "__pycache__").mkdir()    # Generated artifact violation

    passed, violations = run_all_checks()
    assert passed is False
    assert len(violations) > 0


def test_run_all_checks_aggregates_all_violations(mock_repo_root):
    """Test that run_all_checks aggregates violations from all checks."""
    # Create multiple types of violations
    (mock_repo_root / "project_state").mkdir()
    (mock_repo_root / "__pycache__").mkdir()
    kie_dir = mock_repo_root / "kie"
    kie_dir.mkdir()
    (kie_dir / "slides").mkdir()

    passed, violations = run_all_checks()
    assert passed is False

    # Should have violations from multiple checks
    assert any("project_state/" in v for v in violations)
    assert any("__pycache__" in v for v in violations)
    assert any("kie/slides" in v for v in violations)
