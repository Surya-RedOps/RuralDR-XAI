"""
Fundus Image Quality Gate (FIQA)
Orchestrates focus, illumination, exposure, and FOV checks.
Produces GRADEABLE, BORDERLINE, or UNGRADABLE decisions with actionable recapture advice.
"""

from typing import Optional, Dict
import numpy as np

from ..core.contracts import QualityStatus, QualityMetrics
from ..core.config import QUALITY_THRESHOLDS
from .focus import compute_tenengrad, compute_laplacian_variance
from .illumination import compute_shannon_entropy, compute_exposure_and_glare
from .fov import extract_retinal_mask, compute_fov_coverage


class ImageQualityGate:
    """
    Automated Fundus Image Quality Gate.
    Adheres strictly to the requirement that ungradable images must trigger
    actionable recapture advice and halt automatic diagnosis.
    """

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or QUALITY_THRESHOLDS

    def evaluate(self, image_rgb: np.ndarray, mask: Optional[np.ndarray] = None) -> QualityMetrics:
        """
        Evaluates a raw or preprocessed fundus image.
        """
        if mask is None:
            mask = extract_retinal_mask(image_rgb)

        focus_tenengrad = compute_tenengrad(image_rgb, mask)
        focus_laplacian = compute_laplacian_variance(image_rgb, mask)
        entropy = compute_shannon_entropy(image_rgb, mask)
        exposure_glare = compute_exposure_and_glare(image_rgb, mask)
        fov_coverage = compute_fov_coverage(image_rgb, mask)

        # Normalize metrics to [0, 1] range based on benchmark thresholds
        norm_focus = float(np.clip(focus_tenengrad / 100.0, 0.0, 1.0))
        norm_entropy = float(np.clip((entropy - 2.5) / 4.0, 0.0, 1.0))
        norm_fov = float(np.clip(fov_coverage / 0.70, 0.0, 1.0))
        glare_penalty = exposure_glare["glare_artifact_score"]

        # Composite Quality Score Q in [0, 1]
        raw_score = 0.35 * norm_focus + 0.35 * norm_entropy + 0.30 * norm_fov - 0.25 * glare_penalty
        quality_score = float(np.clip(raw_score, 0.0, 1.0))

        # Check rejection rules and generate specific clinical recapture guidance
        advice = []
        is_focus_fail = focus_tenengrad < self.thresholds["min_focus_tenengrad"]
        is_illum_fail = entropy < self.thresholds["min_entropy"] or exposure_glare["underexposed_ratio"] > 0.40
        is_glare_fail = exposure_glare["overexposed_ratio"] > self.thresholds["max_glare_ratio"]
        is_fov_fail = fov_coverage < self.thresholds["min_fov_coverage"]

        if is_focus_fail:
            advice.append("Focus score inadequate: Adjust objective lens focus on retinal vasculature.")
        if is_illum_fail:
            advice.append("Illumination insufficient / dark periphery: Increase flash intensity setting.")
        if is_glare_fail:
            advice.append("Excessive reflection or corneal glare: Re-align camera optical axis to pupil center.")
        if is_fov_fail:
            advice.append("Incomplete retinal field of view: Center the fundus and verify pupil alignment.")

        # Determine Gradability Status
        if len(advice) >= 2 or quality_score < self.thresholds["borderline_score"] or (is_focus_fail and is_illum_fail):
            status = QualityStatus.UNGRADABLE
            is_gradeable = False
        elif len(advice) == 1 or quality_score < self.thresholds["quality_pass_score"]:
            status = QualityStatus.BORDERLINE
            is_gradeable = True  # Can proceed if adaptive enhancement rescues quality
        else:
            status = QualityStatus.GRADEABLE
            is_gradeable = True

        return QualityMetrics(
            status=status,
            quality_score=quality_score,
            focus_score=focus_tenengrad,
            illumination_score=entropy,
            fov_coverage=fov_coverage,
            glare_artifact_score=glare_penalty,
            is_gradeable=is_gradeable,
            recapture_advice=advice,
        )
