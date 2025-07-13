from sqlalchemy import Column, Integer, String, Enum, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), index=True)
    role = Column(Enum(UserRole), default=UserRole.USER, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tests = relationship("Test", back_populates="created_by_user")
    test_attempts = relationship("TestAttempt", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"