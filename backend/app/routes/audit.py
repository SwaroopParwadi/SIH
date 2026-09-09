"""
GET /api/audit — paginated audit log with hash chain
POST /api/audit/verify — verify hash chain integrity
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
import pymongo

router = APIRouter()


def get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


def compute_hash(data: dict) -> str:
    """Compute SHA-256 hash of a document (excluding _id)."""
    # Create a deterministic JSON string for hashing
    hashable = {
        "case_id": data.get("case_id", ""),
        "action": data.get("action", ""),
        "timestamp": data.get("timestamp", ""),
        "previous_hash": data.get("previous_hash", ""),
        "details": data.get("details", ""),
    }
    json_str = json.dumps(hashable, sort_keys=True)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


@router.get("/")
async def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_id: Optional[str] = None,
    action: Optional[str] = None,
    risk_level: Optional[str] = None,
):
    """
    Get paginated audit log from MongoDB Atlas.

    Each audit entry includes a SHA-256 hash that chains to the previous entry,
    ensuring tamper detection.

    Query params:
    - page: page number (default 1)
    - page_size: items per page (default 20, max 100)
    - case_id: filter by case ID
    - action: filter by action type
    - risk_level: filter by risk level (critical, warning, info, success)
    """
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    collection = db.audit_logs
    query = {}

    if case_id:
        query["case_id"] = case_id
    if action:
        query["action"] = action
    if risk_level:
        query["risk_level"] = risk_level

    total = collection.count_documents(query)
    total_pages = (total + page_size - 1) // page_size
    skip = (page - 1) * page_size

    logs = list(collection.find(query).sort("timestamp", -1).skip(skip).limit(page_size))

    return {
        "audit_logs": [
            {
                "case_id": log.get("case_id"),
                "action": log.get("action"),
                "timestamp": log.get("timestamp"),
                "previous_hash": log.get("previous_hash"),
                "current_hash": log.get("current_hash"),
                "details": log.get("details"),
                "risk_level": log.get("risk_level", "info"),
                "user": log.get("user", "System"),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/verify")
async def verify_audit_chain(
    case_id: Optional[str] = None,
):
    """
    Verify the SHA-256 hash chain integrity of audit logs.

    Returns:
    - valid: bool — whether the chain is intact
    - total_entries: number of entries verified
    - corrupted_entries: entries where hash mismatch detected
    - first_hash: hash of first entry (genesis)
    - last_hash: hash of last entry
    """
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    collection = db.audit_logs

    # Build query
    query = {}
    if case_id:
        query["case_id"] = case_id

    # Get all entries in chronological order (oldest first for chain verification)
    entries = list(collection.find(query).sort("timestamp", 1))

    if not entries:
        return {
            "valid": True,
            "total_entries": 0,
            "corrupted_entries": [],
            "first_hash": None,
            "last_hash": None,
            "message": "No audit entries found",
        }

    corrupted = []
    prev_hash = ""

    for i, entry in enumerate(entries):
        stored_hash = entry.get("current_hash", "")
        entry_copy = dict(entry)
        entry_copy["previous_hash"] = prev_hash

        computed_hash = compute_hash(entry_copy)

        if stored_hash != computed_hash:
            corrupted.append({
                "index": i,
                "case_id": entry.get("case_id"),
                "timestamp": entry.get("timestamp"),
                "stored_hash": stored_hash,
                "computed_hash": computed_hash,
            })

        # Update prev_hash for next iteration
        if stored_hash:
            prev_hash = stored_hash
        else:
            # If no stored hash, use computed for next chain
            prev_hash = computed_hash

    is_valid = len(corrupted) == 0
    first_entry = entries[0]
    last_entry = entries[-1]

    return {
        "valid": is_valid,
        "total_entries": len(entries),
        "corrupted_entries": corrupted,
        "first_hash": first_entry.get("current_hash"),
        "last_hash": last_entry.get("current_hash"),
        "first_entry_timestamp": first_entry.get("timestamp"),
        "last_entry_timestamp": last_entry.get("timestamp"),
        "message": "Hash chain integrity verified successfully" if is_valid else f"Found {len(corrupted)} corrupted entry/entries in hash chain",
    }


@router.post("/", status_code=201)
async def create_audit_entry(
    case_id: str,
    action: str,
    details: Optional[str] = None,
    risk_level: str = "info",
    user: str = "System",
):
    """
    Create a new audit log entry with SHA-256 hash chain.

    The current_hash is computed from the entry data + previous_hash,
    creating an immutable chain of audit records.
    """
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    collection = db.audit_logs
    now = datetime.now(timezone.utc)

    # Find the most recent entry to get its hash
    last_entry = collection.find_one(sort=[("timestamp", -1)])
    previous_hash = last_entry.get("current_hash", "") if last_entry else ""

    timestamp_iso = now.isoformat()

    # Create entry data for hashing
    entry_data = {
        "case_id": case_id,
        "action": action,
        "timestamp": timestamp_iso,
        "previous_hash": previous_hash,
        "details": details or "",
    }

    # Compute current hash
    current_hash = compute_hash(entry_data)

    # Insert entry
    result = collection.insert_one({
        "case_id": case_id,
        "action": action,
        "timestamp": timestamp_iso,
        "previous_hash": previous_hash,
        "current_hash": current_hash,
        "details": details,
        "risk_level": risk_level,
        "user": user,
        "created_at": timestamp_iso,
    })

    return {
        "case_id": case_id,
        "action": action,
        "timestamp": timestamp_iso,
        "previous_hash": previous_hash,
        "current_hash": current_hash,
        "details": details,
        "risk_level": risk_level,
        "user": user,
        "id": str(result.inserted_id),
    }
