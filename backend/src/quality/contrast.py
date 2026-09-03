"""
Retina AI: Retinal Contrast Quality Assessment
Measures RMS contrast and local dynamic range on the retinal field of view.
"""

import cv2
import numpy as np


def compute_retinal_contrast(image_rgb: np.ndarray, mask: np.ndarray = None) -> dict:
    """
    Computes RMS (Root Mean Square) contrast and percentile dynamic range on the green channel.
    """
    if image_rgb is None or image_rgb.size == 0:
        return {
            "rms_contrast": 0.0,
            "dynamic_range_p95_p5": 0.0,
            "contrast_score": 0.0,
        }

    if image_rgb.ndim == 3:
        green = image_rgb[:, :, 1]
    else:
        green = image_rgb


    if mask is not None and np.sum(mask > 0) > 0:
        valid_pixels = green[mask > 0].astype(np.float32)
    else:
        valid_pixels = green.ravel().astype(np.float32)

    if len(valid_pixels) == 0:
        return {
            "rms_contrast": 0.0,
            "dynamic_range_p95_p5": 0.0,
            "contrast_score": 0.0,
        }

    # RMS Contrast = standard deviation of pixel intensities
    rms_contrast = float(np.std(valid_pixels))

    # Dynamic Range (5th to 95th percentile intensity difference)
    p5 = np.percentile(valid_pixels, 5)
    p95 = np.percentile(valid_pixels, 95)
    dynamic_range = float(p95 - p5)

    # Normalized contrast score [0, 1] (normal fundus RMS contrast is typically 30-70)
    norm_contrast = float(np.clip(rms_contrast / 50.0, 0.0, 1.0))

    return {
        "rms_contrast": rms_contrast,
        "dynamic_range_p95_p5": dynamic_range,
        "contrast_score": norm_contrast,
    }
