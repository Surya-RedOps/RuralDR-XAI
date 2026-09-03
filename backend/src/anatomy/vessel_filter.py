from typing import Tuple, Optional
import cv2
import numpy as np
from skimage.filters import frangi


def segment_retinal_vessels(
    image_rgb: np.ndarray,
    mask: np.ndarray = None,
    sigmas: tuple = (1.0, 2.0, 3.0),
    threshold_pct: float = 85.0,
) -> Tuple[np.ndarray, float]:
    """
    Segments the retinal vascular tree using Frangi multiscale Hessian eigenvalues.
    Operates on inverted green channel where vessels appear bright.

    Returns:
        vessel_mask: (H, W) uint8 binary array {0, 255}
        vessel_density: float in [0, 1]
    """
    if image_rgb.ndim == 3:
        green = image_rgb[:, :, 1]
    else:
        green = image_rgb

    # Apply CLAHE to green channel to normalize background
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    g_enhanced = clahe.apply(green)

    # Invert green channel (vessels are dark, Frangi expects bright tubular structures)
    inverted = 255 - g_enhanced

    # Compute multiscale Frangi vesselness
    vesselness = frangi(inverted.astype(np.float64) / 255.0, sigmas=sigmas, black_ridges=False)

    if mask is not None:
        valid_pixels = mask > 0
        vesselness[~valid_pixels] = 0.0
        # Adaptive percentile thresholding on valid retinal area
        valid_vals = vesselness[valid_pixels]
        if len(valid_vals) > 0 and np.max(valid_vals) > 0:
            thresh_val = np.percentile(valid_vals[valid_vals > 0], threshold_pct) if np.sum(valid_vals > 0) > 0 else 0.05
            binary_mask = (vesselness >= thresh_val).astype(np.uint8) * 255
        else:
            binary_mask = np.zeros(green.shape, dtype=np.uint8)
    else:
        thresh_val = np.percentile(vesselness[vesselness > 0], threshold_pct) if np.sum(vesselness > 0) > 0 else 0.05
        binary_mask = (vesselness >= thresh_val).astype(np.uint8) * 255

    # Morphological cleaning to remove isolated pixel noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

    if mask is not None:
        cleaned = cv2.bitwise_and(cleaned, cleaned, mask=mask)
        total_retina_pixels = np.sum(mask > 0)
        vessel_density = float(np.sum(cleaned > 0) / total_retina_pixels) if total_retina_pixels > 0 else 0.0
    else:
        vessel_density = float(np.sum(cleaned > 0) / (cleaned.shape[0] * cleaned.shape[1]))

    return cleaned, vessel_density
