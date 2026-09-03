"""
IDRiD Segmentation Dataset Loader
Loads original images and per-lesion binary ground-truth masks from the IDRiD dataset.
Applies joint spatial augmentations to both images and masks.

IDRiD Segmentation Structure:
  1. Original Images / a. Training Set / IDRiD_XX.jpg
  2. All Segmentation Groundtruths / a. Training Set /
     1. Microaneurysms / IDRiD_XX_MA.tif
     2. Haemorrhages / IDRiD_XX_HE.tif
     3. Hard Exudates / IDRiD_XX_EX.tif
     4. Soft Exudates / IDRiD_XX_SE.tif   (sparse: not all images have SE)
     5. Optic Disc / IDRiD_XX_OD.tif       (not used for lesion segmentation)

Mask format: Palette-mode TIF, binary {0, 1}
"""

from typing import Tuple, Optional, Dict, List
from pathlib import Path
import random
import cv2
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset


# Lesion categories and their file suffixes
LESION_CATEGORIES = {
    "microaneurysms": {"dir": "1. Microaneurysms", "suffix": "_MA"},
    "haemorrhages": {"dir": "2. Haemorrhages", "suffix": "_HE"},
    "hard_exudates": {"dir": "3. Hard Exudates", "suffix": "_EX"},
    "soft_exudates": {"dir": "4. Soft Exudates", "suffix": "_SE"},
}

# ImageNet normalization
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def build_idrid_segmentation_manifest(
    idrid_root: Path,
    split: str = "train",
) -> List[Dict[str, Optional[str]]]:
    """
    Builds a manifest mapping each image to its per-lesion mask paths.

    Returns:
        List of dicts with keys: 'image_id', 'image_path', 'microaneurysms', 'haemorrhages',
        'hard_exudates', 'soft_exudates'
    """
    seg_root = idrid_root / "A. Segmentation" / "A. Segmentation"

    if split == "train":
        img_dir = seg_root / "1. Original Images" / "a. Training Set"
        gt_dir = seg_root / "2. All Segmentation Groundtruths" / "a. Training Set"
    else:
        img_dir = seg_root / "1. Original Images" / "b. Testing Set"
        gt_dir = seg_root / "2. All Segmentation Groundtruths" / "b. Testing Set"

    if not img_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {img_dir}")

    manifest = []
    for img_path in sorted(img_dir.glob("IDRiD_*.jpg")):
        image_id = img_path.stem  # e.g., "IDRiD_01"

        entry = {
            "image_id": image_id,
            "image_path": str(img_path),
        }

        for lesion_name, info in LESION_CATEGORIES.items():
            mask_filename = f"{image_id}{info['suffix']}.tif"
            mask_path = gt_dir / info["dir"] / mask_filename
            entry[lesion_name] = str(mask_path) if mask_path.is_file() else None

        manifest.append(entry)

    return manifest


class IDRiDSegmentationDataset(Dataset):
    """
    PyTorch Dataset for IDRiD lesion segmentation.

    Loads images and multi-label binary masks with joint spatial augmentation.
    """

    def __init__(
        self,
        manifest: List[Dict[str, Optional[str]]],
        target_size: Tuple[int, int] = (512, 512),
        is_train: bool = False,
        augment: bool = True,
    ):
        self.manifest = manifest
        self.target_size = target_size
        self.is_train = is_train
        self.augment = augment and is_train
        self.lesion_names = list(LESION_CATEGORIES.keys())

    def __len__(self) -> int:
        return len(self.manifest)

    def _load_image(self, path: str) -> np.ndarray:
        """Load image as RGB uint8 numpy array."""
        with Image.open(path) as img:
            return np.array(img.convert("RGB"), dtype=np.uint8)

    def _load_mask(self, path: Optional[str], target_h: int, target_w: int) -> np.ndarray:
        """Load binary mask, or return zeros if path is None (missing annotation)."""
        if path is None or not Path(path).is_file():
            return np.zeros((target_h, target_w), dtype=np.float32)

        with Image.open(path) as mask_img:
            mask_np = np.array(mask_img, dtype=np.float32)

        # Ensure binary {0, 1}
        if mask_np.max() > 1:
            mask_np = (mask_np > 0).astype(np.float32)

        return mask_np

    def _joint_augment(
        self,
        image: np.ndarray,
        masks: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply identical spatial augmentations to image and all masks.
        Only uses augmentations that maintain image-mask alignment.

        Args:
            image: (H, W, 3) uint8
            masks: (num_classes, H, W) float32
        """
        h, w = image.shape[:2]

        # 1. Random horizontal flip
        if random.random() > 0.5:
            image = cv2.flip(image, 1)
            masks = masks[:, :, ::-1].copy()

        # 2. Random vertical flip
        if random.random() > 0.5:
            image = cv2.flip(image, 0)
            masks = masks[:, ::-1, :].copy()

        # 3. Random rotation (±15 degrees)
        if random.random() > 0.5:
            angle = random.uniform(-15.0, 15.0)
            center = (w // 2, h // 2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)

            image = cv2.warpAffine(image, rot_mat, (w, h),
                                   flags=cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_REFLECT)
            for i in range(masks.shape[0]):
                masks[i] = cv2.warpAffine(masks[i], rot_mat, (w, h),
                                          flags=cv2.INTER_NEAREST,
                                          borderMode=cv2.BORDER_CONSTANT,
                                          borderValue=0)

        # 4. Random brightness/contrast jitter (image only, not masks)
        if random.random() > 0.5:
            alpha = random.uniform(0.9, 1.1)
            beta = random.uniform(-10, 10)
            image = np.clip(alpha * image.astype(np.float32) + beta, 0, 255).astype(np.uint8)

        return image, masks

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, str]:
        """
        Returns:
            image_tensor: (3, H, W) float32 ImageNet-normalized
            mask_tensor: (num_classes, H, W) float32 binary {0.0, 1.0}
            image_id: str
        """
        entry = self.manifest[idx]
        image_id = entry["image_id"]
        target_h, target_w = self.target_size

        # Load and resize image using OpenCV (avoids PIL memory overhead)
        img_bgr = cv2.imread(entry["image_path"])
        if img_bgr is not None:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            image_rgb = cv2.resize(img_rgb, (target_w, target_h), interpolation=cv2.INTER_AREA)
        else:
            image_rgb = np.zeros((target_h, target_w, 3), dtype=np.uint8)

        # Load and resize each mask using OpenCV
        resized_masks = np.zeros((len(self.lesion_names), target_h, target_w), dtype=np.float32)
        for i, lesion_name in enumerate(self.lesion_names):
            mask_path = entry.get(lesion_name)
            if mask_path and Path(mask_path).is_file():
                mask_raw = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
                if mask_raw is not None:
                    mask_resized = cv2.resize(mask_raw, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
                    resized_masks[i] = (mask_resized > 0).astype(np.float32)

        # Apply joint augmentation
        if self.augment:
            image_rgb, resized_masks = self._joint_augment(image_rgb, resized_masks)

        # Normalize image
        norm_img = image_rgb.astype(np.float32) / 255.0
        norm_img = (norm_img - IMAGENET_MEAN) / IMAGENET_STD

        # Convert to tensors
        image_tensor = torch.from_numpy(norm_img).permute(2, 0, 1).float()
        mask_tensor = torch.from_numpy(resized_masks).float()

        return image_tensor, mask_tensor, image_id


