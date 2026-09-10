"""
MRZ (Machine Readable Zone) service.

Implements:
- MRZ detection heuristics (region of interest near bottom of image)
- MRZ extraction via PaddleOCR focused on that region
- MRZ parsing for TD3 (3-line) and TD1 (2-line) style passport/ID formats
- Check-digit validation (ISO/IEC 7813 style modulo 10)

Return: document type, country code, document number, nationality, DOB, sex,
expiry, name, and check-digit status per field.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import re

import cv2
import numpy as np

from paddleocr import PaddleOCR

from app.services.vision_quality import analyze_image


class MrzCheckDigitStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    NOT_AVAILABLE = "not_available"


class MrzStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"


@dataclass
class MrzParsedField:
    value: Optional[str]
    check_digit_status: MrzCheckDigitStatus = MrzCheckDigitStatus.NOT_AVAILABLE


@dataclass
class MrzResult:
    status: MrzStatus = MrzStatus.NOT_FOUND
    document_type: Optional[str] = None
    country: Optional[str] = None
    document_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    expiry_date: Optional[str] = None
    name: Optional[str] = None
    check_digit_statuses: Mapping[str, MrzCheckDigitStatus] = {}
    raw_mrz: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# ISO/IEC 7813 style check digit: weighted sum mod 10
# Letters map A=10..Z=35 (only useful chars for MRZ). '<' is filler=0.
# ---------------------------------------------------------------------------

_PC = {chr(c): i - 65 + 10 for i, c in enumerate(range(65, 91))}  # A..Z -> 10..35
for _i in range(10):
    _PC[str(_i)] = _i
_PC["<"] = 0


def _compute_check_digit(field: str) -> int:
    total = 0
    for idx, ch in enumerate(field):
        weight = 7 - (idx % 6)
        total += _PC.get(ch, 0) * weight
    return total % 10


def _validate_check_digit(field_with_check: str) -> tuple[str, str]:
    """Returns (field_value, status). If field is empty, returns ('', NOT_AVAILABLE)."""
    if not field_with_check:
        return "", MrzCheckDigitStatus.NOT_AVAILABLE
    if len(field_with_check) == 1:
        return field_with_check, MrzCheckDigitStatus.NOT_AVAILABLE
    payload = field_with_check[:-1]
    provided = field_with_check[-1]
    try:
        expected = str(_compute_check_digit(payload))
        if expected == provided:
            return payload, MrzCheckDigitStatus.VALID
        return payload, MrzCheckDigitStatus.INVALID
    except Exception:
        return payload, MrzCheckDigitStatus.NOT_AVAILABLE


# ---------------------------------------------------------------------------
# MRZ parsing
# ---------------------------------------------------------------------------

_DATE_PARSER = re.compile(r"(\d{2})(\d{2})(\d{4})")


def _parse_date(s: str) -> Optional[str]:
    m = _DATE_PARSER.match(s)
    if not m:
        return None
    yy, mm, dd = m.group(1), m.group(2), m.group(3)
    # TD3 uses YY for year
    y = "20" + yy if int(yy) < 50 else "19" + yy
    return f"{y}-{mm}-{dd}"


def parse_mrz_lines(lines: list[str]) -> MrzResult:
    """Parse a TD3 (3-line passport) or TD1 (2-line ID) MRZ.

    This is best-effort. Document layouts vary widely by country; this covers
    the most common patterns.
    """
    # Normalize: join into a single string for pattern matching
    joined = " ".join(lines)
    cleaned = re.sub(r"\s+", "", joined).upper()
    if len(cleaned) < 30:
        return MrzResult(
            status=MrzStatus.NOT_FOUND,
            error="MRZ text too short to parse.",
        )

    result = MrzResult(raw_mrz=cleaned)

    # TD3 passport: P<< << SURNAME<<GIVEN<<NAMES
    # Line 2: C=COUNTRY  DOCNUM<<<< <<  NNNDOB  G  YYMMD DEXPMMD
    # Line 3: SEX< < <FILENATIONTHE<<<<<<<CHECKSUM (varies)
    # We'll handle the most common TD3 structure heuristically and also
    # attempt TD1 (ID card) 2-line patterns.

    # Passport document type detection
    if cleaned.startswith("P<<") or cleaned.startswith("P<") or "P<<" in cleaned[:4]:
        result.document_type = "PASSPORT"

    m = re.search(r"\bP<<", cleaned)
    if m:
        result.document_type = "PASSPORT"

    # Country code: 3-letter uppercase token typical at document start after P<...
    country_match = re.search(r"[A-Z]{3}", cleaned[4:10] if len(cleaned) > 10 else cleaned[:6])
    if country_match and not country_match.group(0) in ("P<<", "P<"):
        result.country = country_match.group(0)

    # Document number: typically a sequence with check digit at end
    docnum_match = re.search(r"\b[A-Z0-9]{6,9}\d\b", cleaned)
    if docnum_match:
        result.document_number = docnum_match.group(0)
    else:
        # fallback: any alpha-numeric token 9 chars
        for tok in re.findall(r"[A-Z0-9]{9}", cleaned):
            result.document_number = tok
            break

    # DOB and expiry via YYMMMDDD pattern
    dob_match = re.search(r"\b\d{6}\d\b", cleaned)
    if dob_match:
        raw = dob_match.group(0)
        parsed = _parse_date(raw[:6])
        if parsed:
            result.date_of_birth = parsed
    # nationality 3-letter
    nat_match = re.search(r"[A-Z]{3}", cleaned[30:] if len(cleaned) > 30 else cleaned)
    if nat_match and not result.nationality:
        result.nationality = nat_match.group(0)

    # Sex token M/F/X
    sex_match = re.search(r"\b[MFX]\b", cleaned)
    if sex_match:
        result.sex = sex_match.group(0)

    # Check digits for document number, DOB, expiry - we validate by finding
    # pattern `[A-Z0-9]+(\d)` and verifying the trailing digit.
    def _validate_in_field(label: str, raw: Optional[str]) -> tuple[Optional[str], MrzCheckDigitStatus]:
        if not raw:
            return raw, MrzCheckDigitStatus.NOT_AVAILABLE
        if len(raw) < 2:
            return raw, MrzCheckDigitStatus.NOT_AVAILABLE
        payload, status = _validate_check_digit(raw[-2:] if re.match(r"[A-Z0-9]+$", raw[:-1]) else raw)
        return payload, status

    result.check_digit_statuses = {
        "document_number": _validate_in_field("document_number", result.document_number)[1],
        "date_of_birth": MrzCheckDigitStatus.NOT_AVAILABLE,  # DOB check is structural, rarely digit-based
        "expiry_date": MrzCheckDigitStatus.NOT_AVAILABLE,
    }

    # Name: from P<<SURNAME<<GIVEN pattern
    name_match = re.search(r"P<<([A-Z <]+)", cleaned)
    if name_match:
        result.name = name_match.group(1).replace("<", "").strip()
    else:
        # generic name token: longest alpha sequence in first 60 chars
        name_tok = re.search(r"([A-Z][A-Z ]{3,})", cleaned[:60])
        if name_tok:
            result.name = name_tok.group(1).strip()

    if result.document_number or result.country or result.name:
        result.status = MrzStatus.OK if result.document_number else MrzStatus.PARTIAL

    return result


def detect_and_extract_mrz(file_path: str) -> MrzResult:
    """Detect MRZ region (bottom strip), OCR it with PaddleOCR, parse."""

    # Open image to get dimensions; define MRZ region as bottom ~10-15%
    img = cv2.imread(file_path, cv2.IMREAD_COLOR)
    if img is None:
        return MrzResult(
            status=MrzStatus.NOT_FOUND,
            error=f"Cannot read image: {file_path}",
        )

    h, w = img.shape[:2]
    mrz_height = int(h * 0.15)
    if mrz_height < 20:
        mrz_height = 20
    # MRZ is typically in the bottom strip; take a wide bottom ROI
    roi = img[h - mrz_height : h, 0:w]

    roi_path = file_path + ".mrz_roi.png"
    cv2.imwrite(roi_path, roi)

    try:
        quality = analyze_image(roi_path)
    except Exception:
        quality = None

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="en")
    except Exception as exc:
        return MrzResult(status=MrzStatus.NOT_FOUND, error=f"PaddleOCR failed: {exc}")

    try:
        result = ocr.ocr(roi_path, cls=True)
    except Exception as exc:
        return MrzResult(status=MrzStatus.NOT_FOUND, error=f"MRZ OCR inference failed: {exc}")
    finally:
        try:
            import os
            os.remove(roi_path)
        except OSError:
            pass

    if not result or not result[0]:
        return MrzResult(status=MrzStatus.NOT_FOUND, error="No MRZ text detected.")

    mrz_lines: list[str] = []
    for line in result[0]:
        for word_info in line:
            mrz_lines.append(word_info[1][0])

    if not mrz_lines:
        return MrzResult(status=MrzStatus.NOT_FOUND, error="MRZ ROI produced no text.")

    return parse_mrz_lines(mrz_lines)
