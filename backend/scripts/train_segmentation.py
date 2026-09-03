"""
Retina AI: Lesion Segmentation Training Script
Trains a U-Net model on the IDRiD segmentation dataset.

Usage:
    python scripts/train_segmentation.py [--epochs 100] [--batch-size 4] [--lr 1e-4]
"""

import sys
import os
import argparse
import json
import time
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import IDRID_DATASET_DIR, MODELS_DIR
from src.models.unet import LesionUNet
from src.ai.segmentation.dataset import (
    build_idrid_segmentation_manifest,
    IDRiDSegmentationDataset,
)


class DiceBCELoss(nn.Module):
    """Combined Binary Cross-Entropy + Dice Loss for segmentation."""

    def __init__(self, bce_weight: float = 0.5, smooth: float = 1.0):
        super().__init__()
        self.bce_weight = bce_weight
        self.smooth = smooth
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # BCE component
        bce_loss = self.bce(logits, targets)

        # Dice component
        probs = torch.sigmoid(logits)
        intersection = (probs * targets).sum(dim=(2, 3))
        union = probs.sum(dim=(2, 3)) + targets.sum(dim=(2, 3))
        dice = (2.0 * intersection + self.smooth) / (union + self.smooth)
        dice_loss = 1.0 - dice.mean()

        return self.bce_weight * bce_loss + (1.0 - self.bce_weight) * dice_loss


def compute_dice_per_class(
    predictions: torch.Tensor,
    targets: torch.Tensor,
    threshold: float = 0.5,
    smooth: float = 1e-6,
) -> np.ndarray:
    """Computes per-class Dice coefficient."""
    probs = torch.sigmoid(predictions)
    preds = (probs >= threshold).float()

    dice_scores = []
    for c in range(predictions.shape[1]):
        p = preds[:, c].contiguous().view(-1)
        t = targets[:, c].contiguous().view(-1)
        intersection = (p * t).sum()
        dice = (2.0 * intersection + smooth) / (p.sum() + t.sum() + smooth)
        dice_scores.append(dice.item())

    return np.array(dice_scores)


def train_one_epoch(
    model: LesionUNet,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> float:
    """Trains for one epoch, returns mean loss."""
    model.train()
    total_loss = 0.0

    for batch_idx, (images, masks, _) in enumerate(loader):
        images = images.to(device)
        masks = masks.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, masks)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / max(len(loader), 1)


def validate(
    model: LesionUNet,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple:
    """Validates model, returns (mean_loss, per_class_dice)."""
    model.eval()
    total_loss = 0.0
    all_dice = []

    with torch.no_grad():
        for images, masks, _ in loader:
            images = images.to(device)
            masks = masks.to(device)

            logits = model(images)
            loss = criterion(logits, masks)
            total_loss += loss.item()

            dice = compute_dice_per_class(logits, masks)
            all_dice.append(dice)

    mean_loss = total_loss / max(len(loader), 1)
    mean_dice = np.mean(all_dice, axis=0) if all_dice else np.zeros(4)

    return mean_loss, mean_dice


def main():
    parser = argparse.ArgumentParser(description="Train Lesion Segmentation U-Net")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--val-split", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--patience", type=int, default=20,
                        help="Early stopping patience")
    parser.add_argument("--img-size", type=int, default=512)
    parser.add_argument("--encoder", type=str, default="resnet18", help="timm backbone encoder")
    args = parser.parse_args()

    # Reproducibility
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"IDRiD Root: {IDRID_DATASET_DIR}")

    # Build manifest
    manifest = build_idrid_segmentation_manifest(IDRID_DATASET_DIR, split="train")
    print(f"Training images found: {len(manifest)}")

    # Print annotation coverage
    lesion_names = ["microaneurysms", "haemorrhages", "hard_exudates", "soft_exudates"]
    for name in lesion_names:
        count = sum(1 for m in manifest if m.get(name) is not None)
        print(f"  {name}: {count}/{len(manifest)} annotated")

    # Train/Val split
    n_total = len(manifest)
    n_val = max(1, int(n_total * args.val_split))
    n_train = n_total - n_val

    indices = list(range(n_total))
    random.shuffle(indices)
    train_indices = indices[:n_train]
    val_indices = indices[n_train:]

    print(f"Split: {n_train} train, {n_val} val")

    # Create datasets
    target_size = (args.img_size, args.img_size)
    full_dataset = IDRiDSegmentationDataset(
        manifest=manifest,
        target_size=target_size,
        is_train=True,
        augment=True,
    )
    val_dataset = IDRiDSegmentationDataset(
        manifest=manifest,
        target_size=target_size,
        is_train=False,
        augment=False,
    )

    train_loader = DataLoader(
        Subset(full_dataset, train_indices),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        Subset(val_dataset, val_indices),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    # Model
    model = LesionUNet(encoder_name=args.encoder, num_classes=4, pretrained=True)
    model.to(device)

    # Loss, optimizer, scheduler
    criterion = DiceBCELoss(bce_weight=0.5)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)

    # Output directory
    save_dir = MODELS_DIR / "segmentation"
    save_dir.mkdir(parents=True, exist_ok=True)

    best_val_dice = 0.0
    patience_counter = 0
    history = []

    print(f"\n{'='*60}")
    print(f"Training U-Net Lesion Segmentation")
    print(f"{'='*60}")
    print(f"Architecture: ResNet-34 Encoder U-Net")
    print(f"Input Size: {target_size}")
    print(f"Classes: {lesion_names}")
    print(f"Epochs: {args.epochs}, Patience: {args.patience}")
    print(f"Batch Size: {args.batch_size}, LR: {args.lr}")
    print(f"{'='*60}\n")

    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        epoch_t0 = time.time()

        # Train
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)

        # Validate
        val_loss, val_dice = validate(model, val_loader, criterion, device)

        scheduler.step()

        mean_val_dice = float(np.mean(val_dice))
        epoch_time = time.time() - epoch_t0

        # Log
        dice_str = " | ".join(
            f"{lesion_names[i][:4].upper()}: {val_dice[i]:.4f}"
            for i in range(len(lesion_names))
        )
        print(
            f"Epoch {epoch:3d}/{args.epochs} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Mean Dice: {mean_val_dice:.4f} | "
            f"{dice_str} | "
            f"{epoch_time:.1f}s"
        )

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_loss": round(val_loss, 6),
            "val_dice_mean": round(mean_val_dice, 6),
            "val_dice_per_class": {
                lesion_names[i]: round(float(val_dice[i]), 6)
                for i in range(len(lesion_names))
            },
        })

        # Checkpoint best model
        if mean_val_dice > best_val_dice:
            best_val_dice = mean_val_dice
            patience_counter = 0

            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "encoder_name": args.encoder,
                "num_classes": 4,
                "img_size": args.img_size,
                "val_dice_mean": best_val_dice,
                "val_dice_per_class": {
                    lesion_names[i]: float(val_dice[i])
                    for i in range(len(lesion_names))
                },
                "val_loss": val_loss,
            }, save_dir / "lesion_unet_best.pth")

            print(f"  [SAVED] Best model saved (Mean Dice: {best_val_dice:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"\nEarly stopping at epoch {epoch} (patience {args.patience})")
                break

    total_time = time.time() - start_time

    # Save training history
    summary = {
        "architecture": "U-Net (ResNet-34 encoder)",
        "input_size": args.img_size,
        "num_classes": 4,
        "lesion_classes": lesion_names,
        "best_epoch": history[-1]["epoch"] if history else 0,
        "best_val_dice": round(best_val_dice, 6),
        "total_training_time_seconds": round(total_time, 1),
        "device": str(device),
        "training_config": {
            "epochs_run": len(history),
            "max_epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.lr,
            "patience": args.patience,
            "val_split": args.val_split,
            "seed": args.seed,
        },
        "history": history,
    }

    with open(save_dir / "training_history.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Training Complete")
    print(f"{'='*60}")
    print(f"Best Val Dice: {best_val_dice:.4f}")
    print(f"Total Time: {total_time/60:.1f} min")
    print(f"Model saved: {save_dir / 'lesion_unet_best.pth'}")
    print(f"History saved: {save_dir / 'training_history.json'}")


if __name__ == "__main__":
    main()
