"""
Mapbox Geocoder

Paid geocoding service with high quality results and good international coverage.
Requires API key (access token).
"""

import aiohttp
import time
from typing import Optional
from urllib.parse import urlencode, quote

from kie.geo.models import (
    GeocodingRequest,
    GeocodingResult,
    GeocodingStatus,
    GeocodingService,
    ReverseGeocodingResult,
)
from kie.geo.utils import RateLimiter
from kie.exceptions import GeocodingError, APIKeyError


class MapboxGeocoder:
    """
    Geocoder using Mapbox Geocoding API.

    Paid service requiring access token.
    Good international coverage, modern API.
    Rate limits depend on pricing tier.
    """

    BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"

    def __init__(
        self,
        access_token: str,
        rate_limit: float = 100.0,  # requests per second (adjust based on plan)
        timeout: int = 10,
    ):
        """
        Initialize Mapbox geocoder.

        Args:
            access_token: Mapbox access token
            rate_limit: Requests per second (depends on pricing tier)
            timeout: Request timeout in seconds
        """
        if not access_token:
            raise APIKeyError(
                "Mapbox access token is required",
                details={"service": "mapbox"},
            )

        self.access_token = access_token
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.timeout = timeout
        self.requests_made = 0

    async def geocode(
        self,
        request: GeocodingRequest,
    ) -> GeocodingResult:
        """
        Geocode an address using Mapbox.

        Args:
            request: GeocodingRequest with address details

        Returns:
            GeocodingResult with coordinates and metadata
        """
        start_time = time.time()

        try:
            # Respect rate limit
            await self.rate_limiter.wait()

            # Build query
            address = self._build_address_string(request)
            encoded_address = quote(address)

            params = {
                "access_token": self.access_token,
                "limit": 1,  # Return top result only
            }

            url = f"{self.BASE_URL}/{encoded_address}.json?{urlencode(params)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    self.requests_made += 1

                    if response.status == 401:
                        raise APIKeyError(
                            "Mapbox access token invalid",
                            details={"service": "mapbox"},
                        )
                    elif response.status == 429:
                        return GeocodingResult.from_error(
                            address=request.address,
                            error="Mapbox rate limit exceeded",
                            service=GeocodingService.MAPBOX.value,
                            status=GeocodingStatus.RATE_LIMITED,
                        )
                    elif response.status != 200:
                        raise GeocodingError(
                            f"Mapbox API error: {response.status}",
                            details={"status_code": response.status},
                        )

                    data = await response.json()

            # Check for results
            features = data.get("features", [])
            if not features:
                return GeocodingResult(
                    original_address=request.address,
                    service=GeocodingService.MAPBOX.value,
                    status=GeocodingStatus.FAILED,
                    error_message="No results found",
                    response_time_ms=(time.time() - start_time) * 1000,
                )

            # Parse first result (best match)
            result = self._parse_response(features[0], request.address)
            result.response_time_ms = (time.time() - start_time) * 1000

            return result

        except APIKeyError:
            raise
        except Exception as e:
            return GeocodingResult.from_error(
                address=request.address,
                error=str(e),
                service=GeocodingService.MAPBOX.value,
                status=GeocodingStatus.API_ERROR,
            )

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> ReverseGeocodingResult:
        """
        Reverse geocode coordinates using Mapbox.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            ReverseGeocodingResult with address details
        """
        try:
            await self.rate_limiter.wait()

            coords = f"{longitude},{latitude}"  # Mapbox uses lon,lat order
            params = {
                "access_token": self.access_token,
                "limit": 1,
            }

            url = f"{self.BASE_URL}/{coords}.json?{urlencode(params)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    self.requests_made += 1

                    if response.status != 200:
                        raise GeocodingError(
                            f"Mapbox API error: {response.status}",
                            details={"status_code": response.status},
                        )

                    data = await response.json()

            features = data.get("features", [])
            if not features:
                return ReverseGeocodingResult(
                    latitude=latitude,
                    longitude=longitude,
                    service=GeocodingService.MAPBOX.value,
                    status=GeocodingStatus.FAILED,
                    error_message="No results found",
                )

            return self._parse_reverse_response(features[0], latitude, longitude)

        except Exception as e:
            return ReverseGeocodingResult(
                latitude=latitude,
                longitude=longitude,
                service=GeocodingService.MAPBOX.value,
                status=GeocodingStatus.API_ERROR,
                error_message=str(e),
            )

    def _build_address_string(self, request: GeocodingRequest) -> str:
        """Build address string from request."""
        parts = [request.address]
        if request.city:
            parts.append(request.city)
        if request.state:
            parts.append(request.state)
        if request.zip_code:
            parts.append(request.zip_code)
        if request.country and request.country != "US":
            parts.append(request.country)

        return ", ".join(parts)

    def _parse_response(
        self, feature: dict, original_address: str
    ) -> GeocodingResult:
        """Parse Mapbox response."""
        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", [])
        properties = feature.get("properties", {})
        context = feature.get("context", [])

        # Extract coordinates (Mapbox uses [lon, lat] order)
        longitude = coordinates[0] if len(coordinates) > 0 else None
        latitude = coordinates[1] if len(coordinates) > 1 else None

        # Extract address components from context
        components = {}
        for item in context:
            item_id = item.get("id", "")
            text = item.get("text")

            if item_id.startswith("place"):
                components["city"] = text
            elif item_id.startswith("region"):
                components["state"] = text
                components["state_code"] = item.get("short_code", "").replace("US-", "")
            elif item_id.startswith("postcode"):
                components["zip_code"] = text
            elif item_id.startswith("country"):
                components["country"] = text
                components["country_code"] = item.get("short_code")

        # Street from place_name or address
        place_name = feature.get("place_name", "")
        components["street"] = feature.get("address")

        # Determine confidence from relevance score
        relevance = properties.get("relevance", 0.5)
        if relevance >= 0.9:
            confidence = 0.95
            match_type = "exact"
        elif relevance >= 0.75:
            confidence = 0.85
            match_type = "approximate"
        else:
            confidence = 0.70
            match_type = "interpolated"

        return GeocodingResult(
            original_address=original_address,
            latitude=latitude,
            longitude=longitude,
            formatted_address=place_name,
            street=components.get("street"),
            city=components.get("city"),
            state=components.get("state"),
            state_code=components.get("state_code"),
            zip_code=components.get("zip_code"),
            country=components.get("country"),
            country_code=components.get("country_code"),
            confidence=confidence,
            match_type=match_type,
            service=GeocodingService.MAPBOX.value,
            status=GeocodingStatus.SUCCESS if latitude else GeocodingStatus.FAILED,
        )

    def _parse_reverse_response(
        self, feature: dict, latitude: float, longitude: float
    ) -> ReverseGeocodingResult:
        """Parse reverse geocoding response."""
        context = feature.get("context", [])

        components = {}
        for item in context:
            item_id = item.get("id", "")
            text = item.get("text")

            if item_id.startswith("place"):
                components["city"] = text
            elif item_id.startswith("region"):
                components["state"] = text
                components["state_code"] = item.get("short_code", "").replace("US-", "")
            elif item_id.startswith("postcode"):
                components["zip_code"] = text
            elif item_id.startswith("country"):
                components["country"] = text

        return ReverseGeocodingResult(
            latitude=latitude,
            longitude=longitude,
            formatted_address=feature.get("place_name"),
            street=feature.get("address"),
            city=components.get("city"),
            state=components.get("state"),
            state_code=components.get("state_code"),
            zip_code=components.get("zip_code"),
            country=components.get("country"),
            confidence=0.9,
            service=GeocodingService.MAPBOX.value,
            status=GeocodingStatus.SUCCESS,
        )
