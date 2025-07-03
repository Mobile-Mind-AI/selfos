"""
Unit tests for Avatar Upload API endpoints and functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
import io
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from dependencies import get_db, get_current_user
from models import Base, AvatarImage

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
        "uid": "test_avatars_user_123",
        "email": "testavatars@example.com",
        "roles": ["user"]
    }

def override_get_db_avatars():
    """Override database dependency for avatar tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_avatars():
    """Override current user dependency for avatar tests"""
    return {
        "uid": "test_avatars_user_123",
        "email": "testavatars@example.com",
        "roles": ["user"]
    }

@pytest.fixture(scope="module", autouse=True)
def setup_avatars_dependencies():
    """Set up dependency overrides for avatar tests"""
    # Store original overrides
    original_db = app.dependency_overrides.get(get_db)
    original_user = app.dependency_overrides.get(get_current_user)
    
    # Set avatar test overrides
    app.dependency_overrides[get_db] = override_get_db_avatars
    app.dependency_overrides[get_current_user] = override_get_current_user_avatars
    
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


class TestAvatarUpload:
    """Test avatar upload functionality"""

    def test_upload_avatar_success(self, db_session):
        """Test successful avatar upload"""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Upload the avatar
        response = client.post(
            "/api/avatars/upload",
            files={"file": ("test_avatar.jpg", img_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "avatar_id" in data
        assert "filename" in data
        assert "width" in data
        assert "height" in data
        assert "size_bytes" in data
        assert "content_type" in data
        assert "created_at" in data
        
        # Verify database record
        avatar = db_session.query(AvatarImage).filter(
            AvatarImage.id == data["avatar_id"]
        ).first()
        
        assert avatar is not None
        assert avatar.user_id == "test_avatars_user_123"
        assert avatar.filename == "test_avatar.jpg"
        assert avatar.content_type == "image/jpeg"
        assert avatar.is_active is True
        assert avatar.image_data is not None
        assert avatar.thumbnail_data is not None

    def test_upload_avatar_invalid_file_type(self, db_session):
        """Test upload with invalid file type"""
        # Create a text file
        text_content = b"This is not an image"
        
        response = client.post(
            "/api/avatars/upload",
            files={"file": ("test.txt", text_content, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_avatar_large_file(self, db_session):
        """Test upload with very large image (should be compressed)"""
        # Create a large image
        img = Image.new('RGB', (2000, 2000), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=95)
        img_bytes.seek(0)
        
        response = client.post(
            "/api/avatars/upload",
            files={"file": ("large_avatar.jpg", img_bytes, "image/jpeg")}
        )
        
        # Should still succeed - our endpoint handles large images
        assert response.status_code == 200
        data = response.json()
        assert "avatar_id" in data


class TestAvatarRetrieval:
    """Test avatar retrieval functionality"""

    def test_list_user_avatars(self, db_session):
        """Test listing user avatars"""
        # Create test avatars
        avatar1 = AvatarImage(
            user_id="test_avatars_user_123",
            filename="avatar1.jpg",
            content_type="image/jpeg",
            size_bytes=1000,
            width=100,
            height=100,
            image_data=b"fake_image_data_1",
            is_active=True
        )
        avatar2 = AvatarImage(
            user_id="test_avatars_user_123",
            filename="avatar2.png",
            content_type="image/png",
            size_bytes=2000,
            width=200,
            height=200,
            image_data=b"fake_image_data_2",
            is_active=False
        )
        
        db_session.add_all([avatar1, avatar2])
        db_session.commit()
        
        # Test listing active avatars only
        response = client.get("/api/avatars/list")
        assert response.status_code == 200
        
        avatars = response.json()
        active_avatars = [a for a in avatars if a["filename"] in ["avatar1.jpg", "avatar2.png"]]
        assert len([a for a in active_avatars if a["is_active"]]) >= 1  # At least our active avatar
        
        # Test listing all avatars including inactive
        response = client.get("/api/avatars/list?include_inactive=true")
        assert response.status_code == 200
        
        avatars = response.json()
        test_avatars = [a for a in avatars if a["filename"] in ["avatar1.jpg", "avatar2.png"]]
        assert len(test_avatars) >= 2  # Should include both test avatars

    def test_get_avatar_image(self, db_session):
        """Test retrieving avatar image data"""
        # Create test avatar
        avatar = AvatarImage(
            user_id="test_avatars_user_123",
            filename="test_avatar.jpg",
            content_type="image/jpeg",
            size_bytes=1000,
            width=100,
            height=100,
            image_data=b"fake_image_data",
            thumbnail_data=b"fake_thumbnail_data",
            is_active=True
        )
        
        db_session.add(avatar)
        db_session.commit()
        db_session.refresh(avatar)
        
        # Test getting full image
        response = client.get(f"/api/avatars/{avatar.id}/image")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert response.content == b"fake_image_data"
        
        # Test getting thumbnail
        response = client.get(f"/api/avatars/{avatar.id}/image?thumbnail=true")
        assert response.status_code == 200
        assert response.content == b"fake_thumbnail_data"

    def test_get_avatar_base64(self, db_session):
        """Test retrieving avatar as base64"""
        # Create test avatar
        avatar = AvatarImage(
            user_id="test_avatars_user_123",
            filename="test_avatar.jpg",
            content_type="image/jpeg",
            size_bytes=1000,
            width=100,
            height=100,
            image_data=b"fake_image_data",
            is_active=True
        )
        
        db_session.add(avatar)
        db_session.commit()
        db_session.refresh(avatar)
        
        response = client.get(f"/api/avatars/{avatar.id}/base64")
        assert response.status_code == 200
        
        data = response.json()
        assert "base64_data" in data
        assert "content_type" in data
        assert "width" in data
        assert "height" in data
        assert data["content_type"] == "image/jpeg"
        assert data["base64_data"].startswith("data:image/jpeg;base64,")

    def test_get_nonexistent_avatar(self, db_session):
        """Test retrieving non-existent avatar"""
        response = client.get("/api/avatars/nonexistent-id/image")
        assert response.status_code == 404
        assert "Avatar not found" in response.json()["detail"]

    def test_get_other_user_avatar(self, db_session):
        """Test that users can't access other users' avatars"""
        # Create avatar for different user
        other_avatar = AvatarImage(
            user_id="other_user",
            filename="other_avatar.jpg",
            content_type="image/jpeg",
            size_bytes=1000,
            width=100,
            height=100,
            image_data=b"fake_image_data",
            is_active=True
        )
        
        db_session.add(other_avatar)
        db_session.commit()
        db_session.refresh(other_avatar)
        
        response = client.get(f"/api/avatars/{other_avatar.id}/image")
        assert response.status_code == 404  # Should not find avatar for different user


class TestAvatarManagement:
    """Test avatar management functionality"""

    def test_delete_avatar(self, db_session):
        """Test soft deleting an avatar"""
        # Create test avatar
        avatar = AvatarImage(
            user_id="test_avatars_user_123",
            filename="test_avatar.jpg",
            content_type="image/jpeg",
            size_bytes=1000,
            width=100,
            height=100,
            image_data=b"fake_image_data",
            is_active=True
        )
        
        db_session.add(avatar)
        db_session.commit()
        db_session.refresh(avatar)
        
        # Delete avatar
        response = client.delete(f"/api/avatars/{avatar.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["avatar_id"] == avatar.id
        
        # Verify avatar is marked as inactive
        db_session.refresh(avatar)
        assert avatar.is_active is False

    def test_restore_avatar(self, db_session):
        """Test restoring a deleted avatar"""
        # Create inactive avatar
        avatar = AvatarImage(
            user_id="test_avatars_user_123",
            filename="test_avatar.jpg",
            content_type="image/jpeg",
            size_bytes=1000,
            width=100,
            height=100,
            image_data=b"fake_image_data",
            is_active=False
        )
        
        db_session.add(avatar)
        db_session.commit()
        db_session.refresh(avatar)
        
        # Restore avatar
        response = client.post(f"/api/avatars/{avatar.id}/restore")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["avatar_id"] == avatar.id
        
        # Verify avatar is marked as active
        db_session.refresh(avatar)
        assert avatar.is_active is True

    def test_usage_tracking(self, db_session):
        """Test that avatar usage is tracked"""
        # Create test avatar
        avatar = AvatarImage(
            user_id="test_avatars_user_123",
            filename="test_avatar.jpg",
            content_type="image/jpeg",
            size_bytes=1000,
            width=100,
            height=100,
            image_data=b"fake_image_data",
            usage_count=0,
            is_active=True
        )
        
        db_session.add(avatar)
        db_session.commit()
        db_session.refresh(avatar)
        
        initial_count = avatar.usage_count
        
        # Access avatar image
        client.get(f"/api/avatars/{avatar.id}/image")
        
        # Verify usage count increased
        db_session.refresh(avatar)
        assert avatar.usage_count == initial_count + 1
        assert avatar.last_used_at is not None


class TestImageProcessing:
    """Test image processing functionality"""

    def test_rgba_to_rgb_conversion(self, db_session):
        """Test that RGBA images are converted to RGB"""
        # Create an RGBA image
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        response = client.post(
            "/api/avatars/upload",
            files={"file": ("test_rgba.png", img_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify it was converted to JPEG (RGB)
        assert data["content_type"] == "image/jpeg"

    def test_thumbnail_generation(self, db_session):
        """Test that thumbnails are generated"""
        # Create a large image
        img = Image.new('RGB', (500, 500), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        response = client.post(
            "/api/avatars/upload",
            files={"file": ("large_image.jpg", img_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify database record has thumbnail
        avatar = db_session.query(AvatarImage).filter(
            AvatarImage.id == data["avatar_id"]
        ).first()
        
        assert avatar.thumbnail_data is not None
        assert len(avatar.thumbnail_data) < len(avatar.image_data)  # Thumbnail should be smaller