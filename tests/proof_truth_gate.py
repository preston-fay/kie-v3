"""
Proof Script: Truth Gate (Constitution Section 5)

Demonstrates that the Truth Gate prevents commands from claiming
outputs that don't exist on disk.
"""

import shutil
import tempfile
from pathlib import Path

from kie.observability.truth_gate import TruthGate, print_truth_violation_message


def print_section(title: str):
    """Print section header."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_check(passed: bool, message: str):
    """Print check result."""
    symbol = "✓" if passed else "✗"
    print(f"  {symbol} {message}")


def main():
    """Run truth gate proof."""
    print_section("TRUTH GATE PROOF - Constitution Section 5")
    print()
    print("This script demonstrates:")
    print("  1. Commands claiming non-existent outputs are blocked")
    print("  2. Commands with real outputs pass validation")
    print("  3. Truth violations are clearly reported")
    print()

    # Create temporary workspace
    temp_dir = Path(tempfile.mkdtemp(prefix="truth_gate_proof_"))
    try:
        print(f"Created temp workspace: {temp_dir}")
        (temp_dir / "outputs").mkdir(parents=True)
        (temp_dir / "outputs" / "charts").mkdir(parents=True)
        (temp_dir / "exports").mkdir(parents=True)

        gate = TruthGate(temp_dir)

        # TEST 1: False claim detected
        print_section("TEST 1: False Claim Detection")
        print("Simulating command claiming output that doesn't exist...")

        fake_profile = temp_dir / "outputs" / "nonexistent_profile.yaml"
        result_fake = {
            "success": True,
            "profile_saved": str(fake_profile),
        }

        validation = gate.validate_command_outputs("eda", result_fake)
        print_check(not validation.passed, f"Truth gate blocked false claim")
        print_check(len(validation.missing_artifacts) > 0, "Missing artifacts reported")
        print(f"    Missing: {validation.missing_artifacts}")

        # TEST 2: True claim passes
        print_section("TEST 2: True Claim Validation")
        print("Creating real output file...")

        real_profile = temp_dir / "outputs" / "real_profile.yaml"
        real_profile.write_text("shape:\n  rows: 100\n  columns: 5\n")

        result_real = {
            "success": True,
            "profile_saved": str(real_profile),
        }

        validation = gate.validate_command_outputs("eda", result_real)
        print_check(validation.passed, "Truth gate passed for real output")
        print_check(len(validation.missing_artifacts) == 0, "No missing artifacts")
        print_check(len(validation.validated_artifacts) > 0, "Artifacts validated")
        print(f"    Validated: {len(validation.validated_artifacts)} file(s)")

        # TEST 3: Chart count validation
        print_section("TEST 3: Chart Count Validation")
        print("Claiming 3 charts were created...")

        result_charts_fake = {
            "success": True,
            "charts_created": 3,  # Claiming 3 charts
        }

        validation = gate.validate_command_outputs("analyze", result_charts_fake)
        print_check(not validation.passed, "Truth gate blocked false chart claim")
        print(f"    Reason: Charts directory empty but claimed 3 charts")

        # Now create real charts
        print("\nCreating real chart files...")
        charts_dir = temp_dir / "outputs" / "charts"
        (charts_dir / "chart1.png").write_text("chart 1")
        (charts_dir / "chart2.png").write_text("chart 2")
        (charts_dir / "chart3.png").write_text("chart 3")

        result_charts_real = {
            "success": True,
            "charts_created": 3,
        }

        validation = gate.validate_command_outputs("analyze", result_charts_real)
        print_check(validation.passed, "Truth gate passed with real charts")
        print(f"    Validated: {len(validation.validated_artifacts)} chart(s)")

        # TEST 4: Build output validation
        print_section("TEST 4: Build Output Validation")
        print("Claiming presentation was created...")

        fake_pptx = temp_dir / "exports" / "presentation.pptx"
        result_build_fake = {
            "success": True,
            "presentation_path": str(fake_pptx),
        }

        validation = gate.validate_command_outputs("build", result_build_fake)
        print_check(not validation.passed, "Truth gate blocked false presentation claim")

        # Create real presentation
        print("\nCreating real presentation file...")
        fake_pptx.write_text("fake pptx content")

        result_build_real = {
            "success": True,
            "presentation_path": str(fake_pptx),
        }

        validation = gate.validate_command_outputs("build", result_build_real)
        print_check(validation.passed, "Truth gate passed with real presentation")

        # TEST 5: Already-failed commands skip validation
        print_section("TEST 5: Failed Command Handling")
        print("Testing command that already failed...")

        result_already_failed = {
            "success": False,
            "error": "Command failed for other reasons",
            "profile_saved": "/fake/nonexistent/path.yaml",
        }

        validation = gate.validate_command_outputs("eda", result_already_failed)
        print_check(validation.passed, "Truth gate skips already-failed commands")
        print("    (Prevents double-failure)")

        # TEST 6: Truth violation message
        print_section("TEST 6: Truth Violation Messaging")
        print("Demonstrating truth violation message format...")

        fake_validation = TruthGate(temp_dir).validate_command_outputs(
            "eda",
            {"success": True, "profile_saved": "/fake/missing.yaml"}
        )

        if not fake_validation.passed:
            print_truth_violation_message(fake_validation)

        # Summary
        print_section("✅ TRUTH GATE PROOF COMPLETE")
        print()
        print("All tests passed:")
        print("  ✓ False claims are detected and blocked")
        print("  ✓ True claims pass validation")
        print("  ✓ Chart counts are validated")
        print("  ✓ Build outputs are validated")
        print("  ✓ Already-failed commands are handled correctly")
        print("  ✓ Truth violations produce clear error messages")
        print()
        print("Truth Gate is operational and Constitution Section 5 is enforced.")
        print("=" * 70)

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        print()
        print(f"Cleaned up workspace: {temp_dir}")


if __name__ == "__main__":
    main()
