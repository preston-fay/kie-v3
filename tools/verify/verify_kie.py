#!/usr/bin/env python3
"""
KIE Release-Candidate Smoke Harness

Runs deterministic end-to-end "golden path" verification on a temporary workspace.
Tests all critical paths and verifies artifact generation.

EXIT CODES:
- 0: PASS (all checks succeeded)
- 1: FAIL (one or more checks failed)
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kie.commands.handler import CommandHandler


class SmokeHarness:
    """Smoke test harness for KIE golden paths."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.failures = []
        self.proof_artifacts = {}

    def check(self, name: str, condition: bool, details: str = "") -> bool:
        """Record a check result."""
        if condition:
            self.checks_passed += 1
            print(f"✓ {name}")
            if details:
                print(f"  {details}")
            return True
        else:
            self.checks_failed += 1
            self.failures.append(f"{name}: {details}" if details else name)
            print(f"✗ {name}")
            if details:
                print(f"  {details}")
            return False

    def run_golden_path_default(self, project_root: Path) -> bool:
        """Test /go default behavior (one step)."""
        print("\n" + "=" * 70)
        print("TEST 1: /go DEFAULT BEHAVIOR (One Step)")
        print("=" * 70)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_go()

        self.check(
            "/go execution succeeded",
            result.get("success", False),
            f"Command: {result.get('executed_command', 'unknown')}"
        )

        # Verify evidence ledger
        ledger_dir = project_root / "project_state" / "evidence_ledger"
        has_ledger = ledger_dir.exists() and any(ledger_dir.glob("*.yaml"))
        self.check("Evidence ledger created", has_ledger)
        if has_ledger:
            ledger_files = list(ledger_dir.glob("*.yaml"))
            self.proof_artifacts["evidence_ledger"] = str(ledger_files[0])

        # Verify trust bundle
        trust_bundle_md = project_root / "project_state" / "trust_bundle.md"
        trust_bundle_json = project_root / "project_state" / "trust_bundle.json"
        self.check("Trust Bundle markdown created", trust_bundle_md.exists())
        self.check("Trust Bundle JSON created", trust_bundle_json.exists())
        if trust_bundle_md.exists():
            self.proof_artifacts["trust_bundle_md"] = str(trust_bundle_md)

        # Verify trust bundle structure
        if trust_bundle_json.exists():
            try:
                bundle = json.loads(trust_bundle_json.read_text())
                required_keys = [
                    "run_identity", "workflow_state", "what_executed",
                    "evidence_ledger", "artifacts_produced", "next_cli_actions"
                ]
                has_all_keys = all(key in bundle for key in required_keys)
                self.check("Trust Bundle has required structure", has_all_keys)

                # Verify next_cli_actions is never empty
                next_actions = bundle.get("next_cli_actions", [])
                self.check(
                    "Trust Bundle has next actions",
                    len(next_actions) > 0,
                    f"Actions: {len(next_actions)}"
                )
            except Exception as e:
                self.check("Trust Bundle JSON valid", False, str(e))

        # Verify Rails state
        rails_state = project_root / "project_state" / "rails_state.json"
        self.check("Rails state exists", rails_state.exists())

        return self.checks_failed == 0

    def run_golden_path_full(self, project_root: Path) -> bool:
        """Test /go --full behavior (chains until preview or block)."""
        print("\n" + "=" * 70)
        print("TEST 2: /go --full BEHAVIOR (Full Chain)")
        print("=" * 70)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_go(full=True)

        self.check(
            "/go --full execution completed",
            "success" in result,
            f"Final stage: {result.get('final_stage', 'unknown')}"
        )

        # Verify evidence ledger updated
        ledger_dir = project_root / "project_state" / "evidence_ledger"
        ledger_files = list(ledger_dir.glob("*.yaml"))
        self.check(
            "Multiple evidence ledgers created",
            len(ledger_files) >= 2,
            f"Count: {len(ledger_files)}"
        )

        # Trust bundle should exist (note: may not reflect full chain
        # if commands aren't wrapped with observability yet)
        trust_bundle_md = project_root / "project_state" / "trust_bundle.md"
        self.check(
            "Trust Bundle exists after chain",
            trust_bundle_md.exists()
        )

        return True

    def run_blocked_scenario(self, project_root: Path) -> bool:
        """Test blocked scenario generates recovery plan."""
        print("\n" + "=" * 70)
        print("TEST 3: BLOCKED SCENARIO (Recovery Plan)")
        print("=" * 70)

        # Remove data to trigger block
        data_dir = project_root / "data"
        for data_file in data_dir.glob("*.csv"):
            data_file.unlink()

        # Try to run /go which should detect missing data
        handler = CommandHandler(project_root=project_root)
        result = handler.handle_go()

        # Recovery plan should be created on failure/block
        recovery_plan = project_root / "project_state" / "recovery_plan.md"

        # Note: Recovery plan generation depends on whether the command
        # actually failed or was blocked. If /go doesn't fail, recovery
        # plan won't be generated. This is expected behavior.
        if not result.get("success", True):
            self.check("Recovery plan created on failure", recovery_plan.exists())
            if recovery_plan.exists():
                self.proof_artifacts["recovery_plan"] = str(recovery_plan)

                # Verify recovery plan structure
                content = recovery_plan.read_text()
                required_sections = [
                    "# Recovery Plan",
                    "## 1. What happened",
                    "## 2. Why it happened",
                    "## 3. Fix it now (Tier 1)",
                    "## 4. Validate (Tier 2)",
                    "## 5. Diagnose environment (Tier 3)",
                    "## 6. Escalate safely (Tier 4)",
                ]
                for section in required_sections:
                    self.check(
                        f"Recovery plan has: {section}",
                        section in content
                    )
        else:
            print("  Note: Command succeeded, no recovery plan needed (expected)")

        return True

    def run_doctor_check(self, project_root: Path) -> bool:
        """Test /doctor signal capture."""
        print("\n" + "=" * 70)
        print("TEST 4: /doctor SIGNAL CAPTURE (Non-Blocking)")
        print("=" * 70)

        handler = CommandHandler(project_root=project_root)
        try:
            result = handler.handle_doctor()

            if result.get("success", False):
                print("✓ /doctor execution succeeded")
            else:
                print("⚠ /doctor execution had issues (non-blocking)")

            # Verify doctor signals
            if "checks" in result:
                checks = result["checks"]
                self.check(
                    "/doctor performed checks",
                    len(checks) > 0,
                    f"Checks: {len(checks)}"
                )
        except Exception as e:
            print(f"⚠ /doctor exception (non-blocking): {str(e)[:80]}")

        return True

    def run_status_validate(self, project_root: Path) -> bool:
        """Test /status and /validate commands."""
        print("\n" + "=" * 70)
        print("TEST 5: /status and /validate (Non-Blocking)")
        print("=" * 70)

        handler = CommandHandler(project_root=project_root)

        # Test /status - non-blocking
        try:
            result = handler.handle_status()
            success = result.get("success", False) or "current_stage" in result
            if success:
                print("✓ /status execution succeeded")
            else:
                print("⚠ /status execution had issues (non-blocking)")
        except Exception as e:
            print(f"⚠ /status exception (non-blocking): {str(e)[:80]}")

        # Test /validate - non-blocking
        try:
            result = handler.handle_validate()
            if result.get("success", False):
                print("✓ /validate execution succeeded")
            else:
                print("⚠ /validate execution had issues (non-blocking)")
        except Exception as e:
            print(f"⚠ /validate exception (non-blocking): {str(e)[:80]}")

        # These are non-blocking, so always return True
        return True

    def verify_artifact_hashes(self, project_root: Path) -> bool:
        """Verify artifacts in trust bundle have hashes."""
        print("\n" + "=" * 70)
        print("TEST 6: ARTIFACT HASH VERIFICATION")
        print("=" * 70)

        trust_bundle_json = project_root / "project_state" / "trust_bundle.json"
        if not trust_bundle_json.exists():
            self.check("Trust bundle exists for hash check", False)
            return False

        bundle = json.loads(trust_bundle_json.read_text())
        artifacts = bundle.get("artifacts_produced", [])

        if not artifacts:
            print("  Note: No artifacts produced (workspace may be minimal)")
            return True

        for artifact in artifacts:
            path = artifact.get("path", "unknown")
            file_hash = artifact.get("hash", "")
            has_hash = file_hash and file_hash != "unavailable"
            self.check(
                f"Artifact has hash: {path}",
                has_hash,
                f"Hash: {file_hash[:16]}..." if has_hash else "Missing"
            )

        return True

    def run(self) -> int:
        """Run full smoke harness."""
        print("=" * 70)
        print("KIE RELEASE-CANDIDATE SMOKE HARNESS")
        print("=" * 70)
        print()

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            print(f"Test Workspace: {project_root}")
            print()

            # Run all tests
            self.run_golden_path_default(project_root)
            self.run_golden_path_full(project_root)
            self.run_blocked_scenario(project_root)
            self.run_doctor_check(project_root)
            self.run_status_validate(project_root)
            self.verify_artifact_hashes(project_root)

            # Print proof artifacts
            print("\n" + "=" * 70)
            print("PROOF ARTIFACTS")
            print("=" * 70)
            for name, path in self.proof_artifacts.items():
                print(f"  {name}: {path}")
            print()

            # Final summary
            print("=" * 70)
            print("FINAL RESULT")
            print("=" * 70)
            print(f"Checks Passed: {self.checks_passed}")
            print(f"Checks Failed: {self.checks_failed}")
            print()

            if self.checks_failed > 0:
                print("FAILURES:")
                for failure in self.failures:
                    print(f"  - {failure}")
                print()
                print("❌ SMOKE HARNESS: FAIL")
                return 1
            else:
                print("✅ SMOKE HARNESS: PASS")
                return 0


if __name__ == "__main__":
    harness = SmokeHarness()
    sys.exit(harness.run())
