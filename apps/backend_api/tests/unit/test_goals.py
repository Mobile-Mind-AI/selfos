import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from dependencies import get_db, get_current_user
from models import Base

# Test database - isolated in-memory SQLite for this module
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables once
Base.metadata.create_all(bind=engine)

# Test client setup
client = TestClient(app)

# Test fixtures
@pytest.fixture
def db_session():
    """Create a test database session"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

def override_get_db_goals():
    """Override database dependency for testing goals"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_goals():
    """Override authentication dependency for testing goals"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_goals
app.dependency_overrides[get_current_user] = override_get_current_user_goals

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before each test"""
    # Clean up before each test  
    db = TestingSessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM media_attachments"))
        db.execute(text("DELETE FROM tasks"))
        db.execute(text("DELETE FROM goals"))
        db.execute(text("DELETE FROM life_areas"))
        db.execute(text("DELETE FROM users"))
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()
    yield

# Module cleanup
def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session"""
    # Clean up dependency overrides for this module
    app.dependency_overrides.clear()
    engine.dispose()


def test_create_goal():
    """Test creating a new goal"""
    goal_data = {
        "title": "Test Goal",
        "description": "Test Description",
        "status": "in_progress",
        "progress": 25.0,
        "life_area_id": None
    }
    
    response = client.post("/api/goals", json=goal_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test Goal"
    assert data["description"] == "Test Description"
    assert data["status"] == "in_progress"
    assert data["progress"] == 25.0
    assert data["user_id"] == "test_user_123"
    assert data["life_area_id"] is None


def test_create_goal_minimal():
    """Test creating a goal with minimal data"""
    goal_data = {
        "title": "Minimal Goal"
    }
    
    response = client.post("/api/goals", json=goal_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Goal"
    assert data["status"] == "todo"  # Default value
    assert data["progress"] == 0.0   # Default value
    assert data["life_area_id"] is None  # Default value


def test_list_goals():
    """Test listing user goals"""
    # First create a goal
    goal_data = {"title": "List Test Goal"}
    client.post("/api/goals", json=goal_data)
    
    response = client.get("/api/goals")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["user_id"] == "test_user_123"


def test_get_goal():
    """Test getting a specific goal"""
    # Create a goal first
    goal_data = {"title": "Get Test Goal"}
    create_response = client.post("/api/goals", json=goal_data)
    goal_id = create_response.json()["id"]
    
    response = client.get(f"/api/goals/{goal_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == goal_id
    assert data["title"] == "Get Test Goal"
    assert data["user_id"] == "test_user_123"


def test_get_goal_not_found():
    """Test getting a non-existent goal"""
    response = client.get("/api/goals/99999")
    
    assert response.status_code == 404
    assert "Goal not found" in response.json()["detail"]


def test_update_goal():
    """Test updating an existing goal"""
    # Create a goal first
    goal_data = {"title": "Original Goal"}
    create_response = client.post("/api/goals", json=goal_data)
    goal_id = create_response.json()["id"]
    
    # Update the goal
    update_data = {
        "title": "Updated Goal",
        "description": "Updated Description",
        "status": "completed",
        "progress": 100.0
    }
    
    response = client.put(f"/api/goals/{goal_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == goal_id
    assert data["title"] == "Updated Goal"
    assert data["description"] == "Updated Description"
    assert data["status"] == "completed"
    assert data["progress"] == 100.0


def test_update_goal_not_found():
    """Test updating a non-existent goal"""
    update_data = {"title": "Updated Goal"}
    response = client.put("/api/goals/99999", json=update_data)
    
    assert response.status_code == 404
    assert "Goal not found" in response.json()["detail"]


def test_delete_goal():
    """Test deleting an existing goal"""
    # Create a goal first
    goal_data = {"title": "Goal to Delete"}
    create_response = client.post("/api/goals", json=goal_data)
    goal_id = create_response.json()["id"]
    
    # Delete the goal
    response = client.delete(f"/api/goals/{goal_id}")
    
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/api/goals/{goal_id}")
    assert get_response.status_code == 404


def test_delete_goal_not_found():
    """Test deleting a non-existent goal"""
    response = client.delete("/api/goals/99999")
    
    assert response.status_code == 404
    assert "Goal not found" in response.json()["detail"]

