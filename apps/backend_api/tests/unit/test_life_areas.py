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

def override_get_db_life_areas():
    """Override database dependency for testing life areas"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_life_areas():
    """Override authentication dependency for testing life areas"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_life_areas
app.dependency_overrides[get_current_user] = override_get_current_user_life_areas

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


def test_create_life_area():
    """Test creating a new life area"""
    life_area_data = {
        "name": "Health & Fitness",
        "weight": 25,
        "icon": "fitness_center",
        "color": "#4CAF50",
        "description": "Physical health, exercise, nutrition"
    }
    
    response = client.post("/api/life-areas", json=life_area_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Health & Fitness"
    assert data["weight"] == 25
    assert data["icon"] == "fitness_center"
    assert data["color"] == "#4CAF50"
    assert data["description"] == "Physical health, exercise, nutrition"
    assert data["user_id"] == "test_user_123"
    assert "created_at" in data
    assert "updated_at" in data


def test_create_life_area_minimal():
    """Test creating a life area with minimal data"""
    life_area_data = {
        "name": "Career"
    }
    
    response = client.post("/api/life-areas", json=life_area_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Career"
    assert data["weight"] == 10  # Default value
    assert data["icon"] is None
    assert data["color"] is None
    assert data["description"] is None


def test_create_life_area_duplicate_name():
    """Test creating a life area with duplicate name fails"""
    life_area_data = {
        "name": "Health",
        "weight": 20
    }
    
    # Create first life area
    response1 = client.post("/api/life-areas", json=life_area_data)
    assert response1.status_code == 200
    
    # Try to create duplicate
    response2 = client.post("/api/life-areas", json=life_area_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_create_life_area_invalid_weight():
    """Test creating a life area with invalid weight fails"""
    life_area_data = {
        "name": "Invalid Weight",
        "weight": 150  # Over 100
    }
    
    response = client.post("/api/life-areas", json=life_area_data)
    assert response.status_code == 422


def test_list_life_areas():
    """Test listing user life areas"""
    # Create multiple life areas
    life_areas = [
        {"name": "Health", "weight": 30},
        {"name": "Career", "weight": 25},
        {"name": "Relationships", "weight": 20}
    ]
    
    for area_data in life_areas:
        client.post("/api/life-areas", json=area_data)
    
    response = client.get("/api/life-areas")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    
    # Should be ordered by weight descending
    assert data[0]["name"] == "Health"
    assert data[0]["weight"] == 30
    assert data[1]["name"] == "Career"
    assert data[1]["weight"] == 25
    assert data[2]["name"] == "Relationships"
    assert data[2]["weight"] == 20
    
    # All should belong to test user
    for area in data:
        assert area["user_id"] == "test_user_123"


def test_list_life_areas_empty():
    """Test listing life areas when none exist"""
    response = client.get("/api/life-areas")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_life_area():
    """Test getting a specific life area"""
    # Create a life area first
    life_area_data = {"name": "Personal Growth", "weight": 15}
    create_response = client.post("/api/life-areas", json=life_area_data)
    life_area_id = create_response.json()["id"]
    
    response = client.get(f"/api/life-areas/{life_area_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == life_area_id
    assert data["name"] == "Personal Growth"
    assert data["weight"] == 15
    assert data["user_id"] == "test_user_123"


def test_get_life_area_not_found():
    """Test getting a non-existent life area"""
    response = client.get("/api/life-areas/99999")
    
    assert response.status_code == 404
    assert "Life area not found" in response.json()["detail"]


def test_update_life_area():
    """Test updating an existing life area"""
    # Create a life area first
    life_area_data = {"name": "Original Area", "weight": 10}
    create_response = client.post("/api/life-areas", json=life_area_data)
    life_area_id = create_response.json()["id"]
    
    # Update the life area
    update_data = {
        "name": "Updated Area",
        "weight": 35,
        "icon": "update_icon",
        "color": "#FF5722",
        "description": "Updated description"
    }
    
    response = client.put(f"/api/life-areas/{life_area_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == life_area_id
    assert data["name"] == "Updated Area"
    assert data["weight"] == 35
    assert data["icon"] == "update_icon"
    assert data["color"] == "#FF5722"
    assert data["description"] == "Updated description"


def test_update_life_area_partial():
    """Test partial update of a life area"""
    # Create a life area first
    life_area_data = {
        "name": "Original Area", 
        "weight": 10,
        "icon": "original_icon"
    }
    create_response = client.post("/api/life-areas", json=life_area_data)
    life_area_id = create_response.json()["id"]
    
    # Update only weight
    update_data = {"weight": 50}
    
    response = client.put(f"/api/life-areas/{life_area_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == life_area_id
    assert data["name"] == "Original Area"  # Unchanged
    assert data["weight"] == 50  # Updated
    assert data["icon"] == "original_icon"  # Unchanged


def test_update_life_area_duplicate_name():
    """Test updating life area with duplicate name fails"""
    # Create two life areas
    area1_data = {"name": "Area 1"}
    area2_data = {"name": "Area 2"}
    
    client.post("/api/life-areas", json=area1_data)
    create_response2 = client.post("/api/life-areas", json=area2_data)
    area2_id = create_response2.json()["id"]
    
    # Try to update area2 to have same name as area1
    update_data = {"name": "Area 1"}
    response = client.put(f"/api/life-areas/{area2_id}", json=update_data)
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_update_life_area_not_found():
    """Test updating a non-existent life area"""
    update_data = {"name": "Updated Area"}
    response = client.put("/api/life-areas/99999", json=update_data)
    
    assert response.status_code == 404
    assert "Life area not found" in response.json()["detail"]


def test_delete_life_area():
    """Test deleting an existing life area"""
    # Create a life area first
    life_area_data = {"name": "Area to Delete"}
    create_response = client.post("/api/life-areas", json=life_area_data)
    life_area_id = create_response.json()["id"]
    
    # Delete the life area
    response = client.delete(f"/api/life-areas/{life_area_id}")
    
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/api/life-areas/{life_area_id}")
    assert get_response.status_code == 404


def test_delete_life_area_not_found():
    """Test deleting a non-existent life area"""
    response = client.delete("/api/life-areas/99999")
    
    assert response.status_code == 404
    assert "Life area not found" in response.json()["detail"]


def test_get_life_areas_summary():
    """Test getting life areas summary statistics"""
    # Create multiple life areas
    life_areas = [
        {"name": "Health", "weight": 40},
        {"name": "Career", "weight": 30},
        {"name": "Relationships", "weight": 20},
        {"name": "Hobbies", "weight": 10}
    ]
    
    for area_data in life_areas:
        client.post("/api/life-areas", json=area_data)
    
    response = client.get("/api/life-areas/stats/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_areas"] == 4
    assert data["total_weight"] == 100
    assert data["average_weight"] == 25.0
    
    # Check areas_by_weight is ordered correctly
    areas_by_weight = data["areas_by_weight"]
    assert len(areas_by_weight) == 4
    assert areas_by_weight[0]["name"] == "Health"
    assert areas_by_weight[0]["weight"] == 40
    assert areas_by_weight[0]["percentage"] == 40.0
    assert areas_by_weight[1]["name"] == "Career"
    assert areas_by_weight[1]["percentage"] == 30.0


def test_get_life_areas_summary_empty():
    """Test getting summary when no life areas exist"""
    response = client.get("/api/life-areas/stats/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_areas"] == 0
    assert data["total_weight"] == 0
    assert data["average_weight"] == 0
    assert data["areas_by_weight"] == []


def test_life_area_validation():
    """Test various validation scenarios"""
    
    # Test empty name
    response = client.post("/api/life-areas", json={"name": ""})
    assert response.status_code == 422
    
    # Test name too long
    response = client.post("/api/life-areas", json={"name": "A" * 101})
    assert response.status_code == 422
    
    # Test negative weight
    response = client.post("/api/life-areas", json={"name": "Test", "weight": -5})
    assert response.status_code == 422
    
    # Test weight over 100
    response = client.post("/api/life-areas", json={"name": "Test", "weight": 101})
    assert response.status_code == 422
    
    # Test icon too long
    response = client.post("/api/life-areas", json={
        "name": "Test", 
        "icon": "A" * 51
    })
    assert response.status_code == 422
    
    # Test color too long
    response = client.post("/api/life-areas", json={
        "name": "Test", 
        "color": "A" * 51
    })
    assert response.status_code == 422
    
    # Test description too long
    response = client.post("/api/life-areas", json={
        "name": "Test", 
        "description": "A" * 501
    })
    assert response.status_code == 422


def test_life_area_user_isolation():
    """Test that users can only access their own life areas"""
    # This test assumes the current mock user setup
    # In a real scenario, you'd override the user for this test
    
    # Create a life area
    life_area_data = {"name": "User Isolation Test"}
    create_response = client.post("/api/life-areas", json=life_area_data)
    life_area_id = create_response.json()["id"]
    
    # Verify the life area belongs to the test user
    response = client.get(f"/api/life-areas/{life_area_id}")
    assert response.status_code == 200
    assert response.json()["user_id"] == "test_user_123"
    
    # All life areas should belong to the test user
    list_response = client.get("/api/life-areas")
    for area in list_response.json():
        assert area["user_id"] == "test_user_123"