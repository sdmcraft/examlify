#!/usr/bin/env python3
"""
Simple script to test database connection and models
"""

from app.database import engine, SessionLocal, Base
from app.models import User, Test, TestAttempt, QuestionResult

def test_database_connection():
    """Test if we can connect to the database"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")

        # Test connection
        db = SessionLocal()
        user_count = db.query(User).count()
        print(f"✅ Database connected successfully. User count: {user_count}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    test_database_connection()