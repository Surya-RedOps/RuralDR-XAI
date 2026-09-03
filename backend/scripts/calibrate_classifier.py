"""
Retina AI: Temperature Scaling Calibration Script
Optimizes temperature parameter T on the validation set to minimize Expected Calibration Error (ECE).
"""

import sys
import json
import argparse
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import MANIFESTS_DIR, MODELS_DIR
from src.ai.classification.dataset import RetinalFundusDataset
from src.models.classifier import DRClassifier
from src.models.calibrate import TemperatureScaler, compute_ece


def extract_validation_logits_and_labels(model, loader, device):
    model.eval()
    all_logits = []
    all_labels = []

    with torch.no_grad():
        for images, labels, _ in loader:
            images = images.to(device)
            logits = model(images)
            all_logits.append(logits.cpu())
            all_labels.append(labels)

    logits_tensor = torch.cat(all_logits, dim=0)
    labels_tensor = torch.cat(all_labels, dim=0)
    return logits_tensor, labels_tensor


def calibrate_temperature(logits: torch.Tensor, labels: torch.Tensor, max_iters: int = 100):
    """Finds optimal temperature T minimizing NLL on validation logits."""
    temperature = nn.Parameter(torch.ones(1) * 1.5)
    nll_criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.LBFGS([temperature], lr=0.01, max_iter=max_iters)

    def eval_fn():
        optimizer.zero_grad()
        loss = nll_criterion(logits / temperature, labels)
        loss.backward()
        return loss

    optimizer.step(eval_fn)
    return float(temperature.item())


def main():
    parser = argparse.ArgumentParser(description="Calibrate classification confidence via Temperature Scaling.")
    parser.add_argument("--checkpoint", type=str, default=str(MODELS_DIR / "dr_classifier" / "best_model.pth"))
    parser.add_argument("--val_manifest", type=str, default=str(MANIFESTS_DIR / "val_split.csv"))
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    device = torch.device(args.device)
    ckpt_path = Path(args.checkpoint)
    val_manifest = Path(args.val_manifest)

    if not ckpt_path.is_file():
        raise FileNotFoundError(f"Trained checkpoint not found at: {ckpt_path}")
    if not val_manifest.is_file():
        raise FileNotFoundError(f"Validation manifest not found at: {val_manifest}")

    print("=" * 70)
    print("  RETINA AI: CONFIDENCE CALIBRATION (TEMPERATURE SCALING)")
    print("=" * 70)
    print(f"Checkpoint : {ckpt_path.name}")
    print(f"Val Set    : {val_manifest.name}")
    print(f"Device     : {device}\n")

    # Load model
    ckpt = torch.load(ckpt_path, map_location=device)
    arch = ckpt.get("arch", "resnet18")
    img_size = ckpt.get("img_size", 224)

    model = DRClassifier(backbone_name=arch, num_classes=5, pretrained=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)

    # Load validation data
    val_dataset = RetinalFundusDataset(val_manifest, target_size=(img_size, img_size), is_train=False)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

    print(f"[*] Extracting logits from {len(val_dataset)} validation samples...")
    logits, labels = extract_validation_logits_and_labels(model, val_loader, device)

    # Uncalibrated probabilities & ECE
    uncalibrated_probs = torch.softmax(logits, dim=1).numpy()
    labels_np = labels.numpy()
    ece_before, stats_before = compute_ece(uncalibrated_probs, labels_np, num_bins=10)

    # Optimize Temperature
    print("[*] Optimizing temperature scaling parameter T...")
    optimal_t = calibrate_temperature(logits, labels)
    print(f"• Learned Temperature Factor T = {optimal_t:.4f}")

    # Calibrated probabilities & ECE
    calibrated_logits = logits / optimal_t
    calibrated_probs = torch.softmax(calibrated_logits, dim=1).numpy()
    ece_after, stats_after = compute_ece(calibrated_probs, labels_np, num_bins=10)

    print("\n--- Calibration Results ---")
    print(f"• Uncalibrated Expected Calibration Error (ECE): {ece_before * 100:.2f}%")
    print(f"• Calibrated Expected Calibration Error (ECE)  : {ece_after * 100:.2f}%")
    ece_reduction = (ece_before - ece_after) / ece_before * 100 if ece_before > 0 else 0
    print(f"• ECE Error Reduction                          : {ece_reduction:.1f}%")

    calib_config = {
        "temperature_scaling_factor": optimal_t,
        "uncalibrated_ece": float(ece_before),
        "calibrated_ece": float(ece_after),
        "ece_reduction_pct": float(ece_reduction),
        "num_bins": 10,
        "validation_samples": len(val_dataset),
        "calibration_method": "Post-Hoc Temperature Scaling (Guo et al. 2017)",
    }

    calib_file = MODELS_DIR / "dr_classifier" / "calibration_config.json"
    with open(calib_file, "w", encoding="utf-8") as f:
        json.dump(calib_config, f, indent=2)

    print(f"\nSaved calibration config to: {calib_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
