from typing import Optional, Any, Dict, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel


class BaseHandler:
    """Base handler class providing common functionality for all API handlers."""

    def __init__(self, db: Session):
        self.db = db

    def handle_error(self, error: Exception, status_code: int = 500, detail: str = None) -> None:
        """Handle errors and raise appropriate HTTP exceptions."""
        if detail is None:
            detail = str(error)
        raise HTTPException(status_code=status_code, detail=detail)

    def validate_exists(self, model, id: int, error_message: str = "Resource not found") -> Any:
        """Validate that a resource exists in the database."""
        resource = self.db.query(model).filter(model.id == id).first()
        if not resource:
            self.handle_error(Exception(error_message), status_code=404)
        return resource

