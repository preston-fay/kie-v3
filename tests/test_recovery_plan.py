"""
Tests for Recovery Plan generation.

Verifies that Recovery Plan is created for WARN, BLOCK, and FAIL scenarios.
"""

import tempfile
from pathlib import Path

import pytest

from kie.observability import EvidenceLedger, create_ledger
from kie.observability.recovery_plan import (
    generate_recovery_plan,
    save_recovery_plan,
    should_generate_recovery_plan,
)


def test_recovery_plan_for_blocked_precondition():
    """Test Recovery Plan generated when command is blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        # Create ledger for blocked command
        ledger = create_ledger("build", {}, project_root)
        ledger.rails_stage_before = "spec"
        ledger.rails_stage_after = "spec"  # Didn't advance
        ledger.success = False
        ledger.errors.append("Missing data files")

        # Create result with block
        result = {
            "success": False,
            "blocked": True,
            "block_reason": "Cannot build without data files",
            "recovery_commands": [
                "# Add data files to data/ directory",
                "python3 -m kie.cli eda",
            ],
        }

        # Should generate recovery plan
        assert should_generate_recovery_plan(ledger, result)

        # Generate recovery plan
        markdown = generate_recovery_plan(ledger, result, project_root)

        # Verify structure
        assert "# Recovery Plan" in markdown
        assert "## 1. What happened" in markdown
        assert "## 2. Why it happened (proof-backed)" in markdown
        assert "## 3. Fix it now (Tier 1)" in markdown
        assert "## 4. Validate (Tier 2)" in markdown
        assert "## 5. Diagnose environment (Tier 3)" in markdown
        assert "## 6. Escalate safely (Tier 4)" in markdown

        # Verify Tier 1 contains recovery commands
        assert "python3 -m kie.cli eda" in markdown
        assert "Add data files" in markdown

        # Verify Tier 2 contains validation
        assert "python3 -m kie.cli rails" in markdown
        assert "python3 -m kie.cli validate" in markdown

        # Verify Tier 3 contains diagnostics
        assert "python3 -m kie.cli doctor" in markdown

        # Verify Tier 4 contains escalation paths
        assert "project_state/trust_bundle.md" in markdown
        assert "project_state/evidence_ledger" in markdown
        assert "project_state/rails_state.json" in markdown

        # Verify no manual edits or destructive actions
        assert "delete" not in markdown.lower()
        assert "edit" not in markdown.lower() or "Do NOT" in markdown


def test_recovery_plan_for_valid_failure():
    """Test Recovery Plan generated when command fails naturally."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        # Create ledger for failed command
        ledger = create_ledger("analyze", {}, project_root)
        ledger.rails_stage_before = "eda"
        ledger.rails_stage_after = "eda"  # Failed, didn't advance
        ledger.success = False
        ledger.errors.append("Insufficient data variance for analysis")

        # Create result (failure but not blocked)
        result = {
            "success": False,
        }

        # Should generate recovery plan
        assert should_generate_recovery_plan(ledger, result)

        # Generate recovery plan
        markdown = generate_recovery_plan(ledger, result, project_root)

        # Verify structure
        assert "# Recovery Plan" in markdown
        assert "## 1. What happened" in markdown
        assert "Command execution failed" in markdown or "Command failed" in markdown

        # Verify Tier 1 suggests re-running with fixes
        assert "## 3. Fix it now (Tier 1)" in markdown
        assert "python3 -m kie.cli" in markdown

        # Verify errors are referenced
        assert "Insufficient data variance" in markdown or "Error:" in markdown


def test_recovery_plan_not_created_for_success():
    """Test Recovery Plan NOT created for clean success."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create ledger for successful command
        ledger = create_ledger("eda", {}, project_root)
        ledger.rails_stage_after = "eda"
        ledger.success = True

        # Create successful result
        result = {"success": True}

        # Should NOT generate recovery plan
        assert not should_generate_recovery_plan(ledger, result)


def test_recovery_plan_for_enforcement_warn():
    """Test Recovery Plan generated for enforcement warnings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        # Create ledger
        ledger = create_ledger("build", {}, project_root)
        ledger.success = True  # Command succeeded but with warnings

        # Create result with enforcement warning
        result = {
            "success": True,
            "enforcement_result": {
                "decision": "WARN",
                "message": "Data completeness below threshold",
                "violated_invariant": "data_quality_minimum",
            },
        }

        # Should generate recovery plan for WARN
        assert should_generate_recovery_plan(ledger, result)

        # Generate recovery plan
        markdown = generate_recovery_plan(ledger, result, project_root)

        # Verify structure
        assert "# Recovery Plan" in markdown
        assert "## 2. Why it happened (proof-backed)" in markdown
        assert "Policy violation" in markdown or "data completeness" in markdown.lower()


def test_recovery_plan_includes_trust_bundle_linkage():
    """Test Recovery Plan includes Trust Bundle and Evidence Ledger references."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("build", {}, project_root)
        ledger.success = False
        ledger.errors.append("Build failed")

        result = {"success": False}

        # Generate recovery plan
        markdown = generate_recovery_plan(ledger, result, project_root)

        # Verify linkage to other artifacts
        assert "project_state/trust_bundle.md" in markdown
        assert f"project_state/evidence_ledger/{ledger.run_id}.yaml" in markdown
        assert "project_state/rails_state.json" in markdown


def test_recovery_plan_tier_ordering():
    """Test Recovery Plan tiers are in correct order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("analyze", {}, project_root)
        ledger.success = False

        result = {"success": False}

        markdown = generate_recovery_plan(ledger, result, project_root)

        # Find positions of each tier
        tier1_pos = markdown.find("## 3. Fix it now (Tier 1)")
        tier2_pos = markdown.find("## 4. Validate (Tier 2)")
        tier3_pos = markdown.find("## 5. Diagnose environment (Tier 3)")
        tier4_pos = markdown.find("## 6. Escalate safely (Tier 4)")

        # Verify all tiers present
        assert tier1_pos > 0
        assert tier2_pos > 0
        assert tier3_pos > 0
        assert tier4_pos > 0

        # Verify order
        assert tier1_pos < tier2_pos < tier3_pos < tier4_pos


def test_recovery_plan_tier1_cli_only():
    """Test Tier 1 commands are CLI-only and non-destructive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("build", {}, project_root)
        ledger.success = False
        ledger.proof_references["has_data"] = False

        result = {"success": False}

        markdown = generate_recovery_plan(ledger, result, project_root)

        # Extract Tier 1 section
        tier1_start = markdown.find("## 3. Fix it now (Tier 1)")
        tier1_end = markdown.find("## 4. Validate (Tier 2)")
        tier1_section = markdown[tier1_start:tier1_end]

        # Verify CLI commands
        assert "python3 -m kie.cli" in tier1_section

        # Verify no manual edits
        assert "edit" not in tier1_section.lower() or "# " in tier1_section
        assert "manually" not in tier1_section.lower()

        # Verify no destructive actions
        assert "delete" not in tier1_section.lower()
        assert "rm " not in tier1_section.lower()
        assert "remove" not in tier1_section.lower() or "Remove" not in tier1_section


def test_recovery_plan_save():
    """Test Recovery Plan is saved to disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("eda", {}, project_root)
        ledger.success = False

        result = {"success": False}

        # Generate recovery plan
        markdown = generate_recovery_plan(ledger, result, project_root)

        # Save recovery plan
        plan_path = save_recovery_plan(markdown, project_root)

        # Verify file exists
        assert plan_path is not None
        assert plan_path.exists()
        assert plan_path.name == "recovery_plan.md"

        # Verify content
        saved_markdown = plan_path.read_text()
        assert "# Recovery Plan" in saved_markdown
        assert ledger.run_id in saved_markdown


def test_recovery_plan_does_not_alter_result():
    """Test Recovery Plan generation does not modify result dictionary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("build", {}, project_root)
        ledger.success = False

        result = {
            "success": False,
            "blocked": True,
            "block_reason": "Missing prerequisite",
        }

        # Store original result
        original_result = result.copy()

        # Generate recovery plan
        generate_recovery_plan(ledger, result, project_root)

        # Verify result unchanged
        assert result == original_result


def test_recovery_plan_with_enforcement_block():
    """Test Recovery Plan correctly handles enforcement blocks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("analyze", {}, project_root)
        ledger.success = False

        result = {
            "success": False,
            "enforcement_result": {
                "decision": "BLOCK",
                "message": "Cannot analyze without completing EDA first",
                "violated_invariant": "rails_stage_progression",
                "recovery_commands": [
                    "python3 -m kie.cli eda",
                ],
            },
        }

        markdown = generate_recovery_plan(ledger, result, project_root)

        # Verify block is explained
        assert "blocked" in markdown.lower() or "BLOCK" in markdown
        assert "Cannot analyze without completing EDA" in markdown

        # Verify recovery command from enforcement
        assert "python3 -m kie.cli eda" in markdown


def test_recovery_plan_missing_spec():
    """Test Recovery Plan provides correct guidance when spec is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()
        (project_root / "data").mkdir()

        ledger = create_ledger("build", {}, project_root)
        ledger.success = False
        # Set has_data to True so spec check is triggered
        ledger.proof_references["has_data"] = True

        result = {"success": False}

        markdown = generate_recovery_plan(ledger, result, project_root)

        # Should suggest spec initialization
        assert "python3 -m kie.cli spec --init" in markdown


def test_recovery_plan_dashboard_adds_node_guidance():
    """Test Recovery Plan adds Node.js guidance for dashboard commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir()

        ledger = create_ledger("build", {}, project_root)
        ledger.success = False

        result = {"success": False, "dashboard": "failed"}

        markdown = generate_recovery_plan(ledger, result, project_root)

        # Verify Node.js guidance in Tier 3
        tier3_start = markdown.find("## 5. Diagnose environment (Tier 3)")
        tier3_end = markdown.find("## 6. Escalate safely (Tier 4)")
        tier3_section = markdown[tier3_start:tier3_end]

        assert "node" in tier3_section.lower() or "Node" in tier3_section


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
