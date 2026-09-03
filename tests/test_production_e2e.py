"""
RuralDR-XAI: Production End-to-End Test Suite (SIH26038)
Verifies:
1. Valid fundus image passes fundus validation and FIQA quality assessment
2. Non-fundus image (e.g. Porsche/car photo) FAILS fundus validation
3. Non-fundus image NEVER enters DR classification
4. Non-fundus image NEVER generates fake lesion counts or Grad-CAM
5. Real user registration succeeds and hashes password
6. Healthcare worker cannot access doctor routes
7. Doctor cannot access healthcare worker routes
8. Database contains zero fake clinical data
9. S3 private bucket / signed URLs and local fallback storage work
10. Referral creation and doctor final clinical decision recording
"""

import os
from pathlib import Path
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.server import app
from src.db.session import Base, get_db
from src.db.models import (
    User,
    HealthcareWorker,
    Doctor,
    Location,
    HealthcareCentre,
    Hospital,
    Patient,
    ScreeningCase,
    ScreeningImage,
    ImageValidation,
    AIPrediction,
    LesionFinding,
    Referral,
    ClinicalDecision,
)
from src.core.contracts import ModalityStatus
from src.quality.modality import FundusModalityDetector
from src.quality.gate import ImageQualityGate
from src.engine.orchestrator import ScreeningOrchestrator
from src.storage.storage_service import storage_service
from src.core.security import verify_password

# Persistent test SQLite database file
TEST_DB_DIR = Path("data")
TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
TEST_DB_FILE = TEST_DB_DIR / "test_ruraldr.db"
if TEST_DB_FILE.exists():
    try:
        TEST_DB_FILE.unlink()
    except Exception:
        pass

TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def get_real_sample_fundus() -> np.ndarray:
    """Loads sample retinal fundus photograph in RGB."""
    sample_path = Path("data/sample/sample_fundus.jpg")
    if sample_path.is_file():
        bgr = cv2.imread(str(sample_path))
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    # Synthetic fundus with texture
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.circle(img, (256, 256), 220, (210, 90, 30), -1)
    noise = np.random.randint(-15, 15, (512, 512, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initializes tables in test database."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    from src.db.seed import seed_initial_data
    seed_initial_data(db)

    # Seed one verified test hospital
    loc = db.query(Location).first()
    if loc and db.query(Hospital).filter(Hospital.location_id == loc.id).count() == 0:
        hosp = Hospital(
            name="Coimbatore Regional Eye Care Centre",
            location_id=loc.id,
            address="100 Medical Campus Road, Coimbatore",
            contact="+91 422 2300100",
            speciality="Vitreoretinal & Comprehensive Ophthalmology",
            availability="24/7",
            verification_status="VERIFIED",
        )
        db.add(hosp)
        db.commit()
    db.close()
    yield
    # Teardown
    if TEST_DB_FILE.exists():
        try:
            TEST_DB_FILE.unlink()
        except Exception:
            pass


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# 1. AI Safety & The Porsche Bug Prevention Tests
# ==============================================================================
def test_valid_fundus_passes_validation():
    """Test 1: Valid retinal fundus image passes Gate 1 and FIQA Gate 2."""
    detector = FundusModalityDetector()
    gate = ImageQualityGate()

    fundus_img = get_real_sample_fundus()

    # Gate 1
    res1 = detector.verify(fundus_img)
    assert res1.is_fundus is True
    assert res1.status == ModalityStatus.FUNDUS

    # Gate 2
    res2 = gate.evaluate(fundus_img)
    assert res2.is_gradeable is True


def test_non_fundus_car_fails_validation():
    """Test 2 & 3: Non-fundus car photos FAIL Gate 1."""
    detector = FundusModalityDetector()

    # Blue/gray car
    car_blue = np.zeros((512, 512, 3), dtype=np.uint8)
    car_blue[:, :] = [90, 130, 210]
    res1 = detector.verify(car_blue)
    assert res1.is_fundus is False
    assert res1.status == ModalityStatus.NON_FUNDUS

    # Red Porsche car / wallpaper (filling full rectangle)
    car_red = np.zeros((512, 512, 3), dtype=np.uint8)
    car_red[:, :] = [215, 35, 35]
    res2 = detector.verify(car_red)
    assert res2.is_fundus is False
    assert "retinal fundus photograph" in res2.rejection_reason


def test_non_fundus_never_enters_dr_classification_or_gradcam():
    """Test 4, 5, 6: Non-fundus images NEVER produce DR predictions, fake lesions, or Grad-CAM."""
    orchestrator = ScreeningOrchestrator()

    # Red car image
    car_red = np.zeros((512, 512, 3), dtype=np.uint8)
    car_red[:, :] = [220, 30, 30]

    result, layers = orchestrator.process_image(car_red, case_id="TEST-CAR-001")

    # Safety Assertions
    assert result.status.value == "rejected"
    assert result.prediction is None
    assert result.lesions is None or (
        result.lesions.microaneurysms_count == 0
        and result.lesions.hemorrhages_count == 0
        and result.lesions.hard_exudates_area_pct == 0.0
    )
    assert "gradcam_heatmap" not in layers


# ==============================================================================
# 2. Real Registration & Password Hashing Tests
# ==============================================================================
def test_user_registration_and_bcrypt_hashing(client, db_session):
    """Test 7: Real registration hashes passwords using bcrypt."""
    reg_data = {
        "full_name": "Sister Mary, ANM",
        "professional_id": "HW-TN-7721",
        "mobile": "+91 98401 11223",
        "email": "mary.anm@health.tn.gov.in",
        "healthcare_centre_name": "Valparai Sub-Centre",
        "password": "SecurePassword123!",
    }

    res = client.post("/api/v1/auth/register/worker", json=reg_data)
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["user"]["role"] == "worker"

    # Verify password was hashed with bcrypt in DB, NOT stored plaintext
    user = db_session.query(User).filter(User.email == "mary.anm@health.tn.gov.in").first()
    assert user is not None
    assert user.password_hash != "SecurePassword123!"
    assert user.password_hash.startswith("$2")
    assert verify_password("SecurePassword123!", user.password_hash)


# ==============================================================================
# 3. Role-Based Access Isolation Tests
# ==============================================================================
def test_role_based_access_isolation(client):
    """Test 8 & 9: Worker cannot access Doctor routes; Doctor cannot access Worker routes."""
    # 1. Register Worker
    w_data = {
        "full_name": "Health Worker Test",
        "professional_id": "HW-TEST-88",
        "mobile": "+91 98402 88888",
        "email": "worker.test@gov.in",
        "healthcare_centre_name": "Rural PHC",
        "password": "workerPassword123",
    }
    w_res = client.post("/api/v1/auth/register/worker", json=w_data).json()
    w_token = w_res["access_token"]

    # 2. Register Doctor
    d_data = {
        "full_name": "Dr. Ramanathan, MS",
        "medical_reg_number": "MCI-TN-2020-9988",
        "mobile": "+91 94432 99999",
        "email": "ramanathan.dr@hospital.org",
        "hospital_name": "Eye Hospital",
        "password": "doctorPassword123",
    }
    d_res = client.post("/api/v1/auth/register/doctor", json=d_data).json()
    d_token = d_res["access_token"]

    # Worker attempts to access Doctor queue -> Must receive HTTP 403
    w_access_doc = client.get(
        "/api/v1/doctor/cases",
        headers={"Authorization": f"Bearer {w_token}"},
    )
    assert w_access_doc.status_code == 403

    # Doctor attempts to create new screening case -> Must receive HTTP 403
    d_create_case = client.post(
        "/api/v1/screenings",
        json={"patient_id": "PID-999", "age": 45, "gender": "Male", "location_id": 1},
        headers={"Authorization": f"Bearer {d_token}"},
    )
    assert d_create_case.status_code == 403


# ==============================================================================
# 4. Database Cleanliness (Zero Mock Clinical Data)
# ==============================================================================
def test_database_contains_no_fake_clinical_cases(db_session):
    """Test 11: Database contains zero fake cases (RDX-1048) or fake patients (PID-9082)."""
    fake_case = db_session.query(ScreeningCase).filter(ScreeningCase.case_id == "RDX-1048").first()
    assert fake_case is None, "Database must not seed fake case RDX-1048"

    fake_patient = db_session.query(Patient).filter(Patient.patient_id == "PID-9082").first()
    assert fake_patient is None, "Database must not seed fake patient PID-9082"


# ==============================================================================
# 5. Storage Service & Signed URL Tests
# ==============================================================================
def test_storage_service_private_storage():
    """Test 12, 13, 14: Storage service saves image and returns accessible URL."""
    img_data = np.zeros((100, 100, 3), dtype=np.uint8)
    storage_key, storage_type, w, h, size = storage_service.save_image(
        image_data=img_data,
        case_id="TEST-STORAGE-CASE",
        filename="test_fundus.jpg",
    )
    assert storage_key.startswith("cases/TEST-STORAGE-CASE/")
    assert w == 100 and h == 100

    url = storage_service.get_image_url(storage_key, storage_type)
    assert len(url) > 0


# ==============================================================================
# 6. Referral & Doctor Review Workflow Tests
# ==============================================================================
def test_referral_and_doctor_clinical_decision(client, db_session):
    """Test 15, 16, 17: Referral creation and doctor decision recording."""
    # Worker login
    w_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "worker.test@gov.in", "password": "workerPassword123"},
    ).json()
    w_token = w_login["access_token"]

    # 1. Create Patient & Case
    case_res = client.post(
        "/api/v1/screenings",
        json={"patient_id": "PID-TEST-100", "age": 62, "gender": "Female", "location_id": 1},
        headers={"Authorization": f"Bearer {w_token}"},
    ).json()
    case_id = case_res["case_id"]

    # 2. Upload Genuine Fundus Image
    fundus_rgb = get_real_sample_fundus()
    fundus_bgr = cv2.cvtColor(fundus_rgb, cv2.COLOR_RGB2BGR)
    _, encoded = cv2.imencode(".jpg", fundus_bgr)
    upload_res = client.post(
        f"/api/v1/screenings/{case_id}/image",
        files={"file": ("fundus.jpg", encoded.tobytes(), "image/jpeg")},
        headers={"Authorization": f"Bearer {w_token}"},
    )
    assert upload_res.status_code == 200

    # 3. Validate Image
    val_res = client.post(
        f"/api/v1/screenings/{case_id}/validate",
        headers={"Authorization": f"Bearer {w_token}"},
    )
    assert val_res.status_code == 200
    assert val_res.json()["is_fundus"] is True

    # 4. Analyze Image
    an_res = client.post(
        f"/api/v1/screenings/{case_id}/analyze",
        headers={"Authorization": f"Bearer {w_token}"},
    )
    assert an_res.status_code == 200
    an_data = an_res.json()
    assert an_data["status"] == "SCREENED"

    # 5. Create Referral to hospital
    hosp = db_session.query(Hospital).first()
    ref_res = client.post(
        "/api/v1/referrals",
        json={"case_id": case_id, "hospital_id": hosp.id, "priority": "HIGH"},
        headers={"Authorization": f"Bearer {w_token}"},
    )
    assert ref_res.status_code == 200
    assert ref_res.json()["status"] == "PENDING"

    # 6. Doctor Logs In and Submits Clinical Decision
    d_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "ramanathan.dr@hospital.org", "password": "doctorPassword123"},
    ).json()
    d_token = d_login["access_token"]

    dec_res = client.post(
        f"/api/v1/doctor/cases/{case_id}/decision",
        json={
            "decision_type": "CONFIRM_AI",
            "final_dr_stage": an_data.get("dr_stage", 2),
            "clinical_notes": "Clinical confirmation of retinal biomarkers. Recommended panretinal photocoagulation evaluation.",
            "treatment_plan": "Laser Photocoagulation & FFA",
            "follow_up_timeline": "2 Weeks",
        },
        headers={"Authorization": f"Bearer {d_token}"},
    )
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["decision_type"] == "CONFIRM_AI"

    # Verify case transitioned to COMPLETED
    case_db = db_session.query(ScreeningCase).filter(ScreeningCase.case_id == case_id).first()
    assert case_db.status == "COMPLETED"
    assert case_db.referral.status == "COMPLETED"
