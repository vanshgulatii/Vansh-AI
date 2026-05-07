"""
FastAPI backend for Vansh AI student app.
Provides a simple endpoint that forwards a user query to the OpenAI API
and returns the generated response. Uses ChromaDB for vector storage
(if needed later). Environment variables are loaded from a .env file.
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from upload_pdf import router as pdf_router
from quiz import router as quiz_router

# Load environment variables from .env
load_dotenv()

# The OpenAI client will be created during startup after env vars are verified.
client = None

# Import the SQLAlchemy engine and Base metadata to create tables on startup
from database import engine, Base


app = FastAPI(title="Vansh AI Backend")

# CORS middleware – allow frontend origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# Startup event: verify env vars, create OpenAI client, and create DB tables
@app.on_event("startup")
def on_startup():
    # Ensure required env vars are present
    required_vars = ["OPENAI_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            raise RuntimeError(f"Missing required environment variable: {var}")

    # Create OpenAI client
    global client
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Create tables if they don't already exist
    Base.metadata.create_all(bind=engine)

class QueryRequest(BaseModel):
    """Schema for incoming query requests."""
    query: str
    # In a real app you could add "history" or "metadata" fields here.

class QueryResponse(BaseModel):
    """Schema for the response returned to the client."""
    answer: str

@app.post("/api/query", response_model=QueryResponse)
async def query_ai(request: QueryRequest):
    """Forward the user query to OpenAI and return the answer."""
    try:
        # Simple call to the Chat Completion API using gpt-4o-mini (cheap and fast)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": request.query}],
        )
        answer = response.choices[0].message.content.strip()
        return QueryResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}
