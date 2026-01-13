"""
Tests for PR #1: Render-Time KDS Validation

Tests the critical enforcement gate that prevents non-KDS charts
from being published to consultants.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from kie.charts.renderer import ChartRenderer
from kie.exceptions import BrandComplianceError


class TestRenderTimeValidation:
    """Test suite for render-time KDS validation."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with required structure."""
        tmpdir = tempfile.mkdtemp()
        project_root = Path(tmpdir)

        # Create required directories
        (project_root / "outputs").mkdir()
        (project_root / "outputs" / "charts").mkdir()
        (project_root / "data").mkdir()

        # Create sample data file
        data = pd.DataFrame({
            "category": ["North", "South", "East", "West"],
            "revenue": [1200, 800, 1500, 1100],
        })
        data_path = project_root / "data" / "sample.csv"
        data.to_csv(data_path, index=False)

        yield project_root

    @pytest.fixture
    def visualization_plan_valid(self, temp_workspace):
        """
        Create visualization plan that will generate KDS-compliant charts.
        """
        viz_plan = {
            "specifications": [
                {
                    "insight_id": "test_001",
                    "insight_title": "Test Insight",
                    "visualization_required": True,
                    "visualization_type": "bar",
                    "purpose": "comparison",
                    "x_axis": "category",
                    "y_axis": "revenue",
                    "highlights": [],
                    "suppress": [],
                    "annotations": [],
                    "caveats": [],
                    "confidence": {},
                }
            ]
        }

        viz_plan_path = temp_workspace / "outputs" / "visualization_plan.json"
        with open(viz_plan_path, "w") as f:
            json.dump(viz_plan, f)

        return viz_plan_path

    def test_renderer_validates_kds_compliance_success(
        self, temp_workspace, visualization_plan_valid
    ):
        """
        TEST: Renderer validates charts and passes when compliant.

        This is the HAPPY PATH - charts are KDS-compliant and validation passes.
        """
        renderer = ChartRenderer(temp_workspace)

        # Render charts with validation enabled (default)
        result = renderer.render_charts(validate=True)

        # Should succeed
        assert result["success"] is True
        assert result["charts_rendered"] == 1
        assert result["kds_validated"] is True

        # Chart file should exist
        chart_file = temp_workspace / "outputs" / "charts" / "test_001__bar.json"
        assert chart_file.exists()

        # Chart should be valid JSON
        with open(chart_file) as f:
            chart_config = json.load(f)
            assert chart_config["insight_id"] == "test_001"
            assert chart_config["visualization_type"] == "bar"

    def test_renderer_blocks_forbidden_colors(self, temp_workspace, visualization_plan_valid):
        """
        TEST: Renderer blocks charts with forbidden colors (greens).

        This is the ENFORCEMENT TEST - non-KDS colors should be rejected.
        """
        renderer = ChartRenderer(temp_workspace)

        # Render charts first (without validation)
        renderer.render_charts(validate=False)

        # Manually inject a forbidden color into the chart config
        chart_file = temp_workspace / "outputs" / "charts" / "test_001__bar.json"
        with open(chart_file) as f:
            chart_config = json.load(f)

        # Add forbidden green color to config
        chart_config["config"] = {
            "colors": ["#00FF00"],  # Forbidden green
            "gridLines": False,
        }

        with open(chart_file, "w") as f:
            json.dump(chart_config, f)

        # Now try to validate - should raise BrandComplianceError
        with pytest.raises(BrandComplianceError) as exc_info:
            renderer._validate_kds_compliance()

        # Check error message contains violation details
        error = exc_info.value
        assert "KDS COMPLIANCE FAILURE" in str(error)
        assert "violations" in error.details
        assert len(error.details["violations"]) > 0

        # Verify green color is mentioned in violations
        violations_str = " ".join(error.details["violations"])
        assert "#00FF00" in violations_str.upper() or "forbidden color" in violations_str.lower()

    def test_renderer_blocks_gridlines(self, temp_workspace, visualization_plan_valid):
        """
        TEST: Renderer blocks charts with gridlines.

        KDS guidelines prohibit gridlines for clean visual presentation.
        """
        renderer = ChartRenderer(temp_workspace)

        # Render charts first (without validation)
        renderer.render_charts(validate=False)

        # Manually inject gridlines into the chart config
        chart_file = temp_workspace / "outputs" / "charts" / "test_001__bar.json"
        with open(chart_file) as f:
            chart_config = json.load(f)

        # Enable gridlines (KDS violation)
        chart_config["config"] = {
            "gridLines": True,  # VIOLATION
            "colors": ["#7823DC"],  # KDS primary color (OK)
        }

        with open(chart_file, "w") as f:
            json.dump(chart_config, f)

        # Now try to validate - should raise BrandComplianceError
        with pytest.raises(BrandComplianceError) as exc_info:
            renderer._validate_kds_compliance()

        # Check error message mentions gridlines
        error = exc_info.value
        assert "KDS COMPLIANCE FAILURE" in str(error)
        violations_str = " ".join(error.details["violations"])
        assert "gridline" in violations_str.lower() or "grid" in violations_str.lower()

    def test_renderer_validation_can_be_disabled(
        self, temp_workspace, visualization_plan_valid
    ):
        """
        TEST: Validation can be disabled for testing/development.

        validate=False should skip KDS checks (use sparingly!).
        """
        renderer = ChartRenderer(temp_workspace)

        # Render with validation disabled
        result = renderer.render_charts(validate=False)

        # Should succeed even if charts would violate KDS
        assert result["success"] is True
        assert result["kds_validated"] is False

    def test_renderer_validates_multiple_charts(self, temp_workspace):
        """
        TEST: Renderer validates ALL charts in batch.

        If any chart violates KDS, entire batch should be rejected.
        """
        # Create visualization plan with multiple charts
        viz_plan = {
            "specifications": [
                {
                    "insight_id": f"test_{i:03d}",
                    "insight_title": f"Test Insight {i}",
                    "visualization_required": True,
                    "visualization_type": "bar",
                    "purpose": "comparison",
                    "x_axis": "category",
                    "y_axis": "revenue",
                    "highlights": [],
                    "suppress": [],
                    "annotations": [],
                    "caveats": [],
                    "confidence": {},
                }
                for i in range(1, 4)
            ]
        }

        viz_plan_path = temp_workspace / "outputs" / "visualization_plan.json"
        with open(viz_plan_path, "w") as f:
            json.dump(viz_plan, f)

        renderer = ChartRenderer(temp_workspace)

        # Render all charts
        result = renderer.render_charts(validate=True)

        # All charts should be validated
        assert result["success"] is True
        assert result["charts_rendered"] == 3
        assert result["kds_validated"] is True

        # All chart files should exist
        for i in range(1, 4):
            chart_file = (
                temp_workspace / "outputs" / "charts" / f"test_{i:03d}__bar.json"
            )
            assert chart_file.exists()

    def test_renderer_provides_detailed_error_messages(
        self, temp_workspace, visualization_plan_valid
    ):
        """
        TEST: Error messages are clear and actionable.

        Consultants should understand what's wrong and how to fix it.
        """
        renderer = ChartRenderer(temp_workspace)

        # Render charts first (without validation)
        renderer.render_charts(validate=False)

        # Inject multiple violations
        chart_file = temp_workspace / "outputs" / "charts" / "test_001__bar.json"
        with open(chart_file) as f:
            chart_config = json.load(f)

        # Multiple KDS violations
        chart_config["config"] = {
            "gridLines": True,  # Violation 1
            "colors": ["#00FF00", "#FF0000"],  # Violation 2 (green)
            "axisLine": True,  # Violation 3
        }

        with open(chart_file, "w") as f:
            json.dump(chart_config, f)

        # Validate and capture error
        with pytest.raises(BrandComplianceError) as exc_info:
            renderer._validate_kds_compliance()

        error_message = str(exc_info.value)

        # Error should be clear and structured
        assert "❌ KDS COMPLIANCE FAILURE" in error_message
        assert "Charts violate Kearney Design System guidelines" in error_message
        assert "Fix required before charts can be published" in error_message

        # Error details should include all violations
        assert "gridline" in error_message.lower() or "grid" in error_message.lower()

    def test_renderer_validation_preserves_chart_data(
        self, temp_workspace, visualization_plan_valid
    ):
        """
        TEST: Validation doesn't modify chart data.

        Validation is read-only - charts should remain unchanged.
        """
        renderer = ChartRenderer(temp_workspace)

        # Render charts
        result1 = renderer.render_charts(validate=True)

        # Read chart file
        chart_file = temp_workspace / "outputs" / "charts" / "test_001__bar.json"
        with open(chart_file) as f:
            chart_data_before = json.load(f)

        # Validate again
        renderer._validate_kds_compliance()

        # Read chart file again
        with open(chart_file) as f:
            chart_data_after = json.load(f)

        # Chart data should be identical
        assert chart_data_before == chart_data_after


@pytest.mark.integration
class TestRenderTimeValidationIntegration:
    """Integration tests with real KDS validator."""

    def test_kds_validator_integration(self, tmp_path):
        """
        TEST: ChartRenderer integrates correctly with BrandValidator.

        This verifies the validation pipeline works end-to-end.
        """
        from kie.brand.validator import BrandValidator

        project_root = tmp_path
        charts_dir = project_root / "outputs" / "charts"
        charts_dir.mkdir(parents=True)

        # Create a KDS-compliant chart config
        compliant_chart = {
            "type": "bar",
            "data": [{"category": "A", "value": 100}],
            "config": {
                "gridLines": False,
                "colors": ["#7823DC"],  # KDS primary
                "fontFamily": "Inter, Arial, sans-serif",
            },
        }

        chart_path = charts_dir / "test_chart.json"
        with open(chart_path, "w") as f:
            json.dump(compliant_chart, f)

        # Validate with BrandValidator
        validator = BrandValidator(strict=True)
        result = validator.validate_chart_config(chart_path)

        # Should pass
        assert result["compliant"] is True
        assert len(result["violations"]) == 0

    def test_validator_detects_real_violations(self, tmp_path):
        """
        TEST: BrandValidator actually catches KDS violations.

        Ensures our validator logic is working correctly.
        """
        from kie.brand.validator import BrandValidator

        project_root = tmp_path
        charts_dir = project_root / "outputs" / "charts"
        charts_dir.mkdir(parents=True)

        # Create a non-compliant chart config
        violating_chart = {
            "type": "bar",
            "data": [{"category": "A", "value": 100}],
            "config": {
                "gridLines": True,  # VIOLATION
                "colors": ["#00FF00"],  # VIOLATION (green)
            },
        }

        chart_path = charts_dir / "bad_chart.json"
        with open(chart_path, "w") as f:
            json.dump(violating_chart, f)

        # Validate with BrandValidator
        validator = BrandValidator(strict=False)  # Don't raise, just report
        result = validator.validate_chart_config(chart_path)

        # Should fail
        assert result["compliant"] is False
        assert len(result["violations"]) >= 2  # Gridlines + green color


# Run tests with: pytest tests/test_render_time_validation.py -v
