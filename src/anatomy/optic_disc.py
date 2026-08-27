"""
Optic Disc (OD) Detection & Localization
Uses morphological Top-Hat filtering, intensity clustering, and Circular Hough Transform (CHT).
"""

from typing import Tuple, Optional
import cv2
import numpy as np


def locate_optic_disc(
    image_rgb: np.ndarray,
    mask: Optional[np.ndarray] = None,
) -> Tuple[Optional[Tuple[int, int]], Optional[float], Optional[Tuple[int, int, int, int]]]:
    """
    Locates the Optic Disc center coordinate, radius, and bounding box.

    Returns:
        center: (x, y) or None
        radius: float or None
        bbox: (xmin, ymin, xmax, ymax) or None
    """
    if image_rgb.ndim == 3:
        # Red channel has high optic disc reflectivity and lower vascular attenuation
        red = image_rgb[:, :, 0]
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    else:
        red = image_rgb
        gray = image_rgb

    # Morphological Top-Hat to highlight bright circular structures
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    tophat = cv2.morphologyEx(red, cv2.MORPH_TOPHAT, kernel)

    # Blend red channel with Top-Hat
    combined = cv2.addWeighted(red, 0.7, tophat, 0.3, 0)
    if mask is not None:
        combined = cv2.bitwise_and(combined, combined, mask=mask)

    # Blur to smooth vessel bifurcations across the disc
    blurred = cv2.GaussianBlur(combined, (15, 15), 0)

    # Find highest intensity candidate region
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred)

    # Circular Hough Transform around expected disc radius (typically ~30-65 pixels on 512x512)
    h, w = gray.shape[:2]
    min_radius = int(w * 0.04)
    max_radius = int(w * 0.12)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_radius * 2,
        param1=50,
        param2=25,
        minRadius=min_radius,
        maxRadius=max_radius,
    )

    if circles is not None and len(circles) > 0:
        circles = np.round(circles[0, :]).astype("int")
        # Choose circle closest to maximum intensity region
        best_circle = None
        min_dist = float("inf")
        for x, y, r in circles:
            dist = np.sqrt((x - max_loc[0]) ** 2 + (y - max_loc[1]) ** 2)
            if dist < min_dist:
                min_dist = dist
                best_circle = (int(x), int(y), float(r))

        if best_circle is not None:
            cx, cy, r = best_circle
            bbox = (
                max(0, int(cx - r)),
                max(0, int(cy - r)),
                min(w, int(cx + r)),
                min(h, int(cy + r)),
            )
            return (cx, cy), r, bbox

    # Fallback to centroid of brightest cluster if Hough fails
    _, thresh = cv2.threshold(blurred, int(max_val * 0.85), 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        (cx, cy), radius = cv2.minEnclosingCircle(largest)
        r = float(max(min_radius, min(max_radius, radius)))
        cx, cy = int(cx), int(cy)
        bbox = (
            max(0, int(cx - r)),
            max(0, int(cy - r)),
            min(w, int(cx + r)),
            min(h, int(cy + r)),
        )
        return (cx, cy), r, bbox

    return None, None, None
