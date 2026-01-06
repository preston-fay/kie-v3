"""
Output Validation System

Critical safety checks before any output reaches consultants.
Prevents errors, synthetic data issues, and brand violations.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd


class ValidationLevel(str, Enum):
    """Validation severity levels."""

    CRITICAL = "critical"  # Must fix - blocks output
    WARNING = "warning"  # Should fix - allows output with warning
    INFO = "info"  # Nice to fix - informational only


class ValidationCategory(str, Enum):
    """Validation categories."""

    DATA_QUALITY = "data_quality"
    BRAND_COMPLIANCE = "brand_compliance"
    CALCULATION = "calculation"
    SYNTHETIC_DATA = "synthetic_data"
    CONTENT = "content"
    ACCESSIBILITY = "accessibility"


@dataclass
class ValidationResult:
    """Result from a validation check."""

    passed: bool
    level: ValidationLevel
    category: ValidationCategory
    message: str
    details: dict[str, Any] | None = None
    suggestion: str | None = None


class OutputValidator:
    """
    Validates outputs before delivery to consultants.

    Runs comprehensive checks to ensure safety and quality.
    """

    def __init__(self):
        """Initialize validator."""
        self.results: list[ValidationResult] = []

    def validate_all(
        self,
        data: pd.DataFrame | None = None,
        config: dict[str, Any] | None = None,
        content: str | None = None,
    ) -> tuple[bool, list[ValidationResult]]:
        """
        Run all validation checks.

        Args:
            data: DataFrame to validate
            config: Chart/table config to validate
            content: Text content to validate

        Returns:
            Tuple of (passed, results)
        """
        self.results = []

        # Data quality checks
        if data is not None:
            self._validate_data_quality(data)
            self._detect_synthetic_data(data)
            self._validate_calculations(data)

        # Brand compliance checks
        if config is not None:
            self._validate_brand_compliance(config)
            self._validate_accessibility(config)

        # Content checks
        if content is not None:
            self._validate_content(content)

        # Determine overall pass/fail
        critical_failures = [r for r in self.results if not r.passed and r.level == ValidationLevel.CRITICAL]
        passed = len(critical_failures) == 0

        return passed, self.results

    def _validate_data_quality(self, df: pd.DataFrame):
        """Check data quality issues."""

        # Check for all-null columns
        null_cols = df.columns[df.isnull().all()].tolist()
        if null_cols:
            self.results.append(
                ValidationResult(
                    passed=False,
                    level=ValidationLevel.CRITICAL,
                    category=ValidationCategory.DATA_QUALITY,
                    message=f"Columns with all null values: {', '.join(null_cols)}",
                    suggestion="Remove these columns or fill with appropriate values",
                )
            )

        # Check for high null percentage
        for col in df.columns:
            null_pct = df[col].isnull().sum() / len(df)
            if null_pct > 0.5:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.DATA_QUALITY,
                        message=f"Column '{col}' has {null_pct:.1%} null values",
                        suggestion="Consider imputation or column removal",
                    )
                )

        # Check for duplicate rows
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            self.results.append(
                ValidationResult(
                    passed=False,
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.DATA_QUALITY,
                    message=f"{dup_count} duplicate rows detected",
                    suggestion="Review and remove duplicates if unintentional",
                )
            )

        # Check for suspicious values (e.g., all zeros, all same value)
        for col in df.select_dtypes(include=["number"]).columns:
            if (df[col] == 0).all():
                self.results.append(
                    ValidationResult(
                        passed=False,
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.DATA_QUALITY,
                        message=f"Column '{col}' contains all zeros",
                        suggestion="Verify this is intentional",
                    )
                )

            unique_count = df[col].nunique()
            if unique_count == 1:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.DATA_QUALITY,
                        message=f"Column '{col}' has only one unique value",
                        suggestion="Consider removing if not meaningful",
                    )
                )

    def _detect_synthetic_data(self, df: pd.DataFrame):
        """Detect potentially synthetic/fake data."""

        # Check for obviously synthetic patterns
        synthetic_indicators = []

        # Sequential IDs or values
        for col in df.select_dtypes(include=["number"]).columns:
            if len(df) > 2:
                diffs = df[col].diff().dropna()
                if (diffs == 1).all() or (diffs == -1).all():
                    synthetic_indicators.append(f"Sequential values in '{col}'")

        # Suspiciously round numbers
        for col in df.select_dtypes(include=["number"]).columns:
            if df[col].nunique() > 5:  # Only check if enough variety
                # Check if all values are round (divisible by 1000, 100, etc.)
                all_round = ((df[col] % 1000) == 0).all()
                if all_round:
                    synthetic_indicators.append(f"All values in '{col}' are round thousands")

        # Common fake names (Lorem Ipsum, Test, Sample, etc.)
        for col in df.select_dtypes(include=["object"]).columns:
            fake_patterns = ["lorem", "ipsum", "test", "sample", "dummy", "fake", "example", "acme"]
            text_lower = df[col].astype(str).str.lower()

            for pattern in fake_patterns:
                if text_lower.str.contains(pattern).any():
                    synthetic_indicators.append(f"Potential fake data in '{col}' (contains '{pattern}')")
                    break

        # Report synthetic data detection
        if synthetic_indicators:
            self.results.append(
                ValidationResult(
                    passed=False,
                    level=ValidationLevel.CRITICAL,
                    category=ValidationCategory.SYNTHETIC_DATA,
                    message="Potential synthetic/fake data detected",
                    details={"indicators": synthetic_indicators},
                    suggestion="⚠️ CRITICAL: Verify data is real client data, not test/sample data",
                )
            )

    def _validate_calculations(self, df: pd.DataFrame):
        """Validate calculations and derived columns."""

        # Check for impossible values
        for col in df.select_dtypes(include=["number"]).columns:
            # Negative values where they shouldn't be
            if "percent" in col.lower() or "pct" in col.lower():
                if (df[col] < 0).any():
                    self.results.append(
                        ValidationResult(
                            passed=False,
                            level=ValidationLevel.CRITICAL,
                            category=ValidationCategory.CALCULATION,
                            message=f"Negative percentages in '{col}'",
                            suggestion="Check calculation logic",
                        )
                    )

                if (df[col] > 1.5).any():  # Assuming percentages as decimals
                    self.results.append(
                        ValidationResult(
                            passed=False,
                            level=ValidationLevel.WARNING,
                            category=ValidationCategory.CALCULATION,
                            message=f"Percentages over 150% in '{col}'",
                            suggestion="Verify these extreme values are correct",
                        )
                    )

            # Extremely large values (potential overflow/error)
            if df[col].max() > 1e15:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.CALCULATION,
                        message=f"Extremely large values in '{col}' (>{1e15:,.0f})",
                        suggestion="Verify units and check for calculation errors",
                    )
                )

        # Check for infinity and NaN in numeric columns
        for col in df.select_dtypes(include=["number"]).columns:
            if df[col].isin([float("inf"), float("-inf")]).any():
                self.results.append(
                    ValidationResult(
                        passed=False,
                        level=ValidationLevel.CRITICAL,
                        category=ValidationCategory.CALCULATION,
                        message=f"Infinite values in '{col}'",
                        suggestion="Check for division by zero or other calculation errors",
                    )
                )

    def _validate_brand_compliance(self, config: dict[str, Any]):
        """Check KDS brand compliance."""

        # Check for forbidden colors (greens)
        forbidden_colors = ["#00FF00", "#008000", "#00ff00", "#90EE90", "#90ee90", "green"]

        def check_colors_recursive(obj, path=""):
            """Recursively check for forbidden colors."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if "color" in key.lower() or "fill" in key.lower():
                        if isinstance(value, str):
                            value_lower = value.lower()
                            for forbidden in forbidden_colors:
                                if forbidden.lower() in value_lower:
                                    self.results.append(
                                        ValidationResult(
                                            passed=False,
                                            level=ValidationLevel.CRITICAL,
                                            category=ValidationCategory.BRAND_COMPLIANCE,
                                            message=f"Forbidden color (green) detected at {new_path}",
                                            details={"color": value, "location": new_path},
                                            suggestion="Use KDS-approved colors only (purple palette)",
                                        )
                                    )
                    check_colors_recursive(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_colors_recursive(item, f"{path}[{i}]")

        check_colors_recursive(config)

        # Check for gridlines (KDS forbids them)
        # Look for explicit gridline configurations that are enabled
        config_str = str(config).lower()

        # Check for common gridline patterns that indicate enabled grids
        gridline_enabled_patterns = [
            '"grid": true',
            "'grid': true",
            '"show": true',  # within grid config
            "'show': true",  # within grid config
            'gridlines: true',
            'gridlines":true',
            "gridlines':true",
        ]

        has_grid_key = "grid" in config_str or "gridline" in config_str

        # Only flag if we have grid AND it appears to be enabled
        if has_grid_key:
            for pattern in gridline_enabled_patterns:
                if pattern in config_str:
                    # Double check it's actually about grids, not something else
                    # Look at context around the pattern
                    idx = config_str.find(pattern)
                    if idx > 0:
                        context = config_str[max(0, idx-20):min(len(config_str), idx+len(pattern)+20)]
                        if 'grid' in context:
                            self.results.append(
                                ValidationResult(
                                    passed=False,
                                    level=ValidationLevel.CRITICAL,
                                    category=ValidationCategory.BRAND_COMPLIANCE,
                                    message="Gridlines detected (forbidden by KDS)",
                                    suggestion="Remove all gridlines from charts",
                                )
                            )
                            break

    def _validate_accessibility(self, config: dict[str, Any]):
        """Check WCAG accessibility compliance."""

        # Check for color-only differentiation
        # (In real implementation, would check color contrast ratios)

        # Check for font sizes
        def check_font_sizes(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if "fontsize" in key.lower() or "font_size" in key.lower():
                        if isinstance(value, int | float) and value < 10:
                            self.results.append(
                                ValidationResult(
                                    passed=False,
                                    level=ValidationLevel.WARNING,
                                    category=ValidationCategory.ACCESSIBILITY,
                                    message=f"Font size too small ({value}pt) at {new_path}",
                                    suggestion="Use minimum 10pt font for accessibility",
                                )
                            )
                    check_font_sizes(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_font_sizes(item, f"{path}[{i}]")

        check_font_sizes(config)

    def _validate_content(self, content: str):
        """Validate text content."""

        # Check for placeholder text
        placeholders = ["lorem ipsum", "todo", "tbd", "xxx", "[insert", "placeholder", "coming soon"]

        for placeholder in placeholders:
            if placeholder in content.lower():
                self.results.append(
                    ValidationResult(
                        passed=False,
                        level=ValidationLevel.CRITICAL,
                        category=ValidationCategory.CONTENT,
                        message=f"Placeholder text detected: '{placeholder}'",
                        suggestion="Replace all placeholder text with actual content",
                    )
                )

        # Check for profanity or inappropriate language
        # (In production, would use a comprehensive list)
        inappropriate = ["fuck", "shit", "damn"]
        for word in inappropriate:
            if word in content.lower():
                self.results.append(
                    ValidationResult(
                        passed=False,
                        level=ValidationLevel.CRITICAL,
                        category=ValidationCategory.CONTENT,
                        message="Inappropriate language detected",
                        suggestion="Remove all profanity and inappropriate language",
                    )
                )

        # Check for overly long sentences (readability)
        sentences = re.split(r"[.!?]+", content)
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 40:
                self.results.append(
                    ValidationResult(
                        passed=False,
                        level=ValidationLevel.INFO,
                        category=ValidationCategory.CONTENT,
                        message="Sentence with 40+ words detected",
                        suggestion="Consider breaking long sentences for readability",
                    )
                )

    def get_validation_summary(self) -> dict[str, Any]:
        """
        Get summary of validation results.

        Returns:
            Summary dict
        """
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        by_level = {
            "critical": sum(1 for r in self.results if r.level == ValidationLevel.CRITICAL and not r.passed),
            "warning": sum(1 for r in self.results if r.level == ValidationLevel.WARNING and not r.passed),
            "info": sum(1 for r in self.results if r.level == ValidationLevel.INFO and not r.passed),
        }

        by_category = {}
        for result in self.results:
            cat = result.category.value
            if cat not in by_category:
                by_category[cat] = {"passed": 0, "failed": 0}

            if result.passed:
                by_category[cat]["passed"] += 1
            else:
                by_category[cat]["failed"] += 1

        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "by_level": by_level,
            "by_category": by_category,
            "overall_pass": by_level["critical"] == 0,
        }


def validate_output(
    data: pd.DataFrame | None = None,
    config: dict[str, Any] | None = None,
    content: str | None = None,
    strict: bool = True,
) -> tuple[bool, list[ValidationResult], dict[str, Any]]:
    """
    Convenience function to validate outputs.

    Args:
        data: DataFrame to validate
        config: Configuration to validate
        content: Content to validate
        strict: If True, warnings also block output

    Returns:
        Tuple of (passed, results, summary)
    """
    validator = OutputValidator()
    passed, results = validator.validate_all(data, config, content)
    summary = validator.get_validation_summary()

    # In strict mode, warnings also block
    if strict and summary["by_level"]["warning"] > 0:
        passed = False

    return passed, results, summary
