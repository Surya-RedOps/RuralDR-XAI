"""
Unit Tests for Image Quality Gate (FIQA)
"""

import numpy as np
import pytest

from src.core.contracts import QualityStatus
from src.quality.gate import ImageQualityGate
from src.quality.focus import compute_tenengrad, compute_laplacian_variance
from src.quality.illumination import compute_shannon_entropy, compute_exposure_and_glare
from src.quality.fov import compute_fov_coverage, extract_retinal_mask


@pytest.fixture
def sample_fundus_image():
    """Generates a synthetic circular disc image with natural gradient variation strictly for unit tests."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    dist_from_center = np.sqrt((x - 256)**2 + (y - 256)**2)
    retina_mask = dist_from_center <= 220
    
    # Smooth radial intensity gradient
    gradient = np.clip(180 - dist_from_center * 0.4, 40, 200).astype(np.uint8)
    img[retina_mask, 0] = gradient[retina_mask]
    img[retina_mask, 1] = (gradient[retina_mask] * 0.55).astype(np.uint8)
    img[retina_mask, 2] = (gradient[retina_mask] * 0.25).astype(np.uint8)

    # Add artificial vessels and texture for focus test
    img[240:270, 200:300, 1] = 20  # Dark vessel pattern
    return img


@pytest.fixture
def blurry_image():
    """Generates a severely defocused/blurred, low-contrast ungradable image."""
    img = np.ones((512, 512, 3), dtype=np.uint8) * 60
    # No sharp edges anywhere
    return img


@pytest.fixture
def dark_image():
    """Generates a flat underexposed near-black image."""
    return np.zeros((512, 512, 3), dtype=np.uint8)


def test_focus_metrics(sample_fundus_image, blurry_image):
    sharp_ten = compute_tenengrad(sample_fundus_image)
    blurry_ten = compute_tenengrad(blurry_image)
    assert sharp_ten > blurry_ten, "Sharp image should have higher Tenengrad focus score."


def test_illumination_entropy(sample_fundus_image, dark_image):
    entropy_normal = compute_shannon_entropy(sample_fundus_image)
    entropy_dark = compute_shannon_entropy(dark_image)
    assert entropy_normal > entropy_dark, "Normal image should have higher Shannon entropy than near-black image."


def test_fov_coverage(sample_fundus_image):
    mask = extract_retinal_mask(sample_fundus_image)
    coverage = compute_fov_coverage(sample_fundus_image, mask)
    assert 0.50 <= coverage <= 0.85, f"Expected circular mask coverage in [0.50, 0.85], got {coverage}"


def test_quality_gate_ungradable(blurry_image):
    gate = ImageQualityGate()
    metrics = gate.evaluate(blurry_image)
    assert metrics.status in [QualityStatus.UNGRADABLE, QualityStatus.BORDERLINE]
    assert len(metrics.recapture_advice) > 0, "Quality gate must provide actionable recapture advice on failure."
