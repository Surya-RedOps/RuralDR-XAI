from typing import Tuple, List, Optional
import cv2
import numpy as np


def segment_hemorrhages(
    image_rgb: np.ndarray,
    vessel_mask: Optional[np.ndarray] = None,
    optic_disc_mask: Optional[np.ndarray] = None,
    mask: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, int, float]:
    """
    Segments intraretinal hemorrhages.

    Returns:
        he_mask: (H, W) binary uint8 mask {0, 255}
        he_count: int count of discrete hemorrhage regions
        he_area_pct: float percentage of retinal area
    """
    if image_rgb.ndim != 3:
        raise ValueError("Hemorrhage detection requires 3-channel RGB image.")

    r, g, b = cv2.split(image_rgb)

    # Hemorrhages appear dark in green channel and have distinct absorption compared to background
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    g_enh = clahe.apply(g)

    # Ratio of green to red channel highlights blood lesions
    r_float = np.maximum(r.astype(np.float32), 1.0)
    g_float = g_enh.astype(np.float32)
    rg_ratio = g_float / r_float

    # Dark blood lesions have low ratio and low green intensity
    if mask is not None:
        valid_pixels = mask > 0
        valid_vals = g_float[valid_pixels]
        thresh_g = np.percentile(valid_vals, 6.0) if len(valid_vals) > 0 else 40
    else:
        thresh_g = np.percentile(g_float, 6.0)

    binary_he = ((g_float <= thresh_g) & (rg_ratio < 0.85)).astype(np.uint8) * 255

    # Subtract vessel tree (dilated by 2 pixels)
    if vessel_mask is not None:
        dilated_vessels = cv2.dilate(vessel_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        binary_he[dilated_vessels > 0] = 0

    # Subtract Optic Disc
    if optic_disc_mask is not None:
        binary_he[optic_disc_mask > 0] = 0

    # Subtract border
    if mask is not None:
        eroded_mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        binary_he[eroded_mask == 0] = 0

    # Clean isolated noise and connect clusters
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(binary_he, cv2.MORPH_OPEN, kernel)

    # Connected component analysis (hemorrhages are larger than MAs: area >= 15)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned)
    final_he_mask = np.zeros(g.shape, dtype=np.uint8)
    he_count = 0

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= 12:  # Hemorrhage minimum area threshold
            final_he_mask[labels == i] = 255
            he_count += 1

    if mask is not None:
        total_retina_pixels = np.sum(mask > 0)
        he_area_pct = float(np.sum(final_he_mask > 0) / total_retina_pixels * 100.0) if total_retina_pixels > 0 else 0.0
    else:
        he_area_pct = float(np.sum(final_he_mask > 0) / (image_rgb.shape[0] * image_rgb.shape[1]) * 100.0)

    return final_he_mask, he_count, he_area_pct
