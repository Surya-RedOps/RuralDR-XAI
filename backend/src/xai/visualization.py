"""
XAI Saliency & Lesion Overlay Visualizations
Blends Grad-CAM heatmaps, lesion contours, and anatomical landmarks over fundus images.
"""

from typing import Dict, Optional, Tuple
from pathlib import Path
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


def create_gradcam_panel(
    image_rgb: np.ndarray,
    heatmap: np.ndarray,
    class_name: str = "",
    confidence: float = 0.0,
    alpha: float = 0.45,
) -> np.ndarray:
    """
    Creates a side-by-side panel: [Original | Grad-CAM Overlay].

    Args:
        image_rgb: Original RGB image (H, W, 3)
        heatmap: Grad-CAM heatmap (H, W) float32 [0, 1]
        class_name: Label for the predicted class
        confidence: Classification confidence
        alpha: Overlay blend factor

    Returns:
        panel: (H, W*2, 3) RGB image with both views side by side
    """
    h, w = image_rgb.shape[:2]
    overlay = overlay_heatmap(image_rgb, heatmap, alpha=alpha)

    # Add text labels
    original_labeled = image_rgb.copy()
    overlay_labeled = overlay.copy()

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.4, h / 800.0)
    thickness = max(1, int(h / 400))

    cv2.putText(original_labeled, "Original", (10, 30),
                font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    cam_label = "Grad-CAM Attention"
    if class_name:
        cam_label += f" | {class_name}"
    if confidence > 0:
        cam_label += f" ({confidence:.1%})"
    cv2.putText(overlay_labeled, cam_label, (10, 30),
                font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    panel = np.concatenate([original_labeled, overlay_labeled], axis=1)
    return panel


def save_gradcam_outputs(
    image_rgb: np.ndarray,
    heatmap: np.ndarray,
    binary_mask: np.ndarray,
    output_dir: str,
    prefix: str = "gradcam",
    class_name: str = "",
    confidence: float = 0.0,
) -> Dict[str, str]:
    """
    Saves Grad-CAM outputs to disk.

    Returns:
        Dict with keys: 'original', 'heatmap', 'overlay', 'binary_mask', 'panel'
        mapping to saved file paths.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = {}

    # Save original
    orig_path = out / f"{prefix}_original.jpg"
    cv2.imwrite(str(orig_path), cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
    paths["original"] = str(orig_path)

    # Save heatmap as colorized image
    heatmap_uint8 = np.uint8(255 * np.clip(heatmap, 0.0, 1.0))
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    heatmap_path = out / f"{prefix}_heatmap.png"
    cv2.imwrite(str(heatmap_path), heatmap_colored)
    paths["heatmap"] = str(heatmap_path)

    # Save overlay
    overlay = overlay_heatmap(image_rgb, heatmap, alpha=0.45)
    overlay_path = out / f"{prefix}_overlay.jpg"
    cv2.imwrite(str(overlay_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
    paths["overlay"] = str(overlay_path)

    # Save binary mask
    mask_path = out / f"{prefix}_mask.png"
    cv2.imwrite(str(mask_path), binary_mask)
    paths["binary_mask"] = str(mask_path)

    # Save side-by-side panel
    panel = create_gradcam_panel(image_rgb, heatmap, class_name, confidence)
    panel_path = out / f"{prefix}_panel.jpg"
    cv2.imwrite(str(panel_path), cv2.cvtColor(panel, cv2.COLOR_RGB2BGR))
    paths["panel"] = str(panel_path)

    return paths


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
