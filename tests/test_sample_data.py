"""
Tests for Sample Data Management

Verifies that sample data is opt-in and doesn't compete with real data.
"""

import tempfile
from pathlib import Path

import pytest

from kie.commands.handler import CommandHandler


@pytest.fixture
def temp_project():
    """Create temporary project directory with basic structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        # Note: NOT creating folders - tests will do so as needed
        yield project_root


@pytest.fixture
def temp_project_with_structure():
    """Create temporary project directory with KIE structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir(parents=True)
        (project_root / "data").mkdir(parents=True)
        (project_root / "outputs").mkdir(parents=True)

        yield project_root


def test_startkie_no_sample_data(temp_project):
    """Test that /startkie does NOT install sample_data.csv by default."""
    handler = CommandHandler(temp_project)

    # Run startkie
    result = handler.handle_startkie()
    assert result["success"]

    # Verify sample_data.csv was NOT created
    sample_file = temp_project / "data" / "sample_data.csv"
    assert not sample_file.exists()

    # Verify data/ folder exists (with .gitkeep)
    data_dir = temp_project / "data"
    assert data_dir.exists()
    assert data_dir.is_dir()


def test_sampledata_status_not_installed(temp_project_with_structure):
    """/sampledata status shows not installed when sample data absent."""
    handler = CommandHandler(temp_project_with_structure)

    result = handler.handle_sampledata(subcommand="status")
    assert result["success"]
    assert result["installed"] is False
    # Note: message is printed, not returned


def test_sampledata_install(temp_project_with_structure):
    """Test /sampledata install creates sample_data.csv."""
    handler = CommandHandler(temp_project_with_structure)

    # Install sample data
    result = handler.handle_sampledata(subcommand="install")
    assert result["success"]
    assert "installed" in result["message"].lower()

    # Verify file exists
    sample_file = temp_project_with_structure / "data" / "sample_data.csv"
    assert sample_file.exists()

    # Verify tracking file exists
    tracking_file = temp_project_with_structure / "project_state" / "sampledata.yaml"
    assert tracking_file.exists()

    # Read tracking file
    import yaml
    with open(tracking_file) as f:
        tracking = yaml.safe_load(f)

    assert tracking["installed"] is True
    assert "installed_at" in tracking


def test_sampledata_status_installed(temp_project_with_structure):
    """/sampledata status shows installed after installation."""
    handler = CommandHandler(temp_project_with_structure)

    # Install first
    handler.handle_sampledata(subcommand="install")

    # Check status
    result = handler.handle_sampledata(subcommand="status")
    assert result["success"]
    assert result["installed"] is True
    # Note: message is printed, not returned


def test_sampledata_remove(temp_project_with_structure):
    """Test /sampledata remove deletes sample_data.csv."""
    handler = CommandHandler(temp_project_with_structure)

    # Install first
    handler.handle_sampledata(subcommand="install")
    sample_file = temp_project_with_structure / "data" / "sample_data.csv"
    assert sample_file.exists()

    # Remove
    result = handler.handle_sampledata(subcommand="remove")
    assert result["success"]
    assert "removed" in result["message"].lower()

    # Verify file deleted
    assert not sample_file.exists()

    # Verify tracking updated
    tracking_file = temp_project_with_structure / "project_state" / "sampledata.yaml"
    import yaml
    with open(tracking_file) as f:
        tracking = yaml.safe_load(f)

    assert tracking["installed"] is False


def test_sampledata_install_idempotent(temp_project_with_structure):
    """Test that /sampledata install is idempotent."""
    handler = CommandHandler(temp_project_with_structure)

    # Install twice
    result1 = handler.handle_sampledata(subcommand="install")
    result2 = handler.handle_sampledata(subcommand="install")

    assert result1["success"]
    assert result2["success"]

    # Should still have one sample file
    sample_file = temp_project_with_structure / "data" / "sample_data.csv"
    assert sample_file.exists()


def test_eda_prefers_real_data(temp_project_with_structure, monkeypatch):
    """Test that EDA prefers real data over sample_data.csv."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_project_with_structure)

    # Install sample data
    handler.handle_sampledata(subcommand="install")

    # Add real data file
    real_data = temp_project_with_structure / "data" / "real_data.csv"
    real_data.write_text(
        "region,revenue\n"
        "North,1000\n"
        "South,2000\n"
    )

    # Run EDA - should pick real_data.csv
    result = handler.handle_eda()
    assert result["success"]

    # Verify it used real_data.csv (not sample_data.csv)
    data_file = result["data_file"]
    assert "real_data.csv" in data_file
    assert "sample_data.csv" not in data_file

    # Should NOT be marked as sample data
    assert result.get("is_sample_data", False) is False


def test_eda_uses_sample_when_no_real_data(temp_project_with_structure, monkeypatch):
    """Test that EDA uses sample data when only sample_data.csv exists."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_project_with_structure)

    # Install sample data
    handler.handle_sampledata(subcommand="install")

    # Run EDA - should use sample_data.csv
    result = handler.handle_eda()
    assert result["success"]

    # Verify it used sample_data.csv
    data_file = result["data_file"]
    assert "sample_data.csv" in data_file

    # Should be marked as sample data
    assert result.get("is_sample_data", False) is True


def test_eda_fails_when_no_data(temp_project_with_structure):
    """Test that EDA fails with actionable message when data/ is empty."""
    handler = CommandHandler(temp_project_with_structure)

    # Run EDA with no data
    result = handler.handle_eda()

    # Should fail
    assert not result["success"]

    # Should have actionable message
    message = result["message"]
    assert "no data" in message.lower() or "add" in message.lower()
    assert "/sampledata" in message.lower() or "demo" in message.lower()


def test_eda_demo_label_in_review(temp_project_with_structure, monkeypatch):
    """Test that eda_review.md labels sample data as DEMO."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_project_with_structure)

    # Install sample data
    handler.handle_sampledata(subcommand="install")

    # Run EDA
    result = handler.handle_eda()
    assert result["success"]
    assert result["is_sample_data"] is True

    # Read eda_review.md
    review_file = temp_project_with_structure / "outputs" / "internal" / "eda_review.md"
    assert review_file.exists()

    review_content = review_file.read_text()

    # Should contain DEMO warning
    assert "DEMO" in review_content
    assert "sample_data.csv" in review_content


def test_eda_demo_flag_in_json(temp_project_with_structure, monkeypatch):
    """Test that eda_review.json includes is_sample_data flag."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_project_with_structure)

    # Install sample data
    handler.handle_sampledata(subcommand="install")

    # Run EDA
    result = handler.handle_eda()
    assert result["success"]

    # Read eda_review.json
    import json
    review_json = temp_project_with_structure / "outputs" / "internal" / "eda_review.json"
    assert review_json.exists()

    with open(review_json) as f:
        review_data = json.load(f)

    assert review_data["is_sample_data"] is True


def test_eda_no_demo_flag_with_real_data(temp_project_with_structure, monkeypatch):
    """Test that is_sample_data is False when using real data."""
    # Mock input to prevent stdin blocking in tests
    monkeypatch.setattr('builtins.input', lambda _: '')

    handler = CommandHandler(temp_project_with_structure)

    # Add real data (no sample data)
    real_data = temp_project_with_structure / "data" / "real_data.csv"
    real_data.write_text(
        "region,revenue\n"
        "North,1000\n"
        "South,2000\n"
    )

    # Run EDA
    result = handler.handle_eda()
    assert result["success"]

    # Should NOT be sample data
    assert result["is_sample_data"] is False

    # Check JSON
    import json
    review_json = temp_project_with_structure / "outputs" / "internal" / "eda_review.json"
    with open(review_json) as f:
        review_data = json.load(f)

    assert review_data["is_sample_data"] is False

    # Check markdown - should NOT have DEMO warning
    review_md = temp_project_with_structure / "outputs" / "internal" / "eda_review.md"
    review_content = review_md.read_text()
    assert "DEMO MODE" not in review_content
