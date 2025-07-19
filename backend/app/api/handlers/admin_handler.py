import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.exam import Exam

logger = logging.getLogger(__name__)

async def get_admin_stats(db: Session = None) -> Dict[str, Any]:
    """Get admin statistics (admin only)."""
    try:
        if not db:
            db = next(get_db())

        # Get basic statistics
        total_users = db.query(User).count()
        total_exams = db.query(Exam).count()

        # Get users by role
        admin_users = db.query(User).filter(User.role == "admin").count()
        regular_users = db.query(User).filter(User.role == "user").count()

        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = db.query(User).filter(User.created_at >= thirty_days_ago).count()
        recent_exams = db.query(Exam).filter(Exam.created_at >= thirty_days_ago).count()

        return {
            "total_users": total_users,
            "total_exams": total_exams,
            "admin_users": admin_users,
            "regular_users": regular_users,
            "recent_users_30_days": recent_users,
            "recent_exams_30_days": recent_exams,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get admin statistics")