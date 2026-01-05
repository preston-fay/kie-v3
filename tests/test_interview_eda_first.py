"""
Tests for EDA-first pause functionality in interview engine.

When a user reaches deliverable selection and wants to explore data first,
the interview should pause cleanly, save state, and allow resumption after EDA.
"""

import pytest
from pathlib import Path
from kie.interview.engine import InterviewEngine


def test_eda_first_pause_at_deliverable_selection(tmp_path):
    """
    Test that responding 'EDA first' at deliverable selection pauses the interview.
    """
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # Start interview - choose express mode
    r1 = engine.process_message("express")
    assert "interview_mode" in r1["slots_filled"] or "express" in str(r1.get("acknowledgment", []))

    # At deliverable selection, respond with "EDA first"
    r2 = engine.process_message("EDA first")

    # Should NOT set project_type
    assert not engine.state.has_project_type

    # Should NOT be complete
    assert r2["complete"] is False

    # Should have paused message telling user to run /eda
    assert "/eda" in r2["next_question"]
    assert "resume" in r2["next_question"].lower() or "again" in r2["next_question"].lower()

    # Should have stored intent in context
    assert engine.state.spec.context is not None
    assert engine.state.spec.context.get("intent") == "eda_first"
    assert "EDA first" in engine.state.spec.context.get("intent_note", "")

    # State file should exist (interview is resumable)
    assert state_path.exists()


def test_eda_first_various_phrases(tmp_path):
    """
    Test that various EDA-first phrases are recognized.
    """
    eda_phrases = [
        "eda",
        "eda first",
        "start with eda",
        "not sure",
        "not sure yet",
        "decide later",
        "explore first"
    ]

    for phrase in eda_phrases:
        state_path = tmp_path / f"state_{phrase.replace(' ', '_')}.yaml"
        engine = InterviewEngine(state_path=state_path)

        # Get to deliverable selection
        engine.process_message("express")

        # Try the phrase
        response = engine.process_message(phrase)

        # Should pause, not set project_type
        assert not engine.state.has_project_type, f"Failed for phrase: {phrase}"
        assert response["complete"] is False
        assert "/eda" in response["next_question"]


def test_resume_after_eda_first_pause(tmp_path):
    """
    Test that after EDA-first pause, answering 'dashboard' correctly resumes.
    """
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # Start and pause at deliverable selection
    engine.process_message("express")
    r_pause = engine.process_message("not sure yet")

    # Verify paused
    assert not engine.state.has_project_type
    assert r_pause["complete"] is False

    # Simulate user running /eda (they would do this manually)
    # Then resume interview by answering "dashboard"
    engine2 = InterviewEngine(state_path=state_path)  # Reload from disk
    r_resume = engine2.process_message("dashboard")

    # Should now set project_type
    assert engine2.state.has_project_type
    assert engine2.state.spec.project_type.value == "dashboard"

    # Should continue to next question (not complete yet)
    assert r_resume["complete"] is False
    assert r_resume["next_question"] is not None


def test_eda_first_does_not_delete_state(tmp_path):
    """
    Verify that EDA-first pause does NOT delete interview_state.yaml.
    """
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # Get to deliverable selection and pause
    engine.process_message("express")
    engine.process_message("explore first")

    # State file must still exist
    assert state_path.exists()

    # State should be loadable
    engine_reload = InterviewEngine(state_path=state_path)
    assert engine_reload.state.interview_mode == "express"
    assert not engine_reload.state.has_project_type


def test_normal_deliverable_selection_still_works(tmp_path):
    """
    Test that normal 'dashboard' or 'presentation' answers still work correctly.
    """
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    # Normal flow: express -> dashboard
    engine.process_message("express")
    r2 = engine.process_message("dashboard")

    # Should set project_type normally (not trigger EDA-first)
    assert engine.state.has_project_type
    assert engine.state.spec.project_type.value == "dashboard"
    assert r2["complete"] is False
    assert r2["next_question"] is not None

    # Should NOT have eda_first intent
    intent = engine.state.spec.context.get("intent") if engine.state.spec.context else None
    assert intent != "eda_first"


def test_eda_first_acknowledgment_and_message(tmp_path):
    """
    Test that EDA-first response includes proper acknowledgment and message.
    """
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    engine.process_message("express")
    response = engine.process_message("eda first")

    # Should have acknowledgment
    assert len(response.get("acknowledgment", [])) > 0
    assert any("eda" in str(ack).lower() for ack in response["acknowledgment"])

    # Should have message key
    assert "message" in response
    assert "pause" in response["message"].lower() or "resume" in response["message"].lower()


def test_eda_phrase_in_middle_of_sentence_works(tmp_path):
    """
    Test that EDA-first detection works even if phrase is in middle of sentence.
    """
    state_path = tmp_path / "interview_state.yaml"
    engine = InterviewEngine(state_path=state_path)

    engine.process_message("express")
    response = engine.process_message("I want to start with eda and see what the data looks like")

    # Should detect "start with eda" in the sentence
    assert not engine.state.has_project_type
    assert response["complete"] is False
    assert "/eda" in response["next_question"]
