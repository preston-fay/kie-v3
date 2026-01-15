"""
Unified output formatting for all evidence and display values.

Provides smart formatting based on context and value magnitude.
"""

from kie.charts.formatting import format_number, format_percentage, format_currency


def format_evidence_value(value: any, evidence_type: str) -> str:
    """
    Smart format evidence values based on type and magnitude.

    Args:
        value: Value to format (int, float, str, etc.)
        evidence_type: Type hint for formatting (currency, percentage, metric, statistic)

    Returns:
        Formatted string appropriate for consultant-grade output
    """
    if not isinstance(value, (int, float)):
        return str(value)

    # Detect format type from evidence_type
    evidence_lower = evidence_type.lower()

    if evidence_lower in ['currency', 'revenue', 'cost', 'value', 'price']:
        return format_currency(value)
    elif evidence_lower in ['percentage', 'rate', 'ratio', 'share'] or '%' in str(value):
        # Already formatted percentages keep their formatting
        if isinstance(value, str) and '%' in value:
            return value
        # Otherwise format as percentage (value in decimal form 0-1)
        if abs(value) < 1:
            return format_percentage(value, multiply_by_100=True)
        else:
            # Value already in percentage form (e.g., 75 means 75%)
            return format_percentage(value, multiply_by_100=False)
    elif abs(value) > 10000:
        # Large numbers use K/M/B abbreviation
        return format_number(value)
    elif isinstance(value, int):
        return f"{value:,}"
    else:
        # Float with 2 decimal places
        return f"{value:,.2f}"
