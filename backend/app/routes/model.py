"""
GET /api/model/metrics
"""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/model/metrics")
async def get_model_metrics():
    """
    Get AI model performance metrics.
    These are stored mock metrics for the prototype.
    In production, these would come from the ML training pipeline.
    """
    now = datetime.now(timezone.utc).isoformat()

    return {
        "model_name": "DetectionNet-v2.1",
        "model_type": "binary_classification",
        "version": "2.1.0",
        "status": "production",
        "metrics": {
            "accuracy": 96.2,
            "precision": 94.8,
            "recall": 93.5,
            "f1_score": 94.1,
            "roc_auc": 0.987,
            "inference_time_ms": 340,
            "false_positive_rate": 5.2,
            "false_negative_rate": 6.5,
        },
        "benchmarks": {
            "test_samples": 600,
            "train_samples": 1400,
            "validation_samples": 300,
            "true_positives": 287,
            "false_positives": 15,
            "true_negatives": 291,
            "false_negatives": 7,
        },
        "detection_by_type": [
            {"manipulation_type": "text_change", "accuracy": 94.4, "samples": 125},
            {"manipulation_type": "photo_change", "accuracy": 96.4, "samples": 110},
            {"manipulation_type": "number_change", "accuracy": 92.6, "samples": 95},
            {"manipulation_type": "date_change", "accuracy": 90.0, "samples": 80},
            {"manipulation_type": "copy_paste", "accuracy": 95.0, "samples": 100},
            {"manipulation_type": "clone", "accuracy": 93.6, "samples": 110},
            {"manipulation_type": "compression", "accuracy": 88.9, "samples": 90},
            {"manipulation_type": "mixed", "accuracy": 92.2, "samples": 90},
        ],
        "last_updated": now,
        "model_file": "models/DetectionNet-v2.1.pt",
        "framework": "PyTorch",
        "input_shape": [3, 455, 700],
        "note": "Mock metrics for SIH 2026 prototype. Replace with real training data for production.",
    }
