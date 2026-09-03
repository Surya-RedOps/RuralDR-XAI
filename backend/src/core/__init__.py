"""Core contracts and config for RuralDR-XAI"""
from .contracts import (
    QualityStatus,
    DRGrade,
    DR_GRADE_NAMES,
    ConsistencyStatus,
    ReviewPriority,
    QualityMetrics,
    RetinalAnatomy,
    LesionInventory,
    SeverityPrediction,
    EvidenceConsistency,
    ScreeningResult,
)
from .config import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    MANIFESTS_DIR,
    MODELS_DIR,
    CHECKPOINTS_DIR,
    RESULTS_DIR,
    DEFAULT_IMAGE_SIZE,
    NUM_CLASSES,
    QUALITY_THRESHOLDS,
)
