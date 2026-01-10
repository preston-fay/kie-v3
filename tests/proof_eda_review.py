#!/usr/bin/env python3
"""
Proof script for EDA Review Skill - demonstrates automatic execution after /eda.

Tests the complete flow:
1. Bootstrap workspace
2. Add sample data
3. Run /eda command
4. Verify eda_review.md produced
5. Verify review content matches 6-section structure
6. Verify evidence references present
"""

import sys
import tempfile
from pathlib import Path


def proof_eda_review() -> int:
    """
    Proof that EDA Review skill executes automatically after /eda.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 70)
    print("EDA Review Skill Proof")
    print("=" * 70)
    print()

    # Create temp workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)

        print(f"Test workspace: {workspace}")
        print()

        # Step 1: Bootstrap workspace
        print("=" * 70)
        print("STEP 1: Bootstrap Workspace")
        print("=" * 70)

        from kie.commands.handler import CommandHandler

        handler = CommandHandler(project_root=workspace)
        result = handler.handle_startkie()

        if not result["success"]:
            print(f"❌ FAIL: Bootstrap failed: {result['message']}")
            return 1

        print(f"✓ Workspace created")
        print()

        # Step 2: Create sample data
        print("=" * 70)
        print("STEP 2: Create Sample Data")
        print("=" * 70)

        data_dir = workspace / "data"
        data_file = data_dir / "sample.csv"

        # Create CSV with realistic data
        data_content = """region,product,revenue,cost,date
North,Widget A,125000,80000,2024-01-15
South,Widget B,98000,65000,2024-01-15
East,Widget A,145000,90000,2024-01-15
West,Widget C,110000,70000,2024-01-15
North,Widget B,87000,55000,2024-02-15
South,Widget A,132000,85000,2024-02-15
East,Widget C,95000,60000,2024-02-15
West,Widget A,118000,75000,2024-02-15
"""

        data_file.write_text(data_content)
        print(f"✓ Created sample data: {data_file}")
        print(f"  Rows: 8, Columns: 5")
        print()

        # Step 3: Run /eda command
        print("=" * 70)
        print("STEP 3: Run /eda Command")
        print("=" * 70)

        eda_result = handler.handle_eda()

        if not eda_result["success"]:
            print(f"❌ FAIL: EDA failed: {eda_result.get('message', 'Unknown error')}")
            return 1

        print(f"✓ EDA completed successfully")
        print(f"  Data file: {eda_result['data_file']}")
        print(f"  Profile saved: {eda_result['profile_saved']}")
        print()

        # Step 4: Verify eda_review.md produced
        print("=" * 70)
        print("STEP 4: Verify EDA Review Artifact Produced")
        print("=" * 70)

        review_path = workspace / "outputs" / "eda_review.md"

        if not review_path.exists():
            print(f"❌ FAIL: eda_review.md not found at {review_path}")
            return 1

        print(f"✓ eda_review.md exists at: {review_path}")
        print()

        # Step 5: Verify review content structure
        print("=" * 70)
        print("STEP 5: Verify Review Content Structure")
        print("=" * 70)

        review_content = review_path.read_text()

        required_sections = [
            "# EDA Review (Internal)",
            "## 1. Data Overview",
            "## 2. Data Quality Assessment",
            "## 3. Key Patterns & Early Signals",
            "## 4. Anomalies & Outliers",
            "## 5. Analytical Implications",
            "## 6. Recommended Next Analytical Questions",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in review_content:
                missing_sections.append(section)

        if missing_sections:
            print(f"❌ FAIL: Missing required sections:")
            for section in missing_sections:
                print(f"  - {section}")
            return 1

        print("✓ All 6 required sections present:")
        for section in required_sections:
            print(f"  ✓ {section}")
        print()

        # Step 6: Verify evidence references
        print("=" * 70)
        print("STEP 6: Verify Evidence-Backed Claims")
        print("=" * 70)

        # Check for internal-only marker
        if "INTERNAL THINKING ARTIFACT" not in review_content:
            print("❌ FAIL: Missing 'INTERNAL THINKING ARTIFACT' marker")
            return 1

        print("✓ Internal-only marker present")

        # Check for data file reference
        if "sample.csv" not in review_content and "data/" not in review_content:
            print("❌ FAIL: Review does not reference data source")
            return 1

        print("✓ Data source referenced")

        # Check for quantitative evidence
        if "8 rows" not in review_content:
            print("❌ FAIL: Review missing row count evidence")
            return 1

        print("✓ Quantitative evidence present (row count: 8)")

        # Check for column counts
        if "5 columns" not in review_content:
            print("❌ FAIL: Review missing column count evidence")
            return 1

        print("✓ Column count evidence present (5 columns)")

        # Check for recommended questions section has content
        if "Recommended Next Analytical Questions" in review_content:
            # Find section and check for numbered questions
            lines = review_content.split("\n")
            questions_section_found = False
            has_questions = False

            for line in lines:
                if "## 6. Recommended Next Analytical Questions" in line:
                    questions_section_found = True
                elif questions_section_found and line.strip().startswith(("1.", "2.", "3.")):
                    has_questions = True
                    break

            if not has_questions:
                print("❌ FAIL: Recommended Questions section has no numbered questions")
                return 1

            print("✓ Recommended analytical questions present")

        print()

        # Step 7: Verify JSON artifact
        print("=" * 70)
        print("STEP 7: Verify JSON Artifact")
        print("=" * 70)

        json_path = workspace / "outputs" / "eda_review.json"

        if not json_path.exists():
            print(f"❌ FAIL: eda_review.json not found at {json_path}")
            return 1

        print(f"✓ eda_review.json exists")

        import json

        review_data = json.loads(json_path.read_text())

        if not review_data.get("internal_only"):
            print("❌ FAIL: JSON missing internal_only flag")
            return 1

        print("✓ internal_only flag set to True")

        required_json_keys = ["overview", "quality", "analytical_readiness"]
        missing_keys = [k for k in required_json_keys if k not in review_data]

        if missing_keys:
            print(f"❌ FAIL: JSON missing required keys: {missing_keys}")
            return 1

        print("✓ All required JSON keys present")
        print()

        # Final summary
        print("=" * 70)
        print("✅ ALL CHECKS PASSED")
        print("=" * 70)
        print()
        print("EDA Review Skill correctly:")
        print("- Executes automatically after /eda command")
        print("- Produces eda_review.md with 6 required sections")
        print("- Produces eda_review.json with structured data")
        print("- References data source and profiling statistics")
        print("- Marks artifact as INTERNAL ONLY")
        print("- Provides evidence-backed content")
        print("- Recommends analytical questions")

        return 0


if __name__ == "__main__":
    sys.exit(proof_eda_review())
