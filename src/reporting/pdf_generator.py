"""
Automated Clinical Screening PDF Report Generator
Produces a high-density, professional ophthalmology screening summary.
"""

from typing import Optional
from pathlib import Path
import os
import cv2
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from ..core.contracts import ScreeningResult


def generate_clinical_pdf_report(
    result: ScreeningResult,
    annotated_image_np: np.ndarray,
    output_pdf_path: Path,
) -> Path:
    """
    Generates a structured clinical PDF report from real ScreeningResult data.
    """
    output_pdf_path = Path(output_pdf_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # Save temporary annotated image for PDF embedding
    temp_img_path = output_pdf_path.parent / f"temp_{result.case_id}.jpg"
    bgr = cv2.cvtColor(annotated_image_np, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(temp_img_path), bgr)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
    )
    section_heading = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2D3748"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#718096"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("RuralDR-XAI: Diabetic Retinopathy Screening Report", title_style))
    story.append(Paragraph("Smart India Hackathon 2026 — Explainable Retinal Screening Decision Support", subtitle_style))
    story.append(Spacer(1, 10))

    # 2. Case Metadata Table
    meta_data = [
        [
            Paragraph(f"<b>Case Identifier:</b> {result.case_id}", body_style),
            Paragraph(f"<b>Date/Time:</b> {result.timestamp}", body_style),
        ],
        [
            Paragraph(f"<b>Image Quality:</b> {result.quality.status.value} (Score: {result.quality.quality_score:.2f})", body_style),
            Paragraph(f"<b>Review Priority:</b> <b>{result.review_priority.value}</b>", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. Diagnostic Prediction & Triage
    story.append(Paragraph("1. Automated AI Triage & Disease Severity", section_heading))
    if result.prediction is not None:
        pred_data = [
            [
                Paragraph("<b>Predicted ICDR Grade:</b>", body_style),
                Paragraph(f"<b>{result.prediction.grade_name}</b>", body_style),
            ],
            [
                Paragraph("<b>Referable DR Status:</b>", body_style),
                Paragraph(
                    "<font color='red'><b>REFERABLE (Level 2+)</b></font>"
                    if result.prediction.is_referable
                    else "<font color='green'><b>NON-REFERABLE (Level 0/1)</b></font>",
                    body_style,
                ),
            ],
            [
                Paragraph("<b>Calibrated Confidence:</b>", body_style),
                Paragraph(f"{result.prediction.calibrated_confidence * 100:.1f}% (Temperature scaled, T={result.prediction.temperature_scaling_factor:.2f})", body_style),
            ],
            [
                Paragraph("<b>Clinical Triage Action:</b>", body_style),
                Paragraph(f"<b>{result.triage_decision}</b>", body_style),
            ],
        ]
    else:
        pred_data = [
            [Paragraph("<b>Status:</b>", body_style), Paragraph(result.triage_decision, body_style)]
        ]

    pred_table = Table(pred_data, colWidths=[160, 380])
    pred_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7FAFC")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    story.append(pred_table)
    story.append(Spacer(1, 8))

    # 4. Retinal Image Embedding & Lesion Evidence
    story.append(Paragraph("2. Annotated Retinal Findings & Evidence Overlays", section_heading))

    lesion_text = (
        f"• <b>Microaneurysms:</b> {result.lesions.microaneurysms_count} detected (Red dots)<br/>"
        f"• <b>Hard Exudates:</b> {result.lesions.hard_exudates_area_pct:.2f}% retinal surface (Yellow contours)<br/>"
        f"• <b>Soft Exudates (Cotton Wool):</b> {'Detected' if result.lesions.soft_exudates_detected else 'None'} (Cyan)<br/>"
        f"• <b>Hemorrhages:</b> {result.lesions.hemorrhages_count} lesions (Magenta contours)<br/>"
        f"• <b>Macular / Foveal Threat:</b> {'<font color=red><b>WARNING: Exudates within 1 DD of Fovea</b></font>' if result.lesions.foveal_involvement_threat else 'Safe (>1 DD clearance)'}<br/>"
        f"• <b>Vessel Density:</b> {result.anatomy.vessel_density * 100:.1f}% of retinal field"
    )

    if result.evidence_consistency is not None:
        consistency_text = (
            f"<b>Evidence Consistency:</b> {result.evidence_consistency.status.value}<br/>"
            f"<b>Concordance Index:</b> {result.evidence_consistency.concordance_index:.2f}<br/>"
            f"<b>Pointing Game Hit:</b> {'YES' if result.evidence_consistency.pointing_game_hit else 'NO'}"
        )
    else:
        consistency_text = "Consistency Engine: Awaiting deep model output."

    img_element = RLImage(str(temp_img_path), width=3.2 * inch, height=3.2 * inch)

    findings_content = [
        Paragraph(lesion_text, body_style),
        Spacer(1, 6),
        Paragraph(consistency_text, body_style),
    ]

    img_and_findings = [
        [img_element, findings_content]
    ]
    img_table = Table(img_and_findings, colWidths=[240, 300])
    img_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    story.append(img_table)
    story.append(Spacer(1, 8))

    # 5. Recapture advice if quality warning
    if result.quality.recapture_advice:
        story.append(Paragraph("3. Image Quality Notes & Guidance", section_heading))
        advice_str = "<br/>".join([f"• {a}" for a in result.quality.recapture_advice])
        story.append(Paragraph(advice_str, body_style))
        story.append(Spacer(1, 6))

    # 6. Ophthalmologist Sign-Off Box
    sign_off_data = [
        [
            Paragraph("<b>Ophthalmologist Review & Sign-Off:</b>", body_style),
            Paragraph("<b>Clinical Action:</b> [ ] Approved  [ ] Grade Modified  [ ] Re-scan", body_style),
        ],
        [
            Paragraph("Doctor Name / Registration: _______________________", body_style),
            Paragraph("Signature / Date: _______________________", body_style),
        ],
    ]
    sign_table = Table(sign_off_data, colWidths=[270, 270])
    sign_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#718096")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(KeepTogether([sign_table, Spacer(1, 6), Paragraph(result.disclaimer, disclaimer_style)]))

    # Build PDF
    doc.build(story)

    # Clean up temp image
    if temp_img_path.is_file():
        try:
            os.remove(str(temp_img_path))
        except OSError:
            pass

    return output_pdf_path
