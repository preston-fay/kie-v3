"""
KDS Brand Compliance Validator

Validates outputs against Kearney Design System guidelines.
"""

import json
from pathlib import Path
from typing import Any

from kie.brand.colors import KDSColors, meets_wcag_aa
from kie.exceptions import ForbiddenColorError


class BrandValidator:
    """Validates brand compliance for KIE outputs."""

    def __init__(self, strict: bool = True):
        """
        Initialize validator.

        Args:
            strict: If True, raise exceptions on violations
        """
        self.strict = strict

    def validate_chart_config(self, config_path: Path) -> dict[str, Any]:
        """
        Validate Recharts JSON configuration.

        Args:
            config_path: Path to chart JSON file

        Returns:
            Validation result dictionary
        """
        violations = []
        warnings = []

        # Load config
        with open(config_path) as f:
            config = json.load(f)

        # Check 1: No gridlines
        if config.get("config", {}).get("gridLines", False):
            violations.append("Gridlines detected (must be False for KDS compliance)")

        # Check 2: Axis lines disabled (check xAxis/yAxis for new structure)
        chart_config = config.get("config", {})

        # Check xAxis
        x_axis = chart_config.get("xAxis", {})
        if x_axis.get("axisLine", True):
            violations.append("X-axis lines enabled (should be False for clean KDS look)")
        if x_axis.get("tickLine", True):
            violations.append("X-axis tick lines enabled (should be False for clean KDS look)")

        # Check yAxis
        y_axis = chart_config.get("yAxis", {})
        if y_axis.get("axisLine", True):
            violations.append("Y-axis lines enabled (should be False for clean KDS look)")
        if y_axis.get("tickLine", True):
            violations.append("Y-axis tick lines enabled (should be False for clean KDS look)")

        # Check 3: Colors from KDS palette (check bars/lines/areas arrays)
        colors = []

        # Extract colors from bar configs
        for bar in chart_config.get("bars", []):
            if "fill" in bar:
                colors.append(bar["fill"])

        # Extract colors from line configs
        for line in chart_config.get("lines", []):
            if "stroke" in line:
                colors.append(line["stroke"])

        # Extract colors from area configs
        for area in chart_config.get("areas", []):
            if "fill" in area:
                colors.append(area["fill"])

        # Extract colors from pie configs
        pie_config = chart_config.get("pie", {})
        if "colors" in chart_config:
            colors.extend(chart_config["colors"])

        # Also check legacy colors field for backwards compatibility
        colors.extend(chart_config.get("colors", []))

        # Validate colors
        for color in colors:
            if KDSColors.is_forbidden(color):
                violations.append(f"Forbidden color detected: {color}")
                if self.strict:
                    raise ForbiddenColorError(
                        f"Forbidden color {color} violates KDS guidelines",
                        details={"color": color, "file": str(config_path)}
                    )

            if color.upper() not in [c.upper() for c in KDSColors.CHART_PALETTE]:
                warnings.append(f"Non-KDS color: {color} (not in official palette)")

        # Check 4: Data labels present (check bars/lines for label config)
        has_data_labels = False

        # Check bars for labels
        for bar in chart_config.get("bars", []):
            if bar.get("label") is not None:
                has_data_labels = True
                break

        # Check lines for labels
        if not has_data_labels:
            for line in chart_config.get("lines", []):
                if line.get("label") is not None:
                    has_data_labels = True
                    break

        # Legacy check
        if not has_data_labels and not chart_config.get("dataLabels"):
            warnings.append("Data labels not configured (recommended for KDS charts)")

        # Check 5: Typography
        font_family = config.get("config", {}).get("fontFamily", "")
        if "Inter" not in font_family and "Arial" not in font_family:
            warnings.append(f"Font family '{font_family}' not Inter or Arial")

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "file": str(config_path),
        }

    def validate_directory(self, directory: Path) -> dict[str, Any]:
        """
        Validate all chart configs in a directory.

        Args:
            directory: Path to directory containing chart JSONs

        Returns:
            Aggregated validation results
        """
        all_violations = []
        all_warnings = []
        files_checked = 0

        # Find all JSON files
        for json_file in directory.rglob("*.json"):
            try:
                result = self.validate_chart_config(json_file)
                files_checked += 1
                all_violations.extend(
                    [f"{json_file.name}: {v}" for v in result["violations"]]
                )
                all_warnings.extend(
                    [f"{json_file.name}: {w}" for w in result["warnings"]]
                )
            except json.JSONDecodeError:
                all_warnings.append(f"{json_file.name}: Invalid JSON")

        return {
            "compliant": len(all_violations) == 0,
            "files_checked": files_checked,
            "violations": all_violations,
            "warnings": all_warnings,
        }

    def validate_colors(self, colors: list[str]) -> dict[str, Any]:
        """
        Validate list of colors.

        Args:
            colors: List of hex color codes

        Returns:
            Validation result
        """
        violations = []
        warnings = []

        for color in colors:
            # Check forbidden
            if KDSColors.is_forbidden(color):
                violations.append(f"Forbidden color: {color}")
                if self.strict:
                    raise ForbiddenColorError(
                        f"Forbidden color {color}",
                        details={"color": color}
                    )

            # Check if from KDS palette
            if color.upper() not in [c.upper() for c in KDSColors.CHART_PALETTE]:
                warnings.append(f"Non-KDS color: {color}")

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
        }

    def validate_contrast(
        self, foreground: str, background: str, large_text: bool = False
    ) -> dict[str, Any]:
        """
        Validate color contrast meets WCAG AA.

        Args:
            foreground: Foreground color (text)
            background: Background color
            large_text: True if text is large

        Returns:
            Validation result
        """
        meets_standard = meets_wcag_aa(foreground, background, large_text)

        result = {
            "compliant": meets_standard,
            "foreground": foreground,
            "background": background,
            "large_text": large_text,
            "violations": [],
            "warnings": [],
        }

        if not meets_standard:
            from kie.brand.colors import contrast_ratio
            ratio = contrast_ratio(foreground, background)
            threshold = 3.0 if large_text else 4.5
            result["violations"].append(
                f"Insufficient contrast: {ratio:.2f}:1 (need {threshold}:1 for WCAG AA)"
            )

        # Special warning for purple text on dark
        if foreground.upper() == "#7823DC" and background.upper() in ["#1E1E1E", "#000000"]:
            result["warnings"].append(
                "Primary purple (#7823DC) has low contrast on dark backgrounds. "
                "Use white (#FFFFFF) or light purple (#9B4DCA) instead."
            )

        return result

    def generate_report(self, directory: Path, output_path: Path | None = None) -> str:
        """
        Generate comprehensive compliance report.

        Args:
            directory: Directory to validate
            output_path: Optional path to save report

        Returns:
            Report as string
        """
        result = self.validate_directory(directory)

        # Build report
        lines = [
            "=" * 60,
            "KDS BRAND COMPLIANCE REPORT",
            "=" * 60,
            f"Directory: {directory}",
            f"Files checked: {result['files_checked']}",
            f"Compliant: {'✅ YES' if result['compliant'] else '❌ NO'}",
            "",
        ]

        if result["violations"]:
            lines.append("VIOLATIONS:")
            for v in result["violations"]:
                lines.append(f"  ❌ {v}")
            lines.append("")

        if result["warnings"]:
            lines.append("WARNINGS:")
            for w in result["warnings"]:
                lines.append(f"  ⚠️  {w}")
            lines.append("")

        if result["compliant"] and not result["warnings"]:
            lines.append("✅ All outputs are KDS-compliant!")

        lines.append("=" * 60)

        report = "\n".join(lines)

        if output_path:
            output_path.write_text(report)

        return report


def validate_file(file_path: Path, strict: bool = False) -> None:
    """
    Validate a single file and print results.

    Args:
        file_path: Path to chart JSON file
        strict: Raise exceptions on violations
    """
    validator = BrandValidator(strict=strict)
    result = validator.validate_chart_config(file_path)

    print(f"\nValidating: {file_path.name}")
    print(f"Compliant: {'✅ YES' if result['compliant'] else '❌ NO'}")

    if result["violations"]:
        print("\nViolations:")
        for v in result["violations"]:
            print(f"  ❌ {v}")

    if result["warnings"]:
        print("\nWarnings:")
        for w in result["warnings"]:
            print(f"  ⚠️  {w}")


def validate_directory_cli(directory: Path, strict: bool = False) -> None:
    """
    Validate directory from CLI.

    Args:
        directory: Directory to validate
        strict: Raise exceptions on violations
    """
    validator = BrandValidator(strict=strict)
    report = validator.generate_report(directory)
    print(report)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m kie.brand.validator <path>")
        sys.exit(1)

    path = Path(sys.argv[1])
    strict = "--strict" in sys.argv

    if path.is_file():
        validate_file(path, strict=strict)
    elif path.is_dir():
        validate_directory_cli(path, strict=strict)
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)
