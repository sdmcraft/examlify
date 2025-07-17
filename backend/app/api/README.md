# API Handlers Documentation

This directory contains the handler classes for the examlify API. The handlers provide a clean separation between the API routes and the business logic, making the code more maintainable and testable.

## Structure

```
api/
├── handlers/
│   ├── __init__.py          # Exports all handler classes
│   ├── base_handler.py      # Base handler with common functionality
│   ├── auth_handler.py      # Authentication operations
│   ├── exam_handler.py      # Exam management operations
│   ├── session_handler.py   # Exam session operations
│   ├── result_handler.py    # Results and analytics
│   ├── user_handler.py      # User management operations
│   └── admin_handler.py     # Admin-specific operations
├── router.py                # Main API router
└── README.md               # This file
```

## Handler Classes

### BaseHandler
The base class that provides common functionality for all handlers:
- Database session management
- Error handling with appropriate HTTP status codes
- Resource validation

### AuthHandler
Handles authentication-related operations:
- User login with JWT token generation
- Token validation and user retrieval
- Authentication status checking
- Logout functionality

### ExamHandler
Manages exam-related operations:
- Exam CRUD operations
- PDF upload and processing
- Question extraction (placeholder for LLM integration)
- Access control for exam operations

### SessionHandler
Handles exam session management:
- Starting exam attempts
- Session status tracking
- Exam submission and scoring
- Hint and solution generation (placeholder for LLM integration)

### ResultHandler
Manages exam results and analytics:
- Detailed result retrieval
- Performance analytics
- Subject-wise performance breakdown
- Exam history and trends

### UserHandler
Handles user-related operations:
- User profile management
- Password changes
- User CRUD operations (admin)
- User statistics

### AdminHandler
Provides admin-specific functionality:
- System-wide statistics
- User management
- Exam analytics
- Activity logging

## Usage Example

```python
from app.api.handlers import AuthHandler, ExamHandler
from app.database import get_db

# Get database session
db = next(get_db())

# Create handlers
auth_handler = AuthHandler(db)
exam_handler = ExamHandler(db)

# Use handlers
try:
    # Login user
    result = auth_handler.login("username", "password")
    token = result['access_token']

    # Get current user
    user = auth_handler.get_current_user(token)

    # Create an exam
    exam = exam_handler.create_exam("My Exam", "Exam description", user)

    print(f"Created exam: {exam.title}")

except Exception as e:
    print(f"Error: {e}")
```

## API Endpoints

The router (`router.py`) maps HTTP requests to the appropriate handler methods:

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/status` - Check authentication status

### Exams
- `GET /api/exams` - List exams
- `POST /api/exams` - Create exam
- `POST /api/exams/upload` - Upload PDF
- `GET /api/exams/{exam_id}` - Get exam details
- `PUT /api/exams/{exam_id}` - Update exam
- `DELETE /api/exams/{exam_id}` - Delete exam

### Exam Sessions
- `POST /api/exams/{exam_id}/start` - Start exam session
- `GET /api/sessions/{session_id}/status` - Get session status
- `POST /api/sessions/{session_id}/hint/{question_id}` - Get hint
- `POST /api/sessions/{session_id}/solution/{question_id}` - Get solution
- `POST /api/exams/{exam_id}/submit` - Submit exam

### Results
- `GET /api/results/{attempt_id}` - Get detailed results
- `GET /api/results/history` - Get exam history
- `GET /api/results/summary` - Get performance summary

### Users
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update user profile
- `PUT /api/users/password` - Change password
- `GET /api/users/{user_id}/history` - Get user exam history

### Admin
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create user
- `GET /api/admin/users/{user_id}` - Get user details
- `PUT /api/admin/users/{user_id}` - Update user
- `DELETE /api/admin/users/{user_id}` - Delete user
- `GET /api/admin/users/{user_id}/statistics` - Get user statistics
- `GET /api/admin/statistics` - Get system statistics
- `GET /api/admin/analytics/exams` - Get exam analytics
- `GET /api/admin/activity` - Get activity log

## Testing

Run the test script to verify all handlers work correctly:

```bash
cd backend
python test_handlers.py
```

This will:
1. Create test users (admin and regular user)
2. Test authentication
3. Test exam management
4. Test session management
5. Test user management
6. Test admin functionality

## Dependencies

The handlers require the following additional dependencies:
- `PyJWT` - For JWT token handling
- `Werkzeug` - For password hashing
- `python-multipart` - For file uploads

## Security Features

- JWT-based authentication
- Password hashing with Werkzeug
- Role-based access control
- Input validation and sanitization
- Proper error handling with appropriate HTTP status codes

## Future Enhancements

- LLM integration for question extraction
- LLM integration for hint and solution generation
- File upload validation and virus scanning
- Rate limiting
- Audit logging
- Caching for frequently accessed data