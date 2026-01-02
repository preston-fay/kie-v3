"""
KIE v3 Validation System

Comprehensive quality control to ensure output safety before consultant delivery.

Critical Safety Layer:
- Synthetic data detection (prevents test/fake data delivery)
- Brand compliance enforcement (KDS colors, no gridlines)
- Data quality validation (nulls, duplicates, calculations)
- Content validation (placeholders, profanity, readability)
- Accessibility compliance (WCAG 2.1 AA)

Usage:
    from kie.validation import ValidationPipeline, ValidationConfig

    # Initialize pipeline
    pipeline = ValidationPipeline(ValidationConfig(strict=True))

    # Validate chart
    report = pipeline.validate_chart(data, config, output_path)

    # Validate table
    report = pipeline.validate_table(data, config, output_path)

    # Validate slide
    report = pipeline.validate_slide(config, content, output_path)

All validations produce detailed reports and will raise ValidationError
if critical issues are found, preventing unsafe output delivery.
"""

from kie.validation.validators import (
    OutputValidator,
    ValidationLevel,
    ValidationCategory,
    ValidationResult,
    validate_output,
)

from kie.validation.reports import (
    ValidationReport,
    ValidationReportGenerator,
    generate_validation_report,
)

from kie.validation.pipeline import (
    ValidationPipeline,
    ValidationConfig,
    ValidationError,
    validate_chart_output,
    validate_table_output,
    validate_slide_output,
)

__all__ = [
    # Validators
    "OutputValidator",
    "ValidationLevel",
    "ValidationCategory",
    "ValidationResult",
    "validate_output",
    # Reports
    "ValidationReport",
    "ValidationReportGenerator",
    "generate_validation_report",
    # Pipeline
    "ValidationPipeline",
    "ValidationConfig",
    "ValidationError",
    "validate_chart_output",
    "validate_table_output",
    "validate_slide_output",
]
