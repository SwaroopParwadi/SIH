"""
Optional local biometric verification.

- Face verification: 1:1 similarity between document portrait and live webcam face.
- Liveness: basic prototype challenge-response (head movement / blink) only.

Both modules are OPTIONAL.
- If the required library is unavailable, return NOT_AVAILABLE.
- If webcam is unavailable, liveness returns NOT_AVAILABLE.
- The backend must NOT crash if biometrics is unavailable.

This is NOT database-wide identity search and NOT production-grade anti-spoofing.
"""
from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    import face_recognition
    BIOMETICS_AVAILABLE = True
except Exception as e:
    BIOMETICS_AVAILABLE = False
    _BIOMETICS_ERROR = f"face_recognition unavailable: {e}"


class BiometricStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    NOT_AVAILABLE = "not_available"
    NO_FACE_DETECTED = "no_face_detected"
    FAILED = "failed"


@dataclass
class FaceVerificationResult:
    status: BiometricStatus
    similarity_score: Optional[float] = None
    match_status: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    model: str = "local_face_embeddings"


@dataclass
class LivenessResult:
    status: BiometricStatus
    liveness_score: Optional[float] = None
    challenge_passed: bool = False
    notes: Optional[str] = None
    error: Optional[str] = None
    prototype: bool = True


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def _load_image_rgb(path: str):
    if not BIOMETICS_AVAILABLE:
        raise RuntimeError(_BIOMETICS_ERROR)
    return face_recognition.load_image_file(path)


def _detect_face_embeddings(image_rgb):
    if not BIOMETICS_AVAILABLE:
        raise RuntimeError(_BIOMETICS_ERROR)
    encodings = face_recognition.face_encodings(image_rgb)
    locations = face_recognition.face_locations(image_rgb)
    return encodings, locations


def _compare_embeddings(encoding_a, encoding_b):
    if not BIOMETICS_AVAILABLE:    raise RuntimeError(_BIOMETICS_ERROR)

    distances = face_recognition.face_distance([encoding_a], encoding_b)
    dist = float(distances[0])
    similarity = max(0.0, (1.0 - dist)) * 100.0
    return similarity, dist


# ------------------------------------------------------------------
# Face verification (1:1)
# ------------------------------------------------------------------

def verify_faces(
    document_portrait_path: str,
    live_face_path: str,
    tolerance: float = 0.6,
) -> FaceVerificationResult:
    if not BIOMETICS_AVAILABLE:
        return FaceVerificationResult(
            status=BiometricStatus.NOT_AVAILABLE,
            error=_BIOMETICS_ERROR,
        )

    try:
        doc_rgb = _load_image_rgb(document_portrait_path)
    except Exception as e:
        return FaceVerificationResult(
            status=BiometricStatus.FAILED,
            error=f"Failed to load document portrait: {e}",
        )

    try:
        live_rgb = _load_image_rgb(live_face_path)
    except Exception as e:
        return FaceVerificationResult(
            status=BiometricStatus.FAILED,
            error=f"Failed to load live face image: {e}",
        )

    doc_encodings, _doc_locations = _detect_face_embeddings(doc_rgb)
    if not doc_encodings:
        return FaceVerificationResult(
            status=BiometricStatus.NO_FACE_DETECTED,
            match_status="NO_FACE_DETECTED",
            error="No face detected in document portrait",
        )

    live_encodings, _live_locations = _detect_face_embeddings(live_rgb)
    if not live_encodings:
        return FaceVerificationResult(
            status=BiometricStatus.NO_FACE_DETECTED,
            match_status="NO_FACE_DETECTED",
            error="No face detected in live face image",
        )

    doc_encoding = doc_encodings[0]
    live_encoding = live_encodings[0]

    similarity, dist = _compare_embeddings(doc_encoding, live_encoding)

    match = dist <= tolerance
    if match:
        match_status = "MATCH"
        status = BiometricStatus.OK
    else:
        match_status = "MISMATCH"
        status = BiometricStatus.PARTIAL if similarity > 30 else BiometricStatus.FAILED

    confidence = min(1.0, similarity / 100.0)

    return FaceVerificationResult(
        status=status,
        similarity_score=round(similarity, 2),
        match_status=match_status,
        confidence=round(confidence, 3),
    )


# ------------------------------------------------------------------
# Liveness prototype
# ------------------------------------------------------------------

def run_liveness_prototype(webcam_index: int = 0, duration_seconds: float = 10.0) -> LivenessResult:
    if not BIOMETICS_AVAILABLE:
        return LivenessResult(
            status=BiometricStatus.NOT_AVAILABLE,
            error=_BIOMETICS_ERROR,
        )

    try:
        import cv2
    except Exception as e:
        return LivenessResult(
            status=BiometricStatus.NOT_AVAILABLE,
            error=f"OpenCV unavailable for liveness: {e}",
        )

    cap = cv2.VideoCapture(webcam_index)
    if not cap.isOpened():
        return LivenessResult(
            status=BiometricStatus.NOT_AVAILABLE,
            error="Webcam unavailable",
        )

    frames_with_face = 0
    total_frames = 0
    start = time.time()
    blink_signal_detected = False
    prev_eye_open = None

    try:
        while time.time() - start < duration_seconds:
            ret, frame = cap.read()
            if not ret:
                break

            total_frames += 1
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                locations = face_recognition.face_locations(rgb)
            except Exception:
                continue

            if locations:
                frames_with_face += 1

                top, right, bottom, left = locations[0]
                eye_region = rgb[top:bottom, left:right]
                if eye_region.size > 0:
                    mean_val = float(np.mean(eye_region))
                    curr_eye_open = mean_val > 50
                    if prev_eye_open is not None:
                        if prev_eye_open != curr_eye_open:
                            blink_signal_detected = True
                    prev_eye_open = curr_eye_open

            time.sleep(0.03)
    finally:
        cap.release()

    if total_frames == 0:
        return LivenessResult(
            status=BiometricStatus.NOT_AVAILABLE,
            error="No frames captured from webcam",
        )

    face_presence_ratio = frames_with_face / total_frames
    base_score = face_presence_ratio * 70.0
    if blink_signal_detected:
        base_score += 20.0
    if face_presence_ratio > 0.5:
        base_score += 10.0

    liveness_score = min(100.0, base_score)
    challenge_passed = liveness_score >= 60.0

    return LivenessResult(
        status=BiometricStatus.OK if liveness_score > 50 else BiometricStatus.PARTIAL,
        liveness_score=round(liveness_score, 2),
        challenge_passed=challenge_passed,
        notes="BASIC PROTOTYPE LIVENESS - not production-grade anti-spoofing. If webcam unavailable, result is NOT_AVAILABLE.",
        prototype=True,
    )


# ------------------------------------------------------------------
# Webcam capture helper
# ------------------------------------------------------------------

def capture_live_face_image(webcam_index: int = 0, output_path: Optional[str] = None) -> Optional[str]:
    if not BIOMETICS_AVAILABLE:
        return None
    try:
        import cv2
    except Exception:
        return None

    cap = cv2.VideoCapture(webcam_index)
    if not cap.isOpened():
        return None
    try:
        ret, frame = cap.read()
        if not ret:
            return None
        if output_path:
            cv2.imwrite(output_path, frame)
            return output_path
        _, buf = cv2.imencode(".jpg", frame)
        b64 = base64.b64encode(buf).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    finally:
        cap.release()
