"""
Geocoding Utilities

Helper functions for rate limiting, caching, and address normalization.
"""

import asyncio
import time
import hashlib
from typing import Optional, Dict, Any
from functools import wraps
import pandas as pd


class RateLimiter:
    """
    Rate limiter for API requests.

    Ensures we don't exceed service rate limits.
    """

    def __init__(self, requests_per_second: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    async def wait(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        time_since_last = now - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def __call__(self, func):
        """Decorator for rate-limited functions."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            await self.wait()
            return await func(*args, **kwargs)

        return wrapper


class GeocodingCache:
    """
    Simple in-memory cache for geocoding results.

    Prevents redundant API calls for the same addresses.
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached entries
        """
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _make_key(self, address: str, **kwargs) -> str:
        """Create cache key from address and parameters."""
        parts = [address.lower().strip()]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                parts.append(f"{k}:{v}")
        key_string = "|".join(parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, address: str, **kwargs) -> Optional[Any]:
        """Get cached result."""
        key = self._make_key(address, **kwargs)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, address: str, result: Any, **kwargs):
        """Store result in cache."""
        if len(self.cache) >= self.max_size:
            # Simple eviction: remove oldest (first) entry
            self.cache.pop(next(iter(self.cache)))

        key = self._make_key(address, **kwargs)
        self.cache[key] = result

    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100


def normalize_address(address: str) -> str:
    """
    Normalize address for better geocoding results.

    - Remove extra whitespace
    - Standardize abbreviations
    - Fix common issues

    Args:
        address: Raw address string

    Returns:
        Normalized address string
    """
    if not address:
        return ""

    # Remove extra whitespace
    address = " ".join(address.split())

    # Common abbreviations
    replacements = {
        " st ": " street ",
        " st.": " street",
        " ave ": " avenue ",
        " ave.": " avenue",
        " blvd ": " boulevard ",
        " blvd.": " boulevard",
        " rd ": " road ",
        " rd.": " road",
        " dr ": " drive ",
        " dr.": " drive",
        " ln ": " lane ",
        " ln.": " lane",
        " ct ": " court ",
        " ct.": " court",
    }

    address_lower = address.lower()
    for old, new in replacements.items():
        address_lower = address_lower.replace(old, new)

    return address_lower.strip()


def has_geocoding(df: pd.DataFrame) -> bool:
    """
    Check if DataFrame already has geocoding data.

    Args:
        df: Pandas DataFrame

    Returns:
        True if latitude and longitude columns exist
    """
    lat_cols = ["latitude", "lat", "Latitude", "LAT"]
    lon_cols = ["longitude", "lon", "long", "Longitude", "LON", "LONG"]

    has_lat = any(col in df.columns for col in lat_cols)
    has_lon = any(col in df.columns for col in lon_cols)

    return has_lat and has_lon


def extract_coordinates(df: pd.DataFrame) -> Optional[tuple]:
    """
    Extract latitude and longitude columns from DataFrame.

    Args:
        df: Pandas DataFrame

    Returns:
        Tuple of (lat_col_name, lon_col_name) or None if not found
    """
    lat_cols = ["latitude", "lat", "Latitude", "LAT"]
    lon_cols = ["longitude", "lon", "long", "Longitude", "LON", "LONG"]

    lat_col = None
    for col in lat_cols:
        if col in df.columns:
            lat_col = col
            break

    lon_col = None
    for col in lon_cols:
        if col in df.columns:
            lon_col = col
            break

    if lat_col and lon_col:
        return (lat_col, lon_col)

    return None


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate latitude and longitude values.

    Args:
        latitude: Latitude value
        longitude: Longitude value

    Returns:
        True if coordinates are valid
    """
    if latitude is None or longitude is None:
        return False

    # Latitude: -90 to 90
    if not (-90 <= latitude <= 90):
        return False

    # Longitude: -180 to 180
    if not (-180 <= longitude <= 180):
        return False

    return True


def calculate_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2

    # Earth radius in kilometers
    R = 6371.0

    # Convert to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def format_geocoding_stats(
    total: int,
    success: int,
    failed: int,
    duration: float,
) -> str:
    """
    Format geocoding statistics for display.

    Args:
        total: Total addresses processed
        success: Successful geocodes
        failed: Failed geocodes
        duration: Total duration in seconds

    Returns:
        Formatted statistics string
    """
    success_rate = (success / total * 100) if total > 0 else 0
    rate_per_sec = total / duration if duration > 0 else 0

    lines = [
        f"Geocoding Results:",
        f"  Total: {total}",
        f"  ✅ Success: {success} ({success_rate:.1f}%)",
        f"  ❌ Failed: {failed}",
        f"  Duration: {duration:.1f}s",
        f"  Rate: {rate_per_sec:.1f} addresses/sec",
    ]

    return "\n".join(lines)
