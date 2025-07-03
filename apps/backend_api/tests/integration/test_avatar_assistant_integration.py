"""
Integration tests for avatar and assistant profile functionality.
Tests the complete workflow of uploading avatars and using them with assistant profiles.
"""

import pytest
import io
import sys
import os
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from dependencies import get_db, get_current_user
from models import Base, AvatarImage, AssistantProfile

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

def override_get_db_integration():
    """Override database dependency for integration tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_integration():
    """Override current user dependency for integration tests"""
    return {
        "uid": "integration_test_user",
        "email": "integration@example.com",
        "roles": ["user"]
    }

@pytest.fixture(scope="module", autouse=True)
def setup_integration_dependencies():
    """Set up dependency overrides for integration tests"""
    # Store original overrides
    original_db = app.dependency_overrides.get(get_db)
    original_user = app.dependency_overrides.get(get_current_user)
    
    # Set integration test overrides
    app.dependency_overrides[get_db] = override_get_db_integration
    app.dependency_overrides[get_current_user] = override_get_current_user_integration
    
    yield
    
    # Restore original overrides
    if original_db is not None:
        app.dependency_overrides[get_db] = original_db
    else:
        app.dependency_overrides.pop(get_db, None)
        
    if original_user is not None:
        app.dependency_overrides[get_current_user] = original_user
    else:
        app.dependency_overrides.pop(get_current_user, None)


class TestAvatarAssistantIntegration:
    """Test integration between avatar upload and assistant profiles"""

    def test_complete_avatar_workflow(self, db_session):
        """Test complete workflow: upload avatar -> create profile -> use avatar"""
        
        # Step 1: Upload a custom avatar
        img = Image.new('RGB', (200, 200), color='purple')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        upload_response = client.post(
            "/api/avatars/upload",
            files={"file": ("custom_avatar.jpg", img_bytes, "image/jpeg")}
        )
        
        assert upload_response.status_code == 200
        avatar_data = upload_response.json()
        avatar_id = avatar_data["avatar_id"]
        
        # Step 2: Create assistant profile using the uploaded avatar
        profile_data = {
            "name": "Custom Avatar Assistant",
            "description": "An assistant with a custom uploaded avatar",
            "avatar_url": avatar_id,  # Use the uploaded avatar ID
            "ai_model": "gpt-4",
            "language": "en",
            "is_default": True,
            "style": {
                "formality": 30,
                "directness": 70,
                "humor": 60,
                "empathy": 80,
                "motivation": 50
            }
        }
        
        profile_response = client.post("/api/assistant/profile", json=profile_data)
        assert profile_response.status_code == 200
        
        profile_result = profile_response.json()
        assert profile_result["avatar_url"] == avatar_id
        assert profile_result["name"] == "Custom Avatar Assistant"
        
        # Step 3: Retrieve the assistant profile and verify avatar is accessible
        get_profile_response = client.get("/api/assistant/profile")
        assert get_profile_response.status_code == 200
        
        current_profile = get_profile_response.json()
        assert current_profile["avatar_url"] == avatar_id
        
        # Step 4: Retrieve the avatar image using the profile's avatar_url
        avatar_response = client.get(f"/api/avatars/{avatar_id}/image")
        assert avatar_response.status_code == 200
        assert avatar_response.headers["content-type"] == "image/jpeg"
        
        # Step 5: Get avatar as base64 for frontend use
        base64_response = client.get(f"/api/avatars/{avatar_id}/base64")
        assert base64_response.status_code == 200
        
        base64_data = base64_response.json()
        assert base64_data["base64_data"].startswith("data:image/jpeg;base64,")
        
        # Step 6: Verify usage tracking
        avatar = db_session.query(AvatarImage).filter(AvatarImage.id == avatar_id).first()
        assert avatar.usage_count >= 2  # At least 2 accesses (image + base64)

    def test_multiple_profiles_same_avatar(self, db_session):
        """Test using the same avatar for multiple assistant profiles"""
        
        # Upload one avatar
        img = Image.new('RGB', (150, 150), color='orange')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        upload_response = client.post(
            "/api/avatars/upload",
            files={"file": ("shared_avatar.jpg", img_bytes, "image/jpeg")}
        )
        
        avatar_id = upload_response.json()["avatar_id"]
        
        # Create multiple profiles using the same avatar
        profiles_data = [
            {
                "name": "Formal Assistant",
                "avatar_url": avatar_id,
                "style": {"formality": 80, "directness": 40, "humor": 10, "empathy": 60, "motivation": 50},
                "is_default": True
            },
            {
                "name": "Casual Assistant", 
                "avatar_url": avatar_id,
                "style": {"formality": 20, "directness": 80, "humor": 70, "empathy": 90, "motivation": 80},
                "is_default": False
            }
        ]
        
        created_profiles = []
        for i, profile_data in enumerate(profiles_data):
            # Only first profile should be default
            if i > 0:
                profile_data["is_default"] = False
                
            response = client.post("/api/assistant/profile", json=profile_data)
            assert response.status_code == 200
            created_profiles.append(response.json())
        
        # Verify all profiles use the same avatar
        for profile in created_profiles:
            assert profile["avatar_url"] == avatar_id
        
        # List all profiles and verify they all reference the same avatar
        list_response = client.get("/api/assistant/profiles")
        assert list_response.status_code == 200
        
        all_profiles = list_response.json()
        shared_avatar_profiles = [p for p in all_profiles if p["avatar_url"] == avatar_id]
        assert len(shared_avatar_profiles) >= 2

    def test_profile_avatar_change(self, db_session):
        """Test changing avatar for an existing profile"""
        
        # Upload two different avatars
        avatars = []
        colors = ['red', 'blue']
        
        for i, color in enumerate(colors):
            img = Image.new('RGB', (100, 100), color=color)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            upload_response = client.post(
                "/api/avatars/upload",
                files={"file": (f"avatar_{color}.jpg", img_bytes, "image/jpeg")}
            )
            
            avatars.append(upload_response.json()["avatar_id"])
        
        # First get the current profile to see if it exists
        get_response = client.get("/api/assistant/profile")
        if get_response.status_code == 200:
            # Update existing profile to use first avatar
            update_data = {
                "name": "Avatar Changing Assistant", 
                "avatar_url": avatars[0]
            }
            update_response = client.put("/api/assistant/profile", json=update_data)
            assert update_response.status_code == 200
        else:
            # Create new profile with first avatar
            profile_data = {
                "name": "Avatar Changing Assistant",
                "avatar_url": avatars[0],
                "is_default": True
            }
            
            create_response = client.post("/api/assistant/profile", json=profile_data)
            assert create_response.status_code == 200
        
        # Verify initial avatar
        get_response = client.get("/api/assistant/profile")
        assert get_response.json()["avatar_url"] == avatars[0]
        
        # Update profile to use second avatar
        update_data = {"avatar_url": avatars[1]}
        update_response = client.put("/api/assistant/profile", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["avatar_url"] == avatars[1]
        
        # Verify both avatars are still accessible
        for avatar_id in avatars:
            avatar_response = client.get(f"/api/avatars/{avatar_id}/image")
            assert avatar_response.status_code == 200

    def test_avatar_deletion_with_active_profile(self, db_session):
        """Test behavior when avatar is deleted but still referenced by profile"""
        
        # Upload avatar
        img = Image.new('RGB', (100, 100), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        upload_response = client.post(
            "/api/avatars/upload",
            files={"file": ("deletable_avatar.jpg", img_bytes, "image/jpeg")}
        )
        
        avatar_id = upload_response.json()["avatar_id"]
        
        # Set the profile to use this avatar
        profile_data = {
            "name": "Profile with Deletable Avatar",
            "avatar_url": avatar_id
        }
        
        # Update existing profile to use this avatar  
        update_response = client.put("/api/assistant/profile", json=profile_data)
        assert update_response.status_code == 200
        
        # Verify profile is using our avatar
        profile_response = client.get("/api/assistant/profile")
        assert profile_response.status_code == 200
        assert profile_response.json()["avatar_url"] == avatar_id
        
        # Delete the avatar (soft delete)
        delete_response = client.delete(f"/api/avatars/{avatar_id}")
        assert delete_response.status_code == 200
        
        # Profile should still exist and still reference the avatar
        profile_response = client.get("/api/assistant/profile")
        assert profile_response.status_code == 200
        
        current_profile = profile_response.json()
        assert current_profile["avatar_url"] == avatar_id  # Still references deleted avatar
        
        # Trying to access the avatar should fail (it's inactive)
        avatar_response = client.get(f"/api/avatars/{avatar_id}/image")
        assert avatar_response.status_code == 404
        
        # Restore the avatar
        restore_response = client.post(f"/api/avatars/{avatar_id}/restore")
        assert restore_response.status_code == 200
        
        # Now avatar should be accessible again
        avatar_response = client.get(f"/api/avatars/{avatar_id}/image")
        assert avatar_response.status_code == 200

    def test_avatar_list_for_profile_creation(self, db_session):
        """Test that avatar listing works properly for profile creation UI"""
        
        # Upload multiple avatars
        avatar_ids = []
        for i in range(3):
            # Create different colored avatars
            color_value = i * 85  # Creates different RGB values
            img = Image.new('RGB', (100, 100), color=(color_value, color_value, color_value))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            upload_response = client.post(
                "/api/avatars/upload",
                files={"file": (f"test_avatar_{i}.jpg", img_bytes, "image/jpeg")}
            )
            
            avatar_ids.append(upload_response.json()["avatar_id"])
        
        # Delete one avatar
        client.delete(f"/api/avatars/{avatar_ids[1]}")
        
        # List active avatars (should exclude deleted one)
        list_response = client.get("/api/avatars/list")
        assert list_response.status_code == 200
        
        active_avatars = list_response.json()
        active_ids = [avatar["avatar_id"] for avatar in active_avatars]
        
        assert avatar_ids[0] in active_ids
        assert avatar_ids[1] not in active_ids  # Deleted avatar
        assert avatar_ids[2] in active_ids
        
        # List all avatars including inactive
        all_response = client.get("/api/avatars/list?include_inactive=true")
        assert all_response.status_code == 200
        
        all_avatars = all_response.json()
        all_ids = [avatar["avatar_id"] for avatar in all_avatars]
        
        # Should include all avatars including the deleted one
        for avatar_id in avatar_ids:
            assert avatar_id in all_ids

    def test_assistant_config_with_avatar_usage(self, db_session):
        """Test that assistant configuration works with custom avatars"""
        
        # Get assistant configuration
        config_response = client.get("/api/assistant/config")
        assert config_response.status_code == 200
        
        config = config_response.json()
        
        # Upload custom avatar
        img = Image.new('RGB', (100, 100), color='cyan')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        upload_response = client.post(
            "/api/avatars/upload",
            files={"file": ("config_test_avatar.jpg", img_bytes, "image/jpeg")}
        )
        
        avatar_id = upload_response.json()["avatar_id"]
        
        # Create profile using configuration values and custom avatar
        profile_data = {
            "name": "Config Test Assistant",
            "avatar_url": avatar_id,
            "ai_model": list(config["supported_models"].keys())[0],
            "language": list(config["supported_languages"].keys())[0],
            "style": config["default_style"],
            "dialogue_temperature": config["temperature_ranges"]["dialogue"]["default"],
            "intent_temperature": config["temperature_ranges"]["intent"]["default"]
        }
        
        profile_response = client.post("/api/assistant/profile", json=profile_data)
        assert profile_response.status_code == 200
        
        created_profile = profile_response.json()
        assert created_profile["avatar_url"] == avatar_id
        assert created_profile["ai_model"] in config["supported_models"]
        assert created_profile["language"] in config["supported_languages"]
        
        # Verify the avatar is accessible
        avatar_response = client.get(f"/api/avatars/{avatar_id}/image")
        assert avatar_response.status_code == 200