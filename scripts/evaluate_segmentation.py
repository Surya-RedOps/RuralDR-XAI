"""
Retina AI: Lesion Segmentation Evaluation Script
Evaluates the trained U-Net on the IDRiD test set with per-lesion metrics.

Usage:
    python scripts/evaluate_segmentation.py
"""

import sys
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import IDRID_DATASET_DIR, MODELS_DIR, RESULTS_DIR
from src.models.unet import LesionUNet
from src.ai.segmentation.dataset import (
    build_idrid_segmentation_manifest,
    IDRiDSegmentationDataset,
)

LESION_NAMES = ["microaneurysms", "haemorrhages", "hard_exudates", "soft_exudates"]


def compute_metrics(pred: np.ndarray, gt: np.ndarray, smooth: float = 1e-6):
    """Computes Dice, IoU, Precision, Recall for a single binary mask pair."""
    pred_flat = pred.flatten().astype(np.float32)
    gt_flat = gt.flatten().astype(np.float32)

    tp = np.sum(pred_flat * gt_flat)
    fp = np.sum(pred_flat * (1 - gt_flat))
    fn = np.sum((1 - pred_flat) * gt_flat)

    dice = (2.0 * tp + smooth) / (2.0 * tp + fp + fn + smooth)
    iou = (tp + smooth) / (tp + fp + fn + smooth)
    precision = (tp + smooth) / (tp + fp + smooth)
    recall = (tp + smooth) / (tp + fn + smooth)

    return {
        "dice": round(float(dice), 6),
        "iou": round(float(iou), 6),
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "gt_positive_pixels": int(np.sum(gt_flat)),
        "pred_positive_pixels": int(np.sum(pred_flat)),
    }


def save_visualization(
    image_rgb: np.ndarray,
    gt_mask: np.ndarray,
    pred_mask: np.ndarray,
    save_path: str,
    lesion_name: str,
):
    """Saves a 4-panel visualization: original, GT, prediction, overlay."""
    h, w = image_rgb.shape[:2]

    # Resize masks to image size if needed
    if gt_mask.shape[:2] != (h, w):
        gt_mask = cv2.resize(gt_mask, (w, h), interpolation=cv2.INTER_NEAREST)
    if pred_mask.shape[:2] != (h, w):
        pred_mask = cv2.resize(pred_mask, (w, h), interpolation=cv2.INTER_NEAREST)

    # Create panels
    gt_colored = np.zeros_like(image_rgb)
    gt_colored[gt_mask > 0] = [0, 255, 0]  # Green for GT

    pred_colored = np.zeros_like(image_rgb)
    pred_colored[pred_mask > 0] = [255, 0, 0]  # Red for prediction

    overlay = image_rgb.copy()
    overlay[gt_mask > 0] = cv2.addWeighted(overlay[gt_mask > 0], 0.6,
                                            gt_colored[gt_mask > 0], 0.4, 0)
    overlay[pred_mask > 0] = cv2.addWeighted(overlay[pred_mask > 0], 0.6,
                                              pred_colored[pred_mask > 0], 0.4, 0)

    # Stack panels
    top_row = np.concatenate([image_rgb, overlay], axis=1)
    bottom_row = np.concatenate([
        cv2.cvtColor(gt_mask * 255, cv2.COLOR_GRAY2RGB),
        cv2.cvtColor(pred_mask * 255, cv2.COLOR_GRAY2RGB),
    ], axis=1)

    # Resize bottom to match top width
    bottom_row = cv2.resize(bottom_row, (top_row.shape[1], h))

    panel = np.concatenate([top_row, bottom_row], axis=0)

    cv2.imwrite(save_path, cv2.cvtColor(panel, cv2.COLOR_RGB2BGR))


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Load model
    model_path = MODELS_DIR / "segmentation" / "lesion_unet_best.pth"
    if not model_path.is_file():
        print(f"ERROR: Model not found at {model_path}")
        print("Run scripts/train_segmentation.py first.")
        sys.exit(1)

    ckpt = torch.load(model_path, map_location=device)
    img_size = ckpt.get("img_size", 512)

    encoder_name = ckpt.get("encoder_name", "resnet18")
    model = LesionUNet(encoder_name=encoder_name, num_classes=4, pretrained=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()

    print(f"Loaded model from epoch {ckpt.get('epoch', '?')}")
    print(f"Val Dice (at training): {ckpt.get('val_dice_mean', '?')}")

    # Build test manifest
    test_manifest = build_idrid_segmentation_manifest(IDRID_DATASET_DIR, split="test")
    print(f"Test images: {len(test_manifest)}")

    test_dataset = IDRiDSegmentationDataset(
        manifest=test_manifest,
        target_size=(img_size, img_size),
        is_train=False,
        augment=False,
    )
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)

    # Output directory
    out_dir = RESULTS_DIR / "segmentation"
    out_dir.mkdir(parents=True, exist_ok=True)
    viz_dir = out_dir / "visualizations"
    viz_dir.mkdir(parents=True, exist_ok=True)

    # Evaluate
    all_metrics = {name: [] for name in LESION_NAMES}
    total_time = 0.0
    example_count = 0

    print(f"\n{'='*70}")
    print(f"Evaluating on IDRiD Test Set ({len(test_manifest)} images)")
    print(f"{'='*70}\n")

    for batch_idx, (images, masks, image_ids) in enumerate(test_loader):
        images = images.to(device)
        gt_masks = masks.numpy()[0]  # (4, H, W)

        t0 = time.time()
        with torch.no_grad():
            logits = model(images)
            probs = torch.sigmoid(logits).cpu().numpy()[0]
            pred_masks = (probs >= 0.5).astype(np.uint8)
        inference_time = (time.time() - t0) * 1000.0
        total_time += inference_time

        image_id = image_ids[0]

        for c, name in enumerate(LESION_NAMES):
            gt = (gt_masks[c] > 0).astype(np.uint8)
            pred = pred_masks[c]
            metrics = compute_metrics(pred, gt)
            metrics["image_id"] = image_id
            all_metrics[name].append(metrics)

            # Save visualization for first 5 images
            if example_count < 5 and metrics["gt_positive_pixels"] > 0:
                # Denormalize image for visualization
                mean = np.array([0.485, 0.456, 0.406])
                std = np.array([0.229, 0.224, 0.225])
                img_np = images[0].cpu().numpy().transpose(1, 2, 0)
                img_np = ((img_np * std + mean) * 255).clip(0, 255).astype(np.uint8)

                save_visualization(
                    img_np, gt, pred,
                    str(viz_dir / f"{image_id}_{name}.jpg"),
                    name,
                )

        example_count += 1

    # Aggregate metrics
    print(f"\n{'='*70}")
    print(f"Per-Lesion Metrics (IDRiD Test Set)")
    print(f"{'='*70}")

    summary = {}
    for name in LESION_NAMES:
        metrics_list = all_metrics[name]

        # Only consider images that have actual GT annotations (non-zero GT pixels)
        annotated = [m for m in metrics_list if m["gt_positive_pixels"] > 0]
        total_images = len(metrics_list)
        annotated_count = len(annotated)

        if annotated:
            mean_dice = np.mean([m["dice"] for m in annotated])
            mean_iou = np.mean([m["iou"] for m in annotated])
            mean_prec = np.mean([m["precision"] for m in annotated])
            mean_recall = np.mean([m["recall"] for m in annotated])
        else:
            mean_dice = mean_iou = mean_prec = mean_recall = 0.0

        summary[name] = {
            "total_test_images": total_images,
            "annotated_images": annotated_count,
            "mean_dice": round(float(mean_dice), 4),
            "mean_iou": round(float(mean_iou), 4),
            "mean_precision": round(float(mean_prec), 4),
            "mean_recall": round(float(mean_recall), 4),
            "per_image": metrics_list,
        }

        print(f"\n  {name.upper()} ({annotated_count}/{total_images} annotated)")
        print(f"    Dice:      {mean_dice:.4f}")
        print(f"    IoU:       {mean_iou:.4f}")
        print(f"    Precision: {mean_prec:.4f}")
        print(f"    Recall:    {mean_recall:.4f}")

        if name == "soft_exudates" and annotated_count < total_images:
            print(f"    ⚠ Sparse annotations: only {annotated_count}/{total_images} "
                  f"images have soft exudate GT masks")

    avg_inference = total_time / max(len(test_manifest), 1)
    print(f"\n  Average inference time: {avg_inference:.1f} ms/image")

    # Save results
    eval_result = {
        "model_path": str(model_path),
        "test_images": len(test_manifest),
        "input_size": img_size,
        "device": str(device),
        "average_inference_ms": round(avg_inference, 2),
        "per_lesion_metrics": {
            k: {kk: vv for kk, vv in v.items() if kk != "per_image"}
            for k, v in summary.items()
        },
        "per_image_results": {
            k: v["per_image"] for k, v in summary.items()
        },
    }

    with open(out_dir / "evaluation_results.json", "w") as f:
        json.dump(eval_result, f, indent=2)

    print(f"\nResults saved: {out_dir / 'evaluation_results.json'}")
    print(f"Visualizations: {viz_dir}")


if __name__ == "__main__":
    main()
