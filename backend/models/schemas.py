from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class LocationCoord(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None

class SeverityFactors(BaseModel):
    area_score: float
    area_pixels: float
    area_ratio_pct: float
    dimension_score: float
    aspect_ratio: float
    type_risk_score: float
    confidence_score: float
    persistence_score: float
    tracked_frames: int
    lane_position: str

class DamageEventBase(BaseModel):
    damage_type: str
    confidence: float
    severity_score: float
    severity_level: str
    priority: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bbox: List[float] = Field(default_factory=list)
    mask: Optional[List[List[float]]] = None
    factors: Optional[Dict[str, Any]] = None

class DamageEventResponse(DamageEventBase):
    id: str
    inspection_id: Optional[str] = None
    timestamp: datetime
    image_path: Optional[str] = None
    annotated_image_path: Optional[str] = None
    tracking_id: Optional[int] = None
    status: str
    human_verified: bool = False
    human_notes: Optional[str] = None

    class Config:
        from_attributes = True

class InspectionCreate(BaseModel):
    title: Optional[str] = "Road Inspection Survey"
    road_name: Optional[str] = "State Highway 17"
    inspection_type: Optional[str] = "image"
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None

class InspectionResponse(BaseModel):
    id: str
    title: str
    road_name: str
    inspection_type: str
    media_path: Optional[str] = None
    total_defects: int
    pothole_count: int
    crack_count: int
    other_count: int
    avg_severity: float
    max_severity: float
    road_health_index: float
    priority_level: str
    status: str
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DetectionResult(BaseModel):
    damage_type: str
    confidence: float
    severity_score: float
    severity_level: str
    priority: str
    bbox: List[float]
    mask: Optional[List[List[float]]] = None
    area_pixels: float
    factors: Optional[Dict[str, Any]] = None
    location: Optional[LocationCoord] = None

class ImageDetectionResponse(BaseModel):
    success: bool
    inspection_id: str
    processing_time_ms: float
    total_damages: int
    road_health_index: float
    priority_recommendation: str
    lighting_assessment: Dict[str, Any]
    detections: List[DetectionResult]
    annotated_image_url: str

class VideoDetectionResponse(BaseModel):
    success: bool
    inspection_id: str
    total_frames_processed: int
    unique_damage_events: int
    road_health_index: float
    processing_fps: float
    summary_events: List[Dict[str, Any]]
    output_video_url: Optional[str] = None

class HumanReviewUpdate(BaseModel):
    verified_damage_type: Optional[str] = None
    verified_severity_score: Optional[float] = None
    status: Optional[str] = "reviewed"
    notes: Optional[str] = None

class ReportGenerateRequest(BaseModel):
    inspection_id: Optional[str] = None
    format: str = "JSON" # PDF, CSV, JSON
    title: Optional[str] = "Comprehensive Road Condition Assessment Report"
    road_id: Optional[str] = "SH-17"
