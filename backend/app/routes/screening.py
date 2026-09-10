"""
POST /api/screen
POST /api/screen/{case_id}/process
GET /api/screen/{case_id}/result

Screening pipeline:
  Upload -> Quality -> OCR -> MRZ -> Barcode -> Consistency -> AI -> Rules -> Risk -> Evidence -> MongoDB -> Audit
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pymongo

from app.services.barcode_service import (
    BarcodeComparisonResult,
    scan_barcodes,
    compare_barcode_vs_ocr_mrz,
)
from app.services.cross_match_service import (
    CrossMatchResult,
    compare_ocr_vs_mrz,
)
from app.services.mrz_service import MrzResult, detect_and_extract_mrz
from app.services.ocr_service import OcrExtractedData, extract_from_image
from app.services.risk_engine import RiskConfig, SignalInput, fuse_risk
from app.services.service_scoring import IntelligencePayload, to_screening_scores
from app.services.vision_quality import analyze_image
from app.services.biometrics import (
    FaceVerificationResult,
    LivenessResult,
    verify_faces,
    run_liveness_prototype,
    capture_live_face_image,
)
from app.services.audit import append_screening_audit



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
        return 100000 + int(datetime.now().timestamp()) % 900000


def generate_case_id() -> str:
    num = get_next_case_number()
    return f"SD-2026-{num:06d}"


def get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


class ScreeningRequest(BaseModel):
    subject_name: str
    document_type: str
    country_code: str
    notes: Optional[str] = None
    file_path: Optional[str] = None


def _default_model_path() -> Optional[str]:
    from pathlib import Path
    candidate = Path(__file__).resolve().parent.parent.parent / "models" / "best_model.pth"
    if candidate.is_file():
        return str(candidate)
    return None


def run_screening_pipeline(file_path: str, case_id: str, db, now: str):
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path is required")

    # 1. Quality
    try:
        quality = analyze_image(file_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Image quality analysis failed: {exc}")

    # 2. OCR
    ocr: OcrExtractedData
    try:
        ocr = extract_from_image(file_path)
    except Exception as exc:
        ocr = OcrExtractedData(status="failed", error=str(exc))

    # 3. MRZ
    mrz: MrzResult
    try:
        mrz = detect_and_extract_mrz(file_path)
    except Exception as exc:
        mrz = MrzResult(status="not_found", error=str(exc))

    # 4. Cross-match OCR vs MRZ
    cross: CrossMatchResult
    try:
        cross = compare_ocr_vs_mrz(
            ocr_name=ocr.name,
            ocr_dob=ocr.date_of_birth,
            ocr_docnum=ocr.document_number,
            ocr_nationality=ocr.nationality,
            ocr_sex=ocr.sex,
            ocr_expiry=ocr.expiry_date,
            mrz_name=mrz.name,
            mrz_dob=mrz.date_of_birth,
            mrz_docnum=mrz.document_number,
            mrz_nationality=mrz.nationality,
            mrz_sex=mrz.sex,
            mrz_expiry=mrz.expiry_date,
        )
    except Exception as exc:
        cross = CrossMatchResult(overall="NOT_AVAILABLE", details={}, error=str(exc))

    # 5. Barcode
    barcode_scan = scan_barcodes(file_path)
    barcode_comp: BarcodeComparisonResult
    try:
        barcode_comp = compare_barcode_vs_ocr_mrz(
            barcodes=barcode_scan.codes,
            ocr_name=ocr.name,
            ocr_dob=ocr.date_of_birth,
            ocr_docnum=ocr.document_number,
            ocr_nationality=ocr.nationality,
            ocr_sex=ocr.sex,
            ocr_expiry=ocr.expiry_date,
            mrz_name=mrz.name,
            mrz_dob=mrz.date_of_birth,
            mrz_docnum=mrz.document_number,
            mrz_nationality=mrz.nationality,
            mrz_sex=mrz.sex,
            mrz_expiry=mrz.expiry_date,
        )
    except Exception as exc:
        barcode_comp = BarcodeComparisonResult(codes_found=0, error=str(exc))

    # 6. AI forensic model
    from app.services.model_intelligence import ModelIntelligence
    model_path = _default_model_path()
    ai = ModelIntelligence(model_path=model_path)
    ai_result = ai.predict(file_path)

    forensic_score: Optional[float] = None
    if ai_result.get("status") == "OK":
        manipulated_prob = ai_result.get("manipulated_probability", 0.0)
        forensic_score = round(manipulated_prob * 100.0, 2)
    else:
        forensic_score = None

    # 7. Biometrics (optional)
    face_result: FaceVerificationResult
    liveness_result: LivenessResult
    face_score_from_biometrics: Optional[float] = None
    liveness_score_from_biometrics: Optional[float] = None
    face_available = False
    liveness_available = False

    live_face_path = None
    try:
        live_face_path = capture_live_face_image(0, None)
    except Exception:
        live_face_path = None

    face_result = FaceVerificationResult(status="not_available", error="Biometrics module unavailable" if not BIOMETICS_AVAILABLE else None)
    liveness_result = LivenessResult(status="not_available", error="Biometrics module unavailable" if not BIOMETICS_AVAILABLE else None)

    if live_face_path and isinstance(live_face_path, str) and live_face_path.startswith("data:"):
        import base64
        b64_data = live_face_path.split(",", 1)[-1]
        live_face_bytes = base64.b64decode(b64_data)
        live_face_file = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", f"live_{case_id}.jpg")
        os.makedirs(os.path.dirname(live_face_file), exist_ok=True)
        with open(live_face_file, "wb") as f:
            f.write(live_face_bytes)
        live_face_path = live_face_file

    if live_face_path and os.path.exists(live_face_path):
        face_result = verify_faces(file_path, live_face_path)
        liveness_result = run_liveness_prototype(0, 8.0)
        face_available = face_result.status != "not_available"
        liveness_available = liveness_result.status != "not_available"
        if face_result.similarity_score is not None:
            face_score_from_biometrics = face_result.similarity_score
        if liveness_result.liveness_score is not None:
            liveness_score_from_biometrics = liveness_result.liveness_score
    else:
        face_result = FaceVerificationResult(status="not_available")
        liveness_result = LivenessResult(status="not_available")

    # 8. Rules
    rule_score = 100.0
    rule_evidence = []
    if mrz.status.value == "not_found":
        rule_score -= 15.0
        rule_evidence.append({
            "type": "RULE",
            "severity": "MEDIUM",
            "message": "No MRZ detected - rule-based concern",
            "confidence": 0.6,
            "source": "Rule Engine",
        })
    if not ocr.name and not mrz.name:
        rule_score -= 10.0
        rule_evidence.append({
            "type": "RULE",
            "severity": "MEDIUM",
            "message": "No name extracted from either VIZ or MRZ",
            "confidence": 0.5,
            "source": "Rule Engine",
        })
    rule_score = max(0.0, min(100.0, rule_score))

    def _match_to_score(status: str) -> float:
        if status == "MATCH":
            return 100.0
        if status == "MISMATCH":
            return 0.0
        return 50.0

    ocr_mrz_consistency_score = _match_to_score(cross.overall.value)

    barcode_consistency_score = 50.0
    if barcode_comp.codes_found > 0:
        matched = barcode_comp.matched_with_ocr + barcode_comp.matched_with_mrz
        total_possible = max(1, barcode_comp.codes_found * 6)
        barcode_consistency_score = round((matched / total_possible) * 100.0, 2)

    signals = SignalInput(
        image_quality_score=quality.quality_score,
        ocr_score=(ocr.confidence * 100.0) if ocr.confidence is not None else None,
        mrz_score=({"ok": 100.0, "partial": 60.0, "not_found": 0.0}.get(mrz.status.value, 0.0)),
        barcode_score=({"found": 100.0, "not_found": 50.0, "decode_error": 40.0}.get(barcode_scan.status.value, 50.0)),
        forensic_score=forensic_score,
        face_score=face_score_from_biometrics,
        liveness_score=liveness_score_from_biometrics,
        rule_score=rule_score,
        face_available=face_available,
        liveness_available=liveness_available,
        ocr_mrz_consistency_score=ocr_mrz_consistency_score,
        barcode_consistency_score=barcode_consistency_score,
        pre_evidence=rule_evidence,
    )

    risk = fuse_risk(signals, case_id=case_id, config=RiskConfig())

    # Prepare extracted_data fields
    first_name = ""
    surname = ""
    if ocr.name:
        parts = ocr.name.split()
        if len(parts) > 1:
            first_name = " ".join(parts[:-1])
            surname = parts[-1]
        else:
            first_name = parts[0]
    elif mrz.name:
        parts = mrz.name.split()
        if len(parts) > 1:
            first_name = " ".join(parts[:-1])
            surname = parts[-1]
        else:
            first_name = parts[0]

    extracted_doc = {
        "case_id": case_id,
        "name": ocr.name or mrz.name,
        "surname": surname,
        "given_names": first_name,
        "document_number": ocr.document_number or mrz.document_number,
        "nationality": ocr.nationality or mrz.nationality,
        "date_of_birth": ocr.date_of_birth or mrz.date_of_birth,
        "sex": ocr.sex or mrz.sex,
        "issue_date": ocr.issue_date,
        "expiry_date": ocr.expiry_date or mrz.expiry_date,
        "mrz": mrz.raw_mrz,
        "ocr_confidence": ocr.confidence,
        "ocr_status": ocr.status.value,
        "mrz_status": mrz.status.value,
        "ocr_name": ocr.name,
        "mrz_name": mrz.name,
        "ocr_document_number": ocr.document_number,
        "mrz_document_number": mrz.document_number,
        "ocr_nationality": ocr.nationality,
        "mrz_nationality": mrz.nationality,
        "ocr_sex": ocr.sex,
        "mrz_sex": mrz.sex,
        "ocr_date_of_birth": ocr.date_of_birth,
        "mrz_date_of_birth": mrz.date_of_birth,
        "ocr_expiry_date": ocr.expiry_date,
        "mrz_expiry_date": mrz.expiry_date,
        "cross_match_overall": cross.overall.value,
        "cross_match_details": cross.details,
        "barcode_comparison": {
            "codes_found": barcode_comp.codes_found,
            "matched_with_ocr": barcode_comp.matched_with_ocr,
            "matched_with_mrz": barcode_comp.matched_with_mrz,
            "unmatched_codes": barcode_comp.unmatched_codes,
            "missing_barcode_warns": barcode_comp.missing_barcode_warns,
        },
        "model_info": {
            "status": ai_result.get("status"),
            "label": ai_result.get("label"),
            "authentic_probability": ai_result.get("authentic_probability"),
            "manipulated_probability": ai_result.get("manipulated_probability"),
            "model_path": ai_result.get("model_path"),
            "device": ai_result.get("device"),
        },
        "biometrics": {
            "face_verification": {
                "status": face_result.status.value,
                "similarity_score": face_result.similarity_score,
                "match_status": face_result.match_status,
                "confidence": face_result.confidence,
                "error": face_result.error,
            },
            "liveness": {
                "status": liveness_result.status.value,
                "liveness_score": liveness_result.liveness_score,
                "challenge_passed": liveness_result.challenge_passed,
                "notes": liveness_result.notes,
                "prototype": liveness_result.prototype,
                "error": liveness_result.error,
            },
        },
        "image_quality": {
            "quality_score": quality.quality_score,
            "resolution": quality.resolution,
            "blur": quality.blur,
            "brightness": quality.brightness,
            "contrast": quality.contrast,
            "flags": quality.flags,
        },
        "created_at": now,
    }

    # Audit chain update
    audit_entry = append_screening_audit(db, case_id, result)

    payload = IntelligencePayload(
        image_quality=extracted_doc["image_quality"],
        ocr={
            "name": ocr.name,
            "document_number": ocr.document_number,
            "date_of_birth": ocr.date_of_birth,
            "nationality": ocr.nationality,
            "sex": ocr.sex,
            "issue_date": ocr.issue_date,
            "expiry_date": ocr.expiry_date,
            "confidence": ocr.confidence,
            "status": ocr.status.value,
        },
        mrz={
            "status": mrz.status.value,
            "document_type": mrz.document_type,
            "country": mrz.country,
            "document_number": mrz.document_number,
            "nationality": mrz.nationality,
            "date_of_birth": mrz.date_of_birth,
            "sex": mrz.sex,
            "expiry_date": mrz.expiry_date,
            "name": mrz.name,
            "check_digit_statuses": {k: v.value for k, v in mrz.check_digit_statuses.items()},
            "raw_mrz": mrz.raw_mrz,
        },
        cross_match={
            "overall": cross.overall.value,
            "name": cross.name.value,
            "date_of_birth": cross.date_of_birth.value,
            "document_number": cross.document_number.value,
            "nationality": cross.nationality.value,
            "sex": cross.sex.value,
            "expiry_date": cross.expiry_date.value,
            "details": cross.details,
        },
        barcode={
            "status": barcode_scan.status.value,
            "codes": [{"type": c.type, "data": c.data} for c in barcode_scan.codes],
            "comparison": {
                "codes_found": barcode_comp.codes_found,
                "matched_with_ocr": barcode_comp.matched_with_ocr,
                "matched_with_mrz": barcode_comp.matched_with_mrz,
                "unmatched_codes": barcode_comp.unmatched_codes,
                "missing_barcode_warns": barcode_comp.missing_barcode_warns,
            },
        },
    )

    scores = to_screening_scores(payload)

    # Store extracted data
    db.extracted_data.update_one(
        {"case_id": case_id},
        {"$set": extracted_doc},
        upsert=True,
    )

    # Store verification results (includes scores + risk)
    verification_doc = {
        "case_id": case_id,
        **scores,
        "risk_score": risk.risk_score,
        "risk_level": risk.risk_level.value,
        "overall_verdict": (
            "Low Risk" if risk.risk_level == "low"
            else "Suspicious" if risk.risk_level == "suspicious"
            else "High Risk"
        ),
        "model_status": ai_result.get("status"),
        "model_label": ai_result.get("label"),
        "model_authentic_probability": ai_result.get("authentic_probability"),
        "model_manipulated_probability": ai_result.get("manipulated_probability"),
        "face_verification_status": face_result.status.value,
        "face_similarity_score": face_result.similarity_score,
        "face_match_status": face_result.match_status,
        "face_confidence": face_result.confidence,
        "face_error": face_result.error,
        "liveness_status": liveness_result.status.value,
        "liveness_score": liveness_result.liveness_score,
        "liveness_challenge_passed": liveness_result.challenge_passed,
        "liveness_notes": liveness_result.notes,
        "liveness_prototype": liveness_result.prototype,
        "human_review_required": risk.human_review_required,
        "review_recommendation": risk.review_recommendation,
        "disclaimer": risk.disclaimer,
        "created_at": now,
    }
    db.verification_results.update_one(
        {"case_id": case_id},
        {"$set": verification_doc},
        upsert=True,
    )

    # Store evidence
    for item in risk.evidence:
        item["case_id"] = case_id
        item["created_at"] = now
        item["source"] = item.get("source", "Risk Engine")
        db.evidence.insert_one(item)

    return {
        "case_id": case_id,
        "risk_score": risk.risk_score,
        "risk_level": risk.risk_level.value,
        "status": (
            "Verified" if risk.risk_level == "low"
            else "Flagged" if risk.risk_level == "high"
            else "Under Review"
        ),
        "human_review_required": risk.human_review_required,
        "review_recommendation": risk.review_recommendation,
        "disclaimer": risk.disclaimer,
        "individual_scores": risk.individual_scores,
        "evidence_count": len(risk.evidence),
        "evidence": risk.evidence,
        "model_info": verification_doc["model_status"],
        "processed_at": now,
    }


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
async def process_screening(case_id: str, request: Optional[ScreeningRequest] = None):
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    cases_collection = db.cases
    case = cases_collection.find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    file_path = None
    if request and request.file_path:
        file_path = request.file_path
    elif case.get("document_file_path"):
        file_path = case["document_file_path"]

    if not file_path:
        raise HTTPException(status_code=400, detail="No document file_path available for this case. Upload a document first or provide file_path in the request.")

    result = run_screening_pipeline(file_path, case_id, db, now)

    cases_collection.update_one(
        {"case_id": case_id},
        {
            "$set": {
                "risk_score": result["risk_score"],
                "risk_level": result["risk_level"],
                "status": result["status"],
                "updated_at": now,
                "screening_complete": True,
                "processed_at": now,
                "human_review_required": result["human_review_required"],
                "review_recommendation": result["review_recommendation"],
            }
        },
    )

    return {
        "case_id": result["case_id"],
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "status": result["status"],
        "human_review_required": result["human_review_required"],
        "review_recommendation": result["review_recommendation"],
        "disclaimer": result["disclaimer"],
        "individual_scores": result["individual_scores"],
        "evidence_count": result["evidence_count"],
        "evidence": result["evidence"],
        "model_info": result["model_info"],
        "biometrics": result.get("biometrics"),
        "processed_at": result["processed_at"],
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
        "human_review_required": verification.get("human_review_required", False),
        "review_recommendation": verification.get("review_recommendation"),
        "disclaimer": verification.get("disclaimer"),
        "verification_results": {
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
            "ocr_status": extracted.get("ocr_status") if extracted else None,
            "mrz_status": extracted.get("mrz_status") if extracted else None,
            "cross_match_overall": extracted.get("cross_match_overall") if extracted else None,
            "model_info": extracted.get("model_info") if extracted else None,
            "biometrics": extracted.get("biometrics") if extracted else None,
            "image_quality": extracted.get("image_quality") if extracted else None,
        },
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
        "created_at": case.get("created_at"),
    }
