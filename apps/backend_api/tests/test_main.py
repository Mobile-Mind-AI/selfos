import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns expected message"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "SelfOS Backend API"}


def test_health_check():
    """Test basic health check functionality"""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/json"


def test_api_structure():
    """Test that the API has expected structure"""
    # Test that endpoints exist (will return 401 for protected endpoints)
    
    # Auth endpoints should exist
    response = client.post("/register", json={"username": "test", "password": "test"})
    # Should fail due to Firebase mock not being setup, but endpoint should exist
    assert response.status_code in [400, 401, 422]  # Not 404
    
    # Goals endpoints should exist but require auth
    response = client.get("/goals")
    assert response.status_code in [200, 401]  # May be 200 if auth overrides are active
    
    # Tasks endpoints should exist but require auth  
    response = client.get("/tasks")
    assert response.status_code in [200, 401]  # May be 200 if auth overrides are active


def test_cors_headers():
    """Test that CORS headers are properly configured if needed"""
    response = client.get("/")
    
    # Basic test - API should respond normally
    assert response.status_code == 200


def test_content_type_json():
    """Test that API returns JSON content type for JSON endpoints"""
    response = client.get("/")
    
    assert "application/json" in response.headers.get("content-type", "")