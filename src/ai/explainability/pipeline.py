"""
Retina AI: Explainability Pipeline
Orchestrates Quality Gate → DR Classifier → Grad-CAM → Lesion Segmentation → Structured Output.

MEDICAL SAFETY:
This is an AI-assisted screening tool. All outputs require clinical confirmation.
Grad-CAM shows model attention, NOT clinical proof of specific pathology.
Lesion segmentation detects AI-estimated retinal features, NOT confirmed diagnoses.
"""

from typing import Union, Dict, Any, Optional
from pathlib import Path
import time
import json
import uuid
from datetime import datetime, timezone

import cv2
import numpy as np
import torch
from PIL import Image

from ...core.config import MODELS_DIR
from ...core.contracts import (
    QualityStatus,
    DRGrade,
    DR_GRADE_NAMES,
    GradCAMResult,
    ExplainableScreeningResult,
)
from ...quality.gate import ImageQualityGate
from ...preprocess.enhance import AdaptiveEnhancer
from ...ai.classification.inference import load_inference_model, predict_retinopathy
from ...xai.gradcam import GradCAM
from ...xai.visualization import save_gradcam_outputs
from ...ai.segmentation.inference import LesionSegmenter


def _load_image_rgb(image_input: Union[str, Path, np.ndarray, Image.Image]) -> np.ndarray:
    """Safely loads an image into an RGB uint8 numpy array."""
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
            raise ValueError(f"Unsupported image shape: {image_input.shape}")
    else:
        raise TypeError(f"Unsupported image type: {type(image_input)}")


def _build_evidence_summary(
    dr_grade: Optional[int],
    severity: Optional[str],
    confidence: Optional[float],
    gradcam_result: Optional[GradCAMResult],
    segmentation_lesions: list,
) -> list:
    """
    Builds human-readable evidence summary using medically safe terminology.

    IMPORTANT: Does NOT claim causation between lesions and DR grade.
    Uses "associated with" rather than "caused by" language.
    """
    summary = []

    if dr_grade is not None:
        summary.append(f"AI screening result: {severity} (Grade {dr_grade})")

    if confidence is not None:
        summary.append(f"Classification model confidence: {confidence:.1%}")

    if gradcam_result is not None:
        if gradcam_result.is_valid:
            summary.append("Model attention map (Grad-CAM) is available for review")
        else:
            flags = ", ".join(gradcam_result.quality_flags)
            summary.append(f"Model attention map has quality concerns: {flags}")

    # Lesion evidence
    detected_lesions = [l for l in segmentation_lesions if l.detected]
    if detected_lesions:
        lesion_types = [l.lesion_type.replace("_", " ").title() for l in detected_lesions]
        summary.append(
            f"AI-detected retinal features: {', '.join(lesion_types)}"
        )
        for lesion in detected_lesions:
            name = lesion.lesion_type.replace("_", " ").title()
            summary.append(
                f"  - {name}: {lesion.num_connected_components} region(s), "
                f"{lesion.relative_area_pct:.3f}% of image area, "
                f"segmentation confidence {lesion.mean_confidence:.1%}"
            )
    else:
        summary.append("No retinal lesion features detected by the segmentation model")

    summary.append("All findings require clinical confirmation by a qualified ophthalmologist")

    return summary


class ExplainableScreeningPipeline:
    """
    Master explainability pipeline.

    Orchestrates:
        Quality Gate → DR Classifier → Grad-CAM → Lesion Segmentation → Structured JSON

    Tracks per-stage timing and image provenance (original vs. enhanced).
    """

    def __init__(
        self,
        dr_checkpoint_path: Optional[Path] = None,
        seg_checkpoint_path: Optional[Path] = None,
        quality_thresholds: Optional[Dict[str, float]] = None,
        device: Optional[torch.device] = None,
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.dr_checkpoint_path = dr_checkpoint_path
        self.quality_thresholds = quality_thresholds

        # Initialize components
        self.quality_gate = ImageQualityGate(thresholds=quality_thresholds)
        self.enhancer = AdaptiveEnhancer(clahe_clip_limit=2.0)

        # Lazy-load DR model and segmenter
        self._dr_model = None
        self._dr_temp = 1.0
        self._gradcam = None

        try:
            self.segmenter = LesionSegmenter(
                checkpoint_path=seg_checkpoint_path,
                device=self.device,
            )
        except Exception:
            self.segmenter = LesionSegmenter.__new__(LesionSegmenter)
            self.segmenter.model_available = False
            self.segmenter.model = None

    def _ensure_dr_model(self):
        """Lazy-loads and caches the DR classifier."""
        if self._dr_model is None:
            self._dr_model, self._dr_temp, _ = load_inference_model(
                checkpoint_path=self.dr_checkpoint_path,
                device=self.device,
            )
            self._gradcam = GradCAM(self._dr_model, use_plus_plus=True)

    def process(
        self,
        image_input: Union[str, Path, np.ndarray],
        output_dir: Optional[str] = None,
        case_id: Optional[str] = None,
        run_segmentation: bool = True,
    ) -> ExplainableScreeningResult:
        """
        Runs the complete explainability pipeline.

        Args:
            image_input: Path to image or RGB numpy array
            output_dir: Directory to save all outputs (Grad-CAM, masks, etc.)
            case_id: Optional case identifier
            run_segmentation: Whether to run lesion segmentation

        Returns:
            ExplainableScreeningResult with comprehensive pipeline output
        """
        pipeline_t0 = time.time()

        if case_id is None:
            case_id = uuid.uuid4().hex[:12]

        timestamp = datetime.now(timezone.utc).isoformat()

        # Prepare output directory
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

        # Load original image (immutable copy)
        original_rgb = _load_image_rgb(image_input)
        original_image_path = str(image_input) if isinstance(image_input, (str, Path)) else None

        # ─── Stage 1: Quality Gate ──────────────────────────────
        quality_t0 = time.time()
        initial_metrics = self.quality_gate.evaluate(original_rgb)

        enhancement_applied = False
        processed_image = original_rgb
        final_status = initial_metrics.status
        enhanced_image_path = None

        if initial_metrics.status == QualityStatus.BORDERLINE:
            enhanced_rgb = self.enhancer.enhance_borderline_image(original_rgb)
            reassessed = self.quality_gate.evaluate(enhanced_rgb)
            enhancement_applied = True

            if (reassessed.status == QualityStatus.GRADEABLE or
                    (reassessed.quality_score >= 0.50 and len(reassessed.recapture_advice) == 0)):
                final_status = QualityStatus.GRADEABLE
                processed_image = enhanced_rgb

                if output_dir:
                    enh_path = Path(output_dir) / f"{case_id}_enhanced.jpg"
                    cv2.imwrite(str(enh_path), cv2.cvtColor(enhanced_rgb, cv2.COLOR_RGB2BGR))
                    enhanced_image_path = str(enh_path)
            else:
                final_status = QualityStatus.UNGRADABLE

        quality_time = (time.time() - quality_t0) * 1000.0

        status_str = final_status.value.lower()
        if status_str == "gradeable":
            status_str = "acceptable"

        # ─── Early exit for ungradable images ───────────────────
        if final_status != QualityStatus.GRADEABLE:
            total_time = (time.time() - pipeline_t0) * 1000.0
            return ExplainableScreeningResult(
                case_id=case_id,
                timestamp=timestamp,
                original_image_path=original_image_path,
                quality_status=status_str,
                quality_score=round(float(initial_metrics.quality_score), 4),
                is_gradeable=False,
                quality_gate_time_ms=round(quality_time, 2),
                total_pipeline_time_ms=round(total_time, 2),
                evidence_summary=[
                    "Image quality is insufficient for AI screening",
                    "Please recapture with proper focus and illumination",
                ],
            )

        # ─── Stage 2: DR Classification ────────────────────────
        classification_t0 = time.time()
        self._ensure_dr_model()

        dr_result = predict_retinopathy(
            image_input=processed_image,
            checkpoint_path=self.dr_checkpoint_path,
        )
        classification_time = (time.time() - classification_t0) * 1000.0

        dr_grade = dr_result.get("dr_grade")
        severity = dr_result.get("severity")
        confidence = dr_result.get("confidence")
        is_referable = dr_result.get("is_referable")
        class_probs = dr_result.get("class_probabilities")

        # ─── Stage 3: Grad-CAM ─────────────────────────────────
        gradcam_t0 = time.time()
        gradcam_result = None

        if self._gradcam is not None:
            try:
                # Prepare tensor matching classifier preprocessing
                from ...ai.classification.dataset import load_and_preprocess_image
                from ...ai.classification.inference import _MODEL_CACHE

                img_size = _MODEL_CACHE.get("img_size", 224)
                preprocessed = load_and_preprocess_image(
                    processed_image,
                    target_size=(img_size, img_size),
                    apply_clahe=True,
                )

                mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
                std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
                norm_img = preprocessed.astype(np.float32) / 255.0
                norm_img = (norm_img - mean) / std

                input_tensor = torch.from_numpy(norm_img).permute(2, 0, 1).unsqueeze(0).float()
                input_tensor = input_tensor.to(self.device)

                cam_np, binary_mask, gradcam_result = self._gradcam.generate_with_validation(
                    input_tensor, target_class=dr_grade,
                )

                # Save outputs
                if output_dir:
                    # Use the preprocessed image for overlay (matches what the model saw)
                    gradcam_paths = save_gradcam_outputs(
                        image_rgb=preprocessed,
                        heatmap=cam_np,
                        binary_mask=binary_mask,
                        output_dir=output_dir,
                        prefix=f"{case_id}_gradcam",
                        class_name=severity or "",
                        confidence=confidence or 0.0,
                    )
                    gradcam_result.heatmap_path = gradcam_paths.get("heatmap")
                    gradcam_result.overlay_path = gradcam_paths.get("overlay")
                    gradcam_result.binary_mask_path = gradcam_paths.get("binary_mask")

            except Exception as e:
                gradcam_result = GradCAMResult(
                    target_class=dr_grade or 0,
                    is_valid=False,
                    quality_flags=[f"generation_error: {str(e)}"],
                )

        gradcam_time = (time.time() - gradcam_t0) * 1000.0

        # ─── Stage 4: Lesion Segmentation ──────────────────────
        seg_t0 = time.time()
        seg_result = None

        if run_segmentation and self.segmenter and self.segmenter.model_available:
            try:
                seg_result = self.segmenter.segment(
                    image_rgb=processed_image,
                    save_dir=output_dir,
                    prefix=case_id,
                )
            except Exception:
                seg_result = None

        seg_time = (time.time() - seg_t0) * 1000.0

        # ─── Stage 5: Build Evidence Summary ───────────────────
        lesion_list = seg_result.lesions if seg_result else []
        evidence = _build_evidence_summary(
            dr_grade=dr_grade,
            severity=severity,
            confidence=confidence,
            gradcam_result=gradcam_result,
            segmentation_lesions=lesion_list,
        )

        total_time = (time.time() - pipeline_t0) * 1000.0

        # Save original image
        if output_dir:
            orig_save = Path(output_dir) / f"{case_id}_original.jpg"
            cv2.imwrite(str(orig_save), cv2.cvtColor(original_rgb, cv2.COLOR_RGB2BGR))

        # Save structured JSON result
        result = ExplainableScreeningResult(
            case_id=case_id,
            timestamp=timestamp,
            original_image_path=original_image_path,
            enhanced_image_path=enhanced_image_path,
            inference_image_source="enhanced" if enhancement_applied else "original",
            quality_status=status_str,
            quality_score=round(float(initial_metrics.quality_score), 4),
            is_gradeable=True,
            dr_grade=dr_grade,
            severity=severity,
            classification_confidence=confidence,
            is_referable=is_referable,
            class_probabilities=class_probs,
            gradcam_result=gradcam_result,
            segmentation_result=seg_result,
            quality_gate_time_ms=round(quality_time, 2),
            classification_time_ms=round(classification_time, 2),
            gradcam_time_ms=round(gradcam_time, 2),
            segmentation_time_ms=round(seg_time, 2),
            total_pipeline_time_ms=round(total_time, 2),
            evidence_summary=evidence,
        )

        # Save JSON
        if output_dir:
            json_path = Path(output_dir) / f"{case_id}_explainability_result.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)

        return result
