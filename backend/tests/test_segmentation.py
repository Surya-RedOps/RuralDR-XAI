"""
Unit Tests for Lesion Segmentation (U-Net Model, Dataset, Inference)
"""

import numpy as np
import torch
import pytest
from pathlib import Path

from src.models.unet import LesionUNet
from src.core.contracts import LesionDetectionResult, LesionSegmentationResult


class TestUNetArchitecture:
    def test_unet_forward_pass(self):
        model = LesionUNet(encoder_name="resnet34", num_classes=4, pretrained=False)
        x = torch.randn(1, 3, 128, 128)
        out = model(x)
        assert out.shape == (1, 4, 128, 128), f"Expected (1,4,128,128), got {out.shape}"

    def test_unet_single_image(self):
        model = LesionUNet(encoder_name="resnet34", num_classes=4, pretrained=False)
        model.eval()
        x = torch.randn(1, 3, 128, 128)
        out = model(x)
        assert out.shape == (1, 4, 128, 128)

    def test_unet_predict_masks(self):
        model = LesionUNet(encoder_name="resnet34", num_classes=4, pretrained=False)
        model.eval()
        x = torch.randn(1, 3, 128, 128)
        masks = model.predict_masks(x, threshold=0.5)
        assert masks.shape == (1, 4, 128, 128)
        assert masks.dtype == torch.uint8
        assert torch.all((masks == 0) | (masks == 1))

    def test_unet_predict_probabilities(self):
        model = LesionUNet(encoder_name="resnet34", num_classes=4, pretrained=False)
        model.eval()
        x = torch.randn(1, 3, 128, 128)
        probs = model.predict_probabilities(x)
        assert probs.shape == (1, 4, 128, 128)
        assert torch.all(probs >= 0.0) and torch.all(probs <= 1.0)

    def test_unet_lesion_classes(self):
        assert LesionUNet.LESION_CLASSES == [
            "microaneurysms", "haemorrhages", "hard_exudates", "soft_exudates"
        ]

    def test_unet_no_nans(self):
        model = LesionUNet(encoder_name="resnet34", num_classes=4, pretrained=False)
        model.eval()
        x = torch.randn(1, 3, 128, 128)
        out = model(x)
        assert not torch.any(torch.isnan(out)), "Output contains NaN"
        assert not torch.any(torch.isinf(out)), "Output contains Inf"

    def test_unet_different_input_sizes(self):
        model = LesionUNet(encoder_name="resnet34", num_classes=4, pretrained=False)
        model.eval()
        for size in [64, 128]:
            x = torch.randn(1, 3, size, size)
            out = model(x)
            assert out.shape == (1, 4, size, size), f"Failed for size {size}"


class TestLesionContracts:
    def test_lesion_detection_result(self):
        result = LesionDetectionResult(
            lesion_type="microaneurysms",
            detected=True,
            pixel_area=150,
            relative_area_pct=0.057,
            num_connected_components=5,
            mean_confidence=0.72,
        )
        assert result.detected is True
        assert result.pixel_area == 150
        assert "clinical confirmation" in result.disclaimer.lower()

    def test_lesion_segmentation_result(self):
        lesions = [
            LesionDetectionResult(lesion_type="microaneurysms", detected=True),
            LesionDetectionResult(lesion_type="haemorrhages", detected=False),
            LesionDetectionResult(lesion_type="hard_exudates", detected=True),
            LesionDetectionResult(lesion_type="soft_exudates", detected=False),
        ]
        result = LesionSegmentationResult(
            lesions=lesions,
            input_resolution=(512, 512),
            segmentation_time_ms=123.4,
        )
        detected = [l for l in result.lesions if l.detected]
        assert len(detected) == 2

    def test_empty_lesion_result(self):
        result = LesionDetectionResult(lesion_type="haemorrhages")
        assert result.detected is False
        assert result.pixel_area == 0
        assert result.num_connected_components == 0


class TestDatasetManifest:
    def test_manifest_import(self):
        """Verify the dataset module can be imported."""
        from src.ai.segmentation.dataset import (
            build_idrid_segmentation_manifest,
            IDRiDSegmentationDataset,
            LESION_CATEGORIES,
        )
        assert len(LESION_CATEGORIES) == 4
        assert "microaneurysms" in LESION_CATEGORIES
        assert "soft_exudates" in LESION_CATEGORIES

    def test_manifest_build(self):
        """Test manifest building with actual IDRiD data if available."""
        from src.ai.segmentation.dataset import build_idrid_segmentation_manifest
        from src.core.config import IDRID_DATASET_DIR

        if not (IDRID_DATASET_DIR / "A. Segmentation").exists():
            pytest.skip("IDRiD dataset not available")

        manifest = build_idrid_segmentation_manifest(IDRID_DATASET_DIR, split="train")
        assert len(manifest) == 54, f"Expected 54 training images, got {len(manifest)}"

        # Check first entry structure
        entry = manifest[0]
        assert "image_id" in entry
        assert "image_path" in entry
        assert "microaneurysms" in entry
        assert Path(entry["image_path"]).is_file()
