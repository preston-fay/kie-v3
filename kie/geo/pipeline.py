"""
Geocoding Pipeline

Intelligent multi-service geocoding with fallback strategy.
"""

import asyncio
import os
from datetime import datetime

from kie.exceptions import APIKeyError
from kie.geo.models import (
    BatchGeocodingResult,
    GeocodingRequest,
    GeocodingResult,
    GeocodingStatus,
)
from kie.geo.services.census import CensusGeocoder
from kie.geo.services.google import GoogleMapsGeocoder
from kie.geo.services.mapbox import MapboxGeocoder
from kie.geo.services.nominatim import NominatimGeocoder
from kie.geo.utils import GeocodingCache, format_geocoding_stats


class GeocodingPipeline:
    """
    Intelligent geocoding pipeline with fallback strategy.

    Strategy:
    1. Try free services first (Nominatim, Census)
    2. If low confidence or failure, try paid services (if API keys available)
    3. Cache results to avoid redundant requests
    4. Respect rate limits for each service
    """

    def __init__(
        self,
        preferred_service: str = "nominatim",
        fallback_services: list[str] | None = None,
        confidence_threshold: float = 0.75,
        enable_cache: bool = True,
        google_api_key: str | None = None,
        mapbox_access_token: str | None = None,
    ):
        """
        Initialize geocoding pipeline.

        Args:
            preferred_service: Service to try first ("nominatim", "census", "google", "mapbox")
            fallback_services: List of fallback services to try
            confidence_threshold: Minimum confidence to accept result
            enable_cache: Enable result caching
            google_api_key: Google Maps API key (optional)
            mapbox_access_token: Mapbox access token (optional)
        """
        self.preferred_service = preferred_service
        self.fallback_services = fallback_services or ["census"]
        self.confidence_threshold = confidence_threshold
        self.cache = GeocodingCache() if enable_cache else None

        # Load API keys from environment if not provided
        self.google_api_key = google_api_key or os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("KIE_GOOGLE_API_KEY")
        self.mapbox_access_token = mapbox_access_token or os.getenv("MAPBOX_ACCESS_TOKEN") or os.getenv("KIE_MAPBOX_ACCESS_TOKEN")

        # Initialize geocoders
        self.geocoders = {}
        self._initialize_geocoders()

    def _initialize_geocoders(self):
        """Initialize available geocoders."""
        # Always available (free)
        self.geocoders["nominatim"] = NominatimGeocoder()
        self.geocoders["census"] = CensusGeocoder()

        # Paid services (only if API keys available)
        if self.google_api_key:
            try:
                self.geocoders["google"] = GoogleMapsGeocoder(self.google_api_key)
            except APIKeyError:
                pass

        if self.mapbox_access_token:
            try:
                self.geocoders["mapbox"] = MapboxGeocoder(self.mapbox_access_token)
            except APIKeyError:
                pass

    async def geocode(
        self,
        request: GeocodingRequest,
        require_paid: bool = False,
    ) -> GeocodingResult:
        """
        Geocode an address with intelligent fallback.

        Args:
            request: GeocodingRequest
            require_paid: If True, skip free services and use paid only

        Returns:
            GeocodingResult from best available service
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(
                request.address,
                city=request.city,
                state=request.state,
                zip_code=request.zip_code,
            )
            if cached:
                return cached

        # Determine service order
        if require_paid:
            services = [s for s in [self.preferred_service] + self.fallback_services if s in ["google", "mapbox"]]
        else:
            services = [self.preferred_service] + self.fallback_services

        # Try each service
        best_result = None
        for service_name in services:
            if service_name not in self.geocoders:
                continue

            geocoder = self.geocoders[service_name]

            try:
                result = await geocoder.geocode(request)

                # Check if result is good enough
                if result.success and result.confidence >= self.confidence_threshold:
                    # Cache and return
                    if self.cache:
                        self.cache.set(
                            request.address,
                            result,
                            city=request.city,
                            state=request.state,
                            zip_code=request.zip_code,
                        )
                    return result

                # Keep best result so far
                if best_result is None or (result.success and result.confidence > best_result.confidence):
                    best_result = result

            except Exception:
                # Service failed, try next one
                continue

        # Return best result found (even if below threshold)
        if best_result:
            if self.cache:
                self.cache.set(
                    request.address,
                    best_result,
                    city=request.city,
                    state=request.state,
                    zip_code=request.zip_code,
                )
            return best_result

        # All services failed
        return GeocodingResult.from_error(
            address=request.address,
            error="All geocoding services failed",
            status=GeocodingStatus.FAILED,
        )

    async def geocode_batch(
        self,
        requests: list[GeocodingRequest],
        batch_size: int = 100,
        show_progress: bool = True,
    ) -> BatchGeocodingResult:
        """
        Geocode multiple addresses in batch.

        Args:
            requests: List of geocoding requests
            batch_size: Number of concurrent requests
            show_progress: Print progress updates

        Returns:
            BatchGeocodingResult with all results and statistics
        """
        start_time = datetime.utcnow()
        results = []

        # Process in batches
        for i in range(0, len(requests), batch_size):
            batch = requests[i : i + batch_size]

            # Geocode batch concurrently
            batch_results = await asyncio.gather(
                *[self.geocode(req) for req in batch],
                return_exceptions=True,
            )

            # Handle exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append(
                        GeocodingResult.from_error(
                            address=batch[j].address,
                            error=str(result),
                            status=GeocodingStatus.API_ERROR,
                        )
                    )
                else:
                    results.append(result)

            if show_progress:
                progress = min(i + batch_size, len(requests))
                print(f"Geocoded {progress}/{len(requests)} addresses...")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        success_count = sum(1 for r in results if r.success)
        failed_count = sum(1 for r in results if not r.success)
        partial_count = sum(1 for r in results if r.status == GeocodingStatus.PARTIAL)

        # Service statistics
        service_stats = {}
        for result in results:
            if result.service:
                service_stats[result.service] = service_stats.get(result.service, 0) + 1

        batch_result = BatchGeocodingResult(
            results=results,
            total_count=len(requests),
            success_count=success_count,
            failed_count=failed_count,
            partial_count=partial_count,
            start_time=start_time,
            end_time=end_time,
            total_duration_seconds=duration,
            service_stats=service_stats,
        )

        if show_progress:
            print("\n" + format_geocoding_stats(
                total=len(requests),
                success=success_count,
                failed=failed_count,
                duration=duration,
            ))

        return batch_result

    def get_available_services(self) -> list[str]:
        """Get list of available geocoding services."""
        return list(self.geocoders.keys())

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        if not self.cache:
            return {"enabled": False}

        return {
            "enabled": True,
            "size": len(self.cache.cache),
            "hits": self.cache.hits,
            "misses": self.cache.misses,
            "hit_rate": self.cache.hit_rate,
        }
