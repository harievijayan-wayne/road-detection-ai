import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from backend.app.database import get_db
from backend.models.orm import Inspection, DamageEvent, Report
from backend.models.schemas import ReportGenerateRequest
from backend.services.report_generator import report_generator

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/generate")
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    """
    Generates downloadable report in PDF, CSV, or JSON format.
    """
    insp = None
    if payload.inspection_id:
        insp = db.query(Inspection).filter(Inspection.id == payload.inspection_id).first()
    
    events_query = db.query(DamageEvent)
    if payload.inspection_id:
        events_query = events_query.filter(DamageEvent.inspection_id == payload.inspection_id)
    events = events_query.all()

    # Build summary
    total_defects = len(events)
    avg_sev = round(sum(e.severity_score for e in events) / max(1, total_defects), 1)
    
    summary = {
        "inspection_id": insp.id if insp else "ALL_INSPECTIONS",
        "road_id": insp.road_name if insp else payload.road_id,
        "road_health_index": insp.road_health_index if insp else 76.5,
        "priority_recommendation": insp.priority_level if insp else "HIGH PRIORITY",
        "total_defects": total_defects,
        "avg_severity": avg_sev
    }

    damage_dicts = [
        {
            "id": e.id,
            "damage_type": e.damage_type,
            "confidence": e.confidence,
            "severity_score": e.severity_score,
            "severity_level": e.severity_level,
            "priority": e.priority,
            "latitude": e.latitude,
            "longitude": e.longitude,
            "tracking_id": e.tracking_id or 1,
            "status": e.status
        }
        for e in events
    ]

    report_id = f"REP-{payload.format.upper()}-{uuid.uuid4().hex[:6]}"
    
    if payload.format.upper() == "PDF":
        file_path = report_generator.generate_pdf_report(summary, damage_dicts, f"{report_id}.pdf")
    elif payload.format.upper() == "CSV":
        file_path = report_generator.generate_csv_report(summary, damage_dicts, f"{report_id}.csv")
    else:
        file_path = report_generator.generate_json_report({"summary": summary, "defects": damage_dicts}, f"{report_id}.json")

    # Persist report record
    db_rep = Report(
        id=report_id,
        inspection_id=insp.id if insp else None,
        title=payload.title or "Road Condition Assessment Report",
        road_id=summary["road_id"],
        format=payload.format.upper(),
        file_path=file_path,
        summary_data=summary
    )
    db.add(db_rep)
    db.commit()

    return {
        "report_id": report_id,
        "format": payload.format.upper(),
        "download_url": f"/api/reports/download/{report_id}",
        "summary": summary
    }

@router.get("/download/{report_id}")
def download_report(report_id: str, db: Session = Depends(get_db)):
    rep = db.query(Report).filter(Report.id == report_id).first()
    if not rep or not os.path.exists(rep.file_path):
        raise HTTPException(status_code=404, detail="Report file not found.")

    media_types = {
        "PDF": "application/pdf",
        "CSV": "text/csv",
        "JSON": "application/json"
    }
    media_type = media_types.get(rep.format, "application/octet-stream")
    return FileResponse(rep.file_path, media_type=media_type, filename=os.path.basename(rep.file_path))
