"""
US Census Geocoder

Free US-only geocoding service from the US Census Bureau.
High accuracy for US addresses, includes FIPS codes.
No rate limits specified, but respectful usage recommended.
"""

import time

import aiohttp

from kie.exceptions import GeocodingError
from kie.geo.models import (
    GeocodingRequest,
    GeocodingResult,
    GeocodingService,
    GeocodingStatus,
)
from kie.geo.utils import RateLimiter


class CensusGeocoder:
    """
    Geocoder using US Census Bureau Geocoding Services.

    Free service for US addresses only.
    Includes FIPS codes (state, county, tract, block).
    High accuracy, especially for residential addresses.
    """

    BASE_URL = "https://geocoding.geo.census.gov/geocoder/locations"

    def __init__(
        self,
        rate_limit: float = 2.0,  # requests per second (conservative)
        timeout: int = 10,
        benchmark: str = "Public_AR_Current",  # Current vintage
    ):
        """
        Initialize Census geocoder.

        Args:
            rate_limit: Requests per second (no official limit, be respectful)
            timeout: Request timeout in seconds
            benchmark: Census benchmark to use
        """
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.timeout = timeout
        self.benchmark = benchmark
        self.requests_made = 0

    async def geocode(
        self,
        request: GeocodingRequest,
    ) -> GeocodingResult:
        """
        Geocode a US address.

        Args:
            request: GeocodingRequest with address details

        Returns:
            GeocodingResult with coordinates and FIPS codes
        """
        start_time = time.time()

        try:
            # Respect rate limit
            await self.rate_limiter.wait()

            # Build query
            params = self._build_params(request)

            url = f"{self.BASE_URL}/onelineaddress"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=self.timeout
                ) as response:
                    self.requests_made += 1

                    if response.status != 200:
                        raise GeocodingError(
                            f"Census API error: {response.status}",
                            details={"status_code": response.status},
                        )

                    data = await response.json()

            # Parse response
            result = self._parse_response(data, request.address)
            result.response_time_ms = (time.time() - start_time) * 1000

            return result

        except Exception as e:
            return GeocodingResult.from_error(
                address=request.address,
                error=str(e),
                service=GeocodingService.CENSUS.value,
                status=GeocodingStatus.API_ERROR,
            )

    async def geocode_batch(
        self,
        requests: list[GeocodingRequest],
        batch_size: int = 100,
    ) -> list[GeocodingResult]:
        """
        Geocode multiple addresses in batch.

        Census API supports batch geocoding with up to 10,000 addresses.

        Args:
            requests: List of geocoding requests
            batch_size: Number of addresses per batch (max 10,000)

        Returns:
            List of geocoding results
        """
        results = []

        # Process in batches
        for i in range(0, len(requests), batch_size):
            batch = requests[i : i + batch_size]
            batch_results = await self._geocode_batch_internal(batch)
            results.extend(batch_results)

        return results

    async def _geocode_batch_internal(
        self, requests: list[GeocodingRequest]
    ) -> list[GeocodingResult]:
        """Internal batch geocoding implementation."""
        try:
            # Respect rate limit
            await self.rate_limiter.wait()

            # Build CSV data for batch
            csv_lines = ["id,address"]
            for i, req in enumerate(requests):
                address_str = self._build_address_string(req)
                csv_lines.append(f'{i},"{address_str}"')

            csv_data = "\n".join(csv_lines)

            # Make batch request
            url = f"{self.BASE_URL}/addressbatch"
            data = {
                "addressFile": csv_data,
                "benchmark": self.benchmark,
                "format": "json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, data=data, timeout=self.timeout * 2
                ) as response:
                    self.requests_made += 1

                    if response.status != 200:
                        raise GeocodingError(
                            f"Census batch API error: {response.status}",
                            details={"status_code": response.status},
                        )

                    result_data = await response.json()

            # Parse batch results
            results = []
            addresses_by_id = {i: req.address for i, req in enumerate(requests)}

            for record in result_data.get("addressMatches", []):
                record_id = int(record.get("id", -1))
                original_address = addresses_by_id.get(record_id, "Unknown")
                result = self._parse_batch_record(record, original_address)
                results.append(result)

            return results

        except Exception as e:
            # Return errors for all addresses in batch
            return [
                GeocodingResult.from_error(
                    address=req.address,
                    error=str(e),
                    service=GeocodingService.CENSUS.value,
                    status=GeocodingStatus.API_ERROR,
                )
                for req in requests
            ]

    def _build_params(self, request: GeocodingRequest) -> dict[str, str]:
        """Build query parameters for Census API."""
        address_str = self._build_address_string(request)

        return {
            "address": address_str,
            "benchmark": self.benchmark,
            "format": "json",
        }

    def _build_address_string(self, request: GeocodingRequest) -> str:
        """Build single-line address string."""
        parts = [request.address]
        if request.city:
            parts.append(request.city)
        if request.state:
            parts.append(request.state)
        if request.zip_code:
            parts.append(request.zip_code)

        return ", ".join(parts)

    def _parse_response(
        self, data: dict, original_address: str
    ) -> GeocodingResult:
        """Parse Census API response into GeocodingResult."""
        # Check for matches
        matches = data.get("result", {}).get("addressMatches", [])

        if not matches or len(matches) == 0:
            return GeocodingResult(
                original_address=original_address,
                service=GeocodingService.CENSUS.value,
                status=GeocodingStatus.FAILED,
                error_message="No matches found",
            )

        # Take first match (best match)
        match = matches[0]

        return self._parse_match(match, original_address)

    def _parse_match(self, match: dict, original_address: str) -> GeocodingResult:
        """Parse a single match record."""
        coordinates = match.get("coordinates", {})
        matched_address = match.get("matchedAddress", "")
        address_components = match.get("addressComponents", {})
        geographies = match.get("geographies", {})

        # Extract coordinates
        latitude = coordinates.get("y")
        longitude = coordinates.get("x")

        # Extract address components
        street = address_components.get("streetName")
        city = address_components.get("city")
        state = address_components.get("state")
        zip_code = address_components.get("zip")

        # Extract FIPS codes
        census_tracts = geographies.get("Census Tracts", [])
        fips_data = census_tracts[0] if census_tracts else {}

        fips_state = fips_data.get("STATE")
        fips_county = fips_data.get("COUNTY")
        fips_code = f"{fips_state}{fips_county}" if fips_state and fips_county else None

        # Determine confidence and match type
        match_indicator = match.get("matchedAddress", "")
        if "Exact" in match_indicator:
            confidence = 0.95
            match_type = "exact"
        elif "Non-Exact" in match_indicator:
            confidence = 0.75
            match_type = "approximate"
        else:
            confidence = 0.85
            match_type = "interpolated"

        return GeocodingResult(
            original_address=original_address,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            formatted_address=matched_address,
            street=street,
            city=city,
            state=state,
            zip_code=zip_code,
            country="United States",
            country_code="US",
            fips_code=fips_code,
            fips_state=fips_state,
            fips_county=fips_county,
            confidence=confidence,
            match_type=match_type,
            service=GeocodingService.CENSUS.value,
            status=GeocodingStatus.SUCCESS if latitude else GeocodingStatus.FAILED,
        )

    def _parse_batch_record(
        self, record: dict, original_address: str
    ) -> GeocodingResult:
        """Parse batch geocoding record."""
        # Batch records have similar structure to single records
        return self._parse_match(record, original_address)
