import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
from datetime import datetime

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
        "uid": "test_user_feedback_123",
        "email": "feedbackuser@example.com",
        "roles": ["user"]
    }

def override_get_db_feedback_logs():
    """Override database dependency for testing feedback logs"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_feedback_logs():
    """Override authentication dependency for testing feedback logs"""
    return {
        "uid": "test_user_feedback_123",
        "email": "feedbackuser@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_feedback_logs
app.dependency_overrides[get_current_user] = override_get_current_user_feedback_logs

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before each test"""
    # Clean up before each test  
    db = TestingSessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM feedback_logs"))
        db.execute(text("DELETE FROM user_preferences"))
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


def test_create_feedback_log():
    """Test creating a new feedback log"""
    feedback_data = {
        "context_type": "task",
        "context_id": "task_123",
        "context_data": {"action": "complete", "task_title": "Test Task"},
        "feedback_type": "positive",
        "feedback_value": 0.8,
        "comment": "Task completion worked great!",
        "session_id": "session_abc123"
    }
    
    response = client.post("/api/feedback-logs", json=feedback_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "test_user_feedback_123"
    assert data["context_type"] == "task"
    assert data["context_id"] == "task_123"
    assert data["feedback_type"] == "positive"
    assert data["feedback_value"] == 0.8
    assert data["comment"] == "Task completion worked great!"
    assert data["session_id"] == "session_abc123"
    assert "id" in data
    assert "created_at" in data


def test_create_minimal_feedback_log():
    """Test creating a feedback log with minimal required fields"""
    feedback_data = {
        "context_type": "ui_interaction",
        "feedback_type": "neutral"
    }
    
    response = client.post("/api/feedback-logs", json=feedback_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["context_type"] == "ui_interaction"
    assert data["feedback_type"] == "neutral"
    assert data["feedback_value"] is None
    assert data["comment"] is None


def test_get_feedback_logs():
    """Test retrieving feedback logs"""
    # Create some feedback logs first
    feedback_entries = [
        {
            "context_type": "task",
            "feedback_type": "positive",
            "comment": "First feedback"
        },
        {
            "context_type": "goal",
            "feedback_type": "negative",
            "comment": "Second feedback"
        },
        {
            "context_type": "suggestion",
            "feedback_type": "neutral",
            "comment": "Third feedback"
        }
    ]
    
    created_ids = []
    for feedback_data in feedback_entries:
        response = client.post("/api/feedback-logs", json=feedback_data)
        assert response.status_code == 201
        created_ids.append(response.json()["id"])
    
    # Get all feedback logs
    response = client.get("/api/feedback-logs")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(log["user_id"] == "test_user_feedback_123" for log in data)


def test_get_feedback_logs_with_filtering():
    """Test retrieving feedback logs with filters"""
    # Create feedback logs with different types
    feedback_entries = [
        {"context_type": "task", "feedback_type": "positive"},
        {"context_type": "task", "feedback_type": "negative"},
        {"context_type": "goal", "feedback_type": "positive"},
        {"context_type": "goal", "feedback_type": "neutral"}
    ]
    
    for feedback_data in feedback_entries:
        response = client.post("/api/feedback-logs", json=feedback_data)
        assert response.status_code == 201
    
    # Filter by context_type
    response = client.get("/api/feedback-logs?context_type=task")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(log["context_type"] == "task" for log in data)
    
    # Filter by feedback_type
    response = client.get("/api/feedback-logs?feedback_type=positive")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(log["feedback_type"] == "positive" for log in data)
    
    # Filter by both
    response = client.get("/api/feedback-logs?context_type=goal&feedback_type=positive")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["context_type"] == "goal"
    assert data[0]["feedback_type"] == "positive"


def test_get_feedback_logs_pagination():
    """Test pagination of feedback logs"""
    # Create 10 feedback logs
    for i in range(10):
        feedback_data = {
            "context_type": "test",
            "feedback_type": "neutral",
            "comment": f"Feedback {i}"
        }
        response = client.post("/api/feedback-logs", json=feedback_data)
        assert response.status_code == 201
    
    # Test limit
    response = client.get("/api/feedback-logs?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Test offset
    response = client.get("/api/feedback-logs?limit=5&offset=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_get_single_feedback_log():
    """Test retrieving a single feedback log"""
    feedback_data = {
        "context_type": "plan",
        "feedback_type": "positive",
        "comment": "Great planning suggestion!"
    }
    
    create_response = client.post("/api/feedback-logs", json=feedback_data)
    assert create_response.status_code == 201
    feedback_id = create_response.json()["id"]
    
    # Get the specific feedback log
    response = client.get(f"/api/feedback-logs/{feedback_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == feedback_id
    assert data["context_type"] == "plan"
    assert data["comment"] == "Great planning suggestion!"


def test_get_nonexistent_feedback_log():
    """Test retrieving a feedback log that doesn't exist"""
    response = client.get("/api/feedback-logs/nonexistent-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_feedback_log():
    """Test updating a feedback log"""
    feedback_data = {
        "context_type": "suggestion",
        "feedback_type": "neutral",
        "comment": "Initial comment"
    }
    
    create_response = client.post("/api/feedback-logs", json=feedback_data)
    assert create_response.status_code == 201
    feedback_id = create_response.json()["id"]
    
    # Update the feedback log
    update_data = {
        "comment": "Updated comment with more details",
        "processed_at": "2024-01-01T12:00:00"
    }
    
    response = client.put(f"/api/feedback-logs/{feedback_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["comment"] == "Updated comment with more details"
    assert data["processed_at"] is not None


def test_update_nonexistent_feedback_log():
    """Test updating a feedback log that doesn't exist"""
    update_data = {"comment": "Updated comment"}
    
    response = client.put("/api/feedback-logs/nonexistent-id", json=update_data)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_feedback_log():
    """Test deleting a feedback log"""
    feedback_data = {
        "context_type": "test",
        "feedback_type": "negative"
    }
    
    create_response = client.post("/api/feedback-logs", json=feedback_data)
    assert create_response.status_code == 201
    feedback_id = create_response.json()["id"]
    
    # Delete the feedback log
    response = client.delete(f"/api/feedback-logs/{feedback_id}")
    
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/api/feedback-logs/{feedback_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_feedback_log():
    """Test deleting a feedback log that doesn't exist"""
    response = client.delete("/api/feedback-logs/nonexistent-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_feedback_summary():
    """Test getting feedback summary statistics"""
    # Create various feedback logs
    feedback_entries = [
        {"context_type": "task", "feedback_type": "positive", "feedback_value": 0.8},
        {"context_type": "task", "feedback_type": "positive", "feedback_value": 0.9},
        {"context_type": "goal", "feedback_type": "negative", "feedback_value": -0.5},
        {"context_type": "suggestion", "feedback_type": "neutral", "feedback_value": 0.0},
        {"context_type": "ui_interaction", "feedback_type": "positive", "feedback_value": 0.7}
    ]
    
    for feedback_data in feedback_entries:
        response = client.post("/api/feedback-logs", json=feedback_data)
        assert response.status_code == 201
    
    # Get summary
    response = client.get("/api/feedback-logs/summary/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_feedback"] == 5
    assert data["positive_count"] == 3
    assert data["negative_count"] == 1
    assert data["neutral_count"] == 1
    assert abs(data["average_score"] - 0.38) < 0.01  # (0.8 + 0.9 - 0.5 + 0.0 + 0.7) / 5
    assert "context_breakdown" in data
    assert data["context_breakdown"]["task"] == 2
    assert data["context_breakdown"]["goal"] == 1
    assert len(data["recent_feedback"]) == 5


def test_get_context_type_options():
    """Test getting context type options"""
    response = client.get("/api/feedback-logs/context-types/options")
    
    assert response.status_code == 200
    data = response.json()
    assert "context_types" in data
    
    context_types = data["context_types"]
    assert len(context_types) > 0
    
    # Check that expected context types are present
    context_values = [option["value"] for option in context_types]
    expected_types = ["task", "goal", "plan", "suggestion", "ui_interaction"]
    for context_type in expected_types:
        assert context_type in context_values


def test_create_bulk_feedback_logs():
    """Test creating multiple feedback logs in bulk"""
    bulk_data = [
        {"context_type": "task", "feedback_type": "positive"},
        {"context_type": "goal", "feedback_type": "negative"},
        {"context_type": "plan", "feedback_type": "neutral"}
    ]
    
    response = client.post("/api/feedback-logs/bulk", json=bulk_data)
    
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3
    assert all(log["user_id"] == "test_user_feedback_123" for log in data)
    assert data[0]["context_type"] == "task"
    assert data[1]["context_type"] == "goal"
    assert data[2]["context_type"] == "plan"


def test_bulk_create_limit():
    """Test bulk create limit enforcement"""
    # Try to create more than 100 entries
    bulk_data = [{"context_type": "test", "feedback_type": "neutral"} for _ in range(101)]
    
    response = client.post("/api/feedback-logs/bulk", json=bulk_data)
    
    assert response.status_code == 400
    assert "Cannot create more than 100" in response.json()["detail"]


def test_delete_bulk_feedback_logs():
    """Test deleting multiple feedback logs in bulk"""
    # Create some feedback logs
    feedback_entries = [
        {"context_type": "task", "feedback_type": "positive"},
        {"context_type": "goal", "feedback_type": "negative"},
        {"context_type": "plan", "feedback_type": "neutral"}
    ]
    
    created_ids = []
    for feedback_data in feedback_entries:
        response = client.post("/api/feedback-logs", json=feedback_data)
        assert response.status_code == 201
        created_ids.append(response.json()["id"])
    
    # Delete them in bulk
    response = client.post("/api/feedback-logs/bulk-delete", json={"feedback_ids": created_ids})
    
    assert response.status_code == 204
    
    # Verify they're deleted
    for feedback_id in created_ids:
        get_response = client.get(f"/api/feedback-logs/{feedback_id}")
        assert get_response.status_code == 404


def test_bulk_delete_limit():
    """Test bulk delete limit enforcement"""
    # Try to delete more than 100 entries
    fake_ids = [f"id_{i}" for i in range(101)]
    
    response = client.post("/api/feedback-logs/bulk-delete", json={"feedback_ids": fake_ids})
    
    assert response.status_code == 400
    assert "Cannot delete more than 100" in response.json()["detail"]


def test_bulk_delete_nonexistent_ids():
    """Test bulk delete with some nonexistent IDs"""
    response = client.post("/api/feedback-logs/bulk-delete", json={"feedback_ids": ["nonexistent1", "nonexistent2"]})
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_feedback_validation():
    """Test various validation scenarios"""
    
    # Test invalid feedback_type
    response = client.post(
        "/api/feedback-logs", 
        json={"context_type": "task", "feedback_type": "invalid_type"}
    )
    assert response.status_code == 422
    
    # Test missing required fields
    response = client.post("/api/feedback-logs", json={"feedback_type": "positive"})
    assert response.status_code == 422
    
    response = client.post("/api/feedback-logs", json={"context_type": "task"})
    assert response.status_code == 422


def test_feedback_value_validation():
    """Test feedback_value range validation"""
    
    # Valid feedback values
    valid_values = [-1.0, -0.5, 0.0, 0.5, 1.0]
    for value in valid_values:
        response = client.post("/api/feedback-logs", json={
            "context_type": "test",
            "feedback_type": "neutral",
            "feedback_value": value
        })
        assert response.status_code == 201
    
    # Invalid feedback values (outside -1.0 to 1.0 range)
    invalid_values = [-1.1, 1.1, -2.0, 2.0]
    for value in invalid_values:
        response = client.post("/api/feedback-logs", json={
            "context_type": "test",
            "feedback_type": "neutral",
            "feedback_value": value
        })
        assert response.status_code == 422


def test_user_isolation():
    """Test that users can only access their own feedback logs"""
    # Create feedback log as test_user_feedback_123
    feedback_data = {"context_type": "task", "feedback_type": "positive"}
    create_response = client.post("/api/feedback-logs", json=feedback_data)
    assert create_response.status_code == 201
    feedback_id = create_response.json()["id"]
    
    # Verify user can access their feedback
    user_logs = client.get("/api/feedback-logs").json()
    assert len(user_logs) == 1
    assert user_logs[0]["user_id"] == "test_user_feedback_123"
    
    # Create a separate TestClient with different user override to avoid interference  
    from fastapi.testclient import TestClient
    from main import app as test_app
    
    def override_get_different_user():
        return {
            "uid": "different_user_456", 
            "email": "different@example.com",
            "roles": ["user"]
        }
    
    # Store original override
    original_override = test_app.dependency_overrides.get(get_current_user)
    
    try:
        # Temporarily override for different user
        test_app.dependency_overrides[get_current_user] = override_get_different_user
        different_client = TestClient(test_app)
        
        # Different user should not see the feedback log
        different_user_logs = different_client.get("/api/feedback-logs").json()
        assert len(different_user_logs) == 0
        
        # Different user should not be able to access the specific feedback log
        access_response = different_client.get(f"/api/feedback-logs/{feedback_id}")
        assert access_response.status_code == 404
    
    finally:
        # Always restore original override
        if original_override:
            test_app.dependency_overrides[get_current_user] = original_override
        else:
            test_app.dependency_overrides.pop(get_current_user, None)


def test_session_grouping():
    """Test session ID grouping functionality"""
    session_id = "session_test_123"
    
    # Create multiple feedback logs with the same session ID
    for i in range(3):
        feedback_data = {
            "context_type": f"test_{i}",
            "feedback_type": "neutral",
            "session_id": session_id
        }
        response = client.post("/api/feedback-logs", json=feedback_data)
        assert response.status_code == 201
    
    # Create one with a different session ID
    feedback_data = {
        "context_type": "other",
        "feedback_type": "positive",
        "session_id": "different_session"
    }
    response = client.post("/api/feedback-logs", json=feedback_data)
    assert response.status_code == 201
    
    # Filter by session ID
    response = client.get(f"/api/feedback-logs?session_id={session_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(log["session_id"] == session_id for log in data)