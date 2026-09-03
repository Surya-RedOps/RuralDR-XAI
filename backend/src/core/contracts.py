"""
RuralDR-XAI: Core Type Definitions and Data Contracts
Enforces strict schema consistency across all pipeline stages.
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel, Field


class ModalityStatus(str, Enum):
    FUNDUS = "FUNDUS"
    NON_FUNDUS = "NON_FUNDUS"
    UNCERTAIN = "UNCERTAIN"


class PipelineStatus(str, Enum):
    SUCCESS = "success"
    REJECTED = "rejected"
    UNGRADABLE = "ungradable"
    UNCERTAIN = "uncertain"
    ERROR = "error"


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


class ModalityVerificationResult(BaseModel):
    status: ModalityStatus
    fundus_probability: float = Field(ge=0.0, le=1.0, description="Model probability that image is retinal fundus")
    confidence: float = Field(ge=0.0, le=1.0)
    is_fundus: bool
    rejection_reason: Optional[str] = None
    color_plausibility_score: float = Field(default=1.0, ge=0.0, le=1.0)
    geometry_plausibility_score: float = Field(default=1.0, ge=0.0, le=1.0)
    details: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = (
        "Pre-classification modality gate. Out-of-domain rejection only. "
        "Does not medically authenticate ocular pathology."
    )


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
    is_referable: bool  # True if Grade >= 1 for screening triage or Grade >= 2
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
    status: PipelineStatus = PipelineStatus.SUCCESS
    modality: Optional[ModalityVerificationResult] = None
    quality: Optional[QualityMetrics] = None
    anatomy: Optional[RetinalAnatomy] = None
    lesions: Optional[LesionInventory] = None
    prediction: Optional[SeverityPrediction] = None
    evidence_consistency: Optional[EvidenceConsistency] = None
    rejection_reason: Optional[str] = None
    triage_decision: str
    review_priority: ReviewPriority
    disclaimer: str = (
        "RuralDR-XAI is an investigational decision-support tool for rural screening triage. "
        "Findings must be validated by a registered ophthalmologist before clinical intervention."
    )


class GradCAMResult(BaseModel):
    """Grad-CAM attribution result for a single class."""
    target_class: int = Field(ge=0, le=4, description="Target DR grade class index")
    target_class_name: str = ""
    heatmap_path: Optional[str] = None
    overlay_path: Optional[str] = None
    binary_mask_path: Optional[str] = None
    is_valid: bool = True
    activation_coverage: float = Field(default=0.0, ge=0.0, le=1.0,
        description="Fraction of image with non-trivial activation (>0.1)")
    peak_intensity: float = Field(default=0.0, ge=0.0, le=1.0,
        description="Maximum activation value in the heatmap")
    quality_flags: List[str] = Field(default_factory=list,
        description="Warnings: 'blank_heatmap', 'saturated_heatmap', 'low_coverage'")
    disclaimer: str = (
        "Grad-CAM shows model attention regions contributing to the predicted class. "
        "It does NOT identify specific lesions or provide clinical proof."
    )


class LesionDetectionResult(BaseModel):
    """Per-lesion-type detection result from segmentation."""
    lesion_type: str
    detected: bool = False
    mask_path: Optional[str] = None
    pixel_area: int = 0
    relative_area_pct: float = 0.0
    num_connected_components: int = 0
    mean_confidence: float = Field(default=0.0, ge=0.0, le=1.0,
        description="Mean model probability over positive predictions")
    approximate_locations: List[Tuple[int, int]] = Field(default_factory=list,
        description="Centroids of detected lesion clusters (x, y)")
    disclaimer: str = "AI-detected retinal feature. Requires clinical confirmation."


class LesionSegmentationResult(BaseModel):
    """Combined lesion segmentation result across all lesion types."""
    lesions: List[LesionDetectionResult] = Field(default_factory=list)
    model_path: Optional[str] = None
    input_resolution: Tuple[int, int] = (512, 512)
    segmentation_time_ms: float = 0.0


class ExplainableScreeningResult(BaseModel):
    """Complete Phase 4 explainability pipeline output."""
    case_id: str = ""
    timestamp: str = ""
    status: PipelineStatus = PipelineStatus.SUCCESS

    # Image provenance
    original_image_path: Optional[str] = None
    enhanced_image_path: Optional[str] = None
    inference_image_source: str = "original"  # "original" or "enhanced"

    # Modality gate
    modality_status: Optional[str] = None
    modality_verified: bool = False
    rejection_reason: Optional[str] = None

    # Quality gate
    quality_status: str = ""
    quality_score: float = 0.0
    is_gradeable: bool = False

    # DR Classification
    dr_grade: Optional[int] = None
    severity: Optional[str] = None
    classification_confidence: Optional[float] = None
    is_referable: Optional[bool] = None
    class_probabilities: Optional[Dict[str, float]] = None

    # Explainability
    gradcam_result: Optional[GradCAMResult] = None

    # Lesion Segmentation
    segmentation_result: Optional[LesionSegmentationResult] = None

    # Timing
    modality_gate_time_ms: float = 0.0
    quality_gate_time_ms: float = 0.0
    classification_time_ms: float = 0.0
    gradcam_time_ms: float = 0.0
    segmentation_time_ms: float = 0.0
    total_pipeline_time_ms: float = 0.0

    # Medical safety
    evidence_summary: List[str] = Field(default_factory=list,
        description="Human-readable AI evidence statements")
    disclaimer: str = (
        "AI screening result only. All findings require clinical confirmation "
        "by a qualified ophthalmologist. This system does not provide definitive diagnoses."
    )
