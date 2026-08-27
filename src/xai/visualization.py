"""
XAI Saliency & Lesion Overlay Visualizations
Blends Grad-CAM heatmaps, lesion contours, and anatomical landmarks over fundus images.
"""

from typing import Dict, Optional, Tuple
import cv2
import numpy as np

from ..core.contracts import RetinalAnatomy, LesionInventory


def overlay_heatmap(
    image_rgb: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.45,
    colormap: int = cv2.COLORMAP_JET,
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Blends a 2D float [0, 1] heatmap over an RGB fundus image.
    """
    h, w = image_rgb.shape[:2]
    if heatmap.shape[:2] != (h, w):
        heatmap = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)

    heatmap_uint8 = np.uint8(255 * np.clip(heatmap, 0.0, 1.0))
    colored_heatmap = cv2.applyColorMap(heatmap_uint8, colormap)
    colored_heatmap = cv2.cvtColor(colored_heatmap, cv2.COLOR_BGR2RGB)

    blended = cv2.addWeighted(image_rgb, 1.0 - alpha, colored_heatmap, alpha, 0)
    if mask is not None:
        blended = cv2.bitwise_and(blended, blended, mask=mask)
    return blended


def create_comprehensive_annotated_fundus(
    image_rgb: np.ndarray,
    anatomy: RetinalAnatomy,
    lesion_masks: Dict[str, np.ndarray],
    heatmap: Optional[np.ndarray] = None,
    show_anatomy: bool = True,
    show_lesions: bool = True,
    show_cam: bool = True,
) -> np.ndarray:
    """
    Creates a full clinical multi-layer annotation display.
    """
    canvas = image_rgb.copy()
    h, w = canvas.shape[:2]

    # 1. Grad-CAM layer
    if show_cam and heatmap is not None:
        canvas = overlay_heatmap(canvas, heatmap, alpha=0.35)

    # 2. Lesion Overlays:
    # - Microaneurysms: Red dots
    # - Hard Exudates: Bright yellow contours
    # - Soft Exudates: Cyan contours
    # - Hemorrhages: Magenta contours
    if show_lesions:
        if "hard_exudates" in lesion_masks and np.sum(lesion_masks["hard_exudates"] > 0) > 0:
            contours, _ = cv2.findContours(lesion_masks["hard_exudates"], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(canvas, contours, -1, (255, 255, 0), thickness=2)  # Yellow

        if "soft_exudates" in lesion_masks and np.sum(lesion_masks["soft_exudates"] > 0) > 0:
            contours, _ = cv2.findContours(lesion_masks["soft_exudates"], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(canvas, contours, -1, (0, 255, 255), thickness=2)  # Cyan

        if "hemorrhages" in lesion_masks and np.sum(lesion_masks["hemorrhages"] > 0) > 0:
            contours, _ = cv2.findContours(lesion_masks["hemorrhages"], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(canvas, contours, -1, (255, 0, 255), thickness=2)  # Magenta

        if "microaneurysms" in lesion_masks and np.sum(lesion_masks["microaneurysms"] > 0) > 0:
            contours, _ = cv2.findContours(lesion_masks["microaneurysms"], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                (x, y), radius = cv2.minEnclosingCircle(cnt)
                cv2.circle(canvas, (int(x), int(y)), int(max(3, radius + 1)), (255, 0, 0), thickness=2)  # Red circle

    # 3. Anatomy Overlays:
    # - Optic Disc: Green circle
    # - Fovea: Blue target crosshair
    if show_anatomy:
        if anatomy.optic_disc_center is not None and anatomy.optic_disc_radius is not None:
            cx, cy = anatomy.optic_disc_center
            r = int(anatomy.optic_disc_radius)
            cv2.circle(canvas, (cx, cy), r, (0, 255, 0), thickness=2)
            cv2.putText(canvas, "OD", (cx - 15, cy - r - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        if anatomy.fovea_center is not None:
            fx, fy = anatomy.fovea_center
            # Draw crosshair
            cv2.drawMarker(canvas, (fx, fy), (0, 140, 255), markerType=cv2.MARKER_CROSS, markerSize=18, thickness=2)
            cv2.putText(canvas, "Fovea", (fx + 10, fy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)

    return canvas
