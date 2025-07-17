from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
from dotenv import load_dotenv

# Import database and models
from .database import engine, get_db
from .models import Base, User, Exam, ExamAttempt, QuestionResult

# Import API router
from .api.router import router as api_router

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="examlify API",
    description="Exam Management System API",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "examlify API is running!"}

@app.get("/health")
async def health_check(db = Depends(get_db)):
    """Health check endpoint for the application."""
    try:
        # Check database connection by querying user count
        from sqlalchemy import func
        from .models import User
        user_count = db.query(func.count(User.id)).scalar()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": {
                "status": "connected",
                "user_count": user_count
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": {
                "status": "disconnected",
                "error": str(e)
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)