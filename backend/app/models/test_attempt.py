from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer)
    answers_json = Column(JSON)
    total_score = Column(Integer)
    max_score = Column(Integer)
    percentage = Column(Numeric(5, 2))

    # Relationships
    user = relationship("User", back_populates="test_attempts")
    test = relationship("Test", back_populates="test_attempts")
    question_results = relationship("QuestionResult", back_populates="test_attempt")

    def __repr__(self):
        return f"<TestAttempt(id={self.id}, user_id={self.user_id}, test_id={self.test_id})>"