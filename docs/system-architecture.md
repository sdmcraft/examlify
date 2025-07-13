# Test Management System - Technical Architecture Document

## 1. Architecture Overview

### 1.1 System Architecture Pattern
The system follows a **3-tier architecture** with clear separation of concerns:
- **Presentation Layer:** HTML/CSS/JavaScript frontend
- **Business Logic Layer:** Python backend with RESTful APIs
- **Data Layer:** MySQL database with structured and unstructured data

### 1.2 Architecture Principles
- **Modularity:** Each service has a single responsibility
- **Scalability:** Designed for future growth as needed
- **Security:** Defense in depth with multiple security layers
- **Maintainability:** Clean code practices and comprehensive documentation
- **Testability:** Unit and integration testing at all levels

---

## 2. Component Architecture

### 2.1 Frontend Architecture

#### 2.1.1 Technology Stack
```
Frontend Stack:
├── HTML5 (Semantic markup)
├── CSS3 (Flexbox/Grid layouts)
├── Vanilla JavaScript (ES6+)
├── Optional: Lightweight library (Alpine.js/Vanilla Components)
```

#### 2.1.2 Frontend Components
- **Login Component:** Authentication interface
- **Dashboard Component:** Test selection and history
- **Upload Component:** PDF upload interface
- **Test Interface:** Question rendering and interaction
- **Timer Component:** Countdown and elapsed time display
- **Results Component:** Score display and analysis
- **Admin Panel:** User management interface

#### 2.1.3 State Management
```javascript
// Simple state management pattern
const AppState = {
    user: null,
    currentTest: null,
    testSession: null,
    timer: null,
    answers: {},

    // State management methods
    updateUser(user) { /* ... */ },
    startTest(test) { /* ... */ },
    updateAnswer(questionId, answer) { /* ... */ }
};
```

### 2.2 Backend Architecture

#### 2.2.1 Backend Design
```
Backend Application (FastAPI/Flask):
├── Authentication Module
├── PDF Processing Module
├── Test Management Module
├── Scoring Module
├── Reporting Module
└── Admin Module
```

#### 2.2.2 Module Details

**Authentication Module**
```python
# auth_service.py
class AuthService:
    def authenticate(username, password) -> User
    def authorize(user, resource) -> bool
    def create_session(user) -> Session
    def validate_session(token) -> bool
```

**PDF Processing Module**
```python
# pdf_service.py
class PDFProcessingService:
    def extract_text(pdf_file) -> str
    def process_with_llm(text) -> dict
    def validate_questions(questions) -> bool
    def store_processed_test(test_data) -> int
```

**Test Management Module**
```python
# test_service.py
class TestService:
    def get_available_tests(user) -> List[Test]
    def start_test_session(user, test_id) -> Session
    def submit_answer(session, question_id, answer) -> bool
    def end_test_session(session) -> Results
```

#### 2.2.3 API Design Patterns

**RESTful API Structure**
```
/api/v1/
├── auth/
│   ├── POST /login
│   ├── POST /logout
│   └── GET /status
├── tests/
│   ├── GET /
│   ├── POST /upload
│   ├── GET /{test_id}
│   ├── POST /{test_id}/start
│   └── POST /{test_id}/submit
├── results/
│   ├── GET /{attempt_id}
│   ├── GET /history
│   └── GET /summary
└── admin/
    ├── GET /users
    ├── POST /users
    └── GET /analytics
```

**Response Format Standard**
```json
{
    "success": true,
    "data": { /* response data */ },
    "error": null,
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "uuid"
}
```

### 2.3 Database Architecture

The database layer uses MySQL 8.0+ with InnoDB storage engine for ACID compliance and performance optimization. Key architectural considerations include:

- **Connection Pooling:** Efficient database connection management
- **Transaction Management:** Ensures data consistency across operations
- **Indexing Strategy:** Optimized indexes for common query patterns
- **JSON Storage:** Flexible storage for questions and answers data

For detailed database schema, table definitions, indexes, and data access patterns, see **[Database Design Document](database-design.md)**.

---

## 3. External Service Integration

### 3.1 LLM Service Integration

#### 3.1.1 LLM Provider Abstraction
```python
# llm_provider.py
class LLMProvider:
    def extract_questions(self, pdf_text: str) -> dict:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def extract_questions(self, pdf_text: str) -> dict:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": QUESTION_EXTRACTION_PROMPT},
                {"role": "user", "content": pdf_text}
            ]
        )
        return json.loads(response.choices[0].message.content)
```

#### 3.1.2 Service Implementation
```python
# Simple LLM service for question extraction
class LLMService:
    def __init__(self):
        self.provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_questions(self, pdf_text: str) -> dict:
        return self.provider.extract_questions(pdf_text)
```

### 3.2 PDF Processing Pipeline

#### 3.2.1 PDF Processing Workflow
```python
# pdf_pipeline.py
class PDFProcessingPipeline:
    def __init__(self):
        self.validators = [FileFormatValidator(), FileSizeValidator()]
        self.extractors = [PyPDF2Extractor(), PDFPlumberExtractor()]
        self.llm_service = LLMService()

    def process_pdf(self, pdf_file) -> dict:
        # 1. Validate file
        for validator in self.validators:
            validator.validate(pdf_file)

        # 2. Extract text
        text = self.extract_text(pdf_file)

        # 3. Process with LLM
        questions = self.llm_service.extract_questions(text)

        # 4. Validate structure
        self.validate_questions(questions)

        return questions
```

---

## 4. Security Architecture

### 4.1 Authentication & Authorization

#### 4.1.1 Security Layers
```python
# security_middleware.py
class SecurityMiddleware:
    def __init__(self):
        self.auth_service = AuthService()
        self.rate_limiter = RateLimiter()

    def authenticate_request(self, request):
        # Extract and validate credentials
        token = request.headers.get('Authorization')
        return self.auth_service.validate_session(token)

    def check_rate_limit(self, request):
        # Implement rate limiting
        return self.rate_limiter.check_limit(request.remote_addr)
```

#### 4.1.2 Input Validation
```python
# validation.py
from marshmallow import Schema, fields, validate

class TestUploadSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(missing="")
    pdf_file = fields.Raw(required=True)

class AnswerSubmissionSchema(Schema):
    question_id = fields.Str(required=True)
    answer = fields.Str(required=True)
    timestamp = fields.DateTime(required=True)
```

### 4.2 Data Protection

#### 4.2.1 Database Security
```sql
-- Database user with minimal privileges
CREATE USER 'test_app'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, INSERT, UPDATE ON test_db.* TO 'test_app'@'localhost';
GRANT DELETE ON test_db.test_attempts TO 'test_app'@'localhost';
```

#### 4.2.2 PDF Storage Security
```python
# secure_storage.py
class SecureStorage:
    def store_pdf(self, pdf_content: bytes, filename: str) -> str:
        # Encrypt PDF content before storage
        encrypted_content = self.encrypt(pdf_content)

        # Store in database with integrity check
        checksum = hashlib.sha256(pdf_content).hexdigest()

        return self.database.store_blob(encrypted_content, filename, checksum)
```

---

## 5. Performance Optimization

### 5.1 Caching Strategy

#### 5.1.1 Simple Database Caching
```python
# Simple caching for database queries
class DatabaseManager:
    def __init__(self):
        self.connection = create_database_connection()

    def get_test_data(self, test_id):
        # Direct database query with built-in connection pooling
        return self.connection.execute(
            "SELECT * FROM tests WHERE id = ?", (test_id,)
        ).fetchone()
```

**Note:** Advanced caching strategies (Redis, multi-level caching) can be added in future iterations when performance requirements demand it.

### 5.2 Database Optimization

#### 5.2.1 Query Optimization
```sql
-- Optimized query for test history
SELECT
    ta.id,
    ta.started_at,
    ta.completed_at,
    ta.total_score,
    ta.percentage,
    t.title
FROM test_attempts ta
JOIN tests t ON ta.test_id = t.id
WHERE ta.user_id = ?
ORDER BY ta.completed_at DESC
LIMIT 20;

-- Index for the above query
CREATE INDEX idx_test_attempts_user_completed ON test_attempts(user_id, completed_at DESC);
```

#### 5.2.2 Connection Pooling
```python
# database_pool.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class DatabasePool:
    def __init__(self, connection_string):
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True
        )
```

---

## 6. Monitoring & Observability

### 6.1 Logging Architecture

#### 6.1.1 Structured Logging
```python
# logging_config.py
import structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

---

## 7. Deployment Architecture

### 7.2 Production Deployment

#### 7.2.1 Environment Configuration
```bash
# .env.production
DATABASE_URL=mysql://user:secure_password@db-server:3306/testdb
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_jwt_secret_key
DEBUG=false
LOG_LEVEL=INFO
```

---

## 8. Testing Strategy

### 8.1 Testing Pyramid

#### 8.1.1 Unit Tests
```python
# test_pdf_service.py
import pytest
from services.pdf_service import PDFProcessingService

class TestPDFService:
    def setup_method(self):
        self.pdf_service = PDFProcessingService()

    def test_extract_questions_valid_pdf(self):
        # Test with valid PDF
        with open('test_data/sample_test.pdf', 'rb') as f:
            result = self.pdf_service.process_pdf(f)

        assert result['questions'] is not None
        assert len(result['questions']) > 0

    def test_extract_questions_invalid_pdf(self):
        # Test with invalid PDF
        with pytest.raises(ValidationError):
            self.pdf_service.process_pdf(b'invalid_pdf_content')
```

#### 8.1.2 Integration Tests
```python
# test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from main import app

class TestAPIIntegration:
    def setup_method(self):
        self.client = TestClient(app)

    def test_upload_and_process_pdf(self):
        # Test complete PDF upload workflow
        with open('test_data/sample_test.pdf', 'rb') as f:
            response = self.client.post(
                '/api/tests/upload',
                files={'pdf_file': f},
                data={'title': 'Test Upload'}
            )

        assert response.status_code == 200
        test_id = response.json()['data']['test_id']

        # Verify test can be retrieved
        response = self.client.get(f'/api/tests/{test_id}')
        assert response.status_code == 200
```

---