"""
KIE v3 Base Classes

Abstract base classes for charts, geocoders, exporters, etc.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RechartsConfig:
    """Base configuration for Recharts visualizations."""

    chart_type: str
    data: list[dict[str, Any]]
    config: dict[str, Any]
    title: str | None = None
    subtitle: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.chart_type,
            "data": self.data,
            "config": self.config,
            "title": self.title,
            "subtitle": self.subtitle,
        }

    def to_json(self, path: Path | None = None, indent: int = 2) -> str:
        """
        Convert to JSON string.

        Args:
            path: Optional path to save JSON file
            indent: JSON indentation level

        Returns:
            JSON string
        """
        json_str = json.dumps(self.to_dict(), indent=indent)

        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str)

        return json_str

    def to_svg(self, output_path: Path | str) -> Path:
        """
        Render chart to SVG using Pygal (pure Python).

        Falls back to JSON if rendering fails.

        Args:
            output_path: Path to save SVG file

        Returns:
            Path to saved file (SVG if successful, JSON if fallback)
        """
        output_path = Path(output_path)

        # First save JSON (for backward compatibility and debugging)
        json_path = output_path.with_suffix('.json')
        self.to_json(json_path)

        # Render using Pygal (pure Python - no Node.js needed)
        try:
            from kie.charts.svg_renderer import to_svg as pygal_to_svg

            svg_path = pygal_to_svg(self, output_path)

            if svg_path.exists():
                # print(f"✓ Rendered chart to {svg_path}")  # Commented to reduce noise
                return svg_path
            else:
                print(f"⚠️  SVG rendering failed - chart saved as JSON only")
                return json_path

        except ValueError as e:
            # KDS validation failure or unsupported chart type
            print(f"⚠️  Chart rendering failed: {e}")
            return json_path
        except Exception as e:
            print(f"⚠️  Unexpected rendering error: {e}")
            return json_path


    @classmethod
    def from_json(cls, json_str: str) -> "RechartsConfig":
        """Load from JSON string."""
        data = json.loads(json_str)
        return cls(
            chart_type=data["type"],
            data=data["data"],
            config=data["config"],
            title=data.get("title"),
            subtitle=data.get("subtitle"),
        )


class ChartBuilder(ABC):
    """
    Abstract base class for chart builders.

    Chart builders generate Recharts-compatible JSON configurations
    from data. They do NOT render charts directly - that's the job
    of React components.
    """

    @abstractmethod
    def build(self, data: Any, **kwargs) -> RechartsConfig:
        """
        Build chart configuration from data.

        Args:
            data: Input data (pandas DataFrame, list of dicts, etc.)
            **kwargs: Chart-specific configuration options

        Returns:
            RechartsConfig object ready for JSON serialization
        """
        pass

    def save(self, data: Any, output_path: Path, **kwargs) -> Path:
        """
        Build chart and save JSON config to file.

        Args:
            data: Input data
            output_path: Path to save JSON file
            **kwargs: Chart-specific configuration options

        Returns:
            Path to saved JSON file
        """
        config = self.build(data, **kwargs)
        config.to_json(output_path)
        return output_path


@dataclass
class GeocodingResult:
    """Result from a geocoding operation."""

    address: str
    latitude: float | None = None
    longitude: float | None = None
    fips_code: str | None = None
    confidence: float = 0.0
    service: str | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        """Check if geocoding was successful."""
        return self.latitude is not None and self.longitude is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "fips_code": self.fips_code,
            "confidence": self.confidence,
            "service": self.service,
            "error": self.error,
            "success": self.success,
        }


class Geocoder(ABC):
    """
    Abstract base class for geocoding services.

    Geocoders convert addresses to lat/long coordinates and enrich
    with FIPS codes.
    """

    def __init__(
        self,
        rate_limit: float = 1.0,
        timeout: int = 10,
        max_retries: int = 3,
    ):
        """
        Initialize geocoder.

        Args:
            rate_limit: Requests per second
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def geocode(
        self,
        address: str,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
        country: str = "US",
    ) -> GeocodingResult:
        """
        Geocode a single address.

        Args:
            address: Street address
            city: City name
            state: State abbreviation
            zip_code: ZIP/postal code
            country: Country code (default: US)

        Returns:
            GeocodingResult with lat/long and metadata
        """
        pass

    @abstractmethod
    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> GeocodingResult:
        """
        Reverse geocode from coordinates to address.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            GeocodingResult with address and metadata
        """
        pass

    async def geocode_batch(
        self, addresses: list[str], batch_size: int = 100
    ) -> list[GeocodingResult | None]:
        """
        Geocode multiple addresses in batches.

        Args:
            addresses: List of addresses to geocode
            batch_size: Number of addresses per batch

        Returns:
            List of GeocodingResults (None for failures)
        """
        results: list[GeocodingResult | None] = []

        for i in range(0, len(addresses), batch_size):
            batch = addresses[i : i + batch_size]
            for address in batch:
                try:
                    result = await self.geocode(address)
                    results.append(result if result.success else None)
                except Exception as e:
                    results.append(
                        GeocodingResult(
                            address=address, error=str(e), service=self.__class__.__name__
                        )
                    )

        return results


class Exporter(ABC):
    """
    Abstract base class for exporters.

    Exporters take KIE outputs (charts, insights, data) and generate
    final deliverables (PowerPoint, HTML, PDF, etc.).
    """

    @abstractmethod
    def export(
        self, inputs: dict[str, Any], output_path: Path, **kwargs
    ) -> Path:
        """
        Export deliverable.

        Args:
            inputs: Dictionary of input artifacts (charts, data, etc.)
            output_path: Path for output file
            **kwargs: Exporter-specific options

        Returns:
            Path to exported file
        """
        pass


class BrandValidator(ABC):
    """
    Abstract base class for brand compliance validators.

    Validators check outputs against KDS guidelines and flag violations.
    """

    @abstractmethod
    def validate(self, artifact: Any) -> dict[str, Any]:
        """
        Validate artifact against brand guidelines.

        Args:
            artifact: Artifact to validate (chart config, HTML, etc.)

        Returns:
            Dictionary with validation results:
            {
                "compliant": bool,
                "violations": List[str],
                "warnings": List[str]
            }
        """
        pass
