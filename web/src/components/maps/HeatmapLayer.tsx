/**
 * Heatmap Layer Component
 *
 * Density visualization with KDS purple gradient.
 */

import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';

interface HeatmapData {
  latitude: number;
  longitude: number;
  weight?: number;
}

interface HeatmapLayerProps {
  data: HeatmapData[];
  radius?: number;
  blur?: number;
  maxZoom?: number;
  minOpacity?: number;
  gradient?: Record<number, string>; // KDS purple gradient by default
}

/**
 * KDS purple heatmap gradient
 */
const KDS_HEATMAP_GRADIENT = {
  0.0: '#1E1E1E',
  0.2: '#E0D2FA',
  0.4: '#C8A5F0',
  0.6: '#AF7DEB',
  0.8: '#9150E1',
  1.0: '#7823DC',
};

/**
 * Heatmap layer component
 */
export function HeatmapLayer({
  data,
  radius = 25,
  blur = 15,
  maxZoom = 13,
  minOpacity = 0.4,
  gradient = KDS_HEATMAP_GRADIENT,
}: HeatmapLayerProps) {
  const map = useMap();

  useEffect(() => {
    // Filter out invalid coordinates
    const validData = data.filter(
      (d) =>
        d.latitude !== null &&
        d.latitude !== undefined &&
        d.longitude !== null &&
        d.longitude !== undefined &&
        !isNaN(d.latitude) &&
        !isNaN(d.longitude)
    );

    // Convert to heatmap format: [lat, lng, intensity]
    const heatData: [number, number, number][] = validData.map((d) => {
      const weight = d.weight !== undefined ? d.weight : 1;
      return [d.latitude, d.longitude, weight];
    });

    if (heatData.length === 0) {
      return;
    }

    // Create heatmap layer
    // @ts-ignore - leaflet.heat types not available
    const heatLayer = L.heatLayer(heatData, {
      radius,
      blur,
      maxZoom,
      minOpacity,
      gradient,
    });

    // Add to map
    heatLayer.addTo(map);

    // Cleanup
    return () => {
      map.removeLayer(heatLayer);
    };
  }, [map, data, radius, blur, maxZoom, minOpacity, gradient]);

  return null;
}

export default HeatmapLayer;
