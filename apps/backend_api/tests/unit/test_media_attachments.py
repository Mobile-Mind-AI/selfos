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

def override_get_db_media():
    """Override database dependency for testing media attachments"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_media():
    """Override authentication dependency for testing media attachments"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_media
app.dependency_overrides[get_current_user] = override_get_current_user_media

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


def test_create_media_attachment():
    """Test creating a new media attachment"""
    attachment_data = {
        "filename": "test_image_123.jpg",
        "original_filename": "vacation_photo.jpg",
        "file_path": "/uploads/user_123/test_image_123.jpg",
        "file_size": 1024000,  # 1MB
        "mime_type": "image/jpeg",
        "file_type": "image",
        "title": "Beautiful Sunset",
        "description": "A stunning sunset from our vacation",
        "width": 1920,
        "height": 1080
    }
    
    response = client.post("/media-attachments", json=attachment_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test_image_123.jpg"
    assert data["original_filename"] == "vacation_photo.jpg"
    assert data["file_path"] == "/uploads/user_123/test_image_123.jpg"
    assert data["file_size"] == 1024000
    assert data["mime_type"] == "image/jpeg"
    assert data["file_type"] == "image"
    assert data["title"] == "Beautiful Sunset"
    assert data["description"] == "A stunning sunset from our vacation"
    assert data["width"] == 1920
    assert data["height"] == 1080
    assert data["user_id"] == "test_user_123"
    assert data["goal_id"] is None
    assert data["task_id"] is None


def test_create_media_attachment_minimal():
    """Test creating a media attachment with minimal data"""
    attachment_data = {
        "filename": "minimal.mp3",
        "original_filename": "song.mp3",
        "file_path": "/uploads/minimal.mp3",
        "file_size": 5120000,  # 5MB
        "mime_type": "audio/mpeg",
        "file_type": "audio"
    }
    
    response = client.post("/media-attachments", json=attachment_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "minimal.mp3"
    assert data["file_type"] == "audio"
    assert data["title"] is None
    assert data["description"] is None
    assert data["duration"] is None
    assert data["width"] is None
    assert data["height"] is None


def test_create_media_attachment_with_goal():
    """Test creating a media attachment linked to a goal"""
    # First create a goal
    goal_data = {"title": "Test Goal for Media"}
    goal_response = client.post("/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    # Create attachment linked to goal
    attachment_data = {
        "goal_id": goal_id,
        "filename": "goal_video.mp4",
        "original_filename": "motivation.mp4",
        "file_path": "/uploads/goal_video.mp4",
        "file_size": 10240000,  # 10MB
        "mime_type": "video/mp4",
        "file_type": "video",
        "duration": 120,  # 2 minutes
        "width": 720,
        "height": 480
    }
    
    response = client.post("/media-attachments", json=attachment_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] == goal_id
    assert data["task_id"] is None
    assert data["file_type"] == "video"
    assert data["duration"] == 120


def test_create_media_attachment_with_task():
    """Test creating a media attachment linked to a task"""
    # First create a goal and task
    goal_data = {"title": "Test Goal for Task Media"}
    goal_response = client.post("/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    task_data = {"goal_id": goal_id, "title": "Test Task for Media"}
    task_response = client.post("/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Create attachment linked to task
    attachment_data = {
        "task_id": task_id,
        "filename": "task_doc.pdf",
        "original_filename": "requirements.pdf",
        "file_path": "/uploads/task_doc.pdf",
        "file_size": 2048000,  # 2MB
        "mime_type": "application/pdf",
        "file_type": "document",
        "title": "Project Requirements"
    }
    
    response = client.post("/media-attachments", json=attachment_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] is None
    assert data["task_id"] == task_id
    assert data["file_type"] == "document"
    assert data["title"] == "Project Requirements"


def test_create_media_attachment_invalid_goal():
    """Test creating media attachment with non-existent goal"""
    attachment_data = {
        "goal_id": 99999,  # Non-existent goal
        "filename": "test.jpg",
        "original_filename": "test.jpg",
        "file_path": "/uploads/test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    
    response = client.post("/media-attachments", json=attachment_data)
    
    assert response.status_code == 404
    assert "Goal not found" in response.json()["detail"]


def test_create_media_attachment_invalid_task():
    """Test creating media attachment with non-existent task"""
    attachment_data = {
        "task_id": 99999,  # Non-existent task
        "filename": "test.jpg",
        "original_filename": "test.jpg",
        "file_path": "/uploads/test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    
    response = client.post("/media-attachments", json=attachment_data)
    
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_list_media_attachments():
    """Test listing user media attachments"""
    # Create a test attachment first
    attachment_data = {
        "filename": "list_test.jpg",
        "original_filename": "list_test.jpg",
        "file_path": "/uploads/list_test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    client.post("/media-attachments", json=attachment_data)
    
    response = client.get("/media-attachments")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["user_id"] == "test_user_123"


def test_list_media_attachments_by_goal():
    """Test listing media attachments filtered by goal"""
    # Create goal and attachments
    goal_data = {"title": "Filter Test Goal"}
    goal_response = client.post("/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    # Create attachment for this goal
    attachment_data = {
        "goal_id": goal_id,
        "filename": "goal_filter.jpg",
        "original_filename": "goal_filter.jpg",
        "file_path": "/uploads/goal_filter.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    client.post("/media-attachments", json=attachment_data)
    
    # Create attachment not linked to goal
    attachment_data2 = {
        "filename": "no_goal.jpg",
        "original_filename": "no_goal.jpg",
        "file_path": "/uploads/no_goal.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    client.post("/media-attachments", json=attachment_data2)
    
    # Filter by goal
    response = client.get(f"/media-attachments?goal_id={goal_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["goal_id"] == goal_id
    assert data[0]["filename"] == "goal_filter.jpg"


def test_list_media_attachments_by_file_type():
    """Test listing media attachments filtered by file type"""
    # Create different file types
    image_data = {
        "filename": "test.jpg",
        "original_filename": "test.jpg",
        "file_path": "/uploads/test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    client.post("/media-attachments", json=image_data)
    
    video_data = {
        "filename": "test.mp4",
        "original_filename": "test.mp4", 
        "file_path": "/uploads/test.mp4",
        "file_size": 5120,
        "mime_type": "video/mp4",
        "file_type": "video"
    }
    client.post("/media-attachments", json=video_data)
    
    # Filter by image type
    response = client.get("/media-attachments?file_type=image")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["file_type"] == "image"


def test_get_media_attachment():
    """Test getting a specific media attachment"""
    # Create attachment first
    attachment_data = {
        "filename": "get_test.jpg",
        "original_filename": "get_test.jpg",
        "file_path": "/uploads/get_test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    create_response = client.post("/media-attachments", json=attachment_data)
    attachment_id = create_response.json()["id"]
    
    response = client.get(f"/media-attachments/{attachment_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == attachment_id
    assert data["filename"] == "get_test.jpg"
    assert data["user_id"] == "test_user_123"


def test_get_media_attachment_not_found():
    """Test getting a non-existent media attachment"""
    response = client.get("/media-attachments/99999")
    
    assert response.status_code == 404
    assert "Media attachment not found" in response.json()["detail"]


def test_update_media_attachment():
    """Test updating media attachment metadata"""
    # Create attachment first
    attachment_data = {
        "filename": "update_test.jpg",
        "original_filename": "update_test.jpg",
        "file_path": "/uploads/update_test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    create_response = client.post("/media-attachments", json=attachment_data)
    attachment_id = create_response.json()["id"]
    
    # Update metadata
    update_data = {
        "title": "Updated Title",
        "description": "Updated description for storytelling"
    }
    
    response = client.put(f"/media-attachments/{attachment_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == attachment_id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description for storytelling"
    # Original fields should remain unchanged
    assert data["filename"] == "update_test.jpg"
    assert data["file_size"] == 1024


def test_update_media_attachment_associations():
    """Test updating media attachment goal/task associations"""
    # Create goal and task
    goal_data = {"title": "Association Test Goal"}
    goal_response = client.post("/goals", json=goal_data)
    goal_id = goal_response.json()["id"]
    
    task_data = {"goal_id": goal_id, "title": "Association Test Task"}
    task_response = client.post("/tasks", json=task_data)
    task_id = task_response.json()["id"]
    
    # Create attachment
    attachment_data = {
        "filename": "association_test.jpg",
        "original_filename": "association_test.jpg",
        "file_path": "/uploads/association_test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    create_response = client.post("/media-attachments", json=attachment_data)
    attachment_id = create_response.json()["id"]
    
    # Update associations
    update_data = {
        "goal_id": goal_id,
        "task_id": task_id
    }
    
    response = client.put(f"/media-attachments/{attachment_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] == goal_id
    assert data["task_id"] == task_id


def test_update_media_attachment_not_found():
    """Test updating a non-existent media attachment"""
    update_data = {"title": "Updated Title"}
    response = client.put("/media-attachments/99999", json=update_data)
    
    assert response.status_code == 404
    assert "Media attachment not found" in response.json()["detail"]


def test_delete_media_attachment():
    """Test deleting a media attachment"""
    # Create attachment first
    attachment_data = {
        "filename": "delete_test.jpg",
        "original_filename": "delete_test.jpg",
        "file_path": "/uploads/delete_test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    create_response = client.post("/media-attachments", json=attachment_data)
    attachment_id = create_response.json()["id"]
    
    # Delete the attachment
    response = client.delete(f"/media-attachments/{attachment_id}")
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["detail"]
    
    # Verify it's deleted
    get_response = client.get(f"/media-attachments/{attachment_id}")
    assert get_response.status_code == 404


def test_delete_media_attachment_not_found():
    """Test deleting a non-existent media attachment"""
    response = client.delete("/media-attachments/99999")
    
    assert response.status_code == 404
    assert "Media attachment not found" in response.json()["detail"]


def test_get_media_statistics():
    """Test getting media attachment statistics"""
    # Create different types of attachments
    attachments = [
        {
            "filename": "image1.jpg",
            "original_filename": "image1.jpg",
            "file_path": "/uploads/image1.jpg",
            "file_size": 1000000,  # 1MB
            "mime_type": "image/jpeg",
            "file_type": "image"
        },
        {
            "filename": "image2.png",
            "original_filename": "image2.png",
            "file_path": "/uploads/image2.png",
            "file_size": 2000000,  # 2MB
            "mime_type": "image/png",
            "file_type": "image"
        },
        {
            "filename": "video1.mp4",
            "original_filename": "video1.mp4",
            "file_path": "/uploads/video1.mp4",
            "file_size": 5000000,  # 5MB
            "mime_type": "video/mp4",
            "file_type": "video"
        }
    ]
    
    for attachment in attachments:
        client.post("/media-attachments", json=attachment)
    
    response = client.get("/media-attachments/stats/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_attachments"] == 3
    assert data["total_size_bytes"] == 8000000  # 8MB total
    assert abs(data["total_size_mb"] - 7.63) < 0.1  # Allow for floating point precision
    assert len(data["by_file_type"]) == 2  # image and video
    
    # Check file type breakdown
    image_stats = next(ft for ft in data["by_file_type"] if ft["file_type"] == "image")
    video_stats = next(ft for ft in data["by_file_type"] if ft["file_type"] == "video")
    
    assert image_stats["count"] == 2
    assert image_stats["total_size_bytes"] == 3000000  # 3MB
    assert video_stats["count"] == 1
    assert video_stats["total_size_bytes"] == 5000000  # 5MB


def test_user_isolation():
    """Test that users can only access their own media attachments"""
    # Create attachment as test_user_123
    attachment_data = {
        "filename": "isolation_test.jpg",
        "original_filename": "isolation_test.jpg",
        "file_path": "/uploads/isolation_test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_type": "image"
    }
    create_response = client.post("/media-attachments", json=attachment_data)
    attachment_id = create_response.json()["id"]
    
    # Verify user can access their attachment
    user_attachments = client.get("/media-attachments").json()
    assert len(user_attachments) >= 1
    for attachment in user_attachments:
        assert attachment["user_id"] == "test_user_123"
    
    # Create a separate TestClient with different user override to avoid interference
    from fastapi.testclient import TestClient
    from main import app as test_app
    
    # Create a fresh app instance for the different user test
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
        
        # Different user should see no attachments
        different_user_attachments = different_client.get("/media-attachments").json()
        assert len(different_user_attachments) == 0
        
        # Different user should not access specific attachment
        attachment_response = different_client.get(f"/media-attachments/{attachment_id}")
        assert attachment_response.status_code == 404
        
    finally:
        # Always restore original override
        if original_override:
            test_app.dependency_overrides[get_current_user] = original_override
        else:
            test_app.dependency_overrides.pop(get_current_user, None)