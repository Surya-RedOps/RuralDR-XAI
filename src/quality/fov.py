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
    Standard 45-50 degree fundus cameras cover 60%-85% of standard square canvas.
    """
    if mask is None:
        mask = extract_retinal_mask(image_rgb)

    total_pixels = image_rgb.shape[0] * image_rgb.shape[1]
    foreground_pixels = np.sum(mask > 0)
    coverage = float(foreground_pixels / total_pixels)
    return coverage
