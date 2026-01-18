"""
KIE v3 Integration Tests

End-to-end tests for the complete v3 system.
"""

import pytest
from pathlib import Path
import pandas as pd
import tempfile
import shutil

from kie.interview import InterviewEngine, ProjectType, DeliverableType
from kie.validation import ValidationPipeline, ValidationConfig, ValidationError
from kie.workflow import WorkflowOrchestrator, WorkflowStage
from kie.state import StateManager, StateType
from kie.commands import CommandHandler
from kie.charts import ChartFactory
from kie.tables import TableFactory


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Create folders
    (project_path / "data").mkdir()
    (project_path / "outputs").mkdir()
    (project_path / "outputs" / "charts").mkdir()
    (project_path / "outputs" / "tables").mkdir()
    (project_path / "exports").mkdir()
    (project_path / "project_state").mkdir()

    yield project_path

    # Cleanup
    shutil.rmtree(temp_dir)


def test_interview_to_spec(temp_project):
    """Test interview system generates valid spec."""
    interview = InterviewEngine(
        state_path=temp_project / "project_state" / "interview_state.yaml"
    )

    # Simulate conversation
    messages = [
        "I need a sales dashboard for Acme Corp showing Q3 performance",
        "I have a CSV file with sales data",
        "I prefer dark theme",
    ]

    for message in messages:
        response = interview.process_message(message)

    # Check interview completed
    assert interview.state.has_project_type
    assert interview.state.has_data_source
    assert interview.state.spec.client_name == "Acme Corp"
    assert interview.state.spec.project_type == ProjectType.DASHBOARD

    # Export spec
    spec_path = interview.export_spec_yaml(temp_project / "project_state" / "spec.yaml")
    assert spec_path.exists()


def test_validation_blocks_synthetic_data(temp_project):
    """Test validation blocks synthetic/fake data."""
    pipeline = ValidationPipeline(
        ValidationConfig(
            strict=True,
            save_reports=True,
            report_dir=temp_project / "project_state" / "validation_reports",
        )
    )

    # Create synthetic data (should fail)
    synthetic_data = pd.DataFrame(
        {
            "customer": ["Test Corp", "Sample Inc", "Lorem Ipsum"],
            "revenue": [1000000, 2000000, 3000000],  # All round
            "id": [1, 2, 3],  # Sequential
        }
    )

    chart_config = {"type": "bar", "colors": ["#7823DC"]}

    # Should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        pipeline.validate_chart(
            data=synthetic_data,
            chart_config=chart_config,
            output_path=temp_project / "outputs" / "charts" / "test.json",
        )

    # Check error contains synthetic data message
    assert "synthetic" in str(exc_info.value).lower()


def test_validation_blocks_brand_violations(temp_project):
    """Test validation blocks brand violations."""
    pipeline = ValidationPipeline(ValidationConfig(strict=True, save_reports=False))

    # Good data but bad colors
    data = pd.DataFrame(
        {
            "category": ["A", "B", "C"],
            "value": [100, 200, 150],
        }
    )

    # Forbidden green colors
    bad_config = {
        "type": "bar",
        "colors": ["#00FF00", "#008000"],  # Greens!
        "grid": {"show": True},  # Gridlines!
    }

    with pytest.raises(ValidationError) as exc_info:
        pipeline.validate_chart(
            data=data,
            chart_config=bad_config,
            output_path=temp_project / "outputs" / "test.json",
        )

    error_msg = str(exc_info.value).lower()
    # Should catch either forbidden colors OR gridlines (both are brand violations)
    assert "green" in error_msg or "color" in error_msg or "gridline" in error_msg


def test_validation_passes_good_data(temp_project):
    """Test validation passes clean, compliant data."""
    pipeline = ValidationPipeline(ValidationConfig(strict=True, save_reports=False))

    # Good data
    data = pd.DataFrame(
        {
            "region": ["North", "South", "East", "West"],
            "revenue": [1250000, 980000, 1450000, 1100000],
        }
    )

    # Compliant config
    good_config = {
        "type": "bar",
        "colors": ["#7823DC", "#9B4DCA"],  # KDS purple
        "grid": {"show": False},  # No gridlines
    }

    # Should pass
    report = pipeline.validate_chart(
        data=data,
        chart_config=good_config,
        output_path=temp_project / "outputs" / "test.json",
    )

    assert report.overall_passed
    assert report.critical_count == 0


def test_workflow_stage_progression(temp_project):
    """Test workflow progresses through stages."""
    orchestrator = WorkflowOrchestrator(project_root=temp_project)

    # Should start at NOT_STARTED
    assert orchestrator.get_current_stage() == WorkflowStage.NOT_STARTED

    # Advance to requirements
    orchestrator.advance_to_stage(WorkflowStage.REQUIREMENTS)
    assert orchestrator.get_current_stage() == WorkflowStage.REQUIREMENTS

    # Advance to data loading
    orchestrator.advance_to_stage(WorkflowStage.DATA_LOADING)
    assert orchestrator.get_current_stage() == WorkflowStage.DATA_LOADING

    # Check state saved
    assert orchestrator.state_path.exists()

    # Reload and verify
    orchestrator2 = WorkflowOrchestrator(project_root=temp_project)
    assert orchestrator2.get_current_stage() == WorkflowStage.DATA_LOADING


def test_state_manager_persistence(temp_project):
    """Test state manager persists and loads state."""
    manager = StateManager(project_root=temp_project)

    # Save project state
    project_data = {
        "project_name": "Test Project",
        "project_type": "analytics",
        "objective": "Test objective",
    }

    manager.save_state(StateType.PROJECT, project_data)

    # Load it back
    loaded = manager.get_project_state()
    assert loaded["project_name"] == "Test Project"
    assert loaded["project_type"] == "analytics"

    # Check snapshot created
    history = manager.get_history(StateType.PROJECT)
    assert len(history) > 0


def test_state_manager_summary(temp_project):
    """Test state manager generates correct summary."""
    manager = StateManager(project_root=temp_project)

    # Initially should be empty
    summary = manager.get_state_summary()
    assert not summary["project_initialized"]

    # Add project state
    manager.save_state(
        StateType.PROJECT,
        {"project_name": "Test", "project_type": "analytics", "objective": "test"},
    )

    summary = manager.get_state_summary()
    assert summary["project_initialized"]


def test_command_handler_startkie():
    """Test /startkie command creates project structure."""
    # Use empty temp directory - startkie requires empty folder
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_project = Path(tmpdir)
        handler = CommandHandler(project_root=temp_project)

        result = handler.handle_startkie()

        assert result["success"], f"startkie failed: {result.get('message')}"
        assert (temp_project / "CLAUDE.md").exists()
        assert (temp_project / "README.md").exists()
        assert (temp_project / ".gitignore").exists()
        assert (temp_project / "data").exists()
        assert (temp_project / "outputs").exists()


def test_command_handler_status(temp_project):
    """Test /status command returns project status."""
    handler = CommandHandler(project_root=temp_project)

    # Create some state
    spec = {
        "project_name": "Test Project",
        "project_type": "analytics",
        "objective": "Test",
        "data_sources": [{"type": "csv"}],
        "deliverables": ["powerpoint"],
    }

    spec_path = temp_project / "project_state" / "spec.yaml"
    import yaml

    with open(spec_path, "w") as f:
        yaml.dump(spec, f)

    # Get status
    status = handler.handle_status()

    assert status["has_spec"]
    assert status["spec"]["project_name"] == "Test Project"


def test_chart_and_table_integration(temp_project):
    """Test chart and table creation with validation."""
    # Create sample data
    data = [
        {"region": "North", "revenue": 1250000, "growth": 0.15},
        {"region": "South", "revenue": 980000, "growth": 0.12},
        {"region": "East", "revenue": 1450000, "growth": 0.18},
    ]

    # Create chart
    chart_config = ChartFactory.bar(
        data=data,
        x="region",
        y=["revenue"],
        title="Revenue by Region",
    )

    # Save chart config
    chart_path = temp_project / "outputs" / "charts" / "revenue.json"
    chart_path.parent.mkdir(parents=True, exist_ok=True)

    with open(chart_path, "w") as f:
        import json

        json.dump(chart_config.to_dict(), f)

    assert chart_path.exists()

    # Create table
    table_config = TableFactory.standard(data, title="Regional Performance")

    # Save table config
    table_path = temp_project / "outputs" / "tables" / "performance.json"

    with open(table_path, "w") as f:
        json.dump(table_config.model_dump(), f)

    assert table_path.exists()

    # Validate both
    pipeline = ValidationPipeline(ValidationConfig(strict=True, save_reports=False))

    df = pd.DataFrame(data)

    # Chart should pass
    report = pipeline.validate_chart(
        data=df,
        chart_config=chart_config.to_dict(),
        output_path=chart_path,
    )

    assert report.overall_passed

    # Table should pass
    report = pipeline.validate_table(
        data=df,
        table_config=table_config.model_dump(),
        output_path=table_path,
    )

    assert report.overall_passed


def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    import json

    # Use empty temp directory - startkie requires empty folder
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_project = Path(tmpdir)

        # 1. Bootstrap project
        handler = CommandHandler(project_root=temp_project)
        result = handler.handle_startkie()
        assert result["success"], f"startkie failed: {result.get('message')}"

        # 2. Interview
        interview = InterviewEngine(
            state_path=temp_project / "project_state" / "interview_state.yaml"
        )

        interview.process_message("I need an analysis dashboard for Tech Corp showing quarterly revenue")
        interview.process_message("I have CSV data")

        assert interview.state.has_project_type
        assert interview.state.has_data_source

        # Export spec
        spec_path = interview.export_spec_yaml(temp_project / "project_state" / "spec.yaml")
        assert spec_path.exists()

        # 3. Create sample data
        data = pd.DataFrame(
            {
                "quarter": ["Q1", "Q2", "Q3", "Q4"],
                "revenue": [25000000, 27500000, 29000000, 31500000],
            }
        )

        data_path = temp_project / "data" / "revenue.csv"
        data.to_csv(data_path, index=False)

        # 4. Workflow orchestration
        orchestrator = WorkflowOrchestrator(project_root=temp_project)

        # Requirements stage
        result = orchestrator.run_requirements_stage()
        assert result["success"]

        # Data loading stage
        result = orchestrator.run_data_loading_stage()
        assert result["success"]

        # 5. Create outputs
        chart_config = ChartFactory.bar(
            data=data.to_dict("records"),
            x="quarter",
            y=["revenue"],
            title="Quarterly Revenue",
        )

        chart_path = temp_project / "outputs" / "charts" / "revenue.json"
        chart_path.parent.mkdir(parents=True, exist_ok=True)

        with open(chart_path, "w") as f:
            json.dump(chart_config.to_dict(), f)

        # 6. Validate
        pipeline = ValidationPipeline(
            ValidationConfig(
                strict=True,
                save_reports=True,
                report_dir=temp_project / "project_state" / "validation_reports",
            )
        )

        report = pipeline.validate_chart(
            data=data,
            chart_config=chart_config.to_dict(),
            output_path=chart_path,
        )

        assert report.overall_passed

        # 7. State management
        state_manager = StateManager(project_root=temp_project)
        summary = state_manager.get_state_summary()

        assert summary["project_initialized"]
        assert summary["interview_complete"]

        # 8. Export complete state
        export_path = state_manager.export_complete_state()
        assert export_path.exists()

        # Verify complete state contains all components
        import yaml

        with open(export_path) as f:
            complete_state = yaml.safe_load(f)

        assert "states" in complete_state
        assert "summary" in complete_state
        assert complete_state["summary"]["project_initialized"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
