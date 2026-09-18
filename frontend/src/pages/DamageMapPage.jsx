import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Filter, Layers, AlertTriangle, ShieldCheck, Flame, Zap, Eye } from 'lucide-react';
import SeverityBadge from '../components/SeverityBadge';
import PriorityBadge from '../components/PriorityBadge';
import DamageModal from '../components/DamageModal';
import { fetchMapTelemetry, getMediaUrl } from '../services/api';

export default function DamageMapPage() {
  const mapContainerRef = useRef(null);
  const leafletMapRef = useRef(null);
  const markersGroupRef = useRef(null);

  const [mapData, setMapData] = useState(null);
  const [selectedDamage, setSelectedDamage] = useState(null);
  const [filterClass, setFilterClass] = useState('ALL');
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [heatmapMode, setHeatmapMode] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMapTelemetry()
      .then(data => {
        setMapData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Map fetch error:", err);
        setLoading(false);
      });
  }, []);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || !mapData || leafletMapRef.current) return;

    // Load Leaflet global
    if (window.L) {
      const L = window.L;
      const center = mapData.center || [11.0168, 76.9558];
      
      const map = L.map(mapContainerRef.current, {
        center: center,
        zoom: 13,
        zoomControl: true
      });

      // Dark Matter Carto TileLayer
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
        maxZoom: 19
      }).addTo(map);

      const markersGroup = L.layerGroup().addTo(map);
      leafletMapRef.current = map;
      markersGroupRef.current = markersGroup;

      renderMarkers(mapData.features, filterClass, filterSeverity);
    }
  }, [mapData]);

  // Update markers when filters change
  useEffect(() => {
    if (mapData && markersGroupRef.current) {
      renderMarkers(mapData.features, filterClass, filterSeverity);
    }
  }, [filterClass, filterSeverity]);

  const renderMarkers = (features, fClass, fSev) => {
    if (!markersGroupRef.current || !window.L) return;
    const L = window.L;
    markersGroupRef.current.clearLayers();

    const filtered = (features || []).filter(f => {
      const p = f.properties;
      if (fClass !== 'ALL' && p.damage_type !== fClass) return false;
      if (fSev !== 'ALL' && p.severity_level !== fSev) return false;
      return true;
    });

    filtered.forEach(feature => {
      const [lng, lat] = feature.geometry.coordinates;
      const p = feature.properties;

      // Color coding based on severity
      let markerColor = '#38bdf8';
      if (p.severity_level === 'Critical') markerColor = '#ef4444';
      else if (p.severity_level === 'High') markerColor = '#f97316';
      else if (p.severity_level === 'Moderate') markerColor = '#f59e0b';
      else if (p.severity_level === 'Low') markerColor = '#10b981';

      // Custom pulsing SVG marker icon
      const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `
          <div style="
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: ${markerColor};
            border: 2px solid #ffffff;
            box-shadow: 0 0 14px ${markerColor};
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
          ">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #ffffff;"></div>
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const marker = L.marker([lat, lng], { icon: customIcon });

      // Rich Interactive Popup Content
      const popupContent = `
        <div style="min-width: 220px; padding: 4px; font-family: Inter, sans-serif;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 11px; font-weight: 700; color: ${markerColor}; text-transform: uppercase;">
              ${p.severity_level} SEVERITY (${Math.round(p.severity_score)})
            </span>
            <span style="font-size: 10px; color: #94a3b8;">${Math.round(p.confidence * 100)}% Conf</span>
          </div>
          <h4 style="font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 6px;">
            ${p.damage_type}
          </h4>
          <p style="font-size: 11px; color: #94a3b8; margin-bottom: 8px;">
            Priority: <strong>${p.priority}</strong>
          </p>
          <div style="font-size: 10px; color: #64748b; margin-bottom: 8px;">
            GPS: ${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E
          </div>
          <button
            id="inspect-btn-${p.id}"
            style="
              width: 100%;
              background: #0284c7;
              color: white;
              border: none;
              padding: 6px 10px;
              border-radius: 6px;
              font-size: 11px;
              font-weight: 600;
              cursor: pointer;
            "
          >
            Inspect & Calibrate
          </button>
        </div>
      `;

      marker.bindPopup(popupContent);
      marker.on('popupopen', () => {
        const btn = document.getElementById(`inspect-btn-${p.id}`);
        if (btn) {
          btn.onclick = () => {
            setSelectedDamage({
              id: p.id,
              damage_type: p.damage_type,
              confidence: p.confidence,
              severity_score: p.severity_score,
              severity_level: p.severity_level,
              priority: p.priority,
              latitude: lat,
              longitude: lng,
              image_path: p.image_url,
              annotated_image_path: p.image_url,
              status: p.status,
              human_verified: p.human_verified
            });
          };
        }
      });

      marker.addTo(markersGroupRef.current);
    });
  };

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto', padding: '24px 24px 60px' }}>
      {/* Header & Filter Controls Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 20,
        flexWrap: 'wrap',
        gap: 16
      }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', color: '#f8fafc', marginBottom: 4 }}>
            Geospatial Road Damage & Maintenance Heatmap
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem' }}>
            Interactive GIS defect telemetry, cluster density & spatial maintenance priorities
          </p>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(15, 23, 42, 0.7)', padding: '6px 12px', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
            <Filter size={15} color="#38bdf8" />
            <select
              value={filterClass}
              onChange={e => setFilterClass(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: '#f8fafc', fontSize: '0.82rem', outline: 'none' }}
            >
              <option value="ALL">All Damage Classes</option>
              <option value="Pothole">Potholes</option>
              <option value="Alligator crack">Alligator Cracks</option>
              <option value="Longitudinal crack">Longitudinal Cracks</option>
              <option value="Transverse crack">Transverse Cracks</option>
              <option value="Rutting">Rutting</option>
              <option value="Manhole/road-surface defect">Manhole Defects</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(15, 23, 42, 0.7)', padding: '6px 12px', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
            <select
              value={filterSeverity}
              onChange={e => setFilterSeverity(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: '#f8fafc', fontSize: '0.82rem', outline: 'none' }}
            >
              <option value="ALL">All Severities</option>
              <option value="Critical">Critical (81-100)</option>
              <option value="High">High (61-80)</option>
              <option value="Moderate">Moderate (31-60)</option>
              <option value="Low">Low (0-30)</option>
            </select>
          </div>

          <button
            className={heatmapMode ? 'btn-primary' : 'btn-secondary'}
            onClick={() => setHeatmapMode(!heatmapMode)}
            style={{ fontSize: '0.82rem' }}
          >
            <Layers size={15} /> {heatmapMode ? 'Heatmap: ACTIVE' : 'Defect Pins'}
          </button>
        </div>
      </div>

      {/* Map Container & Legend Strip */}
      <div className="glass-panel" style={{ padding: 12, position: 'relative' }}>
        <div
          ref={mapContainerRef}
          style={{ width: '100%', height: 600, borderRadius: 12, overflow: 'hidden' }}
        />

        {/* Floating Legend */}
        <div style={{
          position: 'absolute',
          bottom: 28,
          right: 28,
          zIndex: 1000,
          background: 'rgba(8, 12, 20, 0.85)',
          backdropFilter: 'blur(12px)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 10,
          padding: '12px 18px',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          fontSize: '0.78rem'
        }}>
          <strong style={{ color: '#f8fafc', marginBottom: 2 }}>Severity Legend</strong>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444', boxShadow: '0 0 8px #ef4444' }} />
            <span style={{ color: '#f8fafc' }}>Critical Hazard (81-100)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f97316' }} />
            <span style={{ color: '#f8fafc' }}>High Severity (61-80)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }} />
            <span style={{ color: '#f8fafc' }}>Moderate (31-60)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }} />
            <span style={{ color: '#f8fafc' }}>Low Impact (0-30)</span>
          </div>
        </div>
      </div>

      {/* Detail & Calibration Modal */}
      {selectedDamage && (
        <DamageModal
          damage={selectedDamage}
          onClose={() => setSelectedDamage(null)}
        />
      )}
    </div>
  );
}
