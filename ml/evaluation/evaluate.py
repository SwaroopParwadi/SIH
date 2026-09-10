"""
ml/evaluation/evaluate.py
--------------------------
Evaluate the saved classifier on the SecureDoc-Dataset TEST split.

Calculates:
  Accuracy
  Precision
  Recall
  F1
  ROC-AUC (if both classes present)
  Confusion matrix
  Inference time per image

NEVER fabricates metrics. If the model cannot be loaded, exits with an error.

Run:
    python ml/evaluation/evaluate.py --data-dir "./SecureDoc-Dataset" --model "./models/best_model.pth"
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
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
# Dataset (test split only)
# ----------------------------------------------------------------------

class SecureDocTestDataset(Dataset):
    def __init__(self, root: str, split: str = "test", transform=None):
        self.root = Path(root)
        self.split = split
        self.transform = transform

        authentic_dir = self.root / split / "authentic"
        manipulated_dir = self.root / split / "manipulated"

        self.samples = []

        if authentic_dir.is_dir():
            for p in sorted(authentic_dir.iterdir()):
                if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    self.samples.append((str(p), 0))
        if manipulated_dir.is_dir():
            for p in sorted(manipulated_dir.iterdir()):
                if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    self.samples.append((str(p), 1))

        if not self.samples:
            raise FileNotFoundError(
                f"No images found for split='{split}' under '{self.root}'."
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
# Model reconstruction from checkpoint
# ----------------------------------------------------------------------

def load_model_from_checkpoint(checkpoint_path: str, device: torch.device):
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    model_class = checkpoint.get("model_class")
    num_classes = checkpoint.get("num_classes", 2)
    input_size = checkpoint.get("input_size", 224)
    classes = checkpoint.get("classes", ["authentic", "manipulated"])

    if model_class == "EfficientNet_B0":
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
    elif model_class == "MobileNet_V3_Small":
        weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
        model = models.mobilenet_v3_small(weights=None)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
    else:
        raise ValueError(f"Unknown model_class in checkpoint: {model_class}")

    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    return model, input_size, classes


# ----------------------------------------------------------------------
# Transforms
# ----------------------------------------------------------------------

def build_eval_transform(input_size: int):
    return transforms.Compose([
        transforms.Resize(int(input_size * 1.14)),
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


# ----------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------

def evaluate(args):
    data_dir = Path(args.data_dir).expanduser().resolve()
    model_path = Path(args.model).expanduser().resolve()

    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[evaluate] Device: {device}")

    model, input_size, classes = load_model_from_checkpoint(str(model_path), device)
    print(f"[evaluate] Model: {model.__class__.__name__}, input_size={input_size}, classes={classes}")

    transform = build_eval_transform(input_size)
    dataset = SecureDocTestDataset(str(data_dir), "test", transform=transform)
    print(f"[evaluate] Test samples: {len(dataset)}")

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=min(4, (os.cpu_count() or 2)),
        pin_memory=(device.type == "cuda"),
    )

    all_probs = []
    all_labels = []
    all_paths = []
    total_inf_time = 0.0
    n_batches = 0

    with torch.no_grad():
        for inputs, labels, paths in loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            start = time.perf_counter()
            outputs = model(inputs)
            elapsed = time.perf_counter() - start

            total_inf_time += elapsed
            n_batches += 1

            probs = torch.softmax(outputs, dim=1)
            all_probs.append(probs.cpu().numpy())
            all_labels.append(labels.cpu().numpy())
            all_paths.extend(paths)

    avg_inf_time_per_sample = total_inf_time / len(dataset) if len(dataset) else 0.0

    probs = np.vstack(all_probs)
    labels = np.concatenate(all_labels).astype(int)
    preds = probs.argmax(axis=1)

    metrics = {
        "accuracy": float(accuracy_score(labels, preds)),
        "precision": float(precision_score(labels, preds, zero_division=0)),
        "recall": float(recall_score(labels, preds, zero_division=0)),
        "f1": float(f1_score(labels, preds, zero_division=0)),
        "num_test_samples": len(dataset),
        "inference_time_seconds_total": float(total_inf_time),
        "inference_time_seconds_per_sample": float(avg_inf_time_per_sample),
        "model_path": str(model_path),
        "classes": classes,
    }

    if len(np.unique(labels)) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(labels, probs[:, 1]))
        except Exception as e:
            print(f"[evaluate] ROC-AUC calculation failed: {e}")
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None

    cm = confusion_matrix(labels, preds, labels=[0, 1])
    metrics["confusion_matrix"] = cm.tolist()

    cm_path = model_path.parent / "confusion_matrix.png"
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=range(len(classes)),
           yticks=range(len(classes)),
           xticklabels=classes, yticklabels=classes,
           ylabel="True label",
           xlabel="Predicted label",
           title="Confusion Matrix (Test Set)")
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    plt.tight_layout()
    fig.savefig(cm_path, dpi=150)
    plt.close(fig)
    print(f"[evaluate] Confusion matrix saved -> {cm_path}")

    metrics_path = model_path.parent / "evaluation_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[evaluate] Evaluation metrics saved -> {metrics_path}")

    print("[evaluate] Results:")
    for k, v in metrics.items():
        if k != "confusion_matrix":
            print(f"  {k}: {v}")

    print("[evaluate] Done.")


def main():
    parser = argparse.ArgumentParser(description="Evaluate the saved classifier on the test split")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to SecureDoc-Dataset directory")
    parser.add_argument("--model", type=str, required=True, help="Path to best_model.pth")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size for evaluation")
    args = parser.parse_args()

    evaluate(args)


if __name__ == "__main__":
    main()
