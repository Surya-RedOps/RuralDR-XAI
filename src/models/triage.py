"""
Referable Diabetic Retinopathy (RDR) Triage Engine
Evaluates clinical referral pathways based on ICDR grade and confidence.
"""

from typing import Tuple, Optional
from ..core.contracts import DRGrade, ReviewPriority, SeverityPrediction, LesionInventory


def evaluate_triage_decision(
    prediction: SeverityPrediction,
    lesions: Optional[LesionInventory] = None,
    concordance_status: Optional[str] = None,
) -> Tuple[str, ReviewPriority]:
    """
    Evaluates clinical referral triage and assigns review urgency priority.
    """
    grade = prediction.predicted_grade
    conf = prediction.calibrated_confidence

    # 1. Urgent Referral: PDR (Grade 4) OR Severe NPDR (Grade 3) OR Hard Exudates Threatening Fovea
    if grade == DRGrade.PDR:
        return "URGENT REFERRAL: Proliferative Diabetic Retinopathy detected (High neovascular risk).", ReviewPriority.URGENT
    if grade == DRGrade.SEVERE_NPDR:
        return "URGENT REFERRAL: Severe NPDR (4-2-1 clinical criteria reached). Specialist review within 2 weeks.", ReviewPriority.URGENT
    if lesions is not None and lesions.foveal_involvement_threat:
        return "URGENT REFERRAL: Clinically Significant Macular Edema risk (Hard exudates near fovea).", ReviewPriority.URGENT

    # 2. Routine Referral: Moderate NPDR (Grade 2)
    if grade == DRGrade.MODERATE_NPDR:
        if conf < 0.70 or concordance_status == "REVIEW_REQUIRED":
            return "REFERRAL NEEDED (PRIORITY REVIEW): Moderate NPDR with elevated uncertainty.", ReviewPriority.HIGH
        return "ROUTINE REFERRAL: Moderate NPDR detected. District clinic appointment advised.", ReviewPriority.ELEVATED

    # 3. Non-Referable: Mild NPDR (Grade 1) or No DR (Grade 0)
    if grade == DRGrade.MILD_NPDR:
        return "NON-REFERABLE: Mild NPDR (Microaneurysms only). Re-screening in 6–12 months.", ReviewPriority.ROUTINE

    # Grade 0 No DR
    return "NON-REFERABLE: No signs of Diabetic Retinopathy detected. Annual routine screening.", ReviewPriority.ROUTINE
