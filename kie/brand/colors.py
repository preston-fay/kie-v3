"""
KDS Color System - Official Kearney Design System Colors

IMPORTANT: This is the official 10-color palette from preston-fay/Kearneydesignsystem.
Use colors in the exact order specified for charts.
"""

from enum import Enum


class KDSColors:
    """Official Kearney Design System color palette."""

    # Primary Brand Color
    PRIMARY = "#7823DC"  # Kearney Purple

    # Chart Palette (10 official colors - USE IN THIS EXACT ORDER)
    CHART_PALETTE: tuple[str, ...] = (
        "#D2D2D2",  # 1 - Light Gray
        "#A5A6A5",  # 2 - Medium Gray
        "#787878",  # 3 - Dark Gray
        "#E0D2FA",  # 4 - Light Purple
        "#C8A5F0",  # 5 - Medium Light Purple
        "#AF7DEB",  # 6 - Medium Purple
        "#4B4B4B",  # 7 - Charcoal
        "#1E1E1E",  # 8 - Black (Kearney Black)
        "#9150E1",  # 9 - Bright Purple
        "#7823DC",  # 10 - Kearney Purple (primary)
    )

    # Accent Colors
    ACCENT_LIGHT = "#9B4DCA"  # Light purple for text on dark
    ACCENT_BRIGHT = "#9150E1"  # Bright purple

    # Background Colors
    DARK_BG = "#1E1E1E"  # Kearney Black
    LIGHT_BG = "#FFFFFF"  # White

    # Text Colors
    TEXT_ON_DARK = "#FFFFFF"  # White text on dark backgrounds
    TEXT_ON_LIGHT = "#1E1E1E"  # Dark text on light backgrounds

    # FORBIDDEN COLORS (never use these)
    FORBIDDEN_GREENS: tuple[str, ...] = (
        "#00FF00", "#008000", "#90EE90", "#98FB98", "#00FA9A",
        "#3CB371", "#2E8B57", "#228B22", "#32CD32", "#7FFF00",
        "#7CFC00", "#ADFF2F", "#00FF7F", "#00FFFF", "#40E0D0",
        "#48D1CC", "#20B2AA", "#5F9EA0", "#66CDAA", "#7FFFD4",
        "#006400", "#556B2F", "#6B8E23", "#808000", "#9ACD32",
    )

    @classmethod
    def get_chart_color(cls, index: int) -> str:
        """
        Get chart color by index (cycles through palette).

        Args:
            index: Color index (0-based)

        Returns:
            Hex color code
        """
        return cls.CHART_PALETTE[index % len(cls.CHART_PALETTE)]

    @classmethod
    def get_chart_colors(cls, count: int) -> list[str]:
        """
        Get list of chart colors.

        Args:
            count: Number of colors needed

        Returns:
            List of hex color codes
        """
        return [cls.get_chart_color(i) for i in range(count)]

    @classmethod
    def get_accent_color(cls, background: str = "#1E1E1E") -> str:
        """
        Get appropriate accent color for text on background.

        IMPORTANT: Never use PRIMARY (#7823DC) as text on dark backgrounds
        due to insufficient contrast (fails WCAG AA).

        Args:
            background: Background color (hex)

        Returns:
            Accent color safe for text
        """
        # Simple luminance check
        bg_lower = background.lower()
        if bg_lower in ["#1e1e1e", "#000000", "#4b4b4b"]:
            # Dark background -> use white or light purple
            return cls.TEXT_ON_DARK
        else:
            # Light background -> use dark text or primary
            return cls.TEXT_ON_LIGHT

    @classmethod
    def is_forbidden(cls, color: str) -> bool:
        """
        Check if color is forbidden (e.g., green).

        Args:
            color: Hex color code

        Returns:
            True if color is forbidden
        """
        color_upper = color.upper()
        return any(
            color_upper == forbidden.upper()
            for forbidden in cls.FORBIDDEN_GREENS
        )

    @classmethod
    def validate_palette(cls, colors: list[str]) -> tuple[bool, list[str]]:
        """
        Validate that colors are from KDS palette.

        Args:
            colors: List of hex color codes

        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []

        for color in colors:
            if cls.is_forbidden(color):
                violations.append(f"Forbidden color detected: {color}")
            elif color.upper() not in [c.upper() for c in cls.CHART_PALETTE]:
                violations.append(f"Non-KDS color: {color}")

        return len(violations) == 0, violations


class ColorPalette(Enum):
    """Enum for accessing colors by semantic name."""

    LIGHT_GRAY = "#D2D2D2"
    MEDIUM_GRAY = "#A5A6A5"
    DARK_GRAY = "#787878"
    LIGHT_PURPLE = "#E0D2FA"
    MEDIUM_LIGHT_PURPLE = "#C8A5F0"
    MEDIUM_PURPLE = "#AF7DEB"
    CHARCOAL = "#4B4B4B"
    KEARNEY_BLACK = "#1E1E1E"
    BRIGHT_PURPLE = "#9150E1"
    KEARNEY_PURPLE = "#7823DC"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color code (e.g., "#7823DC")

    Returns:
        RGB tuple (r, g, b)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hex color.

    Args:
        r: Red (0-255)
        g: Green (0-255)
        b: Blue (0-255)

    Returns:
        Hex color code
    """
    return f"#{r:02X}{g:02X}{b:02X}"


def calculate_luminance(hex_color: str) -> float:
    """
    Calculate relative luminance of a color (WCAG formula).

    Args:
        hex_color: Hex color code

    Returns:
        Luminance value (0.0 to 1.0)
    """
    r, g, b = hex_to_rgb(hex_color)

    # Convert to 0-1 scale and apply gamma correction
    def gamma_correct(c: int) -> float:
        c_norm = c / 255.0
        if c_norm <= 0.03928:
            return c_norm / 12.92
        else:
            return ((c_norm + 0.055) / 1.055) ** 2.4

    r_lin = gamma_correct(r)
    g_lin = gamma_correct(g)
    b_lin = gamma_correct(b)

    # Calculate luminance
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate contrast ratio between two colors (WCAG formula).

    Args:
        color1: First hex color
        color2: Second hex color

    Returns:
        Contrast ratio (1:1 to 21:1)
    """
    lum1 = calculate_luminance(color1)
    lum2 = calculate_luminance(color2)

    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)


def meets_wcag_aa(foreground: str, background: str, large_text: bool = False) -> bool:
    """
    Check if color combination meets WCAG 2.1 AA standards.

    Args:
        foreground: Foreground color (text)
        background: Background color
        large_text: True if text is large (18pt+ or 14pt+ bold)

    Returns:
        True if meets WCAG AA standards
    """
    ratio = contrast_ratio(foreground, background)
    threshold = 3.0 if large_text else 4.5
    return ratio >= threshold
