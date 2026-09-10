"""
Model intelligence service.

Loads the trained authentic vs manipulated classifier and provides a
predict method that returns a structured result.

If best_model.pth does not exist or cannot be loaded, returns
MODEL_NOT_LOADED instead of fake predictions.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
from torchvision import models, transforms
from torchvision.datasets.folder import default_loader

CLASSES = ["authentic", "manipulated"]


def build_eval_transform(input_size: int):
    return transforms.Compose([
        transforms.Resize(int(input_size * 1.14)),
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def load_model_from_checkpoint(checkpoint_path: str, device: torch.device):
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    model_class = checkpoint.get("model_class")
    num_classes = checkpoint.get("num_classes", 2)
    input_size = checkpoint.get("input_size", 224)
    classes = checkpoint.get("classes", CLASSES)

    if model_class == "EfficientNet_B0":
        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
    elif model_class == "MobileNet_V3_Small":
        model = models.mobilenet_v3_small(weights=None)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
    else:
        raise ValueError(f"Unknown model_class in checkpoint: {model_class}")

    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    return model, input_size, classes


class ModelIntelligence:
    """
    Lazy-loads the model on first use. Thread-unsafe by design; suitable
    for single-process FastAPI worker. If model is not available, every
    call returns MODEL_NOT_LOADED.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._model: Optional[torch.nn.Module] = None
        self._device: Optional[torch.device] = None
        self._transform: Optional[transforms.Compose] = None
        self._input_size: Optional[int] = None
        self._classes: Optional[list] = None
        self._load_error: Optional[str] = None

    def _ensure_loaded(self):
        if self._model is not None:
            return

        if not self.model_path or not os.path.isfile(self.model_path):
            self._load_error = f"Model file not found: {self.model_path}"
            return

        try:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._model, self._input_size, self._classes = load_model_from_checkpoint(
                self.model_path, self._device
            )
            self._transform = build_eval_transform(self._input_size)
        except Exception as e:
            self._load_error = f"Failed to load model: {e}"

    def predict(self, image_path: str) -> dict:
        self._ensure_loaded()

        if self._load_error or self._model is None:
            return {
                "status": "MODEL_NOT_LOADED",
                "error": self._load_error or "Model not loaded",
                "label": None,
                "authentic_probability": None,
                "manipulated_probability": None,
            }

        try:
            img = default_loader(image_path)
            if img is None:
                return {
                    "status": "INFERENCE_ERROR",
                    "error": f"Cannot read image: {image_path}",
                    "label": None,
                    "authentic_probability": None,
                    "manipulated_probability": None,
                }
        except Exception as e:
            return {
                "status": "INFERENCE_ERROR",
                "error": f"Image read error: {e}",
                "label": None,
                "authentic_probability": None,
                "manipulated_probability": None,
            }

        input_tensor = self._transform(img).unsqueeze(0).to(self._device)

        with torch.no_grad():
            outputs = self._model(input_tensor)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]

        authentic_prob = float(probs[0])
        manipulated_prob = float(probs[1])
        label = self._classes[1] if manipulated_prob > authentic_prob else self._classes[0]

        return {
            "status": "OK",
            "label": label,
            "authentic_probability": round(authentic_prob, 4),
            "manipulated_probability": round(manipulated_prob, 4),
            "model_path": self.model_path,
            "device": self._device.type,
            "classes": self._classes,
        }
