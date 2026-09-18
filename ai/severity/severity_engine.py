"""
Mathematical Severity and Maintenance Priority Engine for Road Damage Detection.
Calculates transparent severity scores, maintenance priorities, and road condition ratings
based on measurable visual characteristics, spatial dimensions, and model confidence.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# 10 Core Damage Classes as defined in requirements
DAMAGE_CLASSES = [
    "Pothole",
    "Longitudinal crack",
    "Transverse crack",
    "Alligator crack",
    "Edge crack",
    "Surface deformation",
    "Rutting",
    "Patch damage",
    "Manhole/road-surface defect",
    "Other road damage"
]

# Base structural hazard weights (0.0 to 1.0)
CLASS_RISK_WEIGHTS: Dict[str, float] = {
    "Pothole": 0.95,
    "Alligator crack": 0.90,
    "Rutting": 0.85,
    "Manhole/road-surface defect": 0.80,
    "Surface deformation": 0.75,
    "Edge crack": 0.70,
    "Transverse crack": 0.65,
    "Longitudinal crack": 0.60,
    "Other road damage": 0.55,
    "Patch damage": 0.50
}

@dataclass
class SeverityConfig:
    weight_area: float = 0.30
    weight_dimension: float = 0.20
    weight_risk: float = 0.20
    weight_confidence: float = 0.15
    weight_persistence: float = 0.15
    
    # Severity Score Thresholds
    threshold_low: float = 30.0
    threshold_moderate: float = 60.0
    threshold_high: float = 80.0
    
    # Priority Score Thresholds
    priority_low_threshold: float = 35.0
    priority_medium_threshold: float = 65.0
    priority_high_threshold: float = 85.0

class SeverityEngine:
    def __init__(self, config: Optional[SeverityConfig] = None):
        self.config = config or SeverityConfig()

    def calculate_severity(self,
                           damage_type: str,
                           confidence: float,
                           bbox: List[float],
                           image_width: int,
                           image_height: int,
                           mask_area_pixels: Optional[float] = None,
                           persistence_frames: int = 1,
                           max_persistence: int = 10,
                           lane_position: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates transparent severity score (0 to 100) and component breakdown.
        
        Args:
            damage_type: Name of defect class
            confidence: Model prediction confidence (0.0 - 1.0)
            bbox: [x1, y1, x2, y2]
            image_width: width of image/frame
            image_height: height of image/frame
            mask_area_pixels: segmented area in pixels (if available)
            persistence_frames: number of consecutive frames defect is tracked
            max_persistence: normalization cap for video persistence
            lane_position: optional 'wheel_path', 'lane_center', 'shoulder'
        """
        img_area = max(1.0, float(image_width * image_height))
        w = max(1.0, bbox[2] - bbox[0])
        h = max(1.0, bbox[3] - bbox[1])
        bbox_area = w * h

        # 1. Area Score: Normalized relative area
        # For road imagery, an individual defect occupying > 8% of total frame is massive
        effective_area = mask_area_pixels if (mask_area_pixels is not None and mask_area_pixels > 0) else bbox_area
        area_ratio = min(1.0, (effective_area / img_area) / 0.08)
        area_score = area_ratio

        # 2. Dimension Score: Elongation or structural span
        # Long cracks spanning across lanes represent higher structural hazard
        aspect_ratio = max(w / h, h / w)
        dimension_score = min(1.0, aspect_ratio / 6.0)

        # 3. Damage Type Base Risk
        risk_weight = CLASS_RISK_WEIGHTS.get(damage_type, 0.55)

        # 4. Confidence
        norm_conf = max(0.0, min(1.0, confidence))

        # 5. Temporal Persistence in video (avoids transient false alarms)
        persistence_score = min(1.0, persistence_frames / max(1.0, float(max_persistence)))

        # Composite Severity Score
        raw_score = (
            self.config.weight_area * area_score +
            self.config.weight_dimension * dimension_score +
            self.config.weight_risk * risk_weight +
            self.config.weight_confidence * norm_conf +
            self.config.weight_persistence * persistence_score
        )
        
        severity_score = round(min(100.0, max(0.0, raw_score * 100.0)), 1)

        # Severity Classification Level
        if severity_score <= self.config.threshold_low:
            severity_level = "Low"
        elif severity_score <= self.config.threshold_moderate:
            severity_level = "Moderate"
        elif severity_score <= self.config.threshold_high:
            severity_level = "High"
        else:
            severity_level = "Critical"

        # Detailed Factor Breakdown for Explainability
        factors = {
            "area_score": round(area_score * 100, 1),
            "area_pixels": round(effective_area, 1),
            "area_ratio_pct": round((effective_area / img_area) * 100, 2),
            "dimension_score": round(dimension_score * 100, 1),
            "aspect_ratio": round(aspect_ratio, 2),
            "type_risk_score": round(risk_weight * 100, 1),
            "confidence_score": round(norm_conf * 100, 1),
            "persistence_score": round(persistence_score * 100, 1),
            "tracked_frames": persistence_frames,
            "lane_position": lane_position or "road_surface"
        }

        return {
            "severity_score": severity_score,
            "severity_level": severity_level,
            "factors": factors
        }

    def calculate_priority(self,
                           severity_score: float,
                           damage_type: str,
                           nearby_defect_count: int = 0,
                           road_importance: str = "arterial",
                           confidence: float = 0.9) -> Dict[str, Any]:
        """
        Determines Maintenance Priority (Low, Medium, High, Urgent).
        Combines AI severity with road functional classification and cluster density.
        """
        # Road classification multiplier
        importance_weights = {
            "expressway": 1.0,
            "highway": 0.95,
            "arterial": 0.85,
            "collector": 0.70,
            "local_residential": 0.55
        }
        imp_score = importance_weights.get(road_importance.lower(), 0.75) * 100.0

        # Cluster density bonus (multiple defects in close proximity escalate priority)
        density_score = min(100.0, nearby_defect_count * 25.0)

        type_risk = CLASS_RISK_WEIGHTS.get(damage_type, 0.55) * 100.0

        priority_index = (
            0.45 * severity_score +
            0.25 * type_risk +
            0.15 * density_score +
            0.15 * imp_score
        )
        priority_index = round(min(100.0, max(0.0, priority_index)), 1)

        if priority_index <= self.config.priority_low_threshold:
            priority_level = "LOW PRIORITY"
            recommended_action = "Routine maintenance; re-evaluate during scheduled quarterly inspection."
            sla_days = 90
        elif priority_index <= self.config.priority_medium_threshold:
            priority_level = "MEDIUM PRIORITY"
            recommended_action = "Schedule asphalt surface sealing or leveling within 30 days."
            sla_days = 30
        elif priority_index <= self.config.priority_high_threshold:
            priority_level = "HIGH PRIORITY"
            recommended_action = "Dispatch road maintenance squad within 7 days for targeted patching."
            sla_days = 7
        else:
            priority_level = "URGENT"
            recommended_action = "Immediate structural hazard alert! Deploy emergency repair crew within 24-48 hours."
            sla_days = 2

        return {
            "priority_index": priority_index,
            "priority_level": priority_level,
            "recommended_action": recommended_action,
            "target_sla_days": sla_days,
            "disclaimer": "AI-assisted maintenance recommendation. Final engineering sign-off required."
        }

    def compute_road_health_index(self, defects: List[Dict[str, Any]], segment_length_meters: float = 500.0) -> Dict[str, Any]:
        """
        Calculates overall Road Health Index (RHI 0-100, akin to Pavement Condition Index PCI).
        """
        if not defects:
            return {
                "road_health_index": 100.0,
                "rating": "Excellent",
                "defect_density_per_km": 0.0,
                "condition_summary": "Pavement in optimal condition with no active defects."
            }

        total_deduct = 0.0
        for d in defects:
            sev = d.get("severity_score", 40.0)
            dtype = d.get("damage_type", "Other road damage")
            weight = CLASS_RISK_WEIGHTS.get(dtype, 0.55)
            # Deduct contribution
            total_deduct += (sev * 0.4) * weight

        # Length normalization
        km_factor = max(0.1, segment_length_meters / 1000.0)
        density_per_km = round(len(defects) / km_factor, 1)

        rhi = max(0.0, min(100.0, 100.0 - (total_deduct / km_factor * 0.6)))
        rhi = round(rhi, 1)

        if rhi >= 85:
            rating = "Good"
        elif rhi >= 65:
            rating = "Fair"
        elif rhi >= 45:
            rating = "Poor"
        else:
            rating = "Failed"

        return {
            "road_health_index": rhi,
            "rating": rating,
            "defect_density_per_km": density_per_km,
            "total_defects": len(defects)
        }
