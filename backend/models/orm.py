from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    role = Column(String(30), default="engineer")
    created_at = Column(DateTime, default=datetime.utcnow)

class Inspection(Base):
    __tablename__ = "inspections"
    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(100), default="Road Inspection Survey")
    road_name = Column(String(100), default="State Highway 17")
    inspection_type = Column(String(30), default="image") # image, video, live_stream
    media_path = Column(String(255), nullable=True)
    total_defects = Column(Integer, default=0)
    pothole_count = Column(Integer, default=0)
    crack_count = Column(Integer, default=0)
    other_count = Column(Integer, default=0)
    avg_severity = Column(Float, default=0.0)
    max_severity = Column(Float, default=0.0)
    road_health_index = Column(Float, default=100.0)
    priority_level = Column(String(30), default="LOW PRIORITY")
    status = Column(String(30), default="completed")
    start_latitude = Column(Float, nullable=True)
    start_longitude = Column(Float, nullable=True)
    end_latitude = Column(Float, nullable=True)
    end_longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    damage_events = relationship("DamageEvent", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")

class DamageEvent(Base):
    __tablename__ = "damage_events"
    id = Column(String(50), primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.id"), index=True, nullable=True)
    damage_type = Column(String(50), index=True, nullable=False)
    confidence = Column(Float, default=0.0)
    severity_score = Column(Float, default=0.0)
    severity_level = Column(String(20), default="Moderate") # Low, Moderate, High, Critical
    priority = Column(String(30), default="MEDIUM PRIORITY") # LOW, MEDIUM, HIGH, URGENT
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    image_path = Column(String(255), nullable=True)
    annotated_image_path = Column(String(255), nullable=True)
    tracking_id = Column(Integer, nullable=True)
    status = Column(String(30), default="confirmed") # detected, confirmed, reviewed, repaired
    bbox = Column(JSON, nullable=True) # [x1, y1, x2, y2]
    mask = Column(JSON, nullable=True) # polygon coordinates
    factors = Column(JSON, nullable=True) # explainability breakdown
    human_verified = Column(Boolean, default=False)
    human_notes = Column(Text, nullable=True)

    inspection = relationship("Inspection", back_populates="damage_events")

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    road_segment_id = Column(String(50), index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, default=45.0)
    heading_deg = Column(Float, default=180.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True, index=True)
    damage_event_id = Column(String(50), ForeignKey("damage_events.id"), nullable=True)
    frame_number = Column(Integer, default=0)
    damage_type = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    bbox = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    id = Column(String(50), primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.id"), nullable=True)
    title = Column(String(100), default="Road Condition Assessment Report")
    road_id = Column(String(50), default="SH-17-SEC-A")
    format = Column(String(10), default="JSON") # PDF, CSV, JSON
    file_path = Column(String(255), nullable=True)
    summary_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="reports")

class ModelRun(Base):
    __tablename__ = "model_runs"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(80), default="YOLO11n-seg")
    device = Column(String(30), default="cpu")
    inference_fps = Column(Float, default=30.0)
    latency_ms = Column(Float, default=33.3)
    map50 = Column(Float, default=0.873)
    created_at = Column(DateTime, default=datetime.utcnow)
