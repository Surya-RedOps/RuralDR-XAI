"""
RuralDR-XAI: SQLAlchemy Database Models
Implements relational schemas for Users, Locations, Hospitals, Screenings, Predictions, Referrals, Doctor Reviews, and Audit Logs.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from .session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False, index=True)  # HEALTHCARE_WORKER, DOCTOR
    email = Column(String(255), unique=True, nullable=False, index=True)
    mobile = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    reg_number = Column(String(100), nullable=True, index=True)  # Doctor Reg No. or Worker Reg ID
    facility_name = Column(String(255), nullable=True)  # PHC or Hospital
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    verification_status = Column(String(50), default="VERIFIED", nullable=False)  # VERIFIED, PENDING, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    location = relationship("Location", back_populates="users")
    screening_cases = relationship("ScreeningCase", back_populates="worker", foreign_keys="ScreeningCase.worker_id")
    assigned_referrals = relationship("Referral", back_populates="doctor", foreign_keys="Referral.doctor_id")
    doctor_reviews = relationship("DoctorReview", back_populates="doctor", foreign_keys="DoctorReview.doctor_id")

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "VERIFIED"


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    healthcare_centre = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="location")
    hospitals = relationship("Hospital", back_populates="location")
    screening_cases = relationship("ScreeningCase", back_populates="location")


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    address = Column(Text, nullable=False)
    contact = Column(String(100), nullable=False)
    speciality = Column(String(255), default="Vitreoretinal & Comprehensive Ophthalmology")
    availability = Column(String(100), default="24/7 Emergency Eye Care")
    is_verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    location = relationship("Location", back_populates="hospitals")
    referrals = relationship("Referral", back_populates="hospital")


class ScreeningCase(Base):
    __tablename__ = "screening_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., RDX-1049
    patient_id = Column(String(50), nullable=False, index=True)  # e.g., PID-9082
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)
    # Statuses: DRAFT, VALIDATED, SCREENED, REFERRED, COMPLETED, REJECTED, UNGRADABLE
    referral_required = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    worker = relationship("User", back_populates="screening_cases", foreign_keys=[worker_id])
    location = relationship("Location", back_populates="screening_cases")
    images = relationship("ScreeningImage", back_populates="case", cascade="all, delete-orphan")
    prediction = relationship("AIPrediction", back_populates="case", uselist=False, cascade="all, delete-orphan")
    referral = relationship("Referral", back_populates="case", uselist=False, cascade="all, delete-orphan")
    doctor_review = relationship("DoctorReview", back_populates="case", uselist=False, cascade="all, delete-orphan")


class ScreeningImage(Base):
    __tablename__ = "screening_images"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), nullable=False, index=True)
    storage_key = Column(String(500), nullable=False)  # Path or S3 key
    storage_type = Column(String(50), default="local", nullable=False)  # "s3" or "local"
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), default="image/jpeg", nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)  # Bytes
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    case = relationship("ScreeningCase", back_populates="images")


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    is_fundus = Column(Boolean, nullable=False)
    modality_confidence = Column(Float, nullable=False)
    quality_status = Column(String(50), nullable=False)  # GRADEABLE, BORDERLINE, UNGRADABLE
    quality_score = Column(Float, nullable=False)
    dr_stage = Column(Integer, nullable=True)  # 0 to 4
    severity_name = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)
    class_probabilities_json = Column(Text, nullable=True)  # JSON string of 5-class calibrated probs
    gradcam_url = Column(Text, nullable=True)  # Data URI or image URL
    lesion_data_json = Column(Text, nullable=True)  # JSON string of detected lesions
    triage_decision = Column(Text, nullable=False)
    priority = Column(String(50), default="ROUTINE", nullable=False)  # ROUTINE, MEDIUM, HIGH, CRITICAL
    model_version = Column(String(100), default="RuralDR-XAI-v1.0", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    case = relationship("ScreeningCase", back_populates="prediction")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    priority = Column(String(50), default="MEDIUM", nullable=False, index=True)  # ROUTINE, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, SENT, ACCEPTED, IN_REVIEW, COMPLETED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    case = relationship("ScreeningCase", back_populates="referral")
    hospital = relationship("Hospital", back_populates="referrals")
    doctor = relationship("User", back_populates="assigned_referrals", foreign_keys=[doctor_id])


class DoctorReview(Base):
    __tablename__ = "doctor_reviews"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_dr_stage = Column(Integer, nullable=False)
    final_dr_stage = Column(Integer, nullable=False)
    final_severity = Column(String(255), nullable=False)
    decision_type = Column(String(50), nullable=False)  # CONFIRM_AI, MODIFY_ASSESSMENT, REQUEST_RECAPTURE, INSUFFICIENT_EVIDENCE
    clinical_notes = Column(Text, nullable=False)
    treatment_plan = Column(Text, nullable=True)
    follow_up_timeline = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    case = relationship("ScreeningCase", back_populates="doctor_review")
    doctor = relationship("User", back_populates="doctor_reviews", foreign_keys=[doctor_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    case_id = Column(String(50), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
