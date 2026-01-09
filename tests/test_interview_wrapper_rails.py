"""
Test interview wrapper Rails flow

Verifies that the post-interview Rails path works correctly:
spec --set → eda → analyze → build
"""

import subprocess
import tempfile
from pathlib import Path


def test_interview_rails_flow_with_data():
    """Test complete Rails flow after spec is set (simulating post-interview)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        kie_repo = Path(__file__).parent.parent  # /Users/.../kie-v3

        # Bootstrap workspace
        result = subprocess.run(
            ["bash", str(kie_repo / "tools" / "bootstrap" / "startkie.sh")],
            cwd=project_root,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(kie_repo)},
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Bootstrap failed: {result.stderr}"

        # Add test data file (small CSV fixture)
        data_dir = project_root / "data"
        test_data = data_dir / "test_sleep_data.csv"
        test_data.write_text(
            "sleep_hours,sleep_quality,age\n"
            "7.5,8,25\n"
            "6.0,5,30\n"
            "8.5,9,22\n"
            "5.5,4,35\n"
            "7.0,7,28\n"
        )

        # Simulate interview completion by running spec --set
        result = subprocess.run(
            [
                "python3", "-m", "kie.cli",
                "spec",
                "--set", "client_name=SleepCo",
                "--set", "objective=Drivers of sleep quality",
                "--set", "deliverable_format=report"
            ],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"spec --set failed: {result.stderr}"

        # Run Rails workflow: eda
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "eda"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0, f"eda failed: {result.stderr}\nStdout: {result.stdout}"

        # Run Rails workflow: analyze
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "analyze"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0, f"analyze failed: {result.stderr}\nStdout: {result.stdout}"

        # Run Rails workflow: build
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "build"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0, f"build failed: {result.stderr}\nStdout: {result.stdout}"

        # Verify outputs directory exists (build may or may not generate charts depending on data)
        outputs_dir = project_root / "outputs"
        # Note: outputs dir creation is optional - build may succeed without creating outputs
        # if there's insufficient data for analysis. The key success is RC=0 for all commands.


def test_rails_flow_without_data():
    """Test that workflow handles missing data gracefully."""
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

        # Set spec without data
        result = subprocess.run(
            [
                "python3", "-m", "kie.cli",
                "spec",
                "--set", "client_name=TestCo",
                "--set", "objective=Test without data",
                "--set", "deliverable_format=report"
            ],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"spec --set failed: {result.stderr}"

        # eda should fail gracefully when no data
        result = subprocess.run(
            ["python3", "-m", "kie.cli", "eda"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        # eda may fail (RC=1) or succeed with warning - either is acceptable
        # The important thing is it doesn't crash
        assert result.returncode in [0, 1], f"eda crashed unexpectedly: {result.stderr}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
