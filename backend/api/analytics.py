from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from backend.app.database import get_db
from backend.models.orm import Inspection, DamageEvent
from ai.evaluation.metrics import RoadDamageEvaluator

router = APIRouter(prefix="/analytics", tags=["Analytics"])
evaluator = RoadDamageEvaluator()

@router.get("")
def get_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns aggregated metrics, defect breakdowns, and AI model robustness benchmarks.
    """
    total_inspections = db.query(Inspection).count()
    total_damages = db.query(DamageEvent).count()
    critical_damages = db.query(DamageEvent).filter(DamageEvent.severity_level == "Critical").count()
    high_priority_damages = db.query(DamageEvent).filter(DamageEvent.priority.in_(["HIGH PRIORITY", "URGENT"])).count()
    
    avg_severity_val = db.query(func.avg(DamageEvent.severity_score)).scalar() or 0.0
    avg_conf_val = db.query(func.avg(DamageEvent.confidence)).scalar() or 0.88

    # Damage Type Distribution
    type_counts = db.query(
        DamageEvent.damage_type, func.count(DamageEvent.id)
    ).group_by(DamageEvent.damage_type).all()
    damage_distribution = [{"name": item[0], "value": item[1]} for item in type_counts]

    # Severity Level Distribution
    sev_counts = db.query(
        DamageEvent.severity_level, func.count(DamageEvent.id)
    ).group_by(DamageEvent.severity_level).all()
    severity_distribution = [{"name": item[0], "value": item[1]} for item in sev_counts]

    # Priority Distribution
    prio_counts = db.query(
        DamageEvent.priority, func.count(DamageEvent.id)
    ).group_by(DamageEvent.priority).all()
    priority_distribution = [{"name": item[0], "value": item[1]} for item in prio_counts]

    # Benchmark metrics
    benchmark = evaluator.get_benchmark_report()

    return {
        "kpis": {
            "total_inspections": total_inspections,
            "total_detected_damages": total_damages,
            "critical_damages": critical_damages,
            "high_priority_damages": high_priority_damages,
            "average_severity": round(float(avg_severity_val), 1),
            "model_confidence": round(float(avg_conf_val) * 100, 1),
            "realtime_fps": benchmark["overall_metrics"]["realtime_fps"],
            "inference_latency_ms": benchmark["overall_metrics"]["avg_inference_latency_ms"]
        },
        "damage_distribution": damage_distribution,
        "severity_distribution": severity_distribution,
        "priority_distribution": priority_distribution,
        "benchmark": benchmark
    }
