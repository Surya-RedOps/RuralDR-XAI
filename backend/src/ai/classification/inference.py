"""
Retina AI: Independent DR Severity Inference Module
Provides standardized, reproducible inference for Diabetic Retinopathy screening with probability calibration.
"""

from typing import Union, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import cv2
import numpy as np
import torch

from ...core.config import MODELS_DIR, CHECKPOINTS_DIR
from ...core.contracts import DRGrade, DR_GRADE_NAMES
from .dataset import load_and_preprocess_image
from ...models.classifier import DRClassifier

# Global model cache for fast re-use without re-instantiation overhead
_MODEL_CACHE: Dict[str, Any] = {
    "model": None,
    "temperature": 1.0,
    "arch": "resnet18",
    "img_size": 224,
    "version": "RetinaAI-DR-v0.1",
}


def load_inference_model(
    checkpoint_path: Optional[Path] = None,
    calib_path: Optional[Path] = None,
    device: Optional[torch.device] = None,
) -> Tuple[DRClassifier, float, str]:
    """
    Loads and caches the trained DR classification model and temperature scaling factor.
    """
    global _MODEL_CACHE

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if checkpoint_path is None:
        # Check standard locations
        dr_ckpt = MODELS_DIR / "dr_classifier" / "best_model.pth"
        global_ckpt = CHECKPOINTS_DIR / "best_classifier.pth"
        if dr_ckpt.is_file():
            checkpoint_path = dr_ckpt
        elif global_ckpt.is_file():
            checkpoint_path = global_ckpt
        else:
            checkpoint_path = None

    if calib_path is None:
        calib_file = MODELS_DIR / "dr_classifier" / "calibration_config.json"
        if calib_file.is_file():
            calib_path = calib_file

    # Load temperature
    temp_factor = 1.0
    if calib_path and Path(calib_path).is_file():
        try:
            with open(calib_path, "r", encoding="utf-8") as f:
                calib_data = json.load(f)
                temp_factor = float(calib_data.get("temperature_scaling_factor", 1.0))
        except Exception:
            temp_factor = 1.0

    # Instantiate model
    arch = "resnet18"
    img_size = 224
    if checkpoint_path and Path(checkpoint_path).is_file():
        ckpt = torch.load(checkpoint_path, map_location=device)
        arch = ckpt.get("arch", "resnet18")
        img_size = ckpt.get("img_size", 224)
        model = DRClassifier(backbone_name=arch, num_classes=5, pretrained=False)
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        model = DRClassifier(backbone_name=arch, num_classes=5, pretrained=False)

    model.to(device)
    model.eval()

    _MODEL_CACHE["model"] = model
    _MODEL_CACHE["temperature"] = temp_factor
    _MODEL_CACHE["arch"] = arch
    _MODEL_CACHE["img_size"] = img_size

    return model, temp_factor, _MODEL_CACHE["version"]


def predict_retinopathy(
    image_input: Union[str, Path, np.ndarray],
    checkpoint_path: Optional[Path] = None,
    calib_path: Optional[Path] = None,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """
    Executes end-to-end inference on a retinal fundus image.

    Args:
        image_input: File path to image or RGB/BGR numpy array
        checkpoint_path: Optional path to custom .pth weights
        calib_path: Optional path to calibration_config.json
        device: Torch device (cpu or cuda)

    Returns:
        Structured dictionary conforming to Retina AI API contract.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 1. Get or initialize model
    if _MODEL_CACHE["model"] is None or checkpoint_path is not None:
        model, temp_factor, version = load_inference_model(checkpoint_path, calib_path, device)
    else:
        model = _MODEL_CACHE["model"]
        temp_factor = _MODEL_CACHE["temperature"]
        version = _MODEL_CACHE["version"]

    img_size = _MODEL_CACHE["img_size"]

    # 2. Clinical Preprocessing (identical to training)
    processed_rgb = load_and_preprocess_image(
        image_input,
        target_size=(img_size, img_size),
        apply_clahe=True,
        clip_limit=2.0,
    )

    # 4. Normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    norm_img = processed_rgb.astype(np.float32) / 255.0
    norm_img = (norm_img - mean) / std

    tensor_in = torch.from_numpy(norm_img).permute(2, 0, 1).unsqueeze(0).float().to(device)

    # 5. Forward Pass & Temperature Calibration
    with torch.no_grad():
        logits = model(tensor_in)
        calibrated_logits = logits / temp_factor
        calibrated_probs = torch.softmax(calibrated_logits, dim=1).cpu().numpy()[0]

    predicted_class_idx = int(np.argmax(calibrated_probs))
    predicted_grade = DRGrade(predicted_class_idx)
    is_referable = bool(predicted_class_idx >= 2)
    confidence = float(calibrated_probs[predicted_class_idx])

    class_probs_dict = {
        str(i): float(calibrated_probs[i]) for i in range(5)
    }

    return {
        "prediction": predicted_class_idx,
        "dr_grade": predicted_class_idx,
        "severity": DR_GRADE_NAMES[predicted_grade],
        "is_referable": is_referable,
        "confidence": round(confidence, 4),
        "class_probabilities": class_probs_dict,
        "model_version": version,
        "temperature_scaling_factor": round(temp_factor, 4),
        "disclaimer": "AI screening result only. Requires clinical confirmation by an ophthalmologist.",
    }
