from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta
import json

from .base_handler import BaseHandler
from ...models import TestAttempt, Test, User, QuestionResult


class SessionHandler(BaseHandler):
    """Handler for test session-related operations."""

    def __init__(self, db: Session):
        super().__init__(db)

    def start_test_session(self, test_id: int, user: User, duration_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Start a new test attempt session."""
        try:
            # Get test details
            test = self.db.query(Test).filter(Test.id == test_id).first()
            if not test:
                self.handle_error(Exception("Test not found"), status_code=404)

            # Check if user has already started this test
            existing_attempt = self.db.query(TestAttempt).filter(
                TestAttempt.user_id == user.id,
                TestAttempt.test_id == test_id,
                TestAttempt.completed_at.is_(None)
            ).first()

            if existing_attempt:
                self.handle_error(Exception("Test already in progress"), status_code=400)

            # Create new test attempt
            test_attempt = TestAttempt(
                user_id=user.id,
                test_id=test_id,
                started_at=datetime.utcnow(),
                duration_seconds=duration_minutes * 60 if duration_minutes else None
            )

            self.db.add(test_attempt)
            self.db.commit()
            self.db.refresh(test_attempt)

            # Calculate expiry time
            expires_at = None
            if duration_minutes:
                expires_at = test_attempt.started_at + timedelta(minutes=duration_minutes)

            return {
                "session_id": test_attempt.id,
                "test": {
                    "id": test.id,
                    "title": test.title,
                    "description": test.description,
                    "questions": test.questions_json
                },
                "started_at": test_attempt.started_at.isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to start test session")

    def get_session_status(self, session_id: int, user: User) -> Dict[str, Any]:
        """Get current session status and progress."""
        try:
            attempt = self.db.query(TestAttempt).filter(
                TestAttempt.id == session_id,
                TestAttempt.user_id == user.id
            ).first()

            if not attempt:
                self.handle_error(Exception("Session not found"), status_code=404)

            test = self.db.query(Test).filter(Test.id == attempt.test_id).first()

            # Calculate time remaining
            time_remaining = None
            if attempt.duration_seconds:
                elapsed = (datetime.utcnow() - attempt.started_at).total_seconds()
                time_remaining = max(0, attempt.duration_seconds - elapsed)

            return {
                "session_id": attempt.id,
                "test_id": attempt.test_id,
                "test_title": test.title if test else None,
                "started_at": attempt.started_at.isoformat(),
                "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
                "time_remaining": time_remaining,
                "is_completed": attempt.completed_at is not None
            }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get session status")

    def submit_test(self, test_id: int, session_id: int, answers: Dict[str, str], user: User) -> Dict[str, Any]:
        """Submit completed test and calculate results."""
        try:
            # Validate session
            attempt = self.db.query(TestAttempt).filter(
                TestAttempt.id == session_id,
                TestAttempt.user_id == user.id,
                TestAttempt.test_id == test_id,
                TestAttempt.completed_at.is_(None)
            ).first()

            if not attempt:
                self.handle_error(Exception("Invalid or completed session"), status_code=400)

            # Get test details
            test = self.db.query(Test).filter(Test.id == test_id).first()
            if not test or not test.questions_json:
                self.handle_error(Exception("Test questions not found"), status_code=400)

            # Calculate results
            questions = test.questions_json.get("questions", [])
            total_score = 0
            max_score = len(questions)
            question_results = []

            for question in questions:
                question_id = question.get("id")
                user_answer = answers.get(question_id)
                correct_answer = question.get("correct_answer")

                is_correct = user_answer == correct_answer
                marks_obtained = 1 if is_correct else 0
                total_score += marks_obtained

                # Create question result
                question_result = QuestionResult(
                    attempt_id=attempt.id,
                    question_id=question_id,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    is_correct=is_correct,
                    marks_obtained=marks_obtained,
                    subject=question.get("subject"),
                    topic=question.get("topic")
                )

                question_results.append(question_result)

            # Calculate percentage
            percentage = (total_score / max_score * 100) if max_score > 0 else 0

            # Update test attempt
            attempt.completed_at = datetime.utcnow()
            attempt.answers_json = answers
            attempt.total_score = total_score
            attempt.max_score = max_score
            attempt.percentage = percentage

            # Add question results
            self.db.add_all(question_results)

            self.db.commit()
            self.db.refresh(attempt)

            return {
                "attempt_id": attempt.id,
                "score": total_score,
                "max_score": max_score,
                "percentage": float(percentage),
                "completed_at": attempt.completed_at.isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to submit test")

    def get_hint(self, session_id: int, question_id: str, user: User) -> Dict[str, Any]:
        """Get hint for a specific question."""
        try:
            # Validate session
            attempt = self.db.query(TestAttempt).filter(
                TestAttempt.id == session_id,
                TestAttempt.user_id == user.id,
                TestAttempt.completed_at.is_(None)
            ).first()

            if not attempt:
                self.handle_error(Exception("Invalid or completed session"), status_code=400)

            # Get test and question details
            test = self.db.query(Test).filter(Test.id == attempt.test_id).first()
            if not test or not test.questions_json:
                self.handle_error(Exception("Test questions not found"), status_code=400)

            questions = test.questions_json.get("questions", [])
            question = next((q for q in questions if q.get("id") == question_id), None)

            if not question:
                self.handle_error(Exception("Question not found"), status_code=404)

            # TODO: Implement hint generation using LLM
            # For now, return a placeholder hint
            hint = f"Hint for question {question_id}: Think about the key concepts in {question.get('topic', 'this topic')}."

            return {
                "hint": hint,
                "used_hint": True
            }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get hint")

    def get_solution(self, session_id: int, question_id: str, user: User) -> Dict[str, Any]:
        """Get detailed solution for a specific question."""
        try:
            # Validate session
            attempt = self.db.query(TestAttempt).filter(
                TestAttempt.id == session_id,
                TestAttempt.user_id == user.id,
                TestAttempt.completed_at.is_(None)
            ).first()

            if not attempt:
                self.handle_error(Exception("Invalid or completed session"), status_code=400)

            # Get test and question details
            test = self.db.query(Test).filter(Test.id == attempt.test_id).first()
            if not test or not test.questions_json:
                self.handle_error(Exception("Test questions not found"), status_code=400)

            questions = test.questions_json.get("questions", [])
            question = next((q for q in questions if q.get("id") == question_id), None)

            if not question:
                self.handle_error(Exception("Question not found"), status_code=404)

            # TODO: Implement solution generation using LLM
            # For now, return the correct answer and a placeholder solution
            solution = f"Detailed solution for question {question_id}: The correct answer is {question.get('correct_answer')}. This involves understanding the concepts in {question.get('topic', 'this topic')}."

            return {
                "correct_answer": question.get("correct_answer"),
                "detailed_solution": solution,
                "used_solution": True
            }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get solution")