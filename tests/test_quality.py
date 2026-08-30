"""
Retina AI: Unit & Integration Tests for Image Quality Gate (FIQA) & Adaptive Enhancement (Phase 3)
"""

import cv2
import numpy as np
import pytest

from src.core.contracts import QualityStatus
from src.quality.gate import ImageQualityGate
from src.quality.focus import compute_tenengrad, compute_laplacian_variance
from src.quality.illumination import compute_shannon_entropy, compute_exposure_and_glare
from src.quality.fov import compute_fov_coverage, extract_retinal_mask, compute_fov_metrics
from src.quality.contrast import compute_retinal_contrast
from src.preprocess.enhance import AdaptiveEnhancer
from src.ai.image_quality.pipeline import assess_image_quality, process_retinal_image


@pytest.fixture
def sample_fundus_image():
    """Generates a synthetic circular fundus image with natural gradient and vessel structure."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    dist_from_center = np.sqrt((x - 256)**2 + (y - 256)**2)
    retina_mask = dist_from_center <= 220

    # Smooth radial intensity gradient mimicking retinal illumination
    gradient = np.clip(180 - dist_from_center * 0.35, 50, 210).astype(np.uint8)
    img[retina_mask, 0] = gradient[retina_mask]
    img[retina_mask, 1] = (gradient[retina_mask] * 0.60).astype(np.uint8)
    img[retina_mask, 2] = (gradient[retina_mask] * 0.25).astype(np.uint8)

    # Add artificial vessel patterns for high-frequency focus/texture
    for offset in range(-60, 60, 15):
        rr = np.clip(256 + offset, 0, 511)
        img[rr : rr + 4, 150:360, 1] = 25
        img[150:360, rr : rr + 4, 1] = 25

    return img


@pytest.fixture
def blurry_image():
    """Generates a severely defocused/blurred, uniform ungradable image."""
    img = np.ones((512, 512, 3), dtype=np.uint8) * 70
    return img


@pytest.fixture
def dark_image():
    """Generates a flat underexposed near-black image."""
    return np.zeros((512, 512, 3), dtype=np.uint8)


@pytest.fixture
def glare_image(sample_fundus_image):
    """Generates an image with severe corneal glare / specular reflection artifact."""
    img = sample_fundus_image.copy()
    y, x = np.ogrid[:512, :512]
    glare_mask = ((x - 256)**2 + (y - 256)**2) <= 80**2
    img[glare_mask] = 255
    return img


@pytest.fixture
def off_center_image():
    """Generates a severely shifted/clipped retinal field."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    # Shifted to far corner
    dist = np.sqrt((x - 450)**2 + (y - 450)**2)
    retina_mask = dist <= 120
    img[retina_mask, 0] = 160
    img[retina_mask, 1] = 100
    img[retina_mask, 2] = 40
    return img


# =========================================================================
# STEP 3-7: QUALITY DIMENSION UNIT TESTS
# =========================================================================

def test_focus_metrics(sample_fundus_image, blurry_image):
    sharp_ten = compute_tenengrad(sample_fundus_image)
    blurry_ten = compute_tenengrad(blurry_image)
    assert sharp_ten > blurry_ten, "Sharp image should have higher Tenengrad focus score."

    sharp_lap = compute_laplacian_variance(sample_fundus_image)
    blurry_lap = compute_laplacian_variance(blurry_image)
    assert sharp_lap > blurry_lap, "Sharp image should have higher Laplacian variance."


def test_illumination_entropy(sample_fundus_image, dark_image):
    entropy_normal = compute_shannon_entropy(sample_fundus_image)
    entropy_dark = compute_shannon_entropy(dark_image)
    assert entropy_normal > entropy_dark, "Normal image should have higher Shannon entropy than near-black image."


def test_exposure_and_glare_metrics(sample_fundus_image, dark_image, glare_image):
    normal_exp = compute_exposure_and_glare(sample_fundus_image)
    dark_exp = compute_exposure_and_glare(dark_image)
    glare_exp = compute_exposure_and_glare(glare_image)

    assert dark_exp["underexposed_ratio"] > 0.80, "Dark image must report high underexposure."
    assert glare_exp["overexposed_ratio"] > 0.05, "Glare image must report high overexposure ratio."
    assert glare_exp["glare_artifact_score"] > normal_exp["glare_artifact_score"]


def test_fov_and_centering(sample_fundus_image, off_center_image):
    mask = extract_retinal_mask(sample_fundus_image)
    coverage = compute_fov_coverage(sample_fundus_image, mask)
    assert 0.45 <= coverage <= 0.85, f"Expected circular mask coverage in [0.45, 0.85], got {coverage}"

    fov_metrics_normal = compute_fov_metrics(sample_fundus_image)
    assert fov_metrics_normal["has_adequate_retina"] is True
    assert fov_metrics_normal["centering_offset"] < 0.20

    fov_metrics_offcenter = compute_fov_metrics(off_center_image)
    assert fov_metrics_offcenter["centering_offset"] > 0.40


def test_contrast_computation(sample_fundus_image, blurry_image):
    contrast_normal = compute_retinal_contrast(sample_fundus_image)
    contrast_flat = compute_retinal_contrast(blurry_image)
    assert contrast_normal["rms_contrast"] > contrast_flat["rms_contrast"]
    assert contrast_normal["dynamic_range_p95_p5"] > contrast_flat["dynamic_range_p95_p5"]


# =========================================================================
# STEP 8 & 14: QUALITY GATE & API EVALUATION
# =========================================================================

def test_quality_gate_acceptable(sample_fundus_image):
    gate = ImageQualityGate()
    metrics = gate.evaluate(sample_fundus_image)
    assert metrics.status == QualityStatus.GRADEABLE
    assert metrics.is_gradeable is True
    assert len(metrics.recapture_advice) == 0


def test_quality_gate_ungradable_blur(blurry_image):
    gate = ImageQualityGate()
    metrics = gate.evaluate(blurry_image)
    assert metrics.status == QualityStatus.UNGRADABLE
    assert metrics.is_gradeable is False
    assert any("focus" in adv.lower() for adv in metrics.recapture_advice)


def test_quality_gate_ungradable_dark(dark_image):
    gate = ImageQualityGate()
    metrics = gate.evaluate(dark_image)
    assert metrics.status == QualityStatus.UNGRADABLE
    assert metrics.is_gradeable is False
    assert len(metrics.recapture_advice) > 0


def test_assess_image_quality_api_schema(sample_fundus_image):
    res = assess_image_quality(sample_fundus_image)
    assert "quality_status" in res
    assert "quality_score" in res
    assert "quality_metrics" in res
    assert "issues" in res
    assert "recommendation" in res
    assert "evaluation_time_ms" in res
    assert res["quality_status"] in ["acceptable", "borderline", "ungradable"]
    assert 0.0 <= res["quality_score"] <= 1.0


# =========================================================================
# STEP 10, 11, 12: BORDERLINE ENHANCEMENT & BEFORE/AFTER VALIDATION
# =========================================================================

def test_borderline_enhancement_and_recheck():
    """Simulates a borderline low-contrast fundus image rescued by adaptive CLAHE."""
    # Construct an image with valid FOV and sharpness but muted contrast
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    dist = np.sqrt((x - 256)**2 + (y - 256)**2)
    retina_mask = dist <= 210
    
    img[retina_mask, 0] = 90
    img[retina_mask, 1] = 60
    img[retina_mask, 2] = 30

    # Add texture
    for offset in range(-50, 50, 20):
        rr = np.clip(256 + offset, 0, 511)
        img[rr : rr + 2, 180:330, 1] = 45

    res = process_retinal_image(img, run_dr_classifier=False)
    assert "initial_quality" in res
    assert "enhancement_applied" in res


def test_original_image_immutability(sample_fundus_image):
    """Verifies that source image array is never modified in-place."""
    original_copy = sample_fundus_image.copy()
    enhancer = AdaptiveEnhancer()
    _ = enhancer.enhance_borderline_image(sample_fundus_image)
    assert np.array_equal(sample_fundus_image, original_copy), "Enhancer must not mutate input array in-place."

    _ = assess_image_quality(sample_fundus_image)
    assert np.array_equal(sample_fundus_image, original_copy), "Quality assessment must not mutate input array in-place."


# =========================================================================
# STEP 15: DR MODEL SAFETY INTERLOCK
# =========================================================================

def test_dr_model_safety_interlock(dark_image):
    """Verifies that ungradable images are strictly blocked from reaching the DR classifier."""
    res = process_retinal_image(dark_image, run_dr_classifier=True)
    assert res["status"] == "ungradable"
    assert res["is_gradeable"] is False
    assert res["dr_prediction"] is None, "DR classifier must NEVER execute on ungradable images."
    assert len(res["issues"]) > 0

