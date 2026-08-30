"""
Retina AI: Localization Subsystem
Locates anatomical landmarks including the Optic Disc and Foveal Avascular Zone.
"""

from ...anatomy.optic_disc import locate_optic_disc
from ...anatomy.fovea import locate_fovea

__all__ = [
    "locate_optic_disc",
    "locate_fovea",
]
