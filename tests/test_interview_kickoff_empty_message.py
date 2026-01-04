"""
Test interview engine handles empty messages safely (kickoff scenario).

Regression tests for:
- process_message("") should not crash
- Should return valid response with next_question
- Should not corrupt state
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from kie.interview.engine import InterviewEngine


class TestInterviewEmptyMessageKickoff:
    """Test empty message handling for fresh interview kickoff."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test state."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_process_message_empty_string_no_crash(self, temp_dir):
        """Regression: process_message("") should not crash on fresh state."""
        state_path = temp_dir / "interview_state.yaml"
        engine = InterviewEngine(state_path=state_path)

        # This used to crash with IndexError: string index out of range
        response = engine.process_message("")

        # Should return valid response
        assert isinstance(response, dict)
        assert "next_question" in response
        assert "complete" in response
        assert "slots_filled" in response
        assert "acknowledgment" in response

    def test_empty_message_returns_first_question(self, temp_dir):
        """Empty message on fresh state should return interview mode question."""
        state_path = temp_dir / "interview_state.yaml"
        engine = InterviewEngine(state_path=state_path)

        response = engine.process_message("")

        # Should return first question (mode selection)
        assert response["next_question"] is not None
        assert len(response["next_question"]) > 0
        assert "express" in response["next_question"].lower() or "mode" in response["next_question"].lower()

    def test_empty_message_does_not_advance_state(self, temp_dir):
        """Empty message should not corrupt or advance interview state."""
        state_path = temp_dir / "interview_state.yaml"
        engine = InterviewEngine(state_path=state_path)

        # Get initial state
        initial_index = engine.state.current_question_index
        initial_slots = list(engine.state.slots_filled)

        # Process empty message
        response = engine.process_message("")

        # State should not advance unexpectedly
        assert engine.state.current_question_index == initial_index
        assert list(engine.state.slots_filled) == initial_slots
        assert response["slots_filled"] == []
        assert response["complete"] is False

    def test_whitespace_message_no_crash(self, temp_dir):
        """Whitespace-only messages should also be safe."""
        state_path = temp_dir / "interview_state.yaml"
        engine = InterviewEngine(state_path=state_path)

        # Test various whitespace patterns
        for message in ["   ", "\n", "\t", " \n \t "]:
            response = engine.process_message(message)
            assert response["next_question"] is not None
            assert response["complete"] is False

    def test_normal_message_still_works(self, temp_dir):
        """Normal messages should continue to work as before."""
        state_path = temp_dir / "interview_state.yaml"
        engine = InterviewEngine(state_path=state_path)

        # First get the mode question
        response = engine.process_message("")
        assert "mode" in response["next_question"].lower() or "express" in response["next_question"].lower()

        # Answer with "dashboard" - should extract project_type
        response = engine.process_message("dashboard")

        # Should have captured something and advanced
        assert len(response["slots_filled"]) > 0 or len(response["acknowledgment"]) > 0
        assert response["next_question"] is not None

    def test_empty_message_after_some_answers(self, temp_dir):
        """Empty message mid-interview should return next question without corruption."""
        state_path = temp_dir / "interview_state.yaml"
        engine = InterviewEngine(state_path=state_path)

        # Answer a few questions
        engine.process_message("express")
        engine.process_message("dashboard")

        # Now send empty message
        response = engine.process_message("")

        # Should return next question without issues
        assert response["next_question"] is not None
        assert response["complete"] is False
        assert response["slots_filled"] == []
