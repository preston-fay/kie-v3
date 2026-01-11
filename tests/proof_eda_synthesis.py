#!/usr/bin/env python3
"""
Proof Script: EDA Synthesis Generation

Demonstrates:
1. End-to-end workflow: bootstrap → sampledata → eda (triggers eda_synthesis)
2. EDA synthesis generated with all required artifacts
3. All required tables created (top_contributors, distribution_summary, missingness_summary, column_reduction)
4. All required charts created (distributions, contributions, missingness)
5. Markdown has required sections in correct order
6. JSON structure is complete
7. Column reduction produces non-empty decisions
8. Truth Gate passes (all artifacts exist)

EXIT CODES:
- 0: PASS (demonstration successful)
- 1: FAIL (errors encountered)
"""

import json
import sys
import tempfile
from pathlib import Path

from kie.commands.handler import CommandHandler


def print_section(title: str):
    """Print section header."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()


def main() -> int:
    """Run proof demonstration."""
    print_section("EDA SYNTHESIS GENERATION - PROOF DEMONSTRATION")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        print(f"Project Root: {project_root}")
        print()

        handler = CommandHandler(project_root)

        # Step 1: Bootstrap workspace
        print_section("STEP 1: BOOTSTRAP WORKSPACE")

        result = handler.handle_startkie()
        if not result["success"]:
            print(f"❌ Bootstrap failed: {result.get('message')}")
            return 1

        print("✓ Workspace bootstrapped")
        print()

        # Step 2: Install sample data
        print_section("STEP 2: INSTALL SAMPLE DATA")

        result = handler.handle_sampledata(subcommand="install")
        if not result["success"]:
            print(f"❌ Sample data install failed: {result.get('message')}")
            return 1

        print("✓ Sample data installed")
        print()

        # Step 3: Run EDA (should trigger eda_synthesis skill)
        print_section("STEP 3: RUN EDA")

        result = handler.handle_eda()
        if not result["success"]:
            print(f"❌ EDA failed: {result.get('message')}")
            return 1

        print("✓ EDA completed")
        print()

        # Step 4: Verify eda_synthesis.md exists
        print_section("STEP 4: VERIFY EDA SYNTHESIS EXISTS")

        outputs_dir = project_root / "outputs"
        synthesis_md_path = outputs_dir / "eda_synthesis.md"
        synthesis_json_path = outputs_dir / "eda_synthesis.json"

        if not synthesis_md_path.exists():
            print("❌ eda_synthesis.md not found")
            return 1

        if not synthesis_json_path.exists():
            print("❌ eda_synthesis.json not found")
            return 1

        print("✓ eda_synthesis.md exists")
        print("✓ eda_synthesis.json exists")
        print()

        # Step 5: Verify required tables
        print_section("STEP 5: VERIFY REQUIRED TABLES")

        tables_dir = outputs_dir / "eda_tables"
        required_tables = [
            "top_contributors.csv",
            "distribution_summary.csv",
            "missingness_summary.csv",
            "column_reduction.csv"
        ]

        all_tables_present = True
        for table_name in required_tables:
            table_path = tables_dir / table_name
            if table_path.exists():
                print(f"✓ {table_name}")
            else:
                print(f"❌ Missing: {table_name}")
                all_tables_present = False

        if not all_tables_present:
            return 1

        print()

        # Step 6: Verify required charts
        print_section("STEP 6: VERIFY REQUIRED CHARTS")

        charts_dir = outputs_dir / "eda_charts"

        # Distribution charts
        distribution_charts = list(charts_dir.glob("distribution_*.json"))
        if distribution_charts:
            print(f"✓ {len(distribution_charts)} distribution chart(s)")
            for chart in distribution_charts:
                print(f"  - {chart.name}")
        else:
            print("❌ No distribution charts found")
            return 1

        # Contribution charts
        contribution_charts = list(charts_dir.glob("contribution_*.json"))
        if contribution_charts:
            print(f"✓ {len(contribution_charts)} contribution chart(s)")
            for chart in contribution_charts:
                print(f"  - {chart.name}")
        else:
            print("❌ No contribution charts found")
            return 1

        # Missingness heatmap
        missingness_chart = charts_dir / "missingness_heatmap.json"
        if missingness_chart.exists():
            print("✓ missingness_heatmap.json")
        else:
            print("❌ missingness_heatmap.json not found")
            return 1

        print()

        # Step 7: Verify required sections in markdown
        print_section("STEP 7: VERIFY REQUIRED SECTIONS")

        synthesis_md = synthesis_md_path.read_text()

        required_sections = [
            "# EDA Synthesis",
            "## 1. Dataset Overview",
            "## 2. What Dominates",
            "## 3. Distributions & Shape",
            "## 4. Outliers & Anomalies",
            "## 5. Missingness & Data Quality",
            "## 6. Column Reduction (Critical)",
            "## 7. What This Means for Analysis",
        ]

        all_sections_present = True
        for section in required_sections:
            if section in synthesis_md:
                print(f"✓ {section}")
            else:
                print(f"❌ Missing: {section}")
                all_sections_present = False

        if not all_sections_present:
            return 1

        # Verify order
        positions = [synthesis_md.index(section) for section in required_sections]
        if positions == sorted(positions):
            print("✓ Sections in correct order")
        else:
            print("❌ Sections not in correct order")
            return 1

        print()

        # Step 8: Verify JSON structure
        print_section("STEP 8: VERIFY JSON STRUCTURE")

        with open(synthesis_json_path) as f:
            synthesis_json = json.load(f)

        required_fields = [
            "generated_at",
            "dataset_overview",
            "dominance_analysis",
            "distribution_analysis",
            "outlier_analysis",
            "quality_analysis",
            "column_reduction",
            "actionable_insights",
            "metadata",
        ]

        all_fields_present = True
        for field in required_fields:
            if field in synthesis_json:
                print(f"✓ {field}")
            else:
                print(f"❌ Missing: {field}")
                all_fields_present = False

        if not all_fields_present:
            return 1

        print()

        # Step 9: Verify column reduction produces decisions
        print_section("STEP 9: VERIFY COLUMN REDUCTION")

        column_reduction = synthesis_json["column_reduction"]

        keep_count = len(column_reduction["keep"])
        ignore_count = len(column_reduction["ignore"])
        investigate_count = len(column_reduction["investigate"])

        print(f"KEEP: {keep_count} columns")
        for col in column_reduction["keep"]:
            reason = column_reduction["reasons"].get(col, "")
            print(f"  - {col}: {reason}")

        print()
        print(f"IGNORE: {ignore_count} columns")
        for col in column_reduction["ignore"]:
            reason = column_reduction["reasons"].get(col, "")
            print(f"  - {col}: {reason}")

        print()
        print(f"INVESTIGATE: {investigate_count} columns")
        for col in column_reduction["investigate"]:
            reason = column_reduction["reasons"].get(col, "")
            print(f"  - {col}: {reason}")

        total_decisions = keep_count + ignore_count + investigate_count
        if total_decisions == 0:
            print("❌ No column reduction decisions made")
            return 1

        print()
        print(f"✓ Total decisions: {total_decisions} columns classified")
        print()

        # Step 10: Verify actionable insights
        print_section("STEP 10: VERIFY ACTIONABLE INSIGHTS")

        insights = synthesis_json["actionable_insights"]

        if len(insights) == 0:
            print("❌ No actionable insights generated")
            return 1

        print(f"Generated {len(insights)} actionable insights:")
        for i, insight in enumerate(insights, 1):
            print(f"{i}. {insight}")

        print()

        # Step 11: Verify artifact classification
        print_section("STEP 11: VERIFY ARTIFACT CLASSIFICATION")

        if synthesis_json["metadata"]["artifact_classification"] == "INTERNAL":
            print("✓ Artifact marked as INTERNAL")
        else:
            print(f"❌ Artifact classification: {synthesis_json['metadata']['artifact_classification']}")
            return 1

        print()

        # Step 12: Print first ~20 lines of synthesis
        print_section("STEP 12: EDA SYNTHESIS EXCERPT (First ~20 lines)")

        synthesis_lines = synthesis_md.split("\n")
        excerpt_lines = synthesis_lines[:20]

        for line in excerpt_lines:
            print(line)

        if len(synthesis_lines) > 20:
            print(f"\n... ({len(synthesis_lines) - 20} more lines)")

        print()

        # Final Summary
        print_section("PROOF DEMONSTRATION COMPLETE")

        print("✅ ALL CHECKS PASSED")
        print()
        print("Verified:")
        print("  ✓ End-to-end workflow (bootstrap → sampledata → eda)")
        print("  ✓ eda_synthesis.md and .json exist")
        print("  ✓ All required tables created (4 tables)")
        print(f"  ✓ All required charts created ({len(distribution_charts) + len(contribution_charts) + 1} charts)")
        print("  ✓ All required sections present in correct order")
        print("  ✓ JSON structure complete")
        print(f"  ✓ Column reduction: {total_decisions} columns classified")
        print(f"  ✓ {len(insights)} actionable insights generated")
        print("  ✓ Artifact marked as INTERNAL")
        print()

        return 0


if __name__ == "__main__":
    sys.exit(main())
