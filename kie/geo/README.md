# KIE v3 Geographic Data System

Complete geocoding, mapping, and spatial analysis for KIE projects.

## Features

### 🌍 Geocoding
- **4 Geocoding Services**: Nominatim (free), US Census (free), Google Maps (paid), Mapbox (paid)
- **Intelligent Fallback**: Automatically tries free services first, then paid if needed
- **Batch Processing**: Geocode thousands of addresses efficiently
- **FIPS Code Enrichment**: Automatic US state/county FIPS codes
- **Confidence Scoring**: 0.0-1.0 quality scores for each result

### 🗺️ Interactive Maps
- **Folium Backend**: Python-generated HTML maps
- **React-Leaflet Frontend**: Interactive React components
- **KDS Styling**: 100% Kearney Design System compliant
- **3 Layer Types**: Choropleth, markers, heatmaps
- **Clustering**: Automatic marker clustering for large datasets

### 📦 Export Formats
- CSV with WKT geometry
- GeoJSON (web/GIS standard)
- Shapefile (ArcGIS/QGIS)
- KML (Google Earth)

### 📊 Spatial Analysis
- Distance matrix calculation
- Nearest neighbor search
- Spatial joins (points to polygons)
- Regional aggregation

---

## Quick Start

### 1. Geocode Addresses

```python
import asyncio
from core_v3.geo import GeocodingRequest, GeocodingPipeline

async def geocode_example():
    # Create pipeline (uses free services by default)
    pipeline = GeocodingPipeline()

    # Create request
    request = GeocodingRequest(
        address="227 W Monroe St",
        city="Chicago",
        state="IL",
        zip_code="60606"
    )

    # Geocode
    result = await pipeline.geocode(request)

    print(f"Latitude: {result.latitude}")
    print(f"Longitude: {result.longitude}")
    print(f"Confidence: {result.confidence}")

asyncio.run(geocode_example())
```

### 2. Create Interactive Map

```python
from core_v3.geo.maps import create_marker_map
import pandas as pd

# Your data
data = pd.DataFrame({
    'latitude': [41.8781, 40.7128],
    'longitude': [-87.6298, -74.0060],
    'name': ['Chicago', 'New York'],
    'value': [250, 300]
})

# Create map
map_builder = create_marker_map(
    data=data,
    popup_cols=['name', 'value'],
    cluster=True
)

# Save
map_builder.save('outputs/my_map.html')
```

### 3. Export to GeoJSON

```python
from core_v3.geo import GeoExporter

exporter = GeoExporter()

# Export to GeoJSON
exporter.to_geojson(
    data=df,
    output_path='exports/data.geojson',
    latitude_col='latitude',
    longitude_col='longitude'
)
```

---

## Architecture

```
geo/
├── models.py              # Data models (GeocodingRequest, GeocodingResult)
├── pipeline.py            # Intelligent geocoding pipeline
├── fips.py                # FIPS code enrichment
├── utils.py               # Rate limiting, caching, validation
├── export.py              # Multi-format export utilities
│
├── services/              # Geocoding service implementations
│   ├── nominatim.py       # OpenStreetMap (free)
│   ├── census.py          # US Census (free, US-only)
│   ├── google.py          # Google Maps (paid)
│   └── mapbox.py          # Mapbox (paid)
│
└── maps/                  # Map builders
    └── folium_builder.py  # Folium with KDS styling
```

---

## Geocoding Services

### Nominatim (Free)
- **Provider**: OpenStreetMap
- **Coverage**: Worldwide
- **Rate Limit**: 1 request/second
- **Setup**: No API key needed
- **Best For**: International addresses, low volume

```python
from core_v3.geo.services import NominatimGeocoder

geocoder = NominatimGeocoder(user_agent="KIE/3.0.0")
result = await geocoder.geocode(request)
```

### US Census (Free)
- **Provider**: US Census Bureau
- **Coverage**: US only
- **Rate Limit**: ~2 requests/second (be respectful)
- **Setup**: No API key needed
- **Best For**: US addresses, FIPS codes, high accuracy
- **Special**: Supports batch geocoding (up to 10,000 addresses)

```python
from core_v3.geo.services import CensusGeocoder

geocoder = CensusGeocoder()
result = await geocoder.geocode(request)
```

### Google Maps (Paid)
- **Provider**: Google Cloud
- **Coverage**: Worldwide (best quality)
- **Rate Limit**: 50+ requests/second (depends on plan)
- **Setup**: Requires `GOOGLE_MAPS_API_KEY` environment variable
- **Best For**: Highest accuracy, rooftop-level precision

```python
import os
from core_v3.geo.services import GoogleMapsGeocoder

api_key = os.getenv("GOOGLE_MAPS_API_KEY")
geocoder = GoogleMapsGeocoder(api_key=api_key)
result = await geocoder.geocode(request)
```

### Mapbox (Paid)
- **Provider**: Mapbox
- **Coverage**: Worldwide (modern API)
- **Rate Limit**: 100+ requests/second (depends on plan)
- **Setup**: Requires `MAPBOX_ACCESS_TOKEN` environment variable
- **Best For**: International, modern JSON API

```python
import os
from core_v3.geo.services import MapboxGeocoder

token = os.getenv("MAPBOX_ACCESS_TOKEN")
geocoder = MapboxGeocoder(access_token=token)
result = await geocoder.geocode(request)
```

---

## Intelligent Pipeline

The `GeocodingPipeline` automatically:
1. Tries free services first (Nominatim, Census)
2. Checks confidence threshold (default 0.75)
3. Falls back to paid services if needed
4. Caches results to minimize API calls
5. Respects rate limits for each service

```python
from core_v3.geo import GeocodingPipeline

# Configure pipeline
pipeline = GeocodingPipeline(
    preferred_service="nominatim",      # Try free first
    fallback_services=["census", "google"],  # Then fallback
    confidence_threshold=0.75,          # Minimum quality
    cache_enabled=True,                 # Cache results
)

# Geocode single address
result = await pipeline.geocode(request)

# Batch geocode (parallelized)
batch_result = await pipeline.geocode_batch(requests)
```

---

## Map Types

### 1. Choropleth (Color-Coded Regions)

```python
from core_v3.geo.maps import create_us_choropleth
import pandas as pd

# State-level data
state_data = pd.DataFrame({
    'state': ['CA', 'TX', 'NY'],
    'value': [39538223, 29145505, 20201249]
})

# Create choropleth
map_builder = create_us_choropleth(
    data=state_data,
    value_column='value',
    key_column='state',
    title='Population by State'
)

map_builder.save('outputs/choropleth.html')
```

### 2. Marker Map (Points)

```python
from core_v3.geo.maps import create_marker_map

# Point data
markers = pd.DataFrame({
    'latitude': [41.8781, 40.7128, 34.0522],
    'longitude': [-87.6298, -74.0060, -118.2437],
    'name': ['Chicago', 'New York', 'Los Angeles'],
    'employees': [250, 300, 180]
})

# Create marker map
map_builder = create_marker_map(
    data=markers,
    popup_cols=['name', 'employees'],
    cluster=True  # Cluster nearby markers
)

map_builder.save('outputs/markers.html')
```

### 3. Heatmap (Density)

```python
from core_v3.geo.maps import create_heatmap

# Point data with weights
heatmap_data = pd.DataFrame({
    'latitude': [...],
    'longitude': [...],
    'revenue': [...]  # Weight column
})

# Create heatmap
map_builder = create_heatmap(
    data=heatmap_data,
    weight_col='revenue'
)

map_builder.save('outputs/heatmap.html')
```

### 4. Multi-Layer Map (Advanced)

```python
from core_v3.geo.maps import MapBuilder, MapConfig, MarkerConfig, HeatmapConfig

# Configure base map
config = MapConfig(
    center=(39.8283, -98.5795),
    zoom=4,
    tiles="CartoDB dark_matter"
)

# Build map with multiple layers
builder = MapBuilder(config=config)
builder.create_map()

# Add marker layer
builder.add_markers(MarkerConfig(
    name="Offices",
    data=office_data,
    cluster=True,
    show=True
))

# Add heatmap layer
builder.add_heatmap(HeatmapConfig(
    name="Revenue Density",
    data=revenue_data,
    weight_col="revenue",
    show=False  # Hidden by default
))

# Add layer control (toggle layers)
builder.add_layer_control()

builder.save('outputs/multi_layer.html')
```

---

## FIPS Code Enrichment

Automatically add US state/county FIPS codes:

```python
from core_v3.geo import FIPSEnricher

enricher = FIPSEnricher()

# Add state FIPS to DataFrame
df = enricher.enrich_dataframe(
    df,
    state_col='state',       # Column with state abbreviations
    output_col='fips_state'  # Output column name
)

# Get state FIPS manually
fips = enricher.get_state_fips('CA')  # Returns '06'

# Validate FIPS codes
is_valid = enricher.validate_fips('06075')  # True (San Francisco County, CA)
```

---

## Export Formats

```python
from core_v3.geo import GeoExporter

exporter = GeoExporter()

# CSV (includes WKT geometry)
exporter.to_csv(df, 'output.csv', include_geometry=True)

# GeoJSON (web/GIS standard)
exporter.to_geojson(
    df,
    'output.geojson',
    latitude_col='latitude',
    longitude_col='longitude',
    properties=['name', 'value']
)

# Shapefile (ArcGIS/QGIS)
exporter.to_shapefile(df, 'output.shp')

# KML (Google Earth)
exporter.to_kml(
    df,
    'output.kml',
    name_col='name',
    description_cols=['value', 'category']
)
```

---

## Spatial Analysis

### Distance Matrix

```python
# Calculate pairwise distances
distance_matrix = exporter.calculate_distance_matrix(
    df,
    latitude_col='latitude',
    longitude_col='longitude',
    unit='miles'  # or 'km', 'meters'
)
```

### Nearest Neighbors

```python
# Find 5 nearest points for each source point
nearest = exporter.find_nearest_points(
    source_points=df_stores,
    target_points=df_warehouses,
    k=5
)
```

### Spatial Join

```python
# Join points to polygons (e.g., assign stores to sales regions)
joined = exporter.create_spatial_join(
    points=df_stores,
    polygons=gdf_regions,
    how='inner'
)
```

### Regional Aggregation

```python
# Aggregate point values by region
aggregated = exporter.aggregate_by_region(
    points=df_sales,
    polygons=gdf_states,
    value_col='revenue',
    agg_func='sum',
    region_id_col='state_name'
)
```

---

## React Components

For web dashboards, use React-Leaflet components with KDS styling:

```tsx
import { KDSMap, MarkerLayer, ChoroplethLayer } from '@/components/maps';

function MyMap() {
  return (
    <KDSMap center={[39.8283, -98.5795]} zoom={4} height="600px">
      <MarkerLayer
        data={markerData}
        cluster={true}
        popupFields={['name', 'value']}
      />

      <ChoroplethLayer
        geoData={statesGeoJSON}
        data={stateData}
        legend={true}
        legendTitle="Population"
      />
    </KDSMap>
  );
}
```

---

## Environment Variables

For paid services, set environment variables:

```bash
# Google Maps
export GOOGLE_MAPS_API_KEY="your-api-key"

# Mapbox
export MAPBOX_ACCESS_TOKEN="your-access-token"
```

Or use `.env` file:

```
GOOGLE_MAPS_API_KEY=your-api-key
MAPBOX_ACCESS_TOKEN=your-access-token
```

---

## KDS Compliance

All maps use official Kearney Design System styling:

- **Colors**: Purple gradient (#7823DC primary)
- **Background**: Dark mode (#1E1E1E)
- **Typography**: Inter font family
- **Borders**: KDS purple (#7823DC)
- **Accessibility**: WCAG 2.1 AA contrast ratios

---

## Examples

See `examples/geo_complete_example.py` for a comprehensive demonstration.

Run it:
```bash
python examples/geo_complete_example.py
```

This will:
1. Geocode sample addresses
2. Enrich with FIPS codes
3. Create 3 interactive maps
4. Export to CSV, GeoJSON, and Shapefile
5. Perform spatial analysis

---

## Best Practices

### 1. Use Free Services First
Configure pipeline to try Nominatim/Census before paid services:

```python
pipeline = GeocodingPipeline(
    preferred_service="nominatim",
    fallback_services=["census", "google"]
)
```

### 2. Enable Caching
Cache results to avoid re-geocoding the same addresses:

```python
pipeline = GeocodingPipeline(cache_enabled=True)
```

### 3. Batch When Possible
Batch geocoding is much faster than sequential:

```python
# Good: Batch geocode
results = await pipeline.geocode_batch(requests)

# Bad: Sequential geocoding
for req in requests:
    result = await pipeline.geocode(req)
```

### 4. Set Appropriate Confidence Thresholds
- **0.95+**: Rooftop accuracy (exact address)
- **0.85+**: High confidence (street-level)
- **0.75+**: Medium confidence (city/postal code)
- **0.60+**: Low confidence (region-level)

### 5. Respect Rate Limits
The system automatically rate limits, but be mindful:
- Nominatim: 1 req/sec max
- Census: 2 req/sec recommended
- Google/Mapbox: Depends on your plan

---

## Troubleshooting

### Geocoding Returns Low Confidence

1. Check address format (include city, state, ZIP)
2. Try different service (Census for US, Google for international)
3. Lower confidence threshold temporarily

### Rate Limit Errors

1. Reduce `rate_limit` parameter in geocoder initialization
2. Use caching to avoid duplicate requests
3. Upgrade to paid service (Google/Mapbox)

### Map Not Displaying

1. Check that DataFrame has valid lat/lon columns
2. Ensure no NaN values in coordinates
3. Verify output directory exists
4. Open HTML in modern browser (not IE)

### Import Errors

1. Install dependencies: `pip install -e ".[geo]"`
2. Check Python version (3.10+ required)
3. Ensure geopandas installed correctly

---

## Performance Tips

- **Batch geocoding**: 10-100x faster than sequential
- **Enable caching**: Avoid re-geocoding same addresses
- **Use Census for US**: Faster than Nominatim, includes FIPS
- **Cluster markers**: For 100+ points, enable clustering
- **Use heatmap**: For 1000+ points, heatmap more performant

---

## Future Enhancements

- [ ] Address normalization/standardization
- [ ] Geocoding quality validation
- [ ] Custom geocoding service integration
- [ ] 3D terrain maps (Mapbox GL)
- [ ] Animated time-series maps
- [ ] Isochrone/drive-time polygons
- [ ] Routing and directions

---

## Support

For issues or questions:
- File an issue in the KIE repository
- See `examples/geo_complete_example.py` for full example
- Check inline documentation in source files
