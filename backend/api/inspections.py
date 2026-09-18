from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.models.orm import Inspection
from backend.models.schemas import InspectionResponse

router = APIRouter(prefix="/inspections", tags=["Inspections"])

@router.get("", response_model=List[InspectionResponse])
def get_inspections(
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Inspection)
    if status:
        query = query.filter(Inspection.status == status)
    return query.order_by(Inspection.created_at.desc()).limit(limit).all()

@router.get("/{inspection_id}", response_model=InspectionResponse)
def get_inspection_detail(inspection_id: str, db: Session = Depends(get_db)):
    insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found.")
    return insp
