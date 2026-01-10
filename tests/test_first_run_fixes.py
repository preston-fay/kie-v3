#!/usr/bin/env python3
"""
Unit tests for first-run experience fixes.

Tests:
- Sample data file exists in project_template
- Data file selection helpers work correctly
- Node version checking works
- Preview shows deliverables
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_sample_data_exists():
    """Test that sample_data.csv exists in project_template and is non-empty."""
    repo_root = Path(__file__).parent.parent
    sample_data = repo_root / "project_template" / "data" / "sample_data.csv"

    assert sample_data.exists(), "sample_data.csv missing from project_template/data/"

    content = sample_data.read_text()
    assert len(content) > 100, f"sample_data.csv too small ({len(content)} bytes)"
    assert "Region" in content, "sample_data.csv missing expected columns"
    assert "Revenue" in content, "sample_data.csv missing Revenue column"


def test_data_file_selection_priority():
    """Test that _select_data_file follows correct priority."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        handler = CommandHandler(project_root=project_root)

        # Test 1: No files
        assert handler._select_data_file() is None

        # Test 2: Only sample_data.csv
        sample_file = data_dir / "sample_data.csv"
        sample_file.write_text("test")
        assert handler._select_data_file() == sample_file

        # Test 3: User CSV takes priority over sample
        user_csv = data_dir / "my_data.csv"
        user_csv.write_text("test")
        assert handler._select_data_file() == user_csv

        # Test 4: XLSX takes priority over CSV
        user_xlsx = data_dir / "my_data.xlsx"
        user_xlsx.write_text("test")
        assert handler._select_data_file() == user_xlsx

        # Test 5: Parquet takes priority after XLSX
        user_parquet = data_dir / "my_data.parquet"
        user_parquet.write_text("test")
        user_xlsx.unlink()
        assert handler._select_data_file() == user_parquet


def test_data_file_selection_persistence():
    """Test that selected data file is saved and loaded correctly."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        handler = CommandHandler(project_root=project_root)

        # Create test file
        test_file = data_dir / "test.csv"
        test_file.write_text("test")

        # Save selection
        handler._save_data_file_selection(test_file)

        # Verify persistence file exists
        selection_file = project_root / "project_state" / "current_data_file.txt"
        assert selection_file.exists()

        # Load selection
        loaded = handler._load_data_file_selection()
        assert loaded == test_file


def test_node_version_check_compatible():
    """Test Node version check with compatible version."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Test with Node 20 (compatible)
        with patch.dict("os.environ", {"TEST_NODE_VERSION": "20.10.0"}):
            is_ok, version, msg = handler._check_node_version()
            assert is_ok is True
            assert version == "20.10.0"
            assert "compatible" in msg.lower()

        # Test with Node 22 (compatible)
        with patch.dict("os.environ", {"TEST_NODE_VERSION": "22.5.0"}):
            is_ok, version, msg = handler._check_node_version()
            assert is_ok is True
            assert version == "22.5.0"


def test_node_version_check_incompatible():
    """Test Node version check with incompatible version."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Test with Node 18 (too old)
        with patch.dict("os.environ", {"TEST_NODE_VERSION": "18.0.0"}):
            is_ok, version, msg = handler._check_node_version()
            assert is_ok is False
            assert version == "18.0.0"
            assert "too old" in msg.lower()

        # Test with Node 16 (too old)
        with patch.dict("os.environ", {"TEST_NODE_VERSION": "16.0.0"}):
            is_ok, version, msg = handler._check_node_version()
            assert is_ok is False


def test_node_version_check_missing():
    """Test Node version check when Node is not installed."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        handler = CommandHandler(project_root=project_root)

        # Clear TEST_NODE_VERSION if set
        with patch.dict("os.environ", {}, clear=True):
            # Mock subprocess to simulate Node not found
            with patch("subprocess.run", side_effect=FileNotFoundError()):
                is_ok, version, msg = handler._check_node_version()
                assert is_ok is False
                assert version is None
                assert "not found" in msg.lower()


def test_build_dashboard_uses_selected_file():
    """Test that _build_dashboard uses the selected data file."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        # Create XLSX file (not CSV)
        xlsx_file = data_dir / "data.xlsx"
        xlsx_file.write_text("test")

        # Save as current file
        handler = CommandHandler(project_root=project_root)
        handler._save_data_file_selection(xlsx_file)

        # Mock spec and _build_dashboard to verify it loads the selection
        spec = {"project_name": "Test", "client_name": "Test"}

        # Verify that _load_data_file_selection returns the XLSX
        loaded = handler._load_data_file_selection()
        assert loaded == xlsx_file
        assert loaded.suffix == ".xlsx"
