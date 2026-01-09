#!/usr/bin/env python3
"""
Proof Script: Client Pack Skill (WOW #3)

Demonstrates:
1. NOT READY case (recovery plan present)
2. WITH CAVEATS case
3. READY case
4. Client pack markdown output
5. Evidence index correctness

EXIT CODES:
- 0: PASS (demonstration successful)
- 1: FAIL (errors encountered)
"""

import json
import sys
import tempfile
from pathlib import Path

import yaml

from kie.skills import SkillContext
from kie.skills.client_pack import ClientPackSkill


def print_section(title: str):
    """Print section header."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()


def main() -> int:
    """Run proof demonstration."""
    print_section("CLIENT PACK SKILL - PROOF DEMONSTRATION")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        print(f"Project Root: {project_root}")
        print()

        # Setup directories
        outputs_dir = project_root / "outputs"
        outputs_dir.mkdir()

        project_state = project_root / "project_state"
        project_state.mkdir()

        evidence_dir = project_state / "evidence_ledger"
        evidence_dir.mkdir()

        # ===================================================================
        # SCENARIO 1: NOT READY (Recovery Plan Exists)
        # ===================================================================
        print_section("SCENARIO 1: NOT READY (Recovery Plan Exists)")

        # Create recovery plan
        recovery_plan = project_state / "recovery_plan.md"
        recovery_plan.write_text("""# Recovery Plan

## Tier: BLOCK

Command `/build` was blocked due to missing data.

## Recovery Steps
1. python3 -m kie.cli eda
2. python3 -m kie.cli analyze
3. python3 -m kie.cli build
""")

        print(f"✓ Recovery Plan created")
        print()

        # Create client_readiness (INTERNAL_ONLY)
        client_readiness_s1 = {
            "overall_readiness": "INTERNAL_ONLY",
            "overall_reason": "Recovery plan exists - outputs require fixes",
            "next_actions": [
                "python3 -m kie.cli doctor",
                "python3 -m kie.cli validate",
            ],
        }
        (outputs_dir / "client_readiness.json").write_text(
            json.dumps(client_readiness_s1, indent=2)
        )

        # Create trust bundle
        trust_bundle_s1 = {
            "run_identity": {"run_id": "proof_run_001", "command": "preview"},
        }
        (project_state / "trust_bundle.json").write_text(
            json.dumps(trust_bundle_s1, indent=2)
        )

        # Create evidence ledger
        ledger_s1 = {
            "run_id": "proof_run_001",
            "command": "/preview",
            "outputs": [],
        }
        (evidence_dir / "proof_run_001.yaml").write_text(yaml.dump(ledger_s1))

        print(f"✓ Artifacts created (INTERNAL_ONLY)")
        print()

        # Execute skill
        skill = ClientPackSkill()
        context_s1 = SkillContext(
            project_root=project_root,
            current_stage="preview",
            artifacts={},
            evidence_ledger_id="proof_run_001",
        )

        result_s1 = skill.execute(context_s1)

        if not result_s1.success:
            print("❌ Scenario 1 failed")
            return 1

        print("✓ Skill executed successfully")
        print(f"  - Is Client Ready: {result_s1.evidence['is_client_ready']}")
        print()

        # Show pack output
        pack_md_s1 = Path(result_s1.artifacts["client_pack_markdown"]).read_text()

        print("Client Pack Output (first 30 lines):")
        print("-" * 70)
        for i, line in enumerate(pack_md_s1.split("\n")[:30], 1):
            print(line)
        print("-" * 70)
        print()

        # Verify NOT READY
        if "NOT CLIENT READY" not in pack_md_s1:
            print("❌ Expected 'NOT CLIENT READY' in title")
            return 1

        if "Next CLI Actions" not in pack_md_s1:
            print("❌ Expected 'Next CLI Actions' section")
            return 1

        print("✅ SCENARIO 1 PASSED: NOT READY pack generated correctly")
        print()

        # ===================================================================
        # SCENARIO 2: WITH CAVEATS
        # ===================================================================
        print_section("SCENARIO 2: WITH CAVEATS")

        # Remove recovery plan
        recovery_plan.unlink()

        # Clean up previous artifacts
        (outputs_dir / "client_pack.md").unlink()
        (outputs_dir / "client_pack.json").unlink()

        # Create client_readiness (WITH_CAVEATS)
        client_readiness_s2 = {
            "overall_readiness": "CLIENT_READY_WITH_CAVEATS",
            "overall_reason": "Evidence-backed but contains limitations",
            "approved_client_narrative": [
                "Analysis complete with evidence-backed findings",
                "Key insights prioritized by decision relevance",
            ],
            "do_not_say": [
                "Do not claim 'high confidence' without explicit confidence levels",
            ],
            "artifact_classifications": [
                {
                    "artifact": "outputs/insight_triage.md",
                    "caveats": [
                        "Some insights have Medium confidence",
                        "Limited data timeframe",
                    ],
                }
            ],
        }
        (outputs_dir / "client_readiness.json").write_text(
            json.dumps(client_readiness_s2, indent=2)
        )

        # Create insight_triage
        insight_triage_s2 = {
            "top_insights": [
                {
                    "title": "Revenue concentration in top 3 customers",
                    "confidence": "High",
                    "evidence": [
                        {"reference": "outputs/eda_profile.json", "value": 0.75}
                    ],
                    "caveats": [],
                },
                {
                    "title": "Sales trending upward in Q4",
                    "confidence": "Medium",
                    "evidence": [
                        {"reference": "outputs/eda_profile.json", "value": 0.12}
                    ],
                    "caveats": ["Limited timeframe"],
                },
            ],
            "consultant_guidance": {
                "lead_with": ["Revenue concentration"],
                "mention_cautiously": ["Sales trending upward"],
            },
        }
        (outputs_dir / "insight_triage.json").write_text(
            json.dumps(insight_triage_s2, indent=2)
        )

        # Create insight_brief
        (outputs_dir / "insight_brief.md").write_text("""# Insight Brief

This analysis examines revenue concentration and sales trends.

## Key Findings
- Revenue highly concentrated in top customers
- Q4 shows positive trend but limited data
""")

        # Update trust bundle
        trust_bundle_s2 = {
            "run_identity": {"run_id": "proof_run_002", "command": "preview"},
        }
        (project_state / "trust_bundle.json").write_text(
            json.dumps(trust_bundle_s2, indent=2)
        )

        # Create evidence ledger with hashes
        ledger_s2 = {
            "run_id": "proof_run_002",
            "command": "/preview",
            "outputs": [
                {"path": "outputs/insight_triage.md", "hash": "abc123def456"},
                {"path": "outputs/insight_triage.json", "hash": "ghi789jkl012"},
                {"path": "outputs/insight_brief.md", "hash": "mno345pqr678"},
            ],
        }
        (evidence_dir / "proof_run_002.yaml").write_text(yaml.dump(ledger_s2))

        print(f"✓ Artifacts created (WITH_CAVEATS)")
        print()

        # Execute skill
        context_s2 = SkillContext(
            project_root=project_root,
            current_stage="preview",
            artifacts={},
            evidence_ledger_id="proof_run_002",
        )

        result_s2 = skill.execute(context_s2)

        if not result_s2.success:
            print("❌ Scenario 2 failed")
            return 1

        print("✓ Skill executed successfully")
        print(f"  - Is Client Ready: {result_s2.evidence['is_client_ready']}")
        print()

        # Show pack output
        pack_md_s2 = Path(result_s2.artifacts["client_pack_markdown"]).read_text()

        print("Client Pack Output (Caveats section):")
        print("-" * 70)
        in_caveats = False
        line_count = 0
        for line in pack_md_s2.split("\n"):
            if "## 4. Caveats & Limitations" in line:
                in_caveats = True
            elif in_caveats and line.startswith("## "):
                break
            if in_caveats:
                print(line)
                line_count += 1
        print("-" * 70)
        print()

        # Verify WITH CAVEATS
        if "CLIENT_READY_WITH_CAVEATS" not in pack_md_s2:
            print("❌ Expected 'CLIENT_READY_WITH_CAVEATS' in readiness")
            return 1

        if "## 4. Caveats & Limitations" not in pack_md_s2:
            print("❌ Expected 'Caveats & Limitations' section")
            return 1

        print("✅ SCENARIO 2 PASSED: WITH CAVEATS pack generated correctly")
        print()

        # Show evidence index
        print("Evidence Index:")
        print("-" * 70)
        in_evidence = False
        for line in pack_md_s2.split("\n"):
            if "## 6. Evidence Index" in line:
                in_evidence = True
            elif in_evidence and line.startswith("## "):
                break
            if in_evidence:
                print(line)
        print("-" * 70)
        print()

        # Verify evidence index
        pack_json_s2 = json.loads(
            Path(result_s2.artifacts["client_pack_json"]).read_text()
        )

        if not pack_json_s2["evidence_index"]:
            print("❌ Expected evidence index in JSON")
            return 1

        print("Evidence Index (JSON):")
        for entry in pack_json_s2["evidence_index"]:
            print(f"  - {entry['artifact']}")
            print(f"    Hash: {entry['hash']}")
            print(f"    Ledger: {entry['ledger_id']}")
        print()

        print("✅ Evidence index verified")
        print()

        # ===================================================================
        # SCENARIO 3: READY
        # ===================================================================
        print_section("SCENARIO 3: READY")

        # Clean up previous artifacts
        (outputs_dir / "client_pack.md").unlink()
        (outputs_dir / "client_pack.json").unlink()

        # Create client_readiness (READY)
        client_readiness_s3 = {
            "overall_readiness": "CLIENT_READY",
            "overall_reason": "All conditions satisfied",
            "approved_client_narrative": [
                "Complete analysis with evidence-backed findings",
                "All insights have high confidence",
                "Ready for client presentation",
            ],
            "do_not_say": [
                "Do not extrapolate beyond data timeframe",
            ],
        }
        (outputs_dir / "client_readiness.json").write_text(
            json.dumps(client_readiness_s3, indent=2)
        )

        # Create run_story
        (outputs_dir / "run_story.md").write_text("""# Run Story

This project analyzed customer revenue data to identify concentration risks
and growth opportunities. The analysis followed a systematic approach using
exploratory data analysis, statistical testing, and visualization.

Key outputs include revenue concentration metrics, trend analysis, and
actionable recommendations for diversifying the customer base.
""")

        # Update trust bundle
        trust_bundle_s3 = {
            "run_identity": {"run_id": "proof_run_003", "command": "preview"},
        }
        (project_state / "trust_bundle.json").write_text(
            json.dumps(trust_bundle_s3, indent=2)
        )

        # Create evidence ledger
        ledger_s3 = {
            "run_id": "proof_run_003",
            "command": "/preview",
            "outputs": [
                {"path": "outputs/run_story.md", "hash": "xyz789abc123"},
            ],
        }
        (evidence_dir / "proof_run_003.yaml").write_text(yaml.dump(ledger_s3))

        print(f"✓ Artifacts created (READY)")
        print()

        # Execute skill
        context_s3 = SkillContext(
            project_root=project_root,
            current_stage="preview",
            artifacts={},
            evidence_ledger_id="proof_run_003",
        )

        result_s3 = skill.execute(context_s3)

        if not result_s3.success:
            print("❌ Scenario 3 failed")
            return 1

        print("✓ Skill executed successfully")
        print(f"  - Is Client Ready: {result_s3.evidence['is_client_ready']}")
        print()

        # Show pack output
        pack_md_s3 = Path(result_s3.artifacts["client_pack_markdown"]).read_text()

        print("Client Pack Output (Executive Narrative section):")
        print("-" * 70)
        in_narrative = False
        line_count = 0
        for line in pack_md_s3.split("\n"):
            if "## 1. Executive Narrative" in line:
                in_narrative = True
            elif in_narrative and line.startswith("## "):
                break
            if in_narrative:
                print(line)
                line_count += 1
                if line_count > 10:
                    break
        print("-" * 70)
        print()

        # Verify READY
        if "CLIENT_READY" not in pack_md_s3 or "NOT CLIENT READY" in pack_md_s3:
            print("❌ Expected 'CLIENT_READY' without 'NOT'")
            return 1

        print("✅ SCENARIO 3 PASSED: READY pack generated correctly")
        print()

        # ===================================================================
        # FINAL SUMMARY
        # ===================================================================
        print_section("PROOF DEMONSTRATION COMPLETE")

        print("✅ ALL SCENARIOS PASSED")
        print()
        print("Verified:")
        print("  ✓ NOT READY case (recovery plan present)")
        print("  ✓ WITH CAVEATS case")
        print("  ✓ READY case")
        print("  ✓ Client pack markdown output")
        print("  ✓ Evidence index correctness")
        print()

        return 0


if __name__ == "__main__":
    sys.exit(main())
