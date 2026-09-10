"""
ml/training/train.py
------------------------
Train an AUTHENTIC vs MANIPULATED classifier on the SecureDoc-Dataset.

Preferred model: EfficientNet-B0 (torchvision)
Fallback:        MobileNetV3 Small

- CPU-only safe; automatically uses CUDA if available.
- Uses transfer learning: replaces the classifier head, fine-tunes the full
  network with a smaller LR for the backbone and a larger LR for the head.
- Saves:
    ./models/best_model.pth
    ./models/model_metrics.json
    ./models/training_history.json
    ./models/confusion_matrix.png

Run:
    python ml/training/train.py --data-dir "./SecureDoc-Dataset"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from torchvision.datasets.folder import default_loader

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------
# Dataset
# ----------------------------------------------------------------------

class SecureDocImageDataset(Dataset):
    """
    Reads images from:
        <data_dir>/train/authentic
        <data_dir>/train/manipulated
        <data_dir>/validation/authentic
        <data_dir>/validation/manipulated

    Only keeps files that exist on disk. Labels:
        authentic   -> 0
        manipulated -> 1
    """

    def __init__(self, root: str, split: str, transform=None):
        self.root = Path(root)
        self.split = split
        self.transform = transform

        self.authentic_dir = self.root / split / "authentic"
        self.manipulated_dir = self.root / split / "manipulated"

        self.samples = []

        if self.authentic_dir.is_dir():
            for p in sorted(self.authentic_dir.iterdir()):
                if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    self.samples.append((str(p), 0))

        if self.manipulated_dir.is_dir():
            for p in sorted(self.manipulated_dir.iterdir()):
                if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    self.samples.append((str(p), 1))

        if not self.samples:
            raise FileNotFoundError(
                f"No images found for split='{split}' under '{self.root}'. "
                f"Expected {split}/authentic and {split}/manipulated directories."
            )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = default_loader(path)
        if self.transform is not None:
            img = self.transform(img)
        return img, label, path


# ----------------------------------------------------------------------
# Model selection
# ----------------------------------------------------------------------

def create_model(num_classes: int = 2, fallback: bool = False):
    """
    Preferred: EfficientNet-B0.
    Fallback:  MobileNetV3 Small.
    Returns model, input_size.
    """
    if not fallback:
        try:
            weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
            model = models.efficientnet_b0(weights=weights)
            input_size = weights.transforms().size[0]
            # Replace classifier
            in_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(in_features, num_classes)
            return model, input_size
        except Exception as e:
            print(f"[train] EfficientNet-B0 unavailable ({e}), falling back to MobileNetV3.")
            fallback = True

    if fallback:
        weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
        model = models.mobilenet_v3_small(weights=weights)
        input_size = weights.transforms().size[0]
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
        return model, input_size

    raise RuntimeError("No supported model available.")


# ----------------------------------------------------------------------
# Transforms
# ----------------------------------------------------------------------

def build_train_transform(input_size: int):
    return transforms.Compose([
        transforms.RandomResizedCrop(input_size, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1, hue=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def build_val_transform(input_size: int):
    return transforms.Compose([
        transforms.Resize(int(input_size * 1.14)),
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


# ----------------------------------------------------------------------
# Training
# ----------------------------------------------------------------------

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    start = time.perf_counter()

    for inputs, labels, _ in loader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += inputs.size(0)

    elapsed = time.perf_counter() - start
    avg_loss = running_loss / total if total else 0.0
    acc = correct / total if total else 0.0
    return avg_loss, acc, elapsed


def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_probs = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels, _ in loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += inputs.size(0)

            probs = torch.softmax(outputs, dim=1)
            all_probs.append(probs.cpu().numpy())
            all_labels.append(labels.cpu().numpy())

    avg_loss = running_loss / total if total else 0.0
    acc = correct / total if total else 0.0

    probs = np.vstack(all_probs)
    labels = np.concatenate(all_labels)
    return avg_loss, acc, probs, labels


def plot_confusion_matrix(cm, classes, out_path):
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=range(len(classes)),
           yticks=range(len(classes)),
           xticklabels=classes, yticklabels=classes,
           ylabel="True label",
           xlabel="Predicted label",
           title="Confusion Matrix")
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def run_training(args):
    data_dir = Path(args.data_dir).expanduser().resolve()
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[train] Device: {device}")

    input_size = 224  # fallback default; model will override
    model, input_size = create_model(num_classes=2, fallback=False)
    print(f"[train] Using model: {model.__class__.__name__}, input_size={input_size}")
    model = model.to(device)

    # Transforms
    train_transform = build_train_transform(input_size)
    val_transform = build_val_transform(input_size)

    train_dataset = SecureDocImageDataset(str(data_dir), "train", transform=train_transform)
    val_dataset = SecureDocImageDataset(str(data_dir), "validation", transform=val_transform)

    print(f"[train] Train samples: {len(train_dataset)}")
    print(f"[train] Validation samples: {len(val_dataset)}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=min(4, (os.cpu_count() or 2)),
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=min(4, (os.cpu_count() or 2)),
        pin_memory=(device.type == "cuda"),
    )

    # Loss / optimizer / scheduler
    criterion = nn.CrossEntropyLoss()

    # Differential learning rates: backbone smaller, head larger
    backbone_params = []
    head_params = []
    for name, param in model.named_parameters():
        if param.requires_grad:
            if "classifier" in name or "head" in name:
                head_params.append(param)
            else:
                backbone_params.append(param)

    optimizer = optim.AdamW([
        {"params": backbone_params, "lr": args.learning_rate * 0.1},
        {"params": head_params, "lr": args.learning_rate},
    ], weight_decay=1e-4)

    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_acc = 0.0
    best_model_path = output_dir / "best_model.pth"
    history = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
        "lr": [],
        "epoch_times": [],
    }

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.perf_counter()

        train_loss, train_acc, train_time = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc, val_probs, val_labels = validate(
            model, val_loader, criterion, device
        )

        scheduler.step()

        current_lr = optimizer.param_groups[0]["lr"]
        epoch_time = time.perf_counter() - epoch_start

        history["train_loss"].append(float(train_loss))
        history["train_acc"].append(float(train_acc))
        history["val_loss"].append(float(val_loss))
        history["val_acc"].append(float(val_acc))
        history["lr"].append(float(current_lr))
        history["epoch_times"].append(float(epoch_time))

        print(
            f"[train] Epoch {epoch:03d}/{args.epochs} | "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} | "
            f"lr={current_lr:.6f} time={epoch_time:.1f}s"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "model_state_dict": model.state_dict(),
                "model_class": model.__class__.__name__,
                "input_size": input_size,
                "num_classes": 2,
                "classes": ["authentic", "manipulated"],
                "epoch": epoch,
                "val_acc": float(val_acc),
            }, best_model_path)
            print(f"[train] New best model saved (val_acc={val_acc:.4f}) -> {best_model_path}")

    # ------------------------------------------------------------------
    # Final evaluation on validation set using best model
    # ------------------------------------------------------------------
    print("[train] Loading best model for final metrics report...")
    checkpoint = torch.load(best_model_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])

    val_loss, val_acc, val_probs, val_labels = validate(model, val_loader, criterion, device)

    preds = val_probs.argmax(axis=1)
    true = val_labels.astype(int)

    metrics = {
        "accuracy": float(accuracy_score(true, preds)),
        "precision": float(precision_score(true, preds, zero_division=0)),
        "recall": float(recall_score(true, preds, zero_division=0)),
        "f1": float(f1_score(true, preds, zero_division=0)),
        "val_loss": float(val_loss),
        "best_val_acc": float(best_val_acc),
        "num_train_samples": len(train_dataset),
        "num_val_samples": len(val_dataset),
        "model_class": checkpoint.get("model_class"),
        "input_size": checkpoint.get("input_size"),
        "classes": checkpoint.get("classes"),
    }

    # ROC-AUC if both classes present
    if len(np.unique(true)) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(true, val_probs[:, 1]))
        except Exception as e:
            print(f"[train] ROC-AUC calculation failed: {e}")
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None

    cm = confusion_matrix(true, preds, labels=[0, 1])
    cm_path = output_dir / "confusion_matrix.png"
    plot_confusion_matrix(cm, ["authentic", "manipulated"], cm_path)

    metrics["confusion_matrix"] = cm.tolist()
    metrics["confusion_matrix_path"] = str(cm_path)

    metrics_path = output_dir / "model_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[train] Metrics saved -> {metrics_path}")

    history_path = output_dir / "training_history.json"
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"[train] Training history saved -> {history_path}")

    print("[train] Done.")


def main():
    parser = argparse.ArgumentParser(description="Train authentic vs manipulated classifier")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to SecureDoc-Dataset directory")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=1e-3, help="Peak learning rate for classifier head")
    parser.add_argument("--output-dir", type=str, default="./models", help="Where to save model + metrics")
    args = parser.parse_args()

    run_training(args)


if __name__ == "__main__":
    main()
