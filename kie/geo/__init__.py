"""
Geographic Data System for KIE v3

Complete geocoding, mapping, and spatial analysis capabilities.
"""

# Models
# FIPS codes
from kie.geo.fips import FIPSEnricher, zip_to_fips_approximation

# Maps
from kie.geo.maps import (
    ChoroplethConfig,
    HeatmapConfig,
    LayerConfig,
    MapBuilder,
    MapConfig,
    MarkerConfig,
)
from kie.geo.maps.folium_builder import (
    create_heatmap,
    create_marker_map,
    create_us_choropleth,
)
from kie.geo.models import (
    BatchGeocodingResult,
    GeocodingRequest,
    GeocodingResult,
    GeocodingService,
    GeocodingStatus,
    ReverseGeocodingResult,
)

# Pipeline
from kie.geo.pipeline import GeocodingPipeline
from kie.geo.services.census import CensusGeocoder
from kie.geo.services.google import GoogleMapsGeocoder
from kie.geo.services.mapbox import MapboxGeocoder

# Geocoding services
from kie.geo.services.nominatim import NominatimGeocoder

# Export
# from kie.geo.export import GeoExporter, export_geocoding_results  # Not yet implemented
# Utils
from kie.geo.utils import (
    GeocodingCache,
    RateLimiter,
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
