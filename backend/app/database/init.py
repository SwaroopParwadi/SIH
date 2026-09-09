"""
MongoDB Atlas collection initialization for SecureDoc AI.

Creates and indexes the following collections:
- cases
- extracted_data
- verification_results
- evidence
- audit_logs
- system_events
"""
import pymongo
from pymongo import MongoClient
from datetime import datetime


def init_collections(mongodb_uri: str, database_name: str = "securedoc") -> dict:
    """
    Initialize all required MongoDB Atlas collections and indexes.
    Returns a dict with status for each collection.
    """
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    db = client[database_name]

    results = {}

    # ── Cases ──────────────────────────────────────────────────────────────
    cases = db.cases
    cases.create_index("case_id", unique=True)
    cases.create_index("status")
    cases.create_index("risk_level")
    cases.create_index("created_at")
    cases.create_index([("case_id", 1), ("status", 1)])
    results["cases"] = {
        "status": "created",
        "indexes": ["case_id (unique)", "status", "risk_level", "created_at", "case_id + status"],
    }

    # ── Extracted Data ─────────────────────────────────────────────────────
    extracted = db.extracted_data
    extracted.create_index("case_id", unique=True)
    extracted.create_index("nationality")
    extracted.create_index("document_number")
    results["extracted_data"] = {
        "status": "created",
        "indexes": ["case_id (unique)", "nationality", "document_number"],
    }

    # ── Verification Results ───────────────────────────────────────────────
    verification = db.verification_results
    verification.create_index("case_id", unique=True)
    verification.create_index([("forensic_score", 1), ("risk_level", 1)])
    results["verification_results"] = {
        "status": "created",
        "indexes": ["case_id (unique)", "forensic_score + risk_level"],
    }

    # ── Evidence ───────────────────────────────────────────────────────────
    evidence = db.evidence
    evidence.create_index([("case_id", 1), ("type", 1)])
    evidence.create_index("severity")
    evidence.create_index("created_at")
    results["evidence"] = {
        "status": "created",
        "indexes": ["case_id + type", "severity", "created_at"],
    }

    # ── Audit Logs (SHA-256 hash chain) ───────────────────────────────────
    audit = db.audit_logs
    audit.create_index("case_id")
    audit.create_index("timestamp")
    audit.create_index([("case_id", 1), ("timestamp", -1)])
    audit.create_index("previous_hash")
    results["audit_logs"] = {
        "status": "created",
        "indexes": ["case_id", "timestamp", "case_id + timestamp", "previous_hash"],
    }

    # ── System Events ──────────────────────────────────────────────────────
    events = db.system_events
    events.create_index("timestamp")
    events.create_index("event_type")
    events.create_index([("event_type", 1), ("timestamp", -1)])
    results["system_events"] = {
        "status": "created",
        "indexes": ["timestamp", "event_type", "event_type + timestamp"],
    }

    # ── Documents Metadata (local file references only) ────────────────────
    docs_meta = db.documents_metadata
    docs_meta.create_index("case_id")
    docs_meta.create_index("file_id", unique=True)
    results["documents_metadata"] = {
        "status": "created",
        "indexes": ["case_id", "file_id (unique)"],
    }

    # Insert a system events document recording DB init
    events.insert_one({
        "event_type": "system_init",
        "message": "SecureDoc AI database initialized",
        "collections_created": list(results.keys()),
        "timestamp": datetime.now(tz=None).isoformat(),
        "status": "success",
    })

    client.close()
    return results


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DATABASE", "securedoc")

    if not uri:
        print("ERROR: MONGODB_URI not set in environment")
        exit(1)

    print(f"Initializing collections in database '{db_name}'...")
    result = init_collections(uri, db_name)

    print("\n=== Collections Created ===")
    for coll, info in result.items():
        print(f"\n{coll}:")
        print(f"  Status: {info['status']}")
        print(f"  Indexes: {', '.join(info['indexes'])}")

    print("\nAll collections initialized successfully")
