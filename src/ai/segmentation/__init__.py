"""
Retina AI: Segmentation Subsystem
Provides vessel tree segmentation and morphological lesion detection (Microaneurysms, Exudates, Hemorrhages).
"""

from ...anatomy.vessel_filter import segment_retinal_vessels
from ...lesions.detector import LesionEvidenceDetector
from ...lesions.microaneurysms import detect_microaneurysms
from ...lesions.exudates import segment_exudates
from ...lesions.hemorrhages import segment_hemorrhages

__all__ = [
    "segment_retinal_vessels",
    "LesionEvidenceDetector",
    "detect_microaneurysms",
    "segment_exudates",
    "segment_hemorrhages",
]
