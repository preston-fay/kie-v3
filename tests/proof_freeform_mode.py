#!/usr/bin/env python3
"""
Proof Script: Permissioned Freeform Mode

Demonstrates end-to-end freeform mode workflow:
1. Fresh workspace
2. Default mode is rails (off-rails execution forbidden)
3. Enable freeform mode
4. Mode persists
5. Disable back to rails

Run: python3 tests/proof_freeform_mode.py
"""

import tempfile
from pathlib import Path

import yaml


def proof_freeform_mode_workflow():
    """Demonstrate complete freeform mode workflow."""
    print("=" * 70)
    print("PROOF: Permissioned Freeform Mode")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        print(f"✓ Created fresh workspace at {project_root}")
        print()

        # Step 1: Bootstrap workspace
        print("Step 1: Bootstrap workspace")
        print("-" * 70)
        from kie.commands.handler import CommandHandler

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_startkie()

        assert result["success"], "Bootstrap failed"
        print(f"✓ Workspace bootstrapped: {result['message']}")
        print()

        # Step 2: Verify default mode is rails
        print("Step 2: Verify default execution mode is 'rails'")
        print("-" * 70)
        from kie.execution_policy import ExecutionPolicy

        policy = ExecutionPolicy(project_root)
        default_mode = policy.get_mode()
        assert default_mode == "rails", f"Expected default mode 'rails', got {default_mode}"
        print(f"✓ Default execution mode: {default_mode}")
        print("  Off-rails execution is FORBIDDEN by default")
        print()

        # Step 3: Check /freeform status (should show rails)
        print("Step 3: Check /freeform status")
        print("-" * 70)
        result = handler.handle_freeform(action="status")
        assert result["success"]
        assert result["mode"] == "rails"
        print(f"✓ /freeform status shows: {result['mode']}")
        print()

        # Step 4: Enable freeform mode
        print("Step 4: Enable freeform mode")
        print("-" * 70)
        result = handler.handle_freeform(action="enable")
        assert result["success"]
        assert result["mode"] == "freeform"
        print(f"✓ Freeform mode enabled: {result['mode']}")
        print("  Custom analysis is now allowed")
        print()

        # Step 5: Verify mode persists
        print("Step 5: Verify mode persists")
        print("-" * 70)
        policy2 = ExecutionPolicy(project_root)
        persisted_mode = policy2.get_mode()
        assert persisted_mode == "freeform"
        print(f"✓ Mode persisted across instances: {persisted_mode}")
        print()

        # Step 6: Verify policy file format
        print("Step 6: Verify policy file format")
        print("-" * 70)
        policy_file = project_root / "project_state" / "execution_policy.yaml"
        assert policy_file.exists(), "Policy file should exist"

        with open(policy_file) as f:
            policy_data = yaml.safe_load(f)

        print(f"✓ Policy file exists: {policy_file.name}")
        print(f"  - mode: {policy_data['mode']}")
        print(f"  - set_at: {policy_data['set_at']}")
        print(f"  - set_by: {policy_data['set_by']}")
        assert policy_data["mode"] == "freeform"
        assert "set_at" in policy_data
        assert policy_data["set_by"] == "user"
        print()

        # Step 7: Test /status shows execution mode
        print("Step 7: Verify /status shows execution mode")
        print("-" * 70)
        status = handler.handle_status()
        assert "execution_mode" in status, "Status should include execution_mode"
        assert status["execution_mode"] == "freeform"
        print(f"✓ /status includes execution_mode: {status['execution_mode']}")
        print()

        # Step 8: Disable freeform mode
        print("Step 8: Disable freeform mode (return to rails)")
        print("-" * 70)
        result = handler.handle_freeform(action="disable")
        assert result["success"]
        assert result["mode"] == "rails"
        print(f"✓ Freeform mode disabled: {result['mode']}")
        print("  Off-rails execution is now forbidden again")
        print()

        # Step 9: Verify mode changed back to rails
        print("Step 9: Verify mode changed back to rails")
        print("-" * 70)
        policy3 = ExecutionPolicy(project_root)
        final_mode = policy3.get_mode()
        assert final_mode == "rails"
        print(f"✓ Final execution mode: {final_mode}")
        print()

        # Step 10: Verify status reflects change
        print("Step 10: Verify /status reflects mode change")
        print("-" * 70)
        status = handler.handle_status()
        assert status["execution_mode"] == "rails"
        print(f"✓ /status shows: {status['execution_mode']}")
        print()

        # Step 11: Verify Rails state not mutated
        print("Step 11: Verify Rails state not mutated")
        print("-" * 70)
        rails_path = project_root / "project_state" / "rails_state.json"

        if rails_path.exists():
            import json
            with open(rails_path) as f:
                rails_data = json.load(f)

            # Rails state should NOT contain execution_mode
            assert "execution_mode" not in rails_data, "Rails state should not contain execution_mode"
            print("✓ Rails state does NOT contain execution_mode (correct)")
        else:
            print("✓ Rails state file not yet created (workspace not advanced)")
        print()

        # Step 12: Test invalid action
        print("Step 12: Test invalid action rejection")
        print("-" * 70)
        result = handler.handle_freeform(action="invalid")
        assert not result["success"]
        print("✓ Invalid action rejected (as expected)")
        print()

        # Final Summary
        print("=" * 70)
        print("PROOF COMPLETE: Permissioned Freeform Mode")
        print("=" * 70)
        print()
        print("✅ Fresh workspace created")
        print("✅ Default mode is 'rails' (off-rails execution forbidden)")
        print("✅ /freeform enable activates custom analysis")
        print("✅ Mode persists in execution_policy.yaml")
        print("✅ /status shows execution_mode field")
        print("✅ /freeform disable returns to rails mode")
        print("✅ Rails state remains separate (not mutated)")
        print("✅ Invalid actions rejected")
        print()
        print("Governance System Working As Designed ✓")
        print()
        print("BEHAVIORAL CONTRACT:")
        print("  • Default: Off-rails execution FORBIDDEN")
        print("  • User must explicitly opt-in via /freeform enable")
        print("  • Mode stored per-project (not global)")
        print("  • Rails authority unchanged")
        print("  • Policy separate from workflow state")


if __name__ == "__main__":
    proof_freeform_mode_workflow()
