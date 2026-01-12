"""
Tests for Freeform Export Command

Tests:
1. /freeform export blocks unless mode==freeform
2. Given freeform artifacts, export produces insights_catalog
3. Visual policy notice is created
4. Build fails with actionable message when manifest missing
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml


def test_freeform_export_blocks_without_freeform_mode():
    """Test that /freeform export blocks unless execution_mode == freeform."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        handler = CommandHandler(tmp_path)
        handler.handle_startkie()

        # Try to export without enabling freeform mode
        result = handler.handle_freeform(subcommand="export")

        assert not result["success"]
        assert "freeform mode" in result["message"].lower()


def test_freeform_export_creates_insights_catalog():
    """Test that /freeform export creates insights_catalog.json from freeform artifacts."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        handler = CommandHandler(tmp_path)
        handler.handle_startkie()

        # Set spec
        spec_path = tmp_path / "project_state" / "spec.yaml"
        spec_path.write_text(
            yaml.dump({
                "project_name": "Test",
                "objective": "Test freeform export"
            })
        )

        # Enable freeform mode
        handler.handle_freeform(subcommand="enable")

        # Create freeform artifacts
        freeform_dir = tmp_path / "outputs" / "freeform" / "tables"
        freeform_dir.mkdir(parents=True, exist_ok=True)

        sample_table = freeform_dir / "test_data.csv"
        sample_table.write_text("metric,value\nrevenue,1000\nmargin,0.25\n")

        # Run export
        result = handler.handle_freeform(subcommand="export")

        # Should create insights_catalog.json (even if pipeline fails partially)
        insights_catalog = tmp_path / "outputs" / "insights_catalog.json"
        assert insights_catalog.exists(), "insights_catalog.json not created"

        # Verify it's valid JSON with insights
        with open(insights_catalog) as f:
            catalog = json.load(f)
        assert "insights" in catalog
        assert isinstance(catalog["insights"], list)


def test_freeform_export_creates_visual_policy_notice():
    """Test that /freeform export creates NOTICE.md for visual policy."""
    from kie.commands.handler import CommandHandler

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        handler = CommandHandler(tmp_path)
        handler.handle_startkie()

        # Enable freeform mode
        handler.handle_freeform(subcommand="enable")

        # Create freeform artifacts including PNG
        freeform_dir = tmp_path / "outputs" / "freeform"
        freeform_dir.mkdir(parents=True, exist_ok=True)

        # Create fake PNG
        fake_png = freeform_dir / "chart.png"
        fake_png.write_bytes(b"fake")

        # Run export
        handler.handle_freeform(subcommand="export")

        # Verify NOTICE.md created
        notice_file = freeform_dir / "NOTICE.md"
        assert notice_file.exists(), "NOTICE.md not created"

        notice_content = notice_file.read_text()
        assert "NON-KIE" in notice_content
        assert "chart.png" in notice_content


def test_build_blocks_in_freeform_without_manifest():
    """Test that /build in freeform mode suggests /freeform export when manifest missing."""
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        handler = CommandHandler(tmp_path)
        handler.handle_startkie()

        # Set spec and intent
        spec_path = tmp_path / "project_state" / "spec.yaml"
        spec_path.write_text(
            yaml.dump({
                "project_name": "Test",
                "objective": "Test build blocking"
            })
        )

        intent_path = tmp_path / "project_state" / "intent.yaml"
        intent_path.write_text("text: Test\n")

        # Set theme
        prefs = OutputPreferences(tmp_path)
        prefs.set_theme("light")

        # Enable freeform mode
        handler.handle_freeform(subcommand="enable")

        # Try to build without manifest (should fail with actionable message)
        with pytest.raises(ValueError) as exc_info:
            handler.handle_build(target="ppt")

        error_message = str(exc_info.value)
        assert "/freeform export" in error_message
        assert "Freeform Mode" in error_message
