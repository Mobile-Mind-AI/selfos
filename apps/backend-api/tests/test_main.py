import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure app module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import main

app = main.app
client = TestClient(app)

@pytest.fixture(autouse=True)
def patch_firebase(monkeypatch):
    # Fake user creation
    class FakeUser:
        def __init__(self, uid, email):
            self.uid = uid
            self.email = email

    def fake_create_user(email, password):
        return FakeUser(uid=f"uid_{email}", email=email)

    monkeypatch.setattr(main.auth, "create_user", fake_create_user)

    # Fake custom token creation
    def fake_create_custom_token(uid):
        return f"token_{uid}".encode("utf-8")

    monkeypatch.setattr(main.auth, "create_custom_token", fake_create_custom_token)

    # Fake verify id token
    def fake_verify_id_token(token):
        if token == "valid_token":
            return {"uid": "uid_user1@example.com", "email": "user1@example.com", "roles": ["user"]}
        raise Exception("Invalid token")

    monkeypatch.setattr(main.auth, "verify_id_token", fake_verify_id_token)

    return monkeypatch

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SelfOS Backend API"}

def test_register():
    payload = {"username": "user1@example.com", "password": "pass"}
    response = client.post("/register", json=payload)
    assert response.status_code == 200
    assert response.json() == {"uid": "uid_user1@example.com", "email": "user1@example.com"}

def test_login():
    payload = {"username": "user1@example.com", "password": "pass"}
    response = client.post("/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("access_token") == "token_user1@example.com"
    assert data.get("token_type") == "bearer"

def test_me_unauthorized():
    response = client.get("/me")
    assert response.status_code == 401

def test_me_authorized():
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"uid": "uid_user1@example.com", "email": "user1@example.com", "roles": ["user"]}