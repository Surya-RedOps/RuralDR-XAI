"""
Unit Tests for Lesion Detection Engines
"""

import cv2
import numpy as np
import pytest

from src.core.contracts import RetinalAnatomy
from src.lesions.detector import LesionEvidenceDetector
from src.lesions.microaneurysms import detect_microaneurysms
from src.lesions.exudates import segment_exudates
from src.lesions.hemorrhages import segment_hemorrhages


@pytest.fixture
def lesion_canvas():
    """Generates synthetic fundus with artificial microaneurysms and exudates."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    retina_mask = np.sqrt((x - 256)**2 + (y - 256)**2) <= 230
    img[retina_mask] = [170, 80, 30]

    # Add 4 Microaneurysms (small dark red dots: 2-3px radius)
    cv2.circle(img, (280, 200), 2, (60, 20, 10), -1)
    cv2.circle(img, (300, 220), 3, (60, 20, 10), -1)
    cv2.circle(img, (270, 320), 2, (60, 20, 10), -1)
    cv2.circle(img, (320, 310), 3, (60, 20, 10), -1)

    # Add Hard Exudates (bright yellow patches)
    cv2.circle(img, (340, 250), 10, (230, 220, 100), -1)
    cv2.circle(img, (360, 260), 8, (230, 220, 100), -1)

    mask = retina_mask.astype(np.uint8) * 255
    return img, mask


def test_microaneurysm_detection(lesion_canvas):
    img, mask = lesion_canvas
    ma_mask, candidates = detect_microaneurysms(img, mask=mask)
    assert len(candidates) >= 1, "Should detect at least one microaneurysm candidate."


def test_exudate_segmentation(lesion_canvas):
    img, mask = lesion_canvas
    hard_mask, soft_mask, area_pct = segment_exudates(img, mask=mask)
    assert np.sum(hard_mask > 0) > 0, "Hard exudate mask should segment bright yellow clusters."
    assert area_pct > 0.0, "Hard exudate area percentage should be positive."


def test_lesion_orchestrator(lesion_canvas):
    img, mask = lesion_canvas
    anatomy = RetinalAnatomy(
        optic_disc_center=(160, 256),
        optic_disc_radius=30.0,
        fovea_center=(300, 256),
    )
    detector = LesionEvidenceDetector()
    inventory, masks = detector.detect(img, anatomy, mask=mask)

    assert inventory.microaneurysms_count >= 1
    assert inventory.hard_exudates_area_pct > 0.0
    assert "combined_lesions" in masks
