"""
RuralDR-XAI: Fundus Modality Verification Gate
Prevents non-retinal / out-of-domain images from entering the DR diagnostic pipeline.

SAFETY NOTICE:
This is an automated modality verification stage (Gate 1).
If the image cannot be verified as a retinal fundus photograph, all downstream
diagnostic processing (DR classification, Grad-CAM, lesion segmentation) is halted.
"""

from typing import Tuple, Dict, Any, Optional
from pathlib import Path
import json
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm

from ..core.contracts import (
    ModalityStatus,
    ModalityVerificationResult,
)
from ..core.config import MODELS_DIR


class FundusClassifierModel(nn.Module):
    """
    Binary Transfer-Learning Neural Network for Fundus vs. Non-Fundus Modality Verification.
    0 = NON-FUNDUS (OOD: vehicles, people, documents, screenshots, landscapes, etc.)
    1 = FUNDUS (Valid retinal fundus photograph)
    """

    def __init__(
        self,
        backbone_name: str = "resnet18",
        pretrained: bool = False,
        dropout_rate: float = 0.2,
    ):
        super().__init__()
        self.backbone_name = backbone_name
        self.backbone = timm.create_model(
            backbone_name,
            pretrained=pretrained,
            num_classes=0,  # pooled feature vector
            drop_rate=dropout_rate,
        )
        num_features = self.backbone.num_features
        self.classifier_head = nn.Sequential(
            nn.Linear(num_features, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(128, 2),  # [Logit(Non-Fundus), Logit(Fundus)]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.backbone(x)
        logits = self.classifier_head(feat)
        return logits


def compute_retinal_color_plausibility(image_rgb: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    Computes structural color plausibility metric for retinal fundus imaging.
    Fundus photography has a distinct optical signature:
    - Retinal pigment epithelium & choroidal blood supply create strong red/orange dominance: R > G > B.
    - Blue channel reflectance is low (< 25% of energy in non-black foreground).
    - Documents have high lightness and near-zero saturation.
    - Outdoor/automotive/screenshot images contain high blue/cyan/cool tones or neutral grays.
    """
    if image_rgb is None or image_rgb.size == 0:
        return 0.0, {"error": "empty_image"}

    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    # Exclude dark background pixels (mask threshold)
    fg_mask = gray > 15
    fg_count = int(np.sum(fg_mask))
    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]

    if fg_count < 100:
        return 0.0, {"reason": "insufficient_foreground"}

    r_fg = image_rgb[:, :, 0][fg_mask].astype(np.float32)
    g_fg = image_rgb[:, :, 1][fg_mask].astype(np.float32)
    b_fg = image_rgb[:, :, 2][fg_mask].astype(np.float32)

    mean_r = float(np.mean(r_fg))
    mean_g = float(np.mean(g_fg))
    mean_b = float(np.mean(b_fg))
    total_rgb = mean_r + mean_g + mean_b + 1e-6

    r_ratio = mean_r / total_rgb
    g_ratio = mean_g / total_rgb
    b_ratio = mean_b / total_rgb

    # 1. Red Dominance Check: Real fundus typically has r_ratio > 0.38 and mean_r >= mean_g >= mean_b
    red_dominance = 1.0 if (r_ratio > 0.38 and mean_r >= mean_g >= mean_b) else (
        0.5 if (mean_r > mean_b) else 0.0
    )

    # 2. Blue Penalty: Retinas absorb blue light strongly. High blue ratio is non-retinal.
    blue_penalty = max(0.0, min(1.0, (b_ratio - 0.22) / 0.15))

    # 3. HSV Saturation and Hue
    sat_fg = hsv[:, :, 1][fg_mask].astype(np.float32)
    mean_sat = float(np.mean(sat_fg)) / 255.0  # 0 to 1
    
    val_fg = hsv[:, :, 2][fg_mask].astype(np.float32)
    mean_val = float(np.mean(val_fg)) / 255.0

    # Documents typically have mean_sat < 0.12 and mean_val > 0.70
    is_document_like = bool(mean_sat < 0.12 and mean_val > 0.70)
    
    # Retinal Hue Check: Hue values in OpenCV HSV are 0-180 (0-30 or 165-180 are red/orange)
    hue_fg = hsv[:, :, 0][fg_mask].astype(np.float32)
    retinal_hue_mask = (hue_fg <= 28) | (hue_fg >= 160)
    retinal_hue_fraction = float(np.sum(retinal_hue_mask) / (fg_count + 1e-6))

    # Calculate overall color plausibility score [0, 1]
    color_score = (
        0.35 * red_dominance
        + 0.35 * retinal_hue_fraction
        + 0.30 * min(1.0, mean_sat / 0.30)
        - 0.50 * blue_penalty
        - (0.80 if is_document_like else 0.0)
    )
    color_score = float(np.clip(color_score, 0.0, 1.0))

    details = {
        "mean_r": mean_r,
        "mean_g": mean_g,
        "mean_b": mean_b,
        "r_ratio": r_ratio,
        "g_ratio": g_ratio,
        "b_ratio": b_ratio,
        "mean_saturation": mean_sat,
        "retinal_hue_fraction": retinal_hue_fraction,
        "blue_penalty": blue_penalty,
        "is_document_like": is_document_like,
    }

    return color_score, details


def compute_retinal_geometry_plausibility(image_rgb: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    Computes geometry and aperture plausibility metrics for retinal fundus imaging.
    Standard fundus cameras have circular or elliptical aperture with black periphery.
    """
    if image_rgb is None or image_rgb.size == 0:
        return 0.0, {"error": "empty_image"}

    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape

    # Binary mask of foreground
    _, binary = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.1, {"reason": "no_contours"}

    largest_cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_cnt)
    perimeter = cv2.arcLength(largest_cnt, True)
    total_pixels = h * w
    area_ratio = area / total_pixels

    # Circularity metric: 4 * pi * Area / Perimeter^2 (1.0 for perfect circle)
    circularity = float((4 * np.pi * area) / (perimeter**2 + 1e-6)) if perimeter > 0 else 0.0
    circularity = min(1.0, circularity)

    # Bounding box aspect ratio
    x, y, bw, bh = cv2.boundingRect(largest_cnt)
    aspect_ratio = float(min(bw, bh) / max(bw, bh)) if max(bw, bh) > 0 else 0.0

    # Retinal images typically have area coverage 0.35 - 0.98 and aspect ratio >= 0.65
    geom_score = 0.5 * min(1.0, circularity / 0.60) + 0.5 * min(1.0, aspect_ratio / 0.65)
    geom_score = float(np.clip(geom_score, 0.0, 1.0))

    details = {
        "circularity": circularity,
        "aspect_ratio": aspect_ratio,
        "area_coverage": area_ratio,
    }

    return geom_score, details


class FundusModalityDetector:
    """
    Pre-Classification Fundus Modality Gate.
    Verifies that the uploaded image is a retinal fundus photograph before passing it
    to quality assessment, lesion extraction, or DR grading.
    """

    def __init__(
        self,
        checkpoint_path: Optional[Path] = None,
        device: Optional[torch.device] = None,
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.checkpoint_path = checkpoint_path or (MODELS_DIR / "fundus_detector" / "best_fundus_detector.pth")

        # Thresholds calibrated on validation split
        self.fundus_pass_prob = 0.65
        self.non_fundus_reject_prob = 0.35
        self.min_color_score = 0.30
        self.min_geom_score = 0.20

        self._load_model()

    def _load_model(self):
        """Loads trained fundus modality detector weights if available."""
        try:
            model = FundusClassifierModel(backbone_name="resnet18", pretrained=False)
            if self.checkpoint_path and Path(self.checkpoint_path).is_file():
                ckpt = torch.load(self.checkpoint_path, map_location=self.device)
                if "model_state_dict" in ckpt:
                    model.load_state_dict(ckpt["model_state_dict"])
                else:
                    model.load_state_dict(ckpt)
                model.to(self.device)
                model.eval()
                self.model = model
            else:
                self.model = None
        except Exception:
            self.model = None

    def verify(self, image_rgb: np.ndarray) -> ModalityVerificationResult:
        """
        Executes multi-evidence fundus modality verification.

        Combines:
        1. Deep Learning binary classifier probability P(fundus)
        2. Optical & color distribution plausibility metric
        3. Retinal geometry & aperture check

        Returns:
            ModalityVerificationResult with ModalityStatus (FUNDUS, NON_FUNDUS, UNCERTAIN)
        """
        if image_rgb is None or image_rgb.size == 0:
            return ModalityVerificationResult(
                status=ModalityStatus.NON_FUNDUS,
                fundus_probability=0.0,
                confidence=1.0,
                is_fundus=False,
                rejection_reason="Empty or invalid image data.",
            )

        # 1. Structural & Optical Checks
        color_score, color_details = compute_retinal_color_plausibility(image_rgb)
        geom_score, geom_details = compute_retinal_geometry_plausibility(image_rgb)

        # 2. Deep Learning Classifier Probability
        if self.model is not None:
            img_resized = cv2.resize(image_rgb, (224, 224), interpolation=cv2.INTER_AREA)
            img_float = img_resized.astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            norm_img = (img_float - mean) / std
            tensor_in = torch.from_numpy(norm_img).permute(2, 0, 1).unsqueeze(0).to(self.device)

            with torch.no_grad():
                logits = self.model(tensor_in)
                probs = F.softmax(logits, dim=1).cpu().numpy()[0]
                prob_non_fundus = float(probs[0])
                prob_fundus = float(probs[1])
        else:
            # High-precision heuristic probability
            prob_fundus = float(0.70 * color_score + 0.30 * geom_score)
            prob_non_fundus = 1.0 - prob_fundus

        combined_details = {
            "model_prob_fundus": prob_fundus,
            "model_prob_non_fundus": prob_non_fundus,
            "color_score": color_score,
            "geom_score": geom_score,
            "color_details": color_details,
            "geom_details": geom_details,
        }

        # Clear Non-Fundus conditions:
        # - Strong non-retinal color signature (color_score < 0.25)
        # - High blue ratio / cool palette (typical of cars, outdoor, UI)
        # - Document-like high lightness & near-zero saturation
        # - Low model fundus prediction
        is_clear_non_fundus = (
            color_score < 0.25
            or color_details.get("is_document_like", False)
            or color_details.get("blue_penalty", 0.0) > 0.40
            or (prob_fundus < self.non_fundus_reject_prob)
            or (color_score < 0.35 and geom_score < 0.25)
        )

        # Clear Fundus conditions:
        is_clear_fundus = (
            color_score >= self.min_color_score
            and prob_fundus >= self.fundus_pass_prob
            and not color_details.get("is_document_like", False)
        )

        if is_clear_non_fundus:
            status = ModalityStatus.NON_FUNDUS
            is_fundus = False
            rejection_reason = "This image does not appear to be a retinal fundus photograph."
            confidence = max(prob_non_fundus, 1.0 - color_score)
        elif is_clear_fundus:
            status = ModalityStatus.FUNDUS
            is_fundus = True
            rejection_reason = None
            confidence = prob_fundus
        else:
            # Borderline/Uncertain
            status = ModalityStatus.UNCERTAIN
            is_fundus = False
            rejection_reason = "Image could not be confidently verified as a retinal fundus photograph."
            confidence = float(abs(prob_fundus - 0.5) * 2.0)

        return ModalityVerificationResult(
            status=status,
            fundus_probability=round(prob_fundus, 4),
            confidence=round(confidence, 4),
            is_fundus=is_fundus,
            rejection_reason=rejection_reason,
            color_plausibility_score=round(color_score, 4),
            geometry_plausibility_score=round(geom_score, 4),
            details=combined_details,
        )
