import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path so tests can import main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SelfOS Backend API"}

def test_register():
    payload = {"username": "user1", "password": "pass"}
    response = client.post("/register", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "User 'user1' registered (stub)"}

def test_login():
    payload = {"username": "user1", "password": "pass"}
    response = client.post("/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"] == "fake.jwt.token"
    assert data["token_type"] == "bearer"

def test_me():
    response = client.get("/me")
    assert response.status_code == 200
    assert response.json() == {"username": "current_user_stub"}