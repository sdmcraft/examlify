from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer)
    pdf_filename = Column(String(255))
    pdf_content = Column(JSON)
    questions_json = Column(JSON)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="exams")
    exam_attempts = relationship("ExamAttempt", back_populates="exam")

    def __repr__(self):
        return f"<Exam(id={self.id}, title='{self.title}', created_by={self.created_by})>"