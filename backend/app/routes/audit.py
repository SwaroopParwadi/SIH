"""
POST /api/audit/verify
GET  /api/audit/records

Tamper-evident audit verification and record retrieval.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.audit import verify_audit_chain, get_audit_records, append_screening_audit, get_db


def _append_audit_for_case(db, case_id: str, screening_result: dict) -> dict:
    return append_screening_audit(db, case_id, screening_result)


router = APIRouter()


class AuditVerifyRequest(BaseModel):
    case_id: Optional[str] = None


@router.post("/verify", status_code=200)
async def audit_verify(request: AuditVerifyRequest):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    result = verify_audit_chain(db, case_id=request.case_id)
    return result


@router.get("/records", status_code=200)
async def audit_records(
    case_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    limit = max(1, min(500, limit))
    offset = max(0, offset)

    records = get_audit_records(db, case_id=case_id, limit=limit, offset=offset)
    return {
        "case_id": case_id,
        "limit": limit,
        "offset": offset,
        "total": len(get_audit_records(db, case_id=case_id, limit=500, offset=0)),
        "records": [
            {
                "event_type": r.get("event_type"),
                "case_id": r.get("case_id"),
                "record_data": r.get("record_data"),
                "previous_hash": r.get("previous_hash"),
                "current_hash": r.get("current_hash"),
                "created_at": r.get("created_at"),
                "verified": r.get("verified"),
            }
            for r in records
        ],
    }
