from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..database import get_db
from ..models import User
from .handlers import (
    AuthHandler, TestHandler, SessionHandler,
    ResultHandler, UserHandler, AdminHandler
)

# Security
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/api", tags=["API"])

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class SuccessResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    auth_handler = AuthHandler(db)
    return auth_handler.get_current_user(credentials.credentials)

# Authentication routes
@router.post("/auth/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """User login endpoint."""
    auth_handler = AuthHandler(db)
    return auth_handler.login(login_data.username, login_data.password)

@router.post("/auth/logout", response_model=SuccessResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User logout endpoint."""
    auth_handler = AuthHandler(db)
    return auth_handler.logout("")  # Token is handled by dependency

@router.get("/auth/status")
async def check_auth_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check authentication status."""
    auth_handler = AuthHandler(db)
    return auth_handler.check_auth_status("")  # Token is handled by dependency

# Test routes
@router.get("/tests")
async def get_tests(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available tests."""
    test_handler = TestHandler(db)
    return test_handler.get_tests(current_user, status)

@router.post("/tests")
async def create_test(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new test."""
    test_handler = TestHandler(db)
    test = test_handler.create_test(title, description, current_user)
    return test

@router.post("/tests/upload")
async def upload_pdf(
    test_id: int = Form(...),
    pdf_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process PDF for a test."""
    test_handler = TestHandler(db)
    return test_handler.upload_pdf(test_id, pdf_file, current_user)

@router.get("/tests/{test_id}")
async def get_test(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific test details."""
    test_handler = TestHandler(db)
    return test_handler.get_test(test_id, current_user)

@router.put("/tests/{test_id}")
async def update_test(
    test_id: int,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update test metadata."""
    test_handler = TestHandler(db)
    return test_handler.update_test(test_id, update_data, current_user)

@router.delete("/tests/{test_id}")
async def delete_test(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a test."""
    test_handler = TestHandler(db)
    return test_handler.delete_test(test_id, current_user)

# Test session routes
@router.post("/tests/{test_id}/start")
async def start_test_session(
    test_id: int,
    duration_minutes: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new test attempt session."""
    session_handler = SessionHandler(db)
    return session_handler.start_test_session(test_id, current_user, duration_minutes)

@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current session status."""
    session_handler = SessionHandler(db)
    return session_handler.get_session_status(session_id, current_user)

@router.post("/sessions/{session_id}/hint/{question_id}")
async def get_hint(
    session_id: int,
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get hint for a specific question."""
    session_handler = SessionHandler(db)
    return session_handler.get_hint(session_id, question_id, current_user)

@router.post("/sessions/{session_id}/solution/{question_id}")
async def get_solution(
    session_id: int,
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed solution for a specific question."""
    session_handler = SessionHandler(db)
    return session_handler.get_solution(session_id, question_id, current_user)

@router.post("/tests/{test_id}/submit")
async def submit_test(
    test_id: int,
    session_id: int,
    answers: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit completed test."""
    session_handler = SessionHandler(db)
    return session_handler.submit_test(test_id, session_id, answers, current_user)

# Results routes
@router.get("/results/{attempt_id}")
async def get_detailed_results(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed test results."""
    result_handler = ResultHandler(db)
    return result_handler.get_detailed_results(attempt_id, current_user)

@router.get("/results/history")
async def get_test_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's test attempt history."""
    result_handler = ResultHandler(db)
    return result_handler.get_test_history(current_user)

@router.get("/results/summary")
async def get_performance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall performance analytics."""
    result_handler = ResultHandler(db)
    return result_handler.get_performance_summary(current_user)

# User routes
@router.get("/users/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile."""
    user_handler = UserHandler(db)
    return user_handler.get_user_profile(current_user)

@router.put("/users/profile")
async def update_user_profile(
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    user_handler = UserHandler(db)
    return user_handler.update_user_profile(current_user, update_data)

@router.put("/users/password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    user_handler = UserHandler(db)
    return user_handler.change_password(current_user, current_password, new_password)

@router.get("/users/{user_id}/history")
async def get_user_test_history(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get test history for a specific user (admin only)."""
    result_handler = ResultHandler(db)
    return result_handler.get_user_test_history(user_id, current_user)

# Admin routes
@router.get("/admin/users")
async def get_all_users(
    role: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all users (admin only)."""
    admin_handler = AdminHandler(db)
    return admin_handler.get_all_users(current_user, role)

@router.post("/admin/users")
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    user_handler = UserHandler(db)
    from ..models import UserRole
    user_role = UserRole(role) if role else UserRole.USER
    return user_handler.create_user(username, email, password, user_role)

@router.get("/admin/users/{user_id}")
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)."""
    user_handler = UserHandler(db)
    return user_handler.get_user_by_id(user_id)

@router.put("/admin/users/{user_id}")
async def update_user(
    user_id: int,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user information (admin only)."""
    user_handler = UserHandler(db)
    return user_handler.update_user(user_id, update_data, current_user)

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    user_handler = UserHandler(db)
    return user_handler.delete_user(user_id, current_user)

@router.get("/admin/users/{user_id}/statistics")
async def get_user_statistics(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics (admin only)."""
    user_handler = UserHandler(db)
    return user_handler.get_user_statistics(user_id, current_user)

@router.get("/admin/statistics")
async def get_system_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall system statistics (admin only)."""
    admin_handler = AdminHandler(db)
    return admin_handler.get_system_statistics(current_user)

@router.get("/admin/analytics/tests")
async def get_test_analytics(
    test_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get test analytics (admin only)."""
    admin_handler = AdminHandler(db)
    return admin_handler.get_test_analytics(current_user, test_id)

@router.get("/admin/activity")
async def get_user_activity_log(
    user_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user activity log (admin only)."""
    admin_handler = AdminHandler(db)
    return admin_handler.get_user_activity_log(current_user, user_id, days)