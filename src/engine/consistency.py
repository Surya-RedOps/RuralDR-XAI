"""
Evidence Consistency Engine (ECEngine)
Quantifies alignment between deep classifier predictions, Grad-CAM attention,
anatomical landmarks, and detected lesion pathology.
"""

from typing import Tuple, List, Dict
import cv2
import numpy as np

from ..core.contracts import (
    DRGrade,
    ConsistencyStatus,
    ReviewPriority,
    EvidenceConsistency,
    SeverityPrediction,
    LesionInventory,
    RetinalAnatomy,
)


class EvidenceConsistencyEngine:
    """
    Evaluates multi-modal evidence concordance to prevent black-box false assurances.
    """

    def __init__(self, min_concordance_threshold: float = 0.25):
        self.min_concordance_threshold = min_concordance_threshold

    def evaluate(
        self,
        prediction: SeverityPrediction,
        lesion_inventory: LesionInventory,
        lesion_masks: Dict[str, np.ndarray],
        cam_mask: np.ndarray,
        cam_heatmap: np.ndarray,
        anatomy: RetinalAnatomy,
    ) -> EvidenceConsistency:
        """
        Computes the clinical concordance index and checks rule consistency.
        """
        grade = prediction.predicted_grade
        conf = prediction.calibrated_confidence
        combined_lesions = lesion_masks.get("combined_lesions", np.zeros_like(cam_mask))

        discordance_reasons: List[str] = []
        pointing_hit = False

        # 1. Pointing Game & Spatial Concordance Index
        lesion_pixels = np.sum(combined_lesions > 0)
        cam_pixels = np.sum(cam_mask > 0)

        if lesion_pixels > 0 and cam_pixels > 0:
            intersection = np.sum((combined_lesions > 0) & (cam_mask > 0))
            concordance_index = float(intersection / (lesion_pixels + 1e-6))
            pointing_hit = intersection > 0
        elif lesion_pixels == 0 and grade == DRGrade.NO_DR:
            concordance_index = 1.0
            pointing_hit = True
        else:
            concordance_index = 0.0
            pointing_hit = False

        # 2. Check Optic Disc Confounding Artifact
        # If Grad-CAM puts >60% of its high energy on the optic disc for DR prediction, it is likely confounding
        if anatomy.optic_disc_center is not None and anatomy.optic_disc_radius is not None and cam_pixels > 0:
            cx, cy = anatomy.optic_disc_center
            r = int(anatomy.optic_disc_radius)
            od_zone = np.zeros_like(cam_mask)
            cv2.circle(od_zone, (cx, cy), r, 255, -1)
            od_cam_overlap = np.sum((cam_mask > 0) & (od_zone > 0))
            od_ratio = float(od_cam_overlap / cam_pixels)
            if od_ratio > 0.60 and grade >= DRGrade.MODERATE_NPDR:
                discordance_reasons.append(
                    f"Model attention concentrated predominantly on Optic Disc ({od_ratio*100:.1f}%), indicating possible feature artifact."
                )

        # 3. Clinical Rule Verifications
        clinical_rule_satisfied = True

        # Rule A: Grade 0 (No DR) but significant lesions detected
        if grade == DRGrade.NO_DR:
            if lesion_inventory.microaneurysms_count > 5 or lesion_inventory.hard_exudates_area_pct > 0.05:
                clinical_rule_satisfied = False
                discordance_reasons.append(
                    f"Model predicted No DR (Grade 0), but {lesion_inventory.microaneurysms_count} MAs and {lesion_inventory.hard_exudates_area_pct}% exudates detected."
                )

        # Rule B: Grade 2+ (Referable DR) but zero lesions detected
        if grade >= DRGrade.MODERATE_NPDR:
            if lesion_inventory.total_lesion_area_pct < 0.01 and lesion_inventory.microaneurysms_count == 0:
                clinical_rule_satisfied = False
                discordance_reasons.append(
                    f"Model predicted {grade.name} (Grade {grade.value}), but morphological lesion detector found no significant lesions."
                )

        # Rule C: Low calibrated confidence (< 65%)
        if conf < 0.65:
            discordance_reasons.append(f"Calibrated confidence is borderline ({conf*100:.1f}%).")

        # 4. Synthesize Final Consistency Status and Human Review Priority
        if not clinical_rule_satisfied or len(discordance_reasons) >= 2 or (grade >= DRGrade.MODERATE_NPDR and concordance_index < 0.05 and conf < 0.80):
            status = ConsistencyStatus.REVIEW_REQUIRED
            priority = ReviewPriority.URGENT if grade >= DRGrade.MODERATE_NPDR else ReviewPriority.HIGH
        elif len(discordance_reasons) == 1 or (concordance_index < self.min_concordance_threshold and grade >= DRGrade.MILD_NPDR):
            status = ConsistencyStatus.PARTIALLY_SUPPORTED
            priority = ReviewPriority.HIGH if grade >= DRGrade.MODERATE_NPDR else ReviewPriority.ELEVATED
        else:
            status = ConsistencyStatus.SUPPORTED
            priority = ReviewPriority.ROUTINE if grade <= DRGrade.MILD_NPDR else ReviewPriority.ELEVATED

        return EvidenceConsistency(
            status=status,
            concordance_index=round(concordance_index, 3),
            pointing_game_hit=pointing_hit,
            clinical_rule_satisfied=clinical_rule_satisfied,
            discordance_reasons=discordance_reasons,
            human_review_priority=priority,
        )
