#!/usr/bin/env python3
"""
Proof Script: Showcase Mode

Demonstrates:
1. Fresh workspace
2. KIE_SHOWCASE=1
3. /go execution
4. client_pack.md output (first 50 lines)
5. DEMO labeling verification
6. Next-steps message

EXIT CODES:
- 0: PASS (demonstration successful)
- 1: FAIL (errors encountered)
"""

import os
import sys
import tempfile
from pathlib import Path


def print_section(title: str):
    """Print section header."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()


def main() -> int:
    """Run proof demonstration."""
    print_section("SHOWCASE MODE - PROOF DEMONSTRATION")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        print(f"Fresh Workspace: {project_root}")
        print()

        # Set KIE_SHOWCASE=1
        os.environ["KIE_SHOWCASE"] = "1"
        print("✓ Set KIE_SHOWCASE=1")
        print()

        try:
            # ===================================================================
            # Run Showcase
            # ===================================================================
            print_section("Running /go (Showcase Mode)")

            from kie.showcase import run_showcase, mark_showcase_completed

            result = run_showcase(project_root)

            if not result["success"]:
                print(f"❌ Showcase failed: {result.get('message')}")
                return 1

            print()
            print("✓ Showcase run completed")
            print()

            # Mark as completed
            mark_showcase_completed(project_root)

            # ===================================================================
            # Verify Client Pack
            # ===================================================================
            print_section("Client Pack Output (First 50 Lines)")

            client_pack = project_root / "outputs" / "client_pack.md"
            if not client_pack.exists():
                print("❌ client_pack.md not found")
                return 1

            content = client_pack.read_text()
            lines = content.split("\n")

            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3d} | {line}")

            print()
            print("=" * 70)
            print()

            # ===================================================================
            # Verify DEMO Labeling
            # ===================================================================
            print_section("Verify DEMO Labeling")

            if "SHOWCASE — DEMO DATA" not in content:
                print("❌ Missing 'SHOWCASE — DEMO DATA' in title")
                return 1

            print("✓ Title contains 'SHOWCASE — DEMO DATA'")

            if "demo data" not in content.lower():
                print("❌ Missing 'demo data' mentions")
                return 1

            print("✓ Content mentions 'demo data'")

            if "This content is generated from demo data" not in content:
                print("⚠️  Missing explicit demo data statement (optional)")
            else:
                print("✓ Explicit demo data statement present")

            print()

            # ===================================================================
            # Verify Evidence Ledger
            # ===================================================================
            print_section("Verify Evidence Ledger")

            evidence_dir = project_root / "project_state" / "evidence_ledger"
            if not evidence_dir.exists():
                print("❌ Evidence Ledger directory not found")
                return 1

            ledger_files = list(evidence_dir.glob("showcase_*.yaml"))
            if not ledger_files:
                print("❌ No showcase ledger files found")
                return 1

            print(f"✓ Found {len(ledger_files)} Evidence Ledger file(s)")
            for ledger_file in ledger_files:
                print(f"  - {ledger_file.name}")
            print()

            # ===================================================================
            # Verify Trust Bundle
            # ===================================================================
            print_section("Verify Trust Bundle")

            trust_bundle = project_root / "project_state" / "trust_bundle.json"
            if not trust_bundle.exists():
                print("❌ Trust Bundle not found")
                return 1

            print("✓ Trust Bundle exists")
            print()

            # ===================================================================
            # Verify WOW Stack
            # ===================================================================
            print_section("Verify WOW Stack")

            outputs_dir = project_root / "outputs"

            wow_artifacts = [
                "insights_catalog.json",
                "insight_triage.json",
                "insight_triage.md",
                "insight_brief.md",
                "run_story.md",
                "client_readiness.json",
                "client_pack.md",
            ]

            all_present = True
            for artifact in wow_artifacts:
                path = outputs_dir / artifact
                if path.exists():
                    print(f"  ✓ {artifact}")
                else:
                    print(f"  ❌ {artifact} MISSING")
                    all_present = False

            if not all_present:
                print()
                print("❌ Some WOW Stack artifacts missing")
                return 1

            print()
            print("✓ All WOW Stack artifacts present")
            print()

            # ===================================================================
            # Verify No Data/ Writes
            # ===================================================================
            print_section("Verify No data/ Writes")

            data_dir = project_root / "data"
            if data_dir.exists() and any(data_dir.iterdir()):
                print("❌ Showcase wrote to data/ directory (violation)")
                return 1

            print("✓ No writes to data/ directory")
            print()

            # ===================================================================
            # Verify Showcase Directory
            # ===================================================================
            print_section("Verify project_state/showcase/")

            showcase_dir = project_root / "project_state" / "showcase"
            if not showcase_dir.exists():
                print("❌ Showcase directory not found")
                return 1

            demo_data = showcase_dir / "demo_data.csv"
            if not demo_data.exists():
                print("❌ demo_data.csv not found in showcase/")
                return 1

            print("✓ Showcase directory exists with demo_data.csv")
            print()

            # ===================================================================
            # Verify Showcase Completed Flag
            # ===================================================================
            print_section("Verify Showcase Completion")

            showcase_flag = project_root / "project_state" / "showcase_completed"
            if not showcase_flag.exists():
                print("❌ showcase_completed flag not found")
                return 1

            print("✓ showcase_completed flag exists")

            # Verify showcase won't auto-activate again (unset env var first)
            from kie.showcase import should_activate_showcase

            # Temporarily unset KIE_SHOWCASE to test auto-disable
            old_env = os.environ.pop("KIE_SHOWCASE", None)

            if should_activate_showcase(project_root):
                print("❌ Showcase would activate again (should be disabled)")
                if old_env:
                    os.environ["KIE_SHOWCASE"] = old_env
                return 1

            # Restore env var
            if old_env:
                os.environ["KIE_SHOWCASE"] = old_env

            print("✓ Showcase auto-activation disabled")
            print()

            # ===================================================================
            # FINAL SUMMARY
            # ===================================================================
            print_section("PROOF DEMONSTRATION COMPLETE")

            print("✅ ALL CHECKS PASSED")
            print()
            print("Verified:")
            print("  ✓ Fresh workspace")
            print("  ✓ KIE_SHOWCASE=1 activation")
            print("  ✓ /go execution (showcase mode)")
            print("  ✓ client_pack.md generated")
            print("  ✓ DEMO labeling present")
            print("  ✓ Evidence Ledger created")
            print("  ✓ Trust Bundle created")
            print("  ✓ Full WOW Stack generated")
            print("  ✓ No data/ writes (isolated)")
            print("  ✓ showcase/ directory used")
            print("  ✓ Auto-disable after completion")
            print()

            return 0

        finally:
            # Clean up environment
            if "KIE_SHOWCASE" in os.environ:
                del os.environ["KIE_SHOWCASE"]


if __name__ == "__main__":
    sys.exit(main())
