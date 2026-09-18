import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.database import get_db
from backend.app.config import settings
from backend.models.orm import Inspection, DamageEvent
from backend.models.schemas import ImageDetectionResponse, VideoDetectionResponse
from backend.services.ai_pipeline import orchestrator

router = APIRouter(prefix="/detect", tags=["Detection"])

@router.post("/image", response_model=ImageDetectionResponse)
async def detect_image(
    file: UploadFile = File(...),
    road_name: Optional[str] = Form("Main Arterial Road"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts road imagery, runs lighting normalization, YOLO/CV detection & segmentation,
    calculates transparent severity and maintenance priority, and persists to DB.
    """
    allowed_exts = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported image file format '{ext}'.")

    # Save uploaded file safely
    insp_id = f"INSP-IMG-{uuid.uuid4().hex[:8]}"
    saved_filename = f"{insp_id}_{file.filename}"
    saved_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
    
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Default coordinates for demo if none passed: Coimbatore region
        eff_lat = latitude if latitude is not None else round(11.0168 + (uuid.uuid4().int % 200 - 100) * 0.0001, 5)
        eff_lng = longitude if longitude is not None else round(76.9558 + (uuid.uuid4().int % 200 - 100) * 0.0001, 5)

        result = orchestrator.process_image(
            image_path=saved_path,
            inspection_id=insp_id,
            latitude=eff_lat,
            longitude=eff_lng
        )

        # Persist Inspection record
        dets = result["detections"]
        potholes = sum(1 for d in dets if "pothole" in d["damage_type"].lower())
        cracks = sum(1 for d in dets if "crack" in d["damage_type"].lower())
        others = len(dets) - (potholes + cracks)
        avg_sev = round(sum(d["severity_score"] for d in dets) / max(1, len(dets)), 1)
        max_sev = max((d["severity_score"] for d in dets), default=0.0)

        db_insp = Inspection(
            id=insp_id,
            title=f"Inspection: {road_name}",
            road_name=road_name,
            inspection_type="image",
            media_path=saved_path,
            total_defects=len(dets),
            pothole_count=potholes,
            crack_count=cracks,
            other_count=others,
            avg_severity=avg_sev,
            max_severity=max_sev,
            road_health_index=result["road_health_index"],
            priority_level=result["priority_recommendation"],
            start_latitude=eff_lat,
            start_longitude=eff_lng,
            status="completed"
        )
        db.add(db_insp)
        db.flush()

        # Persist DamageEvents
        for d in dets:
            evt_id = f"EVT-{d['damage_type'][:3].upper()}-{uuid.uuid4().hex[:6]}"
            evt = DamageEvent(
                id=evt_id,
                inspection_id=insp_id,
                damage_type=d["damage_type"],
                confidence=d["confidence"],
                severity_score=d["severity_score"],
                severity_level=d["severity_level"],
                priority=d["priority"],
                latitude=eff_lat,
                longitude=eff_lng,
                image_path=saved_path,
                annotated_image_path=result["annotated_image_path"],
                bbox=d["bbox"],
                mask=d.get("mask"),
                factors=d.get("severity_factors"),
                status="confirmed"
            )
            db.add(evt)

        db.commit()

        return {
            "success": True,
            "inspection_id": insp_id,
            "processing_time_ms": result["processing_time_ms"],
            "total_damages": result["total_damages"],
            "road_health_index": result["road_health_index"],
            "priority_recommendation": result["priority_recommendation"],
            "lighting_assessment": result["lighting_assessment"],
            "detections": dets,
            "annotated_image_url": result["annotated_image_url"]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

@router.post("/video", response_model=VideoDetectionResponse)
async def detect_video(
    file: UploadFile = File(...),
    road_name: Optional[str] = Form("Highway Transit Corridor"),
    frame_skip: int = Form(2),
    db: Session = Depends(get_db)
):
    """
    Accepts road video, performs frame extraction, ByteTrack tracking,
    duplicate defect suppression, and generates aggregate event analytics.
    """
    insp_id = f"INSP-VID-{uuid.uuid4().hex[:8]}"
    saved_filename = f"{insp_id}_{file.filename}"
    saved_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = orchestrator.process_video(
            video_path=saved_path,
            inspection_id=insp_id,
            frame_skip=frame_skip
        )

        events = result["summary_events"]
        db_insp = Inspection(
            id=insp_id,
            title=f"Video Survey: {road_name}",
            road_name=road_name,
            inspection_type="video",
            media_path=saved_path,
            total_defects=len(events),
            pothole_count=sum(1 for e in events if "pothole" in e["damage_type"].lower()),
            crack_count=sum(1 for e in events if "crack" in e["damage_type"].lower()),
            other_count=sum(1 for e in events if "pothole" not in e["damage_type"].lower() and "crack" not in e["damage_type"].lower()),
            avg_severity=round(sum(e["peak_severity"] for e in events) / max(1, len(events)), 1),
            max_severity=max((e["peak_severity"] for e in events), default=0.0),
            road_health_index=result["road_health_index"],
            priority_level="HIGH PRIORITY" if len(events) > 3 else "MEDIUM PRIORITY",
            status="completed"
        )
        db.add(db_insp)
        db.commit()

        return {
            "success": True,
            "inspection_id": insp_id,
            "total_frames_processed": result["total_frames_processed"],
            "unique_damage_events": result["unique_damage_events"],
            "road_health_index": result["road_health_index"],
            "processing_fps": result["processing_fps"],
            "summary_events": events,
            "output_video_url": result["output_video_url"]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")
