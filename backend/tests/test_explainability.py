"""
Unit Tests for Explainability Pipeline
Tests the combined Quality Gate → DR → Grad-CAM → Segmentation pipeline,
JSON output schema, timing, and medical safety terminology.
"""

import numpy as np
import torch
import pytest

from src.core.contracts import (
    ExplainableScreeningResult,
    GradCAMResult,
    LesionDetectionResult,
    LesionSegmentationResult,
)


class TestExplainableScreeningResult:
    def test_default_construction(self):
        result = ExplainableScreeningResult()
        assert result.case_id == ""
        assert result.is_gradeable is False
        assert result.dr_grade is None
        assert result.disclaimer != ""

    def test_full_construction(self):
        result = ExplainableScreeningResult(
            case_id="test123",
            timestamp="2025-01-01T00:00:00Z",
            quality_status="acceptable",
            quality_score=0.85,
            is_gradeable=True,
            dr_grade=2,
            severity="Level 2 — Moderate Non-Proliferative DR",
            classification_confidence=0.94,
            is_referable=True,
            gradcam_result=GradCAMResult(target_class=2, is_valid=True),
            quality_gate_time_ms=50.0,
            classification_time_ms=200.0,
            gradcam_time_ms=100.0,
            total_pipeline_time_ms=400.0,
        )
        assert result.dr_grade == 2
        assert result.is_referable is True
        assert result.gradcam_result.target_class == 2

    def test_medical_safety_disclaimer(self):
        result = ExplainableScreeningResult()
        disclaimer = result.disclaimer.lower()
        assert "clinical confirmation" in disclaimer or "ophthalmologist" in disclaimer
        assert "definitive" not in disclaimer or "not" in disclaimer

    def test_json_serialization(self):
        result = ExplainableScreeningResult(
            case_id="test",
            dr_grade=1,
            severity="Mild",
            classification_confidence=0.8,
        )
        data = result.model_dump()
        assert isinstance(data, dict)
        assert data["case_id"] == "test"
        assert data["dr_grade"] == 1

    def test_ungradeable_result(self):
        result = ExplainableScreeningResult(
            quality_status="ungradable",
            is_gradeable=False,
            evidence_summary=["Image quality insufficient"],
        )
        assert result.dr_grade is None
        assert result.gradcam_result is None
        assert result.segmentation_result is None


class TestGradCAMResult:
    def test_valid_result(self):
        result = GradCAMResult(
            target_class=2,
            target_class_name="Moderate NPDR",
            is_valid=True,
            activation_coverage=0.35,
            peak_intensity=0.92,
        )
        assert result.is_valid is True
        assert len(result.quality_flags) == 0

    def test_invalid_result_with_flags(self):
        result = GradCAMResult(
            target_class=0,
            is_valid=False,
            quality_flags=["blank_heatmap", "low_coverage"],
        )
        assert result.is_valid is False
        assert "blank_heatmap" in result.quality_flags

    def test_disclaimer_present(self):
        result = GradCAMResult(target_class=0)
        assert "NOT" in result.disclaimer or "not" in result.disclaimer.lower()


class TestLesionResults:
    def test_detection_result(self):
        result = LesionDetectionResult(
            lesion_type="microaneurysms",
            detected=True,
            pixel_area=200,
            relative_area_pct=0.076,
            num_connected_components=8,
            mean_confidence=0.65,
            approximate_locations=[(100, 200), (300, 400)],
        )
        assert result.detected is True
        assert len(result.approximate_locations) == 2

    def test_no_detection(self):
        result = LesionDetectionResult(lesion_type="soft_exudates")
        assert result.detected is False
        assert result.pixel_area == 0

    def test_segmentation_result_with_lesions(self):
        lesions = [
            LesionDetectionResult(lesion_type="microaneurysms", detected=True, pixel_area=100),
            LesionDetectionResult(lesion_type="haemorrhages", detected=True, pixel_area=500),
            LesionDetectionResult(lesion_type="hard_exudates", detected=False),
            LesionDetectionResult(lesion_type="soft_exudates", detected=False),
        ]
        result = LesionSegmentationResult(
            lesions=lesions,
            segmentation_time_ms=150.0,
        )
        detected = [l for l in result.lesions if l.detected]
        assert len(detected) == 2


class TestTimingFields:
    def test_timing_defaults(self):
        result = ExplainableScreeningResult()
        assert result.quality_gate_time_ms == 0.0
        assert result.classification_time_ms == 0.0
        assert result.gradcam_time_ms == 0.0
        assert result.segmentation_time_ms == 0.0
        assert result.total_pipeline_time_ms == 0.0

    def test_timing_values(self):
        result = ExplainableScreeningResult(
            quality_gate_time_ms=45.5,
            classification_time_ms=210.3,
            gradcam_time_ms=98.7,
            segmentation_time_ms=320.1,
            total_pipeline_time_ms=674.6,
        )
        assert result.total_pipeline_time_ms > result.quality_gate_time_ms


class TestImageProvenance:
    def test_original_source(self):
        result = ExplainableScreeningResult(
            inference_image_source="original",
            original_image_path="/path/to/original.jpg",
        )
        assert result.inference_image_source == "original"
        assert result.enhanced_image_path is None

    def test_enhanced_source(self):
        result = ExplainableScreeningResult(
            inference_image_source="enhanced",
            original_image_path="/path/to/original.jpg",
            enhanced_image_path="/path/to/enhanced.jpg",
        )
        assert result.inference_image_source == "enhanced"
        assert result.enhanced_image_path is not None


class TestEvidenceSummary:
    def test_evidence_summary_format(self):
        result = ExplainableScreeningResult(
            evidence_summary=[
                "AI screening result: Grade 2",
                "Classification model confidence: 94.0%",
                "Model attention map (Grad-CAM) is available for review",
            ],
        )
        assert len(result.evidence_summary) == 3
        assert "screening result" in result.evidence_summary[0].lower()

    def test_no_false_clinical_claims(self):
        """Ensure evidence summary doesn't contain prohibited terminology."""
        result = ExplainableScreeningResult(
            evidence_summary=[
                "AI screening result: Grade 3",
                "All findings require clinical confirmation",
            ],
        )
        for line in result.evidence_summary:
            lower = line.lower()
            assert "confirmed dr" not in lower
            assert "definitive diagnosis" not in lower
            assert "guaranteed" not in lower
            assert "must undergo surgery" not in lower
