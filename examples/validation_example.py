"""
Validation System Example

Demonstrates KIE v3's comprehensive quality control system.
"""

import pandas as pd
from pathlib import Path

from kie.validation.pipeline import (
    ValidationPipeline,
    ValidationConfig,
    ValidationError,
)
from kie.charts import ChartFactory
from kie.tables import TableFactory


def main():
    """Run validation examples."""

    print("🔍 KIE v3 Validation System Example")
    print("=" * 60)

    output_dir = Path("outputs/validation_examples")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize pipeline
    pipeline = ValidationPipeline(
        ValidationConfig(
            strict=True,
            save_reports=True,
            report_dir=Path("project_state/validation_reports"),
        )
    )

    # =========================================================================
    # EXAMPLE 1: Good Data (Should Pass)
    # =========================================================================
    print("\n1️⃣  Validating Clean Data (Expected: PASS)")

    good_data = pd.DataFrame(
        {
            "region": ["North", "South", "East", "West"],
            "revenue": [1250000, 980000, 1450000, 1100000],
            "growth": [0.155, 0.123, 0.187, 0.142],
        }
    )

    chart_config = ChartFactory.bar(
        data=good_data.to_dict("records"),
        x="region",
        y=["revenue"],
        title="Regional Revenue",
    )

    try:
        report = pipeline.validate_chart(
            data=good_data,
            chart_config=chart_config.to_dict(),
            output_path=output_dir / "good_chart.json",
        )

        print(f"   ✅ Validation PASSED")
        print(f"   • Critical: {report.critical_count}")
        print(f"   • Warnings: {report.warning_count}")
        print(f"   • Info: {report.info_count}")

    except ValidationError as e:
        print(f"   ❌ Validation FAILED: {e}")

    # =========================================================================
    # EXAMPLE 2: Synthetic Data (Should Fail)
    # =========================================================================
    print("\n2️⃣  Validating Synthetic Data (Expected: FAIL)")

    synthetic_data = pd.DataFrame(
        {
            "customer": ["Customer 1", "Customer 2", "Test Corp", "Sample Inc"],
            "revenue": [1000000, 2000000, 3000000, 4000000],  # All round thousands
            "id": [1, 2, 3, 4],  # Sequential
        }
    )

    try:
        report = pipeline.validate_chart(
            data=synthetic_data,
            chart_config={"type": "bar"},
            output_path=output_dir / "synthetic_chart.json",
        )

        print(f"   ❌ Unexpectedly passed validation")

    except ValidationError as e:
        print(f"   ✅ Correctly BLOCKED synthetic data")
        print(f"   • Critical issues detected:")
        for result in e.report.results:
            if result.level.value == "critical" and not result.passed:
                print(f"     - {result.message}")

    # =========================================================================
    # EXAMPLE 3: Brand Violation (Should Fail)
    # =========================================================================
    print("\n3️⃣  Validating Brand Violation (Expected: FAIL)")

    good_data_bad_colors = pd.DataFrame(
        {
            "category": ["A", "B", "C"],
            "value": [100, 200, 150],
        }
    )

    # Intentionally use forbidden green color
    bad_config = {
        "type": "bar",
        "colors": ["#00FF00", "#008000"],  # Forbidden greens
        "grid": {"show": True},  # Forbidden gridlines
    }

    try:
        report = pipeline.validate_chart(
            data=good_data_bad_colors,
            chart_config=bad_config,
            output_path=output_dir / "brand_violation_chart.json",
        )

        print(f"   ❌ Unexpectedly passed validation")

    except ValidationError as e:
        print(f"   ✅ Correctly BLOCKED brand violations")
        print(f"   • Brand compliance issues:")
        for result in e.report.results:
            if result.category.value == "brand_compliance" and not result.passed:
                print(f"     - {result.message}")

    # =========================================================================
    # EXAMPLE 4: Data Quality Issues (Should Warn)
    # =========================================================================
    print("\n4️⃣  Validating Data Quality Issues (Expected: WARNINGS)")

    quality_issues_data = pd.DataFrame(
        {
            "product": ["Widget A", "Widget B", "Widget C", "Widget D"],
            "sales": [100, 200, 150, 100],
            "margin": [0.5, None, 0.5, 0.5],  # 25% nulls
            "empty_col": [None, None, None, None],  # All nulls
        }
    )

    try:
        # Use non-strict mode to allow warnings
        lenient_pipeline = ValidationPipeline(ValidationConfig(strict=False))

        report = lenient_pipeline.validate_chart(
            data=quality_issues_data,
            chart_config={"type": "bar"},
            output_path=output_dir / "quality_issues_chart.json",
        )

        print(f"   ⚠️  Validation PASSED with warnings")
        print(f"   • Critical: {report.critical_count}")
        print(f"   • Warnings: {report.warning_count}")

        if report.warning_count > 0:
            print(f"   • Warning details:")
            for result in report.results:
                if result.level.value == "warning" and not result.passed:
                    print(f"     - {result.message}")

    except ValidationError as e:
        print(f"   ❌ Validation FAILED: {e}")

    # =========================================================================
    # EXAMPLE 5: Table Validation
    # =========================================================================
    print("\n5️⃣  Validating Table Output (Expected: PASS)")

    table_data = [
        {"product": "Widget A", "revenue": 450000, "growth": 0.15},
        {"product": "Widget B", "revenue": 380000, "growth": 0.12},
        {"product": "Widget C", "revenue": 520000, "growth": 0.18},
    ]

    table_config = TableFactory.standard(table_data, title="Product Performance")

    try:
        report = pipeline.validate_table(
            data=pd.DataFrame(table_data),
            table_config=table_config.model_dump(),
            output_path=output_dir / "product_table.json",
        )

        print(f"   ✅ Validation PASSED")
        print(f"   • All checks passed")

    except ValidationError as e:
        print(f"   ❌ Validation FAILED: {e}")

    # =========================================================================
    # EXAMPLE 6: Content Validation
    # =========================================================================
    print("\n6️⃣  Validating Content (Expected: FAIL)")

    bad_content = """
    This is a TODO: placeholder text that needs to be replaced.
    Lorem ipsum dolor sit amet.
    Contact us at test@example.com
    """

    slide_config = {
        "type": "content",
        "title": "Action Title",
        "background": "#1E1E1E",
        "text_color": "#FFFFFF",
    }

    try:
        report = pipeline.validate_slide(
            slide_config=slide_config,
            content=bad_content,
            output_path=output_dir / "content_slide.pptx",
        )

        print(f"   ❌ Unexpectedly passed validation")

    except ValidationError as e:
        print(f"   ✅ Correctly BLOCKED placeholder content")
        print(f"   • Content issues:")
        for result in e.report.results:
            if result.category.value == "content" and not result.passed:
                print(f"     - {result.message}")

    # =========================================================================
    # Pipeline Summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("📊 Validation Pipeline Summary")
    print("=" * 60)

    summary = pipeline.get_pipeline_summary()

    print(f"Total Validations: {summary['total_reports']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']:.1%}")
    print("")
    print(f"Total Issues Found:")
    print(f"  • Critical: {summary['total_issues']['critical']}")
    print(f"  • Warnings: {summary['total_issues']['warning']}")
    print(f"  • Info: {summary['total_issues']['info']}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("✅ Validation examples complete!")
    print("\n📁 Validation reports saved to: project_state/validation_reports/")
    print("\n💡 Key Features Demonstrated:")
    print("   • Synthetic data detection (test names, sequential IDs)")
    print("   • Brand compliance enforcement (colors, gridlines)")
    print("   • Data quality checks (nulls, duplicates, suspicious values)")
    print("   • Content validation (placeholders, profanity)")
    print("   • Calculation validation (infinity, overflow, negatives)")
    print("   • Accessibility checks (font sizes, contrast)")
    print("\n⚠️  CRITICAL: All outputs are validated before consultant delivery")
    print("   No output reaches consultants without passing validation!")


if __name__ == "__main__":
    main()
