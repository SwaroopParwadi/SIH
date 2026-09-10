"""
GET /api/health/system

Returns system health status per module:
- MongoDB
- OCR
- MRZ
- Barcode
- AI
- Face
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ModuleStatus(BaseModel):
    status: str  # READY, NOT_AVAILABLE, ERROR
    details: str = ""


class SystemHealthResponse(BaseModel):
    mongodb: ModuleStatus
    ocr: ModuleStatus
    mrz: ModuleStatus
    barcode: ModuleStatus
    ai: ModuleStatus
    face: ModuleStatus
    overall: str  # READY, DEGRADED, OFFLINE


def _status_from_bool(available: bool, detail: str = "") -> ModuleStatus:
    if available:
        return ModuleStatus(status="READY", details=detail)
    return ModuleStatus(status="NOT_AVAILABLE", details=detail)


@router.get("/health/system", response_model=SystemHealthResponse)
async def system_health():
    from app.main import app as main_app
    db = getattr(main_app.state, "mongodb_db", None)
    mongodb_client = getattr(main_app.state, "mongodb_client", None)

    mongodb_ok = db is not None and mongodb_client is not None
    try:
        if mongodb_ok:
            mongodb_client.admin.command("ping")
            mongodb_detail = "Connected"
        else:
            mongodb_detail = "Not connected"
    except Exception as e:
        mongodb_ok = False
        mongodb_detail = f"Error: {e}"

    # OCR / MRZ / Barcode depend on OpenCV + pyzbar + PaddleOCR
    try:
        import cv2
        import numpy as np
        ocr_detail = "OpenCV available"
        mrz_detail = "OpenCV available"
        barcode_detail = "OpenCV available"
    except Exception as e:
        ocr_detail = f"OpenCV unavailable: {e}"
        mrz_detail = f"OpenCV unavailable: {e}"
        barcode_detail = f"OpenCV unavailable: {e}"

    try:
        from pyzbar import pyzbar
        barcode_detail = "pyzbar available"
    except Exception as e:
        barcode_detail = f"pyzbar unavailable: {e}"

    try:
        from paddleocr import PaddleOCR
        ocr_detail = "PaddleOCR available"
        mrz_detail = "PaddleOCR available"
    except Exception as e:
        ocr_detail = f"PaddleOCR unavailable: {e}"
        mrz_detail = f"PaddleOCR unavailable: {e}"

    # AI model
    import os
    from pathlib import Path
    model_path = Path(__file__).resolve().parent.parent.parent / "models" / "best_model.pth"
    ai_ok = model_path.is_file()
    ai_detail = f"Model file present: {model_path}" if ai_ok else f"Model file not found: {model_path}"

    # Face biometrics
    try:
        import face_recognition
        face_detail = "face_recognition available"
        face_ok = True
    except Exception as e:
        face_ok = False
        face_detail = f"face_recognition unavailable: {e}"

    mongodb = ModuleStatus(status="READY" if mongodb_ok else "ERROR", details=mongodb_detail)
    ocr_ready = "PaddleOCR available" in ocr_detail
    mrz_ready = "PaddleOCR available" in mrz_detail
    barcode_ready = "pyzbar available" in barcode_detail

    def _module_status(ready: bool, detail: str) -> ModuleStatus:
        return ModuleStatus(status="READY" if ready else "NOT_AVAILABLE", details=detail)

    ocr = _module_status(ocr_ready, ocr_detail)
    mrz = _module_status(mrz_ready, mrz_detail)
    barcode = _module_status(barcode_ready, barcode_detail)
    ai = _module_status(ai_ok, ai_detail)
    face = _module_status(face_ok, face_detail)

    modules = [mongodb, ocr, mrz, barcode, ai, face]
    ready_count = sum(1 for m in modules if m.status == "READY")
    if ready_count == len(modules):
        overall = "READY"
    elif ready_count > 0:
        overall = "DEGRADED"
    else:
        overall = "OFFLINE"

    return SystemHealthResponse(
        mongodb=mongodb,
        ocr=ocr,
        mrz=mrz,
        barcode=barcode,
        ai=ai,
        face=face,
        overall=overall,
    )
