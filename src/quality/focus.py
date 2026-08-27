"""
Fundus Focus and Sharpness Assessment
Computes Tenengrad gradient and Laplacian variance on the green channel.
"""

import cv2
import numpy as np


def compute_tenengrad(image_rgb: np.ndarray, mask: np.ndarray = None) -> float:
    """
    Computes Tenengrad focus metric using Sobel gradient magnitude on the green channel.
    High values indicate sharp edges and well-focused fundus anatomy.
    """
    if image_rgb.ndim == 3:
        green = image_rgb[:, :, 1]
    else:
        green = image_rgb

    sobel_x = cv2.Sobel(green, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(green, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag_sq = sobel_x**2 + sobel_y**2

    if mask is not None and np.sum(mask > 0) > 0:
        valid_pixels = mask > 0
        tenengrad = float(np.mean(grad_mag_sq[valid_pixels]))
    else:
        tenengrad = float(np.mean(grad_mag_sq))

    return tenengrad


def compute_laplacian_variance(image_rgb: np.ndarray, mask: np.ndarray = None) -> float:
    """
    Computes modified Laplacian variance for blur detection.
    """
    if image_rgb.ndim == 3:
        green = image_rgb[:, :, 1]
    else:
        green = image_rgb

    laplacian = cv2.Laplacian(green, cv2.CV_64F)
    if mask is not None and np.sum(mask > 0) > 0:
        valid_pixels = mask > 0
        var_lap = float(np.var(laplacian[valid_pixels]))
    else:
        var_lap = float(np.var(laplacian))

    return var_lap
