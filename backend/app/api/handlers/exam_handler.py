import os
import json
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from app.database import get_db
from app.models.exam import Exam
from app.models.user import User
from app.services.pdf_processing import PDFProcessor
from app.api.handlers.auth_handler import get_current_user

logger = logging.getLogger(__name__)

# Lazy initialization of PDFProcessor
_pdf_processor = None

def get_pdf_processor():
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PDFProcessor()
    return _pdf_processor

class CreateExamRequest(BaseModel):
    """Request model for creating an exam with PDF URL"""
    title: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    pdf_url: HttpUrl  # URL to the PDF file

class ExamResponse(BaseModel):
    """Response model for exam data"""
    id: int
    title: str
    description: Optional[str]
    duration_minutes: Optional[int]
    created_by: int
    created_at: str
    status: str
    processed_data: Optional[Dict[str, Any]] = None

async def create_exam_with_pdf_url(
    request: CreateExamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ExamResponse:
    """
    Create a new exam and process PDF from URL
    """
    try:
        logger.info(f"Creating exam with PDF URL: {request.pdf_url}")

        # Create exam record in database with initial status
        exam = Exam(
            title=request.title,
            description=request.description,
            duration_minutes=request.duration_minutes,
            created_by=current_user.id,
            status="draft"  # Initial status
        )

        db.add(exam)
        db.commit()
        db.refresh(exam)

        logger.info(f"Created exam record with ID: {exam.id}")

        # Update status to "uploaded" before processing
        exam.status = "uploaded"
        db.commit()

        # Process PDF from URL
        try:
            pdf_processor = get_pdf_processor()
            processed_data = await pdf_processor.process_pdf_from_url(
                str(request.pdf_url),
                exam.id
            )

            # Update exam with processed data and set status to "processed"
            exam.questions_json = processed_data
            exam.status = "processed"
            db.commit()

            logger.info(f"Successfully processed PDF for exam {exam.id}")

        except Exception as processing_error:
            logger.error(f"PDF processing failed for exam {exam.id}: {str(processing_error)}")
            # Update status to "processing_failed"
            exam.status = "processing_failed"
            db.commit()
            # Don't fail the entire request, just log the error
            # The exam record is still created but without processed data

        return ExamResponse(
            id=exam.id,
            title=exam.title,
            description=exam.description,
            duration_minutes=exam.duration_minutes,
            created_by=exam.created_by,
            created_at=exam.created_at.isoformat(),
            status=exam.status,
            processed_data=exam.questions_json
        )

    except Exception as e:
        logger.error(f"Failed to create exam: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create exam: {str(e)}")

async def get_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ExamResponse:
    """
    Get exam by ID
    """
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()

        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        # Check if user has access to this exam
        if exam.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        return ExamResponse(
            id=exam.id,
            title=exam.title,
            description=exam.description,
            duration_minutes=exam.duration_minutes,
            created_by=exam.created_by,
            created_at=exam.created_at.isoformat(),
            status=exam.status,
            processed_data=exam.questions_json
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get exam {exam_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get exam: {str(e)}")

async def get_exams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[ExamResponse]:
    """
    Get all exams for the current user
    """
    try:
        if current_user.role == "admin":
            # Admin can see all exams
            exams = db.query(Exam).all()
        else:
            # Regular users can only see their own exams
            exams = db.query(Exam).filter(Exam.created_by == current_user.id).all()

        return [
            ExamResponse(
                id=exam.id,
                title=exam.title,
                description=exam.description,
                duration_minutes=exam.duration_minutes,
                created_by=exam.created_by,
                created_at=exam.created_at.isoformat(),
                status=exam.status,
                processed_data=exam.questions_json
            )
            for exam in exams
        ]

    except Exception as e:
        logger.error(f"Failed to get exams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get exams: {str(e)}")

async def delete_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an exam
    """
    try:
        exam = db.query(Exam).filter(Exam.id == exam_id).first()

        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        # Check if user has permission to delete this exam
        if exam.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db.delete(exam)
        db.commit()

        return {"message": "Exam deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete exam {exam_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete exam: {str(e)}")