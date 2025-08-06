#!/usr/bin/env python3

"""
Simple test to verify tags system works with TestClient
"""

import sys
import os

# Add the backend_api directory to the Python path
backend_api_dir = os.path.dirname(os.path.abspath(__file__))
if backend_api_dir not in sys.path:
    sys.path.append(backend_api_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

# Import all models to ensure tables are created
from models import Base, Tag
from main import app
from dependencies import get_db, get_current_user

def test_tags_with_testclient():
    """Test tags system with FastAPI TestClient"""
    
    # Create test database
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Check if tables exist
    with engine.connect() as connection:
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result.fetchall()]
        print("Created tables:", tables)
        
        # Check tags table structure
        if 'tags' in tables:
            result = connection.execute(text("PRAGMA table_info(tags);"))
            columns = [row[1] for row in result.fetchall()]  # row[1] is column name
            print("Tags table columns:", columns)
        else:
            print("ERROR: Tags table not found!")
            return False
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def override_get_current_user():
        return {
            "uid": "test_user_123",
            "email": "testuser@example.com",
            "roles": ["user"]
        }
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    # Test with client
    with TestClient(app) as client:
        # Test API endpoint
        response = client.post(
            "/api/tags/",
            json={"name": "Test Tag", "color": "#FF5722"},
            headers={"Authorization": "Bearer fake-token"}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 201:
            print("✅ Tags system working correctly!")
            return True
        else:
            print("❌ Tags system has issues")
            return False
    
    # Clean up
    app.dependency_overrides.clear()
    engine.dispose()

if __name__ == "__main__":
    success = test_tags_with_testclient()
    sys.exit(0 if success else 1)
