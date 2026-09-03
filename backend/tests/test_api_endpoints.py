"""
FastAPI REST API Integration Test Suite for RuralDR-XAI
Tests all screening endpoints, auth routes, doctor reviews, and PDF report generation.
"""

import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from src.api.server import app
from src.db.session import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_auth_login_and_me():
    """Test login for both Healthcare Worker and Doctor roles."""
    # 1. Login Worker
    res_worker = client.post(
        "/api/v1/auth/login",
        json={"identifier": "worker@ruraldrxai.demo", "password": "password123"},
    )
    assert res_worker.status_code == 200, res_worker.text
    worker_data = res_worker.json()
    assert "access_token" in worker_data
    assert worker_data["user"]["role"] == "worker"
    worker_token = worker_data["access_token"]

    # 2. Get Worker Profile
    res_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "worker@ruraldrxai.demo"

    # 3. Login Doctor
    res_doc = client.post(
        "/api/v1/auth/login",
        json={"identifier": "doctor@ruraldrxai.demo", "password": "password123"},
    )
    assert res_doc.status_code == 200
    doc_data = res_doc.json()
    assert doc_data["user"]["role"] == "doctor"
    assert doc_data["user"]["is_verified"] is True


def test_locations_and_hospitals():
    """Test location directory and cascading hospital queries."""
    res_locs = client.get("/api/v1/locations")
    assert res_locs.status_code == 200
    locs = res_locs.json()
    assert len(locs) > 0

    first_loc_id = locs[0]["id"]
    res_hosps = client.get(f"/api/v1/locations/{first_loc_id}/hospitals")
    assert res_hosps.status_code == 200
    hosps = res_hosps.json()
    assert len(hosps) > 0


def test_screening_and_out_of_domain_rejection():
    """Test full upload + modality gate rejection on Porsche car image."""
    # Login Worker
    res_worker = client.post(
        "/api/v1/auth/login",
        json={"identifier": "worker@ruraldrxai.demo", "password": "password123"},
    )
    token = res_worker.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Case
    res_create = client.post(
        "/api/v1/screenings",
        json={
            "patient_id": "PID-TEST-PORSCHE",
            "age": 45,
            "gender": "Male",
            "location_id": 1,
            "notes": "Testing non-fundus rejection",
        },
        headers=headers,
    )
    assert res_create.status_code == 200
    case_id = res_create.json()["case_id"]

    # 2. Upload Non-Fundus (Blue/Gray car image)
    car_img = np.zeros((512, 512, 3), dtype=np.uint8)
    car_img[:, :] = [200, 120, 80]  # BGR
    _, buffer = cv2.imencode(".png", car_img)

    res_upload = client.post(
        f"/api/v1/screenings/{case_id}/image",
        files={"file": ("porsche_test.png", io.BytesIO(buffer.tobytes()), "image/png")},
        headers=headers,
    )
    assert res_upload.status_code == 200

    # 3. Validate image -> Modality gate rejection
    res_val = client.post(
        f"/api/v1/screenings/{case_id}/validate",
        headers=headers,
    )
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["is_fundus"] is False
    assert val_data["quality_score"] == 0.0
    assert "not appear to be a retinal fundus photograph" in val_data["rejection_reason"]


def test_valid_fundus_workflow_and_pdf_generation():
    """Test valid fundus analysis, doctor referral, decision submission, and PDF generation."""
    # Login Worker & Doctor
    res_worker = client.post(
        "/api/v1/auth/login",
        json={"identifier": "worker@ruraldrxai.demo", "password": "password123"},
    )
    w_token = res_worker.json()["access_token"]
    w_headers = {"Authorization": f"Bearer {w_token}"}

    res_doc = client.post(
        "/api/v1/auth/login",
        json={"identifier": "doctor@ruraldrxai.demo", "password": "password123"},
    )
    d_token = res_doc.json()["access_token"]
    d_headers = {"Authorization": f"Bearer {d_token}"}

    # 1. Create Case
    res_create = client.post(
        "/api/v1/screenings",
        json={
            "patient_id": "PID-TEST-VALID-01",
            "age": 62,
            "gender": "Female",
            "location_id": 1,
            "notes": "Diabetic for 8 years, visual blurring",
        },
        headers=w_headers,
    )
    case_id = res_create.json()["case_id"]

    # 2. Upload Synthetic Fundus Image
    fundus_img = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.circle(fundus_img, (256, 256), 220, (25, 85, 215), -1)  # BGR
    _, buffer = cv2.imencode(".png", fundus_img)

    client.post(
        f"/api/v1/screenings/{case_id}/image",
        files={"file": ("fundus_test.png", io.BytesIO(buffer.tobytes()), "image/png")},
        headers=w_headers,
    )

    # 3. Analyze Image
    res_analyze = client.post(
        f"/api/v1/screenings/{case_id}/analyze",
        headers=w_headers,
    )
    assert res_analyze.status_code == 200
    an_data = res_analyze.json()
    assert an_data["is_fundus"] is True

    # 4. Refer Case to Hospital
    res_ref = client.post(
        "/api/v1/referrals",
        json={"case_id": case_id, "hospital_id": 1, "notes": "Specialist referral dispatched"},
        headers=w_headers,
    )
    assert res_ref.status_code == 200

    # 5. Doctor Review Queue
    res_queue = client.get("/api/v1/doctor/cases", headers=d_headers)
    assert res_queue.status_code == 200
    q_cases = res_queue.json()["cases"]
    matching = [c for c in q_cases if c["id"] == case_id]
    assert len(matching) > 0

    # 6. Submit Doctor Decision
    res_decision = client.post(
        f"/api/v1/doctor/cases/{case_id}/decision",
        json={
            "decision_type": "CONFIRM_AI",
            "final_dr_stage": 2,
            "clinical_notes": "Macular findings confirmed. Advised FFA.",
            "treatment_plan": "FFA + Vitreoretinal consultation",
            "follow_up_timeline": "3 Weeks",
        },
        headers=d_headers,
    )
    assert res_decision.status_code == 200

    # 7. Get Clinical Report Data
    res_report = client.get(f"/api/v1/reports/{case_id}", headers=d_headers)
    assert res_report.status_code == 200
    rep = res_report.json()
    assert rep["case_id"] == case_id
    assert rep["doctor_review"]["decision_type"] == "CONFIRM_AI"

    # 8. Generate & Download Official PDF Report
    res_pdf = client.get(f"/api/v1/reports/{case_id}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 1000, "PDF content must be non-empty"
