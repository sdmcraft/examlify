# Database Design Document

## 1. Overview

**Product:** examlify Exam Management System
**Version:** 1.0
**Date:** 2025
**Owner:** Database Architecture Team

### 1.1 Purpose
This document outlines the database schema design for the examlify exam management system, including table structures, relationships, indexes, and data management strategies.

### 1.2 Database Technology
- **Database System:** MySQL 8.0+
- **Storage Engine:** InnoDB
- **Character Set:** utf8mb4
- **Collation:** utf8mb4_unicode_ci

---

## 2. Database Schema Overview

### 2.1 Core Entities
- **Users:** System users (admins and exam takers)
- **Exams:** Exam metadata and question data
- **Exam Attempts:** Individual exam sessions
- **Question Results:** Detailed answer analysis

### 2.2 Entity Relationship Diagram
```
┌─────────────┐    1:N    ┌─────────────┐    1:N    ┌─────────────┐
│    Users    │◄──────────│    Exams    │◄──────────│Exam Attempts│
│             │           │             │           │             │
│ - id (PK)   │           │ - id (PK)   │           │ - id (PK)   │
│ - username  │           │ - title     │           │ - user_id   │
│ - email     │           │ - pdf_data  │           │ - exam_id   │
│ - role      │           │ - questions │           │ - answers   │
└─────────────┘           └─────────────┘           └─────────────┘
                                                           │
                                                           │ 1:N
                                                           ▼
                                                  ┌─────────────┐
                                                  │Question     │
                                                  │Results      │
                                                  │             │
                                                  │ - id (PK)   │
                                                  │ - attempt_id│
                                                  │ - question_id│
                                                  │ - is_correct│
                                                  └─────────────┘
```

---

## 3. Table Definitions

### 3.1 Users Table

#### Purpose
Stores user account information including authentication credentials and role-based access control.

#### Schema
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3.2 Exams Table

#### Purpose
Stores exam metadata, PDF content, and extracted question data in JSON format.

#### Schema
```sql
CREATE TABLE exams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    pdf_content LONGBLOB,
    pdf_filename VARCHAR(255),
    questions_json JSON,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_title (title),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3.3 Exam Attempts Table

#### Purpose
Records individual exam sessions including timing, answers, and scoring results.

#### Schema
```sql
CREATE TABLE exam_attempts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    exam_id INT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    duration_seconds INT,
    answers_json JSON,
    total_score INT,
    max_score INT,
    percentage DECIMAL(5,2),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    INDEX idx_user_exam (user_id, exam_id),
    INDEX idx_completed_at (completed_at),
    INDEX idx_percentage (percentage)
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3.4 Question Results Table

#### Purpose
Stores detailed question-level analysis for each test attempt.

#### Schema
```sql
CREATE TABLE question_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    attempt_id INT NOT NULL,
    question_id VARCHAR(50) NOT NULL,
    user_answer VARCHAR(10),
    correct_answer VARCHAR(10),
    is_correct BOOLEAN,
    marks_obtained INT,
    subject VARCHAR(100),
    topic VARCHAR(100),

    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
    INDEX idx_attempt_id (attempt_id),
    INDEX idx_question_id (question_id),
    INDEX idx_subject (subject),
    INDEX idx_topic (topic),
    INDEX idx_is_correct (is_correct)
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 4. JSON Schema Definitions

### 4.1 Questions JSON Schema
```json
{
  "exam_id": "string",
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

### 4.2 Answers JSON Schema
```json
{
  "question_1": {
    "selected_answer": "A",
    "timestamp": "2025-01-01T10:30:00Z",
    "hint_viewed": false,
    "solution_viewed": false
  }
}
```

---

## 5. Indexes and Performance

### 5.1 Core Performance Indexes
```sql
-- User performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

-- Exam management
CREATE INDEX idx_exams_title ON exams(title);
CREATE INDEX idx_exams_created_by ON exams(created_by);

-- Analytics and reporting
CREATE INDEX idx_attempts_user_completed ON exam_attempts(user_id, completed_at DESC);
CREATE INDEX idx_results_attempt_question ON question_results(attempt_id, question_id);
```

### 5.2 Additional Optimized Indexes
```sql
-- Additional indexes for enhanced performance
CREATE INDEX idx_user_username ON users(username);
CREATE INDEX idx_exam_attempts_user_exam ON exam_attempts(user_id, exam_id);
CREATE INDEX idx_question_results_attempt ON question_results(attempt_id);
CREATE INDEX idx_exam_attempts_completed ON exam_attempts(completed_at);
```

---

## 6. Security and Access Control

### 6.1 Database Users
```sql
-- Application user with minimal privileges
CREATE USER 'examlify_app'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT, INSERT, UPDATE ON examlify.* TO 'examlify_app'@'%';
GRANT DELETE ON examlify.exam_attempts TO 'examlify_app'@'%';
GRANT DELETE ON examlify.question_results TO 'examlify_app'@'%';

-- Read-only analytics user
CREATE USER 'examlify_analytics'@'%' IDENTIFIED BY 'analytics_password';
GRANT SELECT ON examlify.* TO 'examlify_analytics'@'%';
```

### 6.2 Data Protection
- Password hashes using BCrypt (cost factor 12)
- PDF content encryption using AES-256
- TLS 1.3 for all database connections

---

## 7. Data Access Layer

### 7.1 Database Abstraction Layer
```python
# Database abstraction layer
class DatabaseManager:
    def __init__(self, connection_string):
        self.db = create_engine(connection_string)

    def get_user(self, username) -> User:
        # Implementation with connection pooling
        pass

    def save_exam_attempt(self, attempt) -> int:
        # Transaction management
        pass
```

### 7.2 Connection Management
- Connection pooling for optimal performance
- Transaction management for data consistency
- Prepared statements for security and performance
- Automatic retry logic for connection failures
