"""
Tests for data-first kickoff guidance system.

Tests that doctor command provides smart next-step recommendations
based on workspace state (data presence, spec.yaml, eda_profile.json).
"""

import pytest
from pathlib import Path
from kie.commands.handler import CommandHandler
from kie.workspace import find_candidate_datasets, select_primary_dataset


def test_find_candidate_datasets_empty_dir(tmp_path):
    """Test that find_candidate_datasets returns empty list when no data/ dir."""
    # No data/ directory
    result = find_candidate_datasets(tmp_path)
    assert result == []


def test_find_candidate_datasets_no_supported_files(tmp_path):
    """Test that find_candidate_datasets ignores unsupported file types."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create unsupported files
    (data_dir / "readme.txt").write_text("Hello")
    (data_dir / "script.py").write_text("print('test')")

    result = find_candidate_datasets(tmp_path)
    assert result == []


def test_find_candidate_datasets_with_csv(tmp_path):
    """Test that find_candidate_datasets detects CSV files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    csv_file = data_dir / "sales.csv"
    csv_file.write_text("date,value\n2026-01-01,100\n")

    result = find_candidate_datasets(tmp_path)
    assert len(result) == 1
    assert result[0] == csv_file


def test_find_candidate_datasets_with_multiple_files(tmp_path):
    """Test that find_candidate_datasets finds multiple supported files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    csv_file = data_dir / "sales.csv"
    xlsx_file = data_dir / "inventory.xlsx"
    csv_file.write_text("date,value\n2026-01-01,100\n")
    xlsx_file.write_text("fake xlsx content")

    result = find_candidate_datasets(tmp_path)
    assert len(result) == 2


def test_select_primary_dataset_empty_list():
    """Test that select_primary_dataset returns None for empty list."""
    result = select_primary_dataset([])
    assert result is None


def test_select_primary_dataset_single_file(tmp_path):
    """Test that select_primary_dataset returns the only file."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    csv_file = data_dir / "sales.csv"
    csv_file.write_text("date,value\n2026-01-01,100\n")

    datasets = [csv_file]
    result = select_primary_dataset(datasets)
    assert result == csv_file


def test_select_primary_dataset_picks_most_recent(tmp_path):
    """Test that select_primary_dataset picks most recently modified file."""
    import time

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    old_file = data_dir / "old.csv"
    old_file.write_text("old")

    time.sleep(0.01)  # Ensure different mtime

    new_file = data_dir / "new.csv"
    new_file.write_text("new")

    datasets = [old_file, new_file]
    result = select_primary_dataset(datasets)
    assert result == new_file


def test_doctor_guidance_data_exists_no_spec_no_eda(tmp_path):
    """
    Test doctor suggests /eda when data exists but no spec.yaml or eda_profile.json.

    This is the core data-first kickoff scenario.
    """
    # Setup workspace
    (tmp_path / "data").mkdir()
    (tmp_path / "outputs").mkdir()
    (tmp_path / "exports").mkdir()
    (tmp_path / "project_state").mkdir()
    (tmp_path / ".claude" / "commands").mkdir(parents=True)

    # Add data file
    csv_file = tmp_path / "data" / "sales.csv"
    csv_file.write_text("date,value\n2026-01-01,100\n")

    # Run doctor
    handler = CommandHandler(project_root=tmp_path)
    result = handler.handle_doctor()

    # Should succeed
    assert result["success"] is True

    # Should have suggestions
    assert "suggestions" in result
    suggestions = result["suggestions"]
    assert len(suggestions) > 0

    # Should mention the data file
    suggestions_text = " ".join(suggestions)
    assert "sales.csv" in suggestions_text or "data/sales.csv" in suggestions_text

    # Should suggest /eda
    assert "/eda" in suggestions_text

    # Should mention exploring data first
    assert "explore" in suggestions_text.lower() or "eda" in suggestions_text.lower()


def test_doctor_guidance_data_exists_eda_exists_no_spec(tmp_path):
    """
    Test doctor suggests /analyze or /interview when data + eda_profile exist but no spec.
    """
    # Setup workspace
    (tmp_path / "data").mkdir()
    (tmp_path / "outputs").mkdir()
    (tmp_path / "exports").mkdir()
    (tmp_path / "project_state").mkdir()
    (tmp_path / ".claude" / "commands").mkdir(parents=True)

    # Add data file
    csv_file = tmp_path / "data" / "revenue.csv"
    csv_file.write_text("month,revenue\nJan,1000\n")

    # Add EDA profile (simulating /eda was run)
    eda_profile = tmp_path / "project_state" / "eda_profile.json"
    eda_profile.write_text('{"columns": ["month", "revenue"]}')

    # Run doctor
    handler = CommandHandler(project_root=tmp_path)
    result = handler.handle_doctor()

    # Should succeed
    assert result["success"] is True

    # Should have suggestions
    assert "suggestions" in result
    suggestions = result["suggestions"]
    assert len(suggestions) > 0

    # Should mention data file
    suggestions_text = " ".join(suggestions)
    assert "revenue.csv" in suggestions_text or "data/revenue.csv" in suggestions_text

    # Should mention EDA exists
    assert "EDA" in suggestions_text or "eda" in suggestions_text.lower()

    # Should suggest next steps: analyze or interview
    assert "/analyze" in suggestions_text or "/interview" in suggestions_text


def test_doctor_guidance_no_data_no_spec(tmp_path):
    """
    Test doctor suggests adding data or starting interview when workspace is empty.
    """
    # Setup minimal workspace (no data)
    (tmp_path / "data").mkdir()
    (tmp_path / "outputs").mkdir()
    (tmp_path / "exports").mkdir()
    (tmp_path / "project_state").mkdir()
    (tmp_path / ".claude" / "commands").mkdir(parents=True)

    # Run doctor
    handler = CommandHandler(project_root=tmp_path)
    result = handler.handle_doctor()

    # Should succeed
    assert result["success"] is True

    # Should have suggestions
    assert "suggestions" in result
    suggestions = result["suggestions"]
    assert len(suggestions) > 0

    # Should suggest adding data or interview
    suggestions_text = " ".join(suggestions)
    assert "data" in suggestions_text.lower() or "interview" in suggestions_text.lower()


def test_doctor_guidance_spec_exists_no_suggestions(tmp_path):
    """
    Test doctor does NOT give data-first suggestions when spec.yaml already exists.
    """
    # Setup workspace with data
    (tmp_path / "data").mkdir()
    (tmp_path / "outputs").mkdir()
    (tmp_path / "exports").mkdir()
    (tmp_path / "project_state").mkdir()
    (tmp_path / ".claude" / "commands").mkdir(parents=True)

    # Add data file
    csv_file = tmp_path / "data" / "sales.csv"
    csv_file.write_text("date,value\n2026-01-01,100\n")

    # Add spec.yaml (project is defined)
    spec_file = tmp_path / "project_state" / "spec.yaml"
    spec_file.write_text("project_name: Test Project\nproject_type: dashboard\n")

    # Run doctor
    handler = CommandHandler(project_root=tmp_path)
    result = handler.handle_doctor()

    # Should succeed
    assert result["success"] is True

    # Should have empty suggestions (or no suggestions key)
    suggestions = result.get("suggestions", [])

    # If suggestions exist, they should NOT be data-first guidance
    # (spec exists, so no need to suggest EDA/interview)
    if suggestions:
        suggestions_text = " ".join(suggestions)
        # Should NOT suggest starting with EDA (project is already defined)
        assert "Next step: Run `/eda`" not in suggestions_text


def test_doctor_guidance_multiple_datasets(tmp_path):
    """
    Test doctor handles multiple datasets gracefully.
    """
    # Setup workspace
    (tmp_path / "data").mkdir()
    (tmp_path / "outputs").mkdir()
    (tmp_path / "exports").mkdir()
    (tmp_path / "project_state").mkdir()
    (tmp_path / ".claude" / "commands").mkdir(parents=True)

    # Add multiple data files
    (tmp_path / "data" / "sales.csv").write_text("date,value\n2026-01-01,100\n")
    (tmp_path / "data" / "inventory.xlsx").write_text("fake xlsx")
    (tmp_path / "data" / "customers.csv").write_text("id,name\n1,Alice\n")

    # Run doctor
    handler = CommandHandler(project_root=tmp_path)
    result = handler.handle_doctor()

    # Should succeed
    assert result["success"] is True

    # Should have suggestions
    assert "suggestions" in result
    suggestions = result["suggestions"]
    assert len(suggestions) > 0

    # Should mention multiple datasets or suggest EDA
    suggestions_text = " ".join(suggestions)
    assert "dataset" in suggestions_text.lower() or "/eda" in suggestions_text
