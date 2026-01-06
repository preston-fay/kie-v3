"""
Smart Formatting Utilities for Charts

Automatic number formatting, label generation, and data transformations.
"""

import re


def format_number(
    value: int | float,
    precision: int = 1,
    prefix: str = "",
    suffix: str = "",
    abbreviate: bool = True,
) -> str:
    """
    Format a number with K/M/B abbreviations.

    Args:
        value: Number to format
        precision: Decimal places for abbreviated numbers
        prefix: Prefix (e.g., "$" for currency)
        suffix: Suffix (e.g., "%" for percentages)
        abbreviate: Whether to use K/M/B abbreviations

    Returns:
        Formatted string

    Examples:
        >>> format_number(1234)
        '1.2K'
        >>> format_number(1234567, prefix="$")
        '$1.2M'
        >>> format_number(1234567890, prefix="$", precision=2)
        '$1.23B'
        >>> format_number(42, abbreviate=False)
        '42'
    """
    if not abbreviate:
        return f"{prefix}{value:,.0f}{suffix}"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000:
        formatted = f"{abs_value / 1_000_000_000:.{precision}f}B"
    elif abs_value >= 1_000_000:
        formatted = f"{abs_value / 1_000_000:.{precision}f}M"
    elif abs_value >= 1_000:
        formatted = f"{abs_value / 1_000:.{precision}f}K"
    else:
        formatted = f"{abs_value:.{precision}f}"

    return f"{sign}{prefix}{formatted}{suffix}"


def format_currency(
    value: int | float,
    currency: str = "$",
    precision: int = 1,
    abbreviate: bool = True,
) -> str:
    """
    Format a number as currency.

    Args:
        value: Amount
        currency: Currency symbol
        precision: Decimal places
        abbreviate: Use K/M/B abbreviations

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(1234567)
        '$1.2M'
        >>> format_currency(1234567, currency="€", precision=2)
        '€1.23M'
    """
    return format_number(value, precision=precision, prefix=currency, abbreviate=abbreviate)


def format_percentage(
    value: int | float,
    precision: int = 1,
    multiply_by_100: bool = False,
) -> str:
    """
    Format a number as percentage.

    Args:
        value: Value to format
        precision: Decimal places
        multiply_by_100: If True, multiply by 100 (for decimal values like 0.15 → 15%)

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(15.5)
        '15.5%'
        >>> format_percentage(0.155, multiply_by_100=True)
        '15.5%'
    """
    if multiply_by_100:
        value = value * 100
    return f"{value:.{precision}f}%"


def format_change(
    value: int | float,
    precision: int = 1,
    show_sign: bool = True,
    as_percentage: bool = False,
) -> str:
    """
    Format a change/delta value with + or - sign.

    Args:
        value: Change value
        precision: Decimal places
        show_sign: Show + for positive values
        as_percentage: Format as percentage

    Returns:
        Formatted change string

    Examples:
        >>> format_change(15.5)
        '+15.5'
        >>> format_change(-8.2)
        '-8.2'
        >>> format_change(0.15, as_percentage=True)
        '+15.0%'
    """
    if as_percentage:
        value = value * 100
        suffix = "%"
    else:
        suffix = ""

    if value > 0 and show_sign:
        return f"+{value:.{precision}f}{suffix}"
    else:
        return f"{value:.{precision}f}{suffix}"


def generate_label(text: str, max_length: int | None = None) -> str:
    """
    Generate a clean label from text.

    - Converts snake_case and camelCase to Title Case
    - Truncates to max_length if specified

    Args:
        text: Input text
        max_length: Maximum length (adds "..." if truncated)

    Returns:
        Formatted label

    Examples:
        >>> generate_label("revenue_usd")
        'Revenue Usd'
        >>> generate_label("totalRevenue")
        'Total Revenue'
        >>> generate_label("very_long_label_name", max_length=15)
        'Very Long Lab...'
    """
    # Convert snake_case to spaces
    text = text.replace("_", " ")

    # Convert camelCase to spaces
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    # Title case
    text = text.title()

    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[: max_length - 3] + "..."

    return text


def calculate_percentages(
    values: list[int | float],
    precision: int = 1,
) -> list[float]:
    """
    Calculate percentages for a list of values.

    Args:
        values: List of numbers
        precision: Decimal places

    Returns:
        List of percentages that sum to 100

    Examples:
        >>> calculate_percentages([25, 50, 25])
        [25.0, 50.0, 25.0]
        >>> calculate_percentages([10, 20, 30])
        [16.7, 33.3, 50.0]
    """
    total = sum(values)
    if total == 0:
        return [0.0] * len(values)

    return [round((v / total) * 100, precision) for v in values]


def smart_round(value: int | float, significant_digits: int = 3) -> int | float:
    """
    Round to significant digits for cleaner charts.

    Args:
        value: Number to round
        significant_digits: Number of significant digits

    Returns:
        Rounded value

    Examples:
        >>> smart_round(1234567)
        1230000
        >>> smart_round(0.001234, significant_digits=2)
        0.0012
    """
    if value == 0:
        return 0

    from math import floor, log10

    magnitude = floor(log10(abs(value)))
    factor = 10 ** (significant_digits - magnitude - 1)
    return round(value * factor) / factor


def format_axis_label(
    value: int | float,
    axis_type: str = "numeric",
) -> str:
    """
    Format axis label based on type.

    Args:
        value: Value to format
        axis_type: "numeric", "currency", "percentage", "time"

    Returns:
        Formatted label

    Examples:
        >>> format_axis_label(1500000, axis_type="currency")
        '$1.5M'
        >>> format_axis_label(0.25, axis_type="percentage")
        '25%'
    """
    if axis_type == "currency":
        return format_currency(value)
    elif axis_type == "percentage":
        return format_percentage(value, multiply_by_100=True)
    elif axis_type == "numeric":
        return format_number(value)
    else:
        return str(value)
