# /validate - Output Validation (KIE v3)

---
name: validate
description: Run comprehensive quality checks on outputs
---

Run KIE v3's validation system to ensure output safety before consultant delivery.

## Usage

```
/validate                  # Validate all outputs
/validate chart <path>     # Validate specific chart
/validate table <path>     # Validate specific table
/validate slide <path>     # Validate specific slide
/validate --reports        # Show validation reports
```

## Critical Importance

⚠️ **NEVER deliver outputs to consultants without validation!**

The validation system prevents:
- Synthetic/fake data (test names, sequential IDs)
- Brand violations (green colors, gridlines)
- Data quality issues (nulls, duplicates, errors)
- Content problems (placeholders, profanity)
- Calculation errors (infinity, overflow, negatives)
- Accessibility violations (font sizes, contrast)

## Implementation

```python
from pathlib import Path
from kie.validation import ValidationPipeline, ValidationConfig

# Initialize pipeline
pipeline = ValidationPipeline(
    ValidationConfig(
        strict=True,  # Warnings also block output
        save_reports=True,
        report_dir=Path("project_state/validation_reports"),
    )
)

print("\n🔍 KIE v3 Validation System")
print("=" * 60)

# Get validation summary
summary = pipeline.get_pipeline_summary()

if summary["total_reports"] == 0:
    print("No validation reports found.")
    print()
    print("Validation reports are created when you:")
    print("  • Generate charts with validation enabled")
    print("  • Create tables with validation enabled")
    print("  • Build presentations with validation enabled")
    print()

else:
    print(f"Total Validations: {summary['total_reports']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']:.1%}")
    print()

    if summary['total_issues']['critical'] > 0:
        print(f"⚠️  CRITICAL ISSUES: {summary['total_issues']['critical']}")
        print("   These MUST be fixed before consultant delivery!")
        print()

    if summary['total_issues']['warning'] > 0:
        print(f"⚠️  Warnings: {summary['total_issues']['warning']}")
        print()

    if summary['total_issues']['info'] > 0:
        print(f"ℹ️  Info: {summary['total_issues']['info']}")
        print()

    # By output type
    if summary.get('by_output_type'):
        print("By Output Type:")
        for output_type, counts in summary['by_output_type'].items():
            total = counts['passed'] + counts['failed']
            print(f"  • {output_type}: {counts['passed']}/{total} passed")
        print()

    # By category
    if summary.get('by_category'):
        print("By Category:")
        for category, counts in summary['by_category'].items():
            if counts['failed'] > 0:
                print(f"  ⚠️  {category}: {counts['failed']} issues")
        print()

print("=" * 60)
print()

# Show recent reports
reports_dir = Path("project_state/validation_reports")
if reports_dir.exists():
    reports = sorted(reports_dir.glob("*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)

    if reports:
        print("Recent Validation Reports:")
        for report in reports[:5]:  # Show 5 most recent
            print(f"  • {report.name}")
        print()
        print("To view a report:")
        print(f"  Read {reports[0]}")
```

## Validation Levels

**CRITICAL** (Blocks Output):
- Synthetic/fake data detected
- Forbidden colors (greens)
- Gridlines present
- Infinity/NaN values
- Placeholder text
- Profanity

**WARNING** (Allows with Alert):
- High null percentage (>50%)
- Duplicate rows
- Suspicious values (all zeros, all same)
- Extreme values
- Long sentences (>40 words)

**INFO** (Informational):
- Readability suggestions
- Optimization opportunities

## Validation Categories

1. **Data Quality**: Nulls, duplicates, suspicious patterns
2. **Synthetic Data**: Test names, sequential IDs, round numbers
3. **Brand Compliance**: Colors, gridlines, fonts
4. **Calculations**: Infinity, overflow, impossible values
5. **Content**: Placeholders, profanity, readability
6. **Accessibility**: Font sizes, contrast ratios

## Example: Validating a Chart

```python
import pandas as pd
from kie.validation import validate_chart_output

# Your data and config
data = pd.DataFrame({
    'region': ['North', 'South', 'East', 'West'],
    'revenue': [1250000, 980000, 1450000, 1100000]
})

chart_config = {
    'type': 'bar',
    'colors': ['#7823DC', '#9B4DCA'],  # KDS colors
    'grid': {'show': False}  # No gridlines
}

try:
    report = validate_chart_output(
        data=data,
        chart_config=chart_config,
        output_path=Path('outputs/charts/revenue.json'),
        strict=True
    )

    print("✅ Validation passed!")
    print(f"Checks run: {report.critical_count + report.warning_count + report.info_count}")

except ValidationError as e:
    print("❌ Validation failed!")
    print(e.report.format_text_report())
```

## Validation Reports

Reports are saved to:
```
project_state/validation_reports/
  {filename}_{type}_validation_{timestamp}.txt
```

Each report contains:
- Overall pass/fail status
- Critical issues (if any)
- Warnings (if any)
- Informational notes
- Category breakdown
- Suggestions for fixes

## Integration

Validation is automatically triggered when:
- `/build` command runs
- Charts/tables/slides are generated
- Exports are created

You can also run validation manually:
- `/validate` - Check everything
- During development for QC

## Strict vs. Lenient Mode

**Strict Mode** (default):
- Warnings block output
- Ensures highest quality
- Recommended for consultant delivery

**Lenient Mode**:
- Only critical issues block
- Warnings allowed
- Useful during development

## Next Steps

After validation:
- All passed → `/build` or `/preview`
- Critical failures → Fix issues and re-validate
- Warnings → Review and decide if fixes needed
