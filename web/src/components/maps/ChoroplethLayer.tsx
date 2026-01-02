/**
 * Choropleth Layer Component
 *
 * Color-coded geographic regions with KDS styling.
 */

import React, { useEffect } from 'react';
import { GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import chroma from 'chroma-js';

interface ChoroplethLayerProps {
  geoData: any; // GeoJSON data
  data: Record<string, number>; // Map of feature IDs to values
  keyProperty?: string; // Property name for feature ID
  colorScale?: string[]; // Color scale (KDS purple gradient by default)
  bins?: number; // Number of color bins
  legend?: boolean; // Show legend
  legendTitle?: string; // Legend title
  onFeatureClick?: (feature: any, value?: number) => void;
  onFeatureHover?: (feature: any, value?: number) => void;
}

/**
 * KDS purple gradient color scale
 */
const KDS_PURPLE_SCALE = [
  '#E0D2FA', // Light purple
  '#C8A5F0', // Medium light purple
  '#AF7DEB', // Medium purple
  '#9150E1', // Bright purple
  '#7823DC', // Kearney purple
];

/**
 * Calculate color bins using quantile method
 */
function calculateBins(values: number[], bins: number): number[] {
  const sorted = [...values].sort((a, b) => a - b);
  const binSize = Math.floor(sorted.length / bins);
  const thresholds: number[] = [];

  for (let i = 1; i < bins; i++) {
    thresholds.push(sorted[i * binSize]);
  }

  return thresholds;
}

/**
 * Get color for value based on scale
 */
function getColor(
  value: number | undefined,
  thresholds: number[],
  colorScale: chroma.Scale
): string {
  if (value === undefined || value === null) {
    return '#1E1E1E'; // KDS background for null values
  }

  // Find bin
  let bin = 0;
  for (let i = 0; i < thresholds.length; i++) {
    if (value >= thresholds[i]) {
      bin = i + 1;
    }
  }

  // Normalize to 0-1
  const t = bin / thresholds.length;
  return colorScale(t).hex();
}

/**
 * Choropleth layer component
 */
export function ChoroplethLayer({
  geoData,
  data,
  keyProperty = 'id',
  colorScale = KDS_PURPLE_SCALE,
  bins = 5,
  legend = true,
  legendTitle = 'Values',
  onFeatureClick,
  onFeatureHover,
}: ChoroplethLayerProps) {
  const map = useMap();

  // Create color scale
  const scale = chroma.scale(colorScale).mode('lab');

  // Calculate thresholds
  const values = Object.values(data).filter((v) => v !== null && v !== undefined);
  const thresholds = calculateBins(values, bins);

  // Style function
  const style = (feature: any) => {
    const featureId = feature.properties[keyProperty];
    const value = data[featureId];
    const color = getColor(value, thresholds, scale);

    return {
      fillColor: color,
      fillOpacity: 0.7,
      color: '#7823DC', // KDS purple border
      weight: 1,
      opacity: 0.3,
    };
  };

  // Interaction handlers
  const onEachFeature = (feature: any, layer: L.Layer) => {
    const featureId = feature.properties[keyProperty];
    const value = data[featureId];

    // Hover effect
    layer.on({
      mouseover: (e) => {
        const target = e.target;
        target.setStyle({
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9,
        });
        target.bringToFront();

        if (onFeatureHover) {
          onFeatureHover(feature, value);
        }
      },
      mouseout: (e) => {
        const target = e.target;
        target.setStyle({
          weight: 1,
          opacity: 0.3,
          fillOpacity: 0.7,
        });
      },
      click: (e) => {
        if (onFeatureClick) {
          onFeatureClick(feature, value);
        }
      },
    });

    // Bind popup
    if (value !== undefined && value !== null) {
      const popupContent = `
        <div style="font-family: Inter, Arial, sans-serif; color: #FFFFFF;">
          <b>${feature.properties.name || featureId}</b><br>
          ${legendTitle}: <b>${value.toLocaleString()}</b>
        </div>
      `;
      layer.bindPopup(popupContent);
    }
  };

  // Add legend
  useEffect(() => {
    if (!legend) return;

    const legendControl = L.control({ position: 'bottomright' });

    legendControl.onAdd = () => {
      const div = L.DomUtil.create('div', 'info legend');
      div.style.backgroundColor = '#1E1E1E';
      div.style.color = '#FFFFFF';
      div.style.padding = '10px';
      div.style.borderRadius = '8px';
      div.style.border = '2px solid #7823DC';
      div.style.fontFamily = 'Inter, Arial, sans-serif';

      div.innerHTML = `<h4 style="margin: 0 0 10px 0;">${legendTitle}</h4>`;

      // Add color bins
      const binValues = [0, ...thresholds];
      for (let i = 0; i < binValues.length; i++) {
        const from = binValues[i];
        const to = binValues[i + 1] || Math.max(...values);
        const color = getColor((from + to) / 2, thresholds, scale);

        div.innerHTML += `
          <div style="margin-bottom: 4px;">
            <i style="background:${color}; width: 18px; height: 18px; display: inline-block; border: 1px solid #7823DC; margin-right: 8px;"></i>
            ${from.toLocaleString()} – ${to.toLocaleString()}
          </div>
        `;
      }

      return div;
    };

    legendControl.addTo(map);

    return () => {
      legendControl.remove();
    };
  }, [map, legend, legendTitle, thresholds, scale, values]);

  return <GeoJSON data={geoData} style={style} onEachFeature={onEachFeature} />;
}

export default ChoroplethLayer;
