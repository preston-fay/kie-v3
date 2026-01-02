"""
Theme System for KIE v3

Supports both dark and light themes with KDS color palettes.
All outputs (charts, maps, slides) respect theme preference.
"""

from dataclasses import dataclass
from typing import Literal, Dict, List
from enum import Enum


class ThemeMode(str, Enum):
    """Theme mode options."""

    DARK = "dark"
    LIGHT = "light"


@dataclass
class ThemeColors:
    """Color palette for a theme."""

    # Backgrounds (required)
    background_primary: str
    background_secondary: str
    background_tertiary: str

    # Text (required)
    text_primary: str
    text_secondary: str
    text_tertiary: str

    # Borders (required)
    border_primary: str
    border_secondary: str

    # Brand colors (always KDS purple - defaults)
    brand_primary: str = "#7823DC"
    brand_accent: str = "#9B4DCA"
    brand_light: str = "#E0D2FA"

    # Chart colors (10 official KDS colors - used in order)
    chart_colors: List[str] = None

    # Semantic colors
    success: str = "#10B981"  # Green for success (exception to no-green rule)
    warning: str = "#F59E0B"  # Orange for warnings
    error: str = "#EF4444"  # Red for errors
    info: str = "#3B82F6"  # Blue for info

    def __post_init__(self):
        """Set default chart colors if not provided."""
        if self.chart_colors is None:
            # Official KDS 10-color palette (same for both themes)
            self.chart_colors = [
                "#D2D2D2",  # 1 - Light Gray
                "#A5A6A5",  # 2 - Medium Gray
                "#787878",  # 3 - Dark Gray
                "#E0D2FA",  # 4 - Light Purple
                "#C8A5F0",  # 5 - Medium Light Purple
                "#AF7DEB",  # 6 - Medium Purple
                "#4B4B4B",  # 7 - Charcoal
                "#1E1E1E",  # 8 - Black / Kearney Black
                "#9150E1",  # 9 - Bright Purple
                "#7823DC",  # 10 - Kearney Purple
            ]


# Dark theme (original KIE default)
DARK_THEME = ThemeColors(
    # Backgrounds
    background_primary="#1E1E1E",  # Kearney Black
    background_secondary="#2A2A2A",  # Slightly lighter
    background_tertiary="#3A3A3A",  # Even lighter
    # Text (white on dark)
    text_primary="#FFFFFF",
    text_secondary="#E0E0E0",
    text_tertiary="#B0B0B0",
    # Borders
    border_primary="#7823DC",  # KDS purple
    border_secondary="#4B4B4B",  # Charcoal
)

# Light theme (new for consultants who prefer light backgrounds)
LIGHT_THEME = ThemeColors(
    # Backgrounds
    background_primary="#FFFFFF",  # White
    background_secondary="#F5F5F5",  # Light gray
    background_tertiary="#E5E5E5",  # Medium light gray
    # Text (dark on light)
    text_primary="#1E1E1E",  # Kearney Black
    text_secondary="#4B4B4B",  # Charcoal
    text_tertiary="#787878",  # Dark gray
    # Borders
    border_primary="#7823DC",  # KDS purple
    border_secondary="#D2D2D2",  # Light gray
)


class ThemeManager:
    """
    Manage theme preferences and provide theme-specific colors.

    Used throughout KIE v3 for consistent theming.
    """

    def __init__(self, mode: ThemeMode = ThemeMode.DARK):
        """
        Initialize theme manager.

        Args:
            mode: Theme mode (dark or light)
        """
        self.mode = mode
        self._themes = {
            ThemeMode.DARK: DARK_THEME,
            ThemeMode.LIGHT: LIGHT_THEME,
        }

    @property
    def colors(self) -> ThemeColors:
        """Get current theme colors."""
        return self._themes[self.mode]

    def set_mode(self, mode: ThemeMode):
        """
        Change theme mode.

        Args:
            mode: New theme mode
        """
        self.mode = mode

    def get_background(self, level: Literal["primary", "secondary", "tertiary"] = "primary") -> str:
        """
        Get background color for current theme.

        Args:
            level: Background level (primary = main, secondary = elevated, tertiary = highest)

        Returns:
            Hex color code
        """
        if level == "primary":
            return self.colors.background_primary
        elif level == "secondary":
            return self.colors.background_secondary
        else:
            return self.colors.background_tertiary

    def get_text(self, level: Literal["primary", "secondary", "tertiary"] = "primary") -> str:
        """
        Get text color for current theme.

        Args:
            level: Text level (primary = main, secondary = muted, tertiary = disabled)

        Returns:
            Hex color code
        """
        if level == "primary":
            return self.colors.text_primary
        elif level == "secondary":
            return self.colors.text_secondary
        else:
            return self.colors.text_tertiary

    def get_border(self, level: Literal["primary", "secondary"] = "primary") -> str:
        """
        Get border color for current theme.

        Args:
            level: Border level (primary = brand, secondary = subtle)

        Returns:
            Hex color code
        """
        if level == "primary":
            return self.colors.border_primary
        else:
            return self.colors.border_secondary

    def get_chart_colors(self, count: int = None) -> List[str]:
        """
        Get chart colors for current theme.

        Args:
            count: Number of colors needed (returns all if None)

        Returns:
            List of hex color codes
        """
        colors = self.colors.chart_colors
        if count is not None:
            # Cycle through colors if more needed than available
            return [colors[i % len(colors)] for i in range(count)]
        return colors

    def get_semantic_color(
        self, type: Literal["success", "warning", "error", "info"]
    ) -> str:
        """
        Get semantic color (status indicators).

        Args:
            type: Semantic type

        Returns:
            Hex color code
        """
        if type == "success":
            return self.colors.success
        elif type == "warning":
            return self.colors.warning
        elif type == "error":
            return self.colors.error
        else:
            return self.colors.info

    def get_accent_color(self, for_background: str = None) -> str:
        """
        Get appropriate accent color with good contrast.

        CRITICAL: Never use primary purple (#7823DC) as text on dark backgrounds.
        Use light purple (#E0D2FA) or white instead.

        Args:
            for_background: Background color to contrast against

        Returns:
            Hex color code with sufficient contrast
        """
        if for_background is None:
            for_background = self.get_background()

        # Check if background is dark
        is_dark_bg = self._is_dark_color(for_background)

        if is_dark_bg:
            # On dark backgrounds: Use light purple or white (NEVER primary purple)
            return self.colors.brand_light  # #E0D2FA
        else:
            # On light backgrounds: Use primary purple
            return self.colors.brand_primary  # #7823DC

    def _is_dark_color(self, hex_color: str) -> bool:
        """
        Check if a color is dark using luminance calculation.

        Args:
            hex_color: Hex color code

        Returns:
            True if dark, False if light
        """
        # Remove # if present
        hex_color = hex_color.lstrip("#")

        # Convert to RGB
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255

        # Calculate relative luminance (ITU-R BT.709)
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Dark if luminance < 0.5
        return luminance < 0.5

    def get_matplotlib_style(self) -> Dict[str, any]:
        """
        Get matplotlib rcParams for current theme.

        Returns:
            Dictionary of matplotlib style parameters
        """
        return {
            "figure.facecolor": self.get_background(),
            "axes.facecolor": self.get_background(),
            "axes.edgecolor": self.get_border("secondary"),
            "axes.labelcolor": self.get_text(),
            "axes.grid": False,  # No gridlines (KDS rule)
            "text.color": self.get_text(),
            "xtick.color": self.get_text(),
            "ytick.color": self.get_text(),
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Arial", "Helvetica", "sans-serif"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
        }

    def get_folium_tiles(self) -> str:
        """
        Get Folium map tiles for current theme.

        Returns:
            Tile layer name
        """
        if self.mode == ThemeMode.DARK:
            return "CartoDB dark_matter"
        else:
            return "CartoDB positron"

    def get_css_variables(self) -> Dict[str, str]:
        """
        Get CSS variables for web components.

        Returns:
            Dictionary of CSS variable names and values
        """
        return {
            "--kds-bg-primary": self.get_background("primary"),
            "--kds-bg-secondary": self.get_background("secondary"),
            "--kds-bg-tertiary": self.get_background("tertiary"),
            "--kds-text-primary": self.get_text("primary"),
            "--kds-text-secondary": self.get_text("secondary"),
            "--kds-text-tertiary": self.get_text("tertiary"),
            "--kds-brand-primary": self.colors.brand_primary,
            "--kds-brand-accent": self.colors.brand_accent,
            "--kds-brand-light": self.colors.brand_light,
            "--kds-border-primary": self.get_border("primary"),
            "--kds-border-secondary": self.get_border("secondary"),
            "--kds-success": self.colors.success,
            "--kds-warning": self.colors.warning,
            "--kds-error": self.colors.error,
            "--kds-info": self.colors.info,
        }

    def to_dict(self) -> Dict[str, any]:
        """
        Export theme configuration as dictionary.

        Returns:
            Dictionary with theme mode and colors
        """
        return {
            "mode": self.mode.value,
            "colors": {
                "background_primary": self.colors.background_primary,
                "background_secondary": self.colors.background_secondary,
                "background_tertiary": self.colors.background_tertiary,
                "text_primary": self.colors.text_primary,
                "text_secondary": self.colors.text_secondary,
                "text_tertiary": self.colors.text_tertiary,
                "brand_primary": self.colors.brand_primary,
                "brand_accent": self.colors.brand_accent,
                "brand_light": self.colors.brand_light,
                "border_primary": self.colors.border_primary,
                "border_secondary": self.colors.border_secondary,
                "chart_colors": self.colors.chart_colors,
                "success": self.colors.success,
                "warning": self.colors.warning,
                "error": self.colors.error,
                "info": self.colors.info,
            },
        }


# Global theme manager instance (can be overridden)
_global_theme = ThemeManager(mode=ThemeMode.DARK)


def get_theme() -> ThemeManager:
    """
    Get global theme manager instance.

    Returns:
        ThemeManager instance
    """
    return _global_theme


def set_theme(mode: ThemeMode):
    """
    Set global theme mode.

    Args:
        mode: Theme mode (dark or light)
    """
    _global_theme.set_mode(mode)


def get_theme_mode() -> ThemeMode:
    """
    Get current theme mode.

    Returns:
        Current ThemeMode
    """
    return _global_theme.mode
