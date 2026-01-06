"""
JSON Schema definitions for Recharts configurations.

These schemas define the structure of JSON files that React components
will consume to render Recharts visualizations.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from kie.brand.theme import get_theme


class AxisConfig(BaseModel):
    """Configuration for chart axes."""

    dataKey: str
    axisLine: bool = False  # KDS: no axis lines
    tickLine: bool = False  # KDS: no tick lines
    tick: dict[str, Any] = Field(default_factory=lambda: {
        "fill": "currentColor",
        "fontSize": 12
    })
    label: dict[str, Any] | None = None


class DataLabelConfig(BaseModel):
    """Configuration for data labels."""

    position: Literal["top", "bottom", "left", "right", "inside", "outside", "center"] = "top"
    fill: str = "currentColor"
    fontSize: int = 12
    fontWeight: int = 500


class LegendConfig(BaseModel):
    """Configuration for chart legend."""

    verticalAlign: Literal["top", "middle", "bottom"] = "bottom"
    align: Literal["left", "center", "right"] = "center"
    iconType: Literal["line", "plainline", "square", "rect", "circle", "cross", "diamond", "star", "triangle", "wye"] = "square"
    wrapperStyle: dict[str, Any] = Field(default_factory=lambda: {
        "fontSize": 12,
        "fontFamily": "Inter, sans-serif"
    })


class TooltipConfig(BaseModel):
    """Configuration for chart tooltip."""

    contentStyle: dict[str, Any] = Field(default_factory=lambda: {
        "backgroundColor": get_theme().get_background("secondary"),
        "border": "none",
        "borderRadius": "4px",
        "padding": "8px",
        "fontSize": 12
    })
    labelStyle: dict[str, Any] = Field(default_factory=lambda: {
        "color": "#FFFFFF",
        "fontWeight": 600
    })
    itemStyle: dict[str, Any] = Field(default_factory=lambda: {
        "color": "#D2D2D2"
    })


class BarConfig(BaseModel):
    """Configuration for bar series in Recharts."""

    dataKey: str
    fill: str
    radius: list[int] = Field(default=[4, 4, 0, 0])  # Rounded top corners
    label: DataLabelConfig | None = None


class LineConfig(BaseModel):
    """Configuration for line series in Recharts."""

    dataKey: str
    stroke: str
    strokeWidth: int = 2
    dot: dict[str, Any] = Field(default_factory=lambda: {"r": 4})
    activeDot: dict[str, Any] = Field(default_factory=lambda: {"r": 6})
    label: DataLabelConfig | None = None


class AreaConfig(BaseModel):
    """Configuration for area series in Recharts."""

    dataKey: str
    fill: str
    stroke: str
    strokeWidth: int = 2
    fillOpacity: float = 0.6
    label: DataLabelConfig | None = None


class PieConfig(BaseModel):
    """Configuration for pie chart in Recharts."""

    dataKey: str
    nameKey: str
    cx: str = "50%"
    cy: str = "50%"
    innerRadius: int = 0  # 0 for pie, >0 for donut
    outerRadius: int = 80
    paddingAngle: int = 2
    label: dict[str, Any] | None = Field(default_factory=lambda: {
        "position": "outside",
        "fontSize": 12
    })


class ChartConfigBase(BaseModel):
    """Base configuration shared by all chart types."""

    title: str | None = None
    subtitle: str | None = None
    width: int = 800
    height: int = 600
    margin: dict[str, int] = Field(default_factory=lambda: {
        "top": 20,
        "right": 30,
        "bottom": 20,
        "left": 40
    })

    # KDS compliance
    gridLines: bool = False  # MUST be False
    fontFamily: str = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

    # Interactive features
    interactive: bool = True

    # Components
    legend: LegendConfig | None = None
    tooltip: TooltipConfig | None = Field(default_factory=TooltipConfig)


class BarChartConfig(ChartConfigBase):
    """Complete configuration for Recharts BarChart."""

    xAxis: AxisConfig
    yAxis: AxisConfig
    bars: list[BarConfig]
    layout: Literal["horizontal", "vertical"] = "horizontal"
    barSize: int | None = None
    barGap: int = 4
    barCategoryGap: str = "20%"


class LineChartConfig(ChartConfigBase):
    """Complete configuration for Recharts LineChart."""

    xAxis: AxisConfig
    yAxis: AxisConfig
    lines: list[LineConfig]


class AreaChartConfig(ChartConfigBase):
    """Complete configuration for Recharts AreaChart."""

    xAxis: AxisConfig
    yAxis: AxisConfig
    areas: list[AreaConfig]
    stackId: str | None = None  # For stacked area charts


class PieChartConfig(ChartConfigBase):
    """Complete configuration for Recharts PieChart."""

    pie: PieConfig
    colors: list[str]


class ScatterChartConfig(ChartConfigBase):
    """Complete configuration for Recharts ScatterChart."""

    xAxis: AxisConfig
    yAxis: AxisConfig
    scatter: dict[str, Any]


class ComboChartConfig(ChartConfigBase):
    """Complete configuration for combo charts (bar + line)."""

    xAxis: AxisConfig
    yAxis: AxisConfig
    bars: list[BarConfig]
    lines: list[LineConfig]


class RechartsSchema(BaseModel):
    """
    Top-level schema for Recharts JSON configuration.

    This is what gets serialized to JSON and consumed by React components.
    """

    type: Literal["bar", "line", "area", "pie", "scatter", "combo", "waterfall", "bullet"]
    data: list[dict[str, Any]]
    config: dict[str, Any]  # Will be one of the *Config types above

    class Config:
        extra = "allow"  # Allow additional fields


def validate_kds_compliance(config: dict[str, Any]) -> list[str]:
    """
    Validate chart configuration against KDS guidelines.

    Args:
        config: Chart configuration dictionary

    Returns:
        List of compliance violations (empty if compliant)
    """
    violations = []

    # Check gridLines
    if config.get("gridLines", False):
        violations.append("gridLines must be False for KDS compliance")

    # Check axis lines
    if config.get("xAxis", {}).get("axisLine", True):
        violations.append("xAxis.axisLine should be False")
    if config.get("yAxis", {}).get("axisLine", True):
        violations.append("yAxis.axisLine should be False")

    # Check tick lines
    if config.get("xAxis", {}).get("tickLine", True):
        violations.append("xAxis.tickLine should be False")
    if config.get("yAxis", {}).get("tickLine", True):
        violations.append("yAxis.tickLine should be False")

    # Check font family
    font = config.get("fontFamily", "")
    if "Inter" not in font and "Arial" not in font:
        violations.append(f"fontFamily should include Inter or Arial, got: {font}")

    return violations
