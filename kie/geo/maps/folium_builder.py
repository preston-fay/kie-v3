"""
Folium Map Builder with KDS Styling

Creates interactive maps with Kearney Design System branding.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import folium
import pandas as pd
from folium import plugins

from kie.brand.colors import KDSColors
from kie.brand.theme import get_theme


@dataclass
class MapConfig:
    """Configuration for map creation."""

    center: tuple[float, float] = (39.8283, -98.5795)  # Center of US
    zoom: int = 4
    width: str = "100%"
    height: str = "600px"
    tiles: str | None = None  # Auto-selected based on theme if None
    attribution: str = "Kearney Insight Engine"

    # KDS styling (auto-populated from theme if None)
    background_color: str | None = None
    text_color: str | None = None
    border_color: str | None = None

    # Map controls
    zoom_control: bool = True
    fullscreen_control: bool = True
    measure_control: bool = False
    minimap: bool = False

    def __post_init__(self):
        """Apply theme defaults if not specified."""
        theme = get_theme()

        # Auto-select tiles based on theme
        if self.tiles is None:
            self.tiles = theme.get_folium_tiles()

        # Auto-populate colors from theme
        if self.background_color is None:
            self.background_color = theme.get_background()

        if self.text_color is None:
            self.text_color = theme.get_text()

        if self.border_color is None:
            self.border_color = theme.colors.brand_primary


@dataclass
class LayerConfig:
    """Base configuration for map layers."""

    name: str
    show: bool = True
    opacity: float = 0.8


@dataclass
class ChoroplethConfig(LayerConfig):
    """Configuration for choropleth layer."""

    geo_data: Any = None  # GeoJSON or file path
    data: pd.DataFrame | None = None
    columns: list[str] | None = None  # [key_column, value_column]
    key_on: str = "feature.properties.id"

    # Color scheme - Official KDS palette
    color_scale: list[str] = None  # Will be set to KDS palette in __post_init__
    fill_color: str = "PuRd"  # Purple-Red gradient (KDS-friendly) - kept for fallback
    fill_opacity: float = 0.7
    line_opacity: float = 0.3
    line_color: str = "#7823DC"
    line_weight: int = 1

    # Legend
    legend_name: str | None = None
    nan_fill_color: str = "#1E1E1E"
    nan_fill_opacity: float = 0.2

    # Bins
    threshold_scale: list[float] | None = None
    bins: int = 5

    def __post_init__(self):
        """Set default color_scale to official KDS palette."""
        if self.color_scale is None:
            self.color_scale = list(KDSColors.CHART_PALETTE)


@dataclass
class MarkerConfig(LayerConfig):
    """Configuration for marker layer."""

    data: pd.DataFrame | None = None
    latitude_col: str = "latitude"
    longitude_col: str = "longitude"

    # Marker appearance
    color: str = "#7823DC"
    icon: str = "info-sign"
    prefix: str = "glyphicon"

    # Popup/tooltip
    popup_cols: list[str] | None = None
    tooltip_cols: list[str] | None = None

    # Clustering
    cluster: bool = False
    cluster_color: str = "#9B4DCA"


@dataclass
class HeatmapConfig(LayerConfig):
    """Configuration for heatmap layer."""

    data: pd.DataFrame | None = None
    latitude_col: str = "latitude"
    longitude_col: str = "longitude"
    weight_col: str | None = None

    # Heatmap styling
    radius: int = 15
    blur: int = 25
    min_opacity: float = 0.4
    max_zoom: int = 13

    # Color gradient (KDS purple gradient)
    gradient: dict[float, str] = field(default_factory=lambda: {
        0.0: "#1E1E1E",
        0.2: "#E0D2FA",
        0.4: "#C8A5F0",
        0.6: "#AF7DEB",
        0.8: "#9150E1",
        1.0: "#7823DC",
    })


class MapBuilder:
    """
    Build interactive maps with KDS styling.

    Supports choropleth, markers, heatmaps, and custom layers.
    Uses Folium with custom KDS templates.
    """

    def __init__(self, config: MapConfig | None = None):
        """
        Initialize map builder.

        Args:
            config: Map configuration (uses defaults if None)
        """
        self.config = config or MapConfig()
        self.map = None
        self.layers = []

    def create_map(self) -> folium.Map:
        """
        Create base map with KDS styling.

        Returns:
            Folium Map object
        """
        self.map = folium.Map(
            location=self.config.center,
            zoom_start=self.config.zoom,
            tiles=self.config.tiles,
            attr=self.config.attribution,
            zoom_control=self.config.zoom_control,
            width=self.config.width,
            height=self.config.height,
        )

        # Add fullscreen control
        if self.config.fullscreen_control:
            plugins.Fullscreen(
                position="topright",
                title="Fullscreen",
                title_cancel="Exit fullscreen",
                force_separate_button=True,
            ).add_to(self.map)

        # Add measure control
        if self.config.measure_control:
            plugins.MeasureControl(
                position="topleft",
                primary_length_unit="miles",
                secondary_length_unit="meters",
                primary_area_unit="acres",
                secondary_area_unit="sqmeters",
            ).add_to(self.map)

        # Add minimap
        if self.config.minimap:
            minimap = plugins.MiniMap(
                tile_layer=self.config.tiles,
                position="bottomright",
            )
            self.map.add_child(minimap)

        # Apply KDS styling via custom CSS
        self._apply_kds_styling()

        return self.map

    def add_choropleth(
        self,
        config: ChoroplethConfig,
    ) -> "MapBuilder":
        """
        Add choropleth layer to map.

        Args:
            config: Choropleth configuration

        Returns:
            Self for chaining
        """
        if self.map is None:
            self.create_map()

        # Load GeoJSON if path or URL provided
        geo_data = config.geo_data
        if isinstance(geo_data, str | Path):
            geo_data_str = str(geo_data)
            if geo_data_str.startswith(('http://', 'https://')):
                # Fetch from URL
                import urllib.request
                with urllib.request.urlopen(geo_data_str) as response:
                    geo_data = json.loads(response.read().decode('utf-8'))
            else:
                # Load from local file
                with open(geo_data) as f:
                    geo_data = json.load(f)

        # Create choropleth
        choropleth = folium.Choropleth(
            geo_data=geo_data,
            name=config.name,
            data=config.data,
            columns=config.columns,
            key_on=config.key_on,
            fill_color=config.fill_color,
            fill_opacity=config.fill_opacity,
            line_opacity=config.line_opacity,
            line_color=config.line_color,
            line_weight=config.line_weight,
            legend_name=config.legend_name,
            nan_fill_color=config.nan_fill_color,
            nan_fill_opacity=config.nan_fill_opacity,
            bins=config.bins if config.threshold_scale is None else config.threshold_scale,
            show=config.show,
        )

        choropleth.add_to(self.map)
        self.layers.append(config.name)

        return self

    def add_markers(
        self,
        config: MarkerConfig,
    ) -> "MapBuilder":
        """
        Add marker layer to map.

        Args:
            config: Marker configuration

        Returns:
            Self for chaining
        """
        if self.map is None:
            self.create_map()

        if config.data is None or config.data.empty:
            return self

        # Create marker cluster if requested
        if config.cluster:
            marker_cluster = plugins.MarkerCluster(
                name=config.name,
                show=config.show,
            ).add_to(self.map)
            parent = marker_cluster
        else:
            parent = self.map

        # Add markers
        for _idx, row in config.data.iterrows():
            lat = row[config.latitude_col]
            lon = row[config.longitude_col]

            # Skip invalid coordinates
            if pd.isna(lat) or pd.isna(lon):
                continue

            # Build popup HTML
            popup_html = None
            if config.popup_cols:
                popup_html = self._build_popup_html(row, config.popup_cols)

            # Build tooltip
            tooltip = None
            if config.tooltip_cols:
                tooltip = self._build_tooltip(row, config.tooltip_cols)

            # Create marker
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300) if popup_html else None,
                tooltip=tooltip,
                icon=folium.Icon(
                    color="purple",  # Closest to KDS purple
                    icon=config.icon,
                    prefix=config.prefix,
                ),
            ).add_to(parent)

        self.layers.append(config.name)
        return self

    def add_heatmap(
        self,
        config: HeatmapConfig,
    ) -> "MapBuilder":
        """
        Add heatmap layer to map.

        Args:
            config: Heatmap configuration

        Returns:
            Self for chaining
        """
        if self.map is None:
            self.create_map()

        if config.data is None or config.data.empty:
            return self

        # Build heatmap data
        heat_data = []
        for _idx, row in config.data.iterrows():
            lat = row[config.latitude_col]
            lon = row[config.longitude_col]

            # Skip invalid coordinates
            if pd.isna(lat) or pd.isna(lon):
                continue

            # Include weight if specified
            if config.weight_col and config.weight_col in row:
                weight = row[config.weight_col]
                if not pd.isna(weight):
                    heat_data.append([lat, lon, weight])
            else:
                heat_data.append([lat, lon])

        # Create heatmap
        heatmap = plugins.HeatMap(
            heat_data,
            name=config.name,
            radius=config.radius,
            blur=config.blur,
            min_opacity=config.min_opacity,
            max_zoom=config.max_zoom,
            gradient=config.gradient,
            show=config.show,
        )

        heatmap.add_to(self.map)
        self.layers.append(config.name)

        return self

    def add_layer_control(self) -> "MapBuilder":
        """
        Add layer control to toggle layers.

        Returns:
            Self for chaining
        """
        if self.map is None:
            self.create_map()

        folium.LayerControl(
            position="topright",
            collapsed=False,
        ).add_to(self.map)

        return self

    def save(self, output_path: str) -> Path:
        """
        Save map to HTML file.

        Args:
            output_path: Output file path

        Returns:
            Path to saved file
        """
        if self.map is None:
            self.create_map()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.map.save(str(output_path))
        return output_path

    def to_html(self) -> str:
        """
        Get map HTML.

        Returns:
            HTML string
        """
        if self.map is None:
            self.create_map()

        return self.map._repr_html_()

    def _apply_kds_styling(self):
        """Apply KDS custom CSS styling to map."""
        kds_css = f"""
        <style>
        .folium-map {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: {self.config.background_color};
        }}

        .leaflet-container {{
            background-color: {self.config.background_color};
            font-family: 'Inter', Arial, sans-serif;
        }}

        .leaflet-popup-content-wrapper {{
            background-color: {self.config.background_color};
            color: {self.config.text_color};
            border: 2px solid {self.config.border_color};
            border-radius: 8px;
            font-family: 'Inter', Arial, sans-serif;
        }}

        .leaflet-popup-tip {{
            background-color: {self.config.background_color};
            border: 2px solid {self.config.border_color};
        }}

        .leaflet-control-layers {{
            background-color: {self.config.background_color};
            color: {self.config.text_color};
            border: 2px solid {self.config.border_color};
            border-radius: 8px;
        }}

        .leaflet-control-layers-toggle {{
            background-color: {self.config.background_color};
            border: 2px solid {self.config.border_color};
        }}

        .leaflet-bar a {{
            background-color: {self.config.background_color};
            border-bottom: 1px solid {self.config.border_color};
            color: {self.config.text_color};
        }}

        .leaflet-bar a:hover {{
            background-color: #2A2A2A;
            color: {self.config.border_color};
        }}

        .info.legend {{
            background-color: {self.config.background_color};
            color: {self.config.text_color};
            border: 2px solid {self.config.border_color};
            border-radius: 8px;
            padding: 10px;
            font-family: 'Inter', Arial, sans-serif;
        }}

        .info.legend i {{
            border: 1px solid {self.config.border_color};
        }}
        </style>
        """

        # Add CSS to map
        self.map.get_root().html.add_child(folium.Element(kds_css))

    def _build_popup_html(self, row: pd.Series, columns: list[str]) -> str:
        """Build HTML for marker popup."""
        html = f"""
        <div style='font-family: Inter, Arial, sans-serif; color: {self.config.text_color};'>
        """

        for col in columns:
            if col in row and not pd.isna(row[col]):
                value = row[col]
                html += f"<b>{col}:</b> {value}<br>"

        html += "</div>"
        return html

    def _build_tooltip(self, row: pd.Series, columns: list[str]) -> str:
        """Build text for marker tooltip."""
        parts = []
        for col in columns:
            if col in row and not pd.isna(row[col]):
                parts.append(f"{col}: {row[col]}")

        return " | ".join(parts)


def create_us_choropleth(
    data: pd.DataFrame,
    value_column: str,
    key_column: str = "state",
    title: str | None = None,
    **kwargs,
) -> MapBuilder:
    """
    Quick function to create US state choropleth.

    Args:
        data: DataFrame with state-level data
        value_column: Column with values to visualize
        key_column: Column with state identifiers (FIPS or abbreviations)
        title: Legend title
        **kwargs: Additional MapConfig parameters

    Returns:
        MapBuilder with choropleth layer
    """
    # Create map centered on US
    map_config = MapConfig(
        center=(39.8283, -98.5795),
        zoom=4,
        **kwargs,
    )

    builder = MapBuilder(config=map_config)
    builder.create_map()

    # Create choropleth config
    choropleth_config = ChoroplethConfig(
        name="US States",
        geo_data="https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json",
        data=data,
        columns=[key_column, value_column],
        key_on="feature.id",
        legend_name=title or value_column,
        fill_color="PuRd",  # Purple-Red gradient (KDS-friendly)
    )

    builder.add_choropleth(choropleth_config)
    builder.add_layer_control()

    return builder


def create_marker_map(
    data: pd.DataFrame,
    latitude_col: str = "latitude",
    longitude_col: str = "longitude",
    popup_cols: list[str] | None = None,
    cluster: bool = True,
    **kwargs,
) -> MapBuilder:
    """
    Quick function to create marker map.

    Args:
        data: DataFrame with location data
        latitude_col: Latitude column name
        longitude_col: Longitude column name
        popup_cols: Columns to show in popup
        cluster: Whether to cluster markers
        **kwargs: Additional MapConfig parameters

    Returns:
        MapBuilder with marker layer
    """
    # Auto-center on data
    center_lat = data[latitude_col].mean()
    center_lon = data[longitude_col].mean()

    map_config = MapConfig(
        center=(center_lat, center_lon),
        zoom=6,
        **kwargs,
    )

    builder = MapBuilder(config=map_config)
    builder.create_map()

    # Create marker config
    marker_config = MarkerConfig(
        name="Markers",
        data=data,
        latitude_col=latitude_col,
        longitude_col=longitude_col,
        popup_cols=popup_cols,
        cluster=cluster,
    )

    builder.add_markers(marker_config)
    builder.add_layer_control()

    return builder


def create_heatmap(
    data: pd.DataFrame,
    latitude_col: str = "latitude",
    longitude_col: str = "longitude",
    weight_col: str | None = None,
    **kwargs,
) -> MapBuilder:
    """
    Quick function to create heatmap.

    Args:
        data: DataFrame with location data
        latitude_col: Latitude column name
        longitude_col: Longitude column name
        weight_col: Optional weight column
        **kwargs: Additional MapConfig parameters

    Returns:
        MapBuilder with heatmap layer
    """
    # Auto-center on data
    center_lat = data[latitude_col].mean()
    center_lon = data[longitude_col].mean()

    map_config = MapConfig(
        center=(center_lat, center_lon),
        zoom=6,
        **kwargs,
    )

    builder = MapBuilder(config=map_config)
    builder.create_map()

    # Create heatmap config
    heatmap_config = HeatmapConfig(
        name="Heatmap",
        data=data,
        latitude_col=latitude_col,
        longitude_col=longitude_col,
        weight_col=weight_col,
    )

    builder.add_heatmap(heatmap_config)

    return builder
