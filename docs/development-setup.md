# Development Setup Guide

## Overview

This guide provides step-by-step instructions for setting up a local development environment for the examlify test management system.

**Note:** The project structure and all necessary files have already been created. This guide focuses on getting the development environment running.

---

## Prerequisites

### Required Software
- **Docker Desktop** (latest version)
- **Python 3.8+**
- **Git**

### Verify Installation
```bash
docker --version
python --version  # or python3 --version
git --version
```

---

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/sdmcraft/examlify
cd examlify
```

### 2. Start Database
```bash
# Start MySQL database only
docker-compose -f docker-compose.dev.yml up -d

# Verify container is running
docker ps
```

### 3. Setup Backend
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test database connection
python test_db.py

# Copy environment file and configure
cp env.example .env
# Edit .env with your OpenAI API key and other settings
```

### 4. Start Development Servers
```bash
# Terminal 1: Backend (from backend directory)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend (from frontend directory)
python -m http.server 3000
```

### 5. Access Applications
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Database:** Connect directly via MySQL client (port 3306)

---

## Database Details

### Connection Details
- **Host:** localhost
- **Port:** 3306
- **Database:** examlify_dev
- **Username:** examlify_user
- **Password:** examlify_pass

### Sample Admin User
- **Username:** admin
- **Password:** admin123

### Database Schema
The database includes:
- `users` - User accounts and authentication
- `tests` - Test definitions and PDF content
- `test_attempts` - User test attempts and scores
- `question_results` - Individual question results with subject/topic tracking

### Current Setup (Minimal)
The current Docker Compose setup includes only:
- **MySQL Database** - No persistence (data resets on restart)
- **No Backend Container** - Run backend locally for development
- **No phpMyAdmin** - Connect directly via MySQL client
- **No Redis** - Session management handled by backend

This minimal setup is perfect for development when you want a clean database every time.

---

## Development Workflow

### Daily Development
```bash
# Start services
docker-compose -f docker-compose.dev.yml up -d
cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd frontend && python -m http.server 3000
```

### Useful Commands
```bash
# View database logs
docker-compose -f docker-compose.dev.yml logs mysql

# Reset database (data will be lost - no persistence)
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# Connect to database directly
mysql -h localhost -P 3306 -u examlify_user -pexamlify_pass examlify_dev

# Run tests
cd backend && pytest tests/ -v

# Stop database
docker-compose -f docker-compose.dev.yml down
```

---

## Troubleshooting

### Common Issues

**Port 3306 already in use:**
```bash
# Stop existing MySQL
sudo service mysql stop  # Linux
brew services stop mysql  # macOS
```

**Python environment issues:**
```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Database connection errors:**
```bash
# Wait for MySQL to start
docker-compose -f docker-compose.dev.yml logs mysql

# Check if MySQL is ready
docker-compose -f docker-compose.dev.yml exec mysql mysqladmin ping -h localhost -u examlify_user -pexamlify_pass
```

**Environment file missing:**
```bash
cp env.example .env
# Edit .env with your settings
```

---

## Project Structure

```
examlify/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utilities
│   │   └── main.py         # FastAPI app
│   ├── tests/              # Test files
│   ├── requirements.txt    # Python dependencies
│   └── env.example         # Environment template
├── frontend/               # Static web files
│   ├── index.html          # Main page
│   ├── styles.css          # Styling
│   └── script.js           # Frontend logic
├── database/
│   └── init.sql            # Database schema
├── docker-compose.dev.yml  # MySQL database only
└── docs/                   # Documentation
```

---

Refer to the [Implementation Roadmap](implementation-roadmap.md) for detailed development phases.