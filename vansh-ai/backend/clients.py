"""
Centralized clients for Vansh AI.
Created by: Vansh Gulati
Initializes OpenAI and ChromaDB clients once for reuse.
"""

import os
from openai import AsyncOpenAI
import chromadb


# OpenAI client (used by chat.py, summary.py, quiz.py)
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ChromaDB persistent client (used by chat.py)
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection(user_id: int):
    """Return (or create) a ChromaDB collection for the given user."""
    collection_name = f"user_{user_id}_docs"
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"user_id": str(user_id)},
    )


async def embed_text(text: str) -> list:
    """Use OpenAI's embedding model to turn text into a vector."""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text,
    )
    return response.data[0].embedding


async def add_to_vectorstore(user_id: int, doc_id: int, text: str, filename: str):
    """Embed text and store it in the user's ChromaDB collection."""
    collection = get_collection(user_id)
    embedding = await embed_text(text)
    collection.add(
        ids=[str(doc_id)],
        documents=[text],
        metadatas=[{"filename": filename, "doc_id": str(doc_id)}],
        embeddings=[embedding],
    )
