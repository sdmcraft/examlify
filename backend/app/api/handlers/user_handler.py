from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from .base_handler import BaseHandler
from ...models import User


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