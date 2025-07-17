from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..database import Base

class QuestionResult(Base):
    __tablename__ = "question_results"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), nullable=False, index=True)
    question_id = Column(String(50), nullable=False)
    user_answer = Column(String(10))
    correct_answer = Column(String(10))
    is_correct = Column(Boolean, default=False)
    marks_obtained = Column(Numeric(5, 2), default=0)
    subject = Column(String(100))
    topic = Column(String(100))

    # Relationships
    exam_attempt = relationship("ExamAttempt", back_populates="question_results")

    def __repr__(self):
        return f"<QuestionResult(id={self.id}, attempt_id={self.attempt_id}, question_id='{self.question_id}')>"