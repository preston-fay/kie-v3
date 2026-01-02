"""
Geographic Data Export Utilities

Export geocoded data to various formats (CSV, GeoJSON, Shapefile).
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json

from kie.geo.models import GeocodingResult, BatchGeocodingResult


class GeoExporter:
    """
    Export geographic data to multiple formats.

    Supports CSV, GeoJSON, Shapefile, and KML.
    """

    def __init__(self):
        """Initialize geo exporter."""
        pass

    def to_csv(
        self,
        data: pd.DataFrame,
        output_path: str,
        include_geometry: bool = False,
    ) -> Path:
        """
        Export to CSV.

        Args:
            data: DataFrame with geographic data
            output_path: Output file path
            include_geometry: Include WKT geometry column

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to regular DataFrame if GeoDataFrame
        if isinstance(data, gpd.GeoDataFrame):
            if include_geometry and "geometry" in data.columns:
                data = data.copy()
                data["geometry_wkt"] = data["geometry"].to_wkt()
            data = pd.DataFrame(data.drop(columns=["geometry"], errors="ignore"))

        data.to_csv(output_path, index=False)
        return output_path

    def to_geojson(
        self,
        data: pd.DataFrame,
        output_path: str,
        latitude_col: str = "latitude",
        longitude_col: str = "longitude",
        properties: Optional[List[str]] = None,
    ) -> Path:
        """
        Export to GeoJSON.

        Args:
            data: DataFrame with geographic data
            output_path: Output file path
            latitude_col: Latitude column name
            longitude_col: Longitude column name
            properties: Columns to include as properties (None = all)

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to GeoDataFrame if not already
        if not isinstance(data, gpd.GeoDataFrame):
            gdf = self._to_geodataframe(data, latitude_col, longitude_col)
        else:
            gdf = data

        # Filter properties
        if properties:
            cols_to_keep = [col for col in properties if col in gdf.columns]
            cols_to_keep.append("geometry")
            gdf = gdf[cols_to_keep]

        # Save as GeoJSON
        gdf.to_file(output_path, driver="GeoJSON")
        return output_path

    def to_shapefile(
        self,
        data: pd.DataFrame,
        output_path: str,
        latitude_col: str = "latitude",
        longitude_col: str = "longitude",
        crs: str = "EPSG:4326",
    ) -> Path:
        """
        Export to Shapefile.

        Args:
            data: DataFrame with geographic data
            output_path: Output file path (will create .shp, .shx, .dbf)
            latitude_col: Latitude column name
            longitude_col: Longitude column name
            crs: Coordinate reference system

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to GeoDataFrame
        if not isinstance(data, gpd.GeoDataFrame):
            gdf = self._to_geodataframe(data, latitude_col, longitude_col, crs=crs)
        else:
            gdf = data
            if gdf.crs is None:
                gdf = gdf.set_crs(crs)

        # Truncate column names to 10 characters (Shapefile limitation)
        gdf = gdf.rename(columns=lambda x: x[:10] if len(x) > 10 else x)

        # Save as Shapefile
        gdf.to_file(output_path, driver="ESRI Shapefile")
        return output_path

    def to_kml(
        self,
        data: pd.DataFrame,
        output_path: str,
        latitude_col: str = "latitude",
        longitude_col: str = "longitude",
        name_col: Optional[str] = None,
        description_cols: Optional[List[str]] = None,
    ) -> Path:
        """
        Export to KML (Google Earth format).

        Args:
            data: DataFrame with geographic data
            output_path: Output file path
            latitude_col: Latitude column name
            longitude_col: Longitude column name
            name_col: Column to use for placemark names
            description_cols: Columns to include in descriptions

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to GeoDataFrame
        if not isinstance(data, gpd.GeoDataFrame):
            gdf = self._to_geodataframe(data, latitude_col, longitude_col)
        else:
            gdf = data

        # Enable fiona driver for KML
        import fiona
        fiona.supported_drivers["KML"] = "rw"

        # Save as KML
        gdf.to_file(output_path, driver="KML")
        return output_path

    def results_to_dataframe(
        self,
        results: List[GeocodingResult],
        include_metadata: bool = True,
    ) -> pd.DataFrame:
        """
        Convert geocoding results to DataFrame.

        Args:
            results: List of GeocodingResult objects
            include_metadata: Include service, status, confidence columns

        Returns:
            DataFrame with geocoding results
        """
        data = []

        for result in results:
            row = {
                "original_address": result.original_address,
                "latitude": result.latitude,
                "longitude": result.longitude,
                "formatted_address": result.formatted_address,
                "street": result.street,
                "city": result.city,
                "county": result.county,
                "state": result.state,
                "state_code": result.state_code,
                "zip_code": result.zip_code,
                "country": result.country,
                "country_code": result.country_code,
                "fips_code": result.fips_code,
                "fips_state": result.fips_state,
                "fips_county": result.fips_county,
            }

            if include_metadata:
                row.update(
                    {
                        "confidence": result.confidence,
                        "match_type": result.match_type,
                        "service": result.service,
                        "status": result.status.value,
                        "error_message": result.error_message,
                        "response_time_ms": result.response_time_ms,
                    }
                )

            data.append(row)

        return pd.DataFrame(data)

    def batch_results_to_dataframe(
        self,
        batch_result: BatchGeocodingResult,
        include_metadata: bool = True,
    ) -> pd.DataFrame:
        """
        Convert batch geocoding results to DataFrame.

        Args:
            batch_result: BatchGeocodingResult object
            include_metadata: Include service, status, confidence columns

        Returns:
            DataFrame with all results
        """
        return self.results_to_dataframe(batch_result.results, include_metadata)

    def _to_geodataframe(
        self,
        data: pd.DataFrame,
        latitude_col: str,
        longitude_col: str,
        crs: str = "EPSG:4326",
    ) -> gpd.GeoDataFrame:
        """
        Convert DataFrame to GeoDataFrame.

        Args:
            data: DataFrame with lat/lon columns
            latitude_col: Latitude column name
            longitude_col: Longitude column name
            crs: Coordinate reference system

        Returns:
            GeoDataFrame with Point geometries
        """
        # Filter out rows with missing coordinates
        valid_data = data.dropna(subset=[latitude_col, longitude_col])

        # Create Point geometries
        geometry = [
            Point(xy) for xy in zip(valid_data[longitude_col], valid_data[latitude_col])
        ]

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(valid_data, geometry=geometry, crs=crs)

        return gdf

    def create_spatial_join(
        self,
        points: pd.DataFrame,
        polygons: gpd.GeoDataFrame,
        latitude_col: str = "latitude",
        longitude_col: str = "longitude",
        how: str = "inner",
    ) -> gpd.GeoDataFrame:
        """
        Spatial join points to polygons.

        Useful for assigning points to regions (e.g., states, counties).

        Args:
            points: DataFrame with point data
            polygons: GeoDataFrame with polygon boundaries
            latitude_col: Latitude column in points
            longitude_col: Longitude column in points
            how: Join type ('inner', 'left', 'right')

        Returns:
            GeoDataFrame with joined data
        """
        # Convert points to GeoDataFrame
        points_gdf = self._to_geodataframe(points, latitude_col, longitude_col)

        # Ensure CRS match
        if points_gdf.crs != polygons.crs:
            points_gdf = points_gdf.to_crs(polygons.crs)

        # Spatial join
        joined = gpd.sjoin(points_gdf, polygons, how=how, predicate="within")

        return joined

    def aggregate_by_region(
        self,
        points: pd.DataFrame,
        polygons: gpd.GeoDataFrame,
        value_col: str,
        agg_func: str = "sum",
        latitude_col: str = "latitude",
        longitude_col: str = "longitude",
        region_id_col: str = "id",
    ) -> pd.DataFrame:
        """
        Aggregate point values by region.

        Args:
            points: DataFrame with point data
            polygons: GeoDataFrame with polygon boundaries
            value_col: Column to aggregate
            agg_func: Aggregation function ('sum', 'mean', 'count', etc.)
            latitude_col: Latitude column in points
            longitude_col: Longitude column in points
            region_id_col: Region identifier column in polygons

        Returns:
            DataFrame with aggregated values by region
        """
        # Spatial join
        joined = self.create_spatial_join(
            points, polygons, latitude_col, longitude_col, how="inner"
        )

        # Aggregate
        agg_result = joined.groupby(region_id_col)[value_col].agg(agg_func).reset_index()

        return agg_result

    def calculate_distance_matrix(
        self,
        data: pd.DataFrame,
        latitude_col: str = "latitude",
        longitude_col: str = "longitude",
        unit: str = "miles",
    ) -> pd.DataFrame:
        """
        Calculate pairwise distance matrix between all points.

        Args:
            data: DataFrame with point data
            latitude_col: Latitude column name
            longitude_col: Longitude column name
            unit: Distance unit ('miles', 'km', 'meters')

        Returns:
            Distance matrix as DataFrame
        """
        from geopy.distance import geodesic

        # Extract coordinates
        coords = data[[latitude_col, longitude_col]].values

        # Calculate distances
        n = len(coords)
        distances = []

        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append(0.0)
                else:
                    dist = geodesic(coords[i], coords[j])

                    # Convert to desired unit
                    if unit == "miles":
                        row.append(dist.miles)
                    elif unit == "km":
                        row.append(dist.km)
                    elif unit == "meters":
                        row.append(dist.meters)
                    else:
                        row.append(dist.miles)  # Default

            distances.append(row)

        # Create DataFrame
        if "id" in data.columns:
            index = data["id"].values
        else:
            index = range(n)

        return pd.DataFrame(distances, index=index, columns=index)

    def find_nearest_points(
        self,
        source_points: pd.DataFrame,
        target_points: pd.DataFrame,
        k: int = 1,
        latitude_col: str = "latitude",
        longitude_col: str = "longitude",
    ) -> pd.DataFrame:
        """
        Find k nearest target points for each source point.

        Args:
            source_points: DataFrame with source points
            target_points: DataFrame with target points
            k: Number of nearest neighbors to find
            latitude_col: Latitude column name
            longitude_col: Longitude column name

        Returns:
            DataFrame with nearest neighbors
        """
        from sklearn.neighbors import BallTree
        import numpy as np

        # Extract coordinates
        source_coords = source_points[[latitude_col, longitude_col]].values
        target_coords = target_points[[latitude_col, longitude_col]].values

        # Convert to radians for haversine distance
        source_coords_rad = np.radians(source_coords)
        target_coords_rad = np.radians(target_coords)

        # Build tree
        tree = BallTree(target_coords_rad, metric="haversine")

        # Query nearest neighbors
        distances, indices = tree.query(source_coords_rad, k=k)

        # Convert distances to miles (Earth radius = 3959 miles)
        distances_miles = distances * 3959

        # Build results
        results = []
        for i, (dist_row, idx_row) in enumerate(zip(distances_miles, indices)):
            for j, (dist, idx) in enumerate(zip(dist_row, idx_row)):
                result = {
                    "source_index": i,
                    "target_index": idx,
                    "distance_miles": dist,
                    "rank": j + 1,
                }

                # Add source point data
                for col in source_points.columns:
                    result[f"source_{col}"] = source_points.iloc[i][col]

                # Add target point data
                for col in target_points.columns:
                    result[f"target_{col}"] = target_points.iloc[idx][col]

                results.append(result)

        return pd.DataFrame(results)


def export_geocoding_results(
    results: List[GeocodingResult],
    output_dir: str,
    formats: List[str] = ["csv", "geojson"],
    base_name: str = "geocoded_data",
) -> Dict[str, Path]:
    """
    Export geocoding results to multiple formats.

    Args:
        results: List of GeocodingResult objects
        output_dir: Output directory
        formats: List of formats ('csv', 'geojson', 'shapefile', 'kml')
        base_name: Base filename

    Returns:
        Dictionary mapping format to file path
    """
    exporter = GeoExporter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert to DataFrame
    df = exporter.results_to_dataframe(results, include_metadata=True)

    # Export to each format
    output_paths = {}

    for fmt in formats:
        if fmt == "csv":
            path = exporter.to_csv(df, output_dir / f"{base_name}.csv")
            output_paths["csv"] = path
        elif fmt == "geojson":
            path = exporter.to_geojson(df, output_dir / f"{base_name}.geojson")
            output_paths["geojson"] = path
        elif fmt == "shapefile":
            path = exporter.to_shapefile(df, output_dir / f"{base_name}.shp")
            output_paths["shapefile"] = path
        elif fmt == "kml":
            path = exporter.to_kml(df, output_dir / f"{base_name}.kml")
            output_paths["kml"] = path

    return output_paths
