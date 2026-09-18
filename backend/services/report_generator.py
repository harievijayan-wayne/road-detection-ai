"""
Road Condition Report Generator.
Generates downloadable inspection reports in PDF, CSV, and JSON formats.
"""

import os
import csv
import json
import fitz  # PyMuPDF
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.config import settings

class ReportGenerator:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or settings.REPORTS_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_json_report(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        fname = filename or f"report_{data.get('inspection_id', 'general')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(self.output_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def generate_csv_report(self, inspection_summary: Dict[str, Any], damage_events: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        fname = filename or f"report_{inspection_summary.get('inspection_id', 'general')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(self.output_dir, fname)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Inspection Header Summary
            writer.writerow(["ROAD CONDITION SURVEY ASSESSMENT REPORT"])
            writer.writerow(["Generated At", datetime.now().isoformat()])
            writer.writerow(["Road Identifier", inspection_summary.get("road_id", "SH-17")])
            writer.writerow(["Road Health Index (RHI)", inspection_summary.get("road_health_index", "N/A")])
            writer.writerow(["Overall Maintenance Priority", inspection_summary.get("priority_recommendation", "N/A")])
            writer.writerow(["Total Defects Detected", len(damage_events)])
            writer.writerow([])

            # Detailed Defects Table
            writer.writerow([
                "Damage Event ID", "Class", "Confidence", "Severity Score",
                "Severity Level", "Priority", "Latitude", "Longitude", "Track ID"
            ])
            for evt in damage_events:
                writer.writerow([
                    evt.get("id") or evt.get("damage_event_id", "N/A"),
                    evt.get("damage_type", "Unknown"),
                    evt.get("confidence", 0.0),
                    evt.get("severity_score", 0.0),
                    evt.get("severity_level", "Moderate"),
                    evt.get("priority", "MEDIUM PRIORITY"),
                    evt.get("latitude", "N/A"),
                    evt.get("longitude", "N/A"),
                    evt.get("tracking_id", 1)
                ])
        return path

    def generate_pdf_report(self, inspection_summary: Dict[str, Any], damage_events: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Generates a professional executive PDF report using PyMuPDF (fitz).
        """
        fname = filename or f"report_{inspection_summary.get('inspection_id', 'general')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = os.path.join(self.output_dir, fname)

        doc = fitz.open()
        page = doc.new_page(width=595, height=842) # A4 size

        # Header block
        header_rect = fitz.Rect(30, 30, 565, 95)
        page.draw_rect(header_rect, color=(0.1, 0.2, 0.4), fill=(0.08, 0.12, 0.22))
        page.insert_text((45, 60), "ROADDAMAGE AI - INFRASTRUCTURE AUDIT", fontsize=16, color=(1, 1, 1), fontname="helv")
        page.insert_text((45, 80), f"Pavement Condition & Structural Priority Assessment | {datetime.now().strftime('%B %d, %Y')}", fontsize=10, color=(0.7, 0.8, 0.9), fontname="helv")

        # KPI Summary Cards
        y = 120
        page.insert_text((35, y), "EXECUTIVE SUMMARY", fontsize=12, color=(0.1, 0.15, 0.3), fontname="helv")
        y += 15

        road_id = inspection_summary.get("road_id", "SH-17 Sector 4")
        rhi = inspection_summary.get("road_health_index", 78.5)
        priority = inspection_summary.get("priority_recommendation", "MEDIUM PRIORITY")
        total = len(damage_events)
        potholes = sum(1 for d in damage_events if "pothole" in d.get("damage_type", "").lower())
        cracks = sum(1 for d in damage_events if "crack" in d.get("damage_type", "").lower())
        others = total - (potholes + cracks)

        summary_lines = [
            f"Road Segment: {road_id}",
            f"Road Health Index (RHI): {rhi} / 100",
            f"Recommended Maintenance Priority: {priority}",
            f"Total Damage Instances Detected: {total}",
            f"Breakdown: {potholes} Pothole(s), {cracks} Crack(s), {others} Surface Defect(s)",
            f"Audit Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        ]

        for line in summary_lines:
            page.insert_text((40, y), f"•  {line}", fontsize=10, color=(0.2, 0.2, 0.2), fontname="helv")
            y += 16

        # Defects Listing Table
        y += 20
        page.insert_text((35, y), "DETECTED ROAD DAMAGE INSTANCES", fontsize=12, color=(0.1, 0.15, 0.3), fontname="helv")
        y += 20

        # Table Header
        col_x = [35, 160, 220, 285, 360, 440]
        headers = ["Defect Type", "Confidence", "Severity", "Level", "Priority", "Status"]
        page.draw_rect(fitz.Rect(30, y - 12, 565, y + 6), fill=(0.92, 0.94, 0.97))
        for x, h in zip(col_x, headers):
            page.insert_text((x, y), h, fontsize=9, color=(0.1, 0.1, 0.1), fontname="helv")
        y += 18

        # Rows (limit to top 15 on first page)
        for i, evt in enumerate(damage_events[:15]):
            row_y = y
            dtype = evt.get("damage_type", "Defect")[:18]
            conf = f"{int(evt.get('confidence', 0.8) * 100)}%"
            sev = f"{evt.get('severity_score', 50)}"
            level = evt.get("severity_level", "Moderate")
            prio = evt.get("priority", "MEDIUM")
            status = evt.get("status", "Confirmed")

            # Alternate row background
            if i % 2 == 1:
                page.draw_rect(fitz.Rect(30, row_y - 10, 565, row_y + 6), fill=(0.97, 0.98, 0.99))

            page.insert_text((col_x[0], row_y), dtype, fontsize=8.5, color=(0.15, 0.15, 0.15), fontname="helv")
            page.insert_text((col_x[1], row_y), conf, fontsize=8.5, color=(0.2, 0.2, 0.2), fontname="helv")
            page.insert_text((col_x[2], row_y), sev, fontsize=8.5, color=(0.2, 0.2, 0.2), fontname="helv")
            page.insert_text((col_x[3], row_y), level, fontsize=8.5, color=(0.2, 0.2, 0.2), fontname="helv")
            page.insert_text((col_x[4], row_y), prio, fontsize=8.5, color=(0.8, 0.2, 0.1) if "URGENT" in prio or "HIGH" in prio else (0.2, 0.4, 0.8), fontname="helv")
            page.insert_text((col_x[5], row_y), status, fontsize=8.5, color=(0.3, 0.3, 0.3), fontname="helv")
            y += 18

        # Footer
        footer_text = "Notice: This automated report is generated by RoadDamageAI computer-vision telemetry. Professional civil engineering inspection recommended before major capital allocations."
        page.insert_text((35, 810), footer_text, fontsize=7.5, color=(0.5, 0.5, 0.5), fontname="helv")

        doc.save(path)
        doc.close()
        return path

report_generator = ReportGenerator()
