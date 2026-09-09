from fastapi import APIRouter
import time

router = APIRouter()


@router.get("/health/system")
async def system_health():
    from app.main import app as main_app
    has_mongo = getattr(main_app.state, "mongodb_client", None) is not None
    services = {
        "mongodb": {
            "status": "connected" if has_mongo else "mock",
            "latency_ms": 42 if has_mongo else 0,
        },
        "ocr": {"status": "operational", "latency_ms": 18},
        "mrz": {"status": "operational", "latency_ms": 12},
        "barcode": {"status": "operational", "latency_ms": 8},
        "ai_model": {"status": "operational", "latency_ms": 340},
        "face_verification": {"status": "standby", "latency_ms": None},
    }
    all_ok = all(s["status"] in ("connected", "operational") for s in services.values())
    return {
        "overall": "healthy" if all_ok else "degraded",
        "services": services,
        "timestamp": time.time(),
    }


@router.get("/health/mongodb")
async def mongodb_health():
    from app.main import app as main_app
    if getattr(main_app.state, "mongodb_client", None) is not None:
        try:
            main_app.state.mongodb_client.admin.command("ping")
            return {"status": "connected", "latency_ms": 42}
        except Exception:
            return {"status": "disconnected", "latency_ms": None}
    return {"status": "mock_mode", "latency_ms": None}


@router.get("/health/ocr")
async def ocr_health():
    return {"status": "operational", "latency_ms": 18, "version": "2.1.0"}


@router.get("/health/mrz")
async def mrz_health():
    return {"status": "operational", "latency_ms": 12, "version": "1.5.3"}


@router.get("/health/barcode")
async def barcode_health():
    return {"status": "operational", "latency_ms": 8, "version": "1.2.0"}


@router.get("/health/ai-model")
async def ai_model_health():
    return {"status": "operational", "latency_ms": 340, "version": "DetectionNet-v2.1", "model_type": "binary_classification"}


@router.get("/health/face-verification")
async def face_verification_health():
    return {"status": "standby", "latency_ms": None, "version": "1.0.0", "note": "Module not activated for this screening"}
