import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from backend.app.database import get_db
from backend.models.orm import DamageEvent

router = APIRouter(prefix="/map", tags=["GIS Map"])

@router.get("")
def get_map_telemetry(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns GeoJSON FeatureCollection of all road damage events with coordinates,
    plus heatmap data points [lat, lng, intensity] for Leaflet heatmaps.
    """
    events = db.query(DamageEvent).filter(DamageEvent.latitude.isnot(None), DamageEvent.longitude.isnot(None)).all()

    features = []
    heatmap_points = []

    for evt in events:
        # Intensity scaled by severity (0.2 to 1.0)
        intensity = max(0.2, min(1.0, evt.severity_score / 100.0))
        heatmap_points.append([evt.latitude, evt.longitude, round(intensity, 2)])

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [evt.longitude, evt.latitude]
            },
            "properties": {
                "id": evt.id,
                "damage_type": evt.damage_type,
                "severity_score": evt.severity_score,
                "severity_level": evt.severity_level,
                "priority": evt.priority,
                "confidence": evt.confidence,
                "timestamp": evt.timestamp.isoformat() if evt.timestamp else None,
                "status": evt.status,
                "human_verified": evt.human_verified,
                "image_url": f"/api/uploads/{evt.annotated_image_path.split(os.sep)[-1]}" if (evt.annotated_image_path and os.path.exists(evt.annotated_image_path)) else None
            }
        }
        features.append(feature)

    # Road corridor center for camera centering (default to Coimbatore / South corridor)
    center_lat = 11.0168
    center_lng = 76.9558
    if events:
        center_lat = round(sum(e.latitude for e in events) / len(events), 5)
        center_lng = round(sum(e.longitude for e in events) / len(events), 5)

    return {
        "type": "FeatureCollection",
        "center": [center_lat, center_lng],
        "total_mapped_defects": len(features),
        "features": features,
        "heatmap_points": heatmap_points
    }
