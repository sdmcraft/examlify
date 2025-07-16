from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException
from datetime import datetime, timedelta

from .base_handler import BaseHandler
from ...models import User, Test, TestAttempt, QuestionResult, UserRole


class AdminHandler(BaseHandler):
    """Handler for admin-specific operations."""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_all_users(self, requesting_user: User, role: Optional[str] = None) -> List[User]:
        """Get list of all users in the system (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            query = self.db.query(User)

            # Filter by role if provided
            if role:
                try:
                    user_role = UserRole(role)
                    query = query.filter(User.role == user_role)
                except ValueError:
                    self.handle_error(Exception("Invalid role"), status_code=400)

            return query.order_by(desc(User.created_at)).all()
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to fetch users")

    def get_system_statistics(self, requesting_user: User) -> Dict[str, Any]:
        """Get overall system statistics (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            # User statistics
            total_users = self.db.query(User).count()
            admin_users = self.db.query(User).filter(User.role == UserRole.ADMIN).count()
            regular_users = total_users - admin_users

            # Test statistics
            total_tests = self.db.query(Test).count()
            tests_with_pdf = self.db.query(Test).filter(Test.pdf_content.isnot(None)).count()

            # Test attempt statistics
            total_attempts = self.db.query(TestAttempt).count()
            completed_attempts = self.db.query(TestAttempt).filter(TestAttempt.completed_at.isnot(None)).count()

            # Question statistics
            total_questions = self.db.query(QuestionResult).count()
            correct_answers = self.db.query(QuestionResult).filter(QuestionResult.is_correct == True).count()

            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_users = self.db.query(User).filter(User.created_at >= thirty_days_ago).count()
            recent_tests = self.db.query(Test).filter(Test.created_at >= thirty_days_ago).count()
            recent_attempts = self.db.query(TestAttempt).filter(TestAttempt.started_at >= thirty_days_ago).count()

            # Top performing users (by average score)
            top_users = self.db.query(
                User.username,
                func.avg(TestAttempt.percentage).label('avg_percentage'),
                func.count(TestAttempt.id).label('total_attempts')
            ).join(TestAttempt).filter(
                TestAttempt.completed_at.isnot(None)
            ).group_by(User.id, User.username).order_by(
                desc(func.avg(TestAttempt.percentage))
            ).limit(10).all()

            # Most popular tests
            popular_tests = self.db.query(
                Test.title,
                func.count(TestAttempt.id).label('attempt_count'),
                func.avg(TestAttempt.percentage).label('avg_percentage')
            ).join(TestAttempt).group_by(Test.id, Test.title).order_by(
                desc(func.count(TestAttempt.id))
            ).limit(10).all()

            return {
                "user_statistics": {
                    "total_users": total_users,
                    "admin_users": admin_users,
                    "regular_users": regular_users,
                    "recent_users": recent_users
                },
                "test_statistics": {
                    "total_tests": total_tests,
                    "tests_with_pdf": tests_with_pdf,
                    "recent_tests": recent_tests
                },
                "attempt_statistics": {
                    "total_attempts": total_attempts,
                    "completed_attempts": completed_attempts,
                    "completion_rate": (completed_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                    "recent_attempts": recent_attempts
                },
                "question_statistics": {
                    "total_questions": total_questions,
                    "correct_answers": correct_answers,
                    "accuracy_rate": (correct_answers / total_questions * 100) if total_questions > 0 else 0
                },
                "top_performing_users": [
                    {
                        "username": user.username,
                        "average_percentage": float(user.avg_percentage) if user.avg_percentage else 0,
                        "total_attempts": user.total_attempts
                    }
                    for user in top_users
                ],
                "most_popular_tests": [
                    {
                        "title": test.title,
                        "attempt_count": test.attempt_count,
                        "average_percentage": float(test.avg_percentage) if test.avg_percentage else 0
                    }
                    for test in popular_tests
                ]
            }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get system statistics")

    def get_test_analytics(self, requesting_user: User, test_id: Optional[int] = None) -> Dict[str, Any]:
        """Get detailed test analytics (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            if test_id:
                # Get analytics for specific test
                test = self.db.query(Test).filter(Test.id == test_id).first()
                if not test:
                    self.handle_error(Exception("Test not found"), status_code=404)

                attempts = self.db.query(TestAttempt).filter(TestAttempt.test_id == test_id).all()

                if not attempts:
                    return {
                        "test_id": test_id,
                        "test_title": test.title,
                        "total_attempts": 0,
                        "average_score": 0,
                        "question_analytics": []
                    }

                # Calculate test-level statistics
                total_attempts = len(attempts)
                completed_attempts = len([a for a in attempts if a.completed_at])
                average_score = sum(a.total_score for a in attempts if a.total_score) / completed_attempts if completed_attempts > 0 else 0
                average_percentage = sum(a.percentage for a in attempts if a.percentage) / completed_attempts if completed_attempts > 0 else 0

                # Get question-level analytics
                question_results = self.db.query(QuestionResult).join(TestAttempt).filter(
                    TestAttempt.test_id == test_id
                ).all()

                question_analytics = {}
                for result in question_results:
                    question_id = result.question_id
                    if question_id not in question_analytics:
                        question_analytics[question_id] = {
                            "total_attempts": 0,
                            "correct_answers": 0,
                            "incorrect_answers": 0,
                            "accuracy_rate": 0
                        }

                    question_analytics[question_id]["total_attempts"] += 1
                    if result.is_correct:
                        question_analytics[question_id]["correct_answers"] += 1
                    else:
                        question_analytics[question_id]["incorrect_answers"] += 1

                # Calculate accuracy rates
                for question_id, stats in question_analytics.items():
                    stats["accuracy_rate"] = (stats["correct_answers"] / stats["total_attempts"] * 100) if stats["total_attempts"] > 0 else 0

                return {
                    "test_id": test_id,
                    "test_title": test.title,
                    "total_attempts": total_attempts,
                    "completed_attempts": completed_attempts,
                    "completion_rate": (completed_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                    "average_score": average_score,
                    "average_percentage": float(average_percentage) if average_percentage else 0,
                    "question_analytics": question_analytics
                }
            else:
                # Get analytics for all tests
                tests = self.db.query(Test).all()
                test_analytics = []

                for test in tests:
                    attempts = self.db.query(TestAttempt).filter(TestAttempt.test_id == test.id).all()
                    completed_attempts = [a for a in attempts if a.completed_at]

                    if completed_attempts:
                        average_score = sum(a.total_score for a in completed_attempts) / len(completed_attempts)
                        average_percentage = sum(a.percentage for a in completed_attempts if a.percentage) / len(completed_attempts)
                    else:
                        average_score = 0
                        average_percentage = 0

                    test_analytics.append({
                        "test_id": test.id,
                        "test_title": test.title,
                        "total_attempts": len(attempts),
                        "completed_attempts": len(completed_attempts),
                        "average_score": average_score,
                        "average_percentage": float(average_percentage) if average_percentage else 0
                    })

                return {
                    "test_analytics": test_analytics
                }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get test analytics")

    def get_user_activity_log(self, requesting_user: User, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get user activity log (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            start_date = datetime.utcnow() - timedelta(days=days)

            if user_id:
                # Get activity for specific user
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    self.handle_error(Exception("User not found"), status_code=404)

                # Get test attempts
                attempts = self.db.query(TestAttempt).filter(
                    TestAttempt.user_id == user_id,
                    TestAttempt.started_at >= start_date
                ).order_by(desc(TestAttempt.started_at)).all()

                # Get tests created
                tests_created = self.db.query(Test).filter(
                    Test.created_by == user_id,
                    Test.created_at >= start_date
                ).order_by(desc(Test.created_at)).all()

                return {
                    "user_id": user_id,
                    "username": user.username,
                    "activity_period": f"Last {days} days",
                    "test_attempts": [
                        {
                            "attempt_id": attempt.id,
                            "test_id": attempt.test_id,
                            "started_at": attempt.started_at.isoformat(),
                            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
                            "score": attempt.total_score,
                            "percentage": float(attempt.percentage) if attempt.percentage else 0
                        }
                        for attempt in attempts
                    ],
                    "tests_created": [
                        {
                            "test_id": test.id,
                            "title": test.title,
                            "created_at": test.created_at.isoformat()
                        }
                        for test in tests_created
                    ]
                }
            else:
                # Get activity for all users
                recent_attempts = self.db.query(TestAttempt).filter(
                    TestAttempt.started_at >= start_date
                ).order_by(desc(TestAttempt.started_at)).limit(100).all()

                recent_tests = self.db.query(Test).filter(
                    Test.created_at >= start_date
                ).order_by(desc(Test.created_at)).limit(50).all()

                return {
                    "activity_period": f"Last {days} days",
                    "recent_attempts": [
                        {
                            "attempt_id": attempt.id,
                            "user_id": attempt.user_id,
                            "test_id": attempt.test_id,
                            "started_at": attempt.started_at.isoformat(),
                            "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None
                        }
                        for attempt in recent_attempts
                    ],
                    "recent_tests": [
                        {
                            "test_id": test.id,
                            "title": test.title,
                            "created_by": test.created_by,
                            "created_at": test.created_at.isoformat()
                        }
                        for test in recent_tests
                    ]
                }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get user activity log")