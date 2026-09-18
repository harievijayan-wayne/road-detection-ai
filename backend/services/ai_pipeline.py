"""
AI Pipeline Orchestrator for Road Damage Detection.
Integrates image quality assessment, adaptive lighting normalization,
YOLO/CV segmentation, ByteTrack tracking, mathematical severity scoring,
and rich visual annotation (masks + boxes + priority tags).
"""

import os
import cv2
import time
import uuid
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from ai.preprocessing.lighting_robustness import LightingRobustnessEngine
from ai.inference.detector import RoadDamageDetector
from ai.tracking.tracker import RoadDamageTracker
from ai.severity.severity_engine import SeverityEngine
from backend.app.config import settings

# Visual color mapping per damage class (BGR format for OpenCV)
CLASS_COLORS = {
    "Pothole": (0, 0, 230),                      # Bright Crimson
    "Alligator crack": (0, 69, 255),             # Deep Orange
    "Rutting": (0, 140, 255),                    # Amber
    "Manhole/road-surface defect": (34, 180, 238),# Golden Yellow
    "Surface deformation": (205, 50, 150),       # Purple / Magenta
    "Edge crack": (200, 100, 50),                # Cyan-Blue
    "Transverse crack": (50, 205, 50),           # Lime Green
    "Longitudinal crack": (0, 215, 255),         # Yellow
    "Other road damage": (180, 180, 180),        # Gray
    "Patch damage": (220, 160, 20)               # Teal
}

class PipelineOrchestrator:
    def __init__(self):
        self.lighting_engine = LightingRobustnessEngine()
        self.detector = RoadDamageDetector(
            conf_threshold=settings.CONF_THRESHOLD,
            iou_threshold=settings.IOU_THRESHOLD,
            device=settings.DEVICE
        )
        self.severity_engine = SeverityEngine()

    def process_image(self,
                      image_path: str,
                      inspection_id: Optional[str] = None,
                      latitude: Optional[float] = None,
                      longitude: Optional[float] = None) -> Dict[str, Any]:
        """
        Full pipeline for a single static road image.
        """
        start_time = time.time()
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image from {image_path}")

        # 1. Quality & Lighting Preprocessing
        enhanced_image, lighting_report = self.lighting_engine.adaptive_normalize(image)

        # 2. Damage Detection & Segmentation
        detections = self.detector.detect(enhanced_image, run_severity=True)

        # 3. Compute priority and Road Health Index
        total_defects = len(detections)
        for det in detections:
            p_result = self.severity_engine.calculate_priority(
                severity_score=det["severity_score"],
                damage_type=det["damage_type"],
                nearby_defect_count=max(0, total_defects - 1)
            )
            det["priority"] = p_result["priority_level"]
            det["priority_details"] = p_result

        rhi_report = self.severity_engine.compute_road_health_index(detections)

        # 4. Draw Rich Visual Annotations
        annotated = self.annotate_image(image, detections)
        
        # Save annotated image
        insp_id = inspection_id or f"INSP-{uuid.uuid4().hex[:8]}"
        out_filename = f"annotated_{insp_id}.jpg"
        out_path = os.path.join(settings.UPLOAD_DIR, out_filename)
        cv2.imwrite(out_path, annotated)

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        priority_rec = "LOW PRIORITY"
        if any(d["priority"] == "URGENT" for d in detections):
            priority_rec = "URGENT"
        elif any(d["priority"] == "HIGH PRIORITY" for d in detections):
            priority_rec = "HIGH PRIORITY"
        elif any(d["priority"] == "MEDIUM PRIORITY" for d in detections):
            priority_rec = "MEDIUM PRIORITY"

        return {
            "inspection_id": insp_id,
            "processing_time_ms": elapsed_ms,
            "total_damages": len(detections),
            "road_health_index": rhi_report["road_health_index"],
            "road_health_rating": rhi_report["rating"],
            "priority_recommendation": priority_rec,
            "lighting_assessment": lighting_report,
            "detections": detections,
            "annotated_image_path": out_path,
            "annotated_image_url": f"/api/uploads/{out_filename}",
            "latitude": latitude,
            "longitude": longitude
        }

    def process_video(self,
                      video_path: str,
                      inspection_id: Optional[str] = None,
                      frame_skip: int = 2) -> Dict[str, Any]:
        """
        Real-time tracking video pipeline with duplicate suppression.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video {video_path}")

        tracker = RoadDamageTracker(min_confirm_frames=2)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

        insp_id = inspection_id or f"VID-{uuid.uuid4().hex[:8]}"
        out_filename = f"annotated_{insp_id}.mp4"
        out_path = os.path.join(settings.UPLOAD_DIR, out_filename)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_path, fourcc, fps / frame_skip, (width, height))

        frame_idx = 0
        processed_frames = 0
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if frame_idx % frame_skip != 0:
                continue

            processed_frames += 1
            enhanced, _ = self.lighting_engine.adaptive_normalize(frame)
            raw_dets = self.detector.detect(enhanced, run_severity=True)

            # Update tracker & duplicate suppression
            tracked_dets = tracker.update(raw_dets, frame_idx=frame_idx)

            # Annotate frame
            annotated = self.annotate_image(frame, tracked_dets, show_tracking=True)
            out.write(annotated)

            if processed_frames >= 150: # Cap demo video processing to 150 sampled frames
                break

        cap.release()
        out.release()

        summary_events = tracker.get_summary_events()
        total_time = max(0.1, time.time() - start_time)
        avg_fps = round(processed_frames / total_time, 1)

        rhi_report = self.severity_engine.compute_road_health_index(summary_events)

        return {
            "inspection_id": insp_id,
            "total_frames_processed": processed_frames,
            "unique_damage_events": len(summary_events),
            "road_health_index": rhi_report["road_health_index"],
            "processing_fps": avg_fps,
            "summary_events": summary_events,
            "output_video_path": out_path,
            "output_video_url": f"/api/uploads/{out_filename}"
        }

    def annotate_image(self,
                       image: np.ndarray,
                       detections: List[Dict[str, Any]],
                       show_tracking: bool = False) -> np.ndarray:
        """
        Renders modern, semi-transparent segmentation masks, glowing bounding boxes,
        and HUD badges for each detected defect.
        """
        annotated = image.copy()
        overlay = image.copy()

        for det in detections:
            dt = det["damage_type"]
            conf = det.get("confidence", 0.8)
            sev = det.get("severity_score", 45.0)
            level = det.get("severity_level", "Moderate")
            color = CLASS_COLORS.get(dt, (0, 255, 255))
            bbox = [int(c) for c in det["bbox"]]
            x1, y1, x2, y2 = bbox

            # 1. Draw Segmentation Mask if available
            mask_pts = det.get("mask", None)
            if mask_pts and len(mask_pts) >= 3:
                pts = np.array(mask_pts, dtype=np.int32)
                cv2.fillPoly(overlay, [pts], color)
                cv2.polylines(annotated, [pts], True, color, 2, cv2.LINE_AA)

            # 2. Draw Sleek Rounded Bounding Box Corners
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
            corner_len = min(15, (x2 - x1) // 4, (y2 - y1) // 4)
            t = 3
            # Top-left
            cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), color, t)
            cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), color, t)
            # Top-right
            cv2.line(annotated, (x2, y1), (x2 - corner_len, y1), color, t)
            cv2.line(annotated, (x2, y1), (x2, y1 + corner_len), color, t)
            # Bottom-left
            cv2.line(annotated, (x1, y2), (x1 + corner_len, y2), color, t)
            cv2.line(annotated, (x1, y2), (x1, y2 - corner_len), color, t)
            # Bottom-right
            cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), color, t)
            cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), color, t)

            # 3. Label Badge
            track_str = f"#{det.get('track_id', 1)} " if show_tracking else ""
            label = f"{track_str}{dt} ({int(conf*100)}%) | Sev: {int(sev)} [{level}]"
            
            # Badge background
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.45
            thickness = 1
            (tw, th), baseline = cv2.getTextSize(label, font, scale, thickness)
            badge_y1 = max(0, y1 - th - 10)
            badge_y2 = y1
            cv2.rectangle(annotated, (x1, badge_y1), (x1 + tw + 10, badge_y2), (20, 20, 24), -1)
            cv2.rectangle(annotated, (x1, badge_y1), (x1 + tw + 10, badge_y2), color, 1)
            cv2.putText(annotated, label, (x1 + 5, y1 - 4), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

        # Blend mask overlay for translucent effect (alpha 0.35)
        cv2.addWeighted(overlay, 0.35, annotated, 0.65, 0, annotated)
        return annotated

orchestrator = PipelineOrchestrator()
