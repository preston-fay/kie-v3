"""
Geographic Data System for KIE v3

Complete geocoding, mapping, and spatial analysis capabilities.
"""

# Models
from kie.geo.models import (
    GeocodingRequest,
    GeocodingResult,
    BatchGeocodingResult,
    GeocodingStatus,
    GeocodingService,
    ReverseGeocodingResult,
)

# Geocoding services
from kie.geo.services.nominatim import NominatimGeocoder
from kie.geo.services.census import CensusGeocoder
from kie.geo.services.google import GoogleMapsGeocoder
from kie.geo.services.mapbox import MapboxGeocoder

# Pipeline
from kie.geo.pipeline import GeocodingPipeline

# FIPS codes
from kie.geo.fips import FIPSEnricher, zip_to_fips_approximation

# Maps
from kie.geo.maps import (
    MapBuilder,
    MapConfig,
    LayerConfig,
    ChoroplethConfig,
    MarkerConfig,
    HeatmapConfig,
)
from kie.geo.maps.folium_builder import (
    create_us_choropleth,
    create_marker_map,
    create_heatmap,
)

# Export
# from kie.geo.export import GeoExporter, export_geocoding_results  # Not yet implemented

# Utils
from kie.geo.utils import (
    RateLimiter,
    GeocodingCache,
    normalize_address,
    # parse_coordinates,  # Not yet implemented
    validate_coordinates,
)

__all__ = [
    # Models
    "GeocodingRequest",
    "GeocodingResult",
    "BatchGeocodingResult",
    "GeocodingStatus",
    "GeocodingService",
    "ReverseGeocodingResult",
    # Services
    "NominatimGeocoder",
    "CensusGeocoder",
    "GoogleMapsGeocoder",
    "MapboxGeocoder",
    # Pipeline
    "GeocodingPipeline",
    # FIPS
    "FIPSEnricher",
    "zip_to_fips_approximation",
    # Maps
    "MapBuilder",
    "MapConfig",
    "LayerConfig",
    "ChoroplethConfig",
    "MarkerConfig",
    "HeatmapConfig",
    "create_us_choropleth",
    "create_marker_map",
    "create_heatmap",
    # Export
    # "GeoExporter",
    # "export_geocoding_results",
    # Utils
    "RateLimiter",
    "GeocodingCache",
    "normalize_address",
    # "parse_coordinates",
    "validate_coordinates",
]
