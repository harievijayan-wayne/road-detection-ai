"""
Seed Data and Realistic Sample Image Generator for Hackathon Demo Mode.
Generates realistic asphalt textures with potholes, cracks, and shadow variations,
and populates the database with GPS-tagged inspection surveys.
"""

import os
import cv2
import uuid
import random
import numpy as np
from datetime import datetime, timedelta
from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.models.orm import Inspection, DamageEvent, Location, Report, ModelRun

def generate_sample_road_images():
    """Generates synthetic high-fidelity asphalt test images representing real defect conditions."""
    samples_dir = settings.SAMPLE_DATA_DIR
    os.makedirs(samples_dir, exist_ok=True)

    img_specs = [
        {"name": "sample_pothole_daylight.jpg", "defect": "pothole", "lighting": "normal"},
        {"name": "sample_alligator_crack.jpg", "defect": "alligator", "lighting": "normal"},
        {"name": "sample_longitudinal_crack_shadow.jpg", "defect": "longitudinal", "lighting": "shadow"},
        {"name": "sample_pothole_low_light.jpg", "defect": "pothole", "lighting": "low_light"},
        {"name": "sample_multi_defects_highway.jpg", "defect": "multi", "lighting": "normal"},
        {"name": "sample_transverse_crack.jpg", "defect": "transverse", "lighting": "normal"}
    ]

    for spec in img_specs:
        filepath = os.path.join(samples_dir, spec["name"])
        if os.path.exists(filepath):
            continue

        w, h = 1280, 720
        # Base asphalt road texture (medium-dark textured gray)
        base_gray = random.randint(75, 95)
        asphalt = np.full((h, w, 3), base_gray, dtype=np.uint8)
        
        # Asphalt granular aggregate noise
        noise = np.random.normal(0, 14, (h, w, 3)).astype(np.float32)
        asphalt = np.clip(asphalt.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        # Draw road lane markings (white/yellow dashed stripes)
        lane_color = (220, 220, 220)
        cv2.line(asphalt, (w // 2, 0), (w // 2, h), lane_color, 8)
        # Yellow edge line
        cv2.line(asphalt, (80, 0), (80, h), (30, 190, 220), 10)
        cv2.line(asphalt, (w - 80, 0), (w - 80, h), (220, 220, 220), 8)

        # Add defects based on spec
        defect_type = spec["defect"]
        if defect_type in ["pothole", "multi"]:
            # Dark cavity with rugged rim
            cx, cy = int(w * 0.38), int(h * 0.58)
            rx, ry = 85, 55
            cv2.ellipse(asphalt, (cx, cy), (rx + 15, ry + 10), 15, 0, 360, (50, 50, 50), -1)
            cv2.ellipse(asphalt, (cx, cy), (rx, ry), 15, 0, 360, (25, 25, 28), -1)
            # Internal depth contour
            cv2.ellipse(asphalt, (cx - 5, cy + 5), (rx - 25, ry - 18), 15, 0, 360, (15, 15, 18), -1)

        if defect_type in ["alligator", "multi"]:
            # Interconnected mesh of fine cracks
            grid_cx, grid_cy = int(w * 0.68), int(h * 0.62)
            for i in range(12):
                ox = grid_cx + random.randint(-110, 110)
                oy = grid_cy + random.randint(-70, 70)
                for _ in range(3):
                    tx = ox + random.randint(-40, 40)
                    ty = oy + random.randint(-35, 35)
                    cv2.line(asphalt, (ox, oy), (tx, ty), (28, 28, 30), random.randint(2, 4), cv2.LINE_AA)

        if defect_type in ["longitudinal", "multi"]:
            # Longitudinal road fissure
            pts = []
            curr_x = int(w * 0.48)
            for y in range(int(h * 0.2), int(h * 0.88), 35):
                curr_x += random.randint(-12, 12)
                pts.append([curr_x, y])
            for i in range(len(pts) - 1):
                cv2.line(asphalt, tuple(pts[i]), tuple(pts[i+1]), (22, 22, 25), 4, cv2.LINE_AA)

        if defect_type == "transverse":
            # Crack running horizontally across lane
            pts = []
            curr_y = int(h * 0.52)
            for x in range(int(w * 0.2), int(w * 0.8), 40):
                curr_y += random.randint(-8, 8)
                pts.append([x, curr_y])
            for i in range(len(pts) - 1):
                cv2.line(asphalt, tuple(pts[i]), tuple(pts[i+1]), (24, 24, 26), 4, cv2.LINE_AA)

        # Apply lighting variations
        lighting = spec["lighting"]
        if lighting == "low_light":
            asphalt = cv2.convertScaleAbs(asphalt, alpha=0.38, beta=-30)
        elif lighting == "shadow":
            shadow_mask = np.zeros((h, w), dtype=np.uint8)
            poly_pts = np.array([[0, 0], [w // 2, 0], [int(w * 0.7), h], [0, h]], dtype=np.int32)
            cv2.fillPoly(shadow_mask, [poly_pts], 255)
            shadow_mask = cv2.GaussianBlur(shadow_mask, (45, 45), 0)
            hls = cv2.cvtColor(asphalt, cv2.COLOR_BGR2HLS).astype(np.float32)
            hls[:, :, 1] = np.where(shadow_mask > 80, hls[:, :, 1] * 0.45, hls[:, :, 1])
            asphalt = cv2.cvtColor(np.clip(hls, 0, 255).astype(np.uint8), cv2.COLOR_HLS2BGR)

        cv2.imwrite(filepath, asphalt)

    # Also copy the first sample into uploads as ready-to-test
    sample1 = os.path.join(samples_dir, "sample_pothole_daylight.jpg")
    if os.path.exists(sample1):
        target = os.path.join(settings.UPLOAD_DIR, "demo_test_road.jpg")
        if not os.path.exists(target):
            import shutil
            shutil.copy(sample1, target)

def seed_database():
    """Populates database with realistic GPS inspections and damage events."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Inspection).count() > 0:
        db.close()
        return

    # Base GPS coordinates for demonstration: Coimbatore / Nilgiris Highway Corridor
    # (Coimbatore: 11.0168° N, 76.9558° E)
    base_lat = 11.0168
    base_lng = 76.9558

    surveys = [
        {
            "id": "INSP-CBE-101",
            "title": "Avinashi Road Express Corridor Inspection",
            "road_name": "NH 544 (Avinashi Road)",
            "type": "video",
            "rhi": 68.5,
            "priority": "HIGH PRIORITY",
            "defects": [
                {
                    "type": "Pothole", "conf": 0.94, "sev": 82.5, "level": "Critical", "prio": "URGENT",
                    "lat": base_lat + 0.0042, "lng": base_lng + 0.0051, "box": [420, 360, 610, 520],
                    "factors": {"area_score": 75.0, "dimension_score": 40.0, "type_risk_score": 95.0, "confidence_score": 94.0, "persistence_score": 85.0}
                },
                {
                    "type": "Alligator crack", "conf": 0.89, "sev": 74.0, "level": "High", "prio": "HIGH PRIORITY",
                    "lat": base_lat + 0.0078, "lng": base_lng + 0.0094, "box": [710, 410, 940, 580],
                    "factors": {"area_score": 82.0, "dimension_score": 60.0, "type_risk_score": 90.0, "confidence_score": 89.0, "persistence_score": 70.0}
                },
                {
                    "type": "Transverse crack", "conf": 0.88, "sev": 58.2, "level": "Moderate", "prio": "MEDIUM PRIORITY",
                    "lat": base_lat + 0.0112, "lng": base_lng + 0.0135, "box": [280, 480, 890, 530],
                    "factors": {"area_score": 45.0, "dimension_score": 90.0, "type_risk_score": 65.0, "confidence_score": 88.0, "persistence_score": 60.0}
                },
                {
                    "type": "Rutting", "conf": 0.84, "sev": 63.5, "level": "High", "prio": "HIGH PRIORITY",
                    "lat": base_lat + 0.0145, "lng": base_lng + 0.0178, "box": [500, 320, 580, 640],
                    "factors": {"area_score": 60.0, "dimension_score": 85.0, "type_risk_score": 85.0, "confidence_score": 84.0, "persistence_score": 50.0}
                }
            ]
        },
        {
            "id": "INSP-CBE-102",
            "title": "Trichy Road Sector 2 Aerial & Ground Audit",
            "road_name": "State Highway 17",
            "type": "image",
            "rhi": 84.0,
            "priority": "MEDIUM PRIORITY",
            "defects": [
                {
                    "type": "Longitudinal crack", "conf": 0.91, "sev": 52.0, "level": "Moderate", "prio": "MEDIUM PRIORITY",
                    "lat": base_lat - 0.0035, "lng": base_lng + 0.0062, "box": [620, 240, 680, 610],
                    "factors": {"area_score": 40.0, "dimension_score": 88.0, "type_risk_score": 60.0, "confidence_score": 91.0, "persistence_score": 50.0}
                },
                {
                    "type": "Patch damage", "conf": 0.85, "sev": 42.0, "level": "Moderate", "prio": "LOW PRIORITY",
                    "lat": base_lat - 0.0065, "lng": base_lng + 0.0110, "box": [340, 410, 560, 540],
                    "factors": {"area_score": 48.0, "dimension_score": 35.0, "type_risk_score": 50.0, "confidence_score": 85.0, "persistence_score": 40.0}
                }
            ]
        },
        {
            "id": "INSP-CBE-103",
            "title": "Mettupalayam Ghat Section Safety Scan",
            "road_name": "NH 181 (Ooty Ghat Road)",
            "type": "video",
            "rhi": 51.0,
            "priority": "URGENT",
            "defects": [
                {
                    "type": "Pothole", "conf": 0.96, "sev": 89.0, "level": "Critical", "prio": "URGENT",
                    "lat": base_lat + 0.0210, "lng": base_lng - 0.0080, "box": [380, 390, 590, 560],
                    "factors": {"area_score": 88.0, "dimension_score": 45.0, "type_risk_score": 95.0, "confidence_score": 96.0, "persistence_score": 95.0}
                },
                {
                    "type": "Edge crack", "conf": 0.86, "sev": 71.5, "level": "High", "prio": "HIGH PRIORITY",
                    "lat": base_lat + 0.0245, "lng": base_lng - 0.0120, "box": [80, 350, 220, 680],
                    "factors": {"area_score": 65.0, "dimension_score": 80.0, "type_risk_score": 70.0, "confidence_score": 86.0, "persistence_score": 60.0}
                },
                {
                    "type": "Manhole/road-surface defect", "conf": 0.93, "sev": 78.0, "level": "High", "prio": "HIGH PRIORITY",
                    "lat": base_lat + 0.0280, "lng": base_lng - 0.0150, "box": [640, 420, 810, 590],
                    "factors": {"area_score": 72.0, "dimension_score": 40.0, "type_risk_score": 80.0, "confidence_score": 93.0, "persistence_score": 80.0}
                }
            ]
        }
    ]

    for s in surveys:
        insp = Inspection(
            id=s["id"],
            title=s["title"],
            road_name=s["road_name"],
            inspection_type=s["type"],
            media_path=None,
            total_defects=len(s["defects"]),
            pothole_count=sum(1 for d in s["defects"] if "pothole" in d["type"].lower()),
            crack_count=sum(1 for d in s["defects"] if "crack" in d["type"].lower()),
            other_count=sum(1 for d in s["defects"] if "pothole" not in d["type"].lower() and "crack" not in d["type"].lower()),
            avg_severity=round(sum(d["sev"] for d in s["defects"]) / len(s["defects"]), 1),
            max_severity=max(d["sev"] for d in s["defects"]),
            road_health_index=s["rhi"],
            priority_level=s["priority"],
            status="completed",
            start_latitude=s["defects"][0]["lat"],
            start_longitude=s["defects"][0]["lng"],
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 14))
        )
        db.add(insp)
        db.flush()

        for d in s["defects"]:
            evt = DamageEvent(
                id=f"EVT-{d['type'][:3].upper()}-{uuid.uuid4().hex[:6]}",
                inspection_id=insp.id,
                damage_type=d["type"],
                confidence=d["conf"],
                severity_score=d["sev"],
                severity_level=d["level"],
                priority=d["prio"],
                latitude=d["lat"],
                longitude=d["lng"],
                timestamp=insp.created_at,
                bbox=d["box"],
                mask=[
                    [d["box"][0], d["box"][1]],
                    [d["box"][2], d["box"][1] + 10],
                    [d["box"][2] - 10, d["box"][3]],
                    [d["box"][0] + 5, d["box"][3]]
                ],
                factors=d["factors"],
                status="confirmed"
            )
            db.add(evt)

    db.commit()
    db.close()
    print("[SeedData] Successfully generated sample imagery and seeded database.")

if __name__ == "__main__":
    generate_sample_road_images()
    seed_database()
