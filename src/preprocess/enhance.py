"""
Adaptive Retinal Image Enhancement Pipeline
Includes circular ROI extraction, illumination homogenization (Gaussian subtraction),
edge-preserving bilateral denoising, and CLAHE.
"""

from typing import Tuple, Dict, Any, Optional
import cv2
import numpy as np

from ..quality.fov import extract_retinal_mask
from .clahe import apply_lab_clahe, apply_green_clahe


class AdaptiveEnhancer:
    """
    Adaptive Preprocessing Engine for Color Fundus Photography.
    Preserves original diagnostic features while standardizing illumination and resolution.
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (512, 512),
        clahe_clip_limit: float = 2.0,
        enable_gaussian_illumination_correction: bool = True,
    ):
        self.target_size = target_size
        self.clahe_clip_limit = clahe_clip_limit
        self.enable_gaussian_correction = enable_gaussian_illumination_correction

    def enhance_borderline_image(self, image_rgb: np.ndarray) -> np.ndarray:
        """
        Applies clinically conservative enhancement to borderline-quality fundus images:
        - Mild edge-preserving bilateral filter to suppress acquisition sensor noise.
        - Adaptive Lab CLAHE on L-channel to recover fine vessel and microvascular details.
        - Preserves chromaticity (a*, b*) to avoid altering exudate/hemorrhage hue.
        """
        if image_rgb is None or image_rgb.size == 0:
            return image_rgb

        # 1. Extract Retinal Mask
        mask = extract_retinal_mask(image_rgb)

        # 2. Edge-preserving bilateral filter on RGB (suppresses high-frequency sensor noise)
        denoised = cv2.bilateralFilter(image_rgb, d=5, sigmaColor=25, sigmaSpace=25)

        # 3. Lab CLAHE on Luminance channel
        enhanced = apply_lab_clahe(denoised, clip_limit=self.clahe_clip_limit)

        # 4. Apply mask to ensure outer background remains clean
        if mask is not None and np.sum(mask > 0) > 0:
            enhanced = cv2.bitwise_and(enhanced, enhanced, mask=mask)

        return enhanced

    def process(self, image_rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Processes a raw fundus image into a standardized, enhanced representation.

        Returns:
            enhanced_rgb: (H, W, 3) uint8 array in [0, 255]
            retinal_mask: (H, W) uint8 binary mask in {0, 255}
            applied_metadata: Dictionary of transformation details
        """
        original_shape = image_rgb.shape[:2]

        # 1. Retinal Mask & Bounding Box Cropping
        mask = extract_retinal_mask(image_rgb)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            x, y, w, h = cv2.boundingRect(np.vstack(contours))
            cropped_img = image_rgb[y : y + h, x : x + w]
            cropped_mask = mask[y : y + h, x : x + w]
        else:
            cropped_img = image_rgb
            cropped_mask = mask
            x, y, w, h = 0, 0, original_shape[1], original_shape[0]

        # 2. Resize to standard target dimension
        resized_img = cv2.resize(cropped_img, self.target_size, interpolation=cv2.INTER_AREA)
        resized_mask = cv2.resize(cropped_mask, self.target_size, interpolation=cv2.INTER_NEAREST)

        # 3. Optional Gaussian Illumination Homogenization (Graham's method for fundus images)
        if self.enable_gaussian_correction:
            # Blur with large Gaussian kernel (sigma ~ 15-30) to capture low-frequency illumination gradients
            blurred = cv2.GaussianBlur(resized_img, (0, 0), sigmaX=resized_img.shape[1] / 30)
            # Subtract low-frequency background and re-center around 128
            homogenized = cv2.addWeighted(resized_img, 4.0, blurred, -4.0, 128)
            # Mask out non-retinal background
            homogenized = cv2.bitwise_and(homogenized, homogenized, mask=resized_mask)
            # Blend 50% homogenized with 50% normalized original for natural contrast
            blended = cv2.addWeighted(resized_img, 0.5, homogenized, 0.5, 0)
        else:
            blended = resized_img

        # 4. Adaptive CLAHE
        enhanced = apply_lab_clahe(blended, clip_limit=self.clahe_clip_limit)
        enhanced = cv2.bitwise_and(enhanced, enhanced, mask=resized_mask)

        metadata = {
            "original_shape": original_shape,
            "crop_bbox": (x, y, w, h),
            "target_size": self.target_size,
            "clahe_clip_limit": self.clahe_clip_limit,
            "gaussian_homogenization": self.enable_gaussian_correction,
        }

        return enhanced, resized_mask, metadata
