"""
KDS Typography System

Official Kearney Design System typography settings.
"""

from enum import Enum


class FontFamily(str, Enum):
    """KDS font families."""

    PRIMARY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    MONOSPACE = "'Fira Code', 'Courier New', monospace"

    @classmethod
    def get_stack(cls, family: str = "PRIMARY") -> str:
        """Get font stack as CSS string."""
        return cls[family].value


class FontSize(int, Enum):
    """KDS font sizes (in pixels)."""

    XS = 10
    SM = 12
    BASE = 14
    LG = 16
    XL = 18
    XXL = 20
    XXXL = 24
    DISPLAY_SM = 28
    DISPLAY_MD = 32
    DISPLAY_LG = 36
    DISPLAY_XL = 48


class FontWeight(int, Enum):
    """KDS font weights."""

    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700


class LineHeight(float, Enum):
    """KDS line heights (relative)."""

    TIGHT = 1.2
    NORMAL = 1.5
    RELAXED = 1.75
    LOOSE = 2.0


class Typography:
    """Typography helper class."""

    @staticmethod
    def get_font_config(
        size: FontSize = FontSize.BASE,
        weight: FontWeight = FontWeight.REGULAR,
        family: FontFamily = FontFamily.PRIMARY,
        line_height: LineHeight = LineHeight.NORMAL,
    ) -> dict[str, any]:
        """
        Get complete font configuration.

        Args:
            size: Font size enum
            weight: Font weight enum
            family: Font family enum
            line_height: Line height enum

        Returns:
            Dictionary with font properties
        """
        return {
            "font_family": family.value,
            "font_size": size.value,
            "font_weight": weight.value,
            "line_height": line_height.value,
        }

    @staticmethod
    def get_chart_title_style() -> dict[str, any]:
        """Get typography for chart titles."""
        return {
            "font_family": FontFamily.PRIMARY.value,
            "font_size": FontSize.XL.value,
            "font_weight": FontWeight.SEMIBOLD.value,
            "line_height": LineHeight.TIGHT.value,
        }

    @staticmethod
    def get_chart_label_style() -> dict[str, any]:
        """Get typography for chart axis labels."""
        return {
            "font_family": FontFamily.PRIMARY.value,
            "font_size": FontSize.SM.value,
            "font_weight": FontWeight.REGULAR.value,
            "line_height": LineHeight.NORMAL.value,
        }

    @staticmethod
    def get_data_label_style() -> dict[str, any]:
        """Get typography for data labels on charts."""
        return {
            "font_family": FontFamily.PRIMARY.value,
            "font_size": FontSize.SM.value,
            "font_weight": FontWeight.MEDIUM.value,
            "line_height": LineHeight.TIGHT.value,
        }

    @staticmethod
    def get_slide_title_style() -> dict[str, any]:
        """Get typography for slide titles."""
        return {
            "font_family": FontFamily.PRIMARY.value,
            "font_size": FontSize.DISPLAY_MD.value,
            "font_weight": FontWeight.BOLD.value,
            "line_height": LineHeight.TIGHT.value,
        }

    @staticmethod
    def get_slide_body_style() -> dict[str, any]:
        """Get typography for slide body text."""
        return {
            "font_family": FontFamily.PRIMARY.value,
            "font_size": FontSize.BASE.value,
            "font_weight": FontWeight.REGULAR.value,
            "line_height": LineHeight.RELAXED.value,
        }
