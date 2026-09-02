"""
Retina AI: Stratified Dataset Split Generator
Generates deterministic 70% Train / 15% Val / 15% Test manifests from the APTOS 2019 dataset.
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# pyrefly: ignore [missing-import]
from src.core.config import APTOS_DATASET_DIR, IDRID_DATASET_DIR, MANIFESTS_DIR

DR_CLASS_MAP = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}


def load_idrid_records() -> pd.DataFrame:
    """Loads records from IDRiD Disease Grading groundtruth CSV files."""
    records = []
    grading_dir = IDRID_DATASET_DIR / "B. Disease Grading" / "B. Disease Grading"
    train_csv = grading_dir / "2. Groundtruths" / "a. IDRiD_Disease Grading_Training Labels.csv"
    test_csv = grading_dir / "2. Groundtruths" / "b. IDRiD_Disease Grading_Testing Labels.csv"
    
    img_dir_train = grading_dir / "1. Original Images" / "a. Training Set"
    img_dir_test = grading_dir / "1. Original Images" / "b. Testing Set"

    for csv_file, img_dir in [(train_csv, img_dir_train), (test_csv, img_dir_test)]:
        if not csv_file.is_file():
            continue
        df = pd.read_csv(csv_file)
        grade_col = [c for c in df.columns if "Retinopathy grade" in c][0]
        for _, row in df.iterrows():
            img_id = str(row["Image name"]).strip()
            if pd.isna(row[grade_col]):
                continue
            diag = int(row[grade_col])
            
            # Match image extension (.jpg, .png, .tif, .jpeg)
            matches = list(img_dir.glob(f"{img_id}.*"))
            if matches:
                img_file = matches[0]
                records.append({
                    "id_code": img_id,
                    "diagnosis": diag,
                    "diagnosis_name": DR_CLASS_MAP[diag],
                    "image_path": str(img_file.resolve()),
                    "is_referable": 1 if diag >= 2 else 0,
                    "dataset_source": "IDRiD",
                })
            else:
                print(f"[WARN] IDRiD image file missing: {img_id}")

    return pd.DataFrame(records)


def load_aptos_records() -> pd.DataFrame:
    """Loads records from APTOS dataset if present."""
    train_csv_path = APTOS_DATASET_DIR / "train.csv"
    train_images_dir = APTOS_DATASET_DIR / "train_images"

    if not train_csv_path.is_file():
        return pd.DataFrame()

    df = pd.read_csv(train_csv_path)
    records = []
    for _, row in df.iterrows():
        img_id = str(row["id_code"])
        diag = int(row["diagnosis"])
        matches = list(train_images_dir.glob(f"{img_id}.*"))
        if matches:
            img_file = matches[0]
            records.append({
                "id_code": img_id,
                "diagnosis": diag,
                "diagnosis_name": DR_CLASS_MAP[diag],
                "image_path": str(img_file.resolve()),
                "is_referable": 1 if diag >= 2 else 0,
                "dataset_source": "APTOS",
            })
    return pd.DataFrame(records)


def prepare_stratified_splits(seed: int = 42, train_ratio: float = 0.70, val_ratio: float = 0.15, test_ratio: float = 0.15):
    print("=" * 70)
    print("  RETINA AI: Generating Stratified Train / Val / Test Manifests")
    print("=" * 70)
    print(f"Random seed : {seed}")
    print(f"Ratios      : Train={train_ratio*100:.0f}%, Val={val_ratio*100:.0f}%, Test={test_ratio*100:.0f}%\n")

    idrid_df = load_idrid_records()
    aptos_df = load_aptos_records()

    frames = [f for f in [idrid_df, aptos_df] if not f.empty]
    if not frames:
        raise FileNotFoundError(f"No clinical datasets found at {IDRID_DATASET_DIR} or {APTOS_DATASET_DIR}")

    clean_df = pd.concat(frames, ignore_index=True)
    print(f"• Total verified clinical dataset images: {len(clean_df)}")
    print(f"  - IDRiD samples : {len(idrid_df)}")
    if not aptos_df.empty:
        print(f"  - APTOS samples : {len(aptos_df)}")

    # First split: Train vs Temp (Val + Test)
    temp_ratio = val_ratio + test_ratio
    df_train, df_temp = train_test_split(
        clean_df,
        test_size=temp_ratio,
        random_state=seed,
        stratify=clean_df["diagnosis"],
    )

    # Second split: Val vs Test
    test_rel_ratio = test_ratio / temp_ratio
    df_val, df_test = train_test_split(
        df_temp,
        test_size=test_rel_ratio,
        random_state=seed,
        stratify=df_temp["diagnosis"],
    )

    # Ensure manifests output directory exists
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    train_manifest = MANIFESTS_DIR / "train_split.csv"
    val_manifest = MANIFESTS_DIR / "val_split.csv"
    test_manifest = MANIFESTS_DIR / "test_split.csv"

    df_train.to_csv(train_manifest, index=False)
    df_val.to_csv(val_manifest, index=False)
    df_test.to_csv(test_manifest, index=False)

    print("\n--- Split Distributions ---")
    for name, split_df, path in [("TRAIN", df_train, train_manifest), ("VAL", df_val, val_manifest), ("TEST", df_test, test_manifest)]:
        print(f"\n[{name}] Total: {len(split_df)} samples -> {path.name}")
        dist = split_df["diagnosis"].value_counts().sort_index()
        for g, count in dist.items():
            pct = count / len(split_df) * 100
            print(f"   Grade {g} ({DR_CLASS_MAP[g]:<16}): {count:4d} ({pct:5.2f}%)")

    print("\n" + "=" * 70)
    print("  Stratified Manifest Generation Completed Successfully.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Generate stratified dataset manifests.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    prepare_stratified_splits(seed=args.seed)


if __name__ == "__main__":
    main()
