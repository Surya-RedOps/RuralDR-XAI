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

from src.core.config import APTOS_DATASET_DIR, MANIFESTS_DIR

DR_CLASS_MAP = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}


def prepare_stratified_splits(seed: int = 42, train_ratio: float = 0.70, val_ratio: float = 0.15, test_ratio: float = 0.15):
    print("=" * 70)
    print("  RETINA AI: Generating Stratified Train / Val / Test Manifests")
    print("=" * 70)
    print(f"Dataset root: {APTOS_DATASET_DIR}")
    print(f"Random seed : {seed}")
    print(f"Ratios      : Train={train_ratio*100:.0f}%, Val={val_ratio*100:.0f}%, Test={test_ratio*100:.0f}%\n")

    train_csv_path = APTOS_DATASET_DIR / "train.csv"
    train_images_dir = APTOS_DATASET_DIR / "train_images"

    if not train_csv_path.is_file():
        raise FileNotFoundError(f"APTOS train.csv not found at {train_csv_path}")

    df = pd.read_csv(train_csv_path)
    print(f"• Total dataset rows: {len(df)}")

    # Add relative/absolute image paths and verify existence
    valid_records = []
    for _, row in df.iterrows():
        img_id = str(row["id_code"])
        diag = int(row["diagnosis"])
        img_file = train_images_dir / f"{img_id}.png"
        if img_file.is_file():
            valid_records.append({
                "id_code": img_id,
                "diagnosis": diag,
                "diagnosis_name": DR_CLASS_MAP[diag],
                "image_path": str(img_file.resolve()),
                "is_referable": 1 if diag >= 2 else 0,
            })
        else:
            print(f"[WARN] Image file missing: {img_file}")

    clean_df = pd.DataFrame(valid_records)
    print(f"• Valid verified images: {len(clean_df)}")

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
