/**
 * KDS-Styled Interactive Map Component
 *
 * React-Leaflet map with Kearney Design System styling.
 */

import React, { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// KDS colors
const KDS_COLORS = {
  primary: '#7823DC',
  accent: '#9B4DCA',
  background: '#1E1E1E',
  text: '#FFFFFF',
  border: '#7823DC',
};

interface KDSMapProps {
  center?: [number, number];
  zoom?: number;
  width?: string;
  height?: string;
  children?: React.ReactNode;
  onMapReady?: (map: L.Map) => void;
}

/**
 * Custom map styling component
 */
function MapStyler() {
  const map = useMap();

  useEffect(() => {
    // Apply KDS styling to map controls
    const style = document.createElement('style');
    style.textContent = `
      .leaflet-container {
        background-color: ${KDS_COLORS.background};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
      }

      .leaflet-popup-content-wrapper {
        background-color: ${KDS_COLORS.background};
        color: ${KDS_COLORS.text};
        border: 2px solid ${KDS_COLORS.border};
        border-radius: 8px;
        font-family: 'Inter', Arial, sans-serif;
      }

      .leaflet-popup-tip {
        background-color: ${KDS_COLORS.background};
        border: 2px solid ${KDS_COLORS.border};
      }

      .leaflet-control-layers {
        background-color: ${KDS_COLORS.background};
        color: ${KDS_COLORS.text};
        border: 2px solid ${KDS_COLORS.border};
        border-radius: 8px;
      }

      .leaflet-control-layers-toggle {
        background-color: ${KDS_COLORS.background};
        border: 2px solid ${KDS_COLORS.border};
      }

      .leaflet-bar a {
        background-color: ${KDS_COLORS.background};
        border-bottom: 1px solid ${KDS_COLORS.border};
        color: ${KDS_COLORS.text};
      }

      .leaflet-bar a:hover {
        background-color: #2A2A2A;
        color: ${KDS_COLORS.border};
      }

      .leaflet-control-attribution {
        background-color: rgba(30, 30, 30, 0.8);
        color: ${KDS_COLORS.text};
      }

      .leaflet-control-attribution a {
        color: ${KDS_COLORS.accent};
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, [map]);

  return null;
}

/**
 * KDS-styled map component
 */
export function KDSMap({
  center = [39.8283, -98.5795], // Center of US
  zoom = 4,
  width = '100%',
  height = '600px',
  children,
  onMapReady,
}: KDSMapProps) {
  const handleMapCreated = (map: L.Map) => {
    if (onMapReady) {
      onMapReady(map);
    }
  };

  return (
    <div style={{ width, height }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ width: '100%', height: '100%' }}
        whenCreated={handleMapCreated}
      >
        {/* Dark tile layer (KDS-friendly) */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Apply KDS styling */}
        <MapStyler />

        {/* Children layers */}
        {children}
      </MapContainer>
    </div>
  );
}

export default KDSMap;
