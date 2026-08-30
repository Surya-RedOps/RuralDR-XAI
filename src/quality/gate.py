import json
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

from ..core.contracts import QualityStatus, QualityMetrics
from ..core.config import QUALITY_THRESHOLDS, MODELS_DIR
from .focus import compute_tenengrad, compute_laplacian_variance
from .illumination import compute_shannon_entropy, compute_exposure_and_glare
from .fov import extract_retinal_mask, compute_fov_coverage, compute_fov_metrics
from .contrast import compute_retinal_contrast


def _load_default_thresholds() -> Dict[str, Any]:
    """Loads calibrated engineering thresholds from models/image_quality/thresholds.json if present."""
    thresh_file = MODELS_DIR / "image_quality" / "thresholds.json"
    if thresh_file.is_file():
        try:
            with open(thresh_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: v for k, v in data.items() if isinstance(v, (int, float))}
        except Exception:
            pass
    return dict(QUALITY_THRESHOLDS)


class ImageQualityGate:
    """
    Automated Fundus Image Quality Gate (FIQA).
    Evaluates 9 clinical quality dimensions:
    1. Focus / Blur
    2. Illumination / Entropy
    3. Contrast (RMS & dynamic range)
    4. Retinal Field of View (Coverage & Centering)
    5. Overexposure / Glare
    6. Underexposure / Peripheral Falloff
    7. Retinal Content Visibility
    8. Black Border / Cropping Artifacts
    9. Color Distortion / Noise Artifacts

    Adheres strictly to the requirement that ungradable images must trigger
    actionable recapture advice and halt automatic diagnosis.
    """

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        if thresholds is not None:
            self.thresholds = thresholds
        else:
            self.thresholds = _load_default_thresholds()

    def evaluate(self, image_rgb: np.ndarray, mask: Optional[np.ndarray] = None) -> QualityMetrics:
        """
        Evaluates a raw or preprocessed fundus image across all quality dimensions.
        """
        if image_rgb is None or image_rgb.size == 0:
            return QualityMetrics(
                status=QualityStatus.UNGRADABLE,
                quality_score=0.0,
                focus_score=0.0,
                illumination_score=0.0,
                contrast_score=0.0,
                fov_coverage=0.0,
                glare_artifact_score=1.0,
                is_gradeable=False,
                recapture_advice=["Corrupted or empty image buffer received. Please re-upload or recapture."],
                details={"error": "Empty or corrupted image buffer"},
            )

        if mask is None:
            mask = extract_retinal_mask(image_rgb)

        focus_tenengrad = compute_tenengrad(image_rgb, mask)
        focus_laplacian = compute_laplacian_variance(image_rgb, mask)
        entropy = compute_shannon_entropy(image_rgb, mask)
        exposure_glare = compute_exposure_and_glare(image_rgb, mask)
        fov_metrics = compute_fov_metrics(image_rgb, mask)
        fov_coverage = fov_metrics["fov_coverage"]
        contrast_metrics = compute_retinal_contrast(image_rgb, mask)

        # Normalize metrics to [0, 1] range based on benchmark thresholds
        norm_focus = float(np.clip(focus_tenengrad / 100.0, 0.0, 1.0))
        norm_entropy = float(np.clip((entropy - 2.5) / 4.0, 0.0, 1.0))
        norm_fov = float(np.clip(fov_coverage / 0.70, 0.0, 1.0))
        norm_contrast = float(contrast_metrics["contrast_score"])
        glare_penalty = float(exposure_glare["glare_artifact_score"])
        color_penalty = float(exposure_glare.get("color_distortion_score", 0.0))

        # Composite Quality Score Q in [0, 1]
        raw_score = (
            0.30 * norm_focus
            + 0.25 * norm_entropy
            + 0.25 * norm_fov
            + 0.20 * norm_contrast
            - 0.25 * glare_penalty
            - 0.20 * color_penalty
        )
        quality_score = float(np.clip(raw_score, 0.0, 1.0))

        # Check rejection rules and generate specific actionable recapture guidance
        advice = []
        is_focus_fail = (
            focus_tenengrad < self.thresholds.get("min_focus_tenengrad", 25.0)
            or focus_laplacian < self.thresholds.get("min_focus_laplacian_var", 15.0)
        )
        is_illum_fail = (
            entropy < self.thresholds.get("min_entropy", 3.5)
            or exposure_glare["underexposed_ratio"] > 0.40
            or exposure_glare["mean_luminance"] < 20.0
        )
        is_glare_fail = exposure_glare["overexposed_ratio"] > self.thresholds.get("max_glare_ratio", 0.05)
        is_fov_fail = (
            fov_coverage < self.thresholds.get("min_fov_coverage", 0.45)
            or not fov_metrics["has_adequate_retina"]
        )
        is_contrast_fail = contrast_metrics["rms_contrast"] < self.thresholds.get("min_contrast_rms", 15.0)
        is_color_fail = color_penalty > 0.50

        if is_focus_fail:
            advice.append("Focus score inadequate: Adjust objective lens focus on retinal vasculature and stabilize camera.")
        if is_illum_fail:
            advice.append("Illumination insufficient / dark periphery: Increase flash intensity setting or exposure.")
        if is_glare_fail:
            advice.append("Excessive reflection or corneal glare: Re-align camera optical axis to pupil center.")
        if is_fov_fail:
            advice.append("Incomplete retinal field of view: Center the fundus and verify pupil alignment.")
        if is_contrast_fail:
            advice.append("Severely degraded contrast: Check pupil dilation and sensor exposure.")
        if is_color_fail:
            advice.append("Severe color distortion or sensor artifact: Verify camera white balance and sensor calibration.")

        # Determine Gradability Status
        borderline_threshold = self.thresholds.get("borderline_score", 0.40)
        pass_threshold = self.thresholds.get("quality_pass_score", 0.65)

        if (
            len(advice) >= 2
            or quality_score < borderline_threshold
            or (is_focus_fail and is_illum_fail)
            or not fov_metrics["has_adequate_retina"]
        ):
            status = QualityStatus.UNGRADABLE
            is_gradeable = False
        elif len(advice) == 1 or quality_score < pass_threshold:
            status = QualityStatus.BORDERLINE
            is_gradeable = True  # Can proceed if adaptive enhancement rescues quality
        else:
            status = QualityStatus.GRADEABLE
            is_gradeable = True

        details = {
            "focus_tenengrad": focus_tenengrad,
            "focus_laplacian_var": focus_laplacian,
            "shannon_entropy": entropy,
            "mean_luminance": exposure_glare["mean_luminance"],
            "underexposed_ratio": exposure_glare["underexposed_ratio"],
            "overexposed_ratio": exposure_glare["overexposed_ratio"],
            "rms_contrast": contrast_metrics["rms_contrast"],
            "dynamic_range": contrast_metrics["dynamic_range_p95_p5"],
            "fov_coverage": fov_coverage,
            "centering_offset": fov_metrics["centering_offset"],
            "aspect_ratio": fov_metrics["aspect_ratio"],
            "glare_artifact_score": glare_penalty,
            "color_distortion_score": color_penalty,
            "illumination_uniformity": exposure_glare.get("illumination_uniformity", 1.0),
        }

        return QualityMetrics(
            status=status,
            quality_score=quality_score,
            focus_score=focus_tenengrad,
            illumination_score=entropy,
            contrast_score=norm_contrast,
            fov_coverage=fov_coverage,
            glare_artifact_score=glare_penalty,
            is_gradeable=is_gradeable,
            recapture_advice=advice,
            details=details,
        )

