"""
RuralDR-XAI: Fundus Modality Verification Gate (SIH26038)
Prevents non-retinal / out-of-domain images (vehicles, wallpapers, faces, documents, screenshots)
from entering the diabetic retinopathy diagnostic pipeline.

SAFETY PROTOCOL:
If the image cannot be conclusively verified as a retinal fundus photograph, all downstream
processing (Image Quality Gate, DR classification, Grad-CAM, lesion segmentation) MUST be halted immediately.
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
            num_classes=0,
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
        return self.classifier_head(feat)


def verify_aperture_and_periphery(image_rgb: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    Checks the ocular camera aperture and dark boundary periphery.
    Real retinal fundus photographs are captured through a circular/elliptical optical aperture
    with dark/black periphery corners. Non-fundus images (cars, wallpapers, landscapes, documents)
    fill rectangular bounds with edge content.
    """
    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    # 1. Corner Luminance Check (top-left, top-right, bottom-left, bottom-right)
    # Define 8% corner regions
    cw, ch = max(5, int(w * 0.08)), max(5, int(h * 0.08))
    tl = float(np.mean(gray[:ch, :cw]))
    tr = float(np.mean(gray[:ch, -cw:]))
    bl = float(np.mean(gray[-ch:, :cw]))
    br = float(np.mean(gray[-ch:, -cw:]))
    corner_means = [tl, tr, bl, br]
    avg_corner_luminance = float(np.mean(corner_means))
    max_corner_luminance = float(np.max(corner_means))

    # Real fundus photos have dark periphery corners (typically < 35 intensity)
    # Wallpapers/cars have bright skies, roads, UI bars, or white document corners (e.g. > 60)
    corners_are_dark = max_corner_luminance < 45.0
    corner_penalty = float(np.clip((avg_corner_luminance - 20.0) / 40.0, 0.0, 1.0))

    # 2. Foreground Mask and Circularity
    _, binary = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, {"reason": "no_foreground_contours", "corners_dark": False}

    largest_cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_cnt)
    perimeter = cv2.arcLength(largest_cnt, True)
    total_pixels = h * w
    area_ratio = area / float(total_pixels)

    # Circularity: 4 * pi * Area / Perimeter^2 (1.0 for perfect circle)
    circularity = float((4 * np.pi * area) / (perimeter**2 + 1e-6)) if perimeter > 0 else 0.0
    circularity = min(1.0, circularity)

    # Bounding box aspect ratio
    bx, by, bw, bh = cv2.boundingRect(largest_cnt)
    aspect_ratio = float(min(bw, bh) / max(bw, bh)) if max(bw, bh) > 0 else 0.0

    # Retinal images have circularity >= 0.50, aspect ratio >= 0.65, area coverage 0.25 - 0.95
    aperture_score = (
        0.40 * (1.0 - corner_penalty)
        + 0.35 * min(1.0, circularity / 0.55)
        + 0.25 * min(1.0, aspect_ratio / 0.70)
    )
    aperture_score = float(np.clip(aperture_score, 0.0, 1.0))

    details = {
        "avg_corner_luminance": round(avg_corner_luminance, 2),
        "max_corner_luminance": round(max_corner_luminance, 2),
        "corners_are_dark": corners_are_dark,
        "circularity": round(circularity, 3),
        "aspect_ratio": round(aspect_ratio, 3),
        "area_coverage": round(area_ratio, 3),
    }
    return aperture_score, details


def compute_retinal_color_plausibility(image_rgb: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    Computes structural color plausibility metric for retinal fundus imaging.
    Fundus photography has a distinct optical signature:
    - Retinal pigment epithelium & choroid produce strong red/amber dominance: R > G > B.
    - Blue channel reflectance is very low (< 22% in non-black foreground).
    - Documents have high lightness and near-zero saturation.
    - Outdoor/automotive/screenshot images contain high blue/cyan/cool tones, high specular highlights, or neutral grays.
    """
    if image_rgb is None or image_rgb.size == 0:
        return 0.0, {"error": "empty_image"}

    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    # Exclude dark background pixels (periphery mask)
    fg_mask = gray > 20
    fg_count = int(np.sum(fg_mask))
    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]

    if fg_count < 200:
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
    red_dominance = 1.0 if (r_ratio > 0.40 and mean_r > mean_g and mean_g > mean_b) else (
        0.5 if (mean_r > mean_b and r_ratio > 0.35) else 0.0
    )

    # 2. Blue Penalty: Retinas absorb blue light heavily. Blue ratio > 0.22 is characteristic of non-retinal scenes
    blue_penalty = max(0.0, min(1.0, (b_ratio - 0.20) / 0.12))

    # 3. HSV Saturation and Hue
    sat_fg = hsv[:, :, 1][fg_mask].astype(np.float32)
    mean_sat = float(np.mean(sat_fg)) / 255.0

    val_fg = hsv[:, :, 2][fg_mask].astype(np.float32)
    mean_val = float(np.mean(val_fg)) / 255.0

    # Documents have low saturation and high lightness
    is_document_like = bool(mean_sat < 0.12 and mean_val > 0.70)

    # Retinal Hue Check: Hue in OpenCV is 0-180 (retinal red/amber is 0-26 or 165-180)
    hue_fg = hsv[:, :, 0][fg_mask].astype(np.float32)
    retinal_hue_mask = (hue_fg <= 26) | (hue_fg >= 165)
    retinal_hue_fraction = float(np.sum(retinal_hue_mask) / (fg_count + 1e-6))

    # 4. Specular Highlight Check: Real retinas do not have large pure-white specular glare (> 245 in R, G, and B)
    specular_pixels = np.sum((r_fg > 240) & (g_fg > 240) & (b_fg > 240))
    specular_ratio = float(specular_pixels / (fg_count + 1e-6))
    specular_penalty = float(np.clip(specular_ratio / 0.05, 0.0, 1.0))

    color_score = (
        0.35 * red_dominance
        + 0.35 * retinal_hue_fraction
        + 0.30 * min(1.0, mean_sat / 0.30)
        - 0.50 * blue_penalty
        - 0.30 * specular_penalty
        - (0.80 if is_document_like else 0.0)
    )
    color_score = float(np.clip(color_score, 0.0, 1.0))

    details = {
        "mean_r": round(mean_r, 1),
        "mean_g": round(mean_g, 1),
        "mean_b": round(mean_b, 1),
        "r_ratio": round(r_ratio, 3),
        "b_ratio": round(b_ratio, 3),
        "retinal_hue_fraction": round(retinal_hue_fraction, 3),
        "blue_penalty": round(blue_penalty, 3),
        "specular_penalty": round(specular_penalty, 3),
        "is_document_like": is_document_like,
    }

    return color_score, details


def compute_vascular_presence(image_rgb: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    """
    Evaluates presence of biological branching vessel structure in the green channel.
    In genuine fundus photography, green channel contains distinctive darker branching vessels.
    Cars and wallpapers have straight geometric lines, sharp rectilinear boundaries, or noise.
    """
    g_channel = image_rgb[:, :, 1]
    # Apply CLAHE to enhance local vessel contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(g_channel)

    # Morphological top-hat to detect dark tubular structures
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    blackhat = cv2.morphologyEx(enhanced, cv2.MORPH_BLACKHAT, kernel)

    # Threshold potential vessel pixels
    _, thresh = cv2.threshold(blackhat, 12, 255, cv2.THRESH_BINARY)
    vessel_pixel_count = int(np.sum(thresh > 0))
    total_pixels = g_channel.shape[0] * g_channel.shape[1]
    vessel_ratio = float(vessel_pixel_count / total_pixels)

    # Detect straight line segments using Hough Lines (cars have many straight lines; vessels are curved/branching)
    edges = cv2.Canny(g_channel, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=50, maxLineGap=10)
    straight_line_count = len(lines) if lines is not None else 0

    # Real fundus has curved branching vessels (low straight lines, moderate tubular density)
    # Cars have many straight line segments (chassis, grill, road, spoiler, building edges)
    has_too_many_straight_lines = straight_line_count > 30

    vessel_score = float(np.clip(vessel_ratio / 0.04, 0.0, 1.0))
    if has_too_many_straight_lines:
        vessel_score *= 0.20  # Strong penalty for man-made geometric line patterns

    details = {
        "vessel_ratio": round(vessel_ratio, 4),
        "straight_line_count": straight_line_count,
        "has_too_many_straight_lines": has_too_many_straight_lines,
    }
    return vessel_score, details


class FundusModalityDetector:
    """
    Pre-Classification Fundus Modality Gate (Gate 1).
    Ensures that uploaded images are authentic retinal fundus photographs before
    allowing entry into the clinical pipeline.
    """

    def __init__(
        self,
        checkpoint_path: Optional[Path] = None,
        device: Optional[torch.device] = None,
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.checkpoint_path = checkpoint_path or (MODELS_DIR / "fundus_detector" / "best_fundus_detector.pth")

        self._load_model()

    def _load_model(self):
        """Loads trained fundus modality detector weights if available."""
        try:
            if self.checkpoint_path and Path(self.checkpoint_path).is_file():
                model = FundusClassifierModel(backbone_name="resnet18", pretrained=False)
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
        1. Aperture geometry & corner dark boundary verification
        2. Optical & color distribution plausibility
        3. Retinal vessel signature & geometric line penalty
        4. Deep learning feature classifier (if weights loaded)
        """
        if image_rgb is None or image_rgb.size == 0:
            return ModalityVerificationResult(
                status=ModalityStatus.NON_FUNDUS,
                fundus_probability=0.0,
                confidence=1.0,
                is_fundus=False,
                rejection_reason="Empty or invalid image data.",
            )

        # 1. Aperture & Periphery Geometry Check
        aperture_score, aperture_details = verify_aperture_and_periphery(image_rgb)

        # 2. Optical & Color Distribution
        color_score, color_details = compute_retinal_color_plausibility(image_rgb)

        # 3. Retinal Vascular & Straight Line Check
        vessel_score, vessel_details = compute_vascular_presence(image_rgb)

        # 4. Neural Network Probability if available
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
            # Calibrated multi-factor biometric combination
            prob_fundus = float(0.40 * color_score + 0.40 * aperture_score + 0.20 * vessel_score)
            prob_non_fundus = 1.0 - prob_fundus

        combined_details = {
            "model_prob_fundus": round(prob_fundus, 4),
            "color_score": round(color_score, 4),
            "aperture_score": round(aperture_score, 4),
            "vessel_score": round(vessel_score, 4),
            "color_details": color_details,
            "aperture_details": aperture_details,
            "vessel_details": vessel_details,
        }

        # REJECTION CRITERIA FOR NON-FUNDUS (Cars, Wallpapers, Documents, Faces, Landscapes):
        # 1. MANDATORY: True fundus photography is constrained within an ocular aperture with dark corners.
        #    Full-frame rectangular images with bright scene corners (cars, wallpapers, screenshots, documents) are 100% non-fundus.
        corners_dark = aperture_details.get("corners_are_dark", False)
        area_coverage = aperture_details.get("area_coverage", 1.0)
        is_full_frame_scene = (not corners_dark) or (area_coverage >= 0.98 and aperture_details.get("avg_corner_luminance", 100) > 25)

        is_clear_non_fundus = (
            is_full_frame_scene
            or color_score < 0.32
            or color_details.get("blue_penalty", 0.0) > 0.30
            or color_details.get("is_document_like", False)
            or vessel_details.get("has_too_many_straight_lines", False)
            or prob_fundus < 0.55
            or (color_score < 0.45 and aperture_score < 0.45)
        )

        # PASS CRITERIA FOR GENUINE FUNDUS:
        # - Must have dark ocular aperture corners
        # - Red/amber dominance (color_score >= 0.35)
        # - Aperture check passes (aperture_score >= 0.40)
        # - Organic curved vessel presence without straight line dominance
        # - Overall calibrated probability >= 0.55
        is_clear_fundus = (
            not is_clear_non_fundus
            and corners_dark
            and color_score >= 0.35
            and aperture_score >= 0.40
            and prob_fundus >= 0.55
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
            geometry_plausibility_score=round(aperture_score, 4),
            details=combined_details,
        )
