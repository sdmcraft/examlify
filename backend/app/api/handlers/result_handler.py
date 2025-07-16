from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException
from datetime import datetime, timedelta

from .base_handler import BaseHandler
from ...models import TestAttempt, QuestionResult, Test, User


class ResultHandler(BaseHandler):
    """Handler for test results and analytics."""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_detailed_results(self, attempt_id: int, user: User) -> Dict[str, Any]:
        """Get comprehensive test results and analysis."""
        try:
            # Get test attempt
            attempt = self.db.query(TestAttempt).filter(
                TestAttempt.id == attempt_id,
                TestAttempt.user_id == user.id
            ).first()

            if not attempt:
                self.handle_error(Exception("Test attempt not found"), status_code=404)

            # Get test details
            test = self.db.query(Test).filter(Test.id == attempt.test_id).first()

            # Get question results
            question_results = self.db.query(QuestionResult).filter(
                QuestionResult.attempt_id == attempt_id
            ).all()

            # Calculate subject-wise performance
            subject_performance = {}
            for result in question_results:
                subject = result.subject or "Unknown"
                if subject not in subject_performance:
                    subject_performance[subject] = {
                        "total_questions": 0,
                        "correct_answers": 0,
                        "marks_obtained": 0,
                        "total_marks": 0
                    }

                subject_performance[subject]["total_questions"] += 1
                subject_performance[subject]["total_marks"] += 1
                if result.is_correct:
                    subject_performance[subject]["correct_answers"] += 1
                    subject_performance[subject]["marks_obtained"] += 1

            # Calculate percentages for subjects
            for subject, data in subject_performance.items():
                data["percentage"] = (data["marks_obtained"] / data["total_marks"] * 100) if data["total_marks"] > 0 else 0

            return {
                "attempt_id": attempt.id,
                "test": {
                    "id": test.id if test else None,
                    "title": test.title if test else None,
                    "description": test.description if test else None
                },
                "user": {
                    "id": user.id,
                    "username": user.username
                },
                "summary": {
                    "total_score": attempt.total_score,
                    "max_score": attempt.max_score,
                    "percentage": float(attempt.percentage) if attempt.percentage else 0,
                    "started_at": attempt.started_at.isoformat(),
                    "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
                    "duration_seconds": attempt.duration_seconds
                },
                "question_results": [
                    {
                        "question_id": result.question_id,
                        "user_answer": result.user_answer,
                        "correct_answer": result.correct_answer,
                        "is_correct": result.is_correct,
                        "marks_obtained": result.marks_obtained,
                        "subject": result.subject,
                        "topic": result.topic
                    }
                    for result in question_results
                ],
                "subject_performance": subject_performance
            }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get detailed results")

    def get_test_history(self, user: User) -> List[TestAttempt]:
        """Get user's test attempt history."""
        try:
            attempts = self.db.query(TestAttempt).filter(
                TestAttempt.user_id == user.id,
                TestAttempt.completed_at.isnot(None)
            ).order_by(desc(TestAttempt.completed_at)).all()

            # Add test details to each attempt
            for attempt in attempts:
                test = self.db.query(Test).filter(Test.id == attempt.test_id).first()
                attempt.test_title = test.title if test else "Unknown Test"

            return attempts
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get test history")

    def get_performance_summary(self, user: User) -> Dict[str, Any]:
        """Get overall performance analytics and trends."""
        try:
            # Get all completed attempts
            attempts = self.db.query(TestAttempt).filter(
                TestAttempt.user_id == user.id,
                TestAttempt.completed_at.isnot(None)
            ).all()

            if not attempts:
                return {
                    "total_tests": 0,
                    "average_score": 0,
                    "best_score": 0,
                    "total_questions": 0,
                    "correct_answers": 0,
                    "subject_performance": {},
                    "recent_trends": []
                }

            # Calculate overall statistics
            total_tests = len(attempts)
            total_score = sum(attempt.total_score for attempt in attempts)
            max_possible_score = sum(attempt.max_score for attempt in attempts)
            average_score = total_score / total_tests if total_tests > 0 else 0
            best_score = max(attempt.percentage for attempt in attempts if attempt.percentage)

            # Get question-level statistics
            question_results = self.db.query(QuestionResult).join(TestAttempt).filter(
                TestAttempt.user_id == user.id
            ).all()

            total_questions = len(question_results)
            correct_answers = sum(1 for result in question_results if result.is_correct)

            # Calculate subject-wise performance
            subject_stats = {}
            for result in question_results:
                subject = result.subject or "Unknown"
                if subject not in subject_stats:
                    subject_stats[subject] = {"total": 0, "correct": 0}

                subject_stats[subject]["total"] += 1
                if result.is_correct:
                    subject_stats[subject]["correct"] += 1

            # Calculate percentages for subjects
            subject_performance = {}
            for subject, stats in subject_stats.items():
                subject_performance[subject] = {
                    "total_questions": stats["total"],
                    "correct_answers": stats["correct"],
                    "percentage": (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
                }

            # Get recent trends (last 10 attempts)
            recent_attempts = self.db.query(TestAttempt).filter(
                TestAttempt.user_id == user.id,
                TestAttempt.completed_at.isnot(None)
            ).order_by(desc(TestAttempt.completed_at)).limit(10).all()

            recent_trends = [
                {
                    "attempt_id": attempt.id,
                    "test_id": attempt.test_id,
                    "score": attempt.total_score,
                    "percentage": float(attempt.percentage) if attempt.percentage else 0,
                    "completed_at": attempt.completed_at.isoformat()
                }
                for attempt in recent_attempts
            ]

            return {
                "total_tests": total_tests,
                "average_score": average_score,
                "best_score": float(best_score) if best_score else 0,
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "overall_percentage": (correct_answers / total_questions * 100) if total_questions > 0 else 0,
                "subject_performance": subject_performance,
                "recent_trends": recent_trends
            }
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get performance summary")