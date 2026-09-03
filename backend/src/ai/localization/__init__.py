"""
Retina AI: Localization Subsystem
Locates anatomical landmarks including the Optic Disc and Foveal Avascular Zone.
Includes IDRiD localization dataset loading for future model training.
"""

from ...anatomy.optic_disc import locate_optic_disc
from ...anatomy.fovea import locate_fovea
from .dataset import load_optic_disc_centers, load_fovea_centers, build_localization_manifest

__all__ = [
    "locate_optic_disc",
    "locate_fovea",
    "load_optic_disc_centers",
    "load_fovea_centers",
    "build_localization_manifest",
]
