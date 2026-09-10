"""
Document intelligence scoring layer.

Converts raw OCR/MRZ/barcode/quality signals into the score keys expected by
the screening pipeline without inventing fake detection.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IntelligencePayload:
    image_quality: Optional[Mapping] = None
    ocr: Optional[Mapping] = None
    mrz: Optional[Mapping] = None
    cross_match: Optional[Mapping] = None
    barcode: Optional[Mapping] = None


def to_screening_scores(payload: IntelligencePayload) -> Mapping[str, float]:
    """Produce numerical scores compatible with the existing screening view.

    These are quality/extractability signals - they do NOT represent fake/
    genuine classification. That belongs to the forensic/rule layer.
    """
    def _pick(obj: Optional[Mapping], key: str, default: float) -> float:
        if not obj:
            return default
        v = obj.get(key)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, Mapping):
            return float(v.get(key, default))
        return default

    quality = payload.image_quality
    ocr = payload.ocr
    mrz = payload.mrz
    cross = payload.cross_match
    barcode = payload.barcode

    scores: dict[str, float] = {}

    # image_quality_score: directly from quality report
    scores["image_quality_score"] = _pick(quality, "quality_score", 100.0)

    # ocr_score: confidence * 100, but never above 95 for partials
    ocr_conf = _pick(ocr, "confidence", 0.0) * 100.0
    ocr_status = _pick(ocr, "status", "failed")
    if ocr_status == "partial":
        ocr_conf = min(ocr_conf, 75.0)
    elif ocr_status == "failed":
        ocr_conf = 0.0
    scores["ocr_score"] = ocr_conf

    # mrz_score: based on status + check digit status
    mrz_status = _pick(mrz, "status", "not_found")
    cd_status = _pick(mrz, "check_digit_statuses", {})
    cd_valid = sum(1 for v in cd_status.values() if v == "valid")
    cd_total = max(1, len(cd_status))
    cd_ratio = cd_valid / cd_total if cd_status else 0.0
    if mrz_status == "ok":
        mrz_base = 85.0
    elif mrz_status == "partial":
        mrz_base = 55.0
    else:
        mrz_base = 0.0
    scores["mrz_score"] = mrz_base + cd_ratio * 15.0

    # barcode_score: based on barcode findings
    bc_status = _pick(barcode, "status", "not_found")
    bc_matched = _pick(barcode, "matched_count", 0)
    bc_total = _pick(barcode, "codes_found", 0)
    if bc_status == "found":
        base = 70.0
        if bc_total > 0:
            base += (bc_matched / bc_total) * 20.0
        scores["barcode_score"] = base
    elif bc_status == "decode_error":
        scores["barcode_score"] = 50.0
    else:
        # not found: soft penalty only if document data exists
        doc_data_present = bool(
            _pick(ocr, "name", None) or _pick(ocr, "document_number", None) or
            _pick(mrz, "document_number", None) or _pick(mrz, "country", None)
        )
        scores["barcode_score"] = 60.0 if not doc_data_present else 75.0

    # forensic + face + liveness + rule: leave as placeholders (0.0) until
    # the respective modules are implemented. They are not document-intelligence.
    scores["forensic_score"] = 0.0
    scores["face_score"] = 0.0
    scores["liveness_score"] = 0.0
    scores["rule_score"] = 0.0

    return scores
