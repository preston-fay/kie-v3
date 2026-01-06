"""
Theme-aware configuration helpers for charts.

Provides functions to generate chart configurations that respect theme preferences.
"""

from typing import Any

from kie.brand.theme import get_theme


def get_tooltip_config() -> dict[str, Any]:
    """
    Get tooltip configuration for current theme.

    Returns:
        Tooltip contentStyle dict
    """
    theme = get_theme()
    return {
        "backgroundColor": theme.get_background("secondary"),
        "border": f"1px solid {theme.get_border('secondary')}",
        "borderRadius": "8px",
        "padding": "12px",
        "fontSize": 12,
        "fontFamily": "Inter, sans-serif",
        "color": theme.get_text(),
    }


def get_legend_config() -> dict[str, Any]:
    """
    Get legend configuration for current theme.

    Returns:
        Legend wrapperStyle dict
    """
    theme = get_theme()
    return {
        "fontSize": 12,
        "fontFamily": "Inter, sans-serif",
        "color": theme.get_text(),
    }


def get_axis_tick_config() -> dict[str, Any]:
    """
    Get axis tick configuration for current theme.

    Returns:
        Axis tick style dict
    """
    theme = get_theme()
    return {
        "fill": theme.get_text("secondary"),
        "fontSize": 12,
        "fontFamily": "Inter, sans-serif",
    }


def get_data_label_config(position: str = "top") -> dict[str, Any]:
    """
    Get data label configuration for current theme.

    Args:
        position: Label position

    Returns:
        Data label config dict
    """
    theme = get_theme()
    return {
        "position": position,
        "fill": theme.get_text(),
        "fontSize": 12,
        "fontWeight": 500,
        "fontFamily": "Inter, sans-serif",
    }


def get_chart_container_style() -> dict[str, Any]:
    """
    Get container style for chart wrapper.

    Returns:
        Container style dict
    """
    theme = get_theme()
    return {
        "backgroundColor": theme.get_background(),
        "padding": "16px",
        "borderRadius": "8px",
        "border": f"1px solid {theme.get_border('secondary')}",
    }


def get_recharts_theme_config() -> dict[str, Any]:
    """
    Get complete Recharts theme configuration.

    Returns:
        Complete theme config for Recharts
    """
    theme = get_theme()

    return {
        "backgroundColor": theme.get_background(),
        "textColor": theme.get_text(),
        "fontSize": 12,
        "fontFamily": "Inter, sans-serif",
        "tooltip": get_tooltip_config(),
        "legend": get_legend_config(),
        "axis": {
            "tick": get_axis_tick_config(),
            "axisLine": {"stroke": theme.get_border("secondary")},
            "tickLine": False,  # KDS: no tick lines
        },
        "grid": {
            "strokeDasharray": "0",  # KDS: no gridlines
            "stroke": "transparent",
        },
        "cartesianGrid": {
            "stroke": "transparent",  # KDS: no gridlines
        },
    }
