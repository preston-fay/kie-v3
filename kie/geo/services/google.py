"""
Google Maps Geocoder

Paid geocoding service with highest quality results worldwide.
Requires API key.
"""

import time
from urllib.parse import urlencode

import aiohttp

from kie.exceptions import APIKeyError, GeocodingError
from kie.geo.models import (
    GeocodingRequest,
    GeocodingResult,
    GeocodingService,
    GeocodingStatus,
    ReverseGeocodingResult,
)
from kie.geo.utils import RateLimiter


class GoogleMapsGeocoder:
    """
    Geocoder using Google Maps Geocoding API.

    Paid service requiring API key.
    Best quality results worldwide.
    Rate limits depend on pricing tier.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(
        self,
        api_key: str,
        rate_limit: float = 50.0,  # requests per second (adjust based on plan)
        timeout: int = 10,
    ):
        """
        Initialize Google Maps geocoder.

        Args:
            api_key: Google Maps API key
            rate_limit: Requests per second (depends on pricing tier)
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise APIKeyError(
                "Google Maps API key is required",
                details={"service": "google"},
            )

        self.api_key = api_key
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.timeout = timeout
        self.requests_made = 0

    async def geocode(
        self,
        request: GeocodingRequest,
    ) -> GeocodingResult:
        """
        Geocode an address using Google Maps.

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

            params = {
                "address": address,
                "key": self.api_key,
            }

            url = f"{self.BASE_URL}?{urlencode(params)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    self.requests_made += 1

                    if response.status != 200:
                        raise GeocodingError(
                            f"Google Maps API error: {response.status}",
                            details={"status_code": response.status},
                        )

                    data = await response.json()

            # Check status
            status = data.get("status")
            if status == "REQUEST_DENIED":
                raise APIKeyError(
                    "Google Maps API key invalid or denied",
                    details={"error_message": data.get("error_message")},
                )
            elif status == "OVER_QUERY_LIMIT":
                return GeocodingResult.from_error(
                    address=request.address,
                    error="Google Maps quota exceeded",
                    service=GeocodingService.GOOGLE.value,
                    status=GeocodingStatus.RATE_LIMITED,
                )
            elif status != "OK" or not data.get("results"):
                return GeocodingResult(
                    original_address=request.address,
                    service=GeocodingService.GOOGLE.value,
                    status=GeocodingStatus.FAILED,
                    error_message=f"No results: {status}",
                    response_time_ms=(time.time() - start_time) * 1000,
                )

            # Parse first result (best match)
            result = self._parse_response(data["results"][0], request.address)
            result.response_time_ms = (time.time() - start_time) * 1000

            return result

        except APIKeyError:
            raise
        except Exception as e:
            return GeocodingResult.from_error(
                address=request.address,
                error=str(e),
                service=GeocodingService.GOOGLE.value,
                status=GeocodingStatus.API_ERROR,
            )

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> ReverseGeocodingResult:
        """
        Reverse geocode coordinates using Google Maps.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            ReverseGeocodingResult with address details
        """
        try:
            await self.rate_limiter.wait()

            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key,
            }

            url = f"{self.BASE_URL}?{urlencode(params)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    self.requests_made += 1

                    if response.status != 200:
                        raise GeocodingError(
                            f"Google Maps API error: {response.status}",
                            details={"status_code": response.status},
                        )

                    data = await response.json()

            if data.get("status") != "OK" or not data.get("results"):
                return ReverseGeocodingResult(
                    latitude=latitude,
                    longitude=longitude,
                    service=GeocodingService.GOOGLE.value,
                    status=GeocodingStatus.FAILED,
                    error_message=f"No results: {data.get('status')}",
                )

            return self._parse_reverse_response(data["results"][0], latitude, longitude)

        except Exception as e:
            return ReverseGeocodingResult(
                latitude=latitude,
                longitude=longitude,
                service=GeocodingService.GOOGLE.value,
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
        self, result: dict, original_address: str
    ) -> GeocodingResult:
        """Parse Google Maps response."""
        location = result.get("geometry", {}).get("location", {})
        address_components = result.get("address_components", [])

        # Extract address parts
        components = {}
        for component in address_components:
            types = component.get("types", [])
            name = component.get("long_name")

            if "street_number" in types:
                components["street_number"] = name
            elif "route" in types:
                components["street"] = name
            elif "locality" in types:
                components["city"] = name
            elif "administrative_area_level_2" in types:
                components["county"] = name
            elif "administrative_area_level_1" in types:
                components["state"] = name
                components["state_code"] = component.get("short_name")
            elif "postal_code" in types:
                components["zip_code"] = name
            elif "country" in types:
                components["country"] = name
                components["country_code"] = component.get("short_name")

        # Build street address
        street = components.get("street")
        if components.get("street_number"):
            street = f"{components['street_number']} {street}" if street else components["street_number"]

        # Determine confidence from location_type
        location_type = result.get("geometry", {}).get("location_type")
        if location_type == "ROOFTOP":
            confidence = 0.95
            match_type = "exact"
        elif location_type == "RANGE_INTERPOLATED":
            confidence = 0.85
            match_type = "interpolated"
        elif location_type == "GEOMETRIC_CENTER":
            confidence = 0.75
            match_type = "approximate"
        else:
            confidence = 0.70
            match_type = "approximate"

        return GeocodingResult(
            original_address=original_address,
            latitude=location.get("lat"),
            longitude=location.get("lng"),
            formatted_address=result.get("formatted_address"),
            street=street,
            city=components.get("city"),
            county=components.get("county"),
            state=components.get("state"),
            state_code=components.get("state_code"),
            zip_code=components.get("zip_code"),
            country=components.get("country"),
            country_code=components.get("country_code"),
            confidence=confidence,
            match_type=match_type,
            service=GeocodingService.GOOGLE.value,
            status=GeocodingStatus.SUCCESS,
        )

    def _parse_reverse_response(
        self, result: dict, latitude: float, longitude: float
    ) -> ReverseGeocodingResult:
        """Parse reverse geocoding response."""
        address_components = result.get("address_components", [])

        components = {}
        for component in address_components:
            types = component.get("types", [])
            name = component.get("long_name")

            if "route" in types:
                components["street"] = name
            elif "locality" in types:
                components["city"] = name
            elif "administrative_area_level_2" in types:
                components["county"] = name
            elif "administrative_area_level_1" in types:
                components["state"] = name
                components["state_code"] = component.get("short_name")
            elif "postal_code" in types:
                components["zip_code"] = name
            elif "country" in types:
                components["country"] = name

        return ReverseGeocodingResult(
            latitude=latitude,
            longitude=longitude,
            formatted_address=result.get("formatted_address"),
            street=components.get("street"),
            city=components.get("city"),
            county=components.get("county"),
            state=components.get("state"),
            state_code=components.get("state_code"),
            zip_code=components.get("zip_code"),
            country=components.get("country"),
            confidence=0.9,
            service=GeocodingService.GOOGLE.value,
            status=GeocodingStatus.SUCCESS,
        )
