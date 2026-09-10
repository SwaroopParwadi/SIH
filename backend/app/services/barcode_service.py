"""
Barcode / QR code decode service.

Uses pyzbar for 1D/2D barcodes and OpenCV QRCodeDetector for QR codes.

Missing barcode does NOT automatically mean the document is fake.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import cv2

from pyzbar.pyzbar import decode as pyzbar_decode
from PIL import Image


class BarcodeStatus(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    DECODE_ERROR = "decode_error"


@dataclass
class DecodedBarcode:
    type: str
    data: str
    source: str = "pyzbar"


@dataclass
class BarcodeScanResult:
    status: BarcodeStatus
    codes: list[DecodedBarcode] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class BarcodeComparisonResult:
    codes_found: int
    matched_with_ocr: int = 0
    matched_with_mrz: int = 0
    unmatched_codes: list[dict] = field(default_factory=list)
    missing_barcode_warns: bool = False  # True if no barcode found but OCR/MRZ present


def scan_barcodes(file_path: str) -> BarcodeScanResult:
    codes: list[DecodedBarcode] = []

    # pyzbar - handles QR, EAN, Code128, DataMatrix etc.
    try:
        pil_image = Image.open(file_path)
        raw = pyzbar_decode(pil_image)
        for d in raw:
            codes.append(DecodedBarcode(
                type=d.type.decode("utf-8", errors="replace") if isinstance(d.type, bytes) else str(d.type),
                data=d.data.decode("utf-8", errors="replace") if isinstance(d.data, bytes) else str(d.data),
                source="pyzbar",
            ))
    except Exception as exc:
        return BarcodeScanResult(status=BarcodeStatus.DECODE_ERROR, error=str(exc))

    # OpenCV QR detector - sometimes useful when pyzbar misses a QR
    try:
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            detector = cv2.QRCodeDetector()
            ok, qr_data, rects, _ = detector.detectAndDecodeMulti(img)
            if ok:
                # dedupe against pyzbar results
                for qd in qr_data:
                    if not any(c.data == qd for c in codes):
                        codes.append(DecodedBarcode(
                            type="QRCODE",
                            data=qd,
                            source="opencv_qr",
                        ))
    except Exception:
        pass

    status = BarcodeStatus.FOUND if codes else BarcodeStatus.NOT_FOUND
    return BarcodeScanResult(status=status, codes=codes)


def compare_barcode_vs_ocr_mrz(
    barcodes: list[DecodedBarcode],
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
) -> BarcodeComparisonResult:
    """Best-effort comparison of barcode data against OCR/MRZ fields.

    Many barcodes (e.g. PDF417 on passports) carry structured data. We look
    for substring matches with known fields. Exact decode depends on barcode
    encoding - we do not assume a particular format.
    """
    from app.services.cross_match_service import _normalize

    matched_ocr = 0
    matched_mrz = 0
    unmatched: list[dict] = []

    def _is_field_in_barcode(field_value: Optional[str]) -> bool:
        if not field_value:
            return False
        norm_field = _normalize(field_value)
        if not norm_field:
            return False
        for code in barcodes:
            if norm_field in _normalize(code.data):
                return True
        return False

    fields = [
        ("name", ocr_name, mrz_name),
        ("date_of_birth", ocr_dob, mrz_dob),
        ("document_number", ocr_docnum, mrz_docnum),
        ("nationality", ocr_nationality, mrz_nationality),
        ("sex", ocr_sex, mrz_sex),
        ("expiry_date", ocr_expiry, mrz_expiry),
    ]

    for label, ocr_val, mrz_val in fields:
        if _is_field_in_barcode(ocr_val):
            matched_ocr += 1
        elif _is_field_in_barcode(mrz_val):
            matched_mrz += 1
        else:
            # if a barcode exists and we could not match anything, record it
            if barcodes:
                unmatched.append({"code": barcodes[0].data[:48], "label": label})

    # If barcode expected (OCR/MRZ present) but none found - soft warning
    has_any_document_data = any(
        v for v in [ocr_name, ocr_dob, ocr_docnum, ocr_nationality, ocr_sex, ocr_expiry,
                    mrz_name, mrz_dob, mrz_docnum, mrz_nationality, mrz_sex, mrz_expiry]
    )
    missing_barcode_warns = has_any_document_data and len(barcodes) == 0

    return BarcodeComparisonResult(
        codes_found=len(barcodes),
        matched_with_ocr=matched_ocr,
        matched_with_mrz=matched_mrz,
        unmatched_codes=unmatched,
        missing_barcode_warns=missing_barcode_warns,
    )
