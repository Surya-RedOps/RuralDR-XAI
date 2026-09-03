"""
Retina AI: Retinal Dataset Loader & Augmentation Pipeline
Loads fundus images from split manifests and applies standardized clinical preprocessing and augmentations.
"""

from typing import Tuple, Optional, Callable, Union
from pathlib import Path
import random
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset

from ...preprocess.clahe import apply_lab_clahe


def load_and_preprocess_image(
    image_input: Union[str, Path, np.ndarray, Image.Image],
    target_size: Tuple[int, int] = (224, 224),
    apply_clahe: bool = True,
    clip_limit: float = 2.0,
) -> np.ndarray:
    """
    Safely loads and standardizes a fundus image without RAM spikes.
    Applies resolution standardization and adaptive Lab CLAHE.
    """
    if isinstance(image_input, (str, Path)):
        img_path = Path(image_input)
        if not img_path.is_file():
            return np.zeros((target_size[0], target_size[1], 3), dtype=np.uint8)
        try:
            with Image.open(img_path) as pil_img:
                pil_rgb = pil_img.convert("RGB").resize(target_size, Image.Resampling.BILINEAR)
                img_rgb = np.array(pil_rgb, dtype=np.uint8)
        except Exception:
            return np.zeros((target_size[0], target_size[1], 3), dtype=np.uint8)
    elif isinstance(image_input, Image.Image):
        pil_rgb = image_input.convert("RGB").resize(target_size, Image.Resampling.BILINEAR)
        img_rgb = np.array(pil_rgb, dtype=np.uint8)
    elif isinstance(image_input, np.ndarray):
        if image_input.shape[:2] != target_size:
            img_rgb = cv2.resize(image_input, target_size, interpolation=cv2.INTER_AREA)
        else:
            img_rgb = image_input
    else:
        return np.zeros((target_size[0], target_size[1], 3), dtype=np.uint8)

    # Apply adaptive Lab CLAHE
    if apply_clahe:
        try:
            enhanced = apply_lab_clahe(img_rgb, clip_limit=clip_limit)
        except Exception:
            enhanced = img_rgb
    else:
        enhanced = img_rgb

    return enhanced


class RetinalFundusDataset(Dataset):
    """
    PyTorch Dataset for Diabetic Retinopathy Classification.
    """

    def __init__(
        self,
        manifest_path: Path,
        target_size: Tuple[int, int] = (224, 224),
        is_train: bool = False,
        apply_clahe: bool = True,
    ):
        self.manifest_path = Path(manifest_path)
        if not self.manifest_path.is_file():
            raise FileNotFoundError(f"Manifest file not found: {self.manifest_path}")

        self.df = pd.read_csv(self.manifest_path)
        self.target_size = target_size
        self.is_train = is_train
        self.apply_clahe = apply_clahe

        # ImageNet normalization parameters
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __len__(self) -> int:
        return len(self.df)

    def _augment(self, image_rgb: np.ndarray) -> np.ndarray:
        """
        Medically sound fundus augmentations:
        - Horizontal flip (simulates left/right eye symmetry)
        - Mild rotation (+/- 15 degrees)
        - Slight brightness/contrast variation (+/- 10%)
        """
        # 1. Random Horizontal Flip
        if random.random() > 0.5:
            image_rgb = cv2.flip(image_rgb, 1)

        # 2. Random Small Rotation
        if random.random() > 0.5:
            angle = random.uniform(-15.0, 15.0)
            h, w = image_rgb.shape[:2]
            center = (w // 2, h // 2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            image_rgb = cv2.warpAffine(image_rgb, rot_mat, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

        # 3. Random Mild Brightness / Contrast Jitter
        if random.random() > 0.5:
            alpha = random.uniform(0.9, 1.1)  # contrast
            beta = random.uniform(-10, 10)    # brightness
            image_rgb = np.clip(alpha * image_rgb.astype(np.float32) + beta, 0, 255).astype(np.uint8)

        return image_rgb

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, str]:
        row = self.df.iloc[idx]
        image_path = str(row["image_path"])
        label = int(row["diagnosis"])
        id_code = str(row["id_code"])

        # Load & Preprocess
        processed_rgb = load_and_preprocess_image(
            image_path,
            target_size=self.target_size,
            apply_clahe=self.apply_clahe,
        )

        # Augment (if training)
        if self.is_train:
            processed_rgb = self._augment(processed_rgb)

        # Normalize to [0, 1] then ImageNet mean/std
        norm_img = processed_rgb.astype(np.float32) / 255.0
        norm_img = (norm_img - self.mean) / self.std

        # Convert to Tensor (3, H, W)
        tensor = torch.from_numpy(norm_img).permute(2, 0, 1).float()

        return tensor, label, id_code
