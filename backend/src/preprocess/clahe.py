"""
Contrast Limited Adaptive Histogram Equalization (CLAHE) for Fundus Images
"""

import cv2
import numpy as np


def apply_green_clahe(image_rgb: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)) -> np.ndarray:
    """
    Applies CLAHE specifically to the green channel of an RGB fundus image.
    The green channel exhibits optimal contrast between hemoglobin/vessels/lesions
    and retinal pigment epithelium background.
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    r, g, b = cv2.split(image_rgb)
    g_enhanced = clahe.apply(g)
    enhanced_rgb = cv2.merge([r, g_enhanced, b])
    return enhanced_rgb


def apply_lab_clahe(image_rgb: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)) -> np.ndarray:
    """
    Applies CLAHE to the L* (luminance) channel in Lab color space.
    Enhances contrast while preserving natural retinal chromatic balance.
    """
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_enhanced = clahe.apply(l)
    enhanced_lab = cv2.merge([l_enhanced, a, b])
    enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
    return enhanced_rgb
