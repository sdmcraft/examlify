from sqlalchemy import Column, Integer, String, Text, LargeBinary, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    pdf_content = Column(LargeBinary)
    pdf_filename = Column(String(255))
    questions_json = Column(JSON)
    created_by = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="tests")
    test_attempts = relationship("TestAttempt", back_populates="test")

    def __repr__(self):
        return f"<Test(id={self.id}, title='{self.title}', created_by={self.created_by})>"