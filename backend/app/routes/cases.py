"""
GET /api/cases — paginated case history
GET /api/cases/{case_id} — single case details
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import pymongo

router = APIRouter()


def get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


def _paginate(items: list, page: int, page_size: int) -> dict:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end] if start < total else []
    return {
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


class CaseListResponse(BaseModel):
    cases: list
    total: int
    page: int
    page_size: int
    total_pages: int


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
    Get paginated list of cases from MongoDB.

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
    query: dict = {}

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

    total = collection.count_documents(query)
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
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    """
    Get full details of a single case by case_id (SD-2026-NNNNNN format).
    Returns case info, extracted data, verification results, biometrics, evidence, audit chain status.
    """
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    case = db.cases.find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    extracted = db.extracted_data.find_one({"case_id": case_id})
    verification = db.verification_results.find_one({"case_id": case_id})
    evidence = list(db.evidence.find({"case_id": case_id}))

    # Audit chain verification for this case
    from app.services.audit import verify_audit_chain
    audit_status = verify_audit_chain(db, case_id=case_id)

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
        "human_review_required": verification.get("human_review_required") if verification else None,
        "review_recommendation": verification.get("review_recommendation") if verification else None,
        "disclaimer": verification.get("disclaimer") if verification else None,
        "extracted_data": (
            {
                "name": extracted.get("name"),
                "surname": extracted.get("surname"),
                "given_names": extracted.get("given_names"),
                "document_number": extracted.get("document_number"),
                "nationality": extracted.get("nationality"),
                "date_of_birth": extracted.get("date_of_birth"),
                "sex": extracted.get("sex"),
                "issue_date": extracted.get("issue_date"),
                "expiry_date": extracted.get("expiry_date"),
                "mrz": extracted.get("mrz"),
                "ocr_confidence": extracted.get("ocr_confidence"),
                "ocr_status": extracted.get("ocr_status"),
                "mrz_status": extracted.get("mrz_status"),
                "ocr_name": extracted.get("ocr_name"),
                "mrz_name": extracted.get("mrz_name"),
                "ocr_document_number": extracted.get("ocr_document_number"),
                "mrz_document_number": extracted.get("mrz_document_number"),
                "ocr_nationality": extracted.get("ocr_nationality"),
                "mrz_nationality": extracted.get("mrz_nationality"),
                "ocr_sex": extracted.get("ocr_sex"),
                "mrz_sex": extracted.get("mrz_sex"),
                "ocr_date_of_birth": extracted.get("ocr_date_of_birth"),
                "mrz_date_of_birth": extracted.get("mrz_date_of_birth"),
                "ocr_expiry_date": extracted.get("ocr_expiry_date"),
                "mrz_expiry_date": extracted.get("mrz_expiry_date"),
                "cross_match_overall": extracted.get("cross_match_overall"),
                "cross_match_details": extracted.get("cross_match_details"),
                "barcode_comparison": extracted.get("barcode_comparison"),
                "model_info": extracted.get("model_info"),
                "biometrics": extracted.get("biometrics"),
                "image_quality": extracted.get("image_quality"),
            }
            if extracted else None
        ),
        "verification_results": (
            {
                "image_quality_score": verification.get("image_quality_score"),
                "ocr_score": verification.get("ocr_score"),
                "mrz_score": verification.get("mrz_score"),
                "barcode_score": verification.get("barcode_score"),
                "forensic_score": verification.get("forensic_score"),
                "face_score": verification.get("face_score"),
                "liveness_score": verification.get("liveness_score"),
                "rule_score": verification.get("rule_score"),
                "ocr_mrz_consistency_score": verification.get("ocr_mrz_consistency_score"),
                "barcode_consistency_score": verification.get("barcode_consistency_score"),
                "overall_verdict": verification.get("overall_verdict"),
                "model_status": verification.get("model_status"),
                "model_label": verification.get("model_label"),
                "model_authentic_probability": verification.get("model_authentic_probability"),
                "model_manipulated_probability": verification.get("model_manipulated_probability"),
                "face_verification_status": verification.get("face_verification_status"),
                "face_similarity_score": verification.get("face_similarity_score"),
                "face_match_status": verification.get("face_match_status"),
                "face_confidence": verification.get("face_confidence"),
                "liveness_status": verification.get("liveness_status"),
                "liveness_score": verification.get("liveness_score"),
                "liveness_challenge_passed": verification.get("liveness_challenge_passed"),
                "liveness_notes": verification.get("liveness_notes"),
                "liveness_prototype": verification.get("liveness_prototype"),
            }
            if verification else None
        ),
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
        "audit": audit_status,
    }
