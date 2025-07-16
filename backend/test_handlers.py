#!/usr/bin/env python3
"""
Test script to demonstrate the usage of handler classes.
This script shows how to use the handlers for various API operations.
"""

import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_db, engine
from app.models import Base, User, UserRole
from app.api.handlers import (
    AuthHandler, TestHandler, SessionHandler,
    ResultHandler, UserHandler, AdminHandler
)
from werkzeug.security import generate_password_hash

def create_test_data():
    """Create test data for demonstration."""
    db = next(get_db())

    try:
        # Check if users already exist
        admin_user = db.query(User).filter(User.username == "admin").first()
        regular_user = db.query(User).filter(User.username == "user1").first()

        if not admin_user:
            # Create a test admin user
            admin_user = User(
                username="admin",
                email="admin@examlify.com",
                password_hash=generate_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")

        if not regular_user:
            # Create a test regular user
            regular_user = User(
                username="user1",
                email="user1@examlify.com",
                password_hash=generate_password_hash("user123"),
                role=UserRole.USER
            )
            db.add(regular_user)
            print("✅ Regular user created")
        else:
            print("✅ Regular user already exists")

        db.commit()

        print(f"Admin user: {admin_user.username} (password: admin123)")
        print(f"Regular user: {regular_user.username} (password: user123)")

        return admin_user, regular_user

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        return None, None

def test_auth_handler():
    """Test authentication handler."""
    print("\n🔐 Testing AuthHandler...")

    db = next(get_db())
    auth_handler = AuthHandler(db)

    # Test login
    try:
        result = auth_handler.login("admin", "admin123")
        print(f"✅ Login successful: {result['user']['username']}")

        # Test get current user
        user = auth_handler.get_current_user(result['access_token'])
        print(f"✅ Current user retrieved: {user.username}")

        # Test auth status
        status = auth_handler.check_auth_status(result['access_token'])
        print(f"✅ Auth status: {status['authenticated']}")

        return result['access_token']

    except Exception as e:
        print(f"❌ Auth test failed: {e}")
        return None

def test_test_handler(token):
    """Test test management handler."""
    print("\n📝 Testing TestHandler...")

    db = next(get_db())
    test_handler = TestHandler(db)

    # Get current user
    auth_handler = AuthHandler(db)
    user = auth_handler.get_current_user(token)

    try:
        # Create a test
        test = test_handler.create_test(
            title="Sample Mathematics Test",
            description="A test covering basic algebra and calculus",
            user=user
        )
        print(f"✅ Test created: {test.title} (ID: {test.id})")

        # Get tests
        tests = test_handler.get_tests(user)
        print(f"✅ Retrieved {len(tests)} tests")

        # Get specific test
        test_details = test_handler.get_test(test.id, user)
        print(f"✅ Test details retrieved: {test_details.title}")

        return test.id

    except Exception as e:
        print(f"❌ Test handler test failed: {e}")
        return None

def test_session_handler(token, test_id):
    """Test session management handler."""
    print("\n⏱️ Testing SessionHandler...")

    db = next(get_db())
    session_handler = SessionHandler(db)

    # Get current user
    auth_handler = AuthHandler(db)
    user = auth_handler.get_current_user(token)

    try:
        # Start test session
        session = session_handler.start_test_session(
            test_id=test_id,
            user=user,
            duration_minutes=60
        )
        print(f"✅ Test session started: {session['session_id']}")

        # Get session status
        status = session_handler.get_session_status(session['session_id'], user)
        print(f"✅ Session status: {status['is_completed']}")

        return session['session_id']

    except Exception as e:
        print(f"❌ Session handler test failed: {e}")
        return None

def test_user_handler(token):
    """Test user management handler."""
    print("\n👤 Testing UserHandler...")

    db = next(get_db())
    user_handler = UserHandler(db)

    # Get current user
    auth_handler = AuthHandler(db)
    user = auth_handler.get_current_user(token)

    try:
        # Get user profile
        profile = user_handler.get_user_profile(user)
        print(f"✅ User profile retrieved: {profile['username']}")

        # Update user profile
        updated_user = user_handler.update_user_profile(
            user,
            {"email": "updated@examlify.com"}
        )
        print(f"✅ User profile updated: {updated_user.email}")

        return True

    except Exception as e:
        print(f"❌ User handler test failed: {e}")
        return False

def test_admin_handler(token):
    """Test admin handler."""
    print("\n🔧 Testing AdminHandler...")

    db = next(get_db())
    admin_handler = AdminHandler(db)

    # Get current user
    auth_handler = AuthHandler(db)
    user = auth_handler.get_current_user(token)

    try:
        # Get all users
        users = admin_handler.get_all_users(user)
        print(f"✅ Retrieved {len(users)} users")

        # Get system statistics
        stats = admin_handler.get_system_statistics(user)
        print(f"✅ System statistics retrieved: {stats['user_statistics']['total_users']} users")

        return True

    except Exception as e:
        print(f"❌ Admin handler test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting Handler Tests...")

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Create test data
    admin_user, regular_user = create_test_data()
    if not admin_user or not regular_user:
        print("❌ Failed to create test data. Exiting.")
        return

    # Test authentication
    token = test_auth_handler()
    if not token:
        print("❌ Authentication test failed. Exiting.")
        return

    # Test test management
    test_id = test_test_handler(token)
    if not test_id:
        print("❌ Test management test failed. Exiting.")
        return

    # Test session management
    session_id = test_session_handler(token, test_id)
    if not session_id:
        print("❌ Session management test failed. Exiting.")
        return

    # Test user management
    user_success = test_user_handler(token)
    if not user_success:
        print("❌ User management test failed. Exiting.")
        return

    # Test admin functionality
    admin_success = test_admin_handler(token)
    if not admin_success:
        print("❌ Admin functionality test failed. Exiting.")
        return

    print("\n🎉 All handler tests completed successfully!")

if __name__ == "__main__":
    main()