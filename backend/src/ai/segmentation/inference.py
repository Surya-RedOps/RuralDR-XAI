"""
Retina AI: Lesion Segmentation Inference Module
Provides reusable lesion segmentation with quantification and confidence estimation.

MEDICAL SAFETY NOTE:
Segmentation outputs are AI-detected retinal features. They are NOT confirmed clinical
lesions and require validation by a qualified ophthalmologist.
"""

from typing import Union, Dict, Any, Optional, List, Tuple
from pathlib import Path
import time
import cv2
import numpy as np
import torch
from PIL import Image

from ...core.config import MODELS_DIR
from ...core.contracts import (
    LesionDetectionResult,
    LesionSegmentationResult,
)
from ...models.unet import LesionUNet

# ImageNet normalization
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Global model cache
_SEG_MODEL_CACHE: Dict[str, Any] = {
    "model": None,
    "device": None,
}


def load_segmentation_model(
    checkpoint_path: Optional[Path] = None,
    device: Optional[torch.device] = None,
) -> LesionUNet:
    """Loads and caches the trained lesion segmentation model."""
    global _SEG_MODEL_CACHE

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if checkpoint_path is None:
        checkpoint_path = MODELS_DIR / "segmentation" / "lesion_unet_best.pth"

    if not Path(checkpoint_path).is_file():
        raise FileNotFoundError(
            f"Segmentation model not found at {checkpoint_path}. "
            "Run scripts/train_segmentation.py first."
        )

    ckpt = torch.load(checkpoint_path, map_location=device)
    encoder_name = ckpt.get("encoder_name", "resnet18")
    model = LesionUNet(encoder_name=encoder_name, num_classes=4, pretrained=False)

    if "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        model.load_state_dict(ckpt)

    model.to(device)
    model.eval()

    _SEG_MODEL_CACHE["model"] = model
    _SEG_MODEL_CACHE["device"] = device

    return model


def _preprocess_for_segmentation(
    image_rgb: np.ndarray,
    target_size: Tuple[int, int] = (512, 512),
) -> Tuple[torch.Tensor, Tuple[int, int]]:
    """Preprocesses an RGB image for segmentation inference."""
    orig_size = image_rgb.shape[:2]

    resized = cv2.resize(image_rgb, (target_size[1], target_size[0]),
                         interpolation=cv2.INTER_AREA)

    norm = resized.astype(np.float32) / 255.0
    norm = (norm - IMAGENET_MEAN) / IMAGENET_STD

    tensor = torch.from_numpy(norm).permute(2, 0, 1).unsqueeze(0).float()

    return tensor, orig_size


def _quantify_lesion_mask(
    mask_binary: np.ndarray,
    prob_map: np.ndarray,
    image_area: int,
) -> Dict[str, Any]:
    """
    Quantifies a binary lesion mask.

    Returns:
        pixel_area, relative_area_pct, num_components, mean_confidence, centroids
    """
    pixel_area = int(np.sum(mask_binary > 0))
    relative_area_pct = round(float(pixel_area / image_area * 100.0), 4) if image_area > 0 else 0.0

    # Connected components
    if pixel_area > 0:
        num_labels, labels, stats, centroids_arr = cv2.connectedComponentsWithStats(
            mask_binary.astype(np.uint8)
        )
        num_components = num_labels - 1  # Exclude background
        locations = [
            (int(centroids_arr[i][0]), int(centroids_arr[i][1]))
            for i in range(1, num_labels)
        ]
    else:
        num_components = 0
        locations = []

    # Mean confidence from probability map over positive pixels
    if pixel_area > 0:
        mean_conf = float(np.mean(prob_map[mask_binary > 0]))
    else:
        mean_conf = 0.0

    return {
        "pixel_area": pixel_area,
        "relative_area_pct": relative_area_pct,
        "num_connected_components": num_components,
        "mean_confidence": round(mean_conf, 4),
        "approximate_locations": locations[:50],  # Cap at 50 for large lesion fields
    }


class LesionSegmenter:
    """
    Reusable lesion segmentation inference interface.

    Produces per-lesion binary masks, probability maps, and quantification.
    """

    LESION_NAMES = ["microaneurysms", "haemorrhages", "hard_exudates", "soft_exudates"]

    def __init__(
        self,
        checkpoint_path: Optional[Path] = None,
        device: Optional[torch.device] = None,
        threshold: float = 0.5,
        target_size: Tuple[int, int] = (512, 512),
    ):
        self.threshold = threshold
        self.target_size = target_size
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        try:
            self.model = load_segmentation_model(checkpoint_path, self.device)
            self.model_available = True
            self.model_path = str(checkpoint_path or MODELS_DIR / "segmentation" / "lesion_unet_best.pth")
        except FileNotFoundError:
            self.model = None
            self.model_available = False
            self.model_path = None

    def segment(
        self,
        image_rgb: np.ndarray,
        save_dir: Optional[str] = None,
        prefix: str = "lesion",
    ) -> LesionSegmentationResult:
        """
        Runs lesion segmentation on a retinal fundus image.

        Args:
            image_rgb: (H, W, 3) RGB uint8 image
            save_dir: Optional directory to save mask images
            prefix: Filename prefix for saved masks

        Returns:
            LesionSegmentationResult with per-lesion detection details
        """
        if not self.model_available:
            # Return empty result if model is not trained yet
            return LesionSegmentationResult(
                lesions=[
                    LesionDetectionResult(lesion_type=name, detected=False)
                    for name in self.LESION_NAMES
                ],
                model_path=None,
                input_resolution=self.target_size,
            )

        t0 = time.time()

        # Preprocess
        input_tensor, orig_size = _preprocess_for_segmentation(
            image_rgb, self.target_size
        )
        input_tensor = input_tensor.to(self.device)

        # Inference
        self.model.eval()
        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.sigmoid(logits).cpu().numpy()[0]  # (4, H, W)
            masks = (probs >= self.threshold).astype(np.uint8)

        seg_time_ms = (time.time() - t0) * 1000.0
        image_area = self.target_size[0] * self.target_size[1]

        # Build per-lesion results
        lesion_results = []
        for i, lesion_name in enumerate(self.LESION_NAMES):
            mask_binary = masks[i]
            prob_map = probs[i]

            quant = _quantify_lesion_mask(mask_binary, prob_map, image_area)

            # Optionally save mask
            mask_path = None
            if save_dir and quant["pixel_area"] > 0:
                save_p = Path(save_dir)
                save_p.mkdir(parents=True, exist_ok=True)
                mask_path_obj = save_p / f"{prefix}_{lesion_name}.png"
                cv2.imwrite(str(mask_path_obj), mask_binary * 255)
                mask_path = str(mask_path_obj)

            lesion_results.append(LesionDetectionResult(
                lesion_type=lesion_name,
                detected=bool(quant["pixel_area"] > 0),
                mask_path=mask_path,
                pixel_area=quant["pixel_area"],
                relative_area_pct=quant["relative_area_pct"],
                num_connected_components=quant["num_connected_components"],
                mean_confidence=quant["mean_confidence"],
                approximate_locations=quant["approximate_locations"],
            ))

        return LesionSegmentationResult(
            lesions=lesion_results,
            model_path=self.model_path,
            input_resolution=self.target_size,
            segmentation_time_ms=round(seg_time_ms, 2),
        )

    def get_raw_predictions(
        self,
        image_rgb: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns raw probability maps and binary masks for visualization.

        Returns:
            probs: (4, H, W) float32 probability maps
            masks: (4, H, W) uint8 binary masks
        """
        if not self.model_available:
            h, w = self.target_size
            return np.zeros((4, h, w), dtype=np.float32), np.zeros((4, h, w), dtype=np.uint8)

        input_tensor, _ = _preprocess_for_segmentation(image_rgb, self.target_size)
        input_tensor = input_tensor.to(self.device)

        self.model.eval()
        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.sigmoid(logits).cpu().numpy()[0]
            masks = (probs >= self.threshold).astype(np.uint8)

        return probs, masks
