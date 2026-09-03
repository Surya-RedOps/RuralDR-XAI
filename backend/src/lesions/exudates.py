from typing import Tuple, Optional
import cv2
import numpy as np


def segment_exudates(
    image_rgb: np.ndarray,
    optic_disc_mask: Optional[np.ndarray] = None,
    mask: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Segments hard exudates (EX) and soft exudates (SE / Cotton Wool Spots).

    Returns:
        hard_exudates_mask: (H, W) binary uint8 mask {0, 255}
        soft_exudates_mask: (H, W) binary uint8 mask {0, 255}
        hard_exudates_area_pct: float percentage of retinal area
    """
    if image_rgb.ndim != 3:
        raise ValueError("Exudate segmentation requires 3-channel RGB fundus image.")

    # Convert to Lab color space
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)

    # Exudates have high L* (brightness) and high b* (yellowish tint)
    combined_ex = (l_chan.astype(np.float32) * 0.6 + b_chan.astype(np.float32) * 0.4).astype(np.uint8)

    if mask is not None:
        valid_pixels = mask > 0
        valid_vals = combined_ex[valid_pixels]
        thresh_hard = np.percentile(valid_vals, 97.5) if len(valid_vals) > 0 else 180
        thresh_soft = np.percentile(valid_vals, 94.0) if len(valid_vals) > 0 else 160
    else:
        thresh_hard = np.percentile(combined_ex, 97.5)
        thresh_soft = np.percentile(combined_ex, 94.0)

    _, hard_binary = cv2.threshold(combined_ex, int(thresh_hard), 255, cv2.THRESH_BINARY)
    _, soft_binary = cv2.threshold(combined_ex, int(thresh_soft), 255, cv2.THRESH_BINARY)

    # Subtract Optic Disc (crucial because OD is bright yellow/white and would cause massive false positive)
    if optic_disc_mask is not None:
        dilated_od = cv2.dilate(optic_disc_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        hard_binary[dilated_od > 0] = 0
        soft_binary[dilated_od > 0] = 0

    # Subtract non-retinal background boundary
    if mask is not None:
        eroded_mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20)))
        hard_binary[eroded_mask == 0] = 0
        soft_binary[eroded_mask == 0] = 0

    # Morphological filtering to isolate coherent clusters
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    hard_cleaned = cv2.morphologyEx(hard_binary, cv2.MORPH_OPEN, kernel_small)

    # Soft exudates are larger, fuzzy areas (subtract hard exudates to find remaining fluffy cotton-wool spots)
    soft_diff = cv2.subtract(soft_binary, hard_cleaned)
    kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    soft_cleaned = cv2.morphologyEx(soft_diff, cv2.MORPH_OPEN, kernel_large)

    if mask is not None:
        total_retina_pixels = np.sum(mask > 0)
        hard_area_pct = float(np.sum(hard_cleaned > 0) / total_retina_pixels * 100.0) if total_retina_pixels > 0 else 0.0
    else:
        hard_area_pct = float(np.sum(hard_cleaned > 0) / (image_rgb.shape[0] * image_rgb.shape[1]) * 100.0)

    return hard_cleaned, soft_cleaned, hard_area_pct
