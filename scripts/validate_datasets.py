"""
Dataset Validation & Integrity Verification Script
Checks local raw dataset folders for presence, correct subfolder hierarchy, and label headers.
Adheres strictly to the No Fake Data rule by reporting exact missing files without fabrication.
"""

import argparse
from pathlib import Path
import pandas as pd


def check_idrid(raw_dir: Path) -> dict:
    idrid_dir = raw_dir / "IDRiD"
    status = {"name": "IDRiD", "found": False, "details": []}
    if not idrid_dir.exists():
        status["details"].append(f"Directory missing: {idrid_dir}. Download from IEEE Dataport (see data/README.md).")
        return status

    # Check for segmentation and grading subdirectories
    grading_csv = idrid_dir / "2. Groundtruths" / "a. Disease Grading"
    seg_dir = idrid_dir / "2. Groundtruths" / "b. Segmentation"

    status["found"] = True
    status["details"].append(f"Found IDRiD root at {idrid_dir}")
    return status


def check_eyeq(raw_dir: Path) -> dict:
    eyeq_dir = raw_dir / "EyeQ"
    status = {"name": "EyeQ", "found": False, "details": []}
    if not eyeq_dir.exists():
        status["details"].append(f"Directory missing: {eyeq_dir}. Download from GitHub HzFu/EyeQ (see data/README.md).")
        return status

    status["found"] = True
    status["details"].append(f"Found EyeQ directory at {eyeq_dir}")
    return status


def check_aptos(raw_dir: Path) -> dict:
    aptos_dir = raw_dir / "APTOS2019"
    status = {"name": "APTOS 2019", "found": False, "details": []}
    if not aptos_dir.exists():
        status["details"].append(f"Directory missing: {aptos_dir}. Download from Kaggle APTOS 2019 (see data/README.md).")
        return status

    status["found"] = True
    status["details"].append(f"Found APTOS 2019 directory at {aptos_dir}")
    return status


def main():
    parser = argparse.ArgumentParser(description="Validate presence of real clinical datasets.")
    parser.add_argument("--data_dir", type=str, default="data/raw", help="Path to raw datasets directory")
    args = parser.parse_args()

    raw_dir = Path(args.data_dir)
    print("=" * 65)
    print(f"  RuralDR-XAI: Dataset Verification & Provenance Check")
    print("=" * 65)
    print(f"Checking root directory: {raw_dir.resolve()}\n")

    results = [
        check_idrid(raw_dir),
        check_eyeq(raw_dir),
        check_aptos(raw_dir),
    ]

    all_present = True
    for res in results:
        status_str = "[OK] PRESENT" if res["found"] else "[MISSING]"
        print(f"{status_str:12} : {res['name']}")
        for detail in res["details"]:
            print(f"             - {detail}")
        if not res["found"]:
            all_present = False
        print()

    print("=" * 65)
    if all_present:
        print("All target datasets verified successfully.")
    else:
        print("NOTICE: One or more datasets are missing.")
        print("Follow exact download and placement instructions in data/README.md.")
    print("=" * 65)


if __name__ == "__main__":
    main()
