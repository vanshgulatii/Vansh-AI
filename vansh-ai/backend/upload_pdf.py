"""
PDF upload endpoint for Vansh AI.
Accepts a PDF file, saves it locally, extracts all text using PyPDF2,
stores metadata in the database, and returns the extracted text.
"""

import os
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from PyPDF2 import PdfReader

from auth import get_current_user
from models import UploadedDocument, User
from database import SessionLocal

# ---------------------------------------------------------------------------
# Router setup
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/pdf", tags=["pdf"])

# Folder where uploaded PDFs will be stored (configurable via env)
UPLOAD_DIR = os.getenv("PDF_UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------
@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF, extract text with PyPDF2, save file locally,
    store metadata in DB, and return extracted text.
    """
    # 1. Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    # 2. Read file contents (for size check and saving)
    contents = await file.read()
    max_size = 5 * 1024 * 1024  # 5 MiB limit
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 5 MiB)",
        )

    # 3. Save the file locally with a safe name
    safe_filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # 4. Extract text from PDF using PyPDF2
    try:
        reader = PdfReader(file_path)
        # Combine text from all pages; if a page has no text, use empty string
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from PDF: {exc}",
        )

    # 5. Store metadata in the database
    doc = UploadedDocument(
        title=file.filename,
        file_path=file_path,
        file_type="pdf",
        filename=file.filename,
        mimetype=file.content_type,
        filesize=len(contents),
        owner_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Return the extracted text (and some metadata)
    return {
        "id": doc.id,
        "filename": file.filename,
        "extracted_text": extracted_text,
        "pages": len(reader.pages) if "reader" in locals() else None,
    }
