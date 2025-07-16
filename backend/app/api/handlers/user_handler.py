from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from .base_handler import BaseHandler
from ...models import User, UserRole


class UserHandler(BaseHandler):
    """Handler for user-related operations."""

    def __init__(self, db: Session):
        super().__init__(db)

    def get_user_profile(self, user: User) -> Dict[str, Any]:
        """Get current user's profile information."""
        try:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get user profile")

    def update_user_profile(self, user: User, update_data: Dict[str, Any]) -> User:
        """Update current user's profile information."""
        try:
            # Update allowed fields
            allowed_fields = ["username", "email"]
            for field, value in update_data.items():
                if field in allowed_fields and value is not None:
                    # Check if username or email already exists
                    if field in ["username", "email"]:
                        existing_user = self.db.query(User).filter(
                            getattr(User, field) == value,
                            User.id != user.id
                        ).first()
                        if existing_user:
                            self.handle_error(
                                Exception(f"{field.capitalize()} already exists"),
                                status_code=400
                            )

                    setattr(user, field, value)

            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)

            return user
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to update user profile")

    def change_password(self, user: User, current_password: str, new_password: str) -> Dict[str, str]:
        """Change current user's password."""
        try:
            # Verify current password
            if not check_password_hash(user.password_hash, current_password):
                self.handle_error(Exception("Current password is incorrect"), status_code=400)

            # Validate new password
            if len(new_password) < 8:
                self.handle_error(Exception("New password must be at least 8 characters long"), status_code=400)

            # Hash new password
            new_password_hash = generate_password_hash(new_password)
            user.password_hash = new_password_hash
            user.updated_at = datetime.utcnow()

            self.db.commit()

            return {"message": "Password changed successfully"}
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to change password")

    def create_user(self, username: str, email: str, password: str, role: UserRole = UserRole.USER) -> User:
        """Create a new user (admin only)."""
        try:
            # Check if username or email already exists
            existing_user = self.db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                self.handle_error(Exception("Username or email already exists"), status_code=400)

            # Hash password
            password_hash = generate_password_hash(password)

            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role
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

    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        try:
            return self.validate_exists(User, user_id, "User not found")
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get user")

    def update_user(self, user_id: int, update_data: Dict[str, Any], requesting_user: User) -> User:
        """Update user information (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            user = self.get_user_by_id(user_id)

            # Update allowed fields
            allowed_fields = ["username", "email", "role"]
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

            user = self.get_user_by_id(user_id)

            self.db.delete(user)
            self.db.commit()

            return {"message": "User deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            self.handle_error(e, status_code=500, detail="Failed to delete user")

    def get_user_statistics(self, user_id: int, requesting_user: User) -> Dict[str, Any]:
        """Get user statistics (admin only)."""
        try:
            # Check if requesting user is admin
            if requesting_user.role != UserRole.ADMIN:
                self.handle_error(Exception("Access denied"), status_code=403)

            user = self.get_user_by_id(user_id)

            # Get user's test attempts
            from ...models import TestAttempt
            attempts = self.db.query(TestAttempt).filter(
                TestAttempt.user_id == user_id,
                TestAttempt.completed_at.isnot(None)
            ).all()

            # Calculate statistics
            total_attempts = len(attempts)
            total_score = sum(attempt.total_score for attempt in attempts)
            max_possible_score = sum(attempt.max_score for attempt in attempts)
            average_score = total_score / total_attempts if total_attempts > 0 else 0
            best_score = max(attempt.percentage for attempt in attempts if attempt.percentage) if attempts else 0

            return {
                "user_id": user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at.isoformat(),
                "statistics": {
                    "total_attempts": total_attempts,
                    "total_score": total_score,
                    "max_possible_score": max_possible_score,
                    "average_score": average_score,
                    "best_score": float(best_score) if best_score else 0,
                    "overall_percentage": (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Failed to get user statistics")