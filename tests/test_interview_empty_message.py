"""
Test interview engine handles empty/whitespace messages safely.

Regression test for IndexError crash when process_message("") is called
during interview kickoff in fresh workspaces.
"""

import pytest
from pathlib import Path
from kie.interview.engine import InterviewEngine
from kie.interview.schema import ProjectType


def test_process_empty_message_does_not_crash(tmp_path):
    """Test that process_message("") does not crash with IndexError."""
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # This should NOT crash
    response = engine.process_message("")

    # Should return a valid response dict
    assert isinstance(response, dict)
    assert "next_question" in response
    assert "complete" in response
    assert "acknowledgment" in response
    assert "slots_filled" in response


def test_empty_message_returns_first_question(tmp_path):
    """Test that empty message returns the correct first question for fresh state."""
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    response = engine.process_message("")

    # Should get interview mode question first
    assert response["next_question"] is not None
    assert len(response["next_question"]) > 0
    assert "mode" in response["next_question"].lower() or "express" in response["next_question"].lower()

    # Should not be complete
    assert response["complete"] is False

    # Should not have filled any slots
    assert len(response["slots_filled"]) == 0


def test_empty_message_does_not_advance_state_incorrectly(tmp_path):
    """Test that empty message does not advance question index unexpectedly."""
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # Get initial state
    initial_index = engine.state.current_question_index
    initial_slots = len(engine.state.slots_filled)

    # Process empty message
    response = engine.process_message("")

    # State should not have advanced incorrectly
    assert engine.state.current_question_index == initial_index
    assert len(engine.state.slots_filled) == initial_slots

    # Should still get a next question
    assert response["next_question"] is not None


def test_whitespace_only_message_is_safe(tmp_path):
    """Test that whitespace-only messages are handled safely."""
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # Various whitespace inputs
    whitespace_inputs = ["   ", "\t", "\n", "  \t\n  "]

    for ws_input in whitespace_inputs:
        response = engine.process_message(ws_input)

        # Should not crash and should return valid response
        assert isinstance(response, dict)
        assert "next_question" in response
        assert response["next_question"] is not None


def test_normal_message_still_works_after_empty(tmp_path):
    """Test that processing normal messages still works correctly after empty message."""
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # Start with empty message
    response1 = engine.process_message("")
    assert response1["next_question"] is not None

    # Answer with express mode
    response2 = engine.process_message("express")
    assert "interview_mode" in response2["slots_filled"] or "express" in str(response2["acknowledgment"])

    # Should still get next question
    assert response2["next_question"] is not None


def test_empty_message_with_existing_state(tmp_path):
    """Test that empty message works correctly when resuming from existing state."""
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # Set up some state
    engine.process_message("express")
    engine.process_message("dashboard")

    # Save and reload
    engine.save_state()
    engine2 = InterviewEngine(state_path=state_path)

    # Empty message should return next question without corrupting state
    response = engine2.process_message("")

    assert response["next_question"] is not None
    assert engine2.state.interview_mode == "express"
    assert engine2.state.has_project_type is True


def test_extract_information_hardened_against_empty_message(tmp_path):
    """Test that _extract_information doesn't crash on edge cases."""
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # These should not crash _extract_information if it's called
    edge_cases = ["", " ", "a", "1"]

    for edge_case in edge_cases:
        extracted = engine._extract_information(edge_case)
        assert isinstance(extracted, dict)
