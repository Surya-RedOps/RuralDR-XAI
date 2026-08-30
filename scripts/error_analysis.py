"""
Retina AI: Error Analysis Script
Analyzes disagreements between classification and lesion evidence,
Grad-CAM quality issues, and segmentation failures.

Usage:
    python scripts/error_analysis.py
"""

import sys
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import IDRID_DATASET_DIR, MODELS_DIR, RESULTS_DIR
from src.models.classifier import DRClassifier
from src.models.unet import LesionUNet
from src.xai.gradcam import GradCAM
from src.ai.classification.inference import load_inference_model
from src.ai.segmentation.dataset import build_idrid_segmentation_manifest
from PIL import Image


LESION_NAMES = ["microaneurysms", "haemorrhages", "hard_exudates", "soft_exudates"]


def analyze_gradcam_quality(model, images_dir: Path, n_samples: int = 10):
    """Analyzes Grad-CAM quality across sample images."""
    gradcam = GradCAM(model, use_plus_plus=True)
    issues = []

    image_files = sorted(images_dir.glob("*.jpg"))[:n_samples]
    if not image_files:
        return {"status": "no_images_found", "issues": []}

    for img_path in image_files:
        with Image.open(img_path) as pil_img:
            img = np.array(pil_img.convert("RGB"))

        # Preprocess for classifier
        img_resized = cv2.resize(img, (224, 224))
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm = (img_resized.astype(np.float32) / 255.0 - mean) / std
        tensor = torch.from_numpy(norm).permute(2, 0, 1).unsqueeze(0).float()

        cam, mask, result = gradcam.generate_with_validation(tensor)

        entry = {
            "image": img_path.name,
            "target_class": result.target_class,
            "is_valid": result.is_valid,
            "peak_intensity": result.peak_intensity,
            "activation_coverage": result.activation_coverage,
            "quality_flags": result.quality_flags,
        }

        if not result.is_valid:
            issues.append(entry)

    return {
        "images_analyzed": len(image_files),
        "invalid_heatmaps": len(issues),
        "issues": issues,
    }


def analyze_classification_vs_lesions(
    seg_model: LesionUNet,
    dr_model: DRClassifier,
    manifest: list,
    device: torch.device,
):
    """Analyzes disagreements between DR classification and lesion evidence."""
    discordances = []
    seg_model.eval()
    dr_model.eval()

    for entry in manifest[:20]:  # Sample first 20
        img_path = entry["image_path"]
        with Image.open(img_path) as pil_img:
            img = np.array(pil_img.convert("RGB"))

        # DR classification
        img_224 = cv2.resize(img, (224, 224))
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm_224 = (img_224.astype(np.float32) / 255.0 - mean) / std
        tensor_224 = torch.from_numpy(norm_224).permute(2, 0, 1).unsqueeze(0).float().to(device)

        with torch.no_grad():
            logits = dr_model(tensor_224)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            dr_grade = int(np.argmax(probs))
            confidence = float(probs[dr_grade])

        # Segmentation
        img_512 = cv2.resize(img, (512, 512))
        norm_512 = (img_512.astype(np.float32) / 255.0 - mean) / std
        tensor_512 = torch.from_numpy(norm_512).permute(2, 0, 1).unsqueeze(0).float().to(device)

        with torch.no_grad():
            seg_logits = seg_model(tensor_512)
            seg_probs = torch.sigmoid(seg_logits).cpu().numpy()[0]
            seg_masks = (seg_probs >= 0.5).astype(np.uint8)

        lesion_detected = {
            LESION_NAMES[i]: bool(np.sum(seg_masks[i]) > 0)
            for i in range(4)
        }
        any_lesion = any(lesion_detected.values())

        # Check for discordance
        discordance_reasons = []
        if dr_grade == 0 and any_lesion:
            discordance_reasons.append(
                "DR Grade 0 but lesion segmentation detected features"
            )
        if dr_grade >= 2 and not any_lesion:
            discordance_reasons.append(
                f"DR Grade {dr_grade} but no lesions detected by segmentation"
            )

        if discordance_reasons:
            discordances.append({
                "image_id": entry["image_id"],
                "dr_grade": dr_grade,
                "confidence": round(confidence, 4),
                "lesions_detected": lesion_detected,
                "discordance_reasons": discordance_reasons,
                "note": (
                    "Disagreement between classification and segmentation is not automatically "
                    "a system error. The models may have different sensitivities."
                ),
            })

    return {
        "images_analyzed": min(20, len(manifest)),
        "discordances_found": len(discordances),
        "cases": discordances,
    }


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    out_dir = RESULTS_DIR / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "device": str(device),
    }

    # 1. Load DR model
    print("\n1. Loading DR classifier...")
    try:
        dr_model, temp, _ = load_inference_model(device=device)
        print(f"   DR model loaded (temp={temp})")
    except Exception as e:
        print(f"   ERROR: {e}")
        dr_model = None

    # 2. Grad-CAM quality analysis
    print("\n2. Analyzing Grad-CAM quality...")
    if dr_model:
        # Use IDRiD test images
        test_img_dir = (
            IDRID_DATASET_DIR / "A. Segmentation" / "A. Segmentation"
            / "1. Original Images" / "b. Testing Set"
        )
        gradcam_analysis = analyze_gradcam_quality(dr_model, test_img_dir, n_samples=10)
        report["gradcam_quality"] = gradcam_analysis
        print(f"   Analyzed {gradcam_analysis['images_analyzed']} images")
        print(f"   Invalid heatmaps: {gradcam_analysis['invalid_heatmaps']}")
    else:
        report["gradcam_quality"] = {"status": "dr_model_not_available"}

    # 3. Classification vs segmentation discordance
    print("\n3. Analyzing classification-segmentation agreement...")
    seg_model_path = MODELS_DIR / "segmentation" / "lesion_unet_best.pth"
    if dr_model and seg_model_path.is_file():
        seg_model = LesionUNet(encoder_name="resnet34", num_classes=4, pretrained=False)
        ckpt = torch.load(seg_model_path, map_location=device)
        seg_model.load_state_dict(ckpt["model_state_dict"])
        seg_model.to(device)
        seg_model.eval()

        manifest = build_idrid_segmentation_manifest(IDRID_DATASET_DIR, split="test")
        discordance = analyze_classification_vs_lesions(seg_model, dr_model, manifest, device)
        report["classification_vs_segmentation"] = discordance
        print(f"   Analyzed {discordance['images_analyzed']} images")
        print(f"   Discordances: {discordance['discordances_found']}")
    else:
        report["classification_vs_segmentation"] = {"status": "models_not_available"}
        print("   Segmentation model not yet trained — skipping")

    # 4. Known limitations
    report["known_limitations"] = [
        "Grad-CAM is an explanation of model attention, NOT clinical proof of pathology",
        "Lesion segmentation trained on only 54 IDRiD images — may have limited generalization",
        "Soft exudate masks are sparse (26/54 training, 14/27 test) — lower reliability expected",
        "Microaneurysm segmentation is challenging due to tiny lesion size (2-30 pixels at native resolution)",
        "DR classifier and segmentation model were trained on different datasets and resolutions",
        "Discordance between classification and segmentation may reflect genuine differences in model sensitivity",
        "No clinical validation has been performed on this system",
    ]

    # 5. Recommendations
    report["recommendations"] = [
        "Collect larger pixel-annotated dataset for improved segmentation generalization",
        "Evaluate Grad-CAM with ophthalmologist review to assess clinical relevance",
        "Consider training DR classifier and segmentation on the same dataset for better coherence",
        "Perform prospective clinical validation before any deployment",
    ]

    # Save report
    report_path = out_dir / "error_analysis.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nError analysis report saved: {report_path}")


if __name__ == "__main__":
    main()
