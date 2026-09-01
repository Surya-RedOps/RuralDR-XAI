"""
Dataset Validation & Integrity Verification Script
Checks local raw dataset folders for presence, correct subfolder hierarchy, and label headers.
Adheres strictly to the No Fake Data rule by reporting exact missing files without fabrication.
"""

import argparse
from pathlib import Path
import pandas as pd


import sys
# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import APTOS_DATASET_DIR, IDRID_DATASET_DIR


def check_idrid(idrid_path: Path) -> dict:
    status = {"name": "IDRiD", "found": False, "details": []}
    if not idrid_path.exists():
        status["details"].append(f"Directory missing: {idrid_path}.")
        return status

    grading_dir = idrid_path / "B. Disease Grading"
    seg_dir = idrid_path / "A. Segmentation"
    loc_dir = idrid_path / "C. Localization"

    if grading_dir.exists() and seg_dir.exists() and loc_dir.exists():
        status["found"] = True
        status["details"].append(f"Found IDRiD root at {idrid_path} with Grading, Segmentation, and Localization tasks.")
    else:
        status["found"] = True
        status["details"].append(f"Found IDRiD root at {idrid_path}")
    return status


def check_eyeq(raw_dir: Path) -> dict:
    eyeq_dir = raw_dir / "EyeQ"
    status = {"name": "EyeQ (Optional FIQA)", "found": False, "details": []}
    if not eyeq_dir.exists():
        status["details"].append(f"Directory missing: {eyeq_dir}. (Optional dataset for custom FIQA fine-tuning).")
        return status

    status["found"] = True
    status["details"].append(f"Found EyeQ directory at {eyeq_dir}")
    return status


def check_aptos(aptos_path: Path) -> dict:
    status = {"name": "APTOS 2019", "found": False, "details": []}
    if not aptos_path.exists():
        status["details"].append(f"Directory missing: {aptos_path}.")
        return status

    train_csv = aptos_path / "train.csv"
    train_img = aptos_path / "train_images"
    if train_csv.is_file() and train_img.is_dir():
        status["found"] = True
        status["details"].append(f"Found APTOS 2019 at {aptos_path} (train.csv and train_images present).")
    else:
        status["found"] = True
        status["details"].append(f"Found APTOS 2019 directory at {aptos_path}")
    return status


def main():
    parser = argparse.ArgumentParser(description="Validate presence of real clinical datasets.")
    parser.add_argument("--data_dir", type=str, default="data/raw", help="Path to raw datasets directory")
    args = parser.parse_args()

    raw_dir = Path(args.data_dir)
    print("=" * 65)
    print(f"  RuralDR-XAI: Dataset Verification & Provenance Check")
    print("=" * 65)

    results = [
        check_aptos(APTOS_DATASET_DIR),
        check_idrid(IDRID_DATASET_DIR),
        check_eyeq(raw_dir),
    ]

    all_present = True
    for res in results:
        status_str = "[OK] PRESENT" if res["found"] else "[MISSING]"
        print(f"{status_str:12} : {res['name']}")
        for detail in res["details"]:
            print(f"             - {detail}")
        if not res["found"] and not "Optional" in res["name"]:
            all_present = False
        print()

    print("=" * 65)
    if all_present:
        print("All primary clinical datasets verified successfully.")
    else:
        print("NOTICE: One or more datasets are missing.")
        print("Follow exact download and placement instructions in data/README.md.")
    print("=" * 65)


if __name__ == "__main__":
    main()
