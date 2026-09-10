"""
ml/inference/predict.py
------------------------
Run inference with the saved classifier.

Output:
  label                  -> "authentic" or "manipulated"
  authentic_probability  -> probability for class 0
  manipulated_probability -> probability for class 1

If best_model.pth does not exist, returns MODEL_NOT_LOADED instead of fake
predictions.

Run examples:
    python ml/inference/predict.py --model "./models/best_model.pth" --image "./path/to/image.jpg"
    python ml/inference/predict.py --model "./models/best_model.pth" --image "./SecureDoc-Dataset/test/authentic/SD_00000_authentic.jpg"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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


def predict(model, transform, image_path: str, device: torch.device):
    img = default_loader(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    input_tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(input_tensor)
        probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]

    return probs


def main():
    parser = argparse.ArgumentParser(description="Run inference with the saved classifier")
    parser.add_argument("--model", type=str, required=True, help="Path to best_model.pth")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    args = parser.parse_args()

    model_path = Path(args.model).expanduser().resolve()
    image_path = Path(args.image).expanduser().resolve()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not model_path.is_file():
        result = {
            "status": "MODEL_NOT_LOADED",
            "error": f"Model file not found: {model_path}",
            "label": None,
            "authentic_probability": None,
            "manipulated_probability": None,
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    try:
        model, input_size, classes = load_model_from_checkpoint(str(model_path), device)
    except Exception as e:
        result = {
            "status": "MODEL_NOT_LOADED",
            "error": f"Failed to load model: {e}",
            "label": None,
            "authentic_probability": None,
            "manipulated_probability": None,
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    transform = build_eval_transform(input_size)

    try:
        probs = predict(model, transform, str(image_path), device)
    except Exception as e:
        result = {
            "status": "INFERENCE_ERROR",
            "error": f"Failed to run inference: {e}",
            "label": None,
            "authentic_probability": None,
            "manipulated_probability": None,
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    authentic_prob = float(probs[0])
    manipulated_prob = float(probs[1])
    label = classes[1] if manipulated_prob > authentic_prob else classes[0]

    result = {
        "status": "OK",
        "label": label,
        "authentic_probability": round(authentic_prob, 4),
        "manipulated_probability": round(manipulated_prob, 4),
        "model_path": str(model_path),
        "image_path": str(image_path),
        "device": device.type,
        "classes": classes,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
