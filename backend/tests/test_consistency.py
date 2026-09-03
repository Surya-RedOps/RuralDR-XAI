"""
Unit Tests for Evidence Consistency Engine
"""

import numpy as np
import pytest

from src.core.contracts import (
    DRGrade,
    ConsistencyStatus,
    SeverityPrediction,
    LesionInventory,
    RetinalAnatomy,
)
from src.engine.consistency import EvidenceConsistencyEngine


def test_consistency_supported():
    engine = EvidenceConsistencyEngine()

    pred = SeverityPrediction(
        predicted_grade=DRGrade.NO_DR,
        grade_name="Level 0 — No DR",
        is_referable=False,
        raw_probabilities=[0.95, 0.03, 0.01, 0.005, 0.005],
        calibrated_probabilities=[0.95, 0.03, 0.01, 0.005, 0.005],
        calibrated_confidence=0.95,
    )

    lesions = LesionInventory(microaneurysms_count=0, hard_exudates_area_pct=0.0)
    lesion_masks = {"combined_lesions": np.zeros((100, 100), dtype=np.uint8)}
    cam_mask = np.zeros((100, 100), dtype=np.uint8)
    cam_heatmap = np.zeros((100, 100), dtype=np.float32)
    anatomy = RetinalAnatomy()

    consistency = engine.evaluate(pred, lesions, lesion_masks, cam_mask, cam_heatmap, anatomy)

    assert consistency.status == ConsistencyStatus.SUPPORTED
    assert consistency.concordance_index == 1.0


def test_consistency_review_required():
    engine = EvidenceConsistencyEngine()

    # Discordance: Model predicts No DR, but severe exudates and MAs exist
    pred = SeverityPrediction(
        predicted_grade=DRGrade.NO_DR,
        grade_name="Level 0 — No DR",
        is_referable=False,
        raw_probabilities=[0.90, 0.05, 0.03, 0.01, 0.01],
        calibrated_probabilities=[0.90, 0.05, 0.03, 0.01, 0.01],
        calibrated_confidence=0.90,
    )

    lesions = LesionInventory(microaneurysms_count=15, hard_exudates_area_pct=2.5)
    lesion_masks = {"combined_lesions": np.ones((100, 100), dtype=np.uint8) * 255}
    cam_mask = np.zeros((100, 100), dtype=np.uint8)
    cam_heatmap = np.zeros((100, 100), dtype=np.float32)
    anatomy = RetinalAnatomy()

    consistency = engine.evaluate(pred, lesions, lesion_masks, cam_mask, cam_heatmap, anatomy)

    assert consistency.status in [ConsistencyStatus.REVIEW_REQUIRED, ConsistencyStatus.PARTIALLY_SUPPORTED]
    assert len(consistency.discordance_reasons) > 0, "Discordance reasons must explain contradiction."
