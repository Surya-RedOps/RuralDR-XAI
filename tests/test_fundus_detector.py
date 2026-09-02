"""
RuralDR-XAI: Automated Test Suite for Fundus Modality Gate & OOD Rejection
Verifies that all non-fundus images (cars, people, documents, screenshots, landscapes, X-rays)
are strictly rejected BEFORE any DR classification, Grad-CAM, or lesion segmentation is attempted.
"""

import pytest
import numpy as np
import cv2
import torch
from pathlib import Path

from src.core.contracts import (
    ModalityStatus,
    PipelineStatus,
    QualityStatus,
    ScreeningResult,
    DRGrade,
)
from src.quality.modality import (
    FundusModalityDetector,
    FundusClassifierModel,
    compute_retinal_color_plausibility,
    compute_retinal_geometry_plausibility,
)
from src.engine.orchestrator import ScreeningOrchestrator
from src.models.classifier import DRClassifier
from scripts.train_fundus_detector import generate_synthetic_negative_image


@pytest.fixture(scope="module")
def modality_detector():
    return FundusModalityDetector()


@pytest.fixture(scope="module")
def orchestrator():
    device = torch.device("cpu")
    classifier = DRClassifier(backbone_name="resnet18", num_classes=5, pretrained=False)
    return ScreeningOrchestrator(classifier=classifier, device=device)


@pytest.fixture
def sample_fundus_image():
    """Loads a real fundus image from data/sample or creates a valid fundus synthetic proxy."""
    sample_p = Path("e:/SIH/Base_Architecture/data/sample/sample_fundus.jpg")
    if sample_p.is_file():
        bgr = cv2.imread(str(sample_p))
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    
    # Check APTOS directory
    aptos_dir = Path("e:/SIH/Data_set/aptos2019-blindness-detection/train_images")
    if aptos_dir.is_dir():
        pngs = list(aptos_dir.glob("*.png"))
        if pngs:
            bgr = cv2.imread(str(pngs[0]))
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # Fallback to authentic retinal color proxy with circular FOV
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.circle(img, (256, 256), 220, (180, 70, 20), -1)  # RGB: Red/Orange retina
    cv2.circle(img, (180, 256), 35, (240, 200, 100), -1)  # Optic disc
    cv2.circle(img, (320, 256), 15, (100, 30, 10), -1)  # Fovea
    return img


# ==============================================================================
# 1. COLOR & GEOMETRY HEURISTIC UNIT TESTS
# ==============================================================================

class TestModalityHeuristics:
    def test_color_plausibility_on_fundus(self, sample_fundus_image):
        score, details = compute_retinal_color_plausibility(sample_fundus_image)
        assert score >= 0.40, f"Expected high color score for fundus, got {score}"
        assert details["r_ratio"] > details["b_ratio"], "Red ratio must exceed blue ratio in retina"

    def test_color_plausibility_rejects_document(self):
        doc_img = generate_synthetic_negative_image("document")
        score, details = compute_retinal_color_plausibility(doc_img)
        assert score < 0.20, f"Document image must have low color score, got {score}"
        assert details.get("is_document_like") is True

    def test_color_plausibility_rejects_car(self):
        car_img = generate_synthetic_negative_image("vehicle")
        score, details = compute_retinal_color_plausibility(car_img)
        assert score < 0.35, f"Automotive image must have low color score, got {score}"

    def test_color_plausibility_rejects_screenshot(self):
        screen_img = generate_synthetic_negative_image("screenshot")
        score, details = compute_retinal_color_plausibility(screen_img)
        assert score < 0.35, f"Screenshot image must have low color score, got {score}"

    def test_empty_image_handling(self):
        empty_img = np.zeros((0, 0, 3), dtype=np.uint8)
        score, _ = compute_retinal_color_plausibility(empty_img)
        assert score == 0.0


# ==============================================================================
# 2. NEGATIVE OOD IMAGE REJECTION TESTS (PARTS 6, 16 & 20)
# ==============================================================================

class TestNegativeModalityRejection:
    @pytest.mark.parametrize("category", [
        "vehicle",
        "document",
        "screenshot",
        "person",
        "landscape",
        "medical_xray",
        "abstract",
    ])
    def test_non_fundus_rejected_by_modality_detector(self, modality_detector, category):
        img = generate_synthetic_negative_image(category)
        res = modality_detector.verify(img)
        assert not res.is_fundus, f"Category {category} was incorrectly classified as fundus!"
        assert res.status in (ModalityStatus.NON_FUNDUS, ModalityStatus.UNCERTAIN)

    @pytest.mark.parametrize("category", [
        "vehicle",
        "document",
        "screenshot",
        "person",
        "landscape",
        "medical_xray",
    ])
    def test_full_pipeline_halts_on_non_fundus(self, orchestrator, category):
        """
        CRITICAL SAFETY TEST:
        Ensures that when a non-retinal image is processed:
        - Result status is REJECTED or UNCERTAIN
        - DR classification is NEVER executed (prediction is None)
        - Grad-CAM is NEVER generated
        - Lesion detection is NEVER executed (lesions is None)
        """
        img = generate_synthetic_negative_image(category)
        result, visual_layers = orchestrator.process_image(img, case_id=f"TEST-OOD-{category.upper()}")

        assert result.status in (PipelineStatus.REJECTED, PipelineStatus.UNCERTAIN)
        assert result.modality is not None
        assert not result.modality.is_fundus
        
        # Diagnostic fields MUST strictly be None
        assert result.prediction is None, f"DR Prediction was generated for non-fundus category {category}!"
        assert result.lesions is None, f"Lesion inventory was generated for non-fundus category {category}!"
        assert result.evidence_consistency is None, f"Evidence consistency was generated for {category}!"
        
        # Explainability & Segmentation visual layers MUST NOT exist
        assert "gradcam_heatmap" not in visual_layers, "Grad-CAM heatmap was generated for non-fundus image!"
        assert "hard_exudates" not in visual_layers, "Exudate mask was generated for non-fundus image!"
        assert "microaneurysms" not in visual_layers, "MA mask was generated for non-fundus image!"


# ==============================================================================
# 3. POSITIVE RETINAL IMAGE TESTS (PARTS 7 & 17)
# ==============================================================================

class TestPositiveRetinalAcceptance:
    def test_valid_fundus_passes_modality_gate(self, modality_detector, sample_fundus_image):
        res = modality_detector.verify(sample_fundus_image)
        assert res.is_fundus is True, f"Valid fundus image was rejected! Details: {res.details}"
        assert res.status == ModalityStatus.FUNDUS
        assert res.fundus_probability >= 0.70

    def test_valid_fundus_runs_full_pipeline(self, orchestrator, sample_fundus_image):
        result, visual_layers = orchestrator.process_image(sample_fundus_image, case_id="TEST-VALID-FUNDUS")
        
        assert result.status in (PipelineStatus.SUCCESS, PipelineStatus.UNGRADABLE)
        assert result.modality.is_fundus is True
        
        if result.status == PipelineStatus.SUCCESS:
            assert result.prediction is not None
            assert result.lesions is not None
            assert "gradcam_heatmap" in visual_layers
            assert "composite_annotated" in visual_layers


# ==============================================================================
# 4. CACHE / STATELESSNESS ISOLATION TEST (PART 13 & PART 20 TEST F)
# ==============================================================================

class TestPipelineStatelessness:
    def test_sequential_upload_no_cache_leakage(self, orchestrator, sample_fundus_image):
        # Step 1: Upload Valid Retinal Image A
        result_a, _ = orchestrator.process_image(sample_fundus_image, case_id="CASE-A-RETINAL")
        assert result_a.modality.is_fundus is True

        # Step 2: Upload Non-Retinal Automotive Image B
        car_img = generate_synthetic_negative_image("vehicle")
        result_b, layers_b = orchestrator.process_image(car_img, case_id="CASE-B-CAR")
        
        # Image B must be strictly rejected with zero prediction
        assert result_b.status in (PipelineStatus.REJECTED, PipelineStatus.UNCERTAIN)
        assert result_b.prediction is None
        assert result_b.lesions is None
        assert "gradcam_heatmap" not in layers_b

        # Step 3: Re-upload Retinal Image C
        result_c, _ = orchestrator.process_image(sample_fundus_image, case_id="CASE-C-RETINAL")
        assert result_c.modality.is_fundus is True


# ==============================================================================
# 5. ACCEPTANCE TESTS A THROUGH F (PART 20)
# ==============================================================================

class TestAcceptanceCriteria:
    def test_acceptance_a_valid_retinal_image(self, orchestrator, sample_fundus_image):
        """TEST A: Upload valid retinal image -> Fundus detected -> Full pipeline."""
        result, _ = orchestrator.process_image(sample_fundus_image, case_id="ACCEPT-A")
        assert result.modality.is_fundus is True
        assert result.quality is not None

    def test_acceptance_b_car_image(self, orchestrator):
        """TEST B: Upload car image -> Reject as non-fundus. NO DR prediction."""
        car_img = generate_synthetic_negative_image("vehicle")
        result, _ = orchestrator.process_image(car_img, case_id="ACCEPT-B-CAR")
        assert result.status == PipelineStatus.REJECTED
        assert result.prediction is None
        assert result.lesions is None

    def test_acceptance_c_document_image(self, orchestrator):
        """TEST C: Upload document -> Reject as non-fundus. NO DR prediction."""
        doc_img = generate_synthetic_negative_image("document")
        result, _ = orchestrator.process_image(doc_img, case_id="ACCEPT-C-DOC")
        assert result.status == PipelineStatus.REJECTED
        assert result.prediction is None
        assert result.lesions is None

    def test_acceptance_d_screenshot_image(self, orchestrator):
        """TEST D: Upload screenshot -> Reject as non-fundus. NO DR prediction."""
        screen_img = generate_synthetic_negative_image("screenshot")
        result, _ = orchestrator.process_image(screen_img, case_id="ACCEPT-D-SCREEN")
        assert result.status == PipelineStatus.REJECTED
        assert result.prediction is None
        assert result.lesions is None

    def test_acceptance_e_severe_quality_problem(self, orchestrator):
        """TEST E: Upload retinal image with severe quality problems -> Reject as ungradable. NO unreliable DR prediction."""
        # Pure black / severely underexposed retinal proxy
        black_img = np.zeros((512, 512, 3), dtype=np.uint8)
        cv2.circle(black_img, (256, 256), 200, (8, 4, 2), -1)  # severe underexposure
        result, _ = orchestrator.process_image(black_img, case_id="ACCEPT-E-DARK")
        assert result.status in (PipelineStatus.UNGRADABLE, PipelineStatus.REJECTED)
        assert result.prediction is None
        assert result.lesions is None

    def test_acceptance_f_independent_sequential_runs(self, orchestrator, sample_fundus_image):
        """TEST F: Upload valid retinal image twice with different cases -> Independent predictions, no static result."""
        res1, _ = orchestrator.process_image(sample_fundus_image, case_id="ACCEPT-F1")
        car_img = generate_synthetic_negative_image("vehicle")
        res2, _ = orchestrator.process_image(car_img, case_id="ACCEPT-F2")
        res3, _ = orchestrator.process_image(sample_fundus_image, case_id="ACCEPT-F3")

        assert res1.case_id == "ACCEPT-F1"
        assert res2.case_id == "ACCEPT-F2"
        assert res3.case_id == "ACCEPT-F3"
        assert res2.status == PipelineStatus.REJECTED
        assert res2.prediction is None
