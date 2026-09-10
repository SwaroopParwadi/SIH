"""
GET  /api/demo/mode
POST /api/demo/start
POST /api/demo/run

Demo mode endpoints using the existing synthetic dataset.
Works offline. Clearly marked DEMO MODE.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
from pathlib import Path
from datetime import datetime, timezone

router = APIRouter()

DEMO_ROOT = Path(__file__).resolve().parent.parent.parent / "SecureDoc-Dataset"


class DemoModeInfo(BaseModel):
    name: str
    description: str
    dataset_category: str
    online: bool = False
    demo_mode: bool = True


class DemoModesResponse(BaseModel):
    demo_mode: bool = True
    modes: list[DemoModeInfo]


DEMO_MODES = [
    DemoModeInfo(
        name="Demo Genuine",
        description="Synthetic genuine document from the existing offline dataset.",
        dataset_category="authentic",
    ),
    DemoModeInfo(
        name="Demo Manipulated",
        description="Synthetic manipulated document from the existing offline dataset.",
        dataset_category="manipulated",
    ),
    DemoModeInfo(
        name="Demo Suspicious",
        description="Synthetic document likely to produce suspicious/high-risk screening results from the existing offline dataset.",
        dataset_category="manipulated",
    ),
]


def _get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


def _pick_random_image(category: str) -> Optional[str]:
    if not DEMO_ROOT.is_dir():
        return None
    category_dir = DEMO_ROOT / category
    if not category_dir.is_dir():
        return None
    images = [
        p for p in category_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    if not images:
        return None
    return str(random.choice(images))


def _generate_demo_case_id() -> str:
    num = random.randint(100000, 999999)
    return f"SD-2026-DEMO-{num:06d}"


@router.get("/demo/mode", response_model=DemoModesResponse)
async def list_demo_modes():
    return DemoModesResponse(demo_mode=True, modes=DEMO_MODES)


@router.post("/demo/start", status_code=201)
async def start_demo(mode: str = "Demo Genuine", case_id: Optional[str] = None):
    """
    Start a demo screening case using the existing synthetic dataset.

    Returns a case_id and the chosen file_path.
    """
    db = _get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    category = {
        "Demo Genuine": "authentic",
        "Demo Manipulated": "manipulated",
        "Demo Suspicious": "manipulated",
    }.get(mode, "authentic")

    file_path = _pick_random_image(category)
    if not file_path:
        raise HTTPException(status_code=500, detail=f"No images found in dataset category '{category}'.")

    now = datetime.now(timezone.utc).isoformat()

    if not case_id:
        case_id = _generate_demo_case_id()

    try:
        db.cases.insert_one({
            "case_id": case_id,
            "created_at": now,
            "updated_at": now,
            "document_type": "IDENTITY_DOCUMENT",
            "subject_name": "DEMO_SUBJECT",
            "country_code": "DEMO",
            "notes": f"Demo mode: {mode}",
            "risk_score": 0,
            "risk_level": "pending",
            "status": "Queued",
            "mode": "Demo",
            "document_file_path": file_path,
            "demo_mode": True,
            "screening_complete": False,
        })
    except Exception:
        raise HTTPException(status_code=409, detail=f"Case ID {case_id} already exists")

    return {
        "case_id": case_id,
        "status": "Queued",
        "created_at": now,
        "mode": mode,
        "demo_mode": True,
        "file_path": file_path,
        "dataset_category": category,
        "message": f"Demo case {case_id} created from {category} dataset.",
    }


@router.post("/demo/run", status_code=201)
async def run_demo(mode: str = "Demo Genuine"):
    """
    Create a demo case and immediately run screening on it.
    """
    db = _get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    category = {
        "Demo Genuine": "authentic",
        "Demo Manipulated": "manipulated",
        "Demo Suspicious": "manipulated",
    }.get(mode, "authentic")

    file_path = _pick_random_image(category)
    if not file_path:
        raise HTTPException(status_code=500, detail=f"No images found in dataset category '{category}'.")

    now = datetime.now(timezone.utc).isoformat()

    case_id = _generate_demo_case_id()

    try:
        db.cases.insert_one({
            "case_id": case_id,
            "created_at": now,
            "updated_at": now,
            "document_type": "IDENTITY_DOCUMENT",
            "subject_name": "DEMO_SUBJECT",
            "country_code": "DEMO",
            "notes": f"Demo mode: {mode}",
            "risk_score": 0,
            "risk_level": "pending",
            "status": "Queued",
            "mode": "Demo",
            "document_file_path": file_path,
            "demo_mode": True,
            "screening_complete": False,
        })
    except Exception:
        raise HTTPException(status_code=409, detail=f"Case ID {case_id} already exists")

    from app.routes.screening import process_screening
    result = await process_screening(case_id, request=None)

    return {
        "case_id": case_id,
        "mode": mode,
        "demo_mode": True,
        "dataset_category": category,
        "file_path": file_path,
        "screening": result,
    }
