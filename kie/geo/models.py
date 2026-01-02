"""
Geocoding Data Models

Structured data classes for geocoding results and requests.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class GeocodingService(str, Enum):
    """Supported geocoding services."""

    NOMINATIM = "nominatim"
    CENSUS = "census"
    GOOGLE = "google"
    MAPBOX = "mapbox"
    MANUAL = "manual"


class GeocodingStatus(str, Enum):
    """Geocoding result status."""

    SUCCESS = "success"
    PARTIAL = "partial"  # Low confidence
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    API_ERROR = "api_error"


@dataclass
class GeocodingRequest:
    """Request for geocoding operation."""

    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "US"

    # Request metadata
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }

    def get_full_address(self) -> str:
        """Get full address string."""
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)
        if self.country and self.country != "US":
            parts.append(self.country)
        return ", ".join(parts)


@dataclass
class GeocodingResult:
    """Result from geocoding operation."""

    # Input
    original_address: str

    # Output coordinates
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Normalized address components
    formatted_address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None

    # Geographic codes
    fips_code: Optional[str] = None  # State + County FIPS
    fips_state: Optional[str] = None  # 2-digit state FIPS
    fips_county: Optional[str] = None  # 3-digit county FIPS

    # Metadata
    confidence: float = 0.0  # 0.0 to 1.0
    match_type: Optional[str] = None  # "exact", "approximate", "interpolated"
    service: Optional[str] = None
    status: GeocodingStatus = GeocodingStatus.FAILED
    error_message: Optional[str] = None

    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None

    @property
    def success(self) -> bool:
        """Check if geocoding was successful."""
        return self.status == GeocodingStatus.SUCCESS and self.latitude is not None

    @property
    def coordinates(self) -> Optional[tuple]:
        """Get (latitude, longitude) tuple."""
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_address": self.original_address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "formatted_address": self.formatted_address,
            "street": self.street,
            "city": self.city,
            "county": self.county,
            "state": self.state,
            "state_code": self.state_code,
            "zip_code": self.zip_code,
            "country": self.country,
            "country_code": self.country_code,
            "fips_code": self.fips_code,
            "fips_state": self.fips_state,
            "fips_county": self.fips_county,
            "confidence": self.confidence,
            "match_type": self.match_type,
            "service": self.service,
            "status": self.status.value,
            "error_message": self.error_message,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms,
        }

    @classmethod
    def from_error(
        cls,
        address: str,
        error: str,
        service: Optional[str] = None,
        status: GeocodingStatus = GeocodingStatus.FAILED,
    ) -> "GeocodingResult":
        """Create result from error."""
        return cls(
            original_address=address,
            error_message=error,
            service=service,
            status=status,
        )


@dataclass
class BatchGeocodingResult:
    """Result from batch geocoding operation."""

    results: List[GeocodingResult]
    total_count: int
    success_count: int
    failed_count: int
    partial_count: int

    # Timing
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float

    # Service stats
    service_stats: Dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "partial_count": self.partial_count,
            "success_rate": self.success_rate,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_duration_seconds": self.total_duration_seconds,
            "service_stats": self.service_stats,
        }

    def get_failed_addresses(self) -> List[str]:
        """Get list of addresses that failed geocoding."""
        return [
            r.original_address
            for r in self.results
            if not r.success
        ]

    def get_low_confidence_results(self, threshold: float = 0.7) -> List[GeocodingResult]:
        """Get results with confidence below threshold."""
        return [
            r for r in self.results
            if r.success and r.confidence < threshold
        ]


@dataclass
class ReverseGeocodingResult:
    """Result from reverse geocoding (lat/long → address)."""

    # Input coordinates
    latitude: float
    longitude: float

    # Output address
    formatted_address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

    # Geographic codes
    fips_code: Optional[str] = None
    fips_state: Optional[str] = None
    fips_county: Optional[str] = None

    # Metadata
    confidence: float = 0.0
    service: Optional[str] = None
    status: GeocodingStatus = GeocodingStatus.FAILED
    error_message: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if reverse geocoding was successful."""
        return self.status == GeocodingStatus.SUCCESS and self.formatted_address is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "formatted_address": self.formatted_address,
            "street": self.street,
            "city": self.city,
            "county": self.county,
            "state": self.state,
            "state_code": self.state_code,
            "zip_code": self.zip_code,
            "country": self.country,
            "fips_code": self.fips_code,
            "fips_state": self.fips_state,
            "fips_county": self.fips_county,
            "confidence": self.confidence,
            "service": self.service,
            "status": self.status.value,
            "error_message": self.error_message,
            "success": self.success,
        }
