"""
Test type-specific interview question routing (Phase 1).

Verifies:
- Dashboard and presentation are the only supported types
- Unsupported types trigger redirects with audit trail
- Type-specific questions appear in correct sequence
- Theme enforcement is non-bypassable
- Type-specific answers stored in spec.context
"""

import pytest
from pathlib import Path
from kie.interview.engine import InterviewEngine
from kie.interview.schema import ProjectType
import tempfile
import shutil


@pytest.fixture
def temp_interview():
    """Create temporary interview engine for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    state_path = temp_dir / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)
    yield engine
    shutil.rmtree(temp_dir)


class TestSupportedTypes:
    """Test that only dashboard and presentation are supported."""

    def test_dashboard_is_supported(self, temp_interview):
        """Dashboard should be accepted as valid project type."""
        temp_interview.process_message("express")
        response = temp_interview.process_message("dashboard")

        assert temp_interview.state.has_project_type
        assert temp_interview.state.spec.project_type == ProjectType.DASHBOARD
        assert temp_interview.state.spec.context is None or "attempted_project_type" not in temp_interview.state.spec.context

    def test_presentation_is_supported(self, temp_interview):
        """Presentation should be accepted as valid project type."""
        temp_interview.process_message("express")
        response = temp_interview.process_message("presentation")

        assert temp_interview.state.has_project_type
        assert temp_interview.state.spec.project_type == ProjectType.PRESENTATION
        assert temp_interview.state.spec.context is None or "attempted_project_type" not in temp_interview.state.spec.context

    def test_analytics_is_unsupported(self, temp_interview):
        """Analytics should trigger redirect with audit trail."""
        temp_interview.process_message("express")
        response = temp_interview.process_message("analytics")

        assert not temp_interview.state.has_project_type
        assert temp_interview.state.spec.context is not None
        assert temp_interview.state.spec.context.get("attempted_project_type") == "analytics"
        assert "attempted_unsupported_type" in response["slots_filled"]

    def test_modeling_is_unsupported(self, temp_interview):
        """Modeling should trigger redirect."""
        temp_interview.process_message("express")
        response = temp_interview.process_message("modeling")

        assert not temp_interview.state.has_project_type
        assert temp_interview.state.spec.context.get("attempted_project_type") == "modeling"

    def test_proposal_is_unsupported(self, temp_interview):
        """Proposal should trigger redirect."""
        temp_interview.process_message("express")
        response = temp_interview.process_message("proposal")

        assert not temp_interview.state.has_project_type
        assert temp_interview.state.spec.context.get("attempted_project_type") == "proposal"

    def test_unsupported_type_shows_redirect_message(self, temp_interview):
        """Unsupported types should show redirect message in acknowledgments."""
        temp_interview.process_message("express")
        response = temp_interview.process_message("analytics")

        acks = response.get("acknowledgment", [])
        redirect_ack = [a for a in acks if "⚠️" in a]
        assert len(redirect_ack) > 0
        assert "dashboard" in redirect_ack[0].lower() or "presentation" in redirect_ack[0].lower()


class TestQuestionSequencing:
    """Test that type-specific questions appear in correct order."""

    def test_dashboard_express_sequence(self, temp_interview):
        """Dashboard express should ask dashboard_views and dashboard_filters."""
        # Start interview
        temp_interview.process_message("express")
        temp_interview.process_message("dashboard")

        # Check active sequence
        assert len(temp_interview.state.active_question_sequence) > 0
        assert "dashboard_views" in temp_interview.state.active_question_sequence
        assert "dashboard_filters" in temp_interview.state.active_question_sequence
        assert temp_interview.state.active_question_sequence.index("dashboard_views") < \
               temp_interview.state.active_question_sequence.index("theme")

    def test_presentation_express_sequence(self, temp_interview):
        """Presentation express should ask slide_count and key_message."""
        temp_interview.process_message("express")
        temp_interview.process_message("presentation")

        assert "slide_count" in temp_interview.state.active_question_sequence
        assert "key_message" in temp_interview.state.active_question_sequence
        assert temp_interview.state.active_question_sequence.index("slide_count") < \
               temp_interview.state.active_question_sequence.index("theme")

    def test_dashboard_full_adds_update_frequency(self, temp_interview):
        """Dashboard full mode should add update_frequency question."""
        temp_interview.process_message("full")
        temp_interview.process_message("dashboard")

        assert "update_frequency" in temp_interview.state.active_question_sequence
        # Should come before theme
        assert temp_interview.state.active_question_sequence.index("update_frequency") < \
               temp_interview.state.active_question_sequence.index("theme")

    def test_presentation_full_adds_style(self, temp_interview):
        """Presentation full mode should add presentation_style question."""
        temp_interview.process_message("full")
        temp_interview.process_message("presentation")

        assert "presentation_style" in temp_interview.state.active_question_sequence
        assert temp_interview.state.active_question_sequence.index("presentation_style") < \
               temp_interview.state.active_question_sequence.index("theme")

    def test_question_index_advances(self, temp_interview):
        """Question index should advance as questions are answered."""
        temp_interview.process_message("express")
        temp_interview.process_message("dashboard")

        initial_index = temp_interview.state.current_question_index

        temp_interview.process_message("Analyze Q3 sales performance")  # objective

        assert temp_interview.state.current_question_index > initial_index


class TestTypeSpecificStorage:
    """Test that type-specific answers are stored in spec.context."""

    def test_dashboard_views_stored_in_context(self, temp_interview):
        """Dashboard views answer should be stored in spec.context."""
        temp_interview.process_message("express")
        temp_interview.process_message("dashboard")
        temp_interview.process_message("Track Q3 performance metrics")  # objective - avoid "analysis"
        temp_interview.process_message("sales_data.csv")  # data

        # Answer dashboard_views question
        response = temp_interview.process_message("3 views: overview, regional detail, product comparison")

        assert temp_interview.state.spec.context is not None
        assert "dashboard_views" in temp_interview.state.spec.context
        assert "3 views" in temp_interview.state.spec.context["dashboard_views"]

    def test_dashboard_filters_stored_in_context(self, temp_interview):
        """Dashboard filters answer should be stored in spec.context."""
        temp_interview.process_message("express")
        temp_interview.process_message("dashboard")
        temp_interview.process_message("Improve Q3 decision-making")  # objective
        temp_interview.process_message("sales_data.csv")  # data
        temp_interview.process_message("3 tabs showing overview, detail, comparison")  # dashboard_views

        response = temp_interview.process_message("Date range picker, region dropdown, product line filter")  # dashboard_filters

        assert temp_interview.state.spec.context is not None
        assert "dashboard_filters" in temp_interview.state.spec.context
        assert "Date range" in temp_interview.state.spec.context["dashboard_filters"]

    def test_slide_count_stored_in_context(self, temp_interview):
        """Slide count answer should be stored in spec.context."""
        temp_interview.process_message("express")
        temp_interview.process_message("presentation")
        temp_interview.process_message("Executive summary of Q3")
        temp_interview.process_message("quarterly_results.xlsx")

        response = temp_interview.process_message("10 slides")

        assert "slide_count" in temp_interview.state.spec.context
        assert "10" in temp_interview.state.spec.context["slide_count"]

    def test_key_message_stored_in_context(self, temp_interview):
        """Key message answer should be stored in spec.context."""
        temp_interview.process_message("express")
        temp_interview.process_message("presentation")
        temp_interview.process_message("Executive summary deck")
        temp_interview.process_message("results.xlsx")
        temp_interview.process_message("10 slides")

        response = temp_interview.process_message("Revenue up 15% YoY, recommend expanding in APAC")

        assert temp_interview.state.spec.context is not None
        assert "key_message" in temp_interview.state.spec.context
        assert "Revenue up 15%" in temp_interview.state.spec.context["key_message"]

    def test_no_schema_explosion(self, temp_interview):
        """Verify no new has_* boolean fields were added for type-specific questions."""
        # Check that these attributes DON'T exist
        assert not hasattr(temp_interview.state, "has_dashboard_views")
        assert not hasattr(temp_interview.state, "has_dashboard_filters")
        assert not hasattr(temp_interview.state, "has_slide_count")
        assert not hasattr(temp_interview.state, "has_key_message")


class TestThemeEnforcement:
    """Test that theme preference cannot be bypassed."""

    def test_theme_required_for_completion_dashboard(self, temp_interview):
        """Dashboard interview cannot complete without theme selection."""
        temp_interview.process_message("express")
        temp_interview.process_message("dashboard")
        temp_interview.process_message("Sales analysis")
        temp_interview.process_message("data.csv")
        temp_interview.process_message("3 views")
        temp_interview.process_message("Date range filter")
        # Skip theme, go to project name
        temp_interview.process_message("Q3 Sales Dashboard")

        # Should NOT be complete
        assert not temp_interview.state.is_complete()
        assert not temp_interview.state.has_theme_preference

    def test_theme_required_for_completion_presentation(self, temp_interview):
        """Presentation interview cannot complete without theme selection."""
        temp_interview.process_message("express")
        temp_interview.process_message("presentation")
        temp_interview.process_message("Executive summary")
        temp_interview.process_message("results.xlsx")
        temp_interview.process_message("10 slides")
        temp_interview.process_message("Revenue growth recommendation")
        temp_interview.process_message("Q3 Executive Summary")

        assert not temp_interview.state.is_complete()
        assert not temp_interview.state.has_theme_preference

    def test_dual_completion_check(self, temp_interview):
        """Verify both sequence AND required fields checked for completion."""
        temp_interview.process_message("express")
        temp_interview.process_message("dashboard")
        temp_interview.process_message("Track performance metrics")  # avoid "analysis"
        temp_interview.process_message("data.csv")
        temp_interview.process_message("3 views")
        temp_interview.process_message("Date filters")
        temp_interview.process_message("dark")  # theme
        temp_interview.process_message("Sales Dashboard")

        # Now should be complete (both sequence finished AND theme set)
        assert temp_interview.state.is_complete()
        assert temp_interview.state.has_theme_preference
        assert temp_interview.state.current_question_index >= len(temp_interview.state.active_question_sequence)


class TestAuditTrail:
    """Test that unsupported type attempts are preserved."""

    def test_attempted_type_preserved(self, temp_interview):
        """Attempted unsupported type should be recorded, not deleted."""
        temp_interview.process_message("express")
        temp_interview.process_message("analytics")

        # Should be in context
        assert temp_interview.state.spec.context.get("attempted_project_type") == "analytics"

        # Try again with supported type
        temp_interview.process_message("dashboard")

        # Audit trail should still exist
        assert temp_interview.state.spec.context.get("attempted_project_type") == "analytics"
        # But now has_project_type should be True
        assert temp_interview.state.has_project_type
        assert temp_interview.state.spec.project_type == ProjectType.DASHBOARD


class TestBackwardCompatibility:
    """Test that system works without active_question_sequence (legacy)."""

    def test_legacy_completion_without_sequence(self, temp_interview):
        """Should fall back to required fields check if no sequence active."""
        # Manually set fields without using sequence
        temp_interview.state.interview_mode = "express"
        temp_interview.state.has_project_name = True
        temp_interview.state.has_project_type = True
        temp_interview.state.has_objective = True
        temp_interview.state.has_data_source = True
        temp_interview.state.has_deliverables = True
        temp_interview.state.has_theme_preference = True
        # No active_question_sequence

        assert temp_interview.state.is_complete()
