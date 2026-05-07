"""
SQLAlchemy models for the Vansh AI application.
Defines tables for:
- Users
- Uploaded documents
- Chat history
- Quizzes
- Notes
All models include automatic timestamps via `created_at` and `updated_at`.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    """
    User model representing a registered user of the Vansh AI app.
    Includes fields for authentication and timestamps.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents = relationship("UploadedDocument", back_populates="owner")
    chats = relationship("ChatHistory", back_populates="user")
    quizzes = relationship("Quiz", back_populates="owner")
    notes = relationship("Note", back_populates="owner")


class UploadedDocument(Base):
    """
    Model for documents uploaded by users.
    Stored as text, with metadata and ownership reference.
    """
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    mimetype = Column(String, nullable=False)
    filesize = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    Index('idx_doc_owner', owner_id)
    Index('idx_doc_user', user_id)

    owner = relationship("User", back_populates="documents")


class ChatHistory(Base):
    """
    Model for storing chat history between users and the AI.
    Includes both user prompts and AI responses.
    """
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    Index('idx_chat_user', user_id)

    user = relationship("User", back_populates="chats")


class Quiz(Base):
    """
    Model for storing generated quizzes for users.
    Each quiz has title, description, and list of questions.
    """
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    questions = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    Index('idx_quiz_owner', owner_id)

    owner = relationship("User", back_populates="quizzes")


class Note(Base):
    """
    Model for notes created by users.
    Could be study notes, reminders, or anything the user wants to save.
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    Index('idx_note_owner', owner_id)

    owner = relationship("User", back_populates="notes")
