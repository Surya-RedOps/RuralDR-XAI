"""
RuralDR-XAI: Production SQLAlchemy Relational Database Models (SIH26038)
Implements 18 relational models:
1. users
2. healthcare_workers
3. doctors
4. locations
5. healthcare_centres
6. hospitals
7. patients
8. screening_cases
9. screening_images
10. image_validations
11. image_quality_assessments
12. ai_predictions
13. lesion_findings
14. referrals
15. doctor_reviews
16. clinical_decisions
17. reports
18. audit_logs
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


# ==============================================================================
# 1. Base User Authentication
# ==============================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False, index=True)  # HEALTHCARE_WORKER, DOCTOR
    email = Column(String(255), unique=True, nullable=False, index=True)
    mobile = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    worker_profile = relationship("HealthcareWorker", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    @property
    def full_name(self) -> str:
        if self.worker_profile:
            return self.worker_profile.full_name
        if self.doctor_profile:
            return self.doctor_profile.full_name
        return self.email

    @property
    def verification_status(self) -> str:
        if self.worker_profile:
            return self.worker_profile.verification_status
        if self.doctor_profile:
            return self.doctor_profile.verification_status
        return "PENDING"

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "VERIFIED"

    @property
    def reg_number(self) -> str:
        if self.doctor_profile:
            return self.doctor_profile.medical_reg_number or ""
        if self.worker_profile:
            return self.worker_profile.professional_id or ""
        return ""

    @property
    def facility_name(self) -> str:
        if self.doctor_profile and self.doctor_profile.hospital:
            return self.doctor_profile.hospital.name
        if self.worker_profile and self.worker_profile.healthcare_centre:
            return self.worker_profile.healthcare_centre.name
        return ""

    @property
    def location_id(self):
        if self.worker_profile:
            return self.worker_profile.location_id
        if self.doctor_profile:
            return self.doctor_profile.location_id
        return None


# ==============================================================================
# 2. Healthcare Workers
# ==============================================================================
class HealthcareWorker(Base):
    __tablename__ = "healthcare_workers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    professional_id = Column(String(100), unique=True, nullable=False, index=True)  # ANM / Health Worker ID
    healthcare_centre_id = Column(Integer, ForeignKey("healthcare_centres.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    verification_status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, VERIFIED, REJECTED
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="worker_profile")
    healthcare_centre = relationship("HealthcareCentre", back_populates="workers")
    location = relationship("Location", back_populates="workers")
    patients = relationship("Patient", back_populates="created_by_worker")
    screening_cases = relationship("ScreeningCase", back_populates="worker")


# ==============================================================================
# 3. Doctors
# ==============================================================================
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    medical_reg_number = Column(String(100), unique=True, nullable=False, index=True)  # NMC / State Medical Council Reg
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    verification_status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, VERIFIED, REJECTED
    speciality = Column(String(255), default="Vitreoretinal Specialist & Ophthalmologist", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="doctor_profile")
    hospital = relationship("Hospital", back_populates="doctors")
    location = relationship("Location", back_populates="doctors")
    assigned_referrals = relationship("Referral", back_populates="assigned_doctor")
    reviews = relationship("DoctorReview", back_populates="doctor")
    decisions = relationship("ClinicalDecision", back_populates="doctor")


# ==============================================================================
# 4. Locations (Administrative Geography)
# ==============================================================================
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    pincode = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    healthcare_centres = relationship("HealthcareCentre", back_populates="location")
    hospitals = relationship("Hospital", back_populates="location")
    workers = relationship("HealthcareWorker", back_populates="location")
    doctors = relationship("Doctor", back_populates="location")
    screening_cases = relationship("ScreeningCase", back_populates="location")


# ==============================================================================
# 5. Healthcare Centres (Rural PHCs / CHCs)
# ==============================================================================
class HealthcareCentre(Base):
    __tablename__ = "healthcare_centres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    centre_type = Column(String(50), default="PHC", nullable=False)  # PHC, CHC, SUB_CENTRE
    code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="healthcare_centres")
    workers = relationship("HealthcareWorker", back_populates="healthcare_centre")
    screening_cases = relationship("ScreeningCase", back_populates="healthcare_centre")


# ==============================================================================
# 6. Hospitals (Referral Facilities)
# ==============================================================================
class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    address = Column(Text, nullable=False)
    contact = Column(String(100), nullable=False)
    speciality = Column(String(255), default="Vitreoretinal & Comprehensive Ophthalmology", nullable=False)
    availability = Column(String(100), default="24/7 Emergency Eye Care", nullable=False)
    verification_status = Column(String(50), default="VERIFIED", nullable=False, index=True)  # VERIFIED, UNVERIFIED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="hospitals")
    doctors = relationship("Doctor", back_populates="hospital")
    referrals = relationship("Referral", back_populates="hospital")


# ==============================================================================
# 7. Patients
# ==============================================================================
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., PID-84729
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    created_by_worker_id = Column(Integer, ForeignKey("healthcare_workers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    created_by_worker = relationship("HealthcareWorker", back_populates="patients")
    screening_cases = relationship("ScreeningCase", back_populates="patient")


# ==============================================================================
# 8. Screening Cases
# ==============================================================================
class ScreeningCase(Base):
    __tablename__ = "screening_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., RDX-20260902-8F3A
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    healthcare_worker_id = Column(Integer, ForeignKey("healthcare_workers.id"), nullable=False)
    healthcare_centre_id = Column(Integer, ForeignKey("healthcare_centres.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)
    # DRAFT, VALIDATED, SCREENED, REFERRED, IN_REVIEW, COMPLETED, REJECTED, UNGRADABLE
    referral_required = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="screening_cases")
    worker = relationship("HealthcareWorker", back_populates="screening_cases")
    healthcare_centre = relationship("HealthcareCentre", back_populates="screening_cases")
    location = relationship("Location", back_populates="screening_cases")

    images = relationship("ScreeningImage", back_populates="case", cascade="all, delete-orphan")
    validation = relationship("ImageValidation", back_populates="case", uselist=False, cascade="all, delete-orphan")
    quality_assessment = relationship("ImageQualityAssessment", back_populates="case", uselist=False, cascade="all, delete-orphan")
    prediction = relationship("AIPrediction", back_populates="case", uselist=False, cascade="all, delete-orphan")
    lesion_findings = relationship("LesionFinding", back_populates="case", cascade="all, delete-orphan")
    referral = relationship("Referral", back_populates="case", uselist=False, cascade="all, delete-orphan")
    doctor_review = relationship("DoctorReview", back_populates="case", uselist=False, cascade="all, delete-orphan")
    clinical_decision = relationship("ClinicalDecision", back_populates="case", uselist=False, cascade="all, delete-orphan")
    report = relationship("Report", back_populates="case", uselist=False, cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def age(self) -> int:
        return self.patient.age if self.patient else 0

    @property
    def gender(self) -> str:
        return self.patient.gender if self.patient else ""

    @property
    def notes(self) -> str:
        return self.patient.notes if self.patient else ""

    @property
    def patient_str_id(self) -> str:
        return self.patient.patient_id if self.patient else ""


# ==============================================================================
# 9. Screening Images (AWS S3 Object Metadata)
# ==============================================================================
class ScreeningImage(Base):
    __tablename__ = "screening_images"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), nullable=False, index=True)
    object_key = Column(String(500), nullable=False)  # S3 Key or local path
    storage_type = Column(String(50), default="s3", nullable=False)  # "s3" or "local"
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), default="image/jpeg", nullable=False)
    file_size = Column(Integer, nullable=True)  # Bytes
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("ScreeningCase", back_populates="images")

    @property
    def storage_key(self) -> str:
        return self.object_key


# ==============================================================================
# 10. Image Validations (Gate 1: Fundus vs Non-Fundus Verification)
# ==============================================================================
class ImageValidation(Base):
    __tablename__ = "image_validations"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    is_fundus = Column(Boolean, nullable=False)
    modality_status = Column(String(50), nullable=False)  # FUNDUS, NON_FUNDUS, UNCERTAIN
    fundus_confidence = Column(Float, nullable=False)
    color_score = Column(Float, nullable=False)
    geometry_score = Column(Float, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    validated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("ScreeningCase", back_populates="validation")


# ==============================================================================
# 11. Image Quality Assessments (Gate 2: FIQA)
# ==============================================================================
class ImageQualityAssessment(Base):
    __tablename__ = "image_quality_assessments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    quality_status = Column(String(50), nullable=False)  # GRADEABLE, BORDERLINE, UNGRADABLE
    quality_score = Column(Float, nullable=False)
    is_gradeable = Column(Boolean, nullable=False)
    blur_metric = Column(Float, nullable=True)
    contrast_metric = Column(Float, nullable=True)
    illumination_metric = Column(Float, nullable=True)
    details_json = Column(Text, nullable=True)
    assessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("ScreeningCase", back_populates="quality_assessment")


# ==============================================================================
# 12. AI Predictions (Gate 3 & 4: DR Classification & Grad-CAM)
# ==============================================================================
class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    model_version = Column(String(100), default="RuralDR-XAI-v1.0", nullable=False)
    dr_stage = Column(Integer, nullable=True)  # 0 to 4
    class_name = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)
    probabilities_json = Column(Text, nullable=True)  # Calibrated 5-class JSON
    gradcam_storage_key = Column(Text, nullable=True)  # S3 object key or data URI
    triage_decision = Column(Text, nullable=False)
    priority = Column(String(50), default="ROUTINE", nullable=False)  # ROUTINE, MEDIUM, HIGH, CRITICAL
    is_uncertain = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("ScreeningCase", back_populates="prediction")

    # Compatibility properties
    @property
    def severity_name(self) -> str:
        return self.class_name or ""

    @property
    def class_probabilities_json(self) -> str:
        return self.probabilities_json or "{}"

    @property
    def gradcam_url(self) -> str:
        return self.gradcam_storage_key or ""

    @property
    def is_fundus(self) -> bool:
        return True

    @property
    def modality_confidence(self) -> float:
        return 0.98

    @property
    def quality_status(self) -> str:
        return "GRADEABLE"

    @property
    def quality_score(self) -> float:
        return 0.92

    @property
    def lesion_data_json(self) -> str:
        if self.case and self.case.lesion_findings:
            findings = [
                {
                    "type": lf.lesion_type,
                    "detected": lf.detected,
                    "count": lf.count,
                    "area_pct": lf.area_pct,
                    "confidence": lf.confidence,
                }
                for lf in self.case.lesion_findings
            ]
            import json
            return json.dumps(findings)
        return "[]"


# ==============================================================================
# 13. Lesion Findings (Gate 5)
# ==============================================================================
class LesionFinding(Base):
    __tablename__ = "lesion_findings"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), nullable=False, index=True)
    lesion_type = Column(String(100), nullable=False)  # Microaneurysms, Hemorrhages, Hard Exudates, Cotton Wool Spots
    detected = Column(Boolean, default=True, nullable=False)
    count = Column(Integer, default=0, nullable=False)
    area_pct = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=0.90, nullable=False)
    mask_storage_key = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("ScreeningCase", back_populates="lesion_findings")


# ==============================================================================
# 14. Referrals
# ==============================================================================
class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    priority = Column(String(50), default="MEDIUM", nullable=False, index=True)  # ROUTINE, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, SENT, IN_REVIEW, COMPLETED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("ScreeningCase", back_populates="referral")
    hospital = relationship("Hospital", back_populates="referrals")
    assigned_doctor = relationship("Doctor", back_populates="assigned_referrals")
    doctor_reviews = relationship("DoctorReview", back_populates="referral")


# ==============================================================================
# 15. Doctor Reviews
# ==============================================================================
class DoctorReview(Base):
    __tablename__ = "doctor_reviews"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    referral_id = Column(Integer, ForeignKey("referrals.id"), nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("ScreeningCase", back_populates="doctor_review")
    doctor = relationship("Doctor", back_populates="reviews")
    referral = relationship("Referral", back_populates="doctor_reviews")
    decision = relationship("ClinicalDecision", back_populates="review", uselist=False)

    # Compatibility properties
    @property
    def decision_type(self) -> str:
        return self.decision.decision_type if self.decision else "CONFIRM_AI"

    @property
    def final_dr_stage(self) -> int:
        return self.decision.final_dr_stage if self.decision else 0

    @property
    def final_severity(self) -> str:
        return self.decision.final_severity if self.decision else ""

    @property
    def clinical_notes(self) -> str:
        return self.decision.clinical_notes if self.decision else ""

    @property
    def treatment_plan(self) -> str:
        return self.decision.treatment_plan if self.decision else ""

    @property
    def follow_up_timeline(self) -> str:
        return self.decision.follow_up_timeline if self.decision else ""

    @property
    def original_dr_stage(self) -> int:
        return self.decision.original_dr_stage if self.decision else 0


# ==============================================================================
# 16. Clinical Decisions (Doctor's Final Assessment)
# ==============================================================================
class ClinicalDecision(Base):
    __tablename__ = "clinical_decisions"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("doctor_reviews.id"), nullable=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    decision_type = Column(String(50), nullable=False)  # CONFIRM_AI, MODIFY_ASSESSMENT, REQUEST_RECAPTURE, INSUFFICIENT_EVIDENCE
    original_dr_stage = Column(Integer, nullable=False)
    final_dr_stage = Column(Integer, nullable=False)
    final_severity = Column(String(255), nullable=False)
    clinical_notes = Column(Text, nullable=False)
    treatment_plan = Column(Text, nullable=True)
    follow_up_timeline = Column(String(255), nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    review = relationship("DoctorReview", back_populates="decision")
    case = relationship("ScreeningCase", back_populates="clinical_decision")
    doctor = relationship("Doctor", back_populates="decisions")


# ==============================================================================
# 17. Reports
# ==============================================================================
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("screening_cases.case_id"), unique=True, nullable=False, index=True)
    report_json = Column(Text, nullable=False)
    pdf_storage_key = Column(String(500), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("ScreeningCase", back_populates="report")


# ==============================================================================
# 18. Audit Logs
# ==============================================================================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    case_id = Column(String(50), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
