from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..database import Base

class QuestionResult(Base):
    __tablename__ = "question_results"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False, index=True)
    question_id = Column(String(50), nullable=False, index=True)
    user_answer = Column(String(10))
    correct_answer = Column(String(10))
    is_correct = Column(Boolean, index=True)
    marks_obtained = Column(Integer)
    subject = Column(String(100), index=True)
    topic = Column(String(100), index=True)

    # Relationships
    test_attempt = relationship("TestAttempt", back_populates="question_results")

    def __repr__(self):
        return f"<QuestionResult(id={self.id}, attempt_id={self.attempt_id}, question_id='{self.question_id}')>"