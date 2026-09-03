"""
Unit Tests for Retinal Anatomy Engine
"""

import cv2
import numpy as np
import pytest

from src.anatomy.vessel_filter import segment_retinal_vessels
from src.anatomy.optic_disc import locate_optic_disc
from src.anatomy.fovea import locate_fovea


@pytest.fixture
def synthetic_retina():
    """Generates synthetic fundus canvas with optic disc and vessels for algorithm unit verification."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    retina_mask = np.sqrt((x - 256)**2 + (y - 256)**2) <= 230
    img[retina_mask] = [170, 80, 30]

    # Draw Optic Disc at (160, 256) with radius 35 (Bright yellow/white)
    cv2.circle(img, (160, 256), 35, (240, 230, 160), -1)

    # Draw dark vessels branching from disc
    cv2.line(img, (160, 256), (350, 200), (30, 20, 10), 4)
    cv2.line(img, (160, 256), (350, 310), (30, 20, 10), 4)

    mask = retina_mask.astype(np.uint8) * 255
    return img, mask


def test_optic_disc_localization(synthetic_retina):
    img, mask = synthetic_retina
    od_center, od_radius, od_bbox = locate_optic_disc(img, mask)

    assert od_center is not None, "Optic disc should be located."
    # Center should be near (160, 256)
    dist_error = np.sqrt((od_center[0] - 160)**2 + (od_center[1] - 256)**2)
    assert dist_error < 25, f"Expected OD center near (160, 256), got {od_center} (dist error: {dist_error})"


def test_fovea_localization(synthetic_retina):
    img, mask = synthetic_retina
    od_center = (160, 256)
    od_radius = 35.0
    fovea_center = locate_fovea(img, od_center, od_radius, mask=mask)

    assert fovea_center is not None, "Fovea center should be located."
    # Fovea should be to the right of OD (temporal offset ~ 2-3 disc diameters -> x ~ 280-360)
    assert fovea_center[0] > od_center[0], "Fovea must be positioned temporally relative to optic disc."


def test_vessel_segmentation(synthetic_retina):
    img, mask = synthetic_retina
    vessel_mask, density = segment_retinal_vessels(img, mask)

    assert vessel_mask.shape == (512, 512)
    assert np.sum(vessel_mask > 0) > 0, "Vessel mask should contain segmented vascular pixels."
    assert 0.0 < density < 0.35, f"Vessel density should be in reasonable physiological range, got {density}"
