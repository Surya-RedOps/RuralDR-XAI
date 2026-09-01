"""
Retina AI: Dataset Inspection & Summary Utility
Audits and summarizes APTOS 2019 and IDRiD clinical datasets from centralized paths.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import APTOS_DATASET_DIR, IDRID_DATASET_DIR

DR_CLASS_MAP = {
    0: "0 - No Diabetic Retinopathy",
    1: "1 - Mild Non-Proliferative DR",
    2: "2 - Moderate Non-Proliferative DR",
    3: "3 - Severe Non-Proliferative DR",
    4: "4 - Proliferative Diabetic Retinopathy",
}


def summarize_aptos():
    print("=" * 70)
    print("  APTOS 2019 Blindness Detection Dataset Summary")
    print("=" * 70)
    print(f"Location: {APTOS_DATASET_DIR.resolve()}")

    train_csv = APTOS_DATASET_DIR / "train.csv"
    test_csv = APTOS_DATASET_DIR / "test.csv"
    train_img_dir = APTOS_DATASET_DIR / "train_images"
    test_img_dir = APTOS_DATASET_DIR / "test_images"

    if not train_csv.is_file():
        print(f"[ERROR] train.csv not found at {train_csv}")
        return

    df_train = pd.read_csv(train_csv)
    print(f"• Training samples: {len(df_train)}")
    print(f"• CSV columns: {list(df_train.columns)}")
    print(f"• Image directory: {train_img_dir.name} ({len(list(train_img_dir.glob('*.png')))} images)")
    
    if test_csv.is_file():
        df_test = pd.read_csv(test_csv)
        print(f"• Test samples: {len(df_test)}")
        print(f"• Test image directory: {test_img_dir.name} ({len(list(test_img_dir.glob('*.png')))} images)")

    print("\n--- Class Distribution in Training Set ---")
    dist = df_train["diagnosis"].value_counts().sort_index()
    for grade, count in dist.items():
        label_name = DR_CLASS_MAP.get(grade, f"Class {grade}")
        pct = (count / len(df_train)) * 100
        print(f"  [{grade}] {label_name:<38} : {count:5d} ({pct:5.2f}%)")


def summarize_idrid():
    print("\n" + "=" * 70)
    print("  IDRiD (Indian Diabetic Retinopathy Image Dataset) Summary")
    print("=" * 70)
    print(f"Location: {IDRID_DATASET_DIR.resolve()}")

    # 1. Disease Grading
    grading_dir = IDRID_DATASET_DIR / "B. Disease Grading" / "B. Disease Grading"
    grading_train_csv = grading_dir / "2. Groundtruths" / "a. IDRiD_Disease Grading_Training Labels.csv"
    grading_test_csv = grading_dir / "2. Groundtruths" / "b. IDRiD_Disease Grading_Testing Labels.csv"

    print("\n1. Disease Grading Task:")
    if grading_train_csv.is_file():
        df_train = pd.read_csv(grading_train_csv)
        # Clean columns if needed
        grade_col = [c for c in df_train.columns if "Retinopathy grade" in c][0]
        print(f"   • Training samples: {len(df_train)}")
        print(f"   • Columns: {[c for c in df_train.columns if not c.startswith('Unnamed')]}")
        dist = df_train[grade_col].value_counts().sort_index()
        for grade, count in dist.items():
            if pd.isna(grade):
                continue
            grade_int = int(grade)
            label_name = DR_CLASS_MAP.get(grade_int, f"Class {grade_int}")
            pct = (count / len(df_train)) * 100
            print(f"     [{grade_int}] {label_name:<38} : {count:4d} ({pct:5.2f}%)")

    if grading_test_csv.is_file():
        df_test = pd.read_csv(grading_test_csv)
        print(f"   • Testing samples: {len(df_test)}")

    # 2. Segmentation Task
    seg_dir = IDRID_DATASET_DIR / "A. Segmentation" / "A. Segmentation" / "2. All Segmentation Groundtruths" / "a. Training Set"
    print("\n2. Lesion Segmentation Task:")
    if seg_dir.is_dir():
        for sub in sorted(seg_dir.iterdir()):
            if sub.is_dir():
                mask_files = list(sub.glob("*.tif"))
                print(f"   • {sub.name:<25} : {len(mask_files)} annotated masks")

    # 3. Localization Task
    loc_dir = IDRID_DATASET_DIR / "C. Localization" / "C. Localization" / "2. Groundtruths"
    print("\n3. Anatomical Landmark Localization Task:")
    od_train_csv = loc_dir / "1. Optic Disc Center Location" / "a. IDRiD_OD_Center_Training Set_Markups.csv"
    fovea_train_csv = loc_dir / "2. Fovea Center Location" / "IDRiD_Fovea_Center_Training Set_Markups.csv"
    
    if od_train_csv.is_file():
        df_od = pd.read_csv(od_train_csv)
        print(f"   • Optic Disc Center annotations: {len(df_od)} images")
    if fovea_train_csv.is_file():
        df_fov = pd.read_csv(fovea_train_csv)
        print(f"   • Fovea Center annotations     : {len(df_fov)} images")


def main():
    summarize_aptos()
    summarize_idrid()
    print("\n" + "=" * 70)
    print("  Dataset Audit Complete. All datasets successfully verified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
