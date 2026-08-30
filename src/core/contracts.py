"""
RuralDR-XAI: Core Type Definitions and Data Contracts
Enforces strict schema consistency across all pipeline stages.
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel, Field
import numpy as np


class QualityStatus(str, Enum):
    GRADEABLE = "GRADEABLE"
    BORDERLINE = "BORDERLINE"
    UNGRADABLE = "UNGRADABLE"


class DRGrade(int, Enum):
    NO_DR = 0
    MILD_NPDR = 1
    MODERATE_NPDR = 2
    SEVERE_NPDR = 3
    PDR = 4


DR_GRADE_NAMES = {
    DRGrade.NO_DR: "Level 0 — No Diabetic Retinopathy",
    DRGrade.MILD_NPDR: "Level 1 — Mild Non-Proliferative DR",
    DRGrade.MODERATE_NPDR: "Level 2 — Moderate Non-Proliferative DR",
    DRGrade.SEVERE_NPDR: "Level 3 — Severe Non-Proliferative DR",
    DRGrade.PDR: "Level 4 — Proliferative Diabetic Retinopathy",
}


class ConsistencyStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ReviewPriority(str, Enum):
    ROUTINE = "ROUTINE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    URGENT = "URGENT"


class QualityMetrics(BaseModel):
    status: QualityStatus
    quality_score: float = Field(ge=0.0, le=1.0, description="Overall image quality score in [0, 1]")
    focus_score: float = Field(ge=0.0, description="Tenengrad/Laplacian focus sharpness metric")
    illumination_score: float = Field(ge=0.0, description="Entropy and dynamic range metric")
    contrast_score: Optional[float] = Field(default=None, description="RMS contrast metric")
    fov_coverage: float = Field(ge=0.0, le=1.0, description="Retinal foreground area coverage ratio")
    glare_artifact_score: float = Field(ge=0.0, le=1.0, description="Overexposure/glare penalty score")
    is_gradeable: bool
    recapture_advice: List[str] = Field(default_factory=list)
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RetinalAnatomy(BaseModel):
    optic_disc_center: Optional[Tuple[int, int]] = None  # (x, y)
    optic_disc_radius: Optional[float] = None
    optic_disc_bbox: Optional[Tuple[int, int, int, int]] = None  # (xmin, ymin, xmax, ymax)
    fovea_center: Optional[Tuple[int, int]] = None  # (x, y)
    vessel_density: float = Field(default=0.0, ge=0.0, le=1.0)
    anatomical_landmarks_valid: bool = False


class LesionInventory(BaseModel):
    microaneurysms_count: int = 0
    microaneurysms_quadrants: Dict[str, int] = Field(default_factory=dict)
    hard_exudates_area_pct: float = 0.0
    soft_exudates_detected: bool = False
    hemorrhages_count: int = 0
    hemorrhages_quadrants: Dict[str, int] = Field(default_factory=dict)
    neovascularization_detected: bool = False
    foveal_involvement_threat: bool = False  # True if hard exudates found within 1 disc diameter of fovea
    total_lesion_area_pct: float = 0.0


class SeverityPrediction(BaseModel):
    predicted_grade: DRGrade
    grade_name: str
    is_referable: bool  # True if Grade >= 2
    raw_probabilities: List[float] = Field(description="5-class softmax probabilities [P(0)..P(4)]")
    calibrated_probabilities: List[float] = Field(description="Temperature-scaled calibrated probabilities")
    calibrated_confidence: float = Field(ge=0.0, le=1.0)
    temperature_scaling_factor: float = 1.0


class EvidenceConsistency(BaseModel):
    status: ConsistencyStatus
    concordance_index: float = Field(ge=0.0, le=1.0, description="Lesion-GradCAM spatial overlap ratio")
    pointing_game_hit: bool = False
    clinical_rule_satisfied: bool = True
    discordance_reasons: List[str] = Field(default_factory=list)
    human_review_priority: ReviewPriority


class ScreeningResult(BaseModel):
    case_id: str
    timestamp: str
    quality: QualityMetrics
    anatomy: RetinalAnatomy
    lesions: LesionInventory
    prediction: Optional[SeverityPrediction] = None
    evidence_consistency: Optional[EvidenceConsistency] = None
    triage_decision: str
    review_priority: ReviewPriority
    disclaimer: str = (
        "RuralDR-XAI is an investigational decision-support tool for rural screening triage. "
        "Findings must be validated by a registered ophthalmologist before clinical intervention."
    )
