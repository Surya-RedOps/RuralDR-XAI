"""
Fundus Illumination, Exposure, and Artifact Assessment
"""

import cv2
import numpy as np


def compute_shannon_entropy(image_rgb: np.ndarray, mask: np.ndarray = None) -> float:
    """
    Computes Shannon entropy of pixel intensity distribution on the green channel.
    Well-illuminated images have high entropy (rich diagnostic gradient variation).
    """
    if image_rgb.ndim == 3:
        green = image_rgb[:, :, 1]
    else:
        green = image_rgb

    if mask is not None and np.sum(mask > 0) > 0:
        pixels = green[mask > 0]
    else:
        pixels = green.ravel()

    hist, _ = np.histogram(pixels, bins=256, range=(0, 256), density=True)
    hist = hist[hist > 0]
    entropy = float(-np.sum(hist * np.log2(hist)))
    return entropy


def compute_exposure_and_glare(image_rgb: np.ndarray, mask: np.ndarray = None) -> dict:
    """
    Evaluates underexposure, overexposure, glare artifacts, and illumination uniformity.
    """
    if image_rgb.ndim == 3:
        hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        v_channel = hsv[:, :, 2]
    else:
        v_channel = image_rgb

    if mask is not None and np.sum(mask > 0) > 0:
        valid_v = v_channel[mask > 0]
    else:
        valid_v = v_channel.ravel()

    if len(valid_v) == 0:
        return {
            "mean_luminance": 0.0,
            "underexposed_ratio": 1.0,
            "overexposed_ratio": 0.0,
            "glare_artifact_score": 1.0,
            "illumination_uniformity": 0.0,
            "color_distortion_score": 1.0,
        }

    # Underexposure: percentage of pixels with luminance < 25 (out of 255)
    underexposed_ratio = float(np.sum(valid_v < 25) / len(valid_v))
    # Overexposure / Glare: percentage of pixels with luminance > 245
    overexposed_ratio = float(np.sum(valid_v > 245) / len(valid_v))
    mean_luminance = float(np.mean(valid_v))

    # Glare artifact penalty is high if overexposed patches exist in the retinal center
    glare_score = float(np.clip(overexposed_ratio * 6.0, 0.0, 1.0))

    # Illumination uniformity across retinal quadrants
    if mask is not None and np.sum(mask > 0) > 0:
        h, w = v_channel.shape[:2]
        mid_y, mid_x = h // 2, w // 2
        quad_means = []
        for (y1, y2, x1, x2) in [(0, mid_y, 0, mid_x), (0, mid_y, mid_x, w),
                                 (mid_y, h, 0, mid_x), (mid_y, h, mid_x, w)]:
            q_mask = mask[y1:y2, x1:x2] > 0
            if np.sum(q_mask) > 50:
                quad_means.append(np.mean(v_channel[y1:y2, x1:x2][q_mask]))
        if len(quad_means) >= 2:
            uniformity = float(np.clip(1.0 - (np.std(quad_means) / (np.mean(quad_means) + 1e-5)), 0.0, 1.0))
        else:
            uniformity = 1.0
    else:
        uniformity = 1.0

    # Color distortion check (abnormal channel dominance or complete color collapse)
    color_distortion = 0.0
    if image_rgb.ndim == 3 and mask is not None and np.sum(mask > 0) > 0:
        r = image_rgb[:, :, 0][mask > 0].astype(np.float32)
        g = image_rgb[:, :, 1][mask > 0].astype(np.float32)
        b = image_rgb[:, :, 2][mask > 0].astype(np.float32)
        mean_r, mean_g, mean_b = np.mean(r), np.mean(g), np.mean(b)
        # Fundus images are predominantly reddish-orange (R >= G > B).
        # Check for abnormal inversion or zero green/red channels
        if mean_g < 5.0 and mean_r < 5.0:
            color_distortion = 1.0
        elif mean_b > mean_r + 50:  # Excessive unnatural blue tint
            color_distortion = 0.8

    return {
        "mean_luminance": mean_luminance,
        "underexposed_ratio": underexposed_ratio,
        "overexposed_ratio": overexposed_ratio,
        "glare_artifact_score": glare_score,
        "illumination_uniformity": uniformity,
        "color_distortion_score": color_distortion,
    }

