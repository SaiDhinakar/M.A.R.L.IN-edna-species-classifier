#!/usr/bin/env python3
"""
Create admin user for M.A.R.L.IN backend.
Run this script once to create the initial admin account.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.session import SessionLocal, init_db
from app.models.database_models import User
from app.core.security import get_password_hash


def create_admin_user(username: str = "admin", password: str = "admin123", email: str = "admin@marlin.ai"):
    """Create admin user if it doesn't exist."""
    
    # Ensure database is initialized
    init_db()
    
    db = SessionLocal()
    
    try:
        # Check if admin exists
        existing = db.query(User).filter(User.username == username).first()
        
        if existing:
            print(f"❌ User '{username}' already exists!")
            print(f"   Email: {existing.email}")
            print(f"   Role: {existing.role}")
            print(f"   Active: {existing.is_active}")
            return False
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✅ Admin user created successfully!")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Role: {admin.role}")
        print(f"   ID: {admin.id}")
        print()
        print("🔑 Login credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print()
        print("⚠️  Please change the password after first login!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


def create_test_user(username: str = "testuser", password: str = "testpass", email: str = "test@marlin.ai"):
    """Create a test regular user."""
    
    db = SessionLocal()
    
    try:
        existing = db.query(User).filter(User.username == username).first()
        
        if existing:
            print(f"❌ User '{username}' already exists!")
            return False
        
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role="user",
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("✅ Test user created successfully!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("M.A.R.L.IN eDNA Classifier - User Creation Script")
    print("=" * 60)
    print()
    
    # Create admin user
    print("Creating admin user...")
    create_admin_user()
    
    print()
    
    # Ask if user wants to create test user
    response = input("Create test regular user? (y/n): ").lower()
    if response == 'y':
        create_test_user()
    
    print()
    print("=" * 60)
    print("Done! You can now login to the API.")
    print("API Docs: http://localhost:8000/docs")
    print("=" * 60)
