from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import json
import os
from datetime import datetime

from .base_handler import BaseHandler
from ...models import Test, User, UserRole


class TestHandler(BaseHandler):
    """Handler for test-related operations."""

    def __init__(self, db: Session):
        super().__init__(db)
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    def get_tests(self, user: User, status: Optional[str] = None) -> List[Test]:
        """Get list of tests available to the user."""
        try:
            query = self.db.query(Test)

            # Filter by status if provided
            if status:
                # Note: Test model doesn't have status field yet, this is for future implementation
                pass

            # For now, return all tests. In future, implement proper access control
            if user.role != UserRole.ADMIN:
                # Regular users can see tests they created or public tests
                query = query.filter(Test.created_by == user.id)

            return query.all()
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to fetch tests")

    def get_test(self, test_id: int, user: User) -> Test:
        """Get specific test details."""
        try:
            test = self.validate_exists(Test, test_id, "Test not found")

            # Check access permissions
            if user.role != UserRole.ADMIN and test.created_by != user.id:
                self.handle_error(Exception("Access denied"), status_code=403)

            return test
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to fetch test")

    def create_test(self, title: str, description: Optional[str], user: User) -> Test:
        """Create a new test."""
        try:
            test = Test(
                title=title,
                description=description,
                created_by=user.id
            )

            self.db.add(test)
            self.db.commit()
            self.db.refresh(test)

            return test
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to create test")

    def upload_pdf(self, test_id: int, pdf_file: UploadFile, user: User) -> Dict[str, Any]:
        """Upload and process PDF for a test."""
        try:
            test = self.get_test(test_id, user)

            # Validate file type
            if not pdf_file.filename.lower().endswith('.pdf'):
                self.handle_error(Exception("Only PDF files are allowed"), status_code=400)

            # Save PDF file
            filename = f"test_{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(self.upload_dir, filename)

            with open(file_path, "wb") as buffer:
                content = pdf_file.file.read()
                buffer.write(content)

            # Update test with PDF information
            test.pdf_filename = filename
            test.pdf_content = content

            # TODO: Process PDF with LLM to extract questions
            # For now, we'll create a placeholder questions structure
            questions_json = {
                "questions": [],
                "total_questions": 0,
                "processing_status": "pending"
            }

            test.questions_json = questions_json

            self.db.commit()
            self.db.refresh(test)

            return {
                "test_id": test.id,
                "status": "uploaded",
                "message": "PDF uploaded successfully. Processing will begin shortly.",
                "filename": filename
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to upload PDF")

    def update_test(self, test_id: int, update_data: Dict[str, Any], user: User) -> Test:
        """Update test metadata."""
        try:
            test = self.get_test(test_id, user)

            # Only admin or test creator can update
            if user.role != UserRole.ADMIN and test.created_by != user.id:
                self.handle_error(Exception("Access denied"), status_code=403)

            # Update allowed fields
            allowed_fields = ["title", "description"]
            for field, value in update_data.items():
                if field in allowed_fields and value is not None:
                    setattr(test, field, value)

            test.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(test)

            return test
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to update test")

    def delete_test(self, test_id: int, user: User) -> Dict[str, str]:
        """Delete a test."""
        try:
            test = self.get_test(test_id, user)

            # Only admin or test creator can delete
            if user.role != UserRole.ADMIN and test.created_by != user.id:
                self.handle_error(Exception("Access denied"), status_code=403)

            # Delete associated PDF file if exists
            if test.pdf_filename:
                file_path = os.path.join(self.upload_dir, test.pdf_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

            self.db.delete(test)
            self.db.commit()

            return {"message": "Test deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to delete test")

    def process_questions(self, test_id: int, user: User) -> Dict[str, Any]:
        """Process PDF to extract questions using LLM."""
        try:
            test = self.get_test(test_id, user)

            if not test.pdf_content:
                self.handle_error(Exception("No PDF content found"), status_code=400)

            # TODO: Implement LLM processing here
            # This would involve:
            # 1. Reading the PDF content
            # 2. Sending to LLM for question extraction
            # 3. Parsing the response
            # 4. Updating test.questions_json

            # Placeholder implementation
            questions_json = {
                "questions": [
                    {
                        "id": "q1",
                        "question": "Sample question extracted from PDF",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "subject": "Mathematics",
                        "topic": "Algebra"
                    }
                ],
                "total_questions": 1,
                "processing_status": "completed"
            }

            test.questions_json = questions_json
            self.db.commit()

            return {
                "status": "completed",
                "message": "Questions processed successfully",
                "total_questions": questions_json["total_questions"]
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to process questions")