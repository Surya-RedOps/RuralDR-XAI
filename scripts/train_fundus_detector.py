"""
RuralDR-XAI: Training and Evaluation Script for Fundus Modality Detector
Trains a binary classifier (0: Non-Fundus, 1: Fundus) to prevent out-of-domain images
from reaching the Diabetic Retinopathy pipeline.
"""

import os
import sys
from pathlib import Path
import random
import json
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import MODELS_DIR
from src.quality.modality import FundusClassifierModel


def generate_synthetic_negative_image(category: str, size: tuple = (512, 512)) -> np.ndarray:
    """Generates a representative non-retinal image for a specific OOD category."""
    w, h = size
    img = np.zeros((h, w, 3), dtype=np.uint8)

    if category == "vehicle":
        # Automotive scene: sky, asphalt road, car body with metallic colors, wheels, headlights
        # Blue/gray sky
        for y in range(h // 2):
            img[y, :] = [200 - y // 4, 180 - y // 4, 120]  # BGR
        # Dark asphalt
        img[h // 2:, :] = [60, 60, 60]
        # Car body (red/blue/silver metallic box with curved roof)
        car_color = random.choice([[180, 50, 50], [50, 50, 200], [180, 180, 180], [30, 150, 30]])
        cv2.rectangle(img, (w // 6, h // 2 - 40), (5 * w // 6, h // 2 + 60), car_color, -1)
        cv2.rectangle(img, (w // 4, h // 2 - 100), (3 * w // 4, h // 2 - 40), car_color, -1)
        # Windows
        cv2.rectangle(img, (w // 4 + 10, h // 2 - 90), (3 * w // 4 - 10, h // 2 - 45), (220, 220, 220), -1)
        # Wheels
        cv2.circle(img, (w // 3, h // 2 + 60), 30, (20, 20, 20), -1)
        cv2.circle(img, (2 * w // 3, h // 2 + 60), 30, (20, 20, 20), -1)

    elif category == "document":
        # White sheet of paper with black printed text lines, paragraphs, and tables
        img[:] = [245 + random.randint(-5, 5), 245 + random.randint(-5, 5), 245 + random.randint(-5, 5)]
        # Add margin border
        cv2.rectangle(img, (30, 30), (w - 30, h - 30), (220, 220, 220), 1)
        # Header bar
        cv2.rectangle(img, (50, 50), (w - 50, 80), (180, 140, 100), -1)
        # Text lines
        for y in range(110, h - 60, 18):
            line_w = random.randint(w // 2, w - 100)
            cv2.line(img, (60, y), (60 + line_w, y), (40, 40, 40), 2)
            if random.random() > 0.7:
                y += 10  # paragraph break

    elif category == "screenshot":
        # Code editor / desktop UI: dark background, toolbar, sidebar, colored code syntax
        img[:] = [30, 25, 20]  # dark slate
        # Top title bar
        cv2.rectangle(img, (0, 0), (w, 35), (45, 40, 35), -1)
        # Window controls
        cv2.circle(img, (20, 18), 6, (60, 60, 220), -1)
        cv2.circle(img, (40, 18), 6, (60, 200, 220), -1)
        cv2.circle(img, (60, 18), 6, (80, 200, 80), -1)
        # Sidebar
        cv2.rectangle(img, (0, 35), (100, h), (40, 35, 30), -1)
        # Code lines with colorful tokens
        syntax_colors = [(180, 100, 240), (100, 200, 100), (220, 180, 100), (100, 180, 240)]
        for y in range(60, h - 40, 20):
            x = 120
            while x < w - 80:
                token_len = random.randint(20, 70)
                col = random.choice(syntax_colors)
                cv2.line(img, (x, y), (x + token_len, y), col, 3)
                x += token_len + random.randint(10, 25)

    elif category == "person":
        # Portrait / face silhouette: background, head oval, eyes, nose, shoulders
        bg_col = [random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)]
        img[:] = bg_col
        # Shoulders
        cv2.ellipse(img, (w // 2, h + 80), (w // 2, h // 2), 0, 0, 360, (120, 80, 50), -1)
        # Face / head
        skin_tones = [(160, 200, 230), (120, 160, 200), (80, 120, 160)]
        skin = random.choice(skin_tones)
        cv2.ellipse(img, (w // 2, h // 2 - 30), (w // 4, h // 3), 0, 0, 360, skin, -1)
        # Hair
        cv2.ellipse(img, (w // 2, h // 2 - 90), (w // 4 + 10, h // 4), 0, 180, 360, (20, 20, 30), -1)
        # Eyes
        cv2.circle(img, (w // 2 - 45, h // 2 - 40), 12, (240, 240, 240), -1)
        cv2.circle(img, (w // 2 + 45, h // 2 - 40), 12, (240, 240, 240), -1)
        cv2.circle(img, (w // 2 - 45, h // 2 - 40), 6, (50, 30, 20), -1)
        cv2.circle(img, (w // 2 + 45, h // 2 - 40), 6, (50, 30, 20), -1)

    elif category == "landscape":
        # Natural scenery: blue sky, mountain peaks, green foreground
        for y in range(h // 2):
            img[y, :] = [240 - y // 3, 190 - y // 3, 100]  # Blue sky
        # Mountains
        pts = np.array([[0, h // 2], [w // 4, h // 3 - 30], [w // 2, h // 2 - 20], [3 * w // 4, h // 3], [w, h // 2]], np.int32)
        cv2.fillPoly(img, [pts], (120, 100, 90))
        # Green ground
        cv2.rectangle(img, (0, h // 2), (w, h), (40, 140, 50), -1)

    elif category == "medical_xray":
        # Chest X-ray / CT simulation: grayscale, ribs, lung fields, spine
        gray_img = np.zeros((h, w), dtype=np.uint8)
        gray_img[:] = 20
        # Lung contours (darker regions)
        cv2.ellipse(gray_img, (w // 3, h // 2), (w // 5, h // 3), 0, 0, 360, 60, -1)
        cv2.ellipse(gray_img, (2 * w // 3, h // 2), (w // 5, h // 3), 0, 0, 360, 60, -1)
        # Spine / mediastinum (brighter)
        cv2.rectangle(gray_img, (w // 2 - 25, 40), (w // 2 + 25, h - 40), 160, -1)
        # Rib lines
        for y in range(h // 4, 3 * h // 4, 30):
            cv2.ellipse(gray_img, (w // 2, y), (w // 3, 20), 0, 0, 180, 140, 4)
        img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)

    else:
        # Wallpaper / abstract geometric patterns
        color1 = [random.randint(50, 220), random.randint(50, 220), random.randint(50, 220)]
        color2 = [random.randint(50, 220), random.randint(50, 220), random.randint(50, 220)]
        for y in range(h):
            alpha = y / float(h)
            img[y, :] = [int((1 - alpha) * color1[c] + alpha * color2[c]) for c in range(3)]
        for _ in range(10):
            pt1 = (random.randint(0, w), random.randint(0, h))
            pt2 = (random.randint(0, w), random.randint(0, h))
            cv2.line(img, pt1, pt2, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), random.randint(2, 6))

    # Convert BGR to RGB
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


class ModalityDataset(Dataset):
    def __init__(self, samples: list, img_size: int = 224):
        self.samples = samples  # list of (image_path_or_array, label)
        self.img_size = img_size
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item, label = self.samples[idx]
        if isinstance(item, (str, Path)):
            bgr = cv2.imread(str(item))
            if bgr is None:
                rgb = np.zeros((self.img_size, self.img_size, 3), dtype=np.uint8)
            else:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        else:
            rgb = item

        resized = cv2.resize(rgb, (self.img_size, self.img_size), interpolation=cv2.INTER_AREA)
        norm = (resized.astype(np.float32) / 255.0 - self.mean) / self.std
        tensor = torch.from_numpy(norm).permute(2, 0, 1).float()
        return tensor, torch.tensor(label, dtype=torch.long)


def build_and_split_dataset(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)

    # 1. Positive Retinal Samples from APTOS and IDRiD and Sample
    positive_paths = []
    aptos_dir = Path("e:/SIH/Data_set/aptos2019-blindness-detection/train_images")
    if aptos_dir.is_dir():
        all_aptos = list(aptos_dir.glob("*.png"))
        positive_paths.extend(random.sample(all_aptos, min(len(all_aptos), 180)))

    idrid_dir = Path("e:/SIH/IDRiD")
    if idrid_dir.is_dir():
        all_idrid = list(idrid_dir.glob("**/*.jpg"))
        positive_paths.extend(random.sample(all_idrid, min(len(all_idrid), 40)))

    sample_f = Path("e:/SIH/Base_Architecture/data/sample/sample_fundus.jpg")
    if sample_f.is_file():
        positive_paths.append(sample_f)

    print(f"[*] Collected {len(positive_paths)} genuine retinal fundus positive samples.")

    # 2. Negative OOD Samples across all required categories
    negative_images = []
    categories = ["vehicle", "document", "screenshot", "person", "landscape", "medical_xray", "abstract"]
    
    samples_per_cat = (len(positive_paths) + len(categories) - 1) // len(categories)
    for cat in categories:
        for _ in range(samples_per_cat):
            img_np = generate_synthetic_negative_image(cat, size=(512, 512))
            negative_images.append(img_np)

    print(f"[*] Generated {len(negative_images)} diverse non-fundus negative samples across {len(categories)} categories.")

    # Combine
    pos_items = [(p, 1) for p in positive_paths]
    neg_items = [(img, 0) for img in negative_images]

    random.shuffle(pos_items)
    random.shuffle(neg_items)

    # Split 70% Train, 15% Val, 15% Test
    def split_data(items):
        n = len(items)
        n_train = int(0.70 * n)
        n_val = int(0.15 * n)
        train = items[:n_train]
        val = items[n_train:n_train + n_val]
        test = items[n_train + n_val:]
        return train, val, test

    pos_tr, pos_va, pos_te = split_data(pos_items)
    neg_tr, neg_va, neg_te = split_data(neg_items)

    train_set = pos_tr + neg_tr
    val_set = pos_va + neg_va
    test_set = pos_te + neg_te

    random.shuffle(train_set)
    random.shuffle(val_set)
    random.shuffle(test_set)

    print(f"[*] Dataset Split: Train={len(train_set)}, Val={len(val_set)}, Test={len(test_set)}")
    return train_set, val_set, test_set


def train_modality_detector(epochs: int = 8, batch_size: int = 16, lr: float = 3e-4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Initializing Fundus Modality Detector training on device: {device}")

    train_set, val_set, test_set = build_and_split_dataset(seed=42)

    train_loader = DataLoader(ModalityDataset(train_set), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(ModalityDataset(val_set), batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(ModalityDataset(test_set), batch_size=batch_size, shuffle=False)

    model = FundusClassifierModel(backbone_name="resnet18", pretrained=False)
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    best_val_f1 = 0.0
    output_dir = MODELS_DIR / "fundus_detector"
    output_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt_path = output_dir / "best_fundus_detector.pth"

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for tensors, labels in train_loader:
            tensors, labels = tensors.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(tensors)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * tensors.size(0)

        train_loss = total_loss / len(train_set)

        # Validation
        model.eval()
        val_preds, val_targets = [], []
        with torch.no_grad():
            for tensors, labels in val_loader:
                tensors = tensors.to(device)
                logits = model(tensors)
                preds = torch.argmax(logits, dim=1).cpu().numpy()
                val_preds.extend(preds)
                val_targets.extend(labels.numpy())

        val_acc = accuracy_score(val_targets, val_preds)
        val_f1 = f1_score(val_targets, val_preds, zero_division=0)

        print(f"Epoch {epoch+1:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val Acc: {val_acc:.4f} | Val F1: {val_f1:.4f}")

        if val_f1 >= best_val_f1:
            best_val_f1 = val_f1
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_f1": val_f1,
                "val_acc": val_acc,
                "backbone": "resnet18",
            }, best_ckpt_path)

    print(f"\n[*] Training Complete. Best model saved to: {best_ckpt_path}")

    # Evaluation on Held-out Test Set
    ckpt = torch.load(best_ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    test_preds, test_targets, test_probs = [], [], []
    with torch.no_grad():
        for tensors, labels in test_loader:
            tensors = tensors.to(device)
            logits = model(tensors)
            probs = F.softmax(logits, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)
            test_preds.extend(preds)
            test_targets.extend(labels.numpy())
            test_probs.extend(probs[:, 1])

    acc = accuracy_score(test_targets, test_preds)
    prec = precision_score(test_targets, test_preds, zero_division=0)
    rec = recall_score(test_targets, test_preds, zero_division=0)
    f1 = f1_score(test_targets, test_preds, zero_division=0)
    cm = confusion_matrix(test_targets, test_preds)

    print("\n" + "=" * 60)
    print("  HELD-OUT TEST SET EVALUATION REPORT (FUNDUS MODALITY DETECTOR)")
    print("=" * 60)
    print(f"• Accuracy:  {acc:.4f} ({acc*100:.2f}%)")
    print(f"• Precision: {prec:.4f} ({prec*100:.2f}%)")
    print(f"• Recall:    {rec:.4f} ({rec*100:.2f}%)")
    print(f"• F1 Score:  {f1:.4f} ({f1*100:.2f}%)")
    print(f"• Confusion Matrix (TN, FP / FN, TP):\n{cm}")
    print("=" * 60)

    # Save metrics JSON
    metrics_path = output_dir / "evaluation_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_samples": len(test_set),
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1_score": float(f1),
            "confusion_matrix": cm.tolist(),
        }, f, indent=2)

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "confusion_matrix": cm,
    }


if __name__ == "__main__":
    train_modality_detector()
