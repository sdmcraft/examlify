# Requirements Document

## 1. Executive Summary

**Product Name:** examlify
**Version:** 1.0
**Date:** 2025
**Owner:** Software Architecture Team

### 1.1 Purpose
A web-based test management system that enables automated question extraction from PDF documents using LLM technology, provides an interactive web interface for test-taking, and includes comprehensive scoring and analytics capabilities.

### 1.2 Key Features
- PDF-based question paper upload and processing
- LLM-powered question extraction and structuring
- Interactive web-based test interface
- Intelligent hint and solution system
- Timer-based test management
- Automated scoring and analytics
- Multi-user authentication and administration
- Comprehensive reporting and test history

---

## 2. Stakeholders

### 2.1 Primary Users
- **Test Takers:** Students/candidates who attempt tests
- **Administrators:** Users who manage the system, create accounts, and monitor tests
- **Content Creators:** Users who upload and manage test content

### 2.2 Technical Stakeholders
- **System Administrator:** Manages system configuration and setup
- **Database Administrator:** Manages data storage and optimization
- **Content Manager:** Oversees test content quality and organization

---

## 3. System Overview

### 3.1 High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (HTML/CSS/JS) │◄──►│   (Python)      │◄──►│   (MySQL)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   LLM Service   │
                       │   (OpenAI/etc)  │
                       └─────────────────┘
```

### 3.2 Core Components
- **PDF Processing Service:** Handles document upload and LLM-based extraction
- **Test Engine:** Manages test sessions, timing, and user interactions
- **Scoring System:** Calculates results and generates reports
- **User Management:** Handles authentication and authorization
- **Content Management:** Stores and retrieves test data

---

## 4. Functional Requirements

### 4.1 User Authentication & Authorization

#### 4.1.1 Authentication System
- **REQ-AUTH-001:** System must support username/password authentication
- **REQ-AUTH-002:** Admin users can create, modify, and delete user accounts
- **REQ-AUTH-003:** Session management with secure logout functionality
- **REQ-AUTH-004:** Password complexity requirements and validation

#### 4.1.2 User Roles
- **REQ-AUTH-005:** **Admin Role:** Full system access, user management, test creation
- **REQ-AUTH-006:** **User Role:** Test taking, result viewing, profile management

### 4.2 PDF Processing & Question Extraction

#### 4.2.1 PDF Upload
- **REQ-PDF-001:** Admin can upload PDF files containing question papers
- **REQ-PDF-002:** System validates PDF format and file size limits
- **REQ-PDF-003:** PDFs are stored as BLOBs in the database for archival
- **REQ-PDF-004:** Upload progress indication and error handling

#### 4.2.2 LLM-Based Extraction
- **REQ-LLM-001:** System uses LLM API to extract questions from PDF content
- **REQ-LLM-002:** Questions are parsed into structured JSON format
- **REQ-LLM-003:** JSON schema includes:
  ```json
  {
    "test_id": "string",
    "title": "string",
    "instructions": "string",
    "questions": [
      {
        "question_id": "string",
        "question_text": "string",
        "question_type": "multiple_choice",
        "options": [
          {
            "option_id": "string",
            "option_text": "string"
          }
        ],
        "correct_answer": "string",
        "hint": "string",
        "detailed_solution": "string",
        "subject": "string",
        "topic": "string",
        "marks": 4,
        "negative_marks": -1
      }
    ]
  }
  ```
- **REQ-LLM-004:** System validates extracted JSON structure

### 4.3 Test Interface & User Experience

#### 4.3.1 Test Setup
- **REQ-TEST-001:** Users can select from available processed tests
- **REQ-TEST-002:** Pre-test setup screen with:
  - Test title and instructions
  - Optional countdown timer configuration
  - "Start Test" button
- **REQ-TEST-003:** System prevents multiple simultaneous test sessions per user

#### 4.3.2 Test Taking Interface
- **REQ-TEST-004:** Clean, intuitive question display with:
  - Question number and navigation
  - Question text with proper formatting
  - Radio button options for multiple choice
  - Current question highlighting
- **REQ-TEST-005:** **Timer System:**
  - Count-up timer when no countdown is set
  - Count-down timer when duration is specified
  - Visual timer display at page top
  - Auto-submission when countdown reaches zero
- **REQ-TEST-006:** **Interactive Features:**
  - "Show Hint" button reveals contextual hints
  - "Show Solution" button displays correct answer and detailed explanation
  - Answer selection becomes disabled after viewing solution
  - Visual indication of answered/unanswered questions

#### 4.3.3 Test Navigation
- **REQ-TEST-007:** Question navigation panel showing:
  - Question numbers with status indicators (answered/unanswered/marked)
  - Quick jump to specific questions
  - Progress indicator
- **REQ-TEST-008:** "End Test" button with confirmation dialog
- **REQ-TEST-009:** Auto-save of answers during test session

### 4.4 Scoring & Evaluation

#### 4.4.1 Scoring Algorithm
- **REQ-SCORE-001:** **Marking Scheme:**
  - Correct answer: +4 marks
  - Incorrect answer: -1 mark
  - Not attempted: 0 marks
- **REQ-SCORE-002:** Subject-wise and topic-wise score calculation
- **REQ-SCORE-003:** Overall total score calculation
- **REQ-SCORE-004:** Percentage calculation

#### 4.4.2 Results Processing
- **REQ-SCORE-005:** Automatic scoring upon test completion
- **REQ-SCORE-006:** Detailed question-wise analysis:
  - Question number
  - User's answer
  - Correct answer
  - Status (correct/incorrect/not attempted)
  - Marks obtained
- **REQ-SCORE-007:** Performance analytics and insights

### 4.5 Reporting & Analytics

#### 4.5.1 Individual Test Report
- **REQ-REPORT-001:** Comprehensive test report containing:
  - Test details (title, date, duration)
  - Overall score and percentage
  - Subject-wise and topic-wise breakdown
  - Question-wise detailed analysis
  - Performance insights and recommendations
- **REQ-REPORT-002:** Exportable report formats (PDF, CSV)

#### 4.5.2 Test History & Summary
- **REQ-REPORT-003:** **Test History Dashboard:**
  - List of all attempted tests
  - Basic stats (score, date, duration)
  - Clickable test entries for detailed view
- **REQ-REPORT-004:** **Summary Analytics:**
  - Performance trends over time
  - Subject-wise and topic-wise strengths/weaknesses
  - Improvement recommendations

#### 4.5.3 Administrative Reports
- **REQ-REPORT-005:** Admin dashboard with:
  - User activity overview
  - Test completion statistics
  - System usage metrics
- **REQ-REPORT-006:** User management interface with test history

---

## 5. Technical Requirements

### 5.1 Frontend Technology Stack
- **REQ-TECH-001:** HTML5, CSS3, JavaScript (ES6+)
- **REQ-TECH-002:** Responsive design for multiple device types
- **REQ-TECH-003:** Modern browser compatibility (Chrome 90+, Firefox 88+, Safari 14+)

### 5.2 Backend Technology Stack
- **REQ-TECH-005:** Python 3.8+ with FastAPI or Flask framework
- **REQ-TECH-006:** RESTful API design with proper HTTP status codes
- **REQ-TECH-007:** JSON-based API communication
- **REQ-TECH-008:** Proper error handling and logging

### 5.3 Database Requirements
- **REQ-DB-001:** MySQL database with proper indexing
- **REQ-DB-002:** BLOB storage for PDF files
- **REQ-DB-003:** Relational schema for:
  - User management
  - Test metadata
  - Question banks
  - Test attempts and results


### 5.4 External Services
- **REQ-EXT-001:** LLM API integration (OpenAI, Anthropic, or similar)
- **REQ-EXT-002:** PDF processing libraries (PyPDF2, pdfplumber, etc.)
- **REQ-EXT-003:** Error handling for external service failures

---

## 6. Non-Functional Requirements

### 6.1 Performance

### 6.2 Security
- **REQ-SEC-001:** Secure authentication with encrypted password storage
- **REQ-SEC-002:** HTTPS encryption for all client-server communication
- **REQ-SEC-003:** Input validation and sanitization
- **REQ-SEC-004:** Protection against common web vulnerabilities (XSS, CSRF, SQL injection)
- **REQ-SEC-005:** Secure session management with automatic timeout

### 6.3 Usability
- **REQ-UX-001:** Intuitive user interface with minimal learning curve
- **REQ-UX-002:** Accessibility compliance (WCAG 2.1 AA)
- **REQ-UX-003:** Mobile-responsive design
- **REQ-UX-004:** Consistent visual design and branding

### 6.4 Reliability
- **REQ-REL-001:** System should be reliable and stable during normal usage
- **REQ-REL-002:** Graceful error handling for common failures

- **REQ-REL-004:** Graceful degradation when external services are unavailable

---

## 7. Database Design

The complete database schema design, including table structures, relationships, indexes, and data management strategies, is documented separately for better organization and maintainability.

**📋 See:** [Database Design Document](./database-design.md)

### 7.1 Key Database Components
- **Users Table:** Authentication and role management
- **Tests Table:** Test metadata and PDF storage
- **Test Attempts Table:** Individual test sessions and scoring
- **Question Results Table:** Detailed question-level analysis

### 7.2 Database Technology Stack
- **Database System:** MySQL 8.0+
- **Storage Engine:** InnoDB
- **Character Set:** utf8mb4 for full Unicode support
- **JSON Support:** Native JSON data type for flexible question storage

---

## 8. API Specification

### 8.1 Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/status` - Check authentication status

### 8.2 Test Management Endpoints
- `POST /api/tests/upload` - Upload PDF and process questions
- `GET /api/tests` - List available tests
- `GET /api/tests/{test_id}` - Get test details
- `POST /api/tests/{test_id}/start` - Start test attempt
- `POST /api/tests/{test_id}/submit` - Submit test answers

### 8.3 Results Endpoints
- `GET /api/results/{attempt_id}` - Get detailed test results
- `GET /api/results/history` - Get user's test history
- `GET /api/results/summary` - Get performance summary

### 8.4 Admin Endpoints
- `POST /api/admin/users` - Create new user
- `GET /api/admin/users` - List all users
- `GET /api/admin/analytics` - System analytics

---

## 9. User Stories

### 9.1 Test Taker Stories
- **US-001:** As a test taker, I want to upload a PDF question paper so that I can take a digital version of the test
- **US-002:** As a test taker, I want to set a countdown timer so that I can simulate exam conditions
- **US-003:** As a test taker, I want to see hints for difficult questions so that I can learn better
- **US-004:** As a test taker, I want to view detailed solutions so that I can understand the correct approach
- **US-005:** As a test taker, I want to see my performance history so that I can track my progress

### 9.2 Administrator Stories
- **US-006:** As an administrator, I want to create user accounts so that I can manage access to the system
- **US-007:** As an administrator, I want to view test results and user activity so that I can manage the system effectively
- **US-008:** As an administrator, I want to see basic usage statistics so that I can understand system usage

---
