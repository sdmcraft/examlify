from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.api.handlers.auth_handler import get_current_user, login, logout
from app.api.handlers.exam_handler import (
    create_exam_with_pdf_url,
    get_exam,
    get_exams,
    delete_exam,
    CreateExamRequest,
    ExamResponse
)
from app.api.handlers.user_handler import create_user, get_users, get_user, update_user, delete_user
from app.api.handlers.admin_handler import get_admin_stats

router = APIRouter(prefix="/api")

# Authentication routes
@router.post("/auth/login")
async def login_endpoint(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    return await login(username, password, db)

@router.post("/auth/logout")
async def logout_endpoint(current_user: User = Depends(get_current_user)):
    return await logout()

# Exam routes
@router.post("/exams", response_model=ExamResponse)
async def create_exam_endpoint(
    request: CreateExamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new exam with PDF URL"""
    return await create_exam_with_pdf_url(request, current_user, db)

@router.get("/exams/{exam_id}", response_model=ExamResponse)
async def get_exam_endpoint(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get exam by ID"""
    return await get_exam(exam_id, current_user, db)

@router.get("/exams", response_model=List[ExamResponse])
async def get_exams_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all exams for the current user"""
    return await get_exams(current_user, db)

@router.delete("/exams/{exam_id}")
async def delete_exam_endpoint(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an exam"""
    return await delete_exam(exam_id, current_user, db)

# User management routes (admin only)
@router.post("/users")
async def create_user_endpoint(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    role: str = Form("user"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await create_user(username, email, password, first_name, last_name, role, db)

@router.get("/users")
async def get_users_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await get_users(db)

@router.get("/users/{user_id}")
async def get_user_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await get_user(user_id, db)

@router.put("/users/{user_id}")
async def update_user_endpoint(
    user_id: int,
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await update_user(user_id, username, email, first_name, last_name, role, db)

@router.delete("/users/{user_id}")
async def delete_user_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await delete_user(user_id, db)

# Admin routes
@router.get("/admin/stats")
async def admin_stats_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin statistics (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return await get_admin_stats(db)