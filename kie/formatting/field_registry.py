"""
Field name beautification registry for consultant-friendly output.

Maps technical column names to client-ready display names.
"""

from typing import Dict


class FieldRegistry:
    """Registry for mapping technical field names to consultant-friendly display names."""

    # Semantic mappings for common patterns
    SEMANTIC_MAPPINGS = {
        # Financial metrics
        'revenue': 'Revenue',
        'cost': 'Cost',
        'profit': 'Profit',
        'margin': 'Margin',
        'gross_margin': 'Gross Margin',
        'net_margin': 'Net Margin',
        'ebitda': 'EBITDA',
        'operating_income': 'Operating Income',
        'net_income': 'Net Income',

        # Returns and performance
        'return_1d': 'Daily Return',
        'return_7d': '7-Day Return',
        'return_30d': '30-Day Return',
        'return_90d': '90-Day Return',
        'return_1y': '1-Year Return',

        # Volatility and risk
        'volatility_7d': '7-Day Volatility',
        'volatility_30d': '30-Day Volatility',
        'volatility_90d': '90-Day Volatility',
        'std_dev': 'Standard Deviation',
        'variance': 'Variance',
        'beta': 'Beta',
        'sharpe_ratio': 'Sharpe Ratio',

        # Volume and activity
        'volume': 'Volume',
        'trading_volume': 'Trading Volume',
        'transaction_count': 'Transaction Count',
        'daily_volume': 'Daily Volume',

        # Prices
        'price': 'Price',
        'close': 'Closing Price',
        'open': 'Opening Price',
        'high': 'High Price',
        'low': 'Low Price',
        'adj_close': 'Adjusted Close',

        # Technical indicators
        'rsi': 'RSI',
        'macd': 'MACD',
        'ema': 'EMA',
        'sma': 'SMA',
        'bollinger_upper': 'Bollinger Upper Band',
        'bollinger_lower': 'Bollinger Lower Band',

        # Geographic and categorical
        'region': 'Region',
        'country': 'Country',
        'state': 'State',
        'city': 'City',
        'segment': 'Segment',
        'category': 'Category',
        'product': 'Product',
        'customer': 'Customer',

        # Time dimensions
        'date': 'Date',
        'year': 'Year',
        'quarter': 'Quarter',
        'month': 'Month',
        'week': 'Week',
        'day': 'Day',

        # Sentiment and qualitative
        'sentiment': 'Sentiment',
        'sentiment_score': 'Sentiment Score',
        'positive': 'Positive',
        'negative': 'Negative',
        'neutral': 'Neutral',

        # Environmental/commodity specific
        'temperature': 'Temperature',
        'temperature_anomaly': 'Temperature Anomaly',
        'precipitation': 'Precipitation',
        'humidity': 'Humidity',
        'yield': 'Yield',
        'production': 'Production',
        'inventory': 'Inventory',
    }

    @classmethod
    def beautify(cls, field_name: str) -> str:
        """
        Convert technical field name to consultant-friendly display name.

        Args:
            field_name: Technical column name (e.g., 'return_7d', 'gross_margin')

        Returns:
            Client-friendly display name (e.g., '7-Day Return', 'Gross Margin')
        """
        # Check exact match first
        if field_name.lower() in cls.SEMANTIC_MAPPINGS:
            return cls.SEMANTIC_MAPPINGS[field_name.lower()]

        # Check for partial matches (e.g., 'total_revenue' -> 'Total Revenue')
        lower_name = field_name.lower()
        for key, value in cls.SEMANTIC_MAPPINGS.items():
            if key in lower_name:
                # Found a match - build the display name
                prefix = lower_name.replace(key, '').strip('_')
                if prefix:
                    # Capitalize prefix (e.g., 'total' -> 'Total')
                    prefix_clean = prefix.replace('_', ' ').title()
                    return f"{prefix_clean} {value}"
                return value

        # Fallback: Title case with underscores replaced by spaces
        return field_name.replace('_', ' ').title()

    @classmethod
    def beautify_dict(cls, data: Dict[str, any]) -> Dict[str, any]:
        """
        Beautify all keys in a dictionary.

        Args:
            data: Dictionary with technical field names as keys

        Returns:
            New dictionary with beautified keys
        """
        return {cls.beautify(key): value for key, value in data.items()}

    @classmethod
    def register_custom_mapping(cls, technical_name: str, display_name: str):
        """
        Register a custom field mapping for project-specific terminology.

        Args:
            technical_name: Technical column name
            display_name: Client-friendly display name
        """
        cls.SEMANTIC_MAPPINGS[technical_name.lower()] = display_name
