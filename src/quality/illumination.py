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
    Evaluates underexposure, overexposure, and glare artifacts using HSV and Lab color spaces.
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
            "glare_artifact_score": 0.0,
        }

    # Underexposure: percentage of pixels with luminance < 25 (out of 255)
    underexposed_ratio = float(np.sum(valid_v < 25) / len(valid_v))
    # Overexposure / Glare: percentage of pixels with luminance > 245
    overexposed_ratio = float(np.sum(valid_v > 245) / len(valid_v))
    mean_luminance = float(np.mean(valid_v))

    # Glare artifact penalty is high if overexposed patches exist in the retinal center
    glare_score = float(np.clip(overexposed_ratio * 5.0, 0.0, 1.0))

    return {
        "mean_luminance": mean_luminance,
        "underexposed_ratio": underexposed_ratio,
        "overexposed_ratio": overexposed_ratio,
        "glare_artifact_score": glare_score,
    }
