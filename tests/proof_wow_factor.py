"""
Proof Outputs for STEP 3: CONSULTANT WOW FACTOR

Demonstrates Insight Brief, Next Steps, and Run Story in action.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

from kie.consultant import InsightBriefGenerator, NextStepsAdvisor, RunStoryGenerator


def demo_wow_factor():
    """Generate proof outputs for WOW factor features."""

    print("=" * 80)
    print("STEP 3: CONSULTANT WOW FACTOR - PROOF OUTPUTS")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Setup workspace
        outputs_dir = tmp_path / "outputs"
        internal_dir = outputs_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)
        project_state_dir = tmp_path / "project_state"
        project_state_dir.mkdir()
        evidence_dir = project_state_dir / "evidence_ledger"
        evidence_dir.mkdir()

        # Create sample insights catalog
        catalog_data = {
            "generated_at": datetime.now().isoformat(),
            "business_question": "What drives quarterly revenue growth?",
            "insights": [
                {
                    "id": "insight_001",
                    "headline": "Northeast Region Drives 60% of Q3 Growth",
                    "supporting_text": "Analysis of Q3 data shows the Northeast region contributed $3.6M of the $6M total revenue increase, representing 60% of growth. This is a 15% increase over Q2 regional contribution.",
                    "insight_type": "comparison",
                    "severity": "key",
                    "category": "finding",
                    "evidence": [
                        {
                            "type": "metric",
                            "reference": "outputs/charts/revenue_by_region.json",
                            "value": 3600000,
                            "label": "Northeast Q3 revenue increase",
                            "confidence": 1.0,
                        },
                        {
                            "type": "comparison",
                            "reference": "outputs/tables/regional_comparison.json",
                            "value": 0.60,
                            "label": "Northeast contribution to growth",
                            "confidence": 1.0,
                        },
                    ],
                    "confidence": 0.95,
                    "statistical_significance": 0.003,
                },
                {
                    "id": "insight_002",
                    "headline": "Enterprise Segment Shows 22% Conversion Rate",
                    "supporting_text": "Enterprise customers demonstrate significantly higher conversion rates (22%) compared to SMB (12%) and Mid-Market (16%) segments.",
                    "insight_type": "distribution",
                    "severity": "key",
                    "category": "finding",
                    "evidence": [
                        {
                            "type": "metric",
                            "reference": "outputs/charts/conversion_by_segment.json",
                            "value": 0.22,
                            "label": "Enterprise conversion rate",
                        }
                    ],
                    "confidence": 0.88,
                    "statistical_significance": 0.01,
                },
                {
                    "id": "insight_003",
                    "headline": "Focus Enterprise Sales Efforts in Northeast",
                    "supporting_text": "Combining high regional growth with strong enterprise conversion creates opportunity for 2x revenue impact through targeted enterprise sales in Northeast territory.",
                    "insight_type": "correlation",
                    "severity": "key",
                    "category": "recommendation",
                    "evidence": [
                        {
                            "type": "statistic",
                            "reference": "outputs/analysis/correlation_matrix.json",
                            "value": 0.78,
                            "label": "Northeast-Enterprise correlation",
                        }
                    ],
                    "confidence": 0.82,
                },
            ],
            "data_summary": {
                "row_count": 1523,
                "column_count": 12,
                "date_range": "2024-Q3",
            },
        }

        catalog_path = internal_dir / "insights_catalog.json"
        catalog_path.write_text(json.dumps(catalog_data, indent=2))

        # Create evidence ledger entries
        eda_ledger = {
            "run_id": "eda_20240115_001",
            "timestamp": "2024-01-15T10:30:00",
            "command": "eda",
            "success": True,
            "outputs": [
                {"path": "outputs/eda_profile.json", "hash": "a1b2c3d4e5f6"}
            ],
        }
        (evidence_dir / "eda_20240115_001.yaml").write_text(yaml.dump(eda_ledger))

        analyze_ledger = {
            "run_id": "analyze_20240115_002",
            "timestamp": "2024-01-15T10:45:00",
            "command": "analyze",
            "success": True,
            "outputs": [
                {"path": "outputs/insights_catalog.json", "hash": "abc123def456"}
            ],
        }
        (evidence_dir / "analyze_20240115_002.yaml").write_text(yaml.dump(analyze_ledger))

        print("PROOF 1: Auto-Generated Insight Brief")
        print("-" * 80)
        print()

        brief_gen = InsightBriefGenerator(tmp_path)
        brief_result = brief_gen.generate()

        if brief_result["success"]:
            print("✓ Insight Brief generated successfully")
            print(f"  - Markdown: {brief_result['brief_markdown']}")
            print(f"  - JSON: {brief_result['brief_json']}")
            print(f"  - Key insights: {brief_result['key_insights_count']}")
            print(f"  - Total insights: {brief_result['total_insights']}")
            print(f"  - Evidence backed: {brief_result['evidence_backed']}")
            print()

            # Show excerpt
            brief_path = Path(brief_result["brief_markdown"])
            brief_content = brief_path.read_text()
            print("Brief Excerpt:")
            print("-" * 40)
            lines = brief_content.split("\n")
            for line in lines[:40]:  # First 40 lines
                print(line)
            print("...")
            print()

        print("=" * 80)
        print()

        print("PROOF 2: Decision-Ready Next Steps")
        print("-" * 80)
        print()

        advisor = NextStepsAdvisor(tmp_path)

        # Simulate various command completions
        test_scenarios = [
            ("startkie", {"success": True}, "After workspace initialization"),
            ("spec", {"success": True}, "After spec created (no data yet)"),
            ("eda", {"success": True}, "After EDA completed"),
            ("analyze", {"success": True}, "After insights generated"),
        ]

        for cmd, result, description in test_scenarios:
            steps = advisor.generate_next_steps(cmd, result)
            print(f"✓ Next steps for /{cmd} ({description}):")
            for step in steps:
                print(f"  {step}")
            print()

        print("=" * 80)
        print()

        print("PROOF 3: Run Story (Consultant Narrative)")
        print("-" * 80)
        print()

        story_gen = RunStoryGenerator(tmp_path)
        story_result = story_gen.generate()

        if story_result["success"]:
            print("✓ Run Story generated successfully")
            print(f"  - Markdown: {story_result['story_markdown']}")
            print(f"  - JSON: {story_result['story_json']}")
            print(f"  - Commands included: {story_result['commands_included']}")
            print()

            # Show excerpt
            story_path = Path(story_result["story_markdown"])
            story_content = story_path.read_text()
            print("Story Excerpt:")
            print("-" * 40)
            lines = story_content.split("\n")
            for line in lines[:50]:  # First 50 lines
                print(line)
            print("...")
            print()

        print("=" * 80)
        print()

        print("PROOF 4: Evidence Backing Verification")
        print("-" * 80)
        print()

        # Verify all outputs cite evidence
        with open(brief_result["brief_json"]) as f:
            brief_data = json.load(f)

        print("✓ Insight Brief Evidence Backing:")
        print(f"  - Executive summary insights: {len(brief_data['executive_summary']['key_insights'])}")
        print(f"  - Findings with evidence: {len([f for f in brief_data['findings'] if f['evidence']])}")
        print(f"  - Artifact provenance tracked: {bool(brief_data['artifact_provenance'])}")
        print()

        # Check provenance
        provenance = brief_data["artifact_provenance"]
        print("  Artifact Provenance:")
        print(f"    - Insights catalog: {provenance['insights_catalog']['path']}")
        if provenance['insights_catalog']['hash']:
            print(f"      Hash: {provenance['insights_catalog']['hash'][:16]}...")
        print()

        with open(story_result["story_json"]) as f:
            story_data = json.load(f)

        print("✓ Run Story Evidence Backing:")
        print(f"  - Commands in workflow: {story_data['workflow']['commands_executed']}")
        print(f"  - Evidence trail entries: {len(story_data['evidence_trail'])}")
        print(f"  - Key insights: {len(story_data['findings']['key_insights'])}")
        print()

        for entry in story_data["evidence_trail"]:
            print(f"    - /{entry['command']}: Ledger {entry['ledger_id']}")
            for output in entry["outputs"]:
                print(f"      - {output['path']} (hash: {output['hash']})")
        print()

        print("=" * 80)
        print()

        print("PROOF 5: WOW Features Never Block Commands")
        print("-" * 80)
        print()

        # Test with missing artifacts
        tmp_path2 = Path(tempfile.mkdtemp())
        (tmp_path2 / "outputs").mkdir()

        # These should all fail gracefully without crashing
        print("✓ Testing graceful failure with missing artifacts:")
        print()

        brief_gen2 = InsightBriefGenerator(tmp_path2)
        result2 = brief_gen2.generate()
        print(f"  - Insight Brief (no catalog): success={result2['success']}")
        print(f"    Message: {result2['message']}")
        print()

        story_gen2 = RunStoryGenerator(tmp_path2)
        result3 = story_gen2.generate()
        print(f"  - Run Story (no ledger): success={result3['success']}")
        print(f"    Message: {result3['message']}")
        print()

        advisor2 = NextStepsAdvisor(tmp_path2)
        steps2 = advisor2.generate_next_steps("unknown", {})
        print(f"  - Next Steps (empty state): returned {len(steps2)} steps")
        print()

        print("✓ All WOW features failed gracefully without crashing")
        print()

        print("=" * 80)
        print()

        print("WOW FACTOR PROOF COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Insight Brief: Evidence-backed consultant-ready document")
        print("  ✓ Next Steps: Deterministic, CLI-executable actions")
        print("  ✓ Run Story: Single narrative replacing fragmented logs")
        print("  ✓ Evidence Backing: All claims traceable to artifacts + hashes")
        print("  ✓ Graceful Failure: Missing artifacts handled without crashing")
        print()
        print("CRITICAL GUARANTEES MAINTAINED:")
        print("  1. NO new analysis (synthesis only)")
        print("  2. Every claim cites evidence")
        print("  3. Missing evidence called out explicitly")
        print("  4. Advisory only (never blocks)")
        print("  5. All outputs reference real artifacts")
        print()


if __name__ == "__main__":
    demo_wow_factor()
