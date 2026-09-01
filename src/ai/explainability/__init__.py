"""
Retina AI: Explainability Subsystem (XAI)
Generates Grad-CAM, Grad-CAM++, and Score-CAM class activation maps, visualization overlays,
and the combined explainability pipeline.
"""

from ...xai.gradcam import GradCAM
from ...xai.scorecam import ScoreCAM
from ...xai.visualization import overlay_heatmap, create_comprehensive_annotated_fundus
from .pipeline import ExplainableScreeningPipeline
from .evidence import generate_evidence_report

__all__ = [
    "GradCAM",
    "ScoreCAM",
    "overlay_heatmap",
    "create_comprehensive_annotated_fundus",
    "ExplainableScreeningPipeline",
    "generate_evidence_report",
]
