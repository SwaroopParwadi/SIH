"""
Risk fusion engine and evidence system.

Combines independent signals:
- image quality
- OCR/MRZ consistency
- barcode consistency
- MRZ validation
- AI forensic score
- face verification
- liveness
- rule validation

The system MUST NOT use the AI model alone to decide whether a document is
fake. High-risk/suspicious results recommend human officer review and do not
claim definitive authentication.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    LOW = "low"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high"


class ModuleStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    NOT_AVAILABLE = "not_available"
    FAILED = "failed"


@dataclass
class RiskConfig:
    weights: Mapping[str, float] = field(default_factory=lambda: {
        "forensic_score": 0.30,
        "ocr_mrz_consistency": 0.20,
        "barcode_consistency": 0.15,
        "mrz_validation": 0.15,
        "face_verification": 0.15,
        "image_quality": 0.05,
    })

    low_max: int = 30
    suspicious_max: int = 65

    def normalize_weights(self) -> Mapping[str, float]:
        total = sum(self.weights.values())
        if total == 0:
            return dict(self.weights)
        return {k: v / total for k, v in self.weights.items()}


@dataclass
class SignalInput:
    image_quality_score: Optional[float] = None
    ocr_score: Optional[float] = None
    mrz_score: Optional[float] = None
    barcode_score: Optional[float] = None
    forensic_score: Optional[float] = None
    face_score: Optional[float] = None
    liveness_score: Optional[float] = None
    rule_score: Optional[float] = None

    face_available: bool = False
    liveness_available: bool = False

    ocr_mrz_consistency_score: Optional[float] = None
    barcode_consistency_score: Optional[float] = None

    pre_evidence: list[dict] = field(default_factory=list)


@dataclass
class RiskResult:
    case_id: Optional[str]
    risk_score: float
    risk_level: RiskLevel
    individual_scores: Mapping[str, Optional[float]]
    evidence: list[dict]
    human_review_required: bool
    review_recommendation: Optional[str]
    disclaimer: str = (
        "This screening uses multiple independent signals. "
        "It does NOT provide definitive proof of authenticity or forgery. "
        "High-risk and suspicious results should be reviewed by a human officer."
    )


def _clamp(v: Optional[float], lo: float = 0.0, hi: float = 100.0) -> float:
    if v is None:
        return lo
    return max(lo, min(hi, float(v)))


def _normalized_module_score(raw: Optional[float], available: bool = True) -> float:
    if not available:
        return 0.0
    if raw is None:
        return 0.0
    return _clamp(raw)


def build_evidence_from_signals(signals: SignalInput, risk_config: RiskConfig) -> list[dict]:
    evidence: list[dict] = []

    def add(type_: str, severity: str, message: str, confidence: float, source: str):
        evidence.append({
            "type": type_,
            "severity": severity,
            "message": message,
            "confidence": round(max(0.0, min(1.0, confidence)), 3),
            "source": source,
        })

    iq = _clamp(signals.image_quality_score)
    if signals.image_quality_score is not None and iq < 70:
        add("IMAGE_QUALITY", "HIGH" if iq < 40 else "MEDIUM",
            f"Image quality score is {iq:.1f}/100",
            confidence=1.0 - (iq / 100.0), source="Image Quality Analyzer")
    elif signals.image_quality_score is not None and iq < 85:
        add("IMAGE_QUALITY", "LOW",
            f"Image quality score is {iq:.1f}/100 - acceptable but not ideal",
            confidence=1.0 - (iq / 100.0), source="Image Quality Analyzer")

    ocr_mrz = _clamp(signals.ocr_mrz_consistency_score)
    if signals.ocr_mrz_consistency_score is not None:
        if ocr_mrz < 50:
            add("OCR_MRZ_INCONSISTENCY", "HIGH",
                f"OCR and MRZ data are inconsistent (consistency score {ocr_mrz:.1f}/100)",
                confidence=1.0 - (ocr_mrz / 100.0), source="Cross-Match Engine")
        elif ocr_mrz < 80:
            add("OCR_MRZ_INCONSISTENCY", "MEDIUM",
                f"OCR and MRZ data show partial inconsistency (consistency score {ocr_mrz:.1f}/100)",
                confidence=1.0 - (ocr_mrz / 100.0), source="Cross-Match Engine")
        else:
            add("OCR_MRZ_MATCH", "LOW",
                f"OCR and MRZ data are consistent (consistency score {ocr_mrz:.1f}/100)",
                confidence=ocr_mrz / 100.0, source="Cross-Match Engine")

    bc = _clamp(signals.barcode_consistency_score)
    if signals.barcode_consistency_score is not None:
        if bc < 50:
            add("BARCODE_INCONSISTENCY", "HIGH",
                f"Barcode data is inconsistent with OCR/MRZ (consistency score {bc:.1f}/100)",
                confidence=1.0 - (bc / 100.0), source="Barcode Verifier")
        elif bc < 80:
            add("BARCODE_INCONSISTENCY", "MEDIUM",
                f"Barcode data shows partial inconsistency (consistency score {bc:.1f}/100)",
                confidence=1.0 - (bc / 100.0), source="Barcode Verifier")
        else:
            add("BARCODE_MATCH", "LOW",
                f"Barcode data is consistent with OCR/MRZ (consistency score {bc:.1f}/100)",
                confidence=bc / 100.0, source="Barcode Verifier")

    mrz = _clamp(signals.mrz_score)
    if signals.mrz_score is not None:
        if mrz < 50:
            add("MRZ_VALIDATION", "HIGH",
                f"MRZ validation failed or check-digit validation failed (score {mrz:.1f}/100)",
                confidence=1.0 - (mrz / 100.0), source="MRZ Parser")
        elif mrz < 80:
            add("MRZ_VALIDATION", "MEDIUM",
                f"MRZ validation partial (score {mrz:.1f}/100)",
                confidence=1.0 - (mrz / 100.0), source="MRZ Parser")
        else:
            add("MRZ_VALIDATION", "LOW",
                f"MRZ validation passed (score {mrz:.1f}/100)",
                confidence=mrz / 100.0, source="MRZ Parser")

    f_score = _clamp(signals.forensic_score)
    if signals.forensic_score is not None:
        if f_score < 50:
            add("FORENSIC_ANOMALY", "HIGH" if f_score < 30 else "MEDIUM",
                f"AI forensic analysis detected anomalies (score {f_score:.1f}/100)",
                confidence=1.0 - (f_score / 100.0), source="Forensic AI")
        elif f_score < 80:
            add("FORENSIC_ANOMALY", "LOW",
                f"AI forensic analysis shows minor concerns (score {f_score:.1f}/100)",
                confidence=1.0 - (f_score / 100.0), source="Forensic AI")
        else:
            add("FORENSIC_CLEAR", "LOW",
                f"AI forensic analysis returned no significant anomalies (score {f_score:.1f}/100)",
                confidence=f_score / 100.0, source="Forensic AI")

    if signals.face_available:
        face = _clamp(signals.face_score)
        if signals.face_score is not None:
            if face < 50:
                add("FACE_VERIFICATION", "HIGH",
                    f"Face verification failed (score {face:.1f}/100)",
                    confidence=1.0 - (face / 100.0), source="Face Verifier")
            elif face < 80:
                add("FACE_VERIFICATION", "MEDIUM",
                    f"Face verification partial (score {face:.1f}/100)",
                    confidence=1.0 - (face / 100.0), source="Face Verifier")
            else:
                add("FACE_VERIFICATION", "LOW",
                    f"Face verification passed (score {face:.1f}/100)",
                    confidence=face / 100.0, source="Face Verifier")
    else:
        add("FACE_VERIFICATION", "LOW",
            "Face verification was not performed (module not available)",
            confidence=0.0, source="Face Verifier")

    if signals.liveness_available:
        liv = _clamp(signals.liveness_score)
        if signals.liveness_score is not None:
            if liv < 50:
                add("LIVENESS", "HIGH",
                    f"Liveness detection failed (score {liv:.1f}/100)",
                    confidence=1.0 - (liv / 100.0), source="Liveness Detector")
            elif liv < 80:
                add("LIVENESS", "MEDIUM",
                    f"Liveness detection partial (score {liv:.1f}/100)",
                    confidence=1.0 - (liv / 100.0), source="Liveness Detector")
            else:
                add("LIVENESS", "LOW",
                    f"Liveness detection passed (score {liv:.1f}/100)",
                    confidence=liv / 100.0, source="Liveness Detector")
    else:
        add("LIVENESS", "LOW",
            "Liveness detection was not performed (module not available)",
            confidence=0.0, source="Liveness Detector")

    rule = _clamp(signals.rule_score)
    if signals.rule_score is not None:
        if rule < 50:
            add("RULE_VIOLATION", "HIGH",
                f"Rule validation failed (score {rule:.1f}/100)",
                confidence=1.0 - (rule / 100.0), source="Rule Engine")
        elif rule < 80:
            add("RULE_VIOLATION", "MEDIUM",
                f"Rule validation partial (score {rule:.1f}/100)",
                confidence=1.0 - (rule / 100.0), source="Rule Engine")
        else:
            add("RULE_CLEAR", "LOW",
                f"Rule validation passed (score {rule:.1f}/100)",
                confidence=rule / 100.0, source="Rule Engine")

    for e in signals.pre_evidence:
        if e not in evidence:
            evidence.append(e)

    return evidence


def fuse_risk(signals: SignalInput, case_id: Optional[str], config: Optional[RiskConfig] = None) -> RiskResult:
    config = config or RiskConfig()
    weights = config.normalize_weights()

    individual_scores = {
        "image_quality_score": signals.image_quality_score,
        "ocr_score": signals.ocr_score,
        "mrz_score": signals.mrz_score,
        "barcode_score": signals.barcode_score,
        "forensic_score": signals.forensic_score,
        "face_score": signals.face_score if signals.face_available else None,
        "liveness_score": signals.liveness_score if signals.liveness_available else None,
        "rule_score": signals.rule_score,
        "ocr_mrz_consistency_score": signals.ocr_mrz_consistency_score,
        "barcode_consistency_score": signals.barcode_consistency_score,
    }

    def contrib(key: str, available: bool = True) -> float:
        raw = None
        if key == "forensic_score":
            raw = signals.forensic_score
        elif key == "ocr_mrz_consistency":
            raw = signals.ocr_mrz_consistency_score
        elif key == "barcode_consistency":
            raw = signals.barcode_consistency_score
        elif key == "mrz_validation":
            raw = signals.mrz_score
        elif key == "face_verification":
            raw = signals.face_score
        elif key == "image_quality":
            raw = signals.image_quality_score
        else:
            raw = None
        return weights.get(key, 0.0) * _normalized_module_score(raw, available=available)

    weighted_good = 0.0
    weighted_possible = 0.0

    weighted_good += contrib("forensic_score")
    weighted_possible += weights.get("forensic_score", 0.0)

    weighted_good += contrib("ocr_mrz_consistency")
    weighted_possible += weights.get("ocr_mrz_consistency", 0.0)

    weighted_good += contrib("barcode_consistency")
    weighted_possible += weights.get("barcode_consistency", 0.0)

    weighted_good += contrib("mrz_validation")
    weighted_possible += weights.get("mrz_validation", 0.0)

    face_weight = weights.get("face_verification", 0.0)
    if signals.face_available:
        weighted_good += contrib("face_verification")
        weighted_possible += face_weight

    liv_weight = weights.get("liveness", 0.0)
    if signals.liveness_available:
        weighted_good += contrib("liveness")
        weighted_possible += liv_weight

    weighted_good += contrib("image_quality")
    weighted_possible += weights.get("image_quality", 0.0)

    if weighted_possible > 0:
        good_ratio = weighted_good / weighted_possible
    else:
        good_ratio = 0.5

    risk_score = (1.0 - good_ratio) * 100.0
    risk_score = _clamp(risk_score, 0.0, 100.0)

    if risk_score <= config.low_max:
        level = RiskLevel.LOW
    elif risk_score <= config.suspicious_max:
        level = RiskLevel.SUSPICIOUS
    else:
        level = RiskLevel.HIGH_RISK

    evidence = build_evidence_from_signals(signals, config)

    human_review_required = level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)
    recommendation = None
    if human_review_required:
        recommendation = (
            "HUMAN OFFICER REVIEW REQUIRED. "
            "This result is based on multiple signals and does NOT constitute "
            "definitive authentication. Review all evidence before making an "
            "admissibility or verification decision."
        )
    else:
        recommendation = (
            "No immediate human review required based on automated signals. "
            "This is NOT a definitive authenticity determination."
        )

    return RiskResult(
        case_id=case_id,
        risk_score=round(risk_score, 2),
        risk_level=level,
        individual_scores=individual_scores,
        evidence=evidence,
        human_review_required=human_review_required,
        review_recommendation=recommendation,
    )
