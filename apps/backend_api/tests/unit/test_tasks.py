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

def override_get_db_tasks():
    """Override database dependency for testing tasks"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_tasks():
    """Override authentication dependency for testing tasks"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_tasks
app.dependency_overrides[get_current_user] = override_get_current_user_tasks

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


def test_create_task():
    """Test creating a new task"""
    # First create a goal
    goal_data = {"title": "Test Goal for Task"}
    goal_response = client.post("/api/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    # Create task
    task_data = {
        "goal_id": goal_id,
        "title": "Test Task",
        "description": "Test Task Description",
        "due_date": "2024-12-31T23:59:59",
        "duration": 120,
        "status": "in_progress",
        "progress": 25.0,
        "life_area_id": None,
        "dependencies": []
    }
    
    response = client.post("/api/tasks", json=task_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Task Description"
    assert data["goal_id"] == goal_id
    assert data["duration"] == 120
    assert data["status"] == "in_progress"
    assert data["progress"] == 25.0
    assert data["user_id"] == "test_user_123"
    assert data["life_area_id"] is None


def test_create_task_minimal():
    """Test creating a task with minimal data"""
    # First create a goal
    goal_data = {"title": "Test Goal for Minimal Task"}
    goal_response = client.post("/api/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    task_data = {
        "goal_id": goal_id,
        "title": "Minimal Task"
    }
    
    response = client.post("/api/tasks", json=task_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Task"
    assert data["status"] == "todo"  # Default value
    assert data["progress"] == 0.0   # Default value
    assert data["life_area_id"] is None  # Default value
    assert data["dependencies"] == [] # Default value


def test_list_tasks():
    """Test listing user tasks"""
    # Create a goal and task first
    goal_data = {"title": "Goal for List Test"}
    goal_response = client.post("/api/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    task_data = {"goal_id": goal_id, "title": "List Test Task"}
    client.post("/api/tasks", json=task_data)
    
    response = client.get("/api/tasks")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["user_id"] == "test_user_123"


def test_get_task():
    """Test getting a specific task"""
    # Create goal and task first
    goal_data = {"title": "Goal for Get Test"}
    goal_response = client.post("/api/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    task_data = {"goal_id": goal_id, "title": "Get Test Task"}
    create_response = client.post("/api/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    response = client.get(f"/api/tasks/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Get Test Task"
    assert data["goal_id"] == goal_id
    assert data["user_id"] == "test_user_123"


def test_get_task_not_found():
    """Test getting a non-existent task"""
    response = client.get("/api/tasks/99999")
    
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_update_task():
    """Test updating an existing task"""
    # Create goal and task first
    goal_data = {"title": "Goal for Update Test"}
    goal_response = client.post("/api/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    task_data = {"goal_id": goal_id, "title": "Original Task"}
    create_response = client.post("/api/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Update the task
    update_data = {
        "goal_id": goal_id,  # Required field
        "title": "Updated Task",
        "description": "Updated Description",
        "duration": 60,
        "status": "completed",
        "progress": 100.0
    }
    
    response = client.put(f"/api/tasks/{task_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Updated Task"
    assert data["description"] == "Updated Description"
    assert data["duration"] == 60
    assert data["status"] == "completed"
    assert data["progress"] == 100.0


def test_update_task_not_found():
    """Test updating a non-existent task"""
    update_data = {"goal_id": 1, "title": "Updated Task"}
    response = client.put("/api/tasks/99999", json=update_data)
    
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_delete_task():
    """Test deleting an existing task"""
    # Create goal and task first
    goal_data = {"title": "Goal for Delete Test"}
    goal_response = client.post("/api/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    task_data = {"goal_id": goal_id, "title": "Task to Delete"}
    create_response = client.post("/api/tasks", json=task_data)
    task_id = create_response.json()["id"]
    
    # Delete the task
    response = client.delete(f"/api/tasks/{task_id}")
    
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404


def test_delete_task_not_found():
    """Test deleting a non-existent task"""
    response = client.delete("/api/tasks/99999")
    
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]

