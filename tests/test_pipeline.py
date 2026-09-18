"""
Automated Unit and Pipeline Tests for Road Damage AI System.
Tests:
- Lighting Robustness & Quality Assessment
- Mathematical Severity & Maintenance Priority Model
- Object Tracking & Duplicate Detection Suppression
- Database Schema and Endpoints
"""

import os
import cv2
import numpy as np
import pytest

from ai.preprocessing.lighting_robustness import LightingRobustnessEngine
from ai.severity.severity_engine import SeverityEngine, SeverityConfig, DAMAGE_CLASSES
from ai.tracking.tracker import RoadDamageTracker, compute_iou

def test_lighting_robustness():
    engine = LightingRobustnessEngine()
    
    # 1. Test normal synthetic image
    normal_img = np.full((100, 100, 3), 128, dtype=np.uint8)
    metrics = engine.assess_quality(normal_img)
    assert metrics["exposure_state"] == "normal"
    assert "quality_score" in metrics

    # 2. Test low-light image
    dark_img = np.full((100, 100, 3), 25, dtype=np.uint8)
    enhanced, report = engine.adaptive_normalize(dark_img)
    assert report["initial_metrics"]["exposure_state"] == "low_light"
    assert report["enhancement_applied"] is True
    assert enhanced.mean() > dark_img.mean()

    # 3. Test CLAHE in LAB space
    clahe_res = engine.apply_clahe(dark_img)
    assert clahe_res.shape == dark_img.shape

def test_severity_engine_scoring():
    engine = SeverityEngine()

    # Pothole test (high hazard)
    res_pothole = engine.calculate_severity(
        damage_type="Pothole",
        confidence=0.95,
        bbox=[100, 100, 250, 220],
        image_width=1280,
        image_height=720,
        persistence_frames=4
    )
    assert 0 <= res_pothole["severity_score"] <= 100
    assert res_pothole["severity_level"] in ["Low", "Moderate", "High", "Critical"]
    assert "factors" in res_pothole
    assert res_pothole["factors"]["type_risk_score"] == 95.0

    # Crack test
    res_crack = engine.calculate_severity(
        damage_type="Longitudinal crack",
        confidence=0.85,
        bbox=[200, 100, 220, 500],
        image_width=1280,
        image_height=720,
        persistence_frames=2
    )
    assert res_crack["severity_score"] >= 0
    # Longitudinal crack has lower type risk (60.0) than Pothole (95.0)
    assert res_crack["factors"]["type_risk_score"] == 60.0

def test_maintenance_priority():
    engine = SeverityEngine()
    
    # High severity pothole in arterial corridor
    prio_res = engine.calculate_priority(
        severity_score=85.0,
        damage_type="Pothole",
        nearby_defect_count=3,
        road_importance="highway"
    )
    assert prio_res["priority_level"] in ["HIGH PRIORITY", "URGENT"]
    assert prio_res["target_sla_days"] <= 7

def test_tracking_and_duplicate_suppression():
    tracker = RoadDamageTracker(iou_threshold=0.35, min_confirm_frames=2)

    # Frame 1: Defect appears
    det_f1 = [{
        "damage_type": "Pothole",
        "confidence": 0.90,
        "bbox": [100.0, 100.0, 200.0, 180.0],
        "severity_score": 75.0
    }]
    res_f1 = tracker.update(det_f1, frame_idx=1)
    assert len(res_f1) == 1
    event_id_1 = res_f1[0]["damage_event_id"]
    track_id_1 = res_f1[0]["track_id"]

    # Frame 2: Same pothole slightly shifted (as vehicle moves closer)
    det_f2 = [{
        "damage_type": "Pothole",
        "confidence": 0.92,
        "bbox": [105.0, 115.0, 215.0, 200.0],
        "severity_score": 78.0
    }]
    res_f2 = tracker.update(det_f2, frame_idx=2)
    assert len(res_f2) == 1
    # MUST have the same damage_event_id and track_id (duplicate suppression!)
    assert res_f2[0]["damage_event_id"] == event_id_1
    assert res_f2[0]["track_id"] == track_id_1
    assert res_f2[0]["persistence_frames"] == 2
    assert res_f2[0]["is_confirmed"] is True

    # Frame 3: Same pothole tracked again
    det_f3 = [{
        "damage_type": "Pothole",
        "confidence": 0.94,
        "bbox": [110.0, 130.0, 230.0, 220.0],
        "severity_score": 80.0
    }]
    res_f3 = tracker.update(det_f3, frame_idx=3)
    assert res_f3[0]["damage_event_id"] == event_id_1

    # Verify summary events has ONLY 1 unique event, NOT 3 events!
    summary = tracker.get_summary_events()
    assert len(summary) == 1
    assert summary[0]["total_frames"] == 3
    assert summary[0]["damage_type"] == "Pothole"
