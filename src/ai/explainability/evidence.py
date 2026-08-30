"""
Retina AI: Evidence Summary Generator
Produces structured, medically safe evidence summaries for clinical review.

IMPORTANT: This module uses careful clinical terminology:
- "AI screening result" NOT "diagnosis"
- "AI-detected feature" NOT "confirmed lesion"
- "Model attention region" NOT "clinical proof"
- "Requires clinical confirmation" for all outputs
"""

from typing import Dict, Any, Optional, List
from ...core.contracts import (
    ExplainableScreeningResult,
    GradCAMResult,
    LesionDetectionResult,
    DR_GRADE_NAMES,
    DRGrade,
)


SEVERITY_DESCRIPTIONS = {
    0: "No signs of diabetic retinopathy detected by the AI model",
    1: "Mild non-proliferative changes detected",
    2: "Moderate non-proliferative changes detected — referral may be warranted",
    3: "Severe non-proliferative changes detected — referral recommended",
    4: "Proliferative changes detected — urgent referral recommended",
}


def generate_evidence_report(
    result: ExplainableScreeningResult,
) -> Dict[str, Any]:
    """
    Generates a structured evidence report suitable for the doctor dashboard.

    Returns a dict with sections:
    - screening_result: DR grade and confidence
    - model_attention: Grad-CAM availability and quality
    - detected_features: Per-lesion detection results
    - clinical_guidance: Medically safe guidance statements
    - limitations: Known model limitations
    """
    report: Dict[str, Any] = {
        "case_id": result.case_id,
        "timestamp": result.timestamp,
    }

    # Section 1: Screening Result
    report["screening_result"] = {
        "ai_grade": result.dr_grade,
        "severity_description": SEVERITY_DESCRIPTIONS.get(result.dr_grade or 0, "Unknown"),
        "grade_name": result.severity,
        "classification_confidence": result.classification_confidence,
        "is_referable": result.is_referable,
        "class_probabilities": result.class_probabilities,
        "note": "AI screening result — not a definitive clinical diagnosis",
    }

    # Section 2: Model Attention
    gc = result.gradcam_result
    report["model_attention"] = {
        "gradcam_available": gc is not None and gc.is_valid if gc else False,
        "overlay_path": gc.overlay_path if gc else None,
        "attention_class": gc.target_class if gc else None,
        "activation_coverage": gc.activation_coverage if gc else 0.0,
        "quality_flags": gc.quality_flags if gc else [],
        "note": (
            "Grad-CAM highlights regions that influenced the model's prediction. "
            "It does NOT identify specific lesions or provide clinical proof."
        ),
    }

    # Section 3: Detected Features
    features = []
    if result.segmentation_result:
        for lesion in result.segmentation_result.lesions:
            features.append({
                "type": lesion.lesion_type.replace("_", " ").title(),
                "detected": lesion.detected,
                "region_count": lesion.num_connected_components,
                "relative_area_pct": lesion.relative_area_pct,
                "segmentation_confidence": lesion.mean_confidence,
                "mask_path": lesion.mask_path,
            })

    report["detected_features"] = {
        "features": features,
        "note": "AI-detected retinal features associated with the model's analysis",
    }

    # Section 4: Clinical Guidance
    guidance = []
    dr_grade = result.dr_grade or 0
    if dr_grade >= 3:
        guidance.append("URGENT: AI suggests severe or proliferative changes — priority clinical review recommended")
    elif dr_grade == 2:
        guidance.append("AI suggests moderate changes — clinical review within standard referral timeline")
    elif dr_grade == 1:
        guidance.append("AI suggests mild changes — routine follow-up may be appropriate")
    else:
        guidance.append("No DR features detected by AI — routine screening interval")

    if result.segmentation_result:
        detected = [l for l in result.segmentation_result.lesions if l.detected]
        if detected and dr_grade == 0:
            guidance.append(
                "NOTE: Lesion segmentation detected features but classifier assigned Grade 0. "
                "This discordance may warrant clinical review."
            )

    report["clinical_guidance"] = {
        "recommendations": guidance,
        "note": "The doctor remains responsible for clinical interpretation and treatment decisions",
    }

    # Section 5: Limitations
    report["limitations"] = [
        "This is an AI-assisted screening tool, not a diagnostic device",
        "Grad-CAM provides model attention visualization, not clinical proof",
        "Lesion segmentation may produce false positives or miss subtle lesions",
        "Results should be interpreted by a qualified ophthalmologist",
        f"Image was processed at {result.segmentation_result.input_resolution if result.segmentation_result else 'N/A'} resolution",
        f"DR classifier input: 224×224 with CLAHE preprocessing",
    ]

    # Processing times
    report["processing_times"] = {
        "quality_gate_ms": result.quality_gate_time_ms,
        "classification_ms": result.classification_time_ms,
        "gradcam_ms": result.gradcam_time_ms,
        "segmentation_ms": result.segmentation_time_ms,
        "total_pipeline_ms": result.total_pipeline_time_ms,
    }

    return report
