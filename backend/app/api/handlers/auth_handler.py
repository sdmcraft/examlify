import logging
import traceback
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import jwt
import os

from .base_handler import BaseHandler
from ...models import User

# Set up logging
logger = logging.getLogger(__name__)


class AuthHandler(BaseHandler):
    """Handler for authentication-related operations."""

    def __init__(self, db: Session):
        super().__init__(db)
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 365 * 24 * 60))  # 365 days default

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return access token."""
        try:
            # Find user by username or email
            user = self.db.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()

            if not user:
                self.handle_error(Exception("Invalid credentials"), status_code=401)

            if not check_password_hash(user.password_hash, password):
                self.handle_error(Exception("Invalid credentials"), status_code=401)

            # Generate access token
            access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
            access_token = self._create_access_token(
                data={"sub": str(user.id), "username": user.username, "role": user.role},
                expires_delta=access_token_expires
            )

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Login failed")

    def logout(self, token: str) -> Dict[str, str]:
        """Logout user by invalidating token (in a real app, you'd add to blacklist)."""
        try:
            # In a production app, you would add the token to a blacklist
            # For now, we'll just return success
            return {"message": "Successfully logged out"}
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Logout failed")

    def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                self.handle_error(Exception("Invalid token"), status_code=401)

            user = self.db.query(User).filter(User.id == int(user_id)).first()
            if user is None:
                self.handle_error(Exception("User not found"), status_code=401)

            return user
        except jwt.ExpiredSignatureError:
            self.handle_error(Exception("Token has expired"), status_code=401)
        except jwt.PyJWTError:
            self.handle_error(Exception("Invalid token"), status_code=401)
        except Exception as e:
            self.handle_error(e, status_code=500, detail="Authentication failed")

    def check_auth_status(self, token: str) -> Dict[str, Any]:
        """Check if current session is valid."""
        try:
            user = self.get_current_user(token)
            return {
                "authenticated": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }
        except HTTPException:
            return {"authenticated": False, "user": None}

    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt