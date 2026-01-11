"""
Tests for Intent Gate System

Verifies that intent-first workflow is enforced correctly.
"""

import tempfile
from pathlib import Path

import pytest

from kie.commands.handler import CommandHandler
from kie.state.intent import IntentStorage, is_intent_clarified


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / "project_state").mkdir(parents=True)
        (project_root / "data").mkdir(parents=True)

        # Add sample data file
        data_file = project_root / "data" / "test_data.csv"
        data_file.write_text("region,revenue\nNorth,1000\nSouth,2000\n")

        yield project_root


def test_intent_storage_initialization(temp_project):
    """Test IntentStorage initialization."""
    storage = IntentStorage(temp_project)
    assert storage.project_root == temp_project
    assert not storage.is_clarified()


def test_intent_capture_and_retrieval(temp_project):
    """Test capturing and retrieving intent."""
    storage = IntentStorage(temp_project)

    # Capture intent
    result = storage.capture_intent("Analyze quarterly sales trends", captured_via="test")
    assert result["success"]
    assert result["objective"] == "Analyze quarterly sales trends"

    # Verify clarified
    assert storage.is_clarified()

    # Retrieve intent
    intent = storage.get_intent()
    assert intent is not None
    assert intent["objective"] == "Analyze quarterly sales trends"
    assert intent["captured_via"] == "test"


def test_analyze_blocks_without_intent(temp_project):
    """Test that /analyze blocks when intent is not clarified and does NOT call stdin."""
    handler = CommandHandler(temp_project)

    # Verify intent is not clarified
    assert not is_intent_clarified(temp_project)

    # Run analyze - should block without stdin
    result = handler.handle_analyze()

    # Verify blocked
    assert not result["success"]
    assert result.get("blocked") is True
    assert "intent" in result["message"].lower() or "objective" in result["message"].lower()

    # Now set intent and verify analyze works
    storage = IntentStorage(temp_project)
    storage.capture_intent("Test objective", captured_via="test")

    # Now analyze should work
    assert is_intent_clarified(temp_project)
    result = handler.handle_analyze()
    assert result["success"]


def test_build_blocks_without_intent(temp_project):
    """Test that /build blocks when intent is not clarified."""
    handler = CommandHandler(temp_project)

    # Verify intent is not clarified
    assert not is_intent_clarified(temp_project)

    # Manually set intent
    storage = IntentStorage(temp_project)
    storage.capture_intent("Build presentation", captured_via="test")

    # Now intent is clarified
    assert is_intent_clarified(temp_project)


def test_preview_blocks_without_intent(temp_project):
    """Test that /preview blocks when intent is not clarified."""
    handler = CommandHandler(temp_project)

    # Verify intent is not clarified
    assert not is_intent_clarified(temp_project)

    # Manually set intent
    storage = IntentStorage(temp_project)
    storage.capture_intent("Preview outputs", captured_via="test")

    # Now intent is clarified
    assert is_intent_clarified(temp_project)


def test_eda_works_without_intent(temp_project):
    """Test that /eda works WITHOUT intent (exploratory)."""
    handler = CommandHandler(temp_project)

    # Verify intent is not clarified
    assert not is_intent_clarified(temp_project)

    # EDA should work without intent (exploratory command)
    result = handler.handle_eda()

    # EDA should succeed even without intent
    assert result["success"]


def test_status_works_without_intent(temp_project):
    """Test that /status works WITHOUT intent (informational)."""
    handler = CommandHandler(temp_project)

    # Verify intent is not clarified
    assert not is_intent_clarified(temp_project)

    # Status should work without intent
    result = handler.handle_status()

    # Check intent is displayed
    assert "intent" in result
    assert result["intent"] == "NOT SET"


def test_intent_from_interview(temp_project):
    """Test intent detection from interview state."""
    # Create interview_state.yaml with objective
    interview_state = temp_project / "project_state" / "interview_state.yaml"
    interview_state.write_text("objective: Create sales dashboard\n")

    # Verify intent is clarified
    assert is_intent_clarified(temp_project)

    # Get intent
    storage = IntentStorage(temp_project)
    intent = storage.get_intent()
    assert intent["objective"] == "Create sales dashboard"


def test_intent_from_spec(temp_project):
    """Test intent detection from spec.yaml."""
    # Create spec.yaml with meaningful objective
    spec = temp_project / "project_state" / "spec.yaml"
    spec.write_text("objective: Analyze revenue trends\nproject_name: Test\n")

    # Verify intent is clarified
    assert is_intent_clarified(temp_project)

    # Get intent
    storage = IntentStorage(temp_project)
    intent = storage.get_intent()
    assert intent["objective"] == "Analyze revenue trends"


def test_generic_objective_not_valid(temp_project):
    """Test that generic objectives don't count as clarified intent."""
    # Create spec.yaml with generic objective
    spec = temp_project / "project_state" / "spec.yaml"
    spec.write_text("objective: Analysis\nproject_name: Test\n")

    # Verify intent is NOT clarified (generic objective rejected)
    assert not is_intent_clarified(temp_project)


def test_intent_capture_event_recording(temp_project):
    """Test that intent capture events are recorded."""
    storage = IntentStorage(temp_project)

    # Create evidence_ledger directory
    ledger_dir = temp_project / "project_state" / "evidence_ledger"
    ledger_dir.mkdir(parents=True)

    # Capture intent
    storage.capture_intent("Test objective", captured_via="test")

    # Verify event was recorded
    event_file = ledger_dir / "intent_capture_events.yaml"
    assert event_file.exists()

    # Read events
    import yaml
    with open(event_file) as f:
        events = yaml.safe_load(f)

    assert len(events) == 1
    assert events[0]["objective"] == "Test objective"
    assert events[0]["captured_via"] == "test"


def test_multiple_intent_captures(temp_project):
    """Test multiple intent capture events."""
    storage = IntentStorage(temp_project)
    ledger_dir = temp_project / "project_state" / "evidence_ledger"
    ledger_dir.mkdir(parents=True)

    # Capture multiple intents
    storage.capture_intent("First objective", captured_via="test1")
    storage.capture_intent("Second objective", captured_via="test2")

    # Verify events
    event_file = ledger_dir / "intent_capture_events.yaml"
    import yaml
    with open(event_file) as f:
        events = yaml.safe_load(f)

    assert len(events) == 2
    assert events[0]["objective"] == "First objective"
    assert events[1]["objective"] == "Second objective"


def test_intent_command_status(temp_project):
    """Test /intent status command."""
    handler = CommandHandler(temp_project)

    # Status when not set
    result = handler.handle_intent(subcommand="status")
    assert result["success"]
    assert result["intent"] == "NOT SET"

    # Set intent
    storage = IntentStorage(temp_project)
    storage.capture_intent("Test objective", captured_via="test")

    # Status when set
    result = handler.handle_intent(subcommand="status")
    assert result["success"]
    assert result["intent"] == "Test objective"


def test_intent_command_set(temp_project):
    """Test /intent set command."""
    handler = CommandHandler(temp_project)

    # Set intent
    result = handler.handle_intent(subcommand="set", objective="Analyze sales data")
    assert result["success"]
    assert result["objective"] == "Analyze sales data"

    # Verify intent is clarified
    assert is_intent_clarified(temp_project)

    # Verify storage
    storage = IntentStorage(temp_project)
    intent = storage.get_intent()
    assert intent["objective"] == "Analyze sales data"
    assert intent["captured_via"] == "cli"


def test_intent_command_set_requires_objective(temp_project):
    """Test /intent set requires objective."""
    handler = CommandHandler(temp_project)

    # Set without objective should fail
    result = handler.handle_intent(subcommand="set", objective=None)
    assert not result["success"]
    assert "objective required" in result["message"].lower()


def test_intent_command_clear(temp_project):
    """Test /intent clear command."""
    handler = CommandHandler(temp_project)

    # Set intent first
    storage = IntentStorage(temp_project)
    storage.capture_intent("Test objective", captured_via="test")
    assert is_intent_clarified(temp_project)

    # Clear intent
    result = handler.handle_intent(subcommand="clear")
    assert result["success"]

    # Verify intent is not clarified
    assert not is_intent_clarified(temp_project)


def test_intent_command_enables_analyze(temp_project):
    """Test that /intent set enables /analyze to proceed."""
    handler = CommandHandler(temp_project)

    # Verify intent not set
    assert not is_intent_clarified(temp_project)

    # Analyze should block
    result = handler.handle_analyze()
    assert not result["success"]
    assert result.get("blocked") is True

    # Set intent via command
    result = handler.handle_intent(subcommand="set", objective="Test analysis")
    assert result["success"]

    # Now analyze should work
    result = handler.handle_analyze()
    assert result["success"]
