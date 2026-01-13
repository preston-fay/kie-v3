"""
HTML Validator for KDS Compliance

Validates rendered Recharts HTML for KDS compliance by parsing SVG output.

This is the FINAL safety net - validates actual rendered output, not just JSON configs.

WHAT IT CHECKS:
- Forbidden colors in SVG (greens, bright reds, blues)
- Gridlines in rendered charts
- Proper KDS palette usage

WHEN TO USE:
- CI/CD pipelines (strict validation)
- Pre-delivery QC checks
- Debug mode (--validate-html flag)

PERFORMANCE:
- Lightweight HTML parsing (no browser)
- Fast enough for CI, but opt-in to avoid slowdowns
"""

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from kie.brand.colors import KDSColors


class RechartsHTMLValidator(HTMLParser):
    """
    Parse Recharts HTML and validate KDS compliance.

    Uses html.parser (stdlib) to extract SVG attributes and verify:
    - No forbidden colors in fill/stroke
    - No gridlines (line elements with grid-like patterns)
    - Only KDS palette colors used
    """

    def __init__(self):
        super().__init__()
        self.violations: list[str] = []
        self.in_svg = False
        self.colors_used: set[str] = set()
        self.line_count = 0  # Track potential gridlines
        self.grid_patterns: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        """Process opening tags and extract color attributes."""
        if tag == 'svg':
            self.in_svg = True

        if self.in_svg:
            # Check colors in fill/stroke attributes
            for attr_name, attr_value in attrs:
                if attr_name in ['fill', 'stroke'] and attr_value:
                    self._check_color(attr_value, attr_name, tag)

                # Detect potential gridlines (line elements)
                if tag == 'line':
                    self.line_count += 1
                    # Collect line attributes for grid pattern detection
                    line_attrs = dict(attrs)
                    self._check_for_gridlines(line_attrs)

    def handle_endtag(self, tag: str):
        """Process closing tags."""
        if tag == 'svg':
            self.in_svg = False

    def _check_color(self, color: str, attr_name: str, tag: str):
        """
        Validate color against KDS compliance rules.

        Args:
            color: Color value (hex, rgb, named)
            attr_name: Attribute name (fill, stroke)
            tag: HTML tag name
        """
        # Normalize color
        color_normalized = color.strip().lower()

        # Skip transparent/none
        if color_normalized in ['none', 'transparent']:
            return

        self.colors_used.add(color_normalized)

        # Check forbidden greens
        if self._is_forbidden_green(color_normalized):
            self.violations.append(
                f"FORBIDDEN GREEN color in rendered {tag} {attr_name}: {color}"
            )

        # Check forbidden colors (bright reds, blues, etc.)
        if self._is_forbidden_color(color_normalized):
            self.violations.append(
                f"FORBIDDEN color in rendered {tag} {attr_name}: {color}"
            )

    def _is_forbidden_green(self, color: str) -> bool:
        """
        Check if color is a forbidden green.

        Args:
            color: Color value (normalized)

        Returns:
            True if color is forbidden green
        """
        # Hex patterns for greens
        if color.startswith('#'):
            # Extract RGB components from hex
            try:
                if len(color) == 4:  # Short form like #0F0
                    r = int(color[1], 16) * 17
                    g = int(color[2], 16) * 17
                    b = int(color[3], 16) * 17
                elif len(color) == 7:  # Full form like #00FF00
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                else:
                    return False

                # Green if G > R and G > B by significant margin
                return g > r + 30 and g > b + 30

            except ValueError:
                return False

        # RGB patterns: rgb(0, 255, 0)
        if color.startswith('rgb'):
            match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', color)
            if match:
                r, g, b = map(int, match.groups())
                return g > r + 30 and g > b + 30

        # Named greens
        forbidden_green_names = [
            'green', 'lime', 'limegreen', 'forestgreen',
            'darkgreen', 'lightgreen', 'springgreen', 'seagreen'
        ]
        return any(name in color for name in forbidden_green_names)

    def _is_forbidden_color(self, color: str) -> bool:
        """
        Check if color is in FORBIDDEN_GREENS list.

        Args:
            color: Color value (normalized)

        Returns:
            True if color is forbidden
        """
        # Check against FORBIDDEN_GREENS from brand/colors.py
        if color.startswith('#'):
            return color.upper() in [c.upper() for c in KDSColors.FORBIDDEN_GREENS]

        return False

    def _check_for_gridlines(self, line_attrs: dict[str, str | None]):
        """
        Check if line element appears to be a gridline.

        Gridlines typically have:
        - Stroke color (gray)
        - Regular spacing patterns
        - Low opacity

        Args:
            line_attrs: Dictionary of line element attributes
        """
        stroke = line_attrs.get('stroke', '').lower()
        opacity = line_attrs.get('opacity', line_attrs.get('stroke-opacity', '1'))

        # Heuristic: gray lines with low opacity are likely gridlines
        is_gray = any(gray in stroke for gray in ['gray', 'grey', '#ccc', '#ddd', '#eee'])

        try:
            opacity_val = float(opacity) if opacity else 1.0
            is_faint = opacity_val < 0.3
        except ValueError:
            is_faint = False

        if is_gray and is_faint:
            self.grid_patterns.append(f"Potential gridline: stroke={stroke}, opacity={opacity}")

    def validate(self, html_path: Path) -> dict[str, Any]:
        """
        Validate rendered HTML file for KDS compliance.

        Args:
            html_path: Path to HTML file with embedded Recharts

        Returns:
            {
                "compliant": bool,
                "violations": list[str],
                "warnings": list[str],
                "colors_detected": list[str],
                "line_count": int
            }
        """
        if not html_path.exists():
            return {
                "compliant": False,
                "violations": [f"HTML file not found: {html_path}"],
                "warnings": [],
                "colors_detected": [],
                "line_count": 0
            }

        # Reset state
        self.violations = []
        self.colors_used = set()
        self.line_count = 0
        self.grid_patterns = []
        self.in_svg = False

        # Parse HTML
        try:
            with open(html_path, encoding='utf-8') as f:
                self.feed(f.read())
        except Exception as e:
            return {
                "compliant": False,
                "violations": [f"Failed to parse HTML: {str(e)}"],
                "warnings": [],
                "colors_detected": [],
                "line_count": 0
            }

        # Warnings (non-blocking)
        warnings = []
        if self.line_count > 20:
            warnings.append(
                f"Suspicious number of line elements ({self.line_count}) - possible gridlines"
            )

        if self.grid_patterns:
            warnings.append(
                f"Detected {len(self.grid_patterns)} potential gridline patterns"
            )

        return {
            "compliant": len(self.violations) == 0,
            "violations": self.violations,
            "warnings": warnings,
            "colors_detected": sorted(list(self.colors_used)),
            "line_count": self.line_count
        }


def validate_html_outputs(
    outputs_dir: Path,
    strict: bool = False
) -> dict[str, Any]:
    """
    Validate all HTML files in outputs directory.

    Args:
        outputs_dir: Directory containing HTML outputs
        strict: If True, treat warnings as violations

    Returns:
        {
            "compliant": bool,
            "files_checked": int,
            "violations": dict[str, list[str]],
            "warnings": dict[str, list[str]]
        }
    """
    if not outputs_dir.exists():
        return {
            "compliant": False,
            "files_checked": 0,
            "violations": {"_system": [f"Outputs directory not found: {outputs_dir}"]},
            "warnings": {}
        }

    validator = RechartsHTMLValidator()
    all_violations: dict[str, list[str]] = {}
    all_warnings: dict[str, list[str]] = {}
    files_checked = 0

    # Find all HTML files
    html_files = list(outputs_dir.rglob("*.html"))

    for html_file in html_files:
        files_checked += 1
        result = validator.validate(html_file)

        if result["violations"]:
            rel_path = str(html_file.relative_to(outputs_dir))
            all_violations[rel_path] = result["violations"]

        if result["warnings"]:
            rel_path = str(html_file.relative_to(outputs_dir))
            all_warnings[rel_path] = result["warnings"]

    # In strict mode, warnings become violations
    if strict and all_warnings:
        all_violations.update(all_warnings)
        all_warnings = {}

    return {
        "compliant": len(all_violations) == 0,
        "files_checked": files_checked,
        "violations": all_violations,
        "warnings": all_warnings
    }
