from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import json
import os
from datetime import datetime

from .base_handler import BaseHandler
from ...models import Exam, User, UserRole


class ExamHandler(BaseHandler):
    """Handler for exam-related operations."""

    def __init__(self, db: Session):
        super().__init__(db)
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    def get_exams(self, user: User, status: Optional[str] = None) -> List[Exam]:
        """Get list of exams available to the user."""
        try:
            query = self.db.query(Exam)

            # Filter by status if provided
            if status:
                # Note: Exam model doesn't have status field yet, this is for future implementation
                pass

            # For now, return all exams. In future, implement proper access control
            if user.role != UserRole.ADMIN:
                # Regular users can see exams they created or public exams
                query = query.filter(Exam.created_by == user.id)

            return query.all()
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to fetch exams")

    def get_exam(self, exam_id: int, user: User) -> Exam:
        """Get specific exam details."""
        try:
            exam = self.validate_exists(Exam, exam_id, "Exam not found")

            # Check access permissions
            if user.role != UserRole.ADMIN and exam.created_by != user.id:
                self.handle_error(Exception("Access denied"), status_code=403)

            return exam
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to fetch exam")

    def create_exam(self, title: str, description: Optional[str], user: User) -> Exam:
        """Create a new exam."""
        try:
            exam = Exam(
                title=title,
                description=description,
                created_by=user.id
            )

            self.db.add(exam)
            self.db.commit()
            self.db.refresh(exam)

            return exam
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to create exam")

    def upload_pdf(self, exam_id: int, pdf_file: UploadFile, user: User) -> Dict[str, Any]:
        """Upload and process PDF for an exam."""
        try:
            exam = self.get_exam(exam_id, user)

            # Validate file type
            if not pdf_file.filename.lower().endswith('.pdf'):
                self.handle_error(Exception("Only PDF files are allowed"), status_code=400)

            # Save PDF file
            filename = f"exam_{exam_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(self.upload_dir, filename)

            with open(file_path, "wb") as buffer:
                content = pdf_file.file.read()
                buffer.write(content)

            # Update exam with PDF information
            exam.pdf_filename = filename
            exam.pdf_content = content

            # TODO: Process PDF with LLM to extract questions
            # For now, we'll create a placeholder questions structure
            questions_json = {
                "questions": [],
                "total_questions": 0,
                "processing_status": "pending"
            }

            exam.questions_json = questions_json

            self.db.commit()
            self.db.refresh(exam)

            return {
                "exam_id": exam.id,
                "status": "uploaded",
                "message": "PDF uploaded successfully. Processing will begin shortly.",
                "filename": filename
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to upload PDF")

    def update_exam(self, exam_id: int, update_data: Dict[str, Any], user: User) -> Exam:
        """Update exam metadata."""
        try:
            exam = self.get_exam(exam_id, user)

            # Only admin or exam creator can update
            if user.role != UserRole.ADMIN and exam.created_by != user.id:
                self.handle_error(Exception("Access denied"), status_code=403)

            # Update allowed fields
            allowed_fields = ["title", "description"]
            for field, value in update_data.items():
                if field in allowed_fields and value is not None:
                    setattr(exam, field, value)

            exam.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(exam)

            return exam
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to update exam")

    def delete_exam(self, exam_id: int, user: User) -> Dict[str, str]:
        """Delete an exam."""
        try:
            exam = self.get_exam(exam_id, user)

            # Only admin or exam creator can delete
            if user.role != UserRole.ADMIN and exam.created_by != user.id:
                self.handle_error(Exception("Access denied"), status_code=403)

            # Delete associated PDF file if exists
            if exam.pdf_filename:
                file_path = os.path.join(self.upload_dir, exam.pdf_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

            self.db.delete(exam)
            self.db.commit()

            return {"message": "Exam deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to delete exam")