"""
Lesion Evidence Extraction Orchestrator
Extracts MAs, Hard Exudates, Soft Exudates, and Hemorrhages.
Computes quadrant distributions and foveal involvement hazard.
"""

from typing import Tuple, Dict, Any, Optional
import cv2
import numpy as np

from ..core.contracts import LesionInventory, RetinalAnatomy
from .microaneurysms import detect_microaneurysms
from .exudates import segment_exudates
from .hemorrhages import segment_hemorrhages


class LesionEvidenceDetector:
    """
    Comprehensive Retinal Lesion Detector.
    Extracts morphologically grounded lesion evidence.
    """

    def __init__(self):
        pass

    def detect(
        self,
        image_rgb: np.ndarray,
        anatomy: RetinalAnatomy,
        vessel_mask: Optional[np.ndarray] = None,
        mask: Optional[np.ndarray] = None,
    ) -> Tuple[LesionInventory, Dict[str, np.ndarray]]:
        """
        Executes all lesion detectors and returns structured inventory + visual mask layers.
        """
        h, w = image_rgb.shape[:2]

        # 1. Create Optic Disc mask from anatomy if available
        od_mask = np.zeros((h, w), dtype=np.uint8)
        if anatomy.optic_disc_center is not None and anatomy.optic_disc_radius is not None:
            cx, cy = anatomy.optic_disc_center
            r = int(anatomy.optic_disc_radius)
            cv2.circle(od_mask, (cx, cy), r, 255, -1)

        # 2. Run Detectors
        ma_mask, ma_candidates = detect_microaneurysms(image_rgb, vessel_mask, od_mask, mask)
        hard_ex_mask, soft_ex_mask, hard_ex_pct = segment_exudates(image_rgb, od_mask, mask)
        he_mask, he_count, he_pct = segment_hemorrhages(image_rgb, vessel_mask, od_mask, mask)

        # 3. Combined lesion mask
        combined_lesion_mask = cv2.bitwise_or(ma_mask, hard_ex_mask)
        combined_lesion_mask = cv2.bitwise_or(combined_lesion_mask, soft_ex_mask)
        combined_lesion_mask = cv2.bitwise_or(combined_lesion_mask, he_mask)

        total_retina_pixels = np.sum(mask > 0) if mask is not None else (h * w)
        total_lesion_pct = float(np.sum(combined_lesion_mask > 0) / total_retina_pixels * 100.0) if total_retina_pixels > 0 else 0.0

        # 4. Check Foveal Hazard (Hard Exudates within 1.0 Disc Diameter of Fovea)
        foveal_hazard = False
        if anatomy.fovea_center is not None and anatomy.optic_disc_radius is not None:
            fx, fy = anatomy.fovea_center
            one_dd = int(anatomy.optic_disc_radius * 2.0)
            fovea_zone = np.zeros((h, w), dtype=np.uint8)
            cv2.circle(fovea_zone, (fx, fy), one_dd, 255, -1)
            ex_in_fovea = cv2.bitwise_and(hard_ex_mask, hard_ex_mask, mask=fovea_zone)
            if np.sum(ex_in_fovea > 0) > 0:
                foveal_hazard = True

        # 5. Partition Lesions into 4 Quadrants (ST, SN, IT, IN)
        cx_split, cy_split = (w // 2, h // 2)
        if anatomy.fovea_center is not None:
            cx_split, cy_split = anatomy.fovea_center

        ma_quadrants = {
            "ST": int(np.sum(ma_mask[:cy_split, cx_split:] > 0)),
            "SN": int(np.sum(ma_mask[:cy_split, :cx_split] > 0)),
            "IT": int(np.sum(ma_mask[cy_split:, cx_split:] > 0)),
            "IN": int(np.sum(ma_mask[cy_split:, :cx_split] > 0)),
        }

        he_quadrants = {
            "ST": int(np.sum(he_mask[:cy_split, cx_split:] > 0)),
            "SN": int(np.sum(he_mask[:cy_split, :cx_split] > 0)),
            "IT": int(np.sum(he_mask[cy_split:, cx_split:] > 0)),
            "IN": int(np.sum(he_mask[cy_split:, :cx_split] > 0)),
        }

        inventory = LesionInventory(
            microaneurysms_count=len(ma_candidates),
            microaneurysms_quadrants=ma_quadrants,
            hard_exudates_area_pct=round(hard_ex_pct, 3),
            soft_exudates_detected=bool(np.sum(soft_ex_mask > 0) > 0),
            hemorrhages_count=he_count,
            hemorrhages_quadrants=he_quadrants,
            neovascularization_detected=False,  # Evaluated in conjunction with vessel tortuosity/severity
            foveal_involvement_threat=bool(foveal_hazard),
            total_lesion_area_pct=round(total_lesion_pct, 3),
        )

        masks = {
            "microaneurysms": ma_mask,
            "hard_exudates": hard_ex_mask,
            "soft_exudates": soft_ex_mask,
            "hemorrhages": he_mask,
            "combined_lesions": combined_lesion_mask,
            "optic_disc": od_mask,
        }

        return inventory, masks
