"""
PaddleOCR extraction service.

Extracts name, document number, DOB, nationality, sex, issue date, expiry
date from an identity document image where possible.

Returns OCR confidence. If the OCR engine cannot be loaded or fails, returns a
structured error instead of raising an unhandled exception.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import logging

from paddleocr import PaddleOCR

from app.services.vision_quality import analyze_image

log = logging.getLogger(__name__)


class OcrStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class OcrExtractedData:
    name: Optional[str] = None
    document_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    sex: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    confidence: Optional[float] = None
    status: OcrStatus = OcrStatus.FAILED
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Heuristic field extraction from PaddleOCR word lines.
# PaddleOCR returns per-word text; real MRZ/VIZ field positions vary by
# country, so we use the best-effort pattern matching below.
# ---------------------------------------------------------------------------

_DATE_RE = __import__("re").compile(
    r"(\d{2})[-/](\d{2})[-/](\d{4})"
)
_DATE_RE_ALT = __import__("re").compile(
    r"(\d{4})[-/](\d{2})[-/](\d{2})"
)


def _normalize_date(value: str) -> Optional[str]:
    """Normalize common date formats to ISO YYYY-MM-DD."""
    m = _DATE_RE.search(value) or _DATE_RE_ALT.search(value)
    if m is None:
        return None
    y, mo, d = m.group(1), m.group(2), m.group(3)
    # Heuristic: if year < 50 assume 20xx else 19xx when format is YY-MM-DD
    if len(y) == 2:
        y = "20" + y if int(y) < 50 else "19" + y
    return f"{y}-{mo}-{d}"


def _extract_fields(text_lines: list[str]) -> dict[str, Optional[str]]:
    result: dict[str, Optional[str]] = {
        "name": None,
        "document_number": None,
        "date_of_birth": None,
        "nationality": None,
        "sex": None,
        "issue_date": None,
        "expiry_date": None,
    }

    joined = " ".join(text_lines)

    # Name: heuristic - first long alphabetic token sequence before numbers
    name_match = __import__("re").search(
        r"([A-Za-z][A-Za-z \-']{3,})", joined
    )
    if name_match:
        result["name"] = name_match.group(1).strip()

    # Document number: typical patterns like ABC123456, or all-caps short token
    doc_match = __import__("re").search(
        r"\b([A-Z]{1,3}\d{6,9}|[\dA-Z]{8,12})\b", joined
    )
    if doc_match:
        result["document_number"] = doc_match.group(1)

    # Sex
    sex_match = __import__("re").search(r"\b([MF])\b", joined)
    if sex_match:
        result["sex"] = sex_match.group(1)

    # Nationality - look for 3-letter country code uppercase
    nat_match = __import__("re").search(r"\b([A-Z]{3})\b", joined)
    if nat_match:
        result["nationality"] = nat_match.group(1)

    # Dates - pick first two dates; older is likely DOB, later is issue/expiry
    dates: list[tuple[int, str]] = []
    for line in text_lines:
        for m in _DATE_RE.finditer(line) or []:
            raw = m.group(0)
            iso = _normalize_date(raw)
            if iso is None:
                continue
            try:
                dt = datetime.strptime(iso, "%Y-%m-%d")
                dates.append((dt.year, iso))
            except ValueError:
                continue
        for m in _DATE_RE_ALT.finditer(line) or []:
            raw = m.group(0)
            iso = _normalize_date(raw)
            if iso is None:
                continue
            try:
                dt = datetime.strptime(iso, "%Y-%m-%d")
                dates.append((dt.year, iso))
            except ValueError:
                continue

    if dates:
        dates_sorted = sorted(set(dates), key=lambda x: x[0])
        result["date_of_birth"] = dates_sorted[0][1]
        if len(dates_sorted) > 1:
            result["issue_date"] = dates_sorted[1][1]
        if len(dates_sorted) > 2:
            result["expiry_date"] = dates_sorted[-1][1]

    return result


def extract_from_image(file_path: str) -> OcrExtractedData:
    try:
        quality = analyze_image(file_path)
    except Exception as exc:
        return OcrExtractedData(
            status=OcrStatus.FAILED,
            error=f"Quality analysis failed: {exc}",
        )

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="en")
    except Exception as exc:
        return OcrExtractedData(
            status=OcrStatus.FAILED,
            error=f"PaddleOCR initialization failed: {exc}",
        )

    try:
        result = ocr.ocr(file_path, cls=True)
    except Exception as exc:
        return OcrExtractedData(
            status=OcrStatus.FAILED,
            error=f"OCR inference failed: {exc}",
        )

    if not result or not result[0]:
        return OcrExtractedData(
            status=OcrStatus.FAILED,
            error="OCR returned no text.",
            confidence=0.0,
        )

    word_lines: list[str] = []
    confidences: list[float] = []
    for line in result[0]:
        for word_info in line:
            word = word_info[1][0]
            conf = float(word_info[1][1])
            word_lines.append(word)
            confidences.append(conf)

    text = " ".join(word_lines)
    fields = _extract_fields(word_lines)

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    return OcrExtractedData(
        name=fields["name"],
        document_number=fields["document_number"],
        date_of_birth=fields["date_of_birth"],
        nationality=fields["nationality"],
        sex=fields["sex"],
        issue_date=fields["issue_date"],
        expiry_date=fields["expiry_date"],
        confidence=round(min(1.0, avg_conf), 3),
        status=(
            OcrStatus.OK if avg_conf >= 0.7 else OcrStatus.PARTIAL
        ),
    )
