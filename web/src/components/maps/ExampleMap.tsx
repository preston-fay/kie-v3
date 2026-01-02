/**
 * Example Map Component
 *
 * Demonstrates all KDS map features.
 */

import React, { useState } from 'react';
import { KDSMap, ChoroplethLayer, MarkerLayer, HeatmapLayer } from './index';

// Example US states GeoJSON (simplified)
const US_STATES_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    // This would contain actual US state geometries
    // For production, load from: https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json
  ],
};

// Example state-level data
const STATE_DATA = {
  'CA': 39538223,
  'TX': 29145505,
  'FL': 21538187,
  'NY': 20201249,
  // ... more states
};

// Example marker data
const MARKER_DATA = [
  {
    id: 1,
    latitude: 40.7128,
    longitude: -74.0060,
    name: 'New York Office',
    employees: 250,
  },
  {
    id: 2,
    latitude: 34.0522,
    longitude: -118.2437,
    name: 'Los Angeles Office',
    employees: 180,
  },
  {
    id: 3,
    latitude: 41.8781,
    longitude: -87.6298,
    name: 'Chicago Office',
    employees: 200,
  },
];

// Example heatmap data
const HEATMAP_DATA = [
  { latitude: 40.7128, longitude: -74.0060, weight: 0.9 },
  { latitude: 34.0522, longitude: -118.2437, weight: 0.7 },
  { latitude: 41.8781, longitude: -87.6298, weight: 0.8 },
  // ... more points
];

export function ExampleMap() {
  const [activeLayer, setActiveLayer] = useState<'choropleth' | 'markers' | 'heatmap'>('markers');

  return (
    <div className="p-4">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-white mb-2">KDS Map Examples</h1>
        <p className="text-gray-300">Interactive maps with Kearney Design System styling</p>
      </div>

      {/* Layer selector */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setActiveLayer('choropleth')}
          className={`px-4 py-2 rounded ${
            activeLayer === 'choropleth'
              ? 'bg-kds-purple text-white'
              : 'bg-gray-700 text-gray-300'
          }`}
        >
          Choropleth
        </button>
        <button
          onClick={() => setActiveLayer('markers')}
          className={`px-4 py-2 rounded ${
            activeLayer === 'markers'
              ? 'bg-kds-purple text-white'
              : 'bg-gray-700 text-gray-300'
          }`}
        >
          Markers
        </button>
        <button
          onClick={() => setActiveLayer('heatmap')}
          className={`px-4 py-2 rounded ${
            activeLayer === 'heatmap'
              ? 'bg-kds-purple text-white'
              : 'bg-gray-700 text-gray-300'
          }`}
        >
          Heatmap
        </button>
      </div>

      {/* Map */}
      <div className="border-2 border-kds-purple rounded-lg overflow-hidden">
        <KDSMap
          center={[39.8283, -98.5795]}
          zoom={4}
          height="600px"
        >
          {activeLayer === 'choropleth' && (
            <ChoroplethLayer
              geoData={US_STATES_GEOJSON}
              data={STATE_DATA}
              keyProperty="id"
              legend={true}
              legendTitle="Population"
              onFeatureClick={(feature, value) => {
                console.log('Clicked:', feature.properties.name, value);
              }}
            />
          )}

          {activeLayer === 'markers' && (
            <MarkerLayer
              data={MARKER_DATA}
              cluster={true}
              popupFields={['name', 'employees']}
              tooltipField="name"
              onMarkerClick={(marker) => {
                console.log('Clicked marker:', marker);
              }}
            />
          )}

          {activeLayer === 'heatmap' && (
            <HeatmapLayer
              data={HEATMAP_DATA}
              radius={50}
              blur={35}
            />
          )}
        </KDSMap>
      </div>

      {/* Legend/Info */}
      <div className="mt-4 p-4 bg-gray-800 border-2 border-kds-purple rounded-lg">
        <h2 className="text-lg font-bold text-white mb-2">Map Features</h2>
        <ul className="text-gray-300 space-y-1">
          <li>• KDS-compliant purple color scheme</li>
          <li>• Dark mode styling throughout</li>
          <li>• Interactive popups and tooltips</li>
          <li>• Responsive and accessible</li>
          <li>• Marker clustering for large datasets</li>
        </ul>
      </div>
    </div>
  );
}

export default ExampleMap;
