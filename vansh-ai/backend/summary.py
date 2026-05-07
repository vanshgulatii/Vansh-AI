"""
AI Summary for Vansh AI
Created by: Vansh Gulati
Summarizes uploaded PDFs using OpenAI.
Generates short summaries + bullet-point notes.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from models import UploadedDocument, User
from clients import get_collection


router = APIRouter(prefix="/api/summary", tags=["summary"])

# Schemas
class SummaryRequest(BaseModel):
    doc_id: int
    max_length: Optional[int] = 200


class SummaryResponse(BaseModel):
    doc_id: int
    filename: str
    short_summary: str
    bullet_points: List[str]


# Get document text from ChromaDB
def get_doc_text(user_id: int, doc_id: int) -> str:
    collection = get_collection(user_id)
    results = collection.get(ids=[str(doc_id)], include=["documents"])
    docs = results.get("documents", [])
    if not docs:
        raise HTTPException(status_code=404, detail="Document not found in vector store")
    return docs[0]


# Generate summary
@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(
    body: SummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify document ownership
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

    # Get text from ChromaDB
    text = get_doc_text(current_user.id, body.doc_id)

    # Truncate if too long
    if len(text) > 12000:
        text = text[:12000] + "...[truncated]"

    # Ask OpenAI
    from clients import openai_client

    prompt = f"""
You are a study assistant. Given the document text below, please:
1. Write a short summary in about {body.max_length} words.
2. Extract 5-8 key bullet-point notes.

Document text:
{text}

Respond in JSON format:
{{
  "short_summary": "...",
  "bullet_points": ["...", "..."]
}}
"""

    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        import json
        result = json.loads(resp.choices[0].message.content.strip())
        return SummaryResponse(
            doc_id=doc.id,
            filename=doc.filename,
            short_summary=result.get("short_summary", ""),
            bullet_points=result.get("bullet_points", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")


# List user documents
@router.get("/documents")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
