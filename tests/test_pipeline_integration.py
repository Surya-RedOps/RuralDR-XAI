"""
End-to-End Pipeline & API Integration Tests
"""

from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.core.contracts import ScreeningResult
from src.engine.orchestrator import ScreeningOrchestrator
from src.reporting.pdf_generator import generate_clinical_pdf_report
from src.api.server import app


@pytest.fixture
def test_fundus_file(tmp_path):
    """Creates a temporary valid image file for API/CLI pipeline test."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    retina_mask = np.sqrt((x - 256)**2 + (y - 256)**2) <= 220
    img[retina_mask] = [180, 85, 30]

    # Draw optic disc and vessel details
    cv2.circle(img, (160, 256), 35, (240, 230, 160), -1)
    cv2.line(img, (160, 256), (320, 200), (30, 20, 10), 3)

    file_path = tmp_path / "test_fundus.jpg"
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(file_path), bgr)
    return file_path


def test_orchestrator_end_to_end(test_fundus_file):
    orchestrator = ScreeningOrchestrator()
    result, visual_layers = orchestrator.process_image(test_fundus_file)

    assert isinstance(result, ScreeningResult)
    assert result.quality.is_gradeable is True
    assert "original" in visual_layers
    assert "composite_annotated" in visual_layers


def test_pdf_generation(test_fundus_file, tmp_path):
    orchestrator = ScreeningOrchestrator()
    result, visual_layers = orchestrator.process_image(test_fundus_file)

    pdf_out = tmp_path / "output_report.pdf"
    composite_np = visual_layers["composite_annotated"]
    generated_path = generate_clinical_pdf_report(result, composite_np, pdf_out)

    assert generated_path.is_file(), "PDF report must be generated and exist on disk."
    assert generated_path.stat().st_size > 1000, "PDF file must be non-empty."


def test_fastapi_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "device" in data


def test_fastapi_screen_endpoint(test_fundus_file):
    client = TestClient(app)
    with open(test_fundus_file, "rb") as f:
        response = client.post(
            "/api/v1/screen",
            files={"file": ("test_fundus.jpg", f, "image/jpeg")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "result" in data
    assert "visual_urls" in data
