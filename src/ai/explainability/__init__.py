"""
Retina AI: Explainability Subsystem (XAI)
Generates Grad-CAM, Grad-CAM++, and Score-CAM class activation maps and visualization overlays.
"""

from ...xai.gradcam import GradCAM
from ...xai.scorecam import ScoreCAM
from ...xai.visualization import overlay_heatmap, create_comprehensive_annotated_fundus

__all__ = [
    "GradCAM",
    "ScoreCAM",
    "overlay_heatmap",
    "create_comprehensive_annotated_fundus",
]
