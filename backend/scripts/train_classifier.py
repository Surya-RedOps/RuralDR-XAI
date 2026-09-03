"""
Retina AI: DR Severity Classifier Training Script
Trains transfer learning backbones with class-weighted cross entropy, cosine annealing, and QWK checkpointing.
"""

import sys
import json
import time
import argparse
import shutil
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import cohen_kappa_score, accuracy_score, f1_score

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import MANIFESTS_DIR, MODELS_DIR, CHECKPOINTS_DIR
from src.ai.classification.dataset import RetinalFundusDataset
from src.models.classifier import DRClassifier


def set_seed(seed: int = 42):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def compute_class_weights(dataset: RetinalFundusDataset) -> torch.Tensor:
    """Computes balanced inverse-frequency class weights: w_c = N / (K * N_c)"""
    counts = dataset.df["diagnosis"].value_counts().sort_index().values
    total_samples = len(dataset)
    num_classes = len(counts)
    weights = total_samples / (num_classes * counts.astype(np.float32))
    # Normalize weights so mean is 1.0
    weights = weights / np.mean(weights)
    return torch.tensor(weights, dtype=torch.float32)


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    all_preds = []
    all_labels = []

    for images, labels, _ in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        preds = torch.argmax(logits, dim=1).detach().cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.detach().cpu().numpy())

    epoch_loss = running_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    return epoch_loss, epoch_acc


def evaluate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels, _ in loader:
            images = images.to(device)
            labels = labels.to(device)

            logits = model(images)
            loss = criterion(logits, labels)

            running_loss += loss.item() * images.size(0)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)

            all_probs.extend(probs)
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    val_loss = running_loss / len(loader.dataset)
    val_acc = accuracy_score(all_labels, all_preds)
    val_qwk = cohen_kappa_score(all_labels, all_preds, weights="quadratic")
    val_f1_macro = f1_score(all_labels, all_preds, average="macro")

    return val_loss, val_acc, val_qwk, val_f1_macro, np.array(all_probs), np.array(all_labels)


def main():
    parser = argparse.ArgumentParser(description="Train Retina AI Diabetic Retinopathy Classifier.")
    parser.add_argument("--arch", type=str, default="resnet18", help="Model backbone (resnet18, resnet34, efficientnet_b0)")
    parser.add_argument("--epochs", type=int, default=6, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--img_size", type=int, default=224, help="Image resolution")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device(args.device)

    print("=" * 70)
    print("  RETINA AI: DIABETIC RETINOPATHY MODEL TRAINING PIPELINE")
    print("=" * 70)
    print(f"• Architecture : {args.arch}")
    print(f"• Device       : {device}")
    print(f"• Epochs       : {args.epochs}")
    print(f"• Batch Size   : {args.batch_size}")
    print(f"• Learning Rate: {args.lr}")
    print(f"• Input Size   : {args.img_size}x{args.img_size}")
    print(f"• Random Seed  : {args.seed}\n")

    train_manifest = MANIFESTS_DIR / "train_split.csv"
    val_manifest = MANIFESTS_DIR / "val_split.csv"

    if not train_manifest.is_file() or not val_manifest.is_file():
        raise FileNotFoundError("Split manifests not found. Run scripts/prepare_splits.py first.")

    # Datasets and Loaders
    train_dataset = RetinalFundusDataset(train_manifest, target_size=(args.img_size, args.img_size), is_train=True)
    val_dataset = RetinalFundusDataset(val_manifest, target_size=(args.img_size, args.img_size), is_train=False)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)

    print(f"• Training samples  : {len(train_dataset)} ({len(train_loader)} batches)")
    print(f"• Validation samples: {len(val_dataset)} ({len(val_loader)} batches)")

    # Class weights for imbalance
    class_weights = compute_class_weights(train_dataset).to(device)
    print(f"• Class weights     : {[round(w, 2) for w in class_weights.cpu().numpy().tolist()]}\n")

    # Initialize model
    print(f"[*] Initializing model with {args.arch} backbone...")
    model = DRClassifier(backbone_name=args.arch, num_classes=5, pretrained=True, dropout_rate=0.3)
    model.to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)

    # Destination directories
    dr_model_dir = MODELS_DIR / "dr_classifier"
    dr_model_dir.mkdir(parents=True, exist_ok=True)
    best_checkpoint_path = dr_model_dir / "best_model.pth"

    best_val_qwk = -1.0
    history = []

    print("-" * 70)
    print(f"{'Epoch':<8} {'Train Loss':<12} {'Train Acc':<12} {'Val Loss':<12} {'Val Acc':<12} {'Val QWK':<10} {'Time':<8}")
    print("-" * 70)

    start_training_time = time.time()

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_qwk, val_f1_macro, _, _ = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        epoch_stats = {
            "epoch": epoch,
            "train_loss": float(train_loss),
            "train_acc": float(train_acc),
            "val_loss": float(val_loss),
            "val_acc": float(val_acc),
            "val_qwk": float(val_qwk),
            "val_f1_macro": float(val_f1_macro),
            "lr": float(optimizer.param_groups[0]["lr"]),
            "epoch_time_sec": float(elapsed),
        }
        history.append(epoch_stats)

        is_best = val_qwk > best_val_qwk
        if is_best:
            best_val_qwk = val_qwk
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "arch": args.arch,
                    "val_qwk": val_qwk,
                    "val_acc": val_acc,
                    "val_loss": val_loss,
                    "img_size": args.img_size,
                },
                best_checkpoint_path,
            )
            # Copy to global checkpoints directory for application runtime
            CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy(best_checkpoint_path, CHECKPOINTS_DIR / "best_classifier.pth")

        best_flag = " [*BEST]" if is_best else ""
        print(f"{epoch:<8} {train_loss:<12.4f} {train_acc*100:<11.2f}% {val_loss:<12.4f} {val_acc*100:<11.2f}% {val_qwk:<10.4f} {elapsed:<6.1f}s{best_flag}")

    total_time = time.time() - start_training_time
    print("-" * 70)
    print(f"Training completed in {total_time/60:.2f} minutes.")
    print(f"Best Validation Quadratic Weighted Kappa (QWK): {best_val_qwk:.4f}")
    print(f"Saved best model weights to: {best_checkpoint_path}")

    # Save Preprocessing and Training Configuration
    prep_config = {
        "target_size": [args.img_size, args.img_size],
        "crop_retinal_roi": True,
        "apply_lab_clahe": True,
        "clahe_clip_limit": 2.0,
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
        "backbone": args.arch,
        "num_classes": 5,
        "class_mapping": {
            "0": "No Diabetic Retinopathy",
            "1": "Mild Non-Proliferative DR",
            "2": "Moderate Non-Proliferative DR",
            "3": "Severe Non-Proliferative DR",
            "4": "Proliferative Diabetic Retinopathy",
        },
    }
    with open(dr_model_dir / "preprocessing_config.json", "w", encoding="utf-8") as f:
        json.dump(prep_config, f, indent=2)

    with open(dr_model_dir / "training_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"Saved preprocessing config to: {dr_model_dir / 'preprocessing_config.json'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
