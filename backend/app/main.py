from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import database and models
from .database import engine, get_db
from .models import Base, User, Test, TestAttempt, QuestionResult

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="examlify API",
    description="Test Management System API",
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

@app.get("/")
async def root():
    return {"message": "examlify API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

@app.get("/db-test")
async def test_database(db = Depends(get_db)):
    try:
        # Test database connection by querying user count
        user_count = db.query(User).count()
        return {"status": "success", "message": "Database connected", "user_count": user_count}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)