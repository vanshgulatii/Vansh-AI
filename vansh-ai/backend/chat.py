"""
AI Chat for Vansh AI
Created by: Vansh Gulati
Answers questions from uploaded PDFs using OpenAI + ChromaDB.
Stores Q&A in ChatHistory.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from models import ChatHistory, UploadedDocument, User
from clients import get_collection, embed_text


# Router
router = APIRouter(prefix="/api/chat", tags=["chat"])


# Schemas
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []


# Ask endpoint
@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Embed question
    q_emb = await embed_text(body.question)

    # 2. Search ChromaDB
    collection = get_collection(current_user.id)
    results = collection.query(query_embeddings=[q_emb], n_results=3)

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    sources = [m.get("filename", "unknown") for m in metas]

    # 3. Build context
    context = "\n\n".join(docs) if docs else ""

    # 4. Ask OpenAI
    system_msg = (
        "You are a helpful study assistant. "
        "Answer using ONLY the context below. "
        "If the context doesn't contain the answer, say you don't have enough information."
    )
    from clients import openai_client
    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {body.question}"},
            ],
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    # 5. Save to history
    db.add(ChatHistory(
        user_id=current_user.id,
        user_message=body.question,
        ai_response=answer,
    ))
    db.commit()

    return ChatResponse(answer=answer, sources=sources)


# History endpoint
@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "question": r.user_message,
            "answer": r.ai_response,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
