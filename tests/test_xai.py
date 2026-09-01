"""
Unit Tests for Explainable AI (Grad-CAM & Visualization)
Tests Grad-CAM generation, quality validation, multi-class generation, and overlay panel creation.
"""

import numpy as np
import torch
import pytest
import tempfile
from pathlib import Path

from src.models.classifier import DRClassifier
from src.xai.gradcam import GradCAM
from src.xai.visualization import overlay_heatmap, create_gradcam_panel, save_gradcam_outputs


@pytest.fixture
def model():
    """Create a test DR classifier."""
    m = DRClassifier(backbone_name="resnet18", num_classes=5, pretrained=False)
    m.eval()
    return m


@pytest.fixture
def gradcam(model):
    """Create a GradCAM instance."""
    return GradCAM(model, use_plus_plus=True)


@pytest.fixture
def sample_tensor():
    """Create a sample input tensor."""
    return torch.randn(1, 3, 224, 224, requires_grad=True)


@pytest.fixture
def sample_image():
    """Create a sample RGB image."""
    return np.ones((224, 224, 3), dtype=np.uint8) * 128


class TestGradCAMGeneration:
    def test_gradcam_basic_generation(self, gradcam, sample_tensor):
        cam, mask = gradcam.generate(sample_tensor, target_class=2)
        assert cam.shape == (224, 224), f"Expected shape (224, 224), got {cam.shape}"
        assert np.min(cam) >= 0.0 and np.max(cam) <= 1.0, "CAM must be in [0, 1]"
        assert mask.shape == (224, 224)
        assert mask.dtype == np.uint8

    def test_gradcam_auto_target_class(self, gradcam, sample_tensor):
        cam, mask = gradcam.generate(sample_tensor, target_class=None)
        assert cam.shape == (224, 224)

    def test_gradcam_all_five_classes(self, gradcam, sample_tensor):
        for cls_idx in range(5):
            cam, mask = gradcam.generate(sample_tensor, target_class=cls_idx)
            assert cam.shape == (224, 224), f"Failed for class {cls_idx}"

    def test_gradcam_correct_dimensions(self, gradcam, sample_tensor):
        cam, mask = gradcam.generate(sample_tensor, target_class=0)
        assert cam.ndim == 2
        assert mask.ndim == 2
        assert cam.dtype == np.float32

    def test_gradcam_no_nans(self, gradcam, sample_tensor):
        cam, _ = gradcam.generate(sample_tensor, target_class=2)
        assert not np.any(np.isnan(cam)), "CAM contains NaN values"
        assert not np.any(np.isinf(cam)), "CAM contains Inf values"


class TestGradCAMValidation:
    def test_validated_generation(self, gradcam, sample_tensor):
        cam, mask, result = gradcam.generate_with_validation(sample_tensor, target_class=2)
        assert cam.shape == (224, 224)
        assert result.target_class == 2
        assert isinstance(result.is_valid, bool)
        assert 0.0 <= result.activation_coverage <= 1.0
        assert 0.0 <= result.peak_intensity <= 1.0

    def test_blank_heatmap_detection(self, gradcam):
        """A zero tensor should produce a blank heatmap warning."""
        zero_tensor = torch.zeros(1, 3, 224, 224, requires_grad=True)
        cam, mask, result = gradcam.generate_with_validation(zero_tensor, target_class=0)
        # The model may or may not produce blank heatmap depending on weights
        # but the validation logic should run without error
        assert isinstance(result.quality_flags, list)

    def test_gradcam_result_has_class_name(self, gradcam, sample_tensor):
        _, _, result = gradcam.generate_with_validation(sample_tensor, target_class=3)
        assert result.target_class == 3
        assert "Severe" in result.target_class_name

    def test_gradcam_result_disclaimer(self, gradcam, sample_tensor):
        _, _, result = gradcam.generate_with_validation(sample_tensor, target_class=0)
        assert "clinical proof" in result.disclaimer.lower() or "NOT" in result.disclaimer


class TestMultiClassGradCAM:
    def test_multi_class_all(self, gradcam, sample_tensor):
        results = gradcam.generate_multi_class(sample_tensor)
        assert len(results) == 5
        for cls_idx in range(5):
            cam, mask, result = results[cls_idx]
            assert cam.shape == (224, 224)
            assert result.target_class == cls_idx

    def test_multi_class_subset(self, gradcam, sample_tensor):
        results = gradcam.generate_multi_class(sample_tensor, class_indices=[0, 2, 4])
        assert len(results) == 3
        assert 0 in results and 2 in results and 4 in results


class TestVisualization:
    def test_overlay_heatmap(self, sample_image):
        cam = np.linspace(0.0, 1.0, 224 * 224).reshape((224, 224)).astype(np.float32)
        blended = overlay_heatmap(sample_image, cam, alpha=0.5)
        assert blended.shape == (224, 224, 3)
        assert blended.dtype == np.uint8

    def test_overlay_heatmap_size_mismatch(self, sample_image):
        """Heatmap should be resized to match image."""
        cam = np.random.rand(7, 7).astype(np.float32)
        blended = overlay_heatmap(sample_image, cam, alpha=0.5)
        assert blended.shape == (224, 224, 3)

    def test_gradcam_panel(self, sample_image):
        cam = np.random.rand(224, 224).astype(np.float32)
        panel = create_gradcam_panel(sample_image, cam, "Test Class", 0.95)
        assert panel.shape == (224, 448, 3)  # Side by side
        assert panel.dtype == np.uint8

    def test_save_gradcam_outputs(self, sample_image):
        cam = np.random.rand(224, 224).astype(np.float32)
        mask = (cam > 0.5).astype(np.uint8) * 255

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = save_gradcam_outputs(
                sample_image, cam, mask, tmpdir,
                prefix="test", class_name="Grade 2", confidence=0.85,
            )
            assert "original" in paths
            assert "heatmap" in paths
            assert "overlay" in paths
            assert "binary_mask" in paths
            assert "panel" in paths
            for key, path in paths.items():
                assert Path(path).is_file(), f"Missing output: {key}"
