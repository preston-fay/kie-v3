"""
Validation Pipeline Integration

Integrates validation into the build pipeline to enforce safety checks.
"""

from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

from kie.validation.validators import (
    OutputValidator,
    ValidationResult,
    validate_output,
)
from kie.validation.reports import ValidationReportGenerator, ValidationReport


@dataclass
class ValidationConfig:
    """Configuration for validation pipeline."""

    strict: bool = True  # If True, warnings also block output
    save_reports: bool = True  # Save validation reports
    report_dir: Path = Path("project_state/validation_reports")
    auto_fix: bool = False  # Attempt automatic fixes (future)
    custom_validators: List[Callable] = None  # User-defined validators


class ValidationPipeline:
    """
    Validation pipeline for KIE v3 outputs.

    Enforces safety checks before outputs reach consultants.
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize validation pipeline.

        Args:
            config: Validation configuration
        """
        self.config = config or ValidationConfig()
        self.validator = OutputValidator()
        self.report_generator = ValidationReportGenerator()

        if self.config.save_reports:
            self.config.report_dir.mkdir(parents=True, exist_ok=True)

    def validate_chart(
        self,
        data: pd.DataFrame,
        chart_config: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> ValidationReport:
        """
        Validate chart output.

        Args:
            data: Chart data
            chart_config: Chart configuration
            output_path: Path to chart file

        Returns:
            ValidationReport

        Raises:
            ValidationError if validation fails
        """
        # Run validation
        passed, results, summary = validate_output(
            data=data,
            config=chart_config,
            strict=self.config.strict,
        )

        # Generate report
        report = self.report_generator.generate_report(
            results=results,
            summary=summary,
            output_type="chart",
            output_path=output_path,
        )

        # Save report
        if self.config.save_reports and output_path:
            report_path = self._get_report_path(output_path, "chart")
            self.report_generator.save_report(report, report_path, format="text")

        # Raise if failed
        if not passed:
            self._handle_validation_failure(report)

        return report

    def validate_table(
        self,
        data: pd.DataFrame,
        table_config: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> ValidationReport:
        """
        Validate table output.

        Args:
            data: Table data
            table_config: Table configuration
            output_path: Path to table file

        Returns:
            ValidationReport

        Raises:
            ValidationError if validation fails
        """
        passed, results, summary = validate_output(
            data=data,
            config=table_config,
            strict=self.config.strict,
        )

        report = self.report_generator.generate_report(
            results=results,
            summary=summary,
            output_type="table",
            output_path=output_path,
        )

        if self.config.save_reports and output_path:
            report_path = self._get_report_path(output_path, "table")
            self.report_generator.save_report(report, report_path, format="text")

        if not passed:
            self._handle_validation_failure(report)

        return report

    def validate_slide(
        self,
        slide_config: Dict[str, Any],
        content: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> ValidationReport:
        """
        Validate PowerPoint slide.

        Args:
            slide_config: Slide configuration
            content: Text content (speaker notes, titles)
            output_path: Path to PPTX file

        Returns:
            ValidationReport

        Raises:
            ValidationError if validation fails
        """
        passed, results, summary = validate_output(
            config=slide_config,
            content=content,
            strict=self.config.strict,
        )

        report = self.report_generator.generate_report(
            results=results,
            summary=summary,
            output_type="slide",
            output_path=output_path,
        )

        if self.config.save_reports and output_path:
            report_path = self._get_report_path(output_path, "slide")
            self.report_generator.save_report(report, report_path, format="text")

        if not passed:
            self._handle_validation_failure(report)

        return report

    def validate_dashboard(
        self,
        components: List[Dict[str, Any]],
        output_path: Optional[Path] = None,
    ) -> ValidationReport:
        """
        Validate dashboard (multiple components).

        Args:
            components: List of component configs
            output_path: Path to dashboard files

        Returns:
            ValidationReport

        Raises:
            ValidationError if validation fails
        """
        # Validate each component
        all_results = []
        all_passed = True

        for component in components:
            # Extract data and config
            data = component.get("data")
            config = component.get("config")
            content = component.get("content")

            passed, results, _ = validate_output(
                data=data,
                config=config,
                content=content,
                strict=self.config.strict,
            )

            all_results.extend(results)
            if not passed:
                all_passed = False

        # Generate combined summary
        validator = OutputValidator()
        validator.results = all_results
        summary = validator.get_validation_summary()

        report = self.report_generator.generate_report(
            results=all_results,
            summary=summary,
            output_type="dashboard",
            output_path=output_path,
        )

        if self.config.save_reports and output_path:
            report_path = self._get_report_path(output_path, "dashboard")
            self.report_generator.save_report(report, report_path, format="text")

        if not all_passed:
            self._handle_validation_failure(report)

        return report

    def validate_presentation(
        self,
        slides: List[Dict[str, Any]],
        output_path: Optional[Path] = None,
    ) -> ValidationReport:
        """
        Validate complete PowerPoint presentation.

        Args:
            slides: List of slide configs
            output_path: Path to PPTX file

        Returns:
            ValidationReport

        Raises:
            ValidationError if validation fails
        """
        all_results = []
        all_passed = True

        for slide in slides:
            passed, results, _ = validate_output(
                data=slide.get("data"),
                config=slide.get("config"),
                content=slide.get("content"),
                strict=self.config.strict,
            )

            all_results.extend(results)
            if not passed:
                all_passed = False

        validator = OutputValidator()
        validator.results = all_results
        summary = validator.get_validation_summary()

        report = self.report_generator.generate_report(
            results=all_results,
            summary=summary,
            output_type="presentation",
            output_path=output_path,
        )

        if self.config.save_reports and output_path:
            report_path = self._get_report_path(output_path, "presentation")
            self.report_generator.save_report(report, report_path, format="text")

        if not all_passed:
            self._handle_validation_failure(report)

        return report

    def _get_report_path(self, output_path: Path, output_type: str) -> Path:
        """
        Generate report path based on output path.

        Args:
            output_path: Path to output file
            output_type: Type of output

        Returns:
            Path for validation report
        """
        # Use output filename as base
        base_name = output_path.stem
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

        report_filename = f"{base_name}_{output_type}_validation_{timestamp}.txt"
        return self.config.report_dir / report_filename

    def _handle_validation_failure(self, report: ValidationReport):
        """
        Handle validation failure.

        Args:
            report: Failed validation report

        Raises:
            ValidationError
        """
        # Format error message
        error_lines = [
            "❌ OUTPUT VALIDATION FAILED",
            f"Critical Issues: {report.critical_count}",
            f"Warnings: {report.warning_count}",
            "",
            "This output cannot be delivered to consultants until issues are resolved.",
            "",
        ]

        # Add critical issues
        critical_results = [
            r for r in report.results if r.level.value == "critical" and not r.passed
        ]

        if critical_results:
            error_lines.append("Critical Issues:")
            for result in critical_results:
                error_lines.append(f"  • {result.message}")
                if result.suggestion:
                    error_lines.append(f"    → {result.suggestion}")

        error_msg = "\n".join(error_lines)

        raise ValidationError(error_msg, report)

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validations run in this pipeline.

        Returns:
            Summary statistics
        """
        return self.report_generator.get_summary_dashboard()

    def clear_history(self):
        """Clear validation history."""
        self.report_generator.reports = []


class ValidationError(Exception):
    """
    Raised when validation fails.

    Contains the validation report for inspection.
    """

    def __init__(self, message: str, report: ValidationReport):
        """
        Initialize validation error.

        Args:
            message: Error message
            report: Validation report
        """
        super().__init__(message)
        self.report = report


# Convenience functions
def validate_chart_output(
    data: pd.DataFrame,
    chart_config: Dict[str, Any],
    output_path: Optional[Path] = None,
    strict: bool = True,
) -> ValidationReport:
    """
    Validate chart output.

    Args:
        data: Chart data
        chart_config: Chart configuration
        output_path: Output path
        strict: Strict mode

    Returns:
        ValidationReport

    Raises:
        ValidationError if validation fails
    """
    pipeline = ValidationPipeline(ValidationConfig(strict=strict))
    return pipeline.validate_chart(data, chart_config, output_path)


def validate_table_output(
    data: pd.DataFrame,
    table_config: Dict[str, Any],
    output_path: Optional[Path] = None,
    strict: bool = True,
) -> ValidationReport:
    """
    Validate table output.

    Args:
        data: Table data
        table_config: Table configuration
        output_path: Output path
        strict: Strict mode

    Returns:
        ValidationReport

    Raises:
        ValidationError if validation fails
    """
    pipeline = ValidationPipeline(ValidationConfig(strict=strict))
    return pipeline.validate_table(data, table_config, output_path)


def validate_slide_output(
    slide_config: Dict[str, Any],
    content: Optional[str] = None,
    output_path: Optional[Path] = None,
    strict: bool = True,
) -> ValidationReport:
    """
    Validate slide output.

    Args:
        slide_config: Slide configuration
        content: Text content
        output_path: Output path
        strict: Strict mode

    Returns:
        ValidationReport

    Raises:
        ValidationError if validation fails
    """
    pipeline = ValidationPipeline(ValidationConfig(strict=strict))
    return pipeline.validate_slide(slide_config, content, output_path)
