"""
GET /api/cases — paginated case history
GET /api/cases/{case_id} — single case details
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import random
import pymongo

router = APIRouter()


class CaseListResponse(BaseModel):
    cases: list
    total: int
    page: int
    page_size: int
    total_pages: int


def get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    document_type: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Get paginated list of cases from MongoDB Atlas.

    Query params:
    - page: page number (default 1)
    - page_size: items per page (default 20, max 100)
    - status: filter by status (Queued, Verified, Under Review, Flagged)
    - risk_level: filter by risk level (low, suspicious, high, pending)
    - document_type: filter by document type
    - search: search by case_id, subject_name, or document_number
    """
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    collection = db.cases
    query = {"screening_complete": True}

    if status:
        query["status"] = status
    if risk_level:
        query["risk_level"] = risk_level
    if document_type:
        query["document_type"] = document_type
    if search:
        query["$or"] = [
            {"case_id": {"$regex": search, "$options": "i"}},
            {"subject_name": {"$regex": search, "$options": "i"}},
            {"document_number": {"$regex": search, "$options": "i"}},
        ]

    # Count total matching documents
    total = collection.count_documents(query)
    total_pages = (total + page_size - 1) // page_size

    # Get paginated results
    skip = (page - 1) * page_size
    cases = list(
        collection.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    return CaseListResponse(
        cases=[
            {
                "case_id": c.get("case_id"),
                "subject_name": c.get("subject_name", "Unknown"),
                "document_type": c.get("document_type", "Unknown"),
                "country_code": c.get("country_code", "UNK"),
                "risk_score": c.get("risk_score", 0),
                "risk_level": c.get("risk_level", "pending"),
                "status": c.get("status", "Queued"),
                "mode": c.get("mode", "AI-Powered"),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at"),
            }
            for c in cases
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    """
    Get full details of a single case by case_id (SD-2026-NNNNNN format).
    Returns case info, extracted data, verification results, and evidence.
    """
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    # Get case
    case = db.cases.find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Get extracted data (if exists)
    extracted = db.extracted_data.find_one({"case_id": case_id})

    # Get verification results (if exists)
    verification = db.verification_results.find_one({"case_id": case_id})

    # Get evidence (if any)
    evidence = list(db.evidence.find({"case_id": case_id}))

    # Build response
    return {
        "case_id": case.get("case_id"),
        "subject_name": case.get("subject_name", "Unknown"),
        "document_type": case.get("document_type", "Unknown"),
        "country_code": case.get("country_code", "UNK"),
        "notes": case.get("notes"),
        "risk_score": case.get("risk_score", 0),
        "risk_level": case.get("risk_level", "pending"),
        "status": case.get("status", "Queued"),
        "mode": case.get("mode", "AI-Powered"),
        "created_at": case.get("created_at"),
        "updated_at": case.get("updated_at"),
        "processed_at": case.get("processed_at"),
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
            "mrz": extracted.get("mrz") if extracted else None,
            "ocr_confidence": extracted.get("ocr_confidence") if extracted else None,
        } if extracted else None,
        "verification_results": {
            "image_quality_score": verification.get("image_quality_score") if verification else None,
            "ocr_score": verification.get("ocr_score") if verification else None,
            "mrz_score": verification.get("mrz_score") if verification else None,
            "barcode_score": verification.get("barcode_score") if verification else None,
            "forensic_score": verification.get("forensic_score") if verification else None,
            "face_score": verification.get("face_score") if verification else None,
            "liveness_score": verification.get("liveness_score") if verification else None,
            "rule_score": verification.get("rule_score") if verification else None,
            "overall_verdict": verification.get("overall_verdict") if verification else None,
        } if verification else None,
        "evidence": [
            {
                "type": e.get("type"),
                "severity": e.get("severity"),
                "message": e.get("message"),
                "confidence": e.get("confidence"),
                "source": e.get("source"),
                "created_at": e.get("created_at"),
            }
            for e in evidence
        ],
    }
