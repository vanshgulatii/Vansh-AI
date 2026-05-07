"""
FastAPI dependencies for database session handling.
Provides a `get_db` dependency that yields a SQLAlchemy session
and ensures it is closed after the request.
"""

from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Generator


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for a request.
    FastAPI will automatically close the session when the request
    finishes (even if an exception occurs).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
