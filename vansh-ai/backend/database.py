"""
SQLAlchemy database connection and session handling for Vansh AI.
This module provides:
- `engine` – the SQLAlchemy engine connected to a local SQLite file.
- `SessionLocal` – a session factory for request‑scoped DB sessions.
- `Base` – the declarative base class that model definitions inherit from.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Load the DB URL from the environment if provided; otherwise default to a local SQLite file.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vansh_ai.db")

# SQLite needs the ``check_same_thread`` flag disabled for use with FastAPI's async workers.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal will be used in FastAPI dependencies to get a DB session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative model definitions.
Base = declarative_base()
