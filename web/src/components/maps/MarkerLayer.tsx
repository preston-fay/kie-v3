/**
 * Marker Layer Component
 *
 * Point markers with optional clustering and KDS styling.
 */


import { Marker, Popup, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';

interface MarkerData {
  id: string | number;
  latitude: number;
  longitude: number;
  [key: string]: any;
}

interface MarkerLayerProps {
  data: MarkerData[];
  cluster?: boolean;
  icon?: L.Icon | L.DivIcon;
  popupFields?: string[]; // Fields to show in popup
  tooltipField?: string; // Field to show in tooltip
  onMarkerClick?: (marker: MarkerData) => void;
}

/**
 * Default KDS marker icon
 */
const KDS_MARKER_ICON = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

/**
 * Create KDS-styled popup content
 */
function createPopupContent(marker: MarkerData, fields?: string[]): string {
  const fieldsToShow = fields || Object.keys(marker).filter(k => k !== 'latitude' && k !== 'longitude');

  let html = '<div style="font-family: Inter, Arial, sans-serif; color: #FFFFFF;">';

  for (const field of fieldsToShow) {
    const value = marker[field];
    if (value !== undefined && value !== null) {
      html += `<b>${field}:</b> ${value}<br>`;
    }
  }

  html += '</div>';
  return html;
}

/**
 * Marker layer component
 */
export function MarkerLayer({
  data,
  cluster = false,
  icon = KDS_MARKER_ICON,
  popupFields,
  tooltipField,
  onMarkerClick,
}: MarkerLayerProps) {
  // Filter out invalid coordinates
  const validMarkers = data.filter(
    (m) =>
      m.latitude !== null &&
      m.latitude !== undefined &&
      m.longitude !== null &&
      m.longitude !== undefined &&
      !isNaN(m.latitude) &&
      !isNaN(m.longitude)
  );

  // Create marker elements
  const markerElements = validMarkers.map((marker) => {
    const position: [number, number] = [marker.latitude, marker.longitude];
    const popupContent = createPopupContent(marker, popupFields);
    const tooltipContent = tooltipField ? String(marker[tooltipField]) : undefined;

    return (
      <Marker
        key={marker.id}
        position={position}
        icon={icon}
        eventHandlers={{
          click: () => {
            if (onMarkerClick) {
              onMarkerClick(marker);
            }
          },
        }}
      >
        <Popup>
          <div dangerouslySetInnerHTML={{ __html: popupContent }} />
        </Popup>
        {tooltipContent && <Tooltip>{tooltipContent}</Tooltip>}
      </Marker>
    );
  });

  // Return with or without clustering
  if (cluster) {
    return (
      <MarkerClusterGroup
        chunkedLoading
        iconCreateFunction={(cluster) => {
          const count = cluster.getChildCount();
          return L.divIcon({
            html: `<div style="
              background-color: #7823DC;
              color: #FFFFFF;
              border-radius: 50%;
              width: 40px;
              height: 40px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-family: Inter, Arial, sans-serif;
              font-weight: bold;
              border: 2px solid #FFFFFF;
            ">${count}</div>`,
            className: 'marker-cluster-custom',
            iconSize: L.point(40, 40, true),
          });
        }}
      >
        {markerElements}
      </MarkerClusterGroup>
    );
  }

  return <>{markerElements}</>;
}

export default MarkerLayer;
