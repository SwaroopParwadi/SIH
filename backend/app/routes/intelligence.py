"""
POST /api/intelligence/analyze
POST /api/intelligence/pipeline/{case_id}

Document intelligence pipeline:
  Upload -> Quality -> OCR -> MRZ -> Barcode -> Consistency -> AI -> Risk -> Evidence
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException

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
from app.services.vision_quality import ImageQualityReport, analyze_image


router = APIRouter()


@dataclass
class PipelineResponse:
    case_id: Optional[str]
    file_path: Optional[str]
    image_quality: Optional[dict]
    ocr: Optional[dict]
    mrz: Optional[dict]
    cross_match: Optional[dict]
    barcode: Optional[dict]
    scores: dict
    risk: dict
    processed_at: str


def _default_model_path() -> Optional[str]:
    from pathlib import Path
    candidate = Path(__file__).resolve().parent.parent.parent / "models" / "best_model.pth"
    if candidate.is_file():
        return str(candidate)
    return None


def run_full_pipeline(file_path: str, case_id: Optional[str] = None):
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path is required")

    now = datetime.now(timezone.utc).isoformat()

    try:
        quality = analyze_image(file_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Image quality analysis failed: {exc}")

    ocr: OcrExtractedData
    try:
        ocr = extract_from_image(file_path)
    except Exception as exc:
        ocr = OcrExtractedData(status="failed", error=str(exc))

    mrz: MrzResult
    try:
        mrz = detect_and_extract_mrz(file_path)
    except Exception as exc:
        mrz = MrzResult(status="not_found", error=str(exc))

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
        face_score=None,
        liveness_score=None,
        rule_score=rule_score,
        face_available=False,
        liveness_available=False,
        ocr_mrz_consistency_score=ocr_mrz_consistency_score,
        barcode_consistency_score=barcode_consistency_score,
        pre_evidence=rule_evidence,
    )

    risk = fuse_risk(signals, case_id=case_id, config=RiskConfig())

    payload = IntelligencePayload(
        image_quality={
            "quality_score": quality.quality_score,
            "resolution": quality.resolution,
            "blur": quality.blur,
            "brightness": quality.brightness,
            "contrast": quality.contrast,
            "flags": quality.flags,
        },
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

    model_info = {
        "status": ai_result.get("status"),
        "label": ai_result.get("label"),
        "authentic_probability": ai_result.get("authentic_probability"),
        "manipulated_probability": ai_result.get("manipulated_probability"),
        "model_path": ai_result.get("model_path"),
        "device": ai_result.get("device"),
    }

    return PipelineResponse(
        case_id=case_id,
        file_path=file_path,
        image_quality=payload.image_quality,
        ocr=payload.ocr,
        mrz=payload.mrz,
        cross_match=payload.cross_match,
        barcode=payload.barcode,
        scores=scores,
        risk={
            "case_id": risk.case_id,
            "risk_score": risk.risk_score,
            "risk_level": risk.risk_level.value,
            "individual_scores": risk.individual_scores,
            "evidence": risk.evidence,
            "human_review_required": risk.human_review_required,
            "review_recommendation": risk.review_recommendation,
            "disclaimer": risk.disclaimer,
            "model_info": model_info,
        },
        processed_at=now,
    )


@router.post("/analyze", response_model=PipelineResponse, status_code=201)
async def analyze_document(request: dict):
    if not request.get("file_path"):
        raise HTTPException(status_code=400, detail="file_path is required")
    return run_full_pipeline(request["file_path"], request.get("case_id"))


@router.post("/pipeline/{case_id}", response_model=PipelineResponse, status_code=201)
async def pipeline_for_case(case_id: str, request: dict):
    if not request.get("file_path"):
        raise HTTPException(status_code=400, detail="file_path is required")
    return run_full_pipeline(request["file_path"], case_id=case_id)
