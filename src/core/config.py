"""
RuralDR-XAI: Global Configuration & Hyperparameters
"""

from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent

# Centralized Dataset Paths (configurable via environment variables or default to local workspace layout)
APTOS_DATASET_DIR = Path(os.getenv("APTOS_DATASET_DIR", str(WORKSPACE_ROOT / "Data_set" / "aptos2019-blindness-detection")))
IDRID_DATASET_DIR = Path(os.getenv("IDRID_DATASET_DIR", str(WORKSPACE_ROOT / "IDRiD")))

# Internal application directories
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", str(DATA_DIR / "raw")))
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MANIFESTS_DIR = DATA_DIR / "manifests"
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(PROJECT_ROOT / "models")))
CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", str(PROJECT_ROOT / "results")))

# Standard image processing constants
DEFAULT_IMAGE_SIZE = (512, 512)
NUM_CLASSES = 5  # ICDR Grade 0 to 4

# Quality Gate default thresholds (tunable on validation set)
QUALITY_THRESHOLDS = {
    "min_focus_tenengrad": 15.0,
    "min_focus_laplacian": 40.0,
    "min_entropy": 4.2,
    "min_fov_coverage": 0.45,
    "max_glare_ratio": 0.12,
    "quality_pass_score": 0.60,
    "borderline_score": 0.40,
}

# Calibration defaults
DEFAULT_TEMPERATURE = 1.25

# Offline Edge Cache settings
MAX_LOCAL_QUEUE_SIZE = 5000
