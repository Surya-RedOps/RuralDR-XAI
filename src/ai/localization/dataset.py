"""
Retina AI: IDRiD Localization Dataset Loader
Parses Optic Disc and Fovea center coordinate CSV files from the IDRiD Localization dataset.

IDRiD Localization Structure:
  C. Localization / C. Localization /
    1. Original Images /
      a. Training Set / IDRiD_XXX.jpg
      b. Testing Set / IDRiD_XXX.jpg
    2. Groundtruths /
      1. Optic Disc Center Location /
        a. IDRiD_OD_Center_Training Set_Markups.csv
        b. IDRiD_OD_Center_Testing Set_Markups.csv
      2. Fovea Center Location /
        IDRiD_Fovea_Center_Training Set_Markups.csv
        IDRiD_Fovea_Center_Testing Set_Markups.csv

CSV format: Image No, X-Coordinate, Y-Coordinate, ...trailing empty columns
"""

from typing import Dict, Tuple, Optional, List
from pathlib import Path
import csv


def load_localization_csv(
    csv_path: Path,
) -> Dict[str, Tuple[int, int]]:
    """
    Parses an IDRiD localization CSV and returns a mapping of image_id -> (x, y).

    Args:
        csv_path: Path to the CSV file

    Returns:
        Dict mapping image ID (e.g., "IDRiD_001") to (x_coordinate, y_coordinate)
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Localization CSV not found: {csv_path}")

    result = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header row

        for row in reader:
            if len(row) < 3:
                continue

            image_id = row[0].strip()
            try:
                x = int(row[1].strip())
                y = int(row[2].strip())
                result[image_id] = (x, y)
            except (ValueError, IndexError):
                continue

    return result


def load_optic_disc_centers(
    idrid_root: Path,
    split: str = "train",
) -> Dict[str, Tuple[int, int]]:
    """Loads optic disc center coordinates for the given split."""
    loc_root = idrid_root / "C. Localization" / "C. Localization" / "2. Groundtruths"
    od_dir = loc_root / "1. Optic Disc Center Location"

    if split == "train":
        csv_path = od_dir / "a. IDRiD_OD_Center_Training Set_Markups.csv"
    else:
        csv_path = od_dir / "b. IDRiD_OD_Center_Testing Set_Markups.csv"

    return load_localization_csv(csv_path)


def load_fovea_centers(
    idrid_root: Path,
    split: str = "train",
) -> Dict[str, Tuple[int, int]]:
    """Loads fovea center coordinates for the given split."""
    loc_root = idrid_root / "C. Localization" / "C. Localization" / "2. Groundtruths"
    fovea_dir = loc_root / "2. Fovea Center Location"

    if split == "train":
        csv_path = fovea_dir / "IDRiD_Fovea_Center_Training Set_Markups.csv"
    else:
        csv_path = fovea_dir / "IDRiD_Fovea_Center_Testing Set_Markups.csv"

    return load_localization_csv(csv_path)


def build_localization_manifest(
    idrid_root: Path,
    split: str = "train",
) -> List[Dict]:
    """
    Builds a complete localization manifest with image paths and ground-truth coordinates.

    Returns:
        List of dicts with: image_id, image_path, od_center, fovea_center
    """
    loc_root = idrid_root / "C. Localization" / "C. Localization"

    if split == "train":
        img_dir = loc_root / "1. Original Images" / "a. Training Set"
    else:
        img_dir = loc_root / "1. Original Images" / "b. Testing Set"

    od_centers = load_optic_disc_centers(idrid_root, split)
    fovea_centers = load_fovea_centers(idrid_root, split)

    manifest = []
    if img_dir.exists():
        for img_path in sorted(img_dir.glob("IDRiD_*.jpg")):
            image_id = img_path.stem
            manifest.append({
                "image_id": image_id,
                "image_path": str(img_path),
                "od_center": od_centers.get(image_id),
                "fovea_center": fovea_centers.get(image_id),
            })

    return manifest
