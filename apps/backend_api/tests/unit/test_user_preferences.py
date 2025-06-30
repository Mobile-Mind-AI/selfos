import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
from datetime import time

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

def override_get_db_user_preferences():
    """Override database dependency for testing user preferences"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_user_preferences():
    """Override authentication dependency for testing user preferences"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_user_preferences
app.dependency_overrides[get_current_user] = override_get_current_user_user_preferences

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before each test"""
    # Clean up before each test  
    db = TestingSessionLocal()
    try:
        from sqlalchemy import text
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


def test_get_user_preferences_creates_default():
    """Test that getting preferences creates default preferences if none exist"""
    response = client.get("/api/user-preferences")
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["tone"] == "friendly"
    assert data["notifications_enabled"] == True
    assert data["default_view"] == "card"
    assert data["mood_tracking_enabled"] == False
    assert data["progress_charts_enabled"] == True
    assert data["ai_suggestions_enabled"] == True
    assert data["data_sharing_enabled"] == False
    assert data["analytics_enabled"] == True


def test_create_user_preferences():
    """Test creating new user preferences"""
    preferences_data = {
        "tone": "coach",
        "notification_time": "09:00:00",
        "notifications_enabled": True,
        "email_notifications": False,
        "prefers_video": True,
        "prefers_audio": False,
        "default_view": "timeline",
        "mood_tracking_enabled": True,
        "progress_charts_enabled": True,
        "ai_suggestions_enabled": False,
        "data_sharing_enabled": False,
        "analytics_enabled": True
    }
    
    response = client.post("/api/user-preferences", json=preferences_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["tone"] == "coach"
    assert data["default_view"] == "timeline"
    assert data["mood_tracking_enabled"] == True
    assert data["ai_suggestions_enabled"] == False


def test_create_preferences_fails_if_already_exist():
    """Test that creating preferences fails if they already exist"""
    # First create preferences
    preferences_data = {"tone": "minimal"}
    response1 = client.post("/api/user-preferences", json=preferences_data)
    assert response1.status_code in [200, 201]  # Accept both OK and Created
    
    # Try to create again - should fail
    response2 = client.post("/api/user-preferences", json=preferences_data)
    assert response2.status_code == 400
    assert "already exist" in response2.json()["detail"]


def test_update_user_preferences():
    """Test updating existing user preferences"""
    # First create preferences
    initial_data = {"tone": "friendly", "default_view": "card"}
    client.post("/api/user-preferences", json=initial_data)
    
    # Update preferences
    update_data = {
        "tone": "professional",
        "mood_tracking_enabled": True,
        "notifications_enabled": False
    }
    
    response = client.put("/api/user-preferences", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["tone"] == "professional"
    assert data["mood_tracking_enabled"] == True
    assert data["notifications_enabled"] == False
    assert data["default_view"] == "card"  # Should remain unchanged


def test_update_preferences_creates_if_not_exist():
    """Test that updating preferences creates new ones if none exist"""
    update_data = {
        "tone": "coach",
        "default_view": "list"
    }
    
    response = client.put("/api/user-preferences", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["tone"] == "coach"
    assert data["default_view"] == "list"
    assert data["notifications_enabled"] == True  # Default value


def test_update_preferences_with_default_life_area():
    """Test updating preferences with a default life area"""
    # First create a life area
    life_area_data = {"name": "Health & Fitness", "weight": 30}
    life_area_response = client.post("/api/life-areas", json=life_area_data)
    life_area_id = life_area_response.json()["id"]
    
    # Update preferences with default life area
    update_data = {"default_life_area_id": life_area_id}
    
    response = client.put("/api/user-preferences", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["default_life_area_id"] == life_area_id


def test_update_preferences_with_invalid_life_area():
    """Test that updating preferences with invalid life area fails"""
    # First create some preferences
    initial_data = {"tone": "friendly"}
    client.post("/api/user-preferences", json=initial_data)
    
    # Try to update with invalid life area
    update_data = {"default_life_area_id": 99999}
    
    response = client.put("/api/user-preferences", json=update_data)
    
    assert response.status_code == 404
    assert "Default life area not found" in response.json()["detail"]


def test_delete_user_preferences():
    """Test deleting user preferences"""
    # First create preferences
    preferences_data = {"tone": "coach"}
    client.post("/api/user-preferences", json=preferences_data)
    
    # Delete preferences
    response = client.delete("/api/user-preferences")
    
    assert response.status_code == 204
    
    # Verify they're deleted by trying to get them (should create new defaults)
    get_response = client.get("/api/user-preferences")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["tone"] == "friendly"  # Default value


def test_delete_nonexistent_preferences():
    """Test deleting preferences that don't exist"""
    response = client.delete("/api/user-preferences")
    
    assert response.status_code == 404
    assert "User preferences not found" in response.json()["detail"]


def test_get_tone_options():
    """Test getting available tone options"""
    response = client.get("/api/user-preferences/tone-options")
    
    assert response.status_code == 200
    data = response.json()
    assert "tone_options" in data
    
    tone_options = data["tone_options"]
    assert len(tone_options) == 4
    
    # Check that all expected tone options are present
    tone_values = [option["value"] for option in tone_options]
    expected_tones = ["friendly", "coach", "minimal", "professional"]
    for tone in expected_tones:
        assert tone in tone_values


def test_get_view_options():
    """Test getting available view mode options"""
    response = client.get("/api/user-preferences/view-options")
    
    assert response.status_code == 200
    data = response.json()
    assert "view_options" in data
    
    view_options = data["view_options"]
    assert len(view_options) == 3
    
    # Check that all expected view options are present
    view_values = [option["value"] for option in view_options]
    expected_views = ["list", "card", "timeline"]
    for view in expected_views:
        assert view in view_values


def test_quick_setup_preferences():
    """Test quick setup for new users"""
    response = client.post(
        "/api/user-preferences/quick-setup",
        params={
            "tone": "coach",
            "notifications": False,
            "default_view": "timeline"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["tone"] == "coach"
    assert data["notifications_enabled"] == False
    assert data["default_view"] == "timeline"


def test_quick_setup_invalid_tone():
    """Test quick setup with invalid tone"""
    response = client.post(
        "/api/user-preferences/quick-setup",
        params={"tone": "invalid_tone"}
    )
    
    assert response.status_code == 400
    assert "Invalid tone" in response.json()["detail"]


def test_quick_setup_invalid_view():
    """Test quick setup with invalid view"""
    response = client.post(
        "/api/user-preferences/quick-setup",
        params={
            "tone": "friendly",
            "default_view": "invalid_view"
        }
    )
    
    assert response.status_code == 400
    assert "Invalid view" in response.json()["detail"]


def test_quick_setup_updates_existing():
    """Test that quick setup updates existing preferences"""
    # First create preferences
    initial_data = {"tone": "minimal", "mood_tracking_enabled": True}
    client.post("/api/user-preferences", json=initial_data)
    
    # Run quick setup
    response = client.post(
        "/api/user-preferences/quick-setup",
        params={
            "tone": "professional",
            "notifications": False,
            "default_view": "list"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["tone"] == "professional"
    assert data["notifications_enabled"] == False
    assert data["default_view"] == "list"
    assert data["mood_tracking_enabled"] == True  # Should remain unchanged


def test_preferences_validation():
    """Test various validation scenarios"""
    
    # Test invalid tone
    response = client.post(
        "/api/user-preferences", 
        json={"tone": "invalid_tone"}
    )
    assert response.status_code == 422
    
    # Test invalid view mode
    response = client.post(
        "/api/user-preferences", 
        json={"default_view": "invalid_view"}
    )
    assert response.status_code == 422


def test_notification_time_handling():
    """Test notification time field handling"""
    preferences_data = {
        "notification_time": "14:30:00",  # 2:30 PM
        "notifications_enabled": True
    }
    
    response = client.post("/api/user-preferences", json=preferences_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "14:30:00" in data["notification_time"]
    assert data["notifications_enabled"] == True


def test_preferences_timestamps():
    """Test that created_at and updated_at timestamps work correctly"""
    # Create preferences
    response = client.post(
        "/api/user-preferences", 
        json={"tone": "friendly"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    created_at = data["created_at"]
    updated_at = data["updated_at"]
    
    assert created_at is not None
    assert updated_at is not None
    
    # Update preferences and check that updated_at changes
    import time
    time.sleep(0.1)  # Small delay to ensure timestamp difference
    
    update_response = client.put(
        "/api/user-preferences",
        json={"tone": "coach"}
    )
    
    assert update_response.status_code == 200
    updated_data = update_response.json()
    
    assert updated_data["created_at"] == created_at  # Should not change
    assert updated_data["updated_at"] != updated_at  # Should change


def test_user_isolation():
    """Test that users can only access their own preferences"""
    # Create preferences as test_user_123
    preferences_data = {"tone": "coach"}
    create_response = client.post("/api/user-preferences", json=preferences_data)
    assert create_response.status_code == 201
    
    # Verify user can access their preferences
    user_preferences = client.get("/api/user-preferences").json()
    assert user_preferences["user_id"] == "test_user_123"
    
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
        
        # Different user should get their own default preferences (auto-created)
        different_user_prefs = different_client.get("/api/user-preferences").json()
        assert different_user_prefs["user_id"] == "different_user_456"
        assert different_user_prefs["tone"] == "friendly"  # Default, not "coach"
        
    finally:
        # Always restore original override
        if original_override:
            test_app.dependency_overrides[get_current_user] = original_override
        else:
            test_app.dependency_overrides.pop(get_current_user, None)