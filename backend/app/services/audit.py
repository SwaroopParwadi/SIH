"""
Tamper-evident audit chain using SHA-256.

Each audit record stores:
- previous_hash
- current_hash = SHA256(previous_hash + canonical_record_data)

POST /api/audit/verify checks the chain integrity and returns VALID or COMPROMISED.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

from pymongo import MongoClient


def get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


def _canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def compute_current_hash(previous_hash: str, record_data: dict) -> str:
    canonical = _canonical_json(record_data)
    combined = previous_hash + canonical
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def create_audit_record(
    db,
    event_type: str,
    case_id: Optional[str],
    record_data: dict,
    previous_hash: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()

    if previous_hash is None:
        previous_hash = "0" * 64

    current_hash = compute_current_hash(previous_hash, record_data)

    entry = {
        "event_type": event_type,
        "case_id": case_id,
        "record_data": record_data,
        "previous_hash": previous_hash,
        "current_hash": current_hash,
        "created_at": now,
        "verified": False,
    }

    db.audit_chain.insert_one(entry)
    return entry


def append_screening_audit(db, case_id: str, screening_result: dict) -> dict:
    previous = _get_latest_hash(db, case_id)
    record_data = {
        "case_id": case_id,
        "event": "screening_completed",
        "risk_score": screening_result.get("risk_score"),
        "risk_level": screening_result.get("risk_level"),
        "status": screening_result.get("status"),
        "human_review_required": screening_result.get("human_review_required"),
        "evidence_count": screening_result.get("evidence_count"),
        "processed_at": screening_result.get("processed_at"),
    }
    return create_audit_record(db, "screening_completed", case_id, record_data, previous_hash=previous)


def _get_latest_hash(db, case_id: Optional[str] = None) -> str:
    query = {}
    if case_id:
        query["case_id"] = case_id
    latest = db.audit_chain.find(query).sort("created_at", -1).limit(1).next()
    if latest:
        return latest["current_hash"]
    return "0" * 64


def verify_audit_chain(db, case_id: Optional[str] = None) -> dict:
    """
    Verify the audit chain for a given case_id (or global chain if case_id is None).

    Returns:
    {
        "status": "VALID" | "COMPROMISED",
        "case_id": ...,
        "records_checked": int,
        "broken_at": Optional[dict],
        "message": str
    }
    """
    query = {}
    if case_id:
        query["case_id"] = case_id

    records = list(db.audit_chain.find(query).sort("created_at", 1))
    if not records:
        return {
            "status": "VALID",
            "case_id": case_id,
            "records_checked": 0,
            "broken_at": None,
            "message": "No audit records found.",
        }

    previous = "0" * 64
    for idx, rec in enumerate(records):
        expected = compute_current_hash(previous, rec["record_data"])
        if rec["current_hash"] != expected:
            return {
                "status": "COMPROMISED",
                "case_id": case_id,
                "records_checked": idx + 1,
                "broken_at": {
                    "record_id": str(rec["_id"]),
                    "created_at": rec["created_at"],
                    "expected_hash": expected,
                    "stored_hash": rec["current_hash"],
                },
                "message": f"Audit chain compromised at record index {idx}.",
            }
        previous = rec["current_hash"]

    return {
        "status": "VALID",
        "case_id": case_id,
        "records_checked": len(records),
        "broken_at": None,
        "message": "Audit chain integrity verified.",
    }


def get_audit_records(db, case_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> list:
    query = {}
    if case_id:
        query["case_id"] = case_id
    return list(db.audit_chain.find(query).sort("created_at", -1).skip(offset).limit(limit))
