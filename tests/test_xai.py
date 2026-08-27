"""
Unit Tests for Explainable AI (Grad-CAM & Visualization)
"""

import numpy as np
import torch
import pytest

from src.models.classifier import DRClassifier
from src.xai.gradcam import GradCAM
from src.xai.visualization import overlay_heatmap


def test_gradcam_generation():
    model = DRClassifier(backbone_name="resnet18", num_classes=5, pretrained=False)
    gradcam = GradCAM(model, use_plus_plus=True)

    x = torch.randn(1, 3, 224, 224, requires_grad=True)
    cam, mask = gradcam.generate(x, target_class=2)

    assert cam.shape == (224, 224), f"Expected shape (224, 224), got {cam.shape}"
    assert np.min(cam) >= 0.0 and np.max(cam) <= 1.0, "CAM heatmap must be normalized in [0, 1]."
    assert mask.shape == (224, 224)


def test_overlay_heatmap():
    img = np.ones((100, 100, 3), dtype=np.uint8) * 128
    cam = np.linspace(0.0, 1.0, 10000).reshape((100, 100)).astype(np.float32)
    blended = overlay_heatmap(img, cam, alpha=0.5)

    assert blended.shape == (100, 100, 3)
    assert blended.dtype == np.uint8
