"""
Unit Tests for Deep Classifier, Calibration, and Triage
"""

import numpy as np
import torch
import pytest

from src.core.contracts import DRGrade, ReviewPriority, SeverityPrediction
from src.models.classifier import DRClassifier
from src.models.calibrate import TemperatureScaler, compute_ece
from src.models.triage import evaluate_triage_decision
from src.models.losses import QuadraticWeightedKappaLoss, FocalLoss


def test_classifier_forward_pass():
    # Instantiate lightweight backbone without downloading pretrained weights for unit test
    model = DRClassifier(backbone_name="resnet18", num_classes=5, pretrained=False)
    x = torch.randn(2, 3, 224, 224)
    logits = model(x)
    assert logits.shape == (2, 5), f"Expected shape (2, 5), got {logits.shape}"


def test_temperature_scaler():
    scaler = TemperatureScaler(initial_temperature=1.5)
    logits = torch.tensor([[2.0, 1.0, 0.0, -1.0, -2.0]])
    scaled = scaler.scale(logits)
    assert torch.allclose(scaled, logits / 1.5)


def test_compute_ece():
    # Perfect calibration synthetic test
    probs = np.array([
        [0.9, 0.1, 0.0, 0.0, 0.0],
        [0.8, 0.2, 0.0, 0.0, 0.0],
        [0.1, 0.9, 0.0, 0.0, 0.0],
    ])
    labels = np.array([0, 0, 1])
    ece, stats = compute_ece(probs, labels, num_bins=5)
    assert ece >= 0.0
    assert "bin_accuracies" in stats


def test_triage_decision():
    pred_referable = SeverityPrediction(
        predicted_grade=DRGrade.MODERATE_NPDR,
        grade_name="Level 2",
        is_referable=True,
        raw_probabilities=[0.05, 0.10, 0.70, 0.10, 0.05],
        calibrated_probabilities=[0.05, 0.10, 0.70, 0.10, 0.05],
        calibrated_confidence=0.70,
    )
    decision, priority = evaluate_triage_decision(pred_referable)
    assert "REFERRAL" in decision
    assert priority in [ReviewPriority.HIGH, ReviewPriority.ELEVATED, ReviewPriority.URGENT]


def test_qwk_loss():
    qwk_loss = QuadraticWeightedKappaLoss(num_classes=5)
    logits = torch.tensor([[5.0, 1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 5.0]])
    targets = torch.tensor([0, 4])
    loss = qwk_loss(logits, targets)
    assert loss >= 0.0
