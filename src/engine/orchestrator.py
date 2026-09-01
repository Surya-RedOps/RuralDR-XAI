"""
RuralDR-XAI Master Pipeline Orchestrator
Executes the complete 10-stage screening workflow.
"""

from typing import Tuple, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
import torch

from ..core.contracts import (
    QualityStatus,
    ReviewPriority,
    RetinalAnatomy,
    ScreeningResult,
)
from ..quality.gate import ImageQualityGate
from ..preprocess.enhance import AdaptiveEnhancer
from ..anatomy.vessel_filter import segment_retinal_vessels
from ..anatomy.optic_disc import locate_optic_disc
from ..anatomy.fovea import locate_fovea
from ..lesions.detector import LesionEvidenceDetector
from ..models.classifier import DRClassifier
from ..models.calibrate import TemperatureScaler
from ..models.triage import evaluate_triage_decision
from ..xai.gradcam import GradCAM
from ..xai.visualization import create_comprehensive_annotated_fundus
from .consistency import EvidenceConsistencyEngine


class ScreeningOrchestrator:
    """
    End-to-End Orchestration Engine for Rural Diabetic Retinopathy Screening.
    """

    def __init__(
        self,
        classifier: Optional[DRClassifier] = None,
        temperature_scaler: Optional[TemperatureScaler] = None,
        device: torch.device = torch.device("cpu"),
    ):
        self.device = device
        self.quality_gate = ImageQualityGate()
        self.enhancer = AdaptiveEnhancer()
        self.lesion_detector = LesionEvidenceDetector()
        self.consistency_engine = EvidenceConsistencyEngine()

        self.classifier = classifier
        if self.classifier is not None:
            self.classifier.to(self.device)
            self.classifier.eval()
            self.gradcam = GradCAM(self.classifier, use_plus_plus=True)
        else:
            self.gradcam = None

        self.temperature_scaler = temperature_scaler or TemperatureScaler()

    def process_image(
        self,
        image_input: Any,  # file path (str/Path) or RGB numpy array
        case_id: Optional[str] = None,
    ) -> Tuple[ScreeningResult, Dict[str, np.ndarray]]:
        """
        Processes a single retinal fundus image through all 10 stages.

        Returns:
            result: Structured ScreeningResult contract
            visual_layers: Dictionary of processed image arrays (original, enhanced, CAM, lesion overlays, composite)
        """
        # 1. Load image
        if isinstance(image_input, (str, Path)):
            image_path = Path(image_input)
            if not image_path.is_file():
                raise FileNotFoundError(f"Input image not found at {image_path}")
            bgr = cv2.imread(str(image_path))
            if bgr is None:
                raise ValueError(f"Failed to decode image from {image_path}")
            image_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            if case_id is None:
                case_id = image_path.stem
        elif isinstance(image_input, np.ndarray):
            image_rgb = image_input
            if case_id is None:
                case_id = f"ANON-{int(datetime.now().timestamp())}"
        else:
            raise TypeError("Expected image file path or numpy array.")

        timestamp_str = datetime.now().isoformat()

        # 2. Stage 1: Quality Gate
        quality = self.quality_gate.evaluate(image_rgb)
        visual_layers = {"original": image_rgb}

        # Ungradable Safety Interlock: Stop immediately if ungradable
        if not quality.is_gradeable:
            empty_anatomy = RetinalAnatomy()
            empty_lesions = self.lesion_detector.detect(image_rgb, empty_anatomy)[0]
            result = ScreeningResult(
                case_id=case_id,
                timestamp=timestamp_str,
                quality=quality,
                anatomy=empty_anatomy,
                lesions=empty_lesions,
                prediction=None,
                evidence_consistency=None,
                triage_decision="UNGRADABLE: Image failed quality gate. Perform immediate recapture using advice.",
                review_priority=ReviewPriority.HIGH,
            )
            return result, visual_layers

        # 3. Stage 2: Adaptive Enhancement
        enhanced_rgb, mask, _ = self.enhancer.process(image_rgb)
        visual_layers["enhanced"] = enhanced_rgb
        visual_layers["retinal_mask"] = mask

        # 4. Stage 3: Retinal Anatomy Localization
        vessel_mask, vessel_density = segment_retinal_vessels(enhanced_rgb, mask)
        od_center, od_radius, od_bbox = locate_optic_disc(enhanced_rgb, mask)
        fovea_center = locate_fovea(enhanced_rgb, od_center, od_radius, vessel_mask, mask)

        anatomy = RetinalAnatomy(
            optic_disc_center=od_center,
            optic_disc_radius=od_radius,
            optic_disc_bbox=od_bbox,
            fovea_center=fovea_center,
            vessel_density=vessel_density,
            anatomical_landmarks_valid=(od_center is not None and fovea_center is not None),
        )
        visual_layers["vessel_mask"] = vessel_mask

        # 5. Stage 4: Lesion-Level Evidence Extraction
        lesion_inventory, lesion_masks = self.lesion_detector.detect(
            enhanced_rgb, anatomy, vessel_mask, mask
        )
        visual_layers.update(lesion_masks)

        # 6. Stage 5: Deep DR Severity Classification & Calibration
        if self.classifier is not None:
            # Prepare tensor (1, 3, H, W) normalized [0, 1] then ImageNet mean/std
            img_float = enhanced_rgb.astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            norm_img = (img_float - mean) / std
            tensor_in = torch.from_numpy(norm_img).permute(2, 0, 1).unsqueeze(0).to(self.device)

            prediction = self.classifier.predict(tensor_in, self.temperature_scaler)

            # 7. Stage 6: Explainable AI (Grad-CAM)
            cam_heatmap, cam_mask = self.gradcam.generate(
                tensor_in, target_class=prediction.predicted_grade.value
            )
            visual_layers["gradcam_heatmap"] = cam_heatmap
            visual_layers["gradcam_mask"] = cam_mask

            # 8. Stage 7: Evidence Consistency Engine
            consistency = self.consistency_engine.evaluate(
                prediction=prediction,
                lesion_inventory=lesion_inventory,
                lesion_masks=lesion_masks,
                cam_mask=cam_mask,
                cam_heatmap=cam_heatmap,
                anatomy=anatomy,
            )

            # 9. Stage 8 & 9: Triage Decision
            triage_msg, priority = evaluate_triage_decision(
                prediction=prediction,
                lesions=lesion_inventory,
                concordance_status=consistency.status.value,
            )
        else:
            # Model not yet loaded/trained: produce evidence-only baseline
            prediction = None
            consistency = None
            cam_heatmap = None
            triage_msg = "MODEL NOT LOADED: Anatomy and morphological lesion extraction complete."
            priority = ReviewPriority.ROUTINE

        # 10. Stage 10: Composite Annotated Visual Overlay
        composite_view = create_comprehensive_annotated_fundus(
            image_rgb=enhanced_rgb,
            anatomy=anatomy,
            lesion_masks=lesion_masks,
            heatmap=cam_heatmap,
            show_anatomy=True,
            show_lesions=True,
            show_cam=(cam_heatmap is not None),
        )
        visual_layers["composite_annotated"] = composite_view

        result = ScreeningResult(
            case_id=case_id,
            timestamp=timestamp_str,
            quality=quality,
            anatomy=anatomy,
            lesions=lesion_inventory,
            prediction=prediction,
            evidence_consistency=consistency,
            triage_decision=triage_msg,
            review_priority=priority,
        )

        return result, visual_layers
