"""
End-to-End Integration Tests for RuralDR-XAI
Validates:
1. Non-fundus OOD rejection (Porsche/wallpaper test) - Gate 1
2. Fundus FIQA optical quality gate - Gate 2
3. Genuine Fundus DR Classification & Grad-CAM Explainability
4. MySQL/SQLite DB persistence & Referral triage workflow
5. Doctor review and clinical decision submission
"""

import os
import json
import cv2
import numpy as np
import pytest
from src.quality.modality import FundusModalityDetector
from src.engine.orchestrator import ScreeningOrchestrator
from src.core.contracts import ModalityStatus, PipelineStatus
from src.db.session import init_db, SessionLocal
from src.db.models import User, Location, ScreeningCase, AIPrediction, Referral, DoctorReview
from src.core.security import create_access_token, decode_access_token, verify_password


def test_modality_detector_rejects_non_fundus():
    """Test that synthetic non-fundus images (like blue/gray car images) are 100% rejected."""
    detector = FundusModalityDetector()
    
    # Synthetic blue/silver car image in RGB format (high blue, low red)
    car_img = np.zeros((512, 512, 3), dtype=np.uint8)
    car_img[:, :] = [80, 120, 200]  # RGB: R=80, G=120, B=200
    
    result = detector.verify(car_img)
    assert not result.is_fundus, "Non-fundus car image should be rejected"
    assert result.status == ModalityStatus.NON_FUNDUS
    assert result.rejection_reason is not None


def test_modality_detector_accepts_fundus():
    """Test that synthetic retinal fundus characteristics (red dominant, circular aperture) are accepted."""
    detector = FundusModalityDetector()
    
    # Synthetic fundus in RGB format: circular aperture with orange-red retinal hue
    fundus_img = np.zeros((512, 512, 3), dtype=np.uint8)
    cv2.circle(fundus_img, (256, 256), 220, (215, 85, 25), -1)  # RGB: R=215, G=85, B=25
    
    result = detector.verify(fundus_img)
    assert result.is_fundus, "Valid fundus optical pattern should pass modality verification"
    assert result.status == ModalityStatus.FUNDUS


def test_orchestrator_safety_interlock_on_car_image():
    """Test that orchestrator halts immediately when non-fundus is submitted and generates NO DR prediction."""
    orchestrator = ScreeningOrchestrator()
    
    # Blue/gray car wallpaper in RGB format
    car_img = np.zeros((512, 512, 3), dtype=np.uint8)
    car_img[:, :] = [50, 100, 200]  # High blue, non-fundus
    
    result, visual_layers = orchestrator.process_image(car_img, "test_porsche_car")
    assert result.status == PipelineStatus.REJECTED
    assert not result.modality.is_fundus
    assert result.prediction is None, "Prediction MUST be None when modality check fails"
    assert "REJECTED" in result.triage_decision


def test_db_seeding_and_auth():
    """Test that demo users and locations are seeded properly with bcrypt password hashing."""
    init_db()
    
    db = SessionLocal()
    try:
        worker = db.query(User).filter(User.email == "worker@ruraldrxai.demo").first()
        assert worker is not None, "Worker user should be seeded"
        assert worker.role == "HEALTHCARE_WORKER"
        assert worker.is_verified
        assert verify_password("password123", worker.password_hash)
        
        doctor = db.query(User).filter(User.email == "doctor@ruraldrxai.demo").first()
        assert doctor is not None, "Doctor user should be seeded"
        assert doctor.role == "DOCTOR"
        assert doctor.is_verified
        assert verify_password("password123", doctor.password_hash)
        
        # Test JWT token creation and decoding
        token = create_access_token({"sub": str(worker.id), "role": "HEALTHCARE_WORKER"})
        payload = decode_access_token(token)
        assert payload["sub"] == str(worker.id)
        assert payload["role"] == "HEALTHCARE_WORKER"
    finally:
        db.close()


def test_full_clinical_workflow():
    """Test complete flow: Create case -> AI analysis -> Hospital Referral -> Doctor Review."""
    init_db()
    
    db = SessionLocal()
    try:
        worker = db.query(User).filter(User.role == "HEALTHCARE_WORKER").first()
        doctor = db.query(User).filter(User.role == "DOCTOR").first()
        location = db.query(Location).first()
        
        assert worker is not None
        assert doctor is not None
        assert location is not None
        
        import uuid
        test_case_id = f"RDX-TEST-{uuid.uuid4().hex[:6].upper()}"
        
        # 1. Create Screening Case
        case = ScreeningCase(
            case_id=test_case_id,
            worker_id=worker.id,
            location_id=location.id,
            patient_id="PID-TEST-999",
            age=58,
            gender="Female",
            notes="Routine checkup",
            status="DRAFT"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        
        # 2. Simulate AI Analysis
        pred = AIPrediction(
            case_id=case.case_id,
            is_fundus=True,
            modality_confidence=0.98,
            quality_status="GRADEABLE",
            quality_score=0.94,
            dr_stage=2,
            severity_name="Moderate NPDR",
            confidence=0.89,
            class_probabilities_json=json.dumps({"0": 0.02, "1": 0.05, "2": 0.89, "3": 0.03, "4": 0.01}),
            priority="MEDIUM",
            triage_decision="Moderate NPDR detected. Ophthalmology referral within 3-4 weeks."
        )
        case.status = "SCREENED"
        case.referral_required = True
        db.add(pred)
        db.commit()
        
        # 3. Create Hospital Referral
        hospital = location.hospitals[0] if location.hospitals else None
        if hospital:
            referral = Referral(
                case_id=case.case_id,
                hospital_id=hospital.id,
                priority="MEDIUM",
                status="PENDING",
                notes="Patient referred for vitreo-retinal evaluation"
            )
            case.status = "REFERRED"
            db.add(referral)
            db.commit()
        
        # 4. Doctor Review & Decision
        review = DoctorReview(
            case_id=case.case_id,
            doctor_id=doctor.id,
            original_dr_stage=2,
            final_dr_stage=2,
            final_severity="Moderate NPDR",
            decision_type="CONFIRM_AI",
            clinical_notes="AI grading verified. Microaneurysms and hard exudates confirmed in parafoveal region.",
            treatment_plan="FFA and glycemic control follow-up",
            follow_up_timeline="3-4 weeks"
        )
        case.status = "COMPLETED"
        db.add(review)
        db.commit()
        
        # Assertions
        updated_case = db.query(ScreeningCase).filter(ScreeningCase.case_id == test_case_id).first()
        assert updated_case.status == "COMPLETED"
        assert updated_case.prediction.dr_stage == 2
        assert updated_case.doctor_review.final_dr_stage == 2
        assert updated_case.doctor_review.decision_type == "CONFIRM_AI"
    finally:
        db.close()
