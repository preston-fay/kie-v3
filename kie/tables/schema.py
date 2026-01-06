"""
Table Schema Definitions

Pydantic models for table configurations consumed by React components.
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ColumnType(str, Enum):
    """Column data types."""

    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    LINK = "link"
    IMAGE = "image"
    SPARKLINE = "sparkline"
    TAG = "tag"


class Alignment(str, Enum):
    """Text alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class SortDirection(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


class ConditionalFormatType(str, Enum):
    """Conditional formatting types."""

    COLOR_SCALE = "color_scale"
    DATA_BARS = "data_bars"
    ICONS = "icons"
    THRESHOLD = "threshold"
    HIGHLIGHT = "highlight"


class NumberFormat(BaseModel):
    """Number formatting options."""

    decimals: int = 0
    thousands_separator: bool = True
    abbreviate: bool = False  # K/M/B abbreviation
    prefix: str = ""
    suffix: str = ""
    negative_style: Literal["minus", "parentheses", "red"] = "minus"


class CurrencyFormat(BaseModel):
    """Currency formatting options."""

    currency_code: str = "USD"
    symbol: str = "$"
    decimals: int = 0
    thousands_separator: bool = True
    abbreviate: bool = False
    symbol_position: Literal["prefix", "suffix"] = "prefix"


class PercentageFormat(BaseModel):
    """Percentage formatting options."""

    decimals: int = 1
    multiply_by_100: bool = True  # If value is 0.15, display as 15%


class DateFormat(BaseModel):
    """Date formatting options."""

    format: str = "MM/DD/YYYY"  # Moment.js format string
    timezone: str | None = None


class ConditionalFormat(BaseModel):
    """Conditional formatting rule."""

    type: ConditionalFormatType
    column: str

    # For COLOR_SCALE and DATA_BARS
    min_value: float | None = None
    max_value: float | None = None
    min_color: str | None = None
    max_color: str | None = None
    mid_color: str | None = None

    # For ICONS
    icon_set: Literal["arrows", "traffic_lights", "stars", "flags"] | None = None

    # For THRESHOLD
    threshold: float | None = None
    operator: Literal["gt", "gte", "lt", "lte", "eq", "neq"] | None = None
    color: str | None = None
    background_color: str | None = None
    font_weight: Literal["normal", "bold"] | None = None

    # For HIGHLIGHT
    highlight_color: str | None = None


class SparklineConfig(BaseModel):
    """Configuration for sparkline charts in cells."""

    type: Literal["line", "bar", "area"] = "line"
    data_key: str  # Key in row data containing array of values
    color: str | None = None
    width: int = 100
    height: int = 30
    show_tooltip: bool = True


class ColumnConfig(BaseModel):
    """Configuration for a table column."""

    key: str  # Data key
    header: str  # Display name
    type: ColumnType = ColumnType.TEXT
    width: int | None = None  # Fixed width in pixels
    min_width: int = 100
    max_width: int | None = None
    alignment: Alignment = Alignment.LEFT
    sortable: bool = True
    filterable: bool = True
    resizable: bool = True
    hidden: bool = False
    frozen: bool = False  # Pin to left/right

    # Formatting
    number_format: NumberFormat | None = None
    currency_format: CurrencyFormat | None = None
    percentage_format: PercentageFormat | None = None
    date_format: DateFormat | None = None

    # Conditional formatting
    conditional_formats: list[ConditionalFormat] = Field(default_factory=list)

    # Sparkline (for SPARKLINE type)
    sparkline_config: SparklineConfig | None = None

    # Custom cell renderer
    cell_renderer: str | None = None  # Name of custom renderer function

    # Footer aggregation
    footer_aggregate: Literal["sum", "avg", "min", "max", "count"] | None = None


class PaginationConfig(BaseModel):
    """Pagination configuration."""

    enabled: bool = True
    page_size: int = 25
    page_size_options: list[int] = Field(default_factory=lambda: [10, 25, 50, 100])
    show_page_size_selector: bool = True


class SortConfig(BaseModel):
    """Sort configuration."""

    column: str
    direction: SortDirection = SortDirection.ASC


class FilterConfig(BaseModel):
    """Filter configuration."""

    column: str
    operator: Literal["contains", "equals", "gt", "gte", "lt", "lte", "between", "in"]
    value: str | int | float | list[Any]


class TableStyle(BaseModel):
    """Table styling options."""

    striped_rows: bool = True
    hover_highlight: bool = True
    bordered: bool = False
    compact: bool = False
    header_background: str | None = None
    header_text_color: str | None = None
    row_height: int = 48
    font_size: int = 14


class ExportConfig(BaseModel):
    """Export configuration."""

    enabled: bool = True
    formats: list[Literal["csv", "excel", "pdf", "json"]] = Field(
        default_factory=lambda: ["csv", "excel"]
    )
    filename: str = "table_export"
    include_filters: bool = True
    include_sorting: bool = True


class TableConfig(BaseModel):
    """Complete table configuration."""

    # Metadata
    title: str | None = None
    description: str | None = None

    # Columns
    columns: list[ColumnConfig]

    # Data
    data: list[dict[str, Any]]

    # Features
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    initial_sort: list[SortConfig] | None = None
    initial_filters: list[FilterConfig] | None = None

    # Styling
    style: TableStyle = Field(default_factory=TableStyle)

    # Export
    export_config: ExportConfig = Field(default_factory=ExportConfig)

    # Search
    global_search_enabled: bool = True
    search_placeholder: str = "Search..."

    # Selection
    selectable_rows: bool = False
    multi_select: bool = False

    # Expandable rows
    expandable: bool = False
    expand_render: str | None = None  # Custom renderer for expanded content

    # Totals row
    show_totals_row: bool = False
    totals_label: str = "Total"

    # Theme (auto-populated from global theme)
    theme_mode: Literal["dark", "light"] | None = None


class TableResponse(BaseModel):
    """Response from table builder."""

    config: TableConfig
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
