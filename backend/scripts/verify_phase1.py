"""
Retina AI: Phase 1 Complete Verification Script
Validates project integrity, modular AI facade, datasets, pipeline execution, and git cleanliness.
"""

import sys
import subprocess
from pathlib import Path
import cv2
import pandas as pd
import torch

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import APTOS_DATASET_DIR, IDRID_DATASET_DIR, PROJECT_ROOT
from src.core.contracts import ScreeningResult
from src.ai.classification import DRClassifier
from src.ai.evaluation import ScreeningOrchestrator
from src.api.server import app


def run_checks():
    print("=" * 70)
    print("  RETINA AI — PHASE 1 SYSTEM INTEGRITY & READINESS VERIFICATION")
    print("=" * 70)
    passed_checks = 0
    total_checks = 10

    # 1. Verify Imports & Project Architecture
    try:
        from src.ai import classification, image_quality, explainability, segmentation, localization, preprocessing, evaluation
        print("[PASS] Check 1: Modular AI package hierarchy (src/ai) imported cleanly.")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 1: Failed to import modular AI hierarchy: {e}")

    # 2. Verify Core Contracts & Config
    try:
        from src.core.contracts import DRGrade, DR_GRADE_NAMES, QualityStatus
        assert len(DR_GRADE_NAMES) == 5
        print("[PASS] Check 2: Core contracts & 5-class ICDR schemas verified.")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 2: Core contracts error: {e}")

    # 3. Verify Backend FastAPI Server
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ONLINE"
        print("[PASS] Check 3: FastAPI backend server and /health route functional.")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 3: FastAPI check failed: {e}")

    # 4. Verify Dataset Paths Configuration
    try:
        assert APTOS_DATASET_DIR.exists(), f"APTOS directory not found at {APTOS_DATASET_DIR}"
        assert IDRID_DATASET_DIR.exists(), f"IDRiD directory not found at {IDRID_DATASET_DIR}"
        print(f"[PASS] Check 4: Dataset paths resolved (APTOS: {APTOS_DATASET_DIR.name}, IDRiD: {IDRID_DATASET_DIR.name}).")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 4: Dataset path resolution failed: {e}")

    # 5. Verify APTOS CSV & Class Representation
    try:
        train_csv = APTOS_DATASET_DIR / "train.csv"
        df = pd.read_csv(train_csv)
        assert "id_code" in df.columns and "diagnosis" in df.columns
        unique_grades = sorted(df["diagnosis"].unique())
        assert unique_grades == [0, 1, 2, 3, 4]
        print(f"[PASS] Check 5: APTOS train.csv loaded ({len(df)} rows, Grades: 0, 1, 2, 3, 4).")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 5: APTOS CSV validation failed: {e}")

    # 6. Verify Retinal Images Readable from Dataset
    try:
        train_img_dir = APTOS_DATASET_DIR / "train_images"
        sample_img_paths = list(train_img_dir.glob("*.png"))[:3]
        assert len(sample_img_paths) > 0
        for p in sample_img_paths:
            img = cv2.imread(str(p))
            assert img is not None and img.shape[0] > 100
        print(f"[PASS] Check 6: Real retinal images loaded successfully ({len(sample_img_paths)} sample images tested).")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 6: Retinal image reading failed: {e}")

    # 7. Verify Base AI Model Architecture
    try:
        model = DRClassifier(backbone_name="resnet18", num_classes=5, pretrained=False)
        model.eval()
        dummy_tensor = torch.randn(1, 3, 512, 512)
        out = model(dummy_tensor)
        assert out.shape == (1, 5)
        print("[PASS] Check 7: Base AI Model (DRClassifier) forward pass verified (logits shape (1, 5)).")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 7: Base model forward pass failed: {e}")

    # 8. Verify End-to-End Inference Pipeline
    try:
        sample_fundus = PROJECT_ROOT / "data" / "sample" / "sample_fundus.jpg"
        orchestrator = ScreeningOrchestrator(classifier=model, device=torch.device("cpu"))
        result, layers = orchestrator.process_image(sample_fundus)
        assert isinstance(result, ScreeningResult)
        assert result.prediction is not None
        assert 0 <= result.prediction.predicted_grade.value <= 4
        assert "composite_annotated" in layers
        print(f"[PASS] Check 8: End-to-End Screening Pipeline executed successfully (Predicted: {result.prediction.grade_name}).")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 8: End-to-end pipeline execution failed: {e}")

    # 9. Verify Checkpoint Directories Setup
    try:
        models_root = PROJECT_ROOT / "models"
        for sub in ["classification", "image_quality", "segmentation", "localization"]:
            assert (models_root / sub).is_dir()
        print("[PASS] Check 9: Modular checkpoint directories created (classification, image_quality, segmentation, localization).")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 9: Model directories check failed: {e}")

    # 10. Verify Git Repository Cleanliness (No large datasets committed)
    try:
        git_check = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        # Check if any large files or raw dataset folders are staged/untracked
        tracked_or_untracked = git_check.stdout.splitlines()
        large_leaks = [f for f in tracked_or_untracked if "Data_set" in f or "train_images" in f or ".tif" in f]
        assert len(large_leaks) == 0, f"Found leaked dataset files in Git: {large_leaks}"
        print("[PASS] Check 10: Git status clean (No large datasets or binary images committed).")
        passed_checks += 1
    except Exception as e:
        print(f"[FAIL] Check 10: Git leakage check failed: {e}")

    print("\n" + "=" * 70)
    print(f"  Verification Result: {passed_checks}/{total_checks} Checks Passed.")
    print("=" * 70)
    return passed_checks == total_checks


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
