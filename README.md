# examlify - Test Management System

A web-based test management system that enables automated question extraction from PDF documents using LLM technology, provides an interactive web interface for test-taking, and includes comprehensive scoring and analytics capabilities.

## Features

- **PDF Upload & Processing:** Upload PDF question papers with automated question extraction
- **LLM Integration:** OpenAI-powered question parsing and structuring
- **Interactive Test Interface:** Timer-based test taking with navigation and progress tracking
- **Intelligent Scoring:** Automated scoring with subject-wise and topic-wise breakdown
- **User Management:** Admin and user roles with secure authentication
- **Comprehensive Reporting:** Detailed analytics and performance insights

## Documentation

### 📋 Requirements & Planning
- **[System Requirements](docs/system-requirements.md)** - Complete functional and technical requirements
- **[Implementation Roadmap](docs/implementation-roadmap.md)** - 7-phase development plan

### 🏗️ Architecture & Design
- **[System Architecture](docs/system-architecture.md)** - Technical architecture and component design
- **[Database Design](docs/database-design.md)** - Complete database schema and data models

### 🚀 Development
- **[Development Setup Guide](docs/development-setup.md)** - Local development environment with Docker MySQL

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

4. **Serve frontend:**
   ```bash
   cd frontend
   python -m http.server 3000
   ```

5. **Access applications:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: Connect via MySQL client (localhost:3306)

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.8+)
- **Database:** MySQL 8.0 with SQLAlchemy ORM
- **Authentication:** JWT tokens
- **LLM Integration:** OpenAI API
- **PDF Processing:** PyPDF2

### Frontend
- **Core:** HTML5, CSS3, JavaScript (ES6+)
- **Styling:** Modern CSS with Flexbox/Grid
- **Architecture:** Modular component-based design

### Development
- **Database:** Docker MySQL container (no persistence)
- **Testing:** pytest for backend, basic integration tests
- **Development Server:** uvicorn with hot reload

## Development Phases

1. **Phase 1 (Weeks 1-4):** Foundation & Authentication
2. **Phase 2 (Weeks 5-8):** PDF Processing & LLM Integration
3. **Phase 3 (Weeks 9-12):** Test Taking Interface
4. **Phase 4 (Weeks 13-16):** Scoring & Results
5. **Phase 5 (Weeks 17-20):** Reporting & History
6. **Phase 6 (Weeks 21-24):** Testing & Optimization
7. **Phase 7 (Weeks 25-28):** Deployment & Production

## Database Schema

### Core Tables
- **users** - User accounts and roles
- **tests** - Test metadata and questions (JSON)
- **test_attempts** - Individual test sessions
- **question_results** - Detailed answer analysis

### Key Features
- Subject and topic categorization for questions
- JSON storage for flexible question structures
- Comprehensive indexing for performance
- Connection pooling and optimized queries

## API Overview

### Authentication
- `POST /auth/login` - User authentication
- `POST /auth/logout` - Session termination
- `GET /auth/me` - Current user info

### Test Management
- `POST /api/tests/upload` - PDF upload and processing
- `GET /api/tests` - List available tests
- `GET /api/tests/{id}` - Get test details

### Test Taking
- `POST /api/tests/{id}/start` - Start test session
- `POST /api/tests/{id}/answer` - Submit answer
- `POST /api/tests/{id}/submit` - Complete test

### Results & Reporting
- `GET /api/results/{attempt_id}` - Get test results
- `GET /api/reports/user/{user_id}` - User performance
- `GET /api/admin/analytics` - System analytics

## Getting Help

For detailed setup instructions, see [Development Setup Guide](docs/development-setup.md).

For architecture details, see [System Architecture](docs/system-architecture.md).

For development phases, see [Implementation Roadmap](docs/implementation-roadmap.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.