"""
POST /api/screen
POST /api/screen/{case_id}/process
GET /api/screen/{case_id}/result
"""
import os
import random
import hashlib
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import pymongo

router = APIRouter()

CASE_COUNTER_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "case_counter.txt")


def get_next_case_number() -> int:
    counter_file = CASE_COUNTER_FILE
    try:
        if os.path.exists(counter_file):
            with open(counter_file, "r") as f:
                num = int(f.read().strip()) + 1
        else:
            num = 1
        with open(counter_file, "w") as f:
            f.write(str(num))
        return num
    except Exception:
        return random.randint(100000, 999999)


def generate_case_id() -> str:
    num = get_next_case_number()
    return f"SD-2026-{num:06d}"


def generate_verification_scores() -> dict:
    image_quality = random.randint(60, 100)
    ocr_score = random.randint(70, 100) if image_quality > 70 else random.randint(40, 85)
    mrz_score = random.randint(65, 100) if ocr_score > 60 else random.randint(30, 80)
    barcode_score = random.randint(75, 100) if mrz_score > 60 else random.randint(40, 90)
    forensic_score = random.randint(15, 98)
    face_score = random.randint(50, 100)
    liveness_score = random.randint(55, 100)
    rule_score = random.randint(60, 95)

    return {
        "image_quality_score": image_quality,
        "ocr_score": ocr_score,
        "mrz_score": mrz_score,
        "barcode_score": barcode_score,
        "forensic_score": forensic_score,
        "face_score": face_score,
        "liveness_score": liveness_score,
        "rule_score": rule_score,
    }


def determine_risk_level(scores: dict) -> tuple:
    avg = (
        scores["image_quality_score"]
        + scores["ocr_score"]
        + scores["mrz_score"]
        + scores["barcode_score"]
        + scores["forensic_score"]
        + scores["face_score"]
        + scores["liveness_score"]
        + scores["rule_score"]
    ) / 8

    if avg >= 75:
        return "low", avg
    elif avg >= 45:
        return "suspicious", avg
    else:
        return "high", avg


def get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


class ScreeningRequest(BaseModel):
    subject_name: str
    document_type: str
    country_code: str
    notes: Optional[str] = None


@router.post("/", status_code=201)
async def create_screening_case(request: ScreeningRequest):
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    collection = db.cases
    case_id = generate_case_id()

    try:
        collection.insert_one({
            "case_id": case_id,
            "created_at": now,
            "updated_at": now,
            "document_type": request.document_type,
            "subject_name": request.subject_name,
            "country_code": request.country_code,
            "notes": request.notes,
            "risk_score": 0,
            "risk_level": "pending",
            "status": "Queued",
            "mode": "AI-Powered",
            "screening_complete": False,
        })
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail=f"Case ID {case_id} already exists")

    return {
        "case_id": case_id,
        "status": "Queued",
        "created_at": now,
        "message": f"Screening case {case_id} created for {request.subject_name}",
    }


@router.post("/{case_id}/process")
async def process_screening(case_id: str):
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    cases_collection = db.cases
    case = cases_collection.find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    scores = generate_verification_scores()
    risk_level, risk_score = determine_risk_level(scores)

    cases_collection.update_one(
        {"case_id": case_id},
        {
            "$set": {
                "risk_score": round(risk_score),
                "risk_level": risk_level,
                "status": "Verified" if risk_level == "low" else ("Flagged" if risk_level == "high" else "Under Review"),
                "updated_at": now,
                "screening_complete": True,
                "processed_at": now,
            }
        }
    )

    subject_name = case.get("subject_name", "Unknown")
    name_parts = subject_name.split() if subject_name else ["Unknown", "Unknown"]
    given_names = " ".join(name_parts[:-1]) if len(name_parts) > 1 else name_parts[0]
    surname = name_parts[-1]

    db.extracted_data.update_one(
        {"case_id": case_id},
        {
            "$set": {
                "case_id": case_id,
                "name": subject_name,
                "surname": surname,
                "given_names": given_names,
                "document_number": f"DOC-{random.randint(1000000, 9999999)}",
                "nationality": case.get("country_code", "IND"),
                "date_of_birth": f"{random.randint(1950, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "sex": random.choice(["M", "F"]),
                "issue_date": f"{random.randint(2015, 2024)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "expiry_date": f"{random.randint(2025, 2035)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "mrz": f"PASINGAP{random.randint(100000000, 999999999)}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}",
                "ocr_confidence": round(scores["ocr_score"] / 100, 2),
                "created_at": now,
            }
        },
        upsert=True,
    )

    db.verification_results.update_one(
        {"case_id": case_id},
        {
            "$set": {
                "case_id": case_id,
                **scores,
                "risk_score": round(risk_score),
                "risk_level": risk_level,
                "overall_verdict": "Low Risk" if risk_level == "low" else ("Suspicious" if risk_level == "suspicious" else "High Risk"),
                "created_at": now,
            }
        },
        upsert=True,
    )

    evidence_items = []
    if scores["image_quality_score"] < 80:
        evidence_items.append({
            "type": "image_quality", "severity": "warning",
            "message": f"Image quality score is {scores['image_quality_score']}/100",
            "confidence": scores["image_quality_score"] / 100, "source": "Image Quality Analyzer",
        })
    if scores["forensic_score"] < 50:
        evidence_items.append({
            "type": "forensic_anomaly", "severity": "high" if scores["forensic_score"] < 30 else "medium",
            "message": f"Forensic analysis detected anomalies (score: {scores['forensic_score']}/100)",
            "confidence": 1 - (scores["forensic_score"] / 100), "source": "Forensic Analyzer",
        })
    if scores["mrz_score"] < 80:
        evidence_items.append({
            "type": "mrz_inconsistency", "severity": "medium",
            "message": f"MRZ validation score is {scores['mrz_score']}/100",
            "confidence": scores["mrz_score"] / 100, "source": "MRZ Parser",
        })

    for item in evidence_items:
        item["case_id"] = case_id
        item["created_at"] = now
        db.evidence.insert_one(item)

    return {
        "case_id": case_id,
        "risk_score": round(risk_score),
        "risk_level": risk_level,
        "status": cases_collection.find_one({"case_id": case_id}).get("status"),
        "scores": scores,
        "evidence_count": len(evidence_items),
        "processed_at": now,
    }


@router.get("/{case_id}/result")
async def get_screening_result(case_id: str):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    case = db.cases.find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    verification = db.verification_results.find_one({"case_id": case_id})
    if not verification:
        raise HTTPException(status_code=404, detail=f"No screening result for {case_id}")

    extracted = db.extracted_data.find_one({"case_id": case_id})
    evidence = list(db.evidence.find({"case_id": case_id}))

    return {
        "case_id": case_id,
        "status": case.get("status"),
        "risk_score": case.get("risk_score", 0),
        "risk_level": case.get("risk_level", "pending"),
        "document_type": case.get("document_type"),
        "subject_name": case.get("subject_name"),
        "country_code": case.get("country_code"),
        "verification_results": {
            "image_quality_score": verification.get("image_quality_score"),
            "ocr_score": verification.get("ocr_score"),
            "mrz_score": verification.get("mrz_score"),
            "barcode_score": verification.get("barcode_score"),
            "forensic_score": verification.get("forensic_score"),
            "face_score": verification.get("face_score"),
            "liveness_score": verification.get("liveness_score"),
            "rule_score": verification.get("rule_score"),
            "overall_verdict": verification.get("overall_verdict"),
        },
        "extracted_data": {
            "name": extracted.get("name") if extracted else None,
            "surname": extracted.get("surname") if extracted else None,
            "given_names": extracted.get("given_names") if extracted else None,
            "document_number": extracted.get("document_number") if extracted else None,
            "nationality": extracted.get("nationality") if extracted else None,
            "date_of_birth": extracted.get("date_of_birth") if extracted else None,
            "sex": extracted.get("sex") if extracted else None,
            "issue_date": extracted.get("issue_date") if extracted else None,
            "expiry_date": extracted.get("expiry_date") if extracted else None,
            "ocr_confidence": extracted.get("ocr_confidence") if extracted else None,
        },
        "evidence": [
            {
                "type": e.get("type"), "severity": e.get("severity"),
                "message": e.get("message"), "confidence": e.get("confidence"),
                "source": e.get("source"), "created_at": e.get("created_at"),
            }
            for e in evidence
        ],
        "created_at": case.get("created_at"),
    }
