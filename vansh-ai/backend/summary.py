"""
AI Summary Generator for Vansh AI.
- Summarizes uploaded PDFs using OpenAI API.
- Generates short summaries and bullet-point notes.
"""

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from auth import get_current_user, get_db
from models import UploadedDocument, User
from chat import get_user_collection

# ---------------------------------------------------------------------------
# Router setup
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/summary", tags=["summary"])

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class SummaryRequest(BaseModel):
    """Request to summarize a specific document by ID."""
    doc_id: int
    max_length: Optional[int] = 200  # words


class SummaryResponse(BaseModel):
    """Response containing the summary and bullet points."""
    doc_id: int
    filename: str
    short_summary: str
    bullet_points: List[str]


# ---------------------------------------------------------------------------
# Helper: retrieve document text from ChromaDB
# ---------------------------------------------------------------------------
def get_document_text(user_id: int, doc_id: int) -> str:
    """Fetch the full text of a document from ChromaDB."""
    collection = get_user_collection(user_id)
    results = collection.get(
        ids=[str(doc_id)],
        include=["documents"],
    )
    docs = results.get("documents", [])
    if not docs:
        raise HTTPException(status_code=404, detail="Document not found in vector store")
    return docs[0]


# ---------------------------------------------------------------------------
# Endpoint: generate summary
# ---------------------------------------------------------------------------
@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(
    body: SummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a short summary and bullet-point notes for an uploaded PDF.
    """
    # 1. Verify the document belongs to the user
    doc = (
        db.query(UploadedDocument)
        .filter(
            UploadedDocument.id == body.doc_id,
            UploadedDocument.owner_id == current_user.id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Retrieve the document text from ChromaDB
    try:
        text = get_document_text(current_user.id, body.doc_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {e}")

    # 3. Truncate text if too long (OpenAI context limits)
    max_chars = 12000  # ~3000 tokens, safe margin
    if len(text) > max_chars:
        text = text[:max_chars] + "...[truncated]"

    # 4. Call OpenAI to generate summary and bullet points
    prompt = f"""
You are a study assistant. Given the following document text, please:
1. Write a short summary in about {body.max_length} words.
2. Extract 5-8 key bullet-point notes.

Document text:
{text}

Respond in JSON format:
{{
  "short_summary": "...",
  "bullet_points": ["...", "...", ...]
}}
"""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},  # ensures JSON output
        )
        import json
        result = json.loads(response.choices[0].message.content.strip())
        short_summary = result.get("short_summary", "")
        bullet_points = result.get("bullet_points", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    return SummaryResponse(
        doc_id=doc.id,
        filename=doc.filename,
        short_summary=short_summary,
        bullet_points=bullet_points,
    )


# ---------------------------------------------------------------------------
# Endpoint: list user's documents (for choosing which to summarize)
# ---------------------------------------------------------------------------
@router.get("/documents")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all uploaded documents for the current user."""
    docs = (
        db.query(UploadedDocument)
        .filter(UploadedDocument.owner_id == current_user.id)
        .order_by(UploadedDocument.created_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "filesize": d.filesize,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]
