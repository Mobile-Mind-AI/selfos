import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from dependencies import get_current_user

# Create isolated app instance for auth tests to avoid dependency override conflicts
from fastapi import FastAPI
from routers.auth import router as auth_router

# Create a clean app instance for auth tests
auth_test_app = FastAPI()
auth_test_app.include_router(auth_router)

# Add the root endpoint for consistency
@auth_test_app.get("/")
async def root():
    return {"message": "SelfOS Backend API"}

# Create test client with clean app
client = TestClient(auth_test_app)


@patch('firebase_admin.auth.create_user')
def test_register_success(mock_create_user):
    """Test successful user registration"""
    # Mock Firebase user creation
    mock_user = MagicMock()
    mock_user.uid = "test_uid_123"
    mock_user.email = "testuser@example.com"
    mock_create_user.return_value = mock_user
    
    response = client.post("/register", json={
        "username": "testuser@example.com", 
        "password": "testpassword"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "uid" in data
    assert data["email"] == "testuser@example.com"
    assert data["uid"] == "test_uid_123"


@patch('firebase_admin.auth.create_user')
def test_register_failure(mock_create_user):
    """Test user registration failure"""
    # Mock Firebase auth failure
    mock_create_user.side_effect = Exception("Email already exists")
    
    response = client.post("/register", json={
        "username": "existing@example.com", 
        "password": "testpassword"
    })
    
    assert response.status_code == 400
    assert "Email already exists" in response.json()["detail"]


@patch('firebase_admin.auth.create_custom_token')
def test_login_success(mock_create_token):
    """Test successful login"""
    # Mock Firebase custom token creation
    mock_create_token.return_value = b"mock_custom_token"
    
    response = client.post("/login", json={
        "username": "test_uid_123", 
        "password": "testpassword"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["access_token"] == "mock_custom_token"
    assert data["token_type"] == "bearer"


@patch('firebase_admin.auth.create_custom_token')
def test_login_failure(mock_create_token):
    """Test login failure with invalid credentials"""
    # Mock Firebase auth failure
    mock_create_token.side_effect = Exception("Invalid user ID")
    
    response = client.post("/login", json={
        "username": "invalid_uid", 
        "password": "wrongpassword"
    })
    
    assert response.status_code == 400
    assert "Invalid user ID" in response.json()["detail"]


@patch('firebase_admin.auth.verify_id_token')
def test_me_endpoint_success(mock_verify_token):
    """Test /me endpoint with valid token"""
    # Mock Firebase token verification
    mock_verify_token.return_value = {
        "uid": "test_uid_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }
    
    response = client.get("/me", headers={
        "Authorization": "Bearer valid_firebase_token"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == "test_uid_123"
    assert data["email"] == "testuser@example.com"
    assert data["roles"] == ["user"]


@patch('firebase_admin.auth.verify_id_token')
def test_me_endpoint_invalid_token(mock_verify_token):
    """Test /me endpoint with invalid token"""
    # Mock Firebase token verification failure
    mock_verify_token.side_effect = Exception("Invalid token")
    
    response = client.get("/me", headers={
        "Authorization": "Bearer invalid_token"
    })
    
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_me_endpoint_no_token():
    """Test /me endpoint without authorization header"""
    response = client.get("/api/me")
    
    assert response.status_code == 401

