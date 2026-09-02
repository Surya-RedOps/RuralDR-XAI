"""
RuralDR-XAI: API Request & Response Schemas
Defines structured Pydantic models for authentication, screening, referral, and clinical review.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from ..core.contracts import ScreeningResult


# ==============================================================================
# Health & Status
# ==============================================================================
class HealthResponse(BaseModel):
    status: str
    version: str
    device: str
    gpu_available: bool
    gpu_name: Optional[str] = None
    offline_mode: bool = True
    database_connected: bool = True
    storage_mode: str = "local"


# ==============================================================================
# Auth Schemas
# ==============================================================================
class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email, mobile, or Medical Registration Number")
    password: str = Field(..., min_length=4)
    reg_number: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: int
    role: str
    email: str
    mobile: str
    full_name: str
    reg_number: Optional[str] = None
    facility_name: Optional[str] = None
    location_id: Optional[int] = None
    verification_status: str
    is_verified: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


# ==============================================================================
# Location & Hospital Schemas
# ==============================================================================
class LocationResponse(BaseModel):
    id: int
    state: str
    district: str
    healthcare_centre: str
    code: str


class HospitalResponse(BaseModel):
    id: int
    name: str
    location_id: int
    district: str
    address: str
    contact: str
    speciality: str
    availability: str
    is_verified: bool


# ==============================================================================
# Screening Case Schemas
# ==============================================================================
class CreateScreeningCaseRequest(BaseModel):
    patient_id: str
    age: int
    gender: str
    location_id: int
    notes: Optional[str] = None


class ScreeningImageInfo(BaseModel):
    id: int
    filename: str
    url: str
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    uploaded_at: datetime


class AIPredictionResponse(BaseModel):
    is_fundus: bool
    modality_confidence: float
    quality_status: str
    quality_score: float
    dr_stage: Optional[int] = None
    severity_name: Optional[str] = None
    confidence: Optional[float] = None
    class_probabilities: Optional[Dict[str, float]] = None
    gradcam_url: Optional[str] = None
    lesion_data: Optional[List[Dict[str, Any]]] = None
    triage_decision: str
    priority: str
    model_version: str
    disclaimer: str = "AI screening result only. Requires clinical confirmation by an ophthalmologist."


class ScreeningCaseResponse(BaseModel):
    id: int
    case_id: str
    patient_id: str
    age: int
    gender: str
    notes: Optional[str] = None
    status: str
    referral_required: bool
    created_at: datetime
    updated_at: datetime
    location: Optional[LocationResponse] = None
    worker_name: Optional[str] = None
    image: Optional[ScreeningImageInfo] = None
    prediction: Optional[AIPredictionResponse] = None
    referral: Optional[Dict[str, Any]] = None
    doctor_review: Optional[Dict[str, Any]] = None


class ValidationResponse(BaseModel):
    is_fundus: bool
    status: str
    modality_confidence: float
    quality_status: str
    quality_score: float
    is_gradeable: bool
    rejection_reason: Optional[str] = None
    recapture_advice: List[str] = []
    details: Dict[str, Any] = {}


class ScreeningAnalysisResponse(BaseModel):
    case_id: str
    status: str
    is_fundus: bool
    is_gradeable: bool
    dr_stage: Optional[int] = None
    severity_name: Optional[str] = None
    confidence: Optional[float] = None
    class_probabilities: Optional[Dict[str, float]] = None
    referral_required: bool
    priority: str
    triage_decision: str
    visual_urls: Dict[str, str] = {}
    lesions: List[Dict[str, Any]] = []
    rejection_reason: Optional[str] = None
    disclaimer: str


# ==============================================================================
# Referral Schemas
# ==============================================================================
class CreateReferralRequest(BaseModel):
    case_id: str
    hospital_id: int
    priority: Optional[str] = "MEDIUM"
    notes: Optional[str] = None


class ReferralResponse(BaseModel):
    id: int
    case_id: str
    hospital_id: int
    hospital_name: str
    hospital_district: str
    doctor_id: Optional[int] = None
    priority: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Doctor Review Schemas
# ==============================================================================
class DoctorDecisionRequest(BaseModel):
    decision_type: str = Field(..., description="CONFIRM_AI, MODIFY_ASSESSMENT, REQUEST_RECAPTURE, INSUFFICIENT_EVIDENCE")
    final_dr_stage: int = Field(..., ge=0, le=4)
    clinical_notes: str
    treatment_plan: Optional[str] = None
    follow_up_timeline: Optional[str] = None


class DoctorReviewResponse(BaseModel):
    id: int
    case_id: str
    doctor_name: str
    doctor_reg_number: Optional[str] = None
    original_dr_stage: int
    final_dr_stage: int
    final_severity: str
    decision_type: str
    clinical_notes: str
    treatment_plan: Optional[str] = None
    follow_up_timeline: Optional[str] = None
    reviewed_at: datetime


# ==============================================================================
# Report Schemas
# ==============================================================================
class ReportResponse(BaseModel):
    case_id: str
    patient_id: str
    age: int
    gender: str
    screening_date: str
    location: str
    healthcare_centre: str
    worker_name: str
    status: str
    original_image_url: Optional[str] = None
    ai_prediction: Optional[AIPredictionResponse] = None
    doctor_review: Optional[DoctorReviewResponse] = None
    hospital_referral: Optional[Dict[str, Any]] = None
    audit_trail: List[Dict[str, Any]] = []
    disclaimer: str
