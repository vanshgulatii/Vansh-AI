"""
PDF upload for Vansh AI
Created by: Vansh Gulati
Accepts PDF uploads, saves locally, extracts text using PyPDF2,
stores metadata in DB, and adds text to ChromaDB vector store.
"""

import os
from werkzeug.utils import secure_filename
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from PyPDF2 import PdfReader

from .auth import get_current_user
from .models import UploadedDocument, User
from .database import SessionLocal
from .clients import add_to_vectorstore

# Router
router = APIRouter(prefix="/api/pdf", tags=["pdf"])

# Upload folder
UPLOAD_DIR = os.getenv("PDF_UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf'}


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Validate file extension
    original_name = secure_filename(file.filename)
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # 2. Validate MIME type (additional check)
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type",
        )

    # 3. Read file contents
    contents = await file.read()
    max_size = 5 * 1024 * 1024  # 5 MiB
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 5 MiB)",
        )

    # 4. Save file locally with safe name
    safe_filename = f"{current_user.id}_{original_name}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # 5. Extract text using PyPDF2
    try:
        reader = PdfReader(file_path)
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read PDF: {exc}",
        )

    # 6. Store metadata in DB
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

    # 7. Add to ChromaDB vector store
    await add_to_vectorstore(current_user.id, doc.id, extracted_text, file.filename)

    return {
        "id": doc.id,
        "filename": file.filename,
        "extracted_text": extracted_text,
        "pages": len(reader.pages),
    }
