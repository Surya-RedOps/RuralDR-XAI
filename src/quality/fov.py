"""
Fundus Field of View (FOV) and Retinal Mask Extraction
"""

import cv2
import numpy as np


def extract_retinal_mask(image_rgb: np.ndarray, threshold: int = 15) -> np.ndarray:
    """
    Extracts the circular/elliptical retinal field-of-view mask.
    Removes black camera background borders.
    """
    if image_rgb.ndim == 3:
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_rgb

    # Threshold dark borders
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

    # Morphological closing and largest connected component
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed)
    if num_labels <= 1:
        return np.ones(gray.shape, dtype=np.uint8) * 255

    # Largest foreground component
    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    mask = np.zeros(gray.shape, dtype=np.uint8)
    mask[labels == largest_label] = 255

    # Fill holes inside retina
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)

    return mask


def compute_fov_coverage(image_rgb: np.ndarray, mask: np.ndarray = None) -> float:
    """
    Computes ratio of valid retinal area relative to total image canvas.
    Standard 45-50 degree fundus cameras cover 45%-85% of standard canvas.
    """
    if mask is None:
        mask = extract_retinal_mask(image_rgb)

    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]
    if total_pixels == 0:
        return 0.0
    foreground_pixels = np.sum(mask > 0)
    coverage = float(foreground_pixels / total_pixels)
    return coverage


def compute_fov_metrics(image_rgb: np.ndarray, mask: np.ndarray = None) -> dict:
    """
    Computes comprehensive FOV metrics including coverage, centering offset, and bounding box geometry.
    """
    if mask is None:
        mask = extract_retinal_mask(image_rgb)

    h, w = image_rgb.shape[:2]
    total_pixels = h * w
    if total_pixels == 0:
        return {
            "fov_coverage": 0.0,
            "centering_offset": 1.0,
            "aspect_ratio": 0.0,
            "has_adequate_retina": False,
        }

    foreground_pixels = int(np.sum(mask > 0))
    coverage = float(foreground_pixels / total_pixels)

    if foreground_pixels < 100:
        return {
            "fov_coverage": coverage,
            "centering_offset": 1.0,
            "aspect_ratio": 0.0,
            "has_adequate_retina": False,
        }

    # Centroid and Centering Offset
    moments = cv2.moments(mask)
    if moments["m00"] > 0:
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
        # Distance from canvas center normalized by half diagonal
        center_x, center_y = w / 2.0, h / 2.0
        dist = np.sqrt((cx - center_x) ** 2 + (cy - center_y) ** 2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        centering_offset = float(dist / max_dist) if max_dist > 0 else 0.0
    else:
        centering_offset = 1.0

    # Bounding box and aspect ratio
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        x, y, bw, bh = cv2.boundingRect(np.vstack(contours))
        aspect_ratio = float(min(bw, bh) / max(bw, bh)) if max(bw, bh) > 0 else 0.0
    else:
        aspect_ratio = 0.0

    # Adequate retina if coverage is above minimum threshold and aspect ratio is reasonably circular
    has_adequate_retina = bool(coverage >= 0.30 and centering_offset < 0.60 and aspect_ratio > 0.40)

    return {
        "fov_coverage": coverage,
        "centering_offset": centering_offset,
        "aspect_ratio": aspect_ratio,
        "has_adequate_retina": has_adequate_retina,
    }

