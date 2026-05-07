"""
Quiz Generator for Vansh AI
Created by: Vansh Gulati
Generates MCQs from uploaded PDFs using OpenAI API.
Stores quizzes in the database.
"""

import os
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from models import Quiz, UploadedDocument, User
from clients import get_collection


router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# Schemas
class QuizGenerateRequest(BaseModel):
    doc_id: int
    num_questions: int = 5
    title: Optional[str] = None


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None


class QuizResponse(BaseModel):
    id: int
    title: str
    questions: List[QuizQuestion]


class QuizListResponse(BaseModel):
    id: int
    title: str
    num_questions: int
    is_completed: bool
    created_at: str


class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: List[int]


class QuizResultResponse(BaseModel):
    quiz_id: int
    score: int
    total: int
    percentage: float
    detailed_results: List[dict]


# Get document text from ChromaDB
def get_doc_text(user_id: int, doc_id: int) -> str:
    collection = get_collection(user_id)
    results = collection.get(ids=[str(doc_id)], include=["documents"])
    docs = results.get("documents", [])
    if not docs:
        raise HTTPException(status_code=404, detail="Document not found in vector store")
    return docs[0]


# Generate quiz
@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    body: QuizGenerateRequest,
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
    try:
        text = get_doc_text(current_user.id, body.doc_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {e}")

    # Truncate if too long
    if len(text) > 12000:
        text = text[:12000] + "...[truncated]"

    # Ask OpenAI to generate MCQs
    from clients import openai_client
    prompt = f"""
You are an educational quiz generator. Based on the following document text,
generate {body.num_questions} multiple-choice questions (MCQs).

For each question provide:
- "question": the question text
- "options": an array of exactly 4 answer choices (strings)
- "correct_answer": the index (0-3) of the correct option
- "explanation": a brief explanation of why the answer is correct

Document text:
{text}

Respond in JSON format:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct_answer": 0,
      "explanation": "..."
    }},
    ...
  ]
}}
"""

    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.choices[0].message.content.strip())
        questions = result.get("questions", [])
        if not questions:
            raise ValueError("No questions generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    # Save quiz to database
    title = body.title or f"Quiz on {doc.filename}"
    quiz = Quiz(
        title=title,
        description=f"Generated from {doc.filename}",
        questions=json.dumps(questions),
        owner_id=current_user.id,
        is_completed=False,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return QuizResponse(
        id=quiz.id,
        title=quiz.title,
        questions=[QuizQuestion(**q) for q in questions],
    )


# List quizzes
@router.get("/list", response_model=List[QuizListResponse])
async def list_quizzes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.owner_id == current_user.id)
        .order_by(Quiz.created_at.desc())
        .all()
    )
    return [
        QuizListResponse(
            id=q.id,
            title=q.title,
            num_questions=len(json.loads(q.questions)) if q.questions else 0,
            is_completed=q.is_completed,
            created_at=q.created_at.isoformat() if q.created_at else "",
        )
        for q in quizzes
    ]


# Get a specific quiz
@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.owner_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = json.loads(quiz.questions) if quiz.questions else []
    return QuizResponse(
        id=quiz.id,
        title=quiz.title,
        questions=[QuizQuestion(**q) for q in questions],
    )


# Submit quiz answers
@router.post("/submit", response_model=QuizResultResponse)
async def submit_quiz(
    body: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == body.quiz_id, Quiz.owner_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = json.loads(quiz.questions) if quiz.questions else []
    if len(body.answers) != len(questions):
        raise HTTPException(status_code=400, detail="Number of answers doesn't match number of questions")

    correct_count = 0
    detailed_results = []
    for i, item in enumerate(zip(questions, body.answers)):
        question, user_answer = item
        correct = question.get("correct_answer", 0)
        is_correct = user_answer == correct
        if is_correct:
            correct_count += 1
        detailed_results.append({
            "question": question.get("question"),
            "options": question.get("options"),
            "user_answer": user_answer,
            "correct_answer": correct,
            "is_correct": is_correct,
            "explanation": question.get("explanation", ""),
        })

    quiz.is_completed = True
    db.commit()

    return QuizResultResponse(
        quiz_id=quiz.id,
        score=correct_count,
        total=len(questions),
        percentage=(correct_count / len(questions)) * 100 if questions else 0,
        detailed_results=detailed_results,
    )
