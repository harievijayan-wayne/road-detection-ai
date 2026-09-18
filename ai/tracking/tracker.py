"""
Object Tracking and Duplicate Detection Engine for Road Damage Video Pipeline.
Prevents multiple counts for the same physical pothole or crack as the inspection vehicle drives past.
Generates unique damage_event_ids and aggregates temporal telemetry.
"""

import uuid
import time
import math
from typing import List, Dict, Any, Optional

def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    """Computes Intersection-over-Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interWidth = max(0.0, xB - xA)
    interHeight = max(0.0, yB - yA)
    interArea = interWidth * interHeight

    boxAArea = max(1.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(1.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return max(0.0, min(1.0, iou))

def compute_centroid(box: List[float]) -> (float, float):
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)

class TrackedDamageObject:
    def __init__(self,
                 track_id: int,
                 damage_type: str,
                 initial_bbox: List[float],
                 initial_confidence: float,
                 frame_idx: int,
                 initial_severity: float,
                 mask_points: Optional[List[List[float]]] = None,
                 gps_coord: Optional[Dict[str, float]] = None):
        self.track_id = track_id
        self.damage_event_id = f"EVT-{damage_type[:3].upper()}-{uuid.uuid4().hex[:8]}"
        self.damage_type = damage_type
        self.bbox = initial_bbox
        self.confidence = initial_confidence
        self.max_confidence = initial_confidence
        self.severity_score = initial_severity
        self.peak_severity = initial_severity
        self.mask_points = mask_points
        self.first_seen_frame = frame_idx
        self.last_seen_frame = frame_idx
        self.frame_count = 1
        self.time_first_seen = time.time()
        self.time_last_seen = self.time_first_seen
        self.gps_coord = gps_coord
        self.is_confirmed = False # True once detected in >= min_confirm_frames
        self.is_active = True
        self.missed_frames = 0

    def update(self,
               bbox: List[float],
               confidence: float,
               frame_idx: int,
               severity: float,
               mask_points: Optional[List[List[float]]] = None,
               gps_coord: Optional[Dict[str, float]] = None):
        self.bbox = bbox
        self.confidence = confidence
        self.max_confidence = max(self.max_confidence, confidence)
        self.severity_score = severity
        self.peak_severity = max(self.peak_severity, severity)
        if mask_points:
            self.mask_points = mask_points
        if gps_coord:
            self.gps_coord = gps_coord
        self.last_seen_frame = frame_idx
        self.time_last_seen = time.time()
        self.frame_count += 1
        self.missed_frames = 0
        if self.frame_count >= 2:
            self.is_confirmed = True

class RoadDamageTracker:
    def __init__(self,
                 iou_threshold: float = 0.35,
                 max_distance_pixels: float = 120.0,
                 max_missed_frames: int = 5,
                 min_confirm_frames: int = 2):
        self.iou_threshold = iou_threshold
        self.max_distance_pixels = max_distance_pixels
        self.max_missed_frames = max_missed_frames
        self.min_confirm_frames = min_confirm_frames
        self.next_track_id = 1
        self.active_tracks: Dict[int, TrackedDamageObject] = {}
        self.completed_events: List[Dict[str, Any]] = []

    def update(self,
               detections: List[Dict[str, Any]],
               frame_idx: int,
               current_gps: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Associates current frame detections with active tracks.
        Returns annotated detections containing track_id, damage_event_id, and persistence.
        """
        matched_track_ids = set()
        unmatched_detections = []
        annotated_detections = []

        # Attempt to match detections to active tracks
        for det in detections:
            bbox = det["bbox"]
            damage_type = det["damage_type"]
            conf = det.get("confidence", 0.5)
            sev = det.get("severity_score", 40.0)
            mask = det.get("mask", None)
            c_x, c_y = compute_centroid(bbox)

            best_match_id = None
            best_iou = 0.0

            for track_id, track in self.active_tracks.items():
                if track_id in matched_track_ids:
                    continue
                # Same or compatible class
                if track.damage_type != damage_type:
                    continue

                iou = compute_iou(bbox, track.bbox)
                t_cx, t_cy = compute_centroid(track.bbox)
                dist = math.hypot(c_x - t_cx, c_y - t_cy)

                # Matching condition: either high IoU or close centroid proximity
                if iou >= self.iou_threshold or (iou > 0.15 and dist < self.max_distance_pixels):
                    if iou > best_iou:
                        best_iou = iou
                        best_match_id = track_id

            if best_match_id is not None:
                matched_track_ids.add(best_match_id)
                track = self.active_tracks[best_match_id]
                track.update(bbox, conf, frame_idx, sev, mask, current_gps)
                
                det_copy = dict(det)
                det_copy["track_id"] = track.track_id
                det_copy["damage_event_id"] = track.damage_event_id
                det_copy["persistence_frames"] = track.frame_count
                det_copy["is_confirmed"] = track.is_confirmed
                annotated_detections.append(det_copy)
            else:
                unmatched_detections.append(det)

        # Create new tracks for unmatched detections
        for det in unmatched_detections:
            new_id = self.next_track_id
            self.next_track_id += 1
            track = TrackedDamageObject(
                track_id=new_id,
                damage_type=det["damage_type"],
                initial_bbox=det["bbox"],
                initial_confidence=det.get("confidence", 0.5),
                frame_idx=frame_idx,
                initial_severity=det.get("severity_score", 40.0),
                mask_points=det.get("mask", None),
                gps_coord=current_gps
            )
            self.active_tracks[new_id] = track

            det_copy = dict(det)
            det_copy["track_id"] = new_id
            det_copy["damage_event_id"] = track.damage_event_id
            det_copy["persistence_frames"] = 1
            det_copy["is_confirmed"] = (self.min_confirm_frames <= 1)
            annotated_detections.append(det_copy)

        # Age unmatched active tracks
        unmatched_tracks = set(self.active_tracks.keys()) - matched_track_ids
        for track_id in unmatched_tracks:
            track = self.active_tracks[track_id]
            track.missed_frames += 1
            if track.missed_frames > self.max_missed_frames:
                # Archive finished event
                if track.frame_count >= self.min_confirm_frames:
                    self.completed_events.append({
                        "damage_event_id": track.damage_event_id,
                        "track_id": track.track_id,
                        "damage_type": track.damage_type,
                        "first_seen_frame": track.first_seen_frame,
                        "last_seen_frame": track.last_seen_frame,
                        "total_frames": track.frame_count,
                        "peak_confidence": round(track.max_confidence, 2),
                        "peak_severity": round(track.peak_severity, 1),
                        "gps_coord": track.gps_coord,
                        "final_bbox": track.bbox
                    })
                del self.active_tracks[track_id]

        return annotated_detections

    def get_summary_events(self) -> List[Dict[str, Any]]:
        """Returns all confirmed unique damage events (deduplicated)."""
        all_events = list(self.completed_events)
        for track in self.active_tracks.values():
            if track.frame_count >= self.min_confirm_frames or len(all_events) == 0:
                all_events.append({
                    "damage_event_id": track.damage_event_id,
                    "track_id": track.track_id,
                    "damage_type": track.damage_type,
                    "first_seen_frame": track.first_seen_frame,
                    "last_seen_frame": track.last_seen_frame,
                    "total_frames": track.frame_count,
                    "peak_confidence": round(track.max_confidence, 2),
                    "peak_severity": round(track.peak_severity, 1),
                    "gps_coord": track.gps_coord,
                    "final_bbox": track.bbox
                })
        return all_events
