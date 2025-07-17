from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from .base_handler import BaseHandler
from ...models import User, Exam, ExamAttempt, QuestionResult, UserRole


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

    def create_user(self, username: str, email: str, password: str, requesting_user: User, first_name: str = None, last_name: str = None, role: str = "user") -> User:
        """Create a new user (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            # Check if username or email already exists
            existing_user = self.db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                self.handle_error(Exception("Username or email already exists"), status_code=400)

            # Hash password
            password_hash = generate_password_hash(password)

            # Parse role
            try:
                user_role = UserRole(role)
            except ValueError:
                self.handle_error(Exception("Invalid role"), status_code=400)

            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                role=user_role
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            return user
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to create user")

    def update_user(self, user_id: int, update_data: Dict[str, Any], requesting_user: User) -> User:
        """Update user information (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                self.handle_error(Exception("User not found"), status_code=404)

            # Update allowed fields
            allowed_fields = ["username", "email", "first_name", "last_name", "role", "status"]
            for field, value in update_data.items():
                if field in allowed_fields and value is not None:
                    # Check if username or email already exists
                    if field in ["username", "email"]:
                        existing_user = self.db.query(User).filter(
                            getattr(User, field) == value,
                            User.id != user_id
                        ).first()
                        if existing_user:
                            self.handle_error(
                                Exception(f"{field.capitalize()} already exists"),
                                status_code=400
                            )

                    # Handle role field
                    if field == "role":
                        try:
                            value = UserRole(value)
                        except ValueError:
                            self.handle_error(Exception("Invalid role"), status_code=400)

                    setattr(user, field, value)

            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)

            return user
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to update user")

    def delete_user(self, user_id: int, requesting_user: User) -> Dict[str, str]:
        """Delete a user (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            # Prevent admin from deleting themselves
            if user_id == requesting_user.id:
                self.handle_error(Exception("Cannot delete your own account"), status_code=400)

            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                self.handle_error(Exception("User not found"), status_code=404)

            self.db.delete(user)
            self.db.commit()

            return {"message": "User deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to delete user")

    def get_user_exam_history(self, user_id: int, requesting_user: User) -> Dict[str, Any]:
        """Get exam history for a specific user (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            # Get user's exam attempts
            attempts = self.db.query(ExamAttempt).filter(
                ExamAttempt.user_id == user_id,
                ExamAttempt.completed_at.isnot(None)
            ).order_by(desc(ExamAttempt.completed_at)).all()

            # Add exam details
            for attempt in attempts:
                exam = self.db.query(Exam).filter(Exam.id == attempt.exam_id).first()
                attempt.exam_title = exam.title if exam else "Unknown Exam"

            return {
                "user_id": user_id,
                "attempts": [
                    {
                        "attempt_id": attempt.id,
                        "exam_id": attempt.exam_id,
                        "exam_title": attempt.exam_title,
                        "score": attempt.total_score,
                        "max_score": attempt.max_score,
                        "percentage": float(attempt.percentage) if attempt.percentage else 0,
                        "started_at": attempt.started_at.isoformat(),
                        "completed_at": attempt.completed_at.isoformat()
                    }
                    for attempt in attempts
                ]
            }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get user exam history")