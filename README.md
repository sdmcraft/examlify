# examlify - Exam Management System

A web-based exam management system that enables automated question extraction from PDF documents using LLM technology, provides an interactive web interface for exam-taking, and includes comprehensive scoring and analytics capabilities.

## Features

- **PDF Upload & Processing:** Upload PDF question papers with automated question extraction
- **LLM Integration:** OpenAI-powered question parsing and structuring
- **Interactive Exam Interface:** Timer-based exam taking with navigation and progress tracking
- **Intelligent Scoring:** Automated scoring with subject-wise and topic-wise breakdown
- **User Management:** Admin and user roles with secure authentication
- **Comprehensive Reporting:** Detailed analytics and performance insights
- **Handler-Based Architecture:** Clean separation of concerns with dedicated handler classes

## Documentation

### 📋 Requirements & Planning
- **[System Requirements](docs/system-requirements.md)** - Complete functional and technical requirements
- **[Implementation Roadmap](docs/implementation-roadmap.md)** - 7-phase development plan

### 🏗️ Architecture & Design
- **[System Architecture](docs/system-architecture.md)** - Technical architecture and component design
- **[Database Design](docs/database-design.md)** - Complete database schema and data models
- **[API Documentation](docs/openapi-spec.yaml)** - Complete OpenAPI 3.0 specification

### 🚀 Development
- **[Development Setup Guide](docs/development-setup.md)** - Local development environment with Docker MySQL
- **[API Handlers Documentation](backend/app/api/README.md)** - Handler classes architecture and usage

## Quick Start

1. **Set up development environment:**
   ```bash
   # Follow the complete guide in docs/development-setup.md
   git clone <your-repo-url>
   cd examlify
   ```

2. **Start MySQL Database:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Set up Python backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app/main.py
   ```



5. **Serve frontend:**
   ```bash
   cd frontend
   python -m http.server 3000
   ```

6. **Access applications:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: Connect via MySQL client (localhost:3306)

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.8+)
- **Database:** MySQL 8.0 with SQLAlchemy ORM
- **Authentication:** JWT tokens with PyJWT
- **Password Hashing:** Werkzeug security
- **File Uploads:** python-multipart
- **LLM Integration:** OpenAI API (planned)
- **PDF Processing:** PyPDF2 (planned)

### Frontend
- **Core:** HTML5, CSS3, JavaScript (ES6+)
- **Styling:** Modern CSS with Flexbox/Grid
- **Architecture:** Modular component-based design

### Development
- **Database:** Docker MySQL container (no persistence)
- **Development Server:** uvicorn with hot reload

## Architecture Overview

### Handler-Based Design
The backend uses a clean handler-based architecture with the following components:

- **BaseHandler** - Common functionality for all handlers
- **AuthHandler** - Authentication and JWT token management
- **ExamHandler** - Exam CRUD operations and PDF processing
- **SessionHandler** - Exam session management and submission
- **ResultHandler** - Results analysis and performance tracking
- **UserHandler** - User profile and account management
- **AdminHandler** - Administrative operations and analytics

### API Router
The main router (`backend/app/api/router.py`) maps HTTP endpoints to appropriate handlers, ensuring:
- Clean separation between API routes and business logic
- Proper request/response validation with Pydantic models
- Consistent error handling and status codes
- Authentication and authorization middleware

## Database Schema

### Core Tables
- **users** - User accounts and roles (admin/user)
- **exams** - Exam metadata, PDF content, and questions (JSON)
- **exam_attempts** - Individual exam sessions and scores
- **question_results** - Detailed answer analysis and subject breakdown

### Key Features
- Subject and topic categorization for questions
- JSON storage for flexible question structures
- Comprehensive indexing for performance
- Connection pooling and optimized queries
- Timestamp tracking for audit trails

## Development Status

### ✅ Completed
- **Database Schema** - Complete with all core tables
- **Handler Architecture** - All handler classes implemented
- **API Router** - Complete API endpoints matching OpenAPI spec
- **Authentication** - JWT-based auth with role-based access
- **Basic CRUD Operations** - Exam, user, and session management
- **Error Handling** - Comprehensive error handling and validation

### 🚧 In Progress
- **PDF Processing** - LLM integration for question extraction
- **Frontend Interface** - Exam taking and admin interfaces
- **Advanced Analytics** - Performance tracking and reporting

### 📋 Planned
- **LLM Integration** - OpenAI API for question processing
- **File Upload Validation** - Virus scanning and file validation
- **Rate Limiting** - API rate limiting and protection
- **Caching** - Redis caching for performance
- **Production Deployment** - Docker containers and CI/CD

## API Documentation

Access the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Getting Help

For detailed setup instructions, see [Development Setup Guide](docs/development-setup.md).

For architecture details, see [System Architecture](docs/system-architecture.md).

For complete API documentation, see [OpenAPI Specification](docs/openapi-spec.yaml).

For handler usage, see [API Handlers Documentation](backend/app/api/README.md).

For development phases, see [Implementation Roadmap](docs/implementation-roadmap.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.