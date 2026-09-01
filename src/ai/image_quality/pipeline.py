"""
Retina AI: Image Quality Gate & Adaptive Enhancement Pipeline
Ensures only clinically gradeable fundus images reach the downstream DR classification engine.
"""

from typing import Union, Dict, Any, Optional
from pathlib import Path
import time
import cv2
import numpy as np
from PIL import Image

from ...core.contracts import QualityStatus
from ...quality.gate import ImageQualityGate
from ...preprocess.enhance import AdaptiveEnhancer
from ..classification.inference import predict_retinopathy


def _load_image_rgb(image_input: Union[str, Path, np.ndarray, Image.Image]) -> np.ndarray:
    """Safely loads an image into an RGB uint8 numpy array without mutating source."""
    if isinstance(image_input, (str, Path)):
        img_path = Path(image_input)
        if not img_path.is_file():
            raise FileNotFoundError(f"Image not found at: {img_path}")
        with Image.open(img_path) as pil_img:
            return np.array(pil_img.convert("RGB"), dtype=np.uint8)
    elif isinstance(image_input, Image.Image):
        return np.array(image_input.convert("RGB"), dtype=np.uint8)
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 2:
            return cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
        elif image_input.ndim == 3 and image_input.shape[2] == 3:
            return image_input.copy()
        elif image_input.ndim == 3 and image_input.shape[2] == 4:
            return cv2.cvtColor(image_input, cv2.COLOR_RGBA2RGB)
        else:
            raise ValueError(f"Unsupported numpy image shape: {image_input.shape}")
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")


def assess_image_quality(
    image_input: Union[str, Path, np.ndarray, Image.Image],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluates retinal image quality against focus, illumination, contrast, FOV, and artifacts.

    Returns:
        {
            "status": "acceptable | borderline | ungradable",
            "quality_status": "acceptable | borderline | ungradable",
            "quality_score": 0.0,
            "quality_metrics": {
                "focus": ...,
                "illumination": ...,
                "contrast": ...,
                "field_of_view": ...,
                "artifacts": ...
            },
            "issues": [...],
            "recommendation": "...",
            "details": {...},
            "is_gradeable": bool,
            "evaluation_time_ms": float
        }
    """
    t0 = time.time()
    img_rgb = _load_image_rgb(image_input)

    gate = ImageQualityGate(thresholds=thresholds)
    metrics = gate.evaluate(img_rgb)
    elapsed_ms = (time.time() - t0) * 1000.0

    status_str = metrics.status.value.lower()
    if status_str == "gradeable":
        status_str = "acceptable"

    # Build primary recommendation message
    if metrics.status == QualityStatus.GRADEABLE:
        recommendation = "Image quality is sufficient for automated AI screening."
    elif metrics.status == QualityStatus.BORDERLINE:
        recommendation = "Image has borderline quality. Adaptive enhancement will be attempted."
    else:
        if metrics.recapture_advice:
            recommendation = " | ".join(metrics.recapture_advice)
        else:
            recommendation = "Image is ungradable due to insufficient optical clarity. Please recapture."

    return {
        "status": status_str,
        "quality_status": status_str,
        "quality_score": round(float(metrics.quality_score), 4),
        "is_gradeable": bool(metrics.is_gradeable),
        "quality_metrics": {
            "focus": round(float(metrics.focus_score), 2),
            "illumination": round(float(metrics.illumination_score), 2),
            "contrast": round(float(metrics.contrast_score or 0.0), 4),
            "field_of_view": round(float(metrics.fov_coverage), 4),
            "artifacts": round(float(metrics.glare_artifact_score), 4),
        },
        "issues": metrics.recapture_advice,
        "recommendation": recommendation,
        "details": metrics.details,
        "evaluation_time_ms": round(elapsed_ms, 2),
    }


def process_retinal_image(
    image_input: Union[str, Path, np.ndarray, Image.Image],
    run_dr_classifier: bool = True,
    dr_checkpoint_path: Optional[Path] = None,
    thresholds: Optional[Dict[str, float]] = None,
    save_enhanced_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Master screening orchestrator:
    1. Load original image (never mutated).
    2. Assess initial quality.
    3. If ACCEPTABLE -> run DR classifier.
    4. If BORDERLINE -> enhance with AdaptiveEnhancer, re-evaluate. If rescued -> run DR classifier.
    5. If UNGRADABLE -> reject and strictly block DR classifier.

    Returns complete structured screening report conforming to Phase 3 contracts.
    """
    total_t0 = time.time()
    original_rgb = _load_image_rgb(image_input)

    gate = ImageQualityGate(thresholds=thresholds)
    enhancer = AdaptiveEnhancer(clahe_clip_limit=2.0)

    # Stage 1: Initial Quality Evaluation
    initial_metrics = gate.evaluate(original_rgb)
    enhancement_applied = False
    reassessed_metrics = None
    processed_image = original_rgb
    final_status = initial_metrics.status
    enhanced_saved_path = None

    # Stage 2: Handle Borderline Quality via Adaptive Enhancement
    if initial_metrics.status == QualityStatus.BORDERLINE:
        enhanced_rgb = enhancer.enhance_borderline_image(original_rgb)
        reassessed_metrics = gate.evaluate(enhanced_rgb)
        enhancement_applied = True

        # Check if enhancement improved quality sufficiently to pass
        if (
            reassessed_metrics.status == QualityStatus.GRADEABLE
            or (reassessed_metrics.quality_score >= 0.50 and len(reassessed_metrics.recapture_advice) == 0)
        ):
            final_status = QualityStatus.GRADEABLE
            processed_image = enhanced_rgb

            if save_enhanced_path:
                save_p = Path(save_enhanced_path)
                save_p.parent.mkdir(parents=True, exist_ok=True)
                bgr = cv2.cvtColor(enhanced_rgb, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(save_p), bgr)
                enhanced_saved_path = str(save_p)
        else:
            # If enhancement failed to rescue quality, mark as ungradable
            final_status = QualityStatus.UNGRADABLE

    # Stage 3: Map to user-facing status
    status_str = final_status.value.lower()
    if status_str == "gradeable":
        status_str = "acceptable"

    # Stage 4: Downstream DR Inference (STRICT SAFETY INTERLOCK: ONLY for gradeable images)
    dr_prediction = None
    if final_status == QualityStatus.GRADEABLE and run_dr_classifier:
        try:
            dr_prediction = predict_retinopathy(
                image_input=processed_image,
                checkpoint_path=dr_checkpoint_path,
            )
        except Exception as e:
            dr_prediction = {"error": f"DR Classifier execution error: {str(e)}"}

    total_time_ms = (time.time() - total_t0) * 1000.0

    # Build actionable recommendation
    if final_status == QualityStatus.GRADEABLE:
        if enhancement_applied:
            recommendation = "Borderline image successfully enhanced and passed to DR classifier."
        else:
            recommendation = "Image quality acceptable. Automated analysis completed."
    else:
        active_advice = (
            reassessed_metrics.recapture_advice
            if (enhancement_applied and reassessed_metrics)
            else initial_metrics.recapture_advice
        )
        if active_advice:
            recommendation = "Image rejected. " + " | ".join(active_advice)
        else:
            recommendation = "Image rejected due to poor quality. Please recapture with proper focus and illumination."

    active_metrics = reassessed_metrics if (enhancement_applied and reassessed_metrics) else initial_metrics

    return {
        "status": status_str,
        "quality_status": status_str,
        "is_gradeable": bool(final_status == QualityStatus.GRADEABLE),
        "quality_score": round(float(active_metrics.quality_score), 4),
        "quality_metrics": {
            "focus": round(float(active_metrics.focus_score), 2),
            "illumination": round(float(active_metrics.illumination_score), 2),
            "contrast": round(float(active_metrics.contrast_score or 0.0), 4),
            "field_of_view": round(float(active_metrics.fov_coverage), 4),
            "artifacts": round(float(active_metrics.glare_artifact_score), 4),
        },
        "enhancement_applied": enhancement_applied,
        "enhanced_image_path": enhanced_saved_path,
        "initial_quality": {
            "status": initial_metrics.status.value.lower() if initial_metrics.status != QualityStatus.GRADEABLE else "acceptable",
            "quality_score": round(float(initial_metrics.quality_score), 4),
            "issues": initial_metrics.recapture_advice,
        },
        "reassessed_quality": {
            "status": reassessed_metrics.status.value.lower() if reassessed_metrics.status != QualityStatus.GRADEABLE else "acceptable",
            "quality_score": round(float(reassessed_metrics.quality_score), 4),
            "issues": reassessed_metrics.recapture_advice,
        }
        if reassessed_metrics
        else None,
        "issues": active_metrics.recapture_advice,
        "recommendation": recommendation,
        "dr_prediction": dr_prediction,
        "total_processing_time_ms": round(total_time_ms, 2),
        "medical_safety_notice": "Retina AI Image Quality Gate is a screening pre-check heuristic. It does not diagnose ocular health.",
    }

