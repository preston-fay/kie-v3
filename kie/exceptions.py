"""
KIE v3 Exception Classes

Custom exceptions for better error handling and debugging.
"""

from typing import Any


class KIEError(Exception):
    """Base exception for all KIE v3 errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# Configuration Errors
class ConfigurationError(KIEError):
    """Raised when configuration is invalid or missing."""
    pass


# Data Errors
class DataError(KIEError):
    """Base class for data-related errors."""
    pass


class DataLoadError(DataError):
    """Raised when data cannot be loaded."""
    pass


class DataValidationError(DataError):
    """Raised when data fails validation."""
    pass


# Chart Errors
class ChartError(KIEError):
    """Base class for chart-related errors."""
    pass


class ChartBuildError(ChartError):
    """Raised when chart cannot be built."""
    pass


class ChartValidationError(ChartError):
    """Raised when chart config is invalid."""
    pass


# Geocoding Errors
class GeocodingError(KIEError):
    """Base class for geocoding-related errors."""
    pass


class GeocodingServiceError(GeocodingError):
    """Raised when geocoding service fails."""
    pass


class GeocodingRateLimitError(GeocodingError):
    """Raised when geocoding rate limit is exceeded."""
    pass


class APIKeyError(GeocodingError):
    """Raised when API key is missing or invalid."""
    pass


# Brand Errors
class BrandComplianceError(KIEError):
    """Raised when output violates KDS brand guidelines."""
    pass


class ForbiddenColorError(BrandComplianceError):
    """Raised when forbidden colors (e.g., green) are detected."""
    pass


# Export Errors
class ExportError(KIEError):
    """Base class for export-related errors."""
    pass


class PowerPointExportError(ExportError):
    """Raised when PowerPoint export fails."""
    pass


class HTMLExportError(ExportError):
    """Raised when HTML export fails."""
    pass


# API Errors
class APIError(KIEError):
    """Base class for API-related errors."""
    pass


class APIRequestError(APIError):
    """Raised when API request fails."""
    pass


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass
