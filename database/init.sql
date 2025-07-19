-- examlify Database Schema
-- Version: 1.0
-- Description: Exam Management System Database

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS examlify_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE examlify_dev;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(10) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Exams Table
CREATE TABLE IF NOT EXISTS exams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    duration_minutes INT,
    pdf_content LONGBLOB,
    pdf_filename VARCHAR(255),
    questions_json JSON,
    status VARCHAR(50) DEFAULT 'draft',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_title (title),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Exam Attempts Table
CREATE TABLE IF NOT EXISTS exam_attempts (
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

-- Question Results Table
CREATE TABLE IF NOT EXISTS question_results (
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

-- Create application user with minimal privileges
CREATE USER IF NOT EXISTS 'examlify_app'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT, INSERT, UPDATE ON examlify_dev.* TO 'examlify_app'@'%';
GRANT DELETE ON examlify_dev.exam_attempts TO 'examlify_app'@'%';
GRANT DELETE ON examlify_dev.question_results TO 'examlify_app'@'%';

-- Create read-only analytics user
CREATE USER IF NOT EXISTS 'examlify_analytics'@'%' IDENTIFIED BY 'analytics_password';
GRANT SELECT ON examlify_dev.* TO 'examlify_analytics'@'%';

FLUSH PRIVILEGES;