from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..database import get_db
from ..models import User
from .handlers import (
    AuthHandler, ExamHandler, SessionHandler,
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

class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class SubmitExamRequest(BaseModel):
    session_id: str
    answers: Dict[str, str]

class StartSessionRequest(BaseModel):
    duration_minutes: Optional[int] = None

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

# Exam routes
@router.get("/exams")
async def get_exams(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available exams."""
    exam_handler = ExamHandler(db)
    return exam_handler.get_exams(current_user, status)

@router.post("/exams/upload")
async def upload_pdf(
    pdf_file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    duration_minutes: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process PDF for an exam."""
    exam_handler = ExamHandler(db)
    # Create exam first
    exam = exam_handler.create_exam(title, description, current_user)
    # Then upload PDF
    return exam_handler.upload_pdf(exam.id, pdf_file, current_user)

@router.get("/exams/{exam_id}")
async def get_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific exam details."""
    exam_handler = ExamHandler(db)
    return exam_handler.get_exam(exam_id, current_user)

@router.put("/exams/{exam_id}")
async def update_exam(
    exam_id: int,
    update_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update exam metadata."""
    exam_handler = ExamHandler(db)
    return exam_handler.update_exam(exam_id, update_data, current_user)

@router.delete("/exams/{exam_id}")
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an exam."""
    exam_handler = ExamHandler(db)
    return exam_handler.delete_exam(exam_id, current_user)

# Exam session routes
@router.post("/exams/{exam_id}/start")
async def start_exam_session(
    exam_id: int,
    session_data: StartSessionRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new exam attempt session."""
    session_handler = SessionHandler(db)
    return session_handler.start_exam_session(exam_id, current_user, session_data.duration_minutes)

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

@router.post("/exams/{exam_id}/submit")
async def submit_exam(
    exam_id: int,
    submit_data: SubmitExamRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit completed exam."""
    session_handler = SessionHandler(db)
    return session_handler.submit_exam(exam_id, int(submit_data.session_id), submit_data.answers, current_user)

# Results routes
@router.get("/results/{attempt_id}")
async def get_detailed_results(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed exam results."""
    result_handler = ResultHandler(db)
    return result_handler.get_detailed_results(attempt_id, current_user)

@router.get("/results/history")
async def get_exam_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's exam attempt history."""
    result_handler = ResultHandler(db)
    return result_handler.get_exam_history(current_user)

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
    profile_data: UpdateProfileRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    user_handler = UserHandler(db)
    return user_handler.update_user_profile(current_user, profile_data.dict(exclude_unset=True))

@router.put("/users/password")
async def change_password(
    password_data: ChangePasswordRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    user_handler = UserHandler(db)
    return user_handler.change_password(current_user, password_data.current_password, password_data.new_password)

@router.get("/users/{user_id}/history")
async def get_user_exam_history(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get exam history for a specific user (admin only)."""
    admin_handler = AdminHandler(db)
    return admin_handler.get_user_exam_history(user_id, current_user)

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
    user_data: CreateUserRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    admin_handler = AdminHandler(db)
    return admin_handler.create_user(
        user_data.username,
        user_data.email,
        user_data.password,
        current_user,
        user_data.first_name,
        user_data.last_name,
        user_data.role
    )

@router.put("/admin/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UpdateUserRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user information (admin only)."""
    admin_handler = AdminHandler(db)
    return admin_handler.update_user(user_id, user_data.dict(exclude_unset=True), current_user)

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    admin_handler = AdminHandler(db)
    return admin_handler.delete_user(user_id, current_user)