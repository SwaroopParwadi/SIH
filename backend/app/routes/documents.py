"""
POST /api/documents/upload
GET /api/documents/{case_id}
"""
import os
import shutil
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Temporary upload directory — images are NOT stored in MongoDB
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}


def get_db():
    from app.main import app as main_app
    return getattr(main_app.state, "mongodb_db", None)


@router.post("/upload", status_code=201)
async def upload_document(
    case_id: str,
    file: UploadFile = File(...),
):
    """
    Upload a document image for a case.
    Image is stored temporarily on the local filesystem (NOT in MongoDB).
    MongoDB stores only the metadata reference.
    """
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    # Validate case exists
    case = db.cases.find_one({"case_id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check file size (read content first)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {len(contents) / (1024*1024):.1f}MB exceeds 10MB limit",
        )

    # Generate unique filename and save locally
    file_id = str(uuid.uuid4())
    filename = f"{case_id}_{file_id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    file_size_kb = len(contents) / 1024

    # Store metadata in MongoDB (NOT the image)
    db.documents_metadata.insert_one({
        "case_id": case_id,
        "file_id": file_id,
        "original_filename": file.filename,
        "stored_filename": filename,
        "file_path": filepath,
        "file_size_bytes": len(contents),
        "file_size_kb": round(file_size_kb, 2),
        "content_type": file.content_type or "image/jpeg",
        "uploaded_at": now,
        "status": "stored",
    })

    # Update case with document reference
    db.cases.update_one(
        {"case_id": case_id},
        {"$set": {"document_uploaded": True, "document_uploaded_at": now, "updated_at": now}},
    )

    return {
        "case_id": case_id,
        "file_id": file_id,
        "original_filename": file.filename,
        "stored_as": filename,
        "file_size_kb": round(file_size_kb, 2),
        "content_type": file.content_type or "image/jpeg",
        "uploaded_at": now,
        "status": "stored_locally",
        "note": "Image stored on local filesystem. MongoDB contains only metadata.",
    }


@router.get("/{case_id}")
async def get_case_documents(case_id: str):
    """Get all document uploads for a case (metadata only)."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    # Check case exists
    if not db.cases.find_one({"case_id": case_id}):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    documents = list(db.documents_metadata.find({"case_id": case_id}))
    return [
        {
            "file_id": doc.get("file_id"),
            "original_filename": doc.get("original_filename"),
            "stored_as": doc.get("stored_filename"),
            "file_size_kb": doc.get("file_size_kb"),
            "content_type": doc.get("content_type"),
            "uploaded_at": doc.get("uploaded_at"),
            "status": doc.get("status"),
            "note": "Image stored locally; download via file_id if needed",
        }
        for doc in documents
    ]


@router.delete("/{file_id}")
async def delete_document(file_id: str):
    """Delete a document file from local storage."""
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    doc = db.documents_metadata.find_one({"file_id": file_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from filesystem
    filepath = doc.get("file_path")
    if filepath and os.path.exists(filepath):
        os.remove(filepath)

    # Remove metadata from MongoDB
    db.documents_metadata.delete_one({"file_id": file_id})

    return {"status": "deleted", "file_id": file_id, "message": "Document removed from local storage and MongoDB"}
