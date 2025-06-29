import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
from datetime import datetime, timedelta

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
        "uid": "test_user_story_123",
        "email": "storyuser@example.com",
        "roles": ["user"]
    }

def override_get_db_story_sessions():
    """Override database dependency for testing story sessions"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_story_sessions():
    """Override authentication dependency for testing story sessions"""
    return {
        "uid": "test_user_story_123",
        "email": "storyuser@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_story_sessions
app.dependency_overrides[get_current_user] = override_get_current_user_story_sessions

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before each test"""
    # Clean up before each test  
    db = TestingSessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM story_sessions"))
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


def test_create_story_session():
    """Test creating a new story session"""
    session_data = {
        "title": "Weekly Progress Story",
        "summary_period": "weekly",
        "content_type": "story",
        "generation_prompt": "Create an inspiring story about my weekly achievements",
        "word_count": 250,
        "estimated_read_time": 60
    }
    
    response = client.post("/story-sessions", json=session_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user_story_123"
    assert data["title"] == "Weekly Progress Story"
    assert data["summary_period"] == "weekly"
    assert data["content_type"] == "story"
    assert data["word_count"] == 250
    assert data["estimated_read_time"] == 60
    assert data["processing_status"] == "pending"
    assert data["posting_status"] == "draft"
    assert "id" in data
    assert "created_at" in data


def test_create_minimal_story_session():
    """Test creating a story session with minimal required fields"""
    session_data = {
        "summary_period": "monthly",
        "content_type": "summary"
    }
    
    response = client.post("/story-sessions", json=session_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["summary_period"] == "monthly"
    assert data["content_type"] == "summary"
    assert data["processing_status"] == "pending"
    assert data["posting_status"] == "draft"


def test_create_story_session_with_sources():
    """Test creating a story session with source references"""
    # First create some goals and life areas
    life_area_response = client.post("/life-areas", json={"name": "Health & Fitness"})
    life_area_id = life_area_response.json()["id"]
    
    goal_response = client.post("/goals", json={
        "title": "Run 5K",
        "life_area_id": life_area_id
    })
    goal_id = goal_response.json()["id"]
    
    task_response = client.post("/tasks", json={
        "title": "Morning run",
        "goal_id": goal_id
    })
    task_id = task_response.json()["id"]
    
    session_data = {
        "title": "Fitness Journey Story",
        "summary_period": "weekly",
        "content_type": "achievement",
        "source_goals": [goal_id],
        "source_tasks": [task_id],
        "source_life_areas": [life_area_id]
    }
    
    response = client.post("/story-sessions", json=session_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["source_goals"] == [goal_id]
    assert data["source_tasks"] == [task_id]
    assert data["source_life_areas"] == [life_area_id]


def test_create_story_session_invalid_sources():
    """Test creating a story session with invalid source references"""
    session_data = {
        "title": "Invalid Story",
        "summary_period": "weekly",
        "source_goals": [99999],  # Non-existent goal
        "source_tasks": [99999]   # Non-existent task
    }
    
    response = client.post("/story-sessions", json=session_data)
    
    assert response.status_code == 400
    assert "do not exist" in response.json()["detail"]


def test_get_story_sessions():
    """Test retrieving story sessions"""
    # Create some story sessions first
    sessions = [
        {
            "title": "Weekly Story 1",
            "summary_period": "weekly",
            "content_type": "story"
        },
        {
            "title": "Monthly Summary",
            "summary_period": "monthly", 
            "content_type": "summary"
        },
        {
            "title": "Achievement Reflection",
            "summary_period": "project-based",
            "content_type": "reflection"
        }
    ]
    
    created_ids = []
    for session_data in sessions:
        response = client.post("/story-sessions", json=session_data)
        assert response.status_code == 200
        created_ids.append(response.json()["id"])
    
    # Get all story sessions
    response = client.get("/story-sessions")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(session["user_id"] == "test_user_story_123" for session in data)


def test_get_story_sessions_with_filtering():
    """Test retrieving story sessions with filters"""
    # Create story sessions with different attributes
    sessions = [
        {"summary_period": "weekly", "content_type": "story", "posting_status": "draft"},
        {"summary_period": "weekly", "content_type": "summary", "posting_status": "posted"},
        {"summary_period": "monthly", "content_type": "story", "posting_status": "draft"},
        {"summary_period": "monthly", "content_type": "reflection", "posting_status": "scheduled"}
    ]
    
    for session_data in sessions:
        response = client.post("/story-sessions", json=session_data)
        assert response.status_code == 200
    
    # Filter by content_type
    response = client.get("/story-sessions?content_type=story")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(session["content_type"] == "story" for session in data)
    
    # Filter by summary_period
    response = client.get("/story-sessions?summary_period=weekly")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(session["summary_period"] == "weekly" for session in data)
    
    # Filter by posting_status
    response = client.get("/story-sessions?posting_status=draft")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(session["posting_status"] == "draft" for session in data)


def test_get_story_sessions_pagination():
    """Test pagination of story sessions"""
    # Create 10 story sessions
    for i in range(10):
        session_data = {
            "title": f"Story {i}",
            "summary_period": "daily",
            "content_type": "summary"
        }
        response = client.post("/story-sessions", json=session_data)
        assert response.status_code == 200
    
    # Test limit
    response = client.get("/story-sessions?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Test offset
    response = client.get("/story-sessions?limit=5&offset=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_get_single_story_session():
    """Test retrieving a single story session"""
    session_data = {
        "title": "Test Story Session",
        "summary_period": "weekly",
        "content_type": "story",
        "generated_text": "This is a test story about weekly progress."
    }
    
    create_response = client.post("/story-sessions", json=session_data)
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    
    # Get the specific story session
    response = client.get(f"/story-sessions/{session_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["title"] == "Test Story Session"
    assert data["view_count"] == 1  # Should increment on view


def test_get_nonexistent_story_session():
    """Test retrieving a story session that doesn't exist"""
    response = client.get("/story-sessions/nonexistent-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_story_session():
    """Test updating a story session"""
    session_data = {
        "title": "Original Title",
        "summary_period": "weekly",
        "content_type": "summary",
        "processing_status": "pending"
    }
    
    create_response = client.post("/story-sessions", json=session_data)
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    
    # Update the story session
    update_data = {
        "title": "Updated Title",
        "generated_text": "This is the generated story content.",
        "word_count": 150,
        "processing_status": "completed",
        "user_rating": 4.5
    }
    
    response = client.put(f"/story-sessions/{session_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["generated_text"] == "This is the generated story content."
    assert data["word_count"] == 150
    assert data["processing_status"] == "completed"
    assert data["user_rating"] == 4.5


def test_update_nonexistent_story_session():
    """Test updating a story session that doesn't exist"""
    update_data = {"title": "Updated Title"}
    
    response = client.put("/story-sessions/nonexistent-id", json=update_data)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_story_session():
    """Test deleting a story session"""
    session_data = {
        "title": "Session to Delete",
        "summary_period": "weekly",
        "content_type": "story"
    }
    
    create_response = client.post("/story-sessions", json=session_data)
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    
    # Delete the story session
    response = client.delete(f"/story-sessions/{session_id}")
    
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/story-sessions/{session_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_story_session():
    """Test deleting a story session that doesn't exist"""
    response = client.delete("/story-sessions/nonexistent-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_story_sessions_summary():
    """Test getting story sessions summary statistics"""
    # Create various story sessions
    sessions = [
        {"content_type": "story", "posting_status": "draft", "processing_status": "completed", "word_count": 300, "user_rating": 4.0},
        {"content_type": "story", "posting_status": "posted", "processing_status": "completed", "word_count": 250, "user_rating": 5.0},
        {"content_type": "summary", "posting_status": "draft", "processing_status": "pending", "word_count": 150, "user_rating": 3.5},
        {"content_type": "reflection", "posting_status": "scheduled", "processing_status": "completed", "word_count": 400, "user_rating": 4.5},
        {"content_type": "achievement", "posting_status": "posted", "processing_status": "failed", "word_count": 200}
    ]
    
    for session_data in sessions:
        response = client.post("/story-sessions", json=session_data)
        assert response.status_code == 200
    
    # Get summary
    response = client.get("/story-sessions/summary/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_sessions"] == 5
    assert data["by_content_type"]["story"] == 2
    assert data["by_content_type"]["summary"] == 1
    assert data["by_posting_status"]["draft"] == 2
    assert data["by_posting_status"]["posted"] == 2
    assert data["by_processing_status"]["completed"] == 3
    assert data["by_processing_status"]["pending"] == 1
    assert data["total_word_count"] == 1300  # 300 + 250 + 150 + 400 + 200
    assert abs(data["average_rating"] - 4.25) < 0.01  # (4.0 + 5.0 + 3.5 + 4.5) / 4
    assert len(data["recent_sessions"]) == 5


def test_generate_story_request():
    """Test requesting story generation"""
    # Create a goal and task for the generation
    life_area_response = client.post("/life-areas", json={"name": "Personal Growth"})
    life_area_id = life_area_response.json()["id"]
    
    goal_response = client.post("/goals", json={
        "title": "Learn Python",
        "life_area_id": life_area_id
    })
    goal_id = goal_response.json()["id"]
    
    # Use current date range to ensure goals are included
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    period_start = (now - timedelta(days=1)).isoformat()
    period_end = (now + timedelta(days=1)).isoformat()
    
    generation_data = {
        "title": "Weekly Learning Progress",
        "summary_period": "weekly",
        "period_start": period_start,
        "period_end": period_end,
        "content_type": "story",
        "generation_prompt": "Create an inspiring story about my learning journey",
        "include_goals": True,
        "include_tasks": True,
        "include_life_areas": [life_area_id]
    }
    
    response = client.post("/story-sessions/generate", json=generation_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Weekly Learning Progress"
    assert data["summary_period"] == "weekly"
    assert data["content_type"] == "story"
    assert data["processing_status"] == "pending"
    assert data["source_goals"] == [goal_id]
    assert life_area_id in data["source_life_areas"]


def test_publish_story_session():
    """Test publishing a story session"""
    # Create a completed story session
    session_data = {
        "title": "Completed Story",
        "summary_period": "weekly",
        "content_type": "story",
        "generated_text": "This is a completed story ready for publishing.",
        "processing_status": "completed"
    }
    
    create_response = client.post("/story-sessions", json=session_data)
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    
    # Publish the story
    publish_data = {
        "platforms": ["instagram", "twitter"],
        "custom_message": "Check out my weekly progress story!"
    }
    
    response = client.post(f"/story-sessions/{session_id}/publish", json=publish_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["posted_to"] == ["instagram", "twitter"]
    assert data["posting_status"] == "posted"
    assert data["posted_at"] is not None


def test_publish_incomplete_story_session():
    """Test publishing a story session that's not ready"""
    session_data = {
        "title": "Incomplete Story",
        "summary_period": "weekly",
        "processing_status": "pending"  # Not completed
    }
    
    create_response = client.post("/story-sessions", json=session_data)
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    
    publish_data = {
        "platforms": ["instagram"]
    }
    
    response = client.post(f"/story-sessions/{session_id}/publish", json=publish_data)
    
    assert response.status_code == 400
    assert "hasn't been generated" in response.json()["detail"]


def test_regenerate_story_session():
    """Test regenerating a story session"""
    session_data = {
        "title": "Story to Regenerate",
        "summary_period": "weekly",
        "content_type": "story",
        "generated_text": "Original story content",
        "processing_status": "completed",
        "regeneration_count": 0
    }
    
    create_response = client.post("/story-sessions", json=session_data)
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    
    # Regenerate the story without request body (test default behavior)
    response = client.post(f"/story-sessions/{session_id}/regenerate")
    
    assert response.status_code == 200
    data = response.json()
    assert data["regeneration_count"] == 1
    assert data["processing_status"] == "pending"


def test_get_content_type_options():
    """Test getting content type options"""
    response = client.get("/story-sessions/content-types/options")
    
    assert response.status_code == 200
    data = response.json()
    assert "content_types" in data
    
    content_types = data["content_types"]
    assert len(content_types) == 4
    
    # Check that expected content types are present
    content_values = [option["value"] for option in content_types]
    expected_types = ["summary", "story", "reflection", "achievement"]
    for content_type in expected_types:
        assert content_type in content_values


def test_get_period_options():
    """Test getting summary period options"""
    response = client.get("/story-sessions/periods/options")
    
    assert response.status_code == 200
    data = response.json()
    assert "periods" in data
    
    periods = data["periods"]
    assert len(periods) > 0
    
    # Check that expected periods are present
    period_values = [option["value"] for option in periods]
    expected_periods = ["daily", "weekly", "monthly", "project-based", "custom"]
    for period in expected_periods:
        assert period in period_values


def test_get_platform_options():
    """Test getting publishing platform options"""
    response = client.get("/story-sessions/platforms/options")
    
    assert response.status_code == 200
    data = response.json()
    assert "platforms" in data
    
    platforms = data["platforms"]
    assert len(platforms) > 0
    
    # Check that expected platforms are present
    platform_values = [option["value"] for option in platforms]
    expected_platforms = ["instagram", "youtube", "twitter", "linkedin"]
    for platform in expected_platforms:
        assert platform in platform_values


def test_story_session_validation():
    """Test various validation scenarios"""
    
    # Test invalid content_type
    response = client.post(
        "/story-sessions", 
        json={"summary_period": "weekly", "content_type": "invalid_type"}
    )
    assert response.status_code == 422
    
    # Test invalid posting_status
    response = client.post(
        "/story-sessions", 
        json={"summary_period": "weekly", "posting_status": "invalid_status"}
    )
    assert response.status_code == 422
    
    # Test invalid user_rating (outside 1-5 range)
    response = client.post(
        "/story-sessions", 
        json={"summary_period": "weekly", "user_rating": 6.0}
    )
    assert response.status_code == 422


def test_user_isolation():
    """Test that users can only access their own story sessions"""
    # Create story session as test_user_story_123
    session_data = {"title": "My Story", "summary_period": "weekly", "content_type": "story"}
    create_response = client.post("/story-sessions", json=session_data)
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    
    # Verify user can access their story session
    user_sessions = client.get("/story-sessions").json()
    assert len(user_sessions) == 1
    assert user_sessions[0]["user_id"] == "test_user_story_123"
    
    # Create a separate TestClient with different user override
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
        
        # Different user should not see the story session
        different_user_sessions = different_client.get("/story-sessions").json()
        assert len(different_user_sessions) == 0
        
        # Different user should not be able to access the specific story session
        access_response = different_client.get(f"/story-sessions/{session_id}")
        assert access_response.status_code == 404
    
    finally:
        # Always restore original override
        if original_override:
            test_app.dependency_overrides[get_current_user] = original_override
        else:
            test_app.dependency_overrides.pop(get_current_user, None)


def test_story_session_timestamps():
    """Test that created_at and updated_at timestamps work correctly"""
    # Create story session
    response = client.post(
        "/story-sessions", 
        json={"title": "Test Story", "summary_period": "weekly", "content_type": "story"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    created_at = data["created_at"]
    updated_at = data["updated_at"]
    
    assert created_at is not None
    assert updated_at is not None
    
    # Update story session and check that updated_at changes
    import time
    time.sleep(0.1)  # Small delay to ensure timestamp difference
    
    session_id = data["id"]
    update_response = client.put(
        f"/story-sessions/{session_id}",
        json={"title": "Updated Story"}
    )
    
    assert update_response.status_code == 200
    updated_data = update_response.json()
    
    assert updated_data["created_at"] == created_at  # Should not change
    assert updated_data["updated_at"] != updated_at  # Should change


def test_engagement_tracking():
    """Test engagement metrics tracking"""
    session_data = {
        "title": "Engagement Test Story",
        "summary_period": "weekly",
        "content_type": "story",
        "view_count": 5,
        "like_count": 3,
        "share_count": 2,
        "engagement_data": {"comments": 1, "saves": 2}
    }
    
    response = client.post("/story-sessions", json=session_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["view_count"] == 5
    assert data["like_count"] == 3
    assert data["share_count"] == 2
    assert data["engagement_data"]["comments"] == 1
    assert data["engagement_data"]["saves"] == 2


def test_period_date_handling():
    """Test period start and end date handling"""
    session_data = {
        "title": "Period Test Story",
        "summary_period": "custom",
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-07T23:59:59",
        "content_type": "summary"
    }
    
    response = client.post("/story-sessions", json=session_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "2024-01-01T00:00:00" in data["period_start"]
    assert "2024-01-07T23:59:59" in data["period_end"]