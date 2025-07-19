from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(String(10), default="user")  # Simple string: "admin" or "user"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    exams = relationship("Exam", back_populates="created_by_user")
    exam_attempts = relationship("ExamAttempt", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"