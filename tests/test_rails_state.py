"""
Test Rails State Tracking

Verifies that rails_state.json is created and updated correctly
as commands execute through the Rails workflow.
"""

import json
import subprocess
import tempfile
from pathlib import Path


def test_rails_state_creation():
    """Test that rails_state.json is created after startkie."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        kie_repo = Path(__file__).parent.parent

        # Bootstrap workspace
        result = subprocess.run(
            ["bash", str(kie_repo / "tools" / "bootstrap" / "startkie.sh")],
            cwd=project_root,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(kie_repo)},
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Bootstrap failed: {result.stderr}"

        # Check rails_state.json was created
        state_path = project_root / "project_state" / "rails_state.json"
        assert state_path.exists(), "rails_state.json not created"

        # Verify content
        with open(state_path) as f:
            state = json.load(f)

        assert "startkie" in state["completed_stages"]
        assert state["current_stage"] == "startkie"
        assert state["workflow_started"] is True


def test_rails_state_progression():
    """Test that Rails state advances correctly through workflow stages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        kie_repo = Path(__file__).parent.parent

        # Bootstrap
        subprocess.run(
            ["bash", str(kie_repo / "tools" / "bootstrap" / "startkie.sh")],
            cwd=project_root,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(kie_repo)},
            capture_output=True,
            text=True
        )

        state_path = project_root / "project_state" / "rails_state.json"

        # Run spec --set
        subprocess.run(
            [
                "python3", "-m", "kie.cli",
                "spec", "--set", "client_name=TestCo",
                "--set", "objective=Test",
                "--set", "deliverable_format=report"
            ],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        # Check state updated
        with open(state_path) as f:
            state = json.load(f)

        assert "startkie" in state["completed_stages"]
        assert "spec" in state["completed_stages"]
        assert state["current_stage"] == "spec"

        # Add test data
        data_dir = project_root / "data"
        (data_dir / "test.csv").write_text("col1,col2\n1,2\n3,4\n")

        # Run eda
        subprocess.run(
            ["python3", "-m", "kie.cli", "eda"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Check state updated
        with open(state_path) as f:
            state = json.load(f)

        assert "eda" in state["completed_stages"]
        assert state["current_stage"] == "eda"


def test_status_displays_rails_progress():
    """Test that /status includes Rails progress information."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        kie_repo = Path(__file__).parent.parent

        # Bootstrap
        subprocess.run(
            ["bash", str(kie_repo / "tools" / "bootstrap" / "startkie.sh")],
            cwd=project_root,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(kie_repo)},
            capture_output=True,
            text=True
        )

        # Run status
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "status"],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"status failed: {result.stderr}"

        # Status output should mention Rails progress
        # The handler returns a dict with rails_progress key
        # which gets printed by the CLI
        output = result.stdout.lower()
        assert "rails" in output or "progress" in output or "completed" in output


def test_suggest_next_command():
    """Test that suggest_next() returns correct next command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Before startkie
        from kie.state import suggest_next_command
        next_cmd = suggest_next_command(project_root)
        assert next_cmd == "startkie"

        # Create minimal state
        state_dir = project_root / "project_state"
        state_dir.mkdir(parents=True)
        state_path = state_dir / "rails_state.json"

        # After startkie
        state_path.write_text(json.dumps({
            "completed_stages": ["startkie"],
            "current_stage": "startkie",
            "workflow_started": True,
            "last_updated": "2025-01-01T00:00:00"
        }))

        next_cmd = suggest_next_command(project_root)
        assert next_cmd == "spec"

        # After spec
        state_path.write_text(json.dumps({
            "completed_stages": ["startkie", "spec"],
            "current_stage": "spec",
            "workflow_started": True,
            "last_updated": "2025-01-01T00:00:00"
        }))

        next_cmd = suggest_next_command(project_root)
        assert next_cmd == "eda"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
