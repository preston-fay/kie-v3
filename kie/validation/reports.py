"""
Validation Report Generator

Creates human-readable validation reports for consultant review.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from kie.validation.validators import ValidationLevel, ValidationResult


@dataclass
class ValidationReport:
    """Complete validation report."""

    timestamp: datetime
    output_type: str  # 'chart', 'table', 'slide', 'dashboard'
    output_path: Path | None
    overall_passed: bool
    critical_count: int
    warning_count: int
    info_count: int
    results: list[ValidationResult]
    summary: dict[str, Any]


class ValidationReportGenerator:
    """
    Generate validation reports for consultant review.

    Creates both text and structured formats.
    """

    def __init__(self):
        """Initialize report generator."""
        self.reports: list[ValidationReport] = []

    def generate_report(
        self,
        results: list[ValidationResult],
        summary: dict[str, Any],
        output_type: str,
        output_path: Path | None = None,
    ) -> ValidationReport:
        """
        Generate validation report.

        Args:
            results: List of validation results
            summary: Validation summary dict
            output_type: Type of output validated
            output_path: Path to output file

        Returns:
            ValidationReport object
        """
        critical_count = summary["by_level"]["critical"]
        warning_count = summary["by_level"]["warning"]
        info_count = summary["by_level"]["info"]

        report = ValidationReport(
            timestamp=datetime.now(),
            output_type=output_type,
            output_path=output_path,
            overall_passed=summary["overall_pass"],
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            results=results,
            summary=summary,
        )

        self.reports.append(report)
        return report

    def format_text_report(self, report: ValidationReport) -> str:
        """
        Format report as text.

        Args:
            report: ValidationReport object

        Returns:
            Formatted text report
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("KIE v3 OUTPUT VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Output Type: {report.output_type}")
        if report.output_path:
            lines.append(f"Output Path: {report.output_path}")
        lines.append("")

        # Overall Status
        status_symbol = "✅" if report.overall_passed else "❌"
        status_text = "PASSED" if report.overall_passed else "FAILED"
        lines.append(f"Overall Status: {status_symbol} {status_text}")
        lines.append("")

        # Summary Counts
        lines.append("Validation Summary:")
        lines.append(f"  • Critical Issues: {report.critical_count}")
        lines.append(f"  • Warnings: {report.warning_count}")
        lines.append(f"  • Info: {report.info_count}")
        lines.append("")

        # Critical Issues (if any)
        if report.critical_count > 0:
            lines.append("=" * 80)
            lines.append("⚠️  CRITICAL ISSUES - MUST FIX BEFORE DELIVERY")
            lines.append("=" * 80)

            critical_results = [
                r
                for r in report.results
                if r.level == ValidationLevel.CRITICAL and not r.passed
            ]

            for i, result in enumerate(critical_results, 1):
                lines.append(f"\n{i}. {result.message}")
                lines.append(f"   Category: {result.category.value}")
                if result.details:
                    lines.append(f"   Details: {result.details}")
                if result.suggestion:
                    lines.append(f"   → {result.suggestion}")
            lines.append("")

        # Warnings (if any)
        if report.warning_count > 0:
            lines.append("=" * 80)
            lines.append("⚠️  WARNINGS - RECOMMENDED FIXES")
            lines.append("=" * 80)

            warning_results = [
                r
                for r in report.results
                if r.level == ValidationLevel.WARNING and not r.passed
            ]

            for i, result in enumerate(warning_results, 1):
                lines.append(f"\n{i}. {result.message}")
                lines.append(f"   Category: {result.category.value}")
                if result.suggestion:
                    lines.append(f"   → {result.suggestion}")
            lines.append("")

        # Info (if any)
        if report.info_count > 0:
            lines.append("=" * 80)
            lines.append("ℹ️  INFORMATIONAL")
            lines.append("=" * 80)

            info_results = [
                r
                for r in report.results
                if r.level == ValidationLevel.INFO and not r.passed
            ]

            for i, result in enumerate(info_results, 1):
                lines.append(f"\n{i}. {result.message}")
                if result.suggestion:
                    lines.append(f"   → {result.suggestion}")
            lines.append("")

        # By Category Breakdown
        lines.append("=" * 80)
        lines.append("VALIDATION BY CATEGORY")
        lines.append("=" * 80)

        for category, counts in report.summary["by_category"].items():
            passed = counts["passed"]
            failed = counts["failed"]
            total = passed + failed

            status = "✅" if failed == 0 else "⚠️"
            lines.append(f"{status} {category.replace('_', ' ').title()}: {passed}/{total} passed")

        lines.append("")

        # Next Steps
        lines.append("=" * 80)
        lines.append("NEXT STEPS")
        lines.append("=" * 80)

        if report.overall_passed:
            lines.append("✅ Output passed all critical validations")
            lines.append("   → Safe to deliver to consultant")
            if report.warning_count > 0:
                lines.append("   → Review warnings for potential improvements")
        else:
            lines.append("❌ Output FAILED validation")
            lines.append(f"   → Fix {report.critical_count} critical issue(s) before delivery")
            lines.append("   → Run validation again after fixes")
            lines.append("")
            lines.append("⚠️  DO NOT DELIVER TO CONSULTANT UNTIL ALL CRITICAL ISSUES ARE RESOLVED")

        lines.append("=" * 80)

        return "\n".join(lines)

    def format_json_report(self, report: ValidationReport) -> dict[str, Any]:
        """
        Format report as JSON.

        Args:
            report: ValidationReport object

        Returns:
            Dict suitable for JSON serialization
        """
        return {
            "timestamp": report.timestamp.isoformat(),
            "output_type": report.output_type,
            "output_path": str(report.output_path) if report.output_path else None,
            "overall_passed": report.overall_passed,
            "counts": {
                "critical": report.critical_count,
                "warning": report.warning_count,
                "info": report.info_count,
            },
            "results": [
                {
                    "passed": r.passed,
                    "level": r.level.value,
                    "category": r.category.value,
                    "message": r.message,
                    "details": r.details,
                    "suggestion": r.suggestion,
                }
                for r in report.results
            ],
            "summary": report.summary,
        }

    def save_report(self, report: ValidationReport, output_path: Path, format: str = "text"):
        """
        Save report to file.

        Args:
            report: ValidationReport object
            output_path: Path to save report
            format: 'text' or 'json'
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "text":
            content = self.format_text_report(report)
            output_path.write_text(content)
        elif format == "json":
            import json

            content = self.format_json_report(report)
            output_path.write_text(json.dumps(content, indent=2))
        else:
            raise ValueError(f"Unknown format: {format}")

    def get_summary_dashboard(self) -> dict[str, Any]:
        """
        Get summary dashboard across all reports.

        Returns:
            Summary statistics
        """
        if not self.reports:
            return {
                "total_reports": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "total_issues": {
                    "critical": 0,
                    "warning": 0,
                    "info": 0,
                },
                "by_output_type": {},
                "by_category": {},
            }

        total = len(self.reports)
        passed = sum(1 for r in self.reports if r.overall_passed)
        failed = total - passed

        critical_total = sum(r.critical_count for r in self.reports)
        warning_total = sum(r.warning_count for r in self.reports)
        info_total = sum(r.info_count for r in self.reports)

        # By output type
        by_type: dict[str, dict[str, int]] = {}
        for report in self.reports:
            if report.output_type not in by_type:
                by_type[report.output_type] = {"passed": 0, "failed": 0}

            if report.overall_passed:
                by_type[report.output_type]["passed"] += 1
            else:
                by_type[report.output_type]["failed"] += 1

        # By category (aggregate across all reports)
        by_category: dict[str, dict[str, int]] = {}
        for report in self.reports:
            for category, counts in report.summary["by_category"].items():
                if category not in by_category:
                    by_category[category] = {"passed": 0, "failed": 0}

                by_category[category]["passed"] += counts["passed"]
                by_category[category]["failed"] += counts["failed"]

        return {
            "total_reports": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "total_issues": {
                "critical": critical_total,
                "warning": warning_total,
                "info": info_total,
            },
            "by_output_type": by_type,
            "by_category": by_category,
        }


def generate_validation_report(
    results: list[ValidationResult],
    summary: dict[str, Any],
    output_type: str,
    output_path: Path | None = None,
    save_to: Path | None = None,
) -> ValidationReport:
    """
    Convenience function to generate and optionally save report.

    Args:
        results: Validation results
        summary: Validation summary
        output_type: Type of output
        output_path: Path to validated output
        save_to: Path to save report (optional)

    Returns:
        ValidationReport object
    """
    generator = ValidationReportGenerator()
    report = generator.generate_report(results, summary, output_type, output_path)

    if save_to:
        format = "json" if save_to.suffix == ".json" else "text"
        generator.save_report(report, save_to, format=format)

    return report
