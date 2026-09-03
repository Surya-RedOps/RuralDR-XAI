from typing import Tuple, List, Optional
import cv2
import numpy as np


def detect_microaneurysms(
    image_rgb: np.ndarray,
    vessel_mask: Optional[np.ndarray] = None,
    optic_disc_mask: Optional[np.ndarray] = None,
    mask: Optional[np.ndarray] = None,
    min_radius: int = 1,
    max_radius: int = 6,
) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
    """
    Detects microaneurysms (MAs) on high-resolution fundus images.

    Returns:
        ma_mask: (H, W) binary uint8 mask {0, 255}
        ma_candidates: List of (x, y, radius) tuples
    """
    green = image_rgb[:, :, 1] if image_rgb.ndim == 3 else image_rgb

    # Apply CLAHE to green channel
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    g_enh = clahe.apply(green)

    # Morphological Bottom-Hat to extract small dark lesions
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max_radius * 2 + 1, max_radius * 2 + 1))
    bothat = cv2.morphologyEx(g_enh, cv2.MORPH_BLACKHAT, kernel)

    # Threshold bottom-hat image
    if mask is not None:
        valid_bothat = bothat[mask > 0]
        thresh_val = np.percentile(valid_bothat, 98.0) if len(valid_bothat) > 0 else 15
    else:
        thresh_val = np.percentile(bothat, 98.0)

    _, binary_ma = cv2.threshold(bothat, int(thresh_val), 255, cv2.THRESH_BINARY)

    # Subtract vessel tree (dilated by 2 pixels to prevent vessel edge artifacts)
    if vessel_mask is not None:
        dilated_vessels = cv2.dilate(vessel_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        binary_ma[dilated_vessels > 0] = 0

    # Subtract Optic Disc
    if optic_disc_mask is not None:
        binary_ma[optic_disc_mask > 0] = 0

    # Subtract non-retinal background boundary
    if mask is not None:
        eroded_mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        binary_ma[eroded_mask == 0] = 0

    # Connected component analysis for size and circularity filtering
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_ma)
    filtered_mask = np.zeros(green.shape, dtype=np.uint8)
    candidates = []

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        # Size constraints (typical MA: 2 to 30 pixels on 512x512)
        if 2 <= area <= 40:
            aspect_ratio = float(w) / float(h) if h > 0 else 0
            if 0.4 <= aspect_ratio <= 2.5:  # Circularity test
                cx, cy = int(centroids[i][0]), int(centroids[i][1])
                r = int(np.ceil(np.sqrt(area / np.pi)))
                filtered_mask[labels == i] = 255
                candidates.append((cx, cy, r))

    return filtered_mask, candidates
