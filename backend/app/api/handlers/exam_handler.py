from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import json
import os
import shutil
import asyncio
from datetime import datetime

from .base_handler import BaseHandler
from ...models import Exam, User
from ...services.pdf_processing import PDFProcessor
from ...utils.file_utils import FileUtils


class ExamHandler(BaseHandler):
    """Handler for exam-related operations."""

    def __init__(self, db: Session):
        super().__init__(db)
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        self._pdf_processor = None
        self.file_utils = FileUtils()

    @property
    def pdf_processor(self):
        """Lazy initialization of PDF processor"""
        if self._pdf_processor is None:
            try:
                # Check if Azure OpenAI credentials are available
                import os
                required_env_vars = [
                    "AZURE_OPENAI_API_KEY",
                    "AZURE_OPENAI_ENDPOINT",
                    "AZURE_OPENAI_DEPLOYMENT_NAME"
                ]

                missing_vars = [var for var in required_env_vars if not os.getenv(var)]
                if missing_vars:
                    raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

                self._pdf_processor = PDFProcessor()
                print("PDF processor initialized successfully")  # Debug log
            except Exception as e:
                print(f"Failed to initialize PDF processor: {str(e)}")  # Debug log
                raise
        return self._pdf_processor

    def get_exams(self, user: User, status: Optional[str] = None) -> List[Exam]:
        """Get list of exams available to the user."""
        try:
            query = self.db.query(Exam)

            # Filter by status if provided
            if status:
                # Note: Exam model doesn't have status field yet, this is for future implementation
                pass

            # For now, return all exams. In future, implement proper access control
            if user.role != "admin":
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
            if user.role != "admin" and exam.created_by != user.id:
                self.handle_error(Exception("Access denied"), status_code=403)

            return exam
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to fetch exam")

    async def create_exam(self, title: str, description: Optional[str], user: User, duration_minutes: Optional[int] = None, pdf_file: Optional[UploadFile] = None) -> Dict[str, Any]:
        """Create a new exam with optional PDF processing."""
        try:
            # Create the exam first
            exam = Exam(
                title=title,
                description=description,
                duration_minutes=duration_minutes,
                created_by=user.id
            )

            self.db.add(exam)
            self.db.commit()
            self.db.refresh(exam)

            # If PDF file is provided, process it
            pdf_processing_result = None
            if pdf_file:
                try:
                    print(f"Starting PDF processing for exam {exam.id}")  # Debug log
                    pdf_processing_result = await self.upload_pdf(exam.id, pdf_file, user)
                    print(f"PDF processing completed: {pdf_processing_result}")  # Debug log
                except Exception as e:
                    # If PDF processing fails, still return the exam but with error info
                    import traceback
                    error_details = f"{str(e)}\n{traceback.format_exc()}"
                    print(f"PDF processing failed: {error_details}")  # Debug log
                    pdf_processing_result = {
                        "status": "failed",
                        "error": error_details
                    }

            # Convert exam to dict to ensure proper serialization
            exam_dict = {
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "duration_minutes": exam.duration_minutes,
                "pdf_filename": exam.pdf_filename,
                "status": exam.status,
                "created_by": exam.created_by,
                "created_at": exam.created_at.isoformat() if exam.created_at else None,
                "updated_at": exam.updated_at.isoformat() if exam.updated_at else None
            }

            return {
                "exam": exam_dict,
                "pdf_processing": pdf_processing_result
            }

        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to create exam")

    async def upload_pdf(self, exam_id: int, pdf_file: UploadFile, user: User) -> Dict[str, Any]:
        """Upload and process PDF for an exam."""
        temp_dir = None
        temp_file_path = None
        try:
            exam = self.get_exam(exam_id, user)

            # Validate PDF file
            self.file_utils.validate_pdf_file(pdf_file)

            # Create temporary directory for processing
            temp_dir = self.file_utils.create_temp_directory(f"exam_{exam_id}_")

            # Save PDF file to temporary location for processing
            filename = f"exam_{exam_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            temp_file_path = self.file_utils.save_to_temp(pdf_file, temp_dir, filename)

            # Process PDF with LLM to extract questions
            processed_exam = None
            try:
                processed_exam = await self.pdf_processor.process_pdf(temp_file_path, exam_id)

                # If processing succeeds, save to permanent location
                permanent_file_path = os.path.join(self.upload_dir, filename)
                shutil.copy2(temp_file_path, permanent_file_path)

                # Update exam with PDF information
                exam.pdf_filename = filename
                exam.questions_json = processed_exam
                exam.title = processed_exam.get("metadata", {}).get("title", exam.title)

                # Update exam status
                exam.status = "processed"

            except Exception as processing_error:
                # If processing fails, don't save to permanent location
                exam.status = "processing_failed"
                exam.questions_json = {
                    "error": str(processing_error),
                    "questions": [],
                    "total_questions": 0,
                    "processing_status": "failed"
                }

            self.db.commit()
            self.db.refresh(exam)

            result = {
                "exam_id": exam.id,
                "status": exam.status,
                "message": "PDF uploaded and processed successfully." if exam.status == "processed" else "PDF uploaded but processing failed.",
                "filename": filename if exam.status == "processed" else None,
                "total_questions": processed_exam.get("metadata", {}).get("total_questions", 0) if processed_exam and exam.status == "processed" else 0
            }

            # Add processed data if processing was successful
            if exam.status == "processed" and processed_exam:
                result["processed_data"] = processed_exam

            return result

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to upload PDF")
        finally:
            # Clean up temporary directory and files
            if temp_dir:
                self.file_utils.cleanup_temp_directory(temp_dir)

    def update_exam(self, exam_id: int, update_data: Dict[str, Any], user: User) -> Exam:
        """Update exam metadata."""
        try:
            exam = self.get_exam(exam_id, user)

            # Only admin or exam creator can update
            if user.role != "admin" and exam.created_by != user.id:
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
            if user.role != "admin" and exam.created_by != user.id:
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