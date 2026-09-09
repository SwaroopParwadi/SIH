"""
GET /api/dashboard/stats
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone, timedelta
from typing import Optional
import pymongo

router = APIRouter()


def get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    days: int = Query(30, ge=1, le=365),
    risk_levels: Optional[str] = None,
):
    """
    Get aggregated dashboard statistics from MongoDB Atlas.

    Returns:
    - total_documents_screened
    - low_risk_count
    - suspicious_count
    - high_risk_count
    - average_risk_score
    - screening_trend (last N days)
    - recent_cases (last 10)
    - system_health (service status)
    """
    db = get_db()
    now = datetime.now(timezone.utc)

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    cutoff = now - timedelta(days=days)
    cases_collection = db.cases

    # Total screened (cases with screening_complete = True)
    total = cases_collection.count_documents({"screening_complete": True})

    # Risk level counts
    low = cases_collection.count_documents({"risk_level": "low", "screening_complete": True})
    suspicious = cases_collection.count_documents({"risk_level": "suspicious", "screening_complete": True})
    high = cases_collection.count_documents({"risk_level": "high", "screening_complete": True})

    # Average risk score
    avg_pipeline = [
        {"$match": {"screening_complete": True, "risk_score": {"$gt": 0}}},
        {"$group": {"_id": None, "avg": {"$avg": "$risk_score"}}},
    ]
    avg_result = list(cases_collection.aggregate(avg_pipeline))
    avg_score = round(avg_result[0]["avg"], 1) if avg_result else 0.0

    # Screening trend (last N days)
    trend_pipeline = [
        {"$match": {"screening_complete": True, "created_at": {"$gte": cutoff.isoformat()}}},
        {            "$project": {
                "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "risk_level": 1,
            }
        },
        {"$group": {"_id": "$day", "low": {"$sum": {"$cond": [{"$eq": ["$risk_level", "low"]}, 1, 0]}}, "suspicious": {"$sum": {"$cond": [{"$eq": ["$risk_level", "suspicious"]}, 1, 0]}}, "high": {"$sum": {"$cond": [{"$eq": ["$risk_level", "high"]}, 1, 0]}}}},
        {"$sort": {"_id": 1}},
    ]
    trend_result = list(cases_collection.aggregate(trend_pipeline))
    screening_trend = [
        {"date": t["_id"], "low": t["low"], "suspicious": t["suspicious"], "high": t["high"]}
        for t in trend_result
    ]

    # Recent cases (last 10)
    recent_cases_pipeline = [
        {"$match": {"screening_complete": True}},
        {"$sort": {"created_at": -1}},
        {"$limit": 10},
        {
            "$project": {
                "_id": 0,
                "case_id": 1,
                "subject_name": 1,
                "document_type": 1,
                "country_code": 1,
                "risk_score": 1,
                "risk_level": 1,
                "status": 1,
                "created_at": 1,
            }
        },
    ]
    recent_cases = list(cases_collection.aggregate(recent_cases_pipeline))

    # System health (mock after real MongoDB connection)
    system_health = {
        "mongodb": {"status": "connected", "latency_ms": 45},
        "ocr": {"status": "operational", "latency_ms": 18},
        "mrz": {"status": "operational", "latency_ms": 12},
        "barcode": {"status": "operational", "latency_ms": 8},
        "ai_model": {"status": "operational", "latency_ms": 340},
        "face_verification": {"status": "standby", "latency_ms": None},
    }

    return {
        "total_documents_screened": total,
        "low_risk_count": low,
        "suspicious_count": suspicious,
        "high_risk_count": high,
        "average_risk_score": avg_score,
        "screening_trend_days": days,
        "screening_trend": screening_trend,
        "recent_cases": [
            {
                "case_id": c.get("case_id"),
                "subject_name": c.get("subject_name", "Unknown"),
                "document_type": c.get("document_type", "Unknown"),
                "country_code": c.get("country_code", "UNK"),
                "risk_score": c.get("risk_score", 0),
                "risk_level": c.get("risk_level", "pending"),
                "status": c.get("status", "Unknown"),
                "screened_at": c.get("created_at"),
            }
            for c in recent_cases
        ],
        "system_health": system_health,
        "generated_at": now.isoformat(),
    }
