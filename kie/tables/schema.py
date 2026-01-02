"""
Table Schema Definitions

Pydantic models for table configurations consumed by React components.
"""

from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


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
    timezone: Optional[str] = None


class ConditionalFormat(BaseModel):
    """Conditional formatting rule."""

    type: ConditionalFormatType
    column: str

    # For COLOR_SCALE and DATA_BARS
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_color: Optional[str] = None
    max_color: Optional[str] = None
    mid_color: Optional[str] = None

    # For ICONS
    icon_set: Optional[Literal["arrows", "traffic_lights", "stars", "flags"]] = None

    # For THRESHOLD
    threshold: Optional[float] = None
    operator: Optional[Literal["gt", "gte", "lt", "lte", "eq", "neq"]] = None
    color: Optional[str] = None
    background_color: Optional[str] = None
    font_weight: Optional[Literal["normal", "bold"]] = None

    # For HIGHLIGHT
    highlight_color: Optional[str] = None


class SparklineConfig(BaseModel):
    """Configuration for sparkline charts in cells."""

    type: Literal["line", "bar", "area"] = "line"
    data_key: str  # Key in row data containing array of values
    color: Optional[str] = None
    width: int = 100
    height: int = 30
    show_tooltip: bool = True


class ColumnConfig(BaseModel):
    """Configuration for a table column."""

    key: str  # Data key
    header: str  # Display name
    type: ColumnType = ColumnType.TEXT
    width: Optional[int] = None  # Fixed width in pixels
    min_width: int = 100
    max_width: Optional[int] = None
    alignment: Alignment = Alignment.LEFT
    sortable: bool = True
    filterable: bool = True
    resizable: bool = True
    hidden: bool = False
    frozen: bool = False  # Pin to left/right

    # Formatting
    number_format: Optional[NumberFormat] = None
    currency_format: Optional[CurrencyFormat] = None
    percentage_format: Optional[PercentageFormat] = None
    date_format: Optional[DateFormat] = None

    # Conditional formatting
    conditional_formats: List[ConditionalFormat] = Field(default_factory=list)

    # Sparkline (for SPARKLINE type)
    sparkline_config: Optional[SparklineConfig] = None

    # Custom cell renderer
    cell_renderer: Optional[str] = None  # Name of custom renderer function

    # Footer aggregation
    footer_aggregate: Optional[Literal["sum", "avg", "min", "max", "count"]] = None


class PaginationConfig(BaseModel):
    """Pagination configuration."""

    enabled: bool = True
    page_size: int = 25
    page_size_options: List[int] = Field(default_factory=lambda: [10, 25, 50, 100])
    show_page_size_selector: bool = True


class SortConfig(BaseModel):
    """Sort configuration."""

    column: str
    direction: SortDirection = SortDirection.ASC


class FilterConfig(BaseModel):
    """Filter configuration."""

    column: str
    operator: Literal["contains", "equals", "gt", "gte", "lt", "lte", "between", "in"]
    value: Union[str, int, float, List[Any]]


class TableStyle(BaseModel):
    """Table styling options."""

    striped_rows: bool = True
    hover_highlight: bool = True
    bordered: bool = False
    compact: bool = False
    header_background: Optional[str] = None
    header_text_color: Optional[str] = None
    row_height: int = 48
    font_size: int = 14


class ExportConfig(BaseModel):
    """Export configuration."""

    enabled: bool = True
    formats: List[Literal["csv", "excel", "pdf", "json"]] = Field(
        default_factory=lambda: ["csv", "excel"]
    )
    filename: str = "table_export"
    include_filters: bool = True
    include_sorting: bool = True


class TableConfig(BaseModel):
    """Complete table configuration."""

    # Metadata
    title: Optional[str] = None
    description: Optional[str] = None

    # Columns
    columns: List[ColumnConfig]

    # Data
    data: List[Dict[str, Any]]

    # Features
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    initial_sort: Optional[List[SortConfig]] = None
    initial_filters: Optional[List[FilterConfig]] = None

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
    expand_render: Optional[str] = None  # Custom renderer for expanded content

    # Totals row
    show_totals_row: bool = False
    totals_label: str = "Total"

    # Theme (auto-populated from global theme)
    theme_mode: Optional[Literal["dark", "light"]] = None


class TableResponse(BaseModel):
    """Response from table builder."""

    config: TableConfig
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
