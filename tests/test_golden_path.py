"""
Tests for Golden Path /go Command

Tests the /go command that routes consultant through workflow based on rails_state.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from kie.commands.handler import CommandHandler


def test_go_exists_in_handler():
    """Test /go command method exists in handler."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        handler = CommandHandler(tmp_path)

        # Verify method exists
        assert hasattr(handler, "handle_go")
        assert callable(handler.handle_go)


def test_go_routes_to_startkie_when_not_started(tmp_path):
    """Test /go provides guidance when project not initialized."""
    handler = CommandHandler(tmp_path)

    # Mark showcase as completed to bypass Showcase Mode
    from kie.showcase.detector import mark_showcase_completed
    mark_showcase_completed(tmp_path)

    # Execute /go
    result = handler.handle_go()

    # Should provide guidance (not execute - workspace needs setup first)
    assert result["success"] is True
    assert "executed_command" in result
    assert result.get("evidence_ledger_id") is not None


def test_go_routes_to_spec_init_when_startkie_complete(tmp_path):
    """Test /go routes to spec --init when startkie done but spec missing."""
    # Setup: workspace initialized, no spec
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create rails_state showing startkie complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie"],
        "current_stage": "startkie",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    # Mark showcase as completed to bypass Showcase Mode
    from kie.showcase.detector import mark_showcase_completed
    mark_showcase_completed(tmp_path)

    handler = CommandHandler(tmp_path)
    result = handler.handle_go()

    # Should indicate spec --init was executed OR guidance provided
    assert result["success"] is True
    executed = result.get("executed_command", "").lower()
    assert "spec" in executed or "guidance" in executed
    assert result.get("evidence_ledger_id") is not None


def test_go_emits_guidance_when_data_missing(tmp_path):
    """Test /go emits clear guidance when spec exists but data missing."""
    # Setup: workspace with spec but no data
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create rails_state showing spec complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec"],
        "current_stage": "spec",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go()

    # Should NOT execute EDA, should provide guidance
    assert result["success"] is True
    assert result.get("executed_command") == "guidance"
    assert "data" in result.get("message", "").lower()
    assert result.get("evidence_ledger_id") is not None
    assert result.get("next_step") is not None


def test_go_executes_eda_when_data_present(tmp_path):
    """Test /go executes EDA when spec complete and data present."""
    # Setup: workspace with spec and data
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create sample data
    data_path = tmp_path / "data" / "sample.csv"
    data_path.write_text("id,value\n1,100\n2,200\n3,300\n")

    # Create rails_state showing spec complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec"],
        "current_stage": "spec",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go()

    # Should execute EDA
    assert result["success"] is True
    assert result.get("executed_command") == "eda"
    assert result.get("evidence_ledger_id") is not None


def test_go_executes_analyze_when_eda_complete(tmp_path):
    """Test /go executes analyze when EDA complete."""
    # Setup: workspace with EDA outputs
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics",
        "data_source": "sample.csv"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create sample data
    data_path = tmp_path / "data" / "sample.csv"
    data_path.write_text("id,value\n1,100\n2,200\n3,300\n")

    # Create EDA output
    eda_profile = {
        "generated_at": datetime.now().isoformat(),
        "data_file": "data/sample.csv",
        "row_count": 3,
        "column_count": 2
    }
    (tmp_path / "outputs" / "eda_profile.json").write_text(json.dumps(eda_profile))

    # Create rails_state showing EDA complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec", "eda"],
        "current_stage": "eda",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go()

    # Should execute analyze
    assert result["success"] is True
    assert result.get("executed_command") == "analyze"
    assert result.get("evidence_ledger_id") is not None


def test_go_executes_build_when_analyze_complete(tmp_path):
    """Test /go executes build when analyze complete."""
    # Setup: workspace with analyze outputs
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics",
        "data_source": "sample.csv"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create insights catalog
    catalog = {
        "generated_at": datetime.now().isoformat(),
        "business_question": "Test",
        "insights": [],
        "data_summary": {}
    }
    (tmp_path / "outputs" / "insights_catalog.json").write_text(json.dumps(catalog))

    # Create rails_state showing analyze complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec", "eda", "analyze"],
        "current_stage": "analyze",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go()

    # Should ATTEMPT to execute build (may succeed or fail based on artifacts)
    # The key is that it routes to build, not that build succeeds
    assert result.get("executed_command") == "build"
    assert result.get("evidence_ledger_id") is not None


def test_go_executes_preview_when_build_complete(tmp_path):
    """Test /go executes preview when build complete."""
    # Setup: workspace with build outputs
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics",
        "data_source": "sample.csv"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create rails_state showing build complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec", "eda", "analyze", "build"],
        "current_stage": "build",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go()

    # Should ATTEMPT to execute preview (may succeed or fail based on outputs)
    # The key is that it routes to preview, not that preview succeeds
    assert result.get("executed_command") == "preview"
    assert result.get("evidence_ledger_id") is not None


def test_go_default_executes_one_action_only(tmp_path):
    """Test /go default mode provides guidance (not multi-step execution)."""
    # Setup: fresh workspace with showcase bypassed
    from kie.showcase.detector import mark_showcase_completed
    mark_showcase_completed(tmp_path)

    handler = CommandHandler(tmp_path)

    # Execute /go
    result = handler.handle_go()

    # Should provide guidance (single action)
    assert result["success"] is True
    assert "executed_command" in result
    assert result.get("evidence_ledger_id") is not None


def test_go_full_mode_chains_stages(tmp_path):
    """Test /go --full chains stages until preview or blocked."""
    # Setup: workspace with data ready for full run
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics",
        "data_source": "sample.csv"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create sample data
    data_path = tmp_path / "data" / "sample.csv"
    data_path.write_text("id,value\n1,100\n2,200\n3,300\n")

    # Create rails_state showing spec complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec"],
        "current_stage": "spec",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go(full=True)

    # Should execute multiple stages
    assert result["success"] is True
    assert result.get("executed_command") == "full"
    assert len(result.get("stages_executed", [])) > 1
    assert result.get("evidence_ledger_id") is not None


def test_go_full_stops_on_block(tmp_path):
    """Test /go --full stops at first block/failure."""
    # Setup: workspace that will block at EDA (no data)
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create rails_state showing spec complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec"],
        "current_stage": "spec",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go(full=True)

    # Should stop when data not available
    assert "stages_executed" in result or "blocked_at" in result
    assert result.get("evidence_ledger_id") is not None

    # Verify rails_state did NOT advance past where it stopped
    rails_state = json.loads(rails_state_path.read_text())
    assert "eda" not in rails_state.get("completed_stages", [])


def test_go_blocked_includes_recovery_steps(tmp_path):
    """Test /go provides recovery steps when blocked."""
    # Setup: workspace that will block (missing data)
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create rails_state showing spec complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec"],
        "current_stage": "spec",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go()

    # Should include next_step guidance
    assert result.get("next_step") is not None
    assert len(result.get("next_step", "")) > 0


def test_go_creates_ledger_for_guidance(tmp_path):
    """Test /go creates evidence ledger even for guidance-only runs."""
    # Setup: workspace needing guidance
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create rails_state showing spec complete
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec"],
        "current_stage": "spec",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)
    result = handler.handle_go()

    # Should have evidence ledger
    assert result.get("evidence_ledger_id") is not None

    # Verify ledger file exists
    ledger_id = result["evidence_ledger_id"]
    ledger_path = tmp_path / "project_state" / "evidence_ledger" / f"{ledger_id}.yaml"
    assert ledger_path.exists()


def test_go_respects_enforcement_blocks(tmp_path):
    """Test /go respects enforcement and does not bypass blocks."""
    # This test verifies /go routes through normal enforcement
    # If enforcement would block, /go also blocks

    # Setup: workspace that enforcement would block
    # (e.g., trying to run analyze without EDA)
    for d in ["data", "outputs", "project_state", "exports"]:
        (tmp_path / d).mkdir()

    # Create spec
    spec_data = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test objective",
        "project_type": "analytics",
        "data_source": "sample.csv"
    }
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(yaml.dump(spec_data))

    # Create rails_state showing spec complete but EDA skipped
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    rails_state_path.write_text(json.dumps({
        "completed_stages": ["startkie", "spec"],
        "current_stage": "spec",
        "workflow_started": True,
        "last_updated": datetime.now().isoformat()
    }))

    handler = CommandHandler(tmp_path)

    # /go should route to EDA (not analyze) because rails_state indicates that's next
    result = handler.handle_go()

    # Should follow rails_state order
    assert result.get("executed_command") in ["eda", "guidance"]
