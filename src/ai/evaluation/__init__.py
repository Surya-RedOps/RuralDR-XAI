"""
Retina AI: Evaluation & Consistency Subsystem
Evaluates clinical rule concordance between Grad-CAM attributions and lesion segmentations, and orchestrates the full pipeline.
"""

from ...engine.consistency import EvidenceConsistencyEngine
from ...engine.orchestrator import ScreeningOrchestrator

__all__ = [
    "EvidenceConsistencyEngine",
    "ScreeningOrchestrator",
]
