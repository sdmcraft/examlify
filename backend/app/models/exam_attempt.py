from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer)
    answers_json = Column(JSON)
    total_score = Column(Integer)
    max_score = Column(Integer)
    percentage = Column(Numeric(5, 2))

    # Relationships
    user = relationship("User", back_populates="exam_attempts")
    exam = relationship("Exam", back_populates="exam_attempts")
    question_results = relationship("QuestionResult", back_populates="exam_attempt")

    def __repr__(self):
        return f"<ExamAttempt(id={self.id}, user_id={self.user_id}, exam_id={self.exam_id})>"