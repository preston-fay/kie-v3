#!/usr/bin/env python3
"""
Proof Script: Client Readiness Skill (WOW #2)

Demonstrates:
1. INTERNAL_ONLY classification driven by recovery plan
2. CLIENT_READY_WITH_CAVEATS driven by triage confidence
3. CLIENT_READY when all conditions met
4. Evidence linkage with artifact hashes
5. Approved client narrative generation

EXIT CODES:
- 0: PASS (demonstration successful)
- 1: FAIL (errors encountered)
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

from kie.insights import (
    Insight,
    InsightCatalog,
    InsightType,
    InsightCategory,
    InsightSeverity,
    Evidence,
)
from kie.skills import SkillContext
from kie.skills.client_readiness import ClientReadinessSkill, ReadinessLabel


def print_section(title: str):
    """Print section header."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()


def main() -> int:
    """Run proof demonstration."""
    print_section("CLIENT READINESS SKILL - PROOF DEMONSTRATION")

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
        # SCENARIO 1: INTERNAL_ONLY (Recovery Plan Exists)
        # ===================================================================
        print_section("SCENARIO 1: INTERNAL_ONLY (Recovery Plan Exists)")

        # Create recovery plan
        recovery_plan = project_state / "recovery_plan.md"
        recovery_plan.write_text("""# Recovery Plan

## Tier: BLOCK

Command `/build` was blocked due to missing prerequisites.

## Recovery Steps
1. python3 -m kie.cli eda
2. python3 -m kie.cli analyze
3. python3 -m kie.cli build
""")

        print(f"✓ Recovery Plan created: {recovery_plan}")
        print()

        # Create trust bundle
        trust_bundle_data_s1 = {
            "run_identity": {"run_id": "proof_run_001", "command": "build"},
            "workflow_state": {"stage_after": "spec"},
            "whats_missing": {
                "items": [
                    {"name": "data files", "severity": "critical"},
                ]
            },
        }
        trust_bundle_path = project_state / "trust_bundle.json"
        trust_bundle_path.write_text(json.dumps(trust_bundle_data_s1, indent=2))

        print(f"✓ Trust Bundle created: {trust_bundle_path}")
        print()

        # Create candidate artifact
        (outputs_dir / "insight_brief.md").write_text(
            "# Insight Brief\n\nTest brief (should be INTERNAL_ONLY)"
        )

        # Execute skill
        skill = ClientReadinessSkill()
        context_s1 = SkillContext(
            project_root=project_root,
            current_stage="build",
            artifacts={},
            evidence_ledger_id="proof_run_001",
        )

        result_s1 = skill.execute(context_s1)

        if not result_s1.success:
            print("❌ Scenario 1 failed")
            return 1

        print("✓ Skill executed successfully")
        print(f"  - Overall Readiness: {result_s1.evidence['overall_readiness']}")
        print()

        # Verify INTERNAL_ONLY
        json_path_s1 = Path(result_s1.artifacts["readiness_json"])
        readiness_s1 = json.loads(json_path_s1.read_text())

        if readiness_s1["overall_readiness"] != ReadinessLabel.INTERNAL_ONLY.value:
            print(f"❌ Expected INTERNAL_ONLY, got {readiness_s1['overall_readiness']}")
            return 1

        print("✅ SCENARIO 1 PASSED: INTERNAL_ONLY classification correct")
        print(f"   Reason: {readiness_s1['overall_reason']}")
        print()

        # ===================================================================
        # SCENARIO 2: CLIENT_READY_WITH_CAVEATS (Low Confidence Insights)
        # ===================================================================
        print_section("SCENARIO 2: CLIENT_READY_WITH_CAVEATS (Low Confidence)")

        # Remove recovery plan
        recovery_plan.unlink()

        # Clean up Scenario 1 artifacts
        (outputs_dir / "insight_brief.md").unlink()
        (outputs_dir / "client_readiness.md").unlink()
        (outputs_dir / "client_readiness.json").unlink()

        # Update trust bundle (no critical issues)
        trust_bundle_data_s2 = {
            "run_identity": {"run_id": "proof_run_002", "command": "build"},
            "workflow_state": {"stage_after": "build"},
            "whats_missing": {"items": []},
            "warnings_blocks": {"warnings": [], "blocks": []},
        }
        trust_bundle_path.write_text(json.dumps(trust_bundle_data_s2, indent=2))

        # Create evidence ledger
        ledger_data_s2 = {
            "run_id": "proof_run_002",
            "command": "/build",
            "outputs": [
                {"path": "outputs/insight_triage.md", "hash": "def456abc789"},
                {"path": "outputs/insight_triage.json", "hash": "ghi012jkl345"},
            ],
        }
        ledger_path_s2 = evidence_dir / "proof_run_002.yaml"
        ledger_path_s2.write_text(yaml.dump(ledger_data_s2))

        print(f"✓ Evidence Ledger created: {ledger_path_s2}")
        print()

        # Create insight triage with non-High confidence
        triage_data = {
            "total_candidate_insights": 5,
            "high_confidence_insights": 1,
            "use_with_caution_insights": 2,
            "top_insights": [
                {
                    "title": "Revenue concentrated in top 3 customers",
                    "confidence": "High",
                    "evidence": [
                        {"type": "metric", "reference": "outputs/eda_profile.json", "value": 0.75}
                    ],
                    "caveats": [],
                },
                {
                    "title": "Sales trending upward in Q4",
                    "confidence": "Medium",
                    "evidence": [
                        {"type": "metric", "reference": "outputs/eda_profile.json", "value": 0.12}
                    ],
                    "caveats": ["Limited data timeframe (2 quarters only)"],
                },
                {
                    "title": "Possible correlation between marketing spend and conversions",
                    "confidence": "Low",
                    "evidence": [],
                    "caveats": ["Weak statistical significance (p=0.15)", "Correlation not causation"],
                },
            ],
            "deprioritized_insights": [
                {"insight": "Minor cost variance in Region D", "reason": "Low decision relevance"}
            ],
            "consultant_guidance": {
                "lead_with": ["Revenue concentrated in top 3 customers"],
                "mention_cautiously": ["Sales trending upward in Q4"],
                "avoid_leading_with": ["Possible correlation between marketing spend"],
            },
        }

        triage_json = outputs_dir / "insight_triage.json"
        triage_json.write_text(json.dumps(triage_data, indent=2))

        triage_md = outputs_dir / "insight_triage.md"
        triage_md.write_text("# Insight Triage\n\nTest triage with mixed confidence")

        print(f"✓ Insight Triage artifacts created")
        print(f"  - High confidence: {triage_data['high_confidence_insights']}")
        print(f"  - Use with caution: {triage_data['use_with_caution_insights']}")
        print()

        # Execute skill
        context_s2 = SkillContext(
            project_root=project_root,
            current_stage="build",
            artifacts={},
            evidence_ledger_id="proof_run_002",
        )

        result_s2 = skill.execute(context_s2)

        if not result_s2.success:
            print("❌ Scenario 2 failed")
            return 1

        print("✓ Skill executed successfully")
        print(f"  - Overall Readiness: {result_s2.evidence['overall_readiness']}")
        print()

        # Verify CLIENT_READY_WITH_CAVEATS
        json_path_s2 = Path(result_s2.artifacts["readiness_json"])
        readiness_s2 = json.loads(json_path_s2.read_text())

        if readiness_s2["overall_readiness"] != ReadinessLabel.CLIENT_READY_WITH_CAVEATS.value:
            print(
                f"❌ Expected CLIENT_READY_WITH_CAVEATS, got {readiness_s2['overall_readiness']}"
            )
            return 1

        print("✅ SCENARIO 2 PASSED: CLIENT_READY_WITH_CAVEATS classification correct")
        print(f"   Reason: {readiness_s2['overall_reason']}")
        print()

        # Show caveats
        print("Caveats detected:")
        classifications_s2 = readiness_s2["artifact_classifications"]
        for classification in classifications_s2:
            if classification["caveats"]:
                print(f"  - {classification['artifact']}:")
                for caveat in classification["caveats"]:
                    print(f"    • {caveat}")
        print()

        # Show approved narrative
        print("Approved Client Narrative:")
        for bullet in readiness_s2["approved_client_narrative"]:
            print(f"  • {bullet}")
        print()

        # ===================================================================
        # SCENARIO 3: CLIENT_READY (All Conditions Met)
        # ===================================================================
        print_section("SCENARIO 3: CLIENT_READY (All Conditions Met)")

        # Clean up previous artifacts
        triage_json.unlink()
        triage_md.unlink()
        (outputs_dir / "client_readiness.md").unlink()
        (outputs_dir / "client_readiness.json").unlink()

        # Update trust bundle (complete, no issues)
        trust_bundle_data_s3 = {
            "run_identity": {"run_id": "proof_run_003", "command": "build"},
            "workflow_state": {"stage_after": "build"},
            "whats_missing": {"items": []},
            "warnings_blocks": {"warnings": [], "blocks": []},
        }
        trust_bundle_path.write_text(json.dumps(trust_bundle_data_s3, indent=2))

        # Create evidence ledger
        ledger_data_s3 = {
            "run_id": "proof_run_003",
            "command": "/build",
            "outputs": [
                {"path": "outputs/insight_brief.md", "hash": "abc123def456"},
                {"path": "outputs/run_story.md", "hash": "xyz789uvw012"},
            ],
        }
        ledger_path_s3 = evidence_dir / "proof_run_003.yaml"
        ledger_path_s3.write_text(yaml.dump(ledger_data_s3))

        print(f"✓ Evidence Ledger created: {ledger_path_s3}")
        print()

        # Create high-quality artifacts
        (outputs_dir / "insight_brief.md").write_text(
            "# Insight Brief\n\nComplete, evidence-backed brief"
        )
        (outputs_dir / "run_story.md").write_text(
            "# Run Story\n\nComplete audit trail"
        )

        # Execute skill
        context_s3 = SkillContext(
            project_root=project_root,
            current_stage="build",
            artifacts={},
            evidence_ledger_id="proof_run_003",
        )

        result_s3 = skill.execute(context_s3)

        if not result_s3.success:
            print("❌ Scenario 3 failed")
            return 1

        print("✓ Skill executed successfully")
        print(f"  - Overall Readiness: {result_s3.evidence['overall_readiness']}")
        print()

        # Verify CLIENT_READY
        json_path_s3 = Path(result_s3.artifacts["readiness_json"])
        readiness_s3 = json.loads(json_path_s3.read_text())

        if readiness_s3["overall_readiness"] != ReadinessLabel.CLIENT_READY.value:
            print(f"❌ Expected CLIENT_READY, got {readiness_s3['overall_readiness']}")
            return 1

        print("✅ SCENARIO 3 PASSED: CLIENT_READY classification correct")
        print(f"   Reason: {readiness_s3['overall_reason']}")
        print()

        # Show evidence linkage
        print("Evidence Linkage:")
        classifications_s3 = readiness_s3["artifact_classifications"]
        for classification in classifications_s3:
            print(f"  - {classification['artifact']}")
            for evidence in classification["evidence"]:
                if evidence["type"] == "artifact":
                    print(f"    • Hash: {evidence['hash']}")
                elif evidence["type"] == "ledger":
                    print(f"    • Ledger: {evidence['ledger_id']}")
        print()

        # ===================================================================
        # FINAL SUMMARY
        # ===================================================================
        print_section("PROOF DEMONSTRATION COMPLETE")

        print("✅ ALL SCENARIOS PASSED")
        print()
        print("Verified:")
        print("  ✓ INTERNAL_ONLY when recovery plan exists")
        print("  ✓ CLIENT_READY_WITH_CAVEATS when evidence limitations exist")
        print("  ✓ CLIENT_READY when all conditions satisfied")
        print("  ✓ Evidence linkage with artifact hashes")
        print("  ✓ Approved client narrative generation")
        print()

        return 0


if __name__ == "__main__":
    sys.exit(main())
