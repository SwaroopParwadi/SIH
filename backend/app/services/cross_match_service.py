"""
VIZ vs MRZ cross-match service.

Compares:
- name
- date of birth
- document number
- nationality
- sex
- expiry date

Returns MATCH / MISMATCH / NOT_AVAILABLE for each field.

Normalization handles:
- case
- spaces
- common OCR differences (e.g. O vs 0, I vs 1, spaces, hyphens)
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import re


class MatchStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NOT_AVAILABLE = "NOT_AVAILABLE"


@dataclass
class CrossMatchResult:
    overall: MatchStatus
    name: MatchStatus = MatchStatus.NOT_AVAILABLE
    date_of_birth: MatchStatus = MatchStatus.NOT_AVAILABLE
    document_number: MatchStatus = MatchStatus.NOT_AVAILABLE
    nationality: MatchStatus = MatchStatus.NOT_AVAILABLE
    sex: MatchStatus = MatchStatus.NOT_AVAILABLE
    expiry_date: MatchStatus = MatchStatus.NOT_AVAILABLE
    details: Mapping[str, dict] = field(default_factory=dict)


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    # uppercase
    s = value.upper()
    # common OCR substitutions
    s = s.translate(str.maketrans({
        "O": "0", "I": "1", "L": "1", "S": "5", "Z": "2"
    }))
    # collapse spaces, hyphens
    s = re.sub(r"[\s\-_]+", "", s)
    return s


def _compare(a: Optional[str], b: Optional[str]) -> MatchStatus:
    if a is None or b is None:
        return MatchStatus.NOT_AVAILABLE
    na = _normalize(a)
    nb = _normalize(b)
    if na == nb:
        return MatchStatus.MATCH
    # soft match: one contains the other after normalization
    if na and nb and (na in nb or nb in na):
        return MatchStatus.MATCH
    return MatchStatus.MISMATCH


def compare_ocr_vs_mrz(
    ocr_name: Optional[str],
    ocr_dob: Optional[str],
    ocr_docnum: Optional[str],
    ocr_nationality: Optional[str],
    ocr_sex: Optional[str],
    ocr_expiry: Optional[str],
    mrz_name: Optional[str],
    mrz_dob: Optional[str],
    mrz_docnum: Optional[str],
    mrz_nationality: Optional[str],
    mrz_sex: Optional[str],
    mrz_expiry: Optional[str],
) -> CrossMatchResult:
    name_status = _compare(ocr_name, mrz_name)
    dob_status = _compare(ocr_dob, mrz_dob)
    docnum_status = _compare(ocr_docnum, mrz_docnum)
    nat_status = _compare(ocr_nationality, mrz_nationality)
    sex_status = _compare(ocr_sex, mrz_sex)
    expiry_status = _compare(ocr_expiry, mrz_expiry)

    statuses = [name_status, dob_status, docnum_status, nat_status, sex_status, expiry_status]
    match_count = sum(1 for s in statuses if s == MatchStatus.MATCH)
    mismatch_count = sum(1 for s in statuses if s == MatchStatus.MISMATCH)

    if mismatch_count > 0:
        overall = MatchStatus.MISMATCH
    elif match_count > 0:
        overall = MatchStatus.MATCH
    else:
        overall = MatchStatus.NOT_AVAILABLE

    return CrossMatchResult(
        overall=overall,
        name=name_status,
        date_of_birth=dob_status,
        document_number=docnum_status,
        nationality=nat_status,
        sex=sex_status,
        expiry_date=expiry_status,
        details={
            "name": {"status": name_status, "ocr": ocr_name, "mrz": mrz_name},
            "date_of_birth": {"status": dob_status, "ocr": ocr_dob, "mrz": mrz_dob},
            "document_number": {"status": docnum_status, "ocr": ocr_docnum, "mrz": mrz_docnum},
            "nationality": {"status": nat_status, "ocr": ocr_nationality, "mrz": mrz_nationality},
            "sex": {"status": sex_status, "ocr": ocr_sex, "mrz": mrz_sex},
            "expiry_date": {"status": expiry_status, "ocr": ocr_expiry, "mrz": mrz_expiry},
        },
    )
