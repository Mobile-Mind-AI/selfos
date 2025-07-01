"""
Unit tests for Assistant Profiles API endpoints and functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from dependencies import get_db, get_current_user
from models import Base, AssistantProfile

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

@pytest.fixture
def mock_user_2():
    """Second mock user for multi-user tests"""
    return {
        "uid": "test_user_456", 
        "email": "testuser2@example.com",
        "roles": ["user"]
    }

def override_get_db_assistant_profiles():
    """Override get_db dependency for assistant profile tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user_assistant_profiles(user_data):
    """Override get_current_user dependency"""
    def _override():
        return user_data
    return _override

# Sample assistant profile data
SAMPLE_PROFILE_DATA = {
    "name": "Helpful Assistant",
    "description": "A friendly and helpful AI assistant",
    "avatar_url": "https://example.com/avatar.png",
    "ai_model": "gpt-4",
    "language": "en",
    "requires_confirmation": False,
    "style": {
        "formality": 60,
        "directness": 70,
        "humor": 40,
        "empathy": 80,
        "motivation": 75
    },
    "dialogue_temperature": 0.7,
    "intent_temperature": 0.2,
    "custom_instructions": "Be encouraging and motivational",
    "is_default": True
}

ONBOARDING_DATA = {
    "name": "My First Assistant",
    "avatar_url": "https://example.com/first-avatar.png",
    "ai_model": "gpt-3.5-turbo",
    "language": "en",
    "requires_confirmation": True,
    "style": {
        "formality": 50,
        "directness": 50,
        "humor": 30,
        "empathy": 70,
        "motivation": 60
    },
    "custom_instructions": "Help me achieve my goals step by step"
}

class TestAssistantProfilesCRUD:
    """Test CRUD operations for assistant profiles."""

    def setup_method(self):
        """Set up test database and dependencies before each test"""
        # Override dependencies
        app.dependency_overrides[get_db] = override_get_db_assistant_profiles
        
        # Clear any existing data
        db = TestingSessionLocal()
        db.query(AssistantProfile).delete()
        db.commit()
        db.close()

    def teardown_method(self):
        """Clean up after each test"""
        app.dependency_overrides.clear()

    def test_create_assistant_profile(self, mock_user):
        """Test creating a new assistant profile"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        response = client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == SAMPLE_PROFILE_DATA["name"]
        assert data["description"] == SAMPLE_PROFILE_DATA["description"]
        assert data["ai_model"] == SAMPLE_PROFILE_DATA["ai_model"]
        assert data["language"] == SAMPLE_PROFILE_DATA["language"]
        assert data["requires_confirmation"] == SAMPLE_PROFILE_DATA["requires_confirmation"]
        assert data["style"] == SAMPLE_PROFILE_DATA["style"]
        assert data["dialogue_temperature"] == SAMPLE_PROFILE_DATA["dialogue_temperature"]
        assert data["intent_temperature"] == SAMPLE_PROFILE_DATA["intent_temperature"]
        assert data["custom_instructions"] == SAMPLE_PROFILE_DATA["custom_instructions"]
        assert data["is_default"] == SAMPLE_PROFILE_DATA["is_default"]
        assert data["user_id"] == mock_user["uid"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_list_assistant_profiles(self, mock_user):
        """Test listing assistant profiles"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        # Create a few profiles first
        client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        
        profile_2 = SAMPLE_PROFILE_DATA.copy()
        profile_2["name"] = "Assistant 2"
        profile_2["is_default"] = False
        client.post("/api/assistant_profiles/", json=profile_2)
        
        response = client.get("/api/assistant_profiles/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        # Default profile should be first
        assert data[0]["is_default"] is True
        assert data[1]["is_default"] is False

    def test_get_assistant_profile_by_id(self, mock_user):
        """Test getting a specific assistant profile by ID"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        # Create profile first
        create_response = client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        profile_id = create_response.json()["id"]
        
        response = client.get(f"/api/assistant_profiles/{profile_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == profile_id
        assert data["name"] == SAMPLE_PROFILE_DATA["name"]

    def test_get_nonexistent_profile(self, mock_user):
        """Test getting a profile that doesn't exist"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        response = client.get("/api/assistant_profiles/nonexistent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_assistant_profile(self, mock_user):
        """Test updating an assistant profile"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        # Create profile first
        create_response = client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        profile_id = create_response.json()["id"]
        
        update_data = {
            "name": "Updated Assistant",
            "style": {
                "formality": 80,
                "directness": 90,
                "humor": 20,
                "empathy": 60,
                "motivation": 95
            }
        }
        
        response = client.patch(f"/api/assistant_profiles/{profile_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["style"] == update_data["style"]
        # Other fields should remain unchanged
        assert data["ai_model"] == SAMPLE_PROFILE_DATA["ai_model"]

    def test_delete_assistant_profile(self, mock_user):
        """Test deleting an assistant profile"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        # Create two profiles first (can't delete if only one exists)
        create_response_1 = client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        profile_id_1 = create_response_1.json()["id"]
        
        profile_2 = SAMPLE_PROFILE_DATA.copy()
        profile_2["name"] = "Assistant 2"
        profile_2["is_default"] = False
        create_response_2 = client.post("/api/assistant_profiles/", json=profile_2)
        profile_id_2 = create_response_2.json()["id"]
        
        # Delete the non-default profile
        response = client.delete(f"/api/assistant_profiles/{profile_id_2}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify it's gone
        get_response = client.get(f"/api/assistant_profiles/{profile_id_2}")
        assert get_response.status_code == 404

    def test_cannot_delete_only_profile(self, mock_user):
        """Test that you cannot delete the only assistant profile"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        # Create only one profile
        create_response = client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        profile_id = create_response.json()["id"]
        
        response = client.delete(f"/api/assistant_profiles/{profile_id}")
        
        assert response.status_code == 400
        assert "only assistant profile" in response.json()["detail"].lower()

    def test_user_isolation(self, mock_user, mock_user_2):
        """Test that users can only see their own profiles"""
        # Create profile for user 1
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        create_response = client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        profile_id = create_response.json()["id"]
        
        # Switch to user 2 and try to access user 1's profile
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user_2)
        response = client.get(f"/api/assistant_profiles/{profile_id}")
        
        assert response.status_code == 404

    def test_default_profile_management(self, mock_user):
        """Test default profile logic"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        # Create first profile (should be default)
        response_1 = client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        profile_1 = response_1.json()
        assert profile_1["is_default"] is True
        
        # Create second profile as default (should unset first)
        profile_2_data = SAMPLE_PROFILE_DATA.copy()
        profile_2_data["name"] = "New Default"
        profile_2_data["is_default"] = True
        
        response_2 = client.post("/api/assistant_profiles/", json=profile_2_data)
        profile_2 = response_2.json()
        assert profile_2["is_default"] is True
        
        # Check that first profile is no longer default
        response_1_check = client.get(f"/api/assistant_profiles/{profile_1['id']}")
        assert response_1_check.json()["is_default"] is False


class TestAssistantProfilesOnboarding:
    """Test onboarding functionality."""

    def setup_method(self):
        """Set up test database and dependencies before each test"""
        app.dependency_overrides[get_db] = override_get_db_assistant_profiles
        
        # Clear any existing data
        db = TestingSessionLocal()
        db.query(AssistantProfile).delete()
        db.commit()
        db.close()

    def teardown_method(self):
        """Clean up after each test"""
        app.dependency_overrides.clear()

    def test_onboarding_flow(self, mock_user):
        """Test the complete onboarding flow"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        response = client.post("/api/assistant_profiles/onboarding", json=ONBOARDING_DATA)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "assistant_profile" in data
        assert "onboarding_completed" in data
        assert "welcome_message" in data
        
        assert data["onboarding_completed"] is True
        assert data["assistant_profile"]["name"] == ONBOARDING_DATA["name"]
        assert data["assistant_profile"]["is_default"] is True
        assert len(data["welcome_message"]) > 0

    def test_get_default_profile(self, mock_user):
        """Test getting the default assistant profile"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        # Create a default profile
        client.post("/api/assistant_profiles/", json=SAMPLE_PROFILE_DATA)
        
        response = client.get("/api/assistant_profiles/default")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_default"] is True
        assert data["name"] == SAMPLE_PROFILE_DATA["name"]

    def test_get_default_profile_not_found(self, mock_user):
        """Test getting default profile when none exists"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        response = client.get("/api/assistant_profiles/default")
        
        assert response.status_code == 404
        assert "no default" in response.json()["detail"].lower()


class TestAssistantProfilesPersonality:
    """Test personality and preview functionality."""

    def setup_method(self):
        """Set up test database and dependencies before each test"""
        app.dependency_overrides[get_db] = override_get_db_assistant_profiles

    def teardown_method(self):
        """Clean up after each test"""
        app.dependency_overrides.clear()

    def test_personality_preview(self, mock_user):
        """Test personality preview functionality"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        preview_data = {
            "style": {
                "formality": 20,  # Very formal
                "directness": 80,  # Very direct
                "humor": 90,      # Very humorous
                "empathy": 95,    # Very empathetic
                "motivation": 85  # Very motivational
            },
            "sample_message": "How can I help you today?"
        }
        
        response = client.post("/api/assistant_profiles/preview", json=preview_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sample_response" in data
        assert "style_description" in data
        assert "personality_summary" in data
        
        # Check personality summary structure
        summary = data["personality_summary"]
        assert "formality" in summary
        assert "directness" in summary
        assert "humor" in summary
        assert "empathy" in summary
        assert "motivation" in summary
        
        # Check that traits are described appropriately
        assert "formal" in summary["formality"].lower()
        assert "direct" in summary["directness"].lower()
        assert "playful" in summary["humor"].lower() or "humorous" in summary["humor"].lower()
        assert "empathetic" in summary["empathy"].lower() or "warm" in summary["empathy"].lower()
        assert "energetic" in summary["motivation"].lower() or "motivational" in summary["motivation"].lower()

    def test_get_assistant_config(self):
        """Test getting assistant configuration options"""
        response = client.get("/api/assistant_profiles/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "supported_languages" in data
        assert "supported_models" in data
        assert "default_style" in data
        assert "temperature_ranges" in data
        
        # Check some expected languages and models
        assert "en" in data["supported_languages"]
        assert "gpt-3.5-turbo" in data["supported_models"] or "gpt-4" in data["supported_models"]
        
        # Check default style structure
        default_style = data["default_style"]
        assert "formality" in default_style
        assert "directness" in default_style
        assert "humor" in default_style
        assert "empathy" in default_style
        assert "motivation" in default_style
        
        # Check temperature ranges
        temp_ranges = data["temperature_ranges"]
        assert "dialogue" in temp_ranges
        assert "intent" in temp_ranges


class TestAssistantProfilesValidation:
    """Test input validation for assistant profiles."""

    def setup_method(self):
        """Set up test database and dependencies before each test"""
        app.dependency_overrides[get_db] = override_get_db_assistant_profiles

    def teardown_method(self):
        """Clean up after each test"""
        app.dependency_overrides.clear()

    def test_invalid_style_values(self, mock_user):
        """Test validation of personality style values"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        invalid_data = SAMPLE_PROFILE_DATA.copy()
        invalid_data["style"] = {
            "formality": 150,  # Invalid: > 100
            "directness": -10,  # Invalid: < 0
            "humor": 50,
            "empathy": 70,
            "motivation": 60
        }
        
        response = client.post("/api/assistant_profiles/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self, mock_user):
        """Test validation of required fields"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        incomplete_data = {
            "description": "Missing name field"
        }
        
        response = client.post("/api/assistant_profiles/", json=incomplete_data)
        
        assert response.status_code == 422  # Validation error

    def test_profile_limit_enforcement(self, mock_user):
        """Test that users cannot create more than 5 profiles"""
        app.dependency_overrides[get_current_user] = override_get_current_user_assistant_profiles(mock_user)
        
        # Create 5 profiles
        for i in range(5):
            profile_data = SAMPLE_PROFILE_DATA.copy()
            profile_data["name"] = f"Assistant {i+1}"
            profile_data["is_default"] = (i == 0)  # Only first is default
            
            response = client.post("/api/assistant_profiles/", json=profile_data)
            assert response.status_code == 200
        
        # Try to create 6th profile
        profile_data = SAMPLE_PROFILE_DATA.copy()
        profile_data["name"] = "Assistant 6"
        profile_data["is_default"] = False
        
        response = client.post("/api/assistant_profiles/", json=profile_data)
        
        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__])