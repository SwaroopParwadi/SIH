"""
Image Quality Service - local OpenCV analysis.

Calculates resolution, blur, brightness and contrast and returns a single
quality_score out of 100.

A low quality score is a WARNING, NOT an automatic fake classification.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import cv2
import numpy as np


class QualityFlag(str, Enum):
    BLUR = "blur"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    RESOLUTION = "resolution"


@dataclass
class ImageQualityReport:
    quality_score: float                       # 0-100
    resolution: Mapping[str, int]              # w, h
    blur: float                                # laplacian variance (higher = sharper)
    brightness: float                          # mean pixel intensity 0-255
    contrast: float                           # std dev of luminance
    flags: list[str]
    recommendation: Optional[str] = None


# ---------------------------------------------------------------------------
# Tunable thresholds - these are heuristics, not truth
# ---------------------------------------------------------------------------
MIN_WIDTH = 640
MIN_HEIGHT = 480
BLUR_VARIANCE_WARN = 100.0     # laplacian variance below this is blurry
BRIGHTNESS_LOW = 40.0         # mean < this is under-exposed
BRIGHTNESS_HIGH = 220.0       # mean > this is over-exposed
CONTRAST_LOW = 15.0           # std < this is low contrast


def analyze_image(file_path: str) -> ImageQualityReport:
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image: {file_path}")

    h, w = img.shape
    resolution = {"width": w, "height": h}

    blur = float(cv2.Laplacian(img, cv2.CV_64F, ksize=3).var())
    brightness = float(img.mean())
    contrast = float(img.std())

    flags: list[str] = []

    if blur < BLUR_VARIANCE_WARN:
        flags.append(QualityFlag.BLUR.value)
    if brightness < BRIGHTNESS_LOW or brightness > BRIGHTNESS_HIGH:
        flags.append(QualityFlag.BRIGHTNESS.value)
    if contrast < CONTRAST_LOW:
        flags.append(QualityFlag.CONTRAST.value)
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        flags.append(QualityFlag.RESOLUTION.value)

    # Weighted quality score. Poor quality lowers the score but never to 0.
    score = 100.0
    score -= min(30.0, (BLUR_VARIANCE_WARN - blur) / BLUR_VARIANCE_WARN * 30) if blur < BLUR_VARIANCE_WARN else 0
    score -= min(20.0, (BRIGHTNESS_LOW - brightness) / BRIGHTNESS_LOW * 20) if brightness < BRIGHTNESS_LOW else 0
    score -= min(20.0, (brightness - BRIGHTNESS_HIGH) / (255 - BRIGHTNESS_HIGH) * 20) if brightness > BRIGHTNESS_HIGH else 0
    score -= min(20.0, (CONTRAST_LOW - contrast) / CONTRAST_LOW * 20) if contrast < CONTRAST_LOW else 0
    score -= min(10.0, (1 - min(w, MIN_WIDTH) / MIN_WIDTH) * 10) if w < MIN_WIDTH else 0
    score -= min(10.0, (1 - min(h, MIN_HEIGHT) / MIN_HEIGHT) * 10) if h < MIN_HEIGHT else 0

    if not flags:
        recommendation = "Image quality is acceptable for OCR/MRZ processing."
    else:
        recommendation = (
            f"Image has {len(flags)} quality concern(s): {', '.join(flags)}. "
            "Processing will still be attempted - quality issues do NOT imply forgery."
        )

    return ImageQualityReport(
        quality_score=max(0.0, min(100.0, round(score, 2))),
        resolution=resolution,
        blur=round(blur, 2),
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        flags=flags,
        recommendation=recommendation,
    )
