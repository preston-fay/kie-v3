"""
Tests for Trust Bundle generation.

Verifies that Trust Bundle is created for all command execution scenarios.
"""

import json
import tempfile
from pathlib import Path

import pytest

from kie.observability import EvidenceLedger, create_ledger
from kie.observability.trust_bundle import generate_trust_bundle, save_trust_bundle


def test_trust_bundle_normal_success():
    """Test Trust Bundle for normal successful command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create project structure
        (project_root / "project_state").mkdir()
        (project_root / "outputs").mkdir()

        # Create sample output file
        output_file = project_root / "outputs" / "test_output.json"
        output_file.write_text('{"test": true}')

        # Create evidence ledger
        ledger = create_ledger("eda", {"data_source": "test.csv"}, project_root)
        ledger.rails_stage_after = "eda"
        ledger.success = True
        ledger.outputs.append({
            "path": str(output_file),
            "hash": "abc123def456",
        })

        # Create result
        result = {
            "success": True,
            "next_steps": ["python3 -m kie.cli analyze"],
        }

        # Generate trust bundle
        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Verify markdown structure
        assert "# Trust Bundle" in markdown
        assert "## 1. Run Identity" in markdown
        assert "## 2. Current Workflow State" in markdown
        assert "## 3. What Executed" in markdown
        assert "## 4. Evidence Ledger" in markdown
        assert "## 5. Artifacts Produced" in markdown
        assert "## 6. Skills Executed" in markdown
        assert "## 7. Warnings / Blocks" in markdown
        assert "## 8. What's Missing" in markdown
        assert "## 9. Next CLI Actions" in markdown

        # Verify run identity
        assert ledger.run_id in markdown
        assert "/eda" in markdown

        # Verify workflow state
        assert "eda" in markdown

        # Verify artifacts
        assert "outputs/test_output.json" in markdown or "test_output.json" in markdown
        assert "abc123" in markdown

        # Verify next actions
        assert "python3 -m kie.cli analyze" in markdown

        # Verify JSON data
        assert json_data["run_identity"]["command"] == "eda"
        assert json_data["workflow_state"]["stage_after"] == "eda"
        assert len(json_data["artifacts_produced"]) == 1
        assert json_data["next_cli_actions"] == ["python3 -m kie.cli analyze"]


def test_trust_bundle_blocked_precondition():
    """Test Trust Bundle when command is blocked by precondition."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        # Create evidence ledger
        ledger = create_ledger("build", {}, project_root)
        ledger.rails_stage_before = "spec"
        ledger.rails_stage_after = "spec"  # Didn't advance
        ledger.success = False
        ledger.errors.append("Cannot build: missing data")

        # Create result with block
        result = {
            "success": False,
            "blocked": True,
            "block_reason": "Missing data files in data/ directory",
            "recovery_commands": [
                "# Add data files to data/ directory",
                "python3 -m kie.cli eda",
            ],
        }

        # Generate trust bundle
        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Verify blocks section
        assert "## 7. Warnings / Blocks" in markdown
        assert "🚫" in markdown
        assert "Missing data files" in markdown

        # Verify next actions include recovery
        assert "## 9. Next CLI Actions" in markdown
        assert "Add data files" in markdown or "eda" in markdown

        # Verify JSON data
        assert json_data["warnings_blocks"]["blocks"]
        assert len(json_data["next_cli_actions"]) >= 1


def test_trust_bundle_valid_failure():
    """Test Trust Bundle when command fails naturally (not blocked)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        # Create evidence ledger
        ledger = create_ledger("analyze", {}, project_root)
        ledger.rails_stage_before = "eda"
        ledger.rails_stage_after = "eda"  # Failed, didn't advance
        ledger.success = False
        ledger.errors.append("Analysis failed: insufficient data variance")

        # Create result (failure but not blocked)
        result = {
            "success": False,
            "next_steps": [
                "python3 -m kie.cli eda",
                "# Review data quality and try again",
            ],
        }

        # Generate trust bundle
        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Verify failure status
        assert "✗ FAILED" in markdown

        # Verify errors are recorded (but not as blocks)
        assert "insufficient data variance" in markdown

        # Verify next actions are present
        assert "## 9. Next CLI Actions" in markdown
        assert "eda" in markdown

        # Verify JSON data
        assert not json_data["what_executed"]["success"]
        assert json_data["next_cli_actions"]


def test_trust_bundle_guidance_no_op():
    """Test Trust Bundle when command provides guidance (e.g., /go with missing data)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        # Create evidence ledger
        ledger = create_ledger("go", {}, project_root)
        ledger.rails_stage_before = "spec"
        ledger.rails_stage_after = "spec"  # No change
        ledger.success = True  # Guidance succeeded
        ledger.warnings.append("No data files found")

        # Create result with guidance
        result = {
            "success": True,
            "guidance": True,
            "message": "Add data files to proceed",
            "next_steps": [
                "# Add CSV, Excel, Parquet, or JSON file to data/",
                "python3 -m kie.cli eda",
            ],
        }

        # Generate trust bundle
        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Verify success (guidance is successful)
        assert "✓ SUCCESS" in markdown

        # Verify warnings
        assert "## 7. Warnings / Blocks" in markdown
        assert "No data files found" in markdown

        # Verify what's missing
        assert "## 8. What's Missing" in markdown

        # Verify next actions
        assert "## 9. Next CLI Actions" in markdown
        assert "eda" in markdown

        # Verify JSON data
        assert json_data["what_executed"]["success"]
        assert json_data["warnings_blocks"]["warnings"]
        assert json_data["next_cli_actions"]


def test_trust_bundle_with_skills():
    """Test Trust Bundle includes skills execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()
        (project_root / "outputs").mkdir()

        # Create skill artifact
        skill_artifact = project_root / "outputs" / "skill_artifact.json"
        skill_artifact.write_text('{"skill": "output"}')

        # Create evidence ledger
        ledger = create_ledger("analyze", {}, project_root)
        ledger.rails_stage_after = "analyze"
        ledger.success = True

        # Add skill execution
        ledger.proof_references["skills_executed"] = [
            {
                "skill_id": "insight_enhancer",
                "success": True,
                "artifacts": {
                    "enhanced_insights": str(skill_artifact),
                },
            }
        ]

        # Create result
        result = {"success": True}

        # Generate trust bundle
        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Verify skills section
        assert "## 6. Skills Executed" in markdown
        assert "insight_enhancer" in markdown
        assert "✓" in markdown  # Success indicator

        # Verify skill artifacts in artifacts section
        assert "## 5. Artifacts Produced" in markdown
        assert "skill_artifact.json" in markdown

        # Verify JSON data
        assert len(json_data["skills_executed"]) == 1
        assert json_data["skills_executed"][0]["skill_id"] == "insight_enhancer"


def test_trust_bundle_save():
    """Test Trust Bundle is saved to disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        # Create evidence ledger
        ledger = create_ledger("status", {}, project_root)
        result = {"success": True}

        # Generate trust bundle
        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Save trust bundle
        md_path, json_path = save_trust_bundle(markdown, json_data, project_root)

        # Verify files exist
        assert md_path is not None
        assert json_path is not None
        assert md_path.exists()
        assert json_path.exists()

        # Verify markdown content
        saved_markdown = md_path.read_text()
        assert "# Trust Bundle" in saved_markdown
        assert ledger.run_id in saved_markdown

        # Verify JSON content
        saved_json = json.loads(json_path.read_text())
        assert saved_json["run_identity"]["run_id"] == ledger.run_id


def test_trust_bundle_always_has_next_actions():
    """Test that Next CLI Actions is never empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        # Create evidence ledger with no next steps
        ledger = create_ledger("doctor", {}, project_root)
        result = {"success": True}  # No next_steps provided

        # Generate trust bundle
        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Verify next actions section exists and has content
        assert "## 9. Next CLI Actions" in markdown
        assert "python3 -m kie.cli" in markdown  # Fallback to status

        # Verify JSON data
        assert json_data["next_cli_actions"]
        assert len(json_data["next_cli_actions"]) > 0


def test_trust_bundle_does_not_alter_result():
    """Test that Trust Bundle generation does not modify result dictionary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("eda", {}, project_root)
        result = {
            "success": True,
            "outputs": ["test.json"],
        }

        # Store original result
        original_result = result.copy()

        # Generate trust bundle
        generate_trust_bundle(ledger, result, project_root)

        # Verify result unchanged
        assert result == original_result


def test_trust_bundle_with_evidence_ledger_linkage():
    """Test Trust Bundle includes evidence ledger ID and path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("spec", {"init": True}, project_root)
        result = {"success": True}

        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Verify ledger linkage in markdown
        assert "## 4. Evidence Ledger" in markdown
        assert ledger.run_id in markdown
        assert f"evidence_ledger/{ledger.run_id}.yaml" in markdown

        # Verify ledger linkage in JSON
        assert json_data["evidence_ledger"]["ledger_id"] == ledger.run_id
        assert ledger.run_id in json_data["evidence_ledger"]["ledger_path"]


def test_trust_bundle_with_artifacts_and_hashes():
    """Test Trust Bundle includes artifacts with hashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()
        (project_root / "outputs").mkdir()

        # Create real artifact
        artifact = project_root / "outputs" / "profile.json"
        artifact.write_text('{"test": "data"}')

        # Compute real hash
        from kie.observability.evidence_ledger import compute_file_hash
        real_hash = compute_file_hash(artifact)

        ledger = create_ledger("eda", {}, project_root)
        ledger.outputs.append({
            "path": str(artifact),
            "hash": real_hash,
        })
        result = {"success": True}

        markdown, json_data = generate_trust_bundle(ledger, result, project_root)

        # Verify hash in markdown
        assert "profile.json" in markdown
        assert real_hash[:16] in markdown  # Truncated hash

        # Verify hash in JSON
        artifacts = json_data["artifacts_produced"]
        assert len(artifacts) == 1
        assert artifacts[0]["hash"] == real_hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
