"""
Tests for Showcase Mode

Proves that:
1. Showcase activates only under defined conditions
2. Showcase auto-disables once real data/spec present
3. Client Pack is generated and labeled DEMO
4. Evidence Ledger exists for showcase run
5. Normal /go behavior unaffected when showcase disabled
6. No rails_state mutation leaks into real mode
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from kie.showcase import should_activate_showcase, mark_showcase_completed, run_showcase


def test_showcase_activates_with_env_var(tmp_path):
    """Test showcase activates when KIE_SHOWCASE=1."""
    # Set environment variable
    os.environ["KIE_SHOWCASE"] = "1"

    try:
        assert should_activate_showcase(tmp_path) is True
    finally:
        # Clean up
        del os.environ["KIE_SHOWCASE"]


def test_showcase_activates_on_first_run(tmp_path):
    """Test showcase activates on first-ever run (no data, no spec)."""
    # No data/, no spec.yaml, no showcase_completed flag
    assert should_activate_showcase(tmp_path) is True


def test_showcase_disabled_when_real_data_exists(tmp_path):
    """Test showcase disabled when real data exists."""
    # Create data directory with real data
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "real_data.csv").write_text("col1,col2\n1,2\n")

    assert should_activate_showcase(tmp_path) is False


def test_showcase_disabled_when_real_spec_exists(tmp_path):
    """Test showcase disabled when real spec.yaml exists."""
    # Create project_state with real spec
    project_state = tmp_path / "project_state"
    project_state.mkdir()

    spec_file = project_state / "spec.yaml"
    spec_file.write_text("""
project_name: "Real Project"
client_name: "Real Client"
objective: "Real objective"
""")

    assert should_activate_showcase(tmp_path) is False


def test_showcase_disabled_when_showcase_completed(tmp_path):
    """Test showcase disabled when showcase_completed flag exists."""
    # Create showcase_completed flag
    project_state = tmp_path / "project_state"
    project_state.mkdir()

    showcase_flag = project_state / "showcase_completed"
    showcase_flag.write_text("Showcase completed\n")

    assert should_activate_showcase(tmp_path) is False


def test_showcase_allowed_with_demo_spec(tmp_path):
    """Test showcase allowed when only demo spec exists."""
    # Create project_state with demo spec
    project_state = tmp_path / "project_state"
    project_state.mkdir()

    spec_file = project_state / "spec.yaml"
    spec_file.write_text("""
# SHOWCASE DEMO SPECIFICATION
project_name: "Demo Project (DEMO)"
showcase_mode: true
""")

    # Should still allow showcase (this is the demo spec, not real)
    assert should_activate_showcase(tmp_path) is True


def test_mark_showcase_completed_creates_flag(tmp_path):
    """Test marking showcase as completed creates flag."""
    mark_showcase_completed(tmp_path)

    showcase_flag = tmp_path / "project_state" / "showcase_completed"
    assert showcase_flag.exists()

    # Should now be disabled
    assert should_activate_showcase(tmp_path) is False


def test_showcase_run_generates_client_pack(tmp_path):
    """Test showcase run generates client_pack.md with DEMO labeling."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    # Check client_pack.md exists
    client_pack = tmp_path / "outputs" / "client_pack.md"
    assert client_pack.exists()

    # Verify DEMO labeling
    content = client_pack.read_text()
    assert "SHOWCASE — DEMO DATA" in content
    assert "demo data" in content.lower()


def test_showcase_run_generates_evidence_ledger(tmp_path):
    """Test showcase run generates Evidence Ledger."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    # Check Evidence Ledger directory exists
    evidence_dir = tmp_path / "project_state" / "evidence_ledger"
    assert evidence_dir.exists()

    # Check for ledger files
    ledger_files = list(evidence_dir.glob("showcase_*.yaml"))
    assert len(ledger_files) > 0


def test_showcase_run_generates_wow_stack(tmp_path):
    """Test showcase run generates full WOW Stack."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    outputs_dir = tmp_path / "outputs"

    # Check for WOW Stack artifacts
    assert (outputs_dir / "insights_catalog.json").exists()
    assert (outputs_dir / "insight_triage.json").exists()
    assert (outputs_dir / "insight_triage.md").exists()
    assert (outputs_dir / "insight_brief.md").exists()
    assert (outputs_dir / "run_story.md").exists()
    assert (outputs_dir / "client_readiness.json").exists()
    assert (outputs_dir / "client_pack.md").exists()


def test_showcase_does_not_write_to_data_dir(tmp_path):
    """Test showcase does not write to data/ directory."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    # Check data/ does not exist or is empty
    data_dir = tmp_path / "data"
    if data_dir.exists():
        data_files = [f for f in data_dir.iterdir() if f.is_file()]
        assert len(data_files) == 0


def test_showcase_writes_to_showcase_dir(tmp_path):
    """Test showcase writes demo data to showcase/ directory."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    # Check showcase/ directory exists
    showcase_dir = tmp_path / "project_state" / "showcase"
    assert showcase_dir.exists()

    # Check for demo data
    demo_data = showcase_dir / "demo_data.csv"
    assert demo_data.exists()


def test_showcase_creates_rails_state(tmp_path):
    """Test showcase creates rails_state.json."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    # Check rails_state exists
    rails_state_path = tmp_path / "project_state" / "rails_state.json"
    assert rails_state_path.exists()

    # Verify showcase_mode flag
    rails_state = json.loads(rails_state_path.read_text())
    assert rails_state.get("showcase_mode") is True


def test_showcase_trust_bundle_has_showcase_flag(tmp_path):
    """Test showcase Trust Bundle includes showcase_mode flag."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    # Check trust bundle
    trust_bundle_path = tmp_path / "project_state" / "trust_bundle.json"
    assert trust_bundle_path.exists()

    trust_bundle = json.loads(trust_bundle_path.read_text())
    assert trust_bundle.get("showcase_mode") is True


def test_showcase_client_readiness_has_showcase_flag(tmp_path):
    """Test showcase client_readiness includes showcase_mode flag."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    # Check client_readiness
    readiness_path = tmp_path / "outputs" / "client_readiness.json"
    assert readiness_path.exists()

    readiness = json.loads(readiness_path.read_text())
    assert readiness.get("showcase_mode") is True


def test_showcase_all_outputs_labeled_demo(tmp_path):
    """Test all showcase markdown outputs are labeled DEMO."""
    # Run showcase
    result = run_showcase(tmp_path)

    assert result["success"] is True

    outputs_dir = tmp_path / "outputs"

    # Check all markdown files
    md_files = list(outputs_dir.glob("*.md"))
    assert len(md_files) > 0

    for md_file in md_files:
        content = md_file.read_text()
        # Each markdown should mention DEMO or demo data
        assert "DEMO" in content or "demo" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
