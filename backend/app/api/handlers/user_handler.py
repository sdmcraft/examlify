import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

async def create_user(
    username: str,
    email: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: str = "user",
    db: Session = None
) -> Dict[str, Any]:
    """Create a new user (admin only)."""
    try:
        if not db:
            db = next(get_db())

        # Check if username or email already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")

        # Hash password
        password_hash = generate_password_hash(password)

        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")

async def get_users(db: Session = None) -> List[Dict[str, Any]]:
    """Get all users (admin only)."""
    try:
        if not db:
            db = next(get_db())

        users = db.query(User).all()

        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ]
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get users")

async def get_user(user_id: int, db: Session = None) -> Dict[str, Any]:
    """Get user by ID (admin only)."""
    try:
        if not db:
            db = next(get_db())

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user")

async def update_user(
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = None
) -> Dict[str, Any]:
    """Update user (admin only)."""
    try:
        if not db:
            db = next(get_db())

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update fields if provided
        if username is not None:
            # Check if username already exists
            existing_user = db.query(User).filter(
                User.username == username,
                User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")
            user.username = username

        if email is not None:
            # Check if email already exists
            existing_user = db.query(User).filter(
                User.email == email,
                User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already exists")
            user.email = email

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        if role is not None:
            user.role = role

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {str(e)}")
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user")

async def delete_user(user_id: int, db: Session = None) -> Dict[str, str]:
    """Delete user (admin only)."""
    try:
        if not db:
            db = next(get_db())

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(user)
        db.commit()

        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {str(e)}")
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user")