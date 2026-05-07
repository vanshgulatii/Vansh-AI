"""
FastAPI backend for Vansh AI student app.
Created by: Vansh Gulati
Provides: query endpoint, auth, PDF upload, chat, summary, quiz APIs.
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Routers
from auth import router as auth_router
from upload_pdf import router as pdf_router
from chat import router as chat_router
from summary import router as summary_router
from quiz import router as quiz_router

# Load environment variables
load_dotenv()

# Database
from database import engine, Base


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Vansh AI Backend")

# CORS middleware — set specific origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(pdf_router)
app.include_router(chat_router)
app.include_router(summary_router)
app.include_router(quiz_router)


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    # Verify required env vars
    required_vars = ["OPENAI_API_KEY", "JWT_SECRET_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            raise RuntimeError(f"Missing required environment variable: {var}")

    # Create DB tables
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Simple query endpoint (uses client from clients.py)
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str


@app.post("/api/query", response_model=QueryResponse)
async def query_ai(request: QueryRequest):
    from clients import openai_client
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": request.query}],
        )
        answer = response.choices[0].message.content.strip()
        return QueryResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}
