from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.models.orm import DamageEvent
from backend.models.schemas import DamageEventResponse, HumanReviewUpdate

router = APIRouter(prefix="/damages", tags=["Damage Events"])

@router.get("", response_model=List[DamageEventResponse])
def get_damages(
    damage_type: Optional[str] = Query(None),
    severity_level: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    inspection_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """List all detected damage events with optional class, severity, and priority filtering."""
    query = db.query(DamageEvent)
    if damage_type:
        query = query.filter(DamageEvent.damage_type.ilike(f"%{damage_type}%"))
    if severity_level:
        query = query.filter(DamageEvent.severity_level == severity_level)
    if priority:
        query = query.filter(DamageEvent.priority == priority)
    if inspection_id:
        query = query.filter(DamageEvent.inspection_id == inspection_id)
    
    return query.order_by(DamageEvent.timestamp.desc()).limit(limit).all()

@router.get("/{event_id}", response_model=DamageEventResponse)
def get_damage_detail(event_id: str, db: Session = Depends(get_db)):
    """Retrieve full details, factors breakdown, and coordinates for a single damage event."""
    evt = db.query(DamageEvent).filter(DamageEvent.id == event_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Damage event not found.")
    return evt

@router.patch("/{event_id}/review", response_model=DamageEventResponse)
def review_damage_event(event_id: str, payload: HumanReviewUpdate, db: Session = Depends(get_db)):
    """
    Human-in-the-Loop Verification / Active Learning feedback loop.
    Allows civil engineers to confirm, correct defect classification or severity.
    """
    evt = db.query(DamageEvent).filter(DamageEvent.id == event_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Damage event not found.")

    if payload.verified_damage_type:
        evt.damage_type = payload.verified_damage_type
    if payload.verified_severity_score is not None:
        evt.severity_score = payload.verified_severity_score
    if payload.status:
        evt.status = payload.status
    if payload.notes:
        evt.human_notes = payload.notes

    evt.human_verified = True
    db.commit()
    db.refresh(evt)
    return evt
