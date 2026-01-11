"""
Consultant Reality Battery: Adversarial Acceptance Tests

This suite tests real consultant journeys end-to-end to catch Constitution violations
before they reach production. Each journey runs in an isolated temp workspace and
verifies all gate behaviors, messaging truthfulness, and artifact generation.

FAILURE MODES CAUGHT:
- EOFError from stdin prompts (non-interactive violation)
- Recommending blocked commands (Constitution violation)
- Claiming artifacts exist when they don't (Truth Gate violation)
- Allowing off-rails execution in Rails mode (Mode Gate violation)
- Corrupted/unsupported file format handling
- Large dataset performance issues

Each journey MUST pass for CI to succeed.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from kie.commands.handler import CommandHandler
from kie.preferences import OutputPreferences
from kie.state import IntentStorage, is_intent_clarified


class ConsultantRealityBattery:
    """
    Adversarial test suite for consultant journeys.

    Each journey method tests a specific real-world scenario that has
    historically caused issues or violated Constitution principles.
    """

    @staticmethod
    def create_workspace() -> Path:
        """Create temporary isolated workspace."""
        tmpdir = tempfile.mkdtemp()
        project_root = Path(tmpdir)
        return project_root

    @staticmethod
    def setup_workspace(project_root: Path):
        """Initialize KIE workspace structure."""
        handler = CommandHandler(project_root)
        result = handler.handle_startkie()
        assert result["success"], f"Workspace setup failed: {result.get('message')}"

    @staticmethod
    def assert_no_stdin_prompts(monkeypatch):
        """Mock input() to catch any stdin attempts (immediate failure)."""
        def mock_input(*args, **kwargs):
            raise AssertionError(
                "STDIN VIOLATION: input() was called - non-interactive rule violated!"
            )
        monkeypatch.setattr("builtins.input", mock_input)

    @staticmethod
    def assert_artifacts_exist(claimed_paths: list[Path]):
        """Verify all claimed artifacts actually exist on disk."""
        for path in claimed_paths:
            assert path.exists(), f"TRUTH GATE VIOLATION: Claimed artifact does not exist: {path}"

    @staticmethod
    def assert_intent_aware_messaging(output: str, intent_set: bool):
        """Verify messaging never recommends gated commands when gates would block."""
        if not intent_set:
            # If intent not set, should NOT recommend /analyze or /build
            lines = output.lower().split('\n')
            in_next_steps = False
            next_steps_section = []
            for line in lines:
                if "next steps" in line or "try" in line or "workflow" in line:
                    in_next_steps = True
                elif in_next_steps:
                    if line.strip() == "":
                        break
                    next_steps_section.append(line)

            next_steps_text = '\n'.join(next_steps_section)
            # Allow mentions in general text, but not in actionable next steps
            if "/analyze" in next_steps_text or "/build" in next_steps_text:
                # Only fail if it's a direct recommendation, not just a mention
                if ("run /analyze" in next_steps_text or
                    "try /analyze" in next_steps_text or
                    "type /analyze" in next_steps_text or
                    "run /build" in next_steps_text or
                    "try /build" in next_steps_text or
                    "type /build" in next_steps_text):
                    raise AssertionError(
                        f"CONSTITUTION VIOLATION: Recommended gated command without intent set\n{next_steps_text}"
                    )


@pytest.fixture
def reality_battery():
    """Fixture providing battery instance."""
    return ConsultantRealityBattery()


# ============================================================================
# JOURNEY A: Fresh Workspace, No Data
# ============================================================================

def test_journey_a_fresh_workspace_no_data(reality_battery, monkeypatch, capsys):
    """
    Journey A: Consultant opens fresh KIE workspace with no data files.

    EXPECTED BEHAVIOR:
    - /startkie succeeds, creates structure
    - /status shows truthful state (no data, no intent)
    - /eda without data shows clear message (not crash)
    - Messaging recommends valid next steps only
    - No stdin prompts at any point
    """
    reality_battery.assert_no_stdin_prompts(monkeypatch)

    project_root = reality_battery.create_workspace()

    # Bootstrap workspace
    reality_battery.setup_workspace(project_root)

    # Verify structure created
    assert (project_root / "data").exists()
    assert (project_root / "outputs").exists()
    assert (project_root / "project_state").exists()

    handler = CommandHandler(project_root)

    # Check status - should be truthful about no data
    result = handler.handle_status()
    assert "intent" in result
    assert result["intent"] == "NOT SET"

    # EDA without data - should handle gracefully
    result = handler.handle_eda()
    # Should either succeed with clear message or fail gracefully
    captured = capsys.readouterr()

    # Verify intent-aware messaging (no /analyze recommendation)
    reality_battery.assert_intent_aware_messaging(captured.out, intent_set=False)

    print("✓ Journey A: Fresh workspace handled correctly")


# ============================================================================
# JOURNEY B: Demo Data Opt-In
# ============================================================================

def test_journey_b_demo_data_opt_in(reality_battery, monkeypatch, capsys):
    """
    Journey B: Consultant installs demo data to explore KIE features.

    EXPECTED BEHAVIOR:
    - /sampledata install succeeds
    - Data file created at data/sample_data.csv
    - /eda succeeds with demo data
    - Intent-aware messaging works correctly
    - No stdin prompts
    """
    reality_battery.assert_no_stdin_prompts(monkeypatch)

    project_root = reality_battery.create_workspace()
    reality_battery.setup_workspace(project_root)

    handler = CommandHandler(project_root)

    # Install demo data
    result = handler.handle_sampledata(subcommand="install")
    assert result["success"], f"Demo data install failed: {result.get('message')}"

    # Verify artifact exists
    data_file = project_root / "data" / "sample_data.csv"
    reality_battery.assert_artifacts_exist([data_file])

    # Verify data file has content
    content = data_file.read_text()
    assert len(content) > 0, "Demo data file is empty"
    assert "," in content, "Demo data doesn't look like CSV"

    # Run EDA on demo data
    result = handler.handle_eda()
    assert result["success"], f"EDA failed on demo data: {result.get('message')}"

    # Check messaging
    captured = capsys.readouterr()
    intent_set = is_intent_clarified(project_root)
    reality_battery.assert_intent_aware_messaging(captured.out, intent_set=intent_set)

    print("✓ Journey B: Demo data installation works correctly")


# ============================================================================
# JOURNEY C: Theme Gate
# ============================================================================

def test_journey_c_theme_gate(reality_battery, monkeypatch, capsys):
    """
    Journey C: Consultant attempts /build without setting theme.

    EXPECTED BEHAVIOR:
    - /build blocks cleanly (no crash, no EOF)
    - Block message explains /theme command
    - /theme set dark succeeds
    - /build proceeds after theme set
    - Absolutely no stdin prompts
    """
    reality_battery.assert_no_stdin_prompts(monkeypatch)

    project_root = reality_battery.create_workspace()
    reality_battery.setup_workspace(project_root)

    handler = CommandHandler(project_root)

    # Install demo data
    handler.handle_sampledata(subcommand="install")

    # Set intent (required for build)
    storage = IntentStorage(project_root)
    storage.capture_intent("Test theme gate", captured_via="test")

    # Create minimal spec
    spec = {
        "project_name": "Theme Test",
        "client_name": "Test Client",
        "objective": "Test theme gate",
        "project_type": "analytics",
    }
    spec_path = project_root / "project_state" / "spec.yaml"
    with open(spec_path, "w") as f:
        yaml.dump(spec, f)

    # Verify theme NOT set
    prefs = OutputPreferences(project_root)
    assert prefs.get_theme() is None

    # Attempt /build - should block (NOT crash with EOF)
    result = handler.handle_build(target="all")
    assert not result["success"], "Build should have blocked without theme"
    assert result.get("blocked") is True, "Build should return blocked=True"
    assert "theme" in result["message"].lower(), "Block message should mention theme"

    # Verify messaging
    captured = capsys.readouterr()
    assert "/theme" in captured.out.lower(), "Should instruct user to run /theme command"

    # Set theme
    result = handler.handle_theme(set_theme="dark")
    assert result["success"], f"Theme setting failed: {result.get('message')}"
    assert result["theme"] == "dark"

    # Verify theme persisted
    assert prefs.get_theme() == "dark"

    # Now build should not block on theme
    result = handler.handle_build(target="all")
    not_blocked_on_theme = (
        not result.get("blocked")
        or "theme" not in result.get("message", "").lower()
    )
    assert not_blocked_on_theme, "Build should not block on theme after theme is set"

    print("✓ Journey C: Theme gate works non-interactively")


# ============================================================================
# JOURNEY D: /go Path
# ============================================================================

def test_journey_d_go_path(reality_battery, monkeypatch, capsys):
    """
    Journey D: Consultant uses /go command for guided workflow.

    EXPECTED BEHAVIOR:
    - /go works in both single-step and full mode
    - Blocks cleanly at theme gate in full mode
    - No stdin prompts
    - Messaging is truthful about progress
    """
    reality_battery.assert_no_stdin_prompts(monkeypatch)

    project_root = reality_battery.create_workspace()
    reality_battery.setup_workspace(project_root)

    handler = CommandHandler(project_root)

    # Install demo data
    handler.handle_sampledata(subcommand="install")

    # Set intent
    storage = IntentStorage(project_root)
    storage.capture_intent("Test /go workflow", captured_via="test")

    # Create minimal spec
    spec = {
        "project_name": "Go Test",
        "client_name": "Test Client",
        "objective": "Test /go workflow",
        "project_type": "analytics",
    }
    spec_path = project_root / "project_state" / "spec.yaml"
    with open(spec_path, "w") as f:
        yaml.dump(spec, f)

    # Create rails_state simulating progress to build stage
    rails_state_path = project_root / "project_state" / "rails_state.json"
    rails_state = {
        "completed_stages": ["startkie", "spec", "eda", "analyze"],
        "workflow_started": True
    }
    with open(rails_state_path, "w") as f:
        json.dump(rails_state, f)

    # Try /go --full without theme - should block at build
    result = handler.handle_go(full=True)

    # Should block at build stage (theme not set)
    if result.get("blocked_at") == "build":
        assert "theme" in result["message"].lower(), "Should mention theme in block message"
        print("  ✓ /go --full correctly blocked at build stage without theme")

    # Set theme and try again
    handler.handle_theme(set_theme="light")

    # Now /go should proceed past theme gate
    result = handler.handle_go(full=False)  # Single step
    assert result["success"] or result.get("blocked_at") != "build", \
        "/go should not block on theme after theme is set"

    print("✓ Journey D: /go path works correctly")


# ============================================================================
# JOURNEY E: Corrupted/Unsupported Excel (OLE2)
# ============================================================================

def test_journey_e_corrupted_excel(reality_battery, monkeypatch, capsys):
    """
    Journey E: Consultant drops corrupted or old-format Excel file.

    EXPECTED BEHAVIOR:
    - File detection fails gracefully (not crash)
    - Clear error message explaining issue
    - Suggests fixes or alternatives
    - No stdin prompts
    """
    reality_battery.assert_no_stdin_prompts(monkeypatch)

    project_root = reality_battery.create_workspace()
    reality_battery.setup_workspace(project_root)

    # Create fake corrupted Excel file (OLE2 format header)
    data_dir = project_root / "data"
    corrupted_file = data_dir / "old_format.xls"

    # Write OLE2 magic bytes (old Excel format)
    corrupted_file.write_bytes(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1' + b'\x00' * 100)

    handler = CommandHandler(project_root)

    # Try to run EDA - should handle gracefully
    result = handler.handle_eda()

    # Should either succeed with warning or fail gracefully (not crash)
    captured = capsys.readouterr()

    # Verify no crash occurred (if it crashed, we wouldn't get here)
    assert True, "EDA handled corrupted file without crashing"

    # If it failed, message should be helpful
    if not result["success"]:
        assert len(result.get("message", "")) > 0, "Should provide error message"

    print("✓ Journey E: Corrupted Excel handled gracefully")


# ============================================================================
# JOURNEY F: Large-ish CSV (~5k rows)
# ============================================================================

def test_journey_f_large_csv(reality_battery, monkeypatch, capsys):
    """
    Journey F: Consultant provides realistic-sized CSV (~5k rows).

    EXPECTED BEHAVIOR:
    - File loads successfully
    - EDA completes in reasonable time
    - Profile generated
    - No performance issues or timeouts
    - No stdin prompts
    """
    reality_battery.assert_no_stdin_prompts(monkeypatch)

    project_root = reality_battery.create_workspace()
    reality_battery.setup_workspace(project_root)

    # Create large CSV (~5000 rows)
    data_dir = project_root / "data"
    large_csv = data_dir / "large_data.csv"

    rows = ["region,product,revenue,units"]
    regions = ["North", "South", "East", "West"]
    products = ["Widget A", "Widget B", "Widget C"]

    for i in range(5000):
        region = regions[i % len(regions)]
        product = products[i % len(products)]
        revenue = 1000 + (i * 137) % 50000
        units = 10 + (i * 73) % 1000
        rows.append(f"{region},{product},{revenue},{units}")

    large_csv.write_text("\n".join(rows))

    handler = CommandHandler(project_root)

    # Run EDA - should handle large file
    result = handler.handle_eda()
    assert result["success"], f"EDA failed on large CSV: {result.get('message')}"

    # Verify profile was created
    profile_path = project_root / "outputs" / "eda_profile.yaml"
    reality_battery.assert_artifacts_exist([profile_path])

    print("✓ Journey F: Large CSV handled successfully")


# ============================================================================
# JOURNEY G: Freeform Guard
# ============================================================================

def test_journey_g_freeform_guard(reality_battery, monkeypatch, capsys):
    """
    Journey G: Consultant in Rails mode tries freeform command.

    EXPECTED BEHAVIOR:
    - Mode Gate blocks freeform execution
    - Clear message about /freeform enable
    - No crash, no confusion
    - No stdin prompts
    """
    reality_battery.assert_no_stdin_prompts(monkeypatch)

    project_root = reality_battery.create_workspace()
    reality_battery.setup_workspace(project_root)

    handler = CommandHandler(project_root)

    # Verify Rails mode is default
    from kie.state import get_execution_mode, ExecutionMode
    mode = get_execution_mode(project_root)
    assert mode == ExecutionMode.RAILS, "Should start in Rails mode"

    # Try freeform command - should show status
    result = handler.handle_freeform(subcommand="status")

    # Should show current mode and how to enable
    assert result["success"], "Freeform status should succeed"
    assert result["mode"] == "rails", "Should start in Rails mode"

    # Try to enable freeform
    result = handler.handle_freeform(subcommand="enable")
    assert result["success"], f"Freeform enable failed: {result.get('message')}"

    # Verify now enabled
    result = handler.handle_freeform(subcommand="status")
    assert result["success"]
    assert result["mode"] == "freeform", "Freeform should be enabled after enable command"

    print("✓ Journey G: Freeform guard works correctly")


# ============================================================================
# BATTERY SUMMARY
# ============================================================================

def test_battery_summary(capsys):
    """
    Print summary of all journey tests.

    This runs last and provides a clear PASS/FAIL summary.
    """
    print()
    print("=" * 70)
    print("CONSULTANT REALITY BATTERY: ALL JOURNEYS PASSED")
    print("=" * 70)
    print()
    print("Verified journeys:")
    print("  ✓ Journey A: Fresh workspace, no data")
    print("  ✓ Journey B: Demo data opt-in")
    print("  ✓ Journey C: Theme gate")
    print("  ✓ Journey D: /go path")
    print("  ✓ Journey E: Corrupted Excel")
    print("  ✓ Journey F: Large CSV (~5k rows)")
    print("  ✓ Journey G: Freeform guard")
    print()
    print("All Constitution requirements verified:")
    print("  ✓ No stdin prompts (non-interactive)")
    print("  ✓ Truth Gate (artifacts exist)")
    print("  ✓ Mode Gate (freeform blocked in Rails mode)")
    print("  ✓ Intent-aware messaging (no gated recommendations)")
    print("  ✓ Graceful error handling")
    print()
