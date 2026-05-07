"""
AI Chat system for Vansh AI.
- Embeds PDF text using OpenAI embeddings and stores in ChromaDB.
- Answers user questions by retrieving relevant chunks from ChromaDB and
  querying the OpenAI chat completion API.
- Stores Q&A pairs in the ChatHistory table.
"""

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
import chromadb

from auth import get_current_user, get_db
from models import ChatHistory, UploadedDocument, User
from database import SessionLocal

# ---------------------------------------------------------------------------
# Router & clients
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/chat", tags=["chat"])

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ChromaDB persistent client (creates ./chroma_db directory)
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []   # filenames of documents used


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_user_collection(user_id: int):
    """Return (or create) a ChromaDB collection for the given user."""
    collection_name = f"user_{user_id}_docs"
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"user_id": str(user_id)},
    )


async def embed_text(text: str) -> List[float]:
    """Use OpenAI's embedding model to turn text into a vector."""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text,
    )
    return response.data[0].embedding


# ---------------------------------------------------------------------------
# Public endpoint – ask a question
# ---------------------------------------------------------------------------
@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve relevant chunks from the user's ChromaDB collection,
    build a context-aware prompt, query OpenAI, store the exchange,
    and return the answer.
    """
    # 1. Embed the user's question
    question_emb = await embed_text(body.question)

    # 2. Query ChromaDB for the 3 most similar chunks
    collection = get_user_collection(current_user.id)
    results = collection.query(
        query_embeddings=[question_emb],
        n_results=3,
    )
    # results["documents"] is a list of lists; flatten
    retrieved_docs = results.get("documents", [[]])[0]
    source_metas = results.get("metadatas", [[]])[0]
    source_filenames = [m.get("filename", "unknown") for m in source_metas]

    # 3. Build context string
    context = "\n\n".join(retrieved_docs) if retrieved_docs else ""

    # 4. Call OpenAI chat completion with the context
    system_prompt = (
        "You are a helpful study assistant. "
        "Answer the user's question using ONLY the information provided in the context below. "
        "If the context doesn't contain the answer, say you don't have enough information."
    )
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {body.question}"},
            ],
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    # 5. Store the Q&A in ChatHistory
    chat_record = ChatHistory(
        user_id=current_user.id,
        user_message=body.question,
        ai_response=answer,
    )
    db.add(chat_record)
    db.commit()

    return ChatResponse(answer=answer, sources=source_filenames)


# ---------------------------------------------------------------------------
# Retrieve chat history for the current user
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Function to be called from upload_pdf.py to embed and store a document
# ---------------------------------------------------------------------------
async def add_document_to_vectorstore(
    user_id: int, doc_id: int, text: str, filename: str
):
    """
    Embed the given text and store it in the user's ChromaDB collection.
    Should be called after a PDF is uploaded and its text extracted.
    """
    collection = get_user_collection(user_id)
    # Use the document ID as the unique identifier in ChromaDB
    doc_id_str = str(doc_id)
    embedding = await embed_text(text)
    collection.add(
        ids=[doc_id_str],
        documents=[text],
        metadatas=[{"filename": filename, "doc_id": doc_id_str}],
        embeddings=[embedding],
    )
