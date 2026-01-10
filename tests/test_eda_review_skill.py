#!/usr/bin/env python3
"""
Unit tests for EDA Review Skill.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml


def test_eda_review_skill_runs_only_in_eda_stage():
    """Test that EDA Review skill is scoped to eda stage only."""
    from kie.skills.eda_review import EDAReviewSkill

    skill = EDAReviewSkill()

    assert skill.stage_scope == ["eda"]
    assert "eda" in skill.stage_scope
    assert "analyze" not in skill.stage_scope
    assert "build" not in skill.stage_scope


def test_eda_review_skill_requires_eda_profile():
    """Test that EDA Review skill requires eda_profile artifact."""
    from kie.skills.eda_review import EDAReviewSkill

    skill = EDAReviewSkill()

    assert "eda_profile" in skill.required_artifacts


def test_eda_review_skill_produces_artifacts():
    """Test that EDA Review skill declares output artifacts."""
    from kie.skills.eda_review import EDAReviewSkill

    skill = EDAReviewSkill()

    assert "eda_review.md" in skill.produces_artifacts
    assert "eda_review.json" in skill.produces_artifacts


def test_eda_review_skill_execution_success():
    """Test EDA Review skill execution with valid profile."""
    from kie.skills.eda_review import EDAReviewSkill
    from kie.skills.base import SkillContext

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        outputs_dir = project_root / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Create mock EDA profile
        profile = {
            "shape": {"rows": 1000, "columns": 10},
            "column_types": {
                "numeric": ["revenue", "cost"],
                "categorical": ["region", "product"],
                "datetime": ["date"],
            },
            "quality": {
                "null_percent": 5.0,
                "duplicate_rows": 10,
                "duplicate_percent": 1.0,
            },
            "issues": {
                "high_null_columns": ["cost"],
                "constant_columns": [],
                "high_cardinality_columns": ["product"],
            },
        }

        profile_path = outputs_dir / "eda_profile.yaml"
        with open(profile_path, "w") as f:
            yaml.dump(profile, f)

        # Execute skill
        skill = EDAReviewSkill()
        context = SkillContext(
            project_root=project_root,
            current_stage="eda",
            artifacts={
                "selected_data_file": "data/test.csv",
                "eda_profile": str(profile_path),
            },
            evidence_ledger_id=None,
        )

        result = skill.execute(context)

        # Verify success
        assert result.success is True

        # Verify artifacts created
        assert "eda_review.md" in result.artifacts
        assert "eda_review.json" in result.artifacts

        review_md_path = Path(result.artifacts["eda_review.md"])
        review_json_path = Path(result.artifacts["eda_review.json"])

        assert review_md_path.exists()
        assert review_json_path.exists()

        # Verify markdown content structure
        review_content = review_md_path.read_text()
        assert "# EDA Review (Internal)" in review_content
        assert "## 1. Data Overview" in review_content
        assert "## 2. Data Quality Assessment" in review_content
        assert "## 3. Key Patterns & Early Signals" in review_content
        assert "## 4. Anomalies & Outliers" in review_content
        assert "## 5. Analytical Implications" in review_content
        assert "## 6. Recommended Next Analytical Questions" in review_content

        # Verify evidence-backed claims
        assert "1,000 rows" in review_content  # References profile data
        assert "5.0%" in review_content  # Null percent from profile

        # Verify internal-only marker
        assert "INTERNAL THINKING ARTIFACT" in review_content

        # Verify JSON structure
        review_data = json.loads(review_json_path.read_text())
        assert review_data["internal_only"] is True
        assert "overview" in review_data
        assert "quality" in review_data
        assert "analytical_readiness" in review_data


def test_eda_review_skill_graceful_failure():
    """Test EDA Review skill graceful failure when profile missing."""
    from kie.skills.eda_review import EDAReviewSkill
    from kie.skills.base import SkillContext

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        outputs_dir = project_root / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Execute skill WITHOUT creating profile
        skill = EDAReviewSkill()
        context = SkillContext(
            project_root=project_root,
            current_stage="eda",
            artifacts={
                "selected_data_file": "data/test.csv",
            },
            evidence_ledger_id=None,
        )

        result = skill.execute(context)

        # Verify graceful failure (still succeeds, produces failure doc)
        assert result.success is True

        # Verify failure doc created
        assert "eda_review.md" in result.artifacts
        review_path = Path(result.artifacts["eda_review.md"])
        assert review_path.exists()

        # Verify failure doc content
        failure_content = review_path.read_text()
        assert "Review Could Not Be Produced" in failure_content
        assert "EDA profiling incomplete" in failure_content

        # Verify warning emitted
        assert len(result.warnings) > 0
        assert any("profiling" in w.lower() or "profile" in w.lower() for w in result.warnings)


def test_eda_review_skill_deterministic_output():
    """Test that same input produces same output (determinism)."""
    from kie.skills.eda_review import EDAReviewSkill
    from kie.skills.base import SkillContext

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        outputs_dir = project_root / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Create profile
        profile = {
            "shape": {"rows": 500, "columns": 5},
            "column_types": {
                "numeric": ["value"],
                "categorical": ["category"],
                "datetime": [],
            },
            "quality": {
                "null_percent": 0.0,
                "duplicate_rows": 0,
                "duplicate_percent": 0.0,
            },
            "issues": {
                "high_null_columns": [],
                "constant_columns": [],
                "high_cardinality_columns": [],
            },
        }

        profile_path = outputs_dir / "eda_profile.yaml"
        with open(profile_path, "w") as f:
            yaml.dump(profile, f)

        skill = EDAReviewSkill()
        context = SkillContext(
            project_root=project_root,
            current_stage="eda",
            artifacts={
                "selected_data_file": "data/test.csv",
                "eda_profile": str(profile_path),
            },
            evidence_ledger_id=None,
        )

        # Execute twice
        result1 = skill.execute(context)
        review1 = Path(result1.artifacts["eda_review.md"]).read_text()

        result2 = skill.execute(context)
        review2 = Path(result2.artifacts["eda_review.md"]).read_text()

        # Compare content (ignore timestamps)
        # Extract core content sections (skip generated timestamp)
        def extract_core_content(text):
            lines = text.split("\n")
            # Skip first 5 lines (header with timestamp)
            return "\n".join(lines[5:])

        core1 = extract_core_content(review1)
        core2 = extract_core_content(review2)

        # Core content should be identical for same input
        assert core1 == core2


def test_eda_review_skill_no_rails_mutation():
    """Test that EDA Review skill does NOT mutate Rails state."""
    from kie.skills.eda_review import EDAReviewSkill
    from kie.skills.base import SkillContext

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        outputs_dir = project_root / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Create Rails state
        rails_dir = project_root / "project_state"
        rails_dir.mkdir(parents=True, exist_ok=True)
        rails_state_path = rails_dir / "rails_state.json"
        rails_state_path.write_text(json.dumps({"current_stage": "eda"}))

        # Create profile
        profile = {
            "shape": {"rows": 100, "columns": 3},
            "column_types": {"numeric": ["x"], "categorical": ["y"], "datetime": []},
            "quality": {"null_percent": 0.0, "duplicate_rows": 0, "duplicate_percent": 0.0},
            "issues": {"high_null_columns": [], "constant_columns": [], "high_cardinality_columns": []},
        }

        profile_path = outputs_dir / "eda_profile.yaml"
        with open(profile_path, "w") as f:
            yaml.dump(profile, f)

        # Record original Rails state
        original_rails_state = rails_state_path.read_text()

        # Execute skill
        skill = EDAReviewSkill()
        context = SkillContext(
            project_root=project_root,
            current_stage="eda",
            artifacts={
                "selected_data_file": "data/test.csv",
                "eda_profile": str(profile_path),
            },
            evidence_ledger_id=None,
        )

        result = skill.execute(context)

        # Verify Rails state unchanged
        current_rails_state = rails_state_path.read_text()
        assert current_rails_state == original_rails_state

        # Skill should succeed but not touch Rails
        assert result.success is True


def test_eda_review_skill_references_data_file():
    """Test that EDA Review references selected data file."""
    from kie.skills.eda_review import EDAReviewSkill
    from kie.skills.base import SkillContext

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        outputs_dir = project_root / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        # Create profile
        profile = {
            "shape": {"rows": 200, "columns": 4},
            "column_types": {"numeric": ["a"], "categorical": ["b"], "datetime": []},
            "quality": {"null_percent": 0.0, "duplicate_rows": 0, "duplicate_percent": 0.0},
            "issues": {"high_null_columns": [], "constant_columns": [], "high_cardinality_columns": []},
        }

        profile_path = outputs_dir / "eda_profile.yaml"
        with open(profile_path, "w") as f:
            yaml.dump(profile, f)

        # Execute skill with specific data file
        skill = EDAReviewSkill()
        data_file = "data/acme_sales.csv"
        context = SkillContext(
            project_root=project_root,
            current_stage="eda",
            artifacts={
                "selected_data_file": data_file,
                "eda_profile": str(profile_path),
            },
            evidence_ledger_id=None,
        )

        result = skill.execute(context)

        # Verify review references data file
        review_path = Path(result.artifacts["eda_review.md"])
        review_content = review_path.read_text()

        assert data_file in review_content

        # Verify evidence contains data file
        assert "data_file" in result.evidence
        assert result.evidence["data_file"] == data_file
