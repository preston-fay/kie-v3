"""
Nominatim Geocoder

Free geocoding service using OpenStreetMap data.
Rate limit: 1 request/second for free tier.
"""

import aiohttp
import time
from typing import Optional
from urllib.parse import urlencode

from kie.geo.models import (
    GeocodingRequest,
    GeocodingResult,
    GeocodingStatus,
    GeocodingService,
    ReverseGeocodingResult,
)
from kie.geo.utils import RateLimiter, normalize_address
from kie.exceptions import GeocodingError, GeocodingRateLimitError


class NominatimGeocoder:
    """
    Geocoder using Nominatim (OpenStreetMap).

    Free service with 1 request/second rate limit.
    Good worldwide coverage but quality varies by region.
    """

    BASE_URL = "https://nominatim.openstreetmap.org"

    def __init__(
        self,
        user_agent: str = "KIE/3.0.0",
        rate_limit: float = 1.0,  # requests per second
        timeout: int = 10,
    ):
        """
        Initialize Nominatim geocoder.

        Args:
            user_agent: User agent string (required by Nominatim)
            rate_limit: Requests per second (max 1.0 for free tier)
            timeout: Request timeout in seconds
        """
        self.user_agent = user_agent
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.timeout = timeout
        self.requests_made = 0

    async def geocode(
        self,
        request: GeocodingRequest,
    ) -> GeocodingResult:
        """
        Geocode an address.

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
            query = self._build_query(request)

            # Make request
            headers = {"User-Agent": self.user_agent}
            params = {
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": 1,
            }

            url = f"{self.BASE_URL}/search?{urlencode(params)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=self.timeout
                ) as response:
                    self.requests_made += 1

                    if response.status == 429:
                        raise GeocodingRateLimitError(
                            "Nominatim rate limit exceeded",
                            details={"service": "nominatim"},
                        )

                    if response.status != 200:
                        raise GeocodingError(
                            f"Nominatim API error: {response.status}",
                            details={"status_code": response.status},
                        )

                    data = await response.json()

            # Parse response
            if not data or len(data) == 0:
                return GeocodingResult(
                    original_address=request.address,
                    service=GeocodingService.NOMINATIM.value,
                    status=GeocodingStatus.FAILED,
                    error_message="No results found",
                    response_time_ms=(time.time() - start_time) * 1000,
                )

            result = self._parse_response(data[0], request.address)
            result.response_time_ms = (time.time() - start_time) * 1000

            return result

        except GeocodingRateLimitError:
            raise
        except Exception as e:
            return GeocodingResult.from_error(
                address=request.address,
                error=str(e),
                service=GeocodingService.NOMINATIM.value,
                status=GeocodingStatus.API_ERROR,
            )

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> ReverseGeocodingResult:
        """
        Reverse geocode coordinates to address.

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            ReverseGeocodingResult with address details
        """
        try:
            # Respect rate limit
            await self.rate_limiter.wait()

            # Make request
            headers = {"User-Agent": self.user_agent}
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
            }

            url = f"{self.BASE_URL}/reverse?{urlencode(params)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=self.timeout
                ) as response:
                    self.requests_made += 1

                    if response.status == 429:
                        raise GeocodingRateLimitError(
                            "Nominatim rate limit exceeded",
                            details={"service": "nominatim"},
                        )

                    if response.status != 200:
                        raise GeocodingError(
                            f"Nominatim API error: {response.status}",
                            details={"status_code": response.status},
                        )

                    data = await response.json()

            # Parse response
            if "error" in data:
                return ReverseGeocodingResult(
                    latitude=latitude,
                    longitude=longitude,
                    service=GeocodingService.NOMINATIM.value,
                    status=GeocodingStatus.FAILED,
                    error_message=data.get("error", "Unknown error"),
                )

            return self._parse_reverse_response(data, latitude, longitude)

        except Exception as e:
            return ReverseGeocodingResult(
                latitude=latitude,
                longitude=longitude,
                service=GeocodingService.NOMINATIM.value,
                status=GeocodingStatus.API_ERROR,
                error_message=str(e),
            )

    def _build_query(self, request: GeocodingRequest) -> str:
        """Build search query from request."""
        # Normalize address
        address = normalize_address(request.address)

        # Build full query
        parts = [address]
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
        self, data: dict, original_address: str
    ) -> GeocodingResult:
        """Parse Nominatim response into GeocodingResult."""
        address = data.get("address", {})

        # Extract address components
        street = address.get("road") or address.get("street")
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("hamlet")
        )
        county = address.get("county")
        state = address.get("state")
        zip_code = address.get("postcode")
        country = address.get("country")
        country_code = address.get("country_code", "").upper()

        # Confidence based on importance score (0-1)
        importance = float(data.get("importance", 0.5))
        confidence = min(importance, 1.0)

        # Determine match type
        place_rank = int(data.get("place_rank", 30))
        if place_rank <= 16:
            match_type = "exact"
        elif place_rank <= 25:
            match_type = "approximate"
        else:
            match_type = "interpolated"

        return GeocodingResult(
            original_address=original_address,
            latitude=float(data["lat"]),
            longitude=float(data["lon"]),
            formatted_address=data.get("display_name"),
            street=street,
            city=city,
            county=county,
            state=state,
            zip_code=zip_code,
            country=country,
            country_code=country_code,
            confidence=confidence,
            match_type=match_type,
            service=GeocodingService.NOMINATIM.value,
            status=GeocodingStatus.SUCCESS,
        )

    def _parse_reverse_response(
        self, data: dict, latitude: float, longitude: float
    ) -> ReverseGeocodingResult:
        """Parse reverse geocoding response."""
        address = data.get("address", {})

        street = address.get("road") or address.get("street")
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
        )
        county = address.get("county")
        state = address.get("state")
        zip_code = address.get("postcode")
        country = address.get("country")

        return ReverseGeocodingResult(
            latitude=latitude,
            longitude=longitude,
            formatted_address=data.get("display_name"),
            street=street,
            city=city,
            county=county,
            state=state,
            zip_code=zip_code,
            country=country,
            confidence=0.8,  # Reverse geocoding typically high confidence
            service=GeocodingService.NOMINATIM.value,
            status=GeocodingStatus.SUCCESS,
        )
