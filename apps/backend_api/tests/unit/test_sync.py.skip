"""
Unit tests for batch sync API endpoints.

Tests the offline-first sync functionality including:
- Batch operations processing
- Conflict detection and resolution
- Delta sync for incremental updates
- Error handling and validation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from models import Base
from models.goals import Goal
from models.onboarding import OnboardingState, PersonalProfile
from dependencies import get_db, get_current_user

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

def override_get_db_sync():
    """Override database dependency for testing sync"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_sync():
    """Override authentication dependency for testing sync"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_sync
app.dependency_overrides[get_current_user] = override_get_current_user_sync

# Test fixtures
@pytest.fixture
def test_user():
    return {"uid": "test_user_123", "email": "testuser@example.com"}

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test_token"}

class TestBatchSync:
    """Test batch synchronization operations."""
    
    def test_batch_sync_create_goal(self, auth_headers):
        """Test creating a goal through batch sync."""
        batch_request = {
            "operations": [
                {
                    "object_id": "goal_123",
                    "object_type": "goal",
                    "operation": "create",
                    "data": {
                        "title": "Test Goal",
                        "description": "A test goal from sync",
                        "status": "active",
                        "progress": 0.0
                    },
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=batch_request, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert results[0]["new_version"] == 1
        # For auto-incrementing IDs, the returned object_id will be the DB-generated ID
        assert results[0]["object_id"] is not None

    def test_batch_sync_update_goal(self, auth_headers):
        """Test updating a goal through batch sync."""
        # First create a goal
        create_request = {
            "operations": [
                {
                    "object_id": "goal_456",
                    "object_type": "goal",
                    "operation": "create",
                    "data": {
                        "title": "Goal to Update",
                        "description": "Will be updated",
                        "status": "active",
                        "progress": 0.0
                    },
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=create_request, 
                             headers=auth_headers)
        assert response.status_code == 200
        create_results = response.json()
        # Get the actual database ID returned from create
        created_id = create_results[0]["object_id"]
        
        # Now update the goal using the actual database ID
        update_request = {
            "operations": [
                {
                    "object_id": created_id,
                    "object_type": "goal",
                    "operation": "update",
                    "data": {
                        "title": "Updated Goal Title",
                        "progress": 50.0
                    },
                    "version": 2,
                    "if_match_version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=update_request, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["object_id"] == created_id
        assert results[0]["status"] == "success"
        assert results[0]["new_version"] == 2

    def test_batch_sync_delete_goal(self, auth_headers):
        """Test deleting a goal through batch sync."""
        # First create a goal
        create_request = {
            "operations": [
                {
                    "object_id": "goal_789",
                    "object_type": "goal",
                    "operation": "create",
                    "data": {
                        "title": "Goal to Delete",
                        "status": "active",
                        "progress": 0.0
                    },
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=create_request, 
                             headers=auth_headers)
        assert response.status_code == 200
        
        # Now delete the goal
        delete_request = {
            "operations": [
                {
                    "object_id": "goal_789",
                    "object_type": "goal",
                    "operation": "delete",
                    "data": {},
                    "version": 2
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=delete_request, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["object_id"] == "goal_789"
        assert results[0]["status"] == "success"

    def test_batch_sync_conflict_detection(self, auth_headers):
        """Test conflict detection when version mismatch occurs."""
        # Create a goal
        create_request = {
            "operations": [
                {
                    "object_id": "goal_conflict",
                    "object_type": "goal",
                    "operation": "create",
                    "data": {
                        "title": "Conflict Test Goal",
                        "status": "active",
                        "progress": 0.0
                    },
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=create_request, 
                             headers=auth_headers)
        assert response.status_code == 200
        create_results = response.json()
        # Get the actual database ID returned from create
        created_id = create_results[0]["object_id"]
        
        # Try to update with wrong version (simulating conflict)
        conflict_request = {
            "operations": [
                {
                    "object_id": created_id,
                    "object_type": "goal", 
                    "operation": "update",
                    "data": {
                        "title": "Updated Title"
                    },
                    "version": 2,
                    "if_match_version": 5  # Wrong version
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=conflict_request, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["object_id"] == created_id
        assert results[0]["status"] == "conflict"
        assert results[0]["new_version"] == 1  # Server version
        assert "server_data" in results[0]

    def test_batch_sync_multiple_operations(self, auth_headers):
        """Test processing multiple operations in a single batch."""
        batch_request = {
            "operations": [
                {
                    "object_id": "goal_multi_1",
                    "object_type": "goal",
                    "operation": "create",
                    "data": {
                        "title": "Goal 1",
                        "status": "active",
                        "progress": 0.0
                    },
                    "version": 1
                },
                {
                    "object_id": "goal_multi_2",
                    "object_type": "goal",
                    "operation": "create",
                    "data": {
                        "title": "Goal 2",
                        "status": "active", 
                        "progress": 25.0
                    },
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=batch_request, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        
        # Check both operations succeeded
        success_count = sum(1 for r in results if r["status"] == "success")
        assert success_count == 2

    def test_batch_sync_invalid_object_type(self, auth_headers):
        """Test handling of invalid object types."""
        batch_request = {
            "operations": [
                {
                    "object_id": "invalid_123",
                    "object_type": "invalid_type",
                    "operation": "create",
                    "data": {"title": "Test"},
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=batch_request, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["object_id"] == "invalid_123"
        assert results[0]["status"] == "error"
        assert "Unknown object type" in results[0]["error_message"]

class TestDeltaSync:
    """Test delta synchronization functionality."""
    
    def test_delta_sync_basic(self, auth_headers):
        """Test basic delta sync functionality."""
        # Create some test data first
        create_request = {
            "operations": [
                {
                    "object_id": "delta_goal_1",
                    "object_type": "goal",
                    "operation": "create",
                    "data": {
                        "title": "Delta Test Goal",
                        "status": "active",
                        "progress": 0.0
                    },
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        create_response = client.post("/api/sync/batch", 
                                    json=create_request, 
                                    headers=auth_headers)
        assert create_response.status_code == 200
        
        # Get delta sync from beginning of time
        since_timestamp = 0
        response = client.get(f"/api/sync/delta/{since_timestamp}", 
                            headers=auth_headers)
        
        assert response.status_code == 200
        delta_data = response.json()
        
        assert "changes" in delta_data
        assert "current_timestamp" in delta_data
        assert "has_more" in delta_data
        assert isinstance(delta_data["changes"], list)
        
        # Should have at least our created goal
        changes = delta_data["changes"]
        goal_changes = [c for c in changes if c["object_type"] == "goal"]
        assert len(goal_changes) >= 1

    def test_delta_sync_with_filter(self, auth_headers):
        """Test delta sync with object type filtering."""
        # Test filtering by object type
        response = client.get("/api/sync/delta/0?object_types=goal", 
                            headers=auth_headers)
        
        assert response.status_code == 200
        delta_data = response.json()
        
        # All changes should be goals
        changes = delta_data["changes"]
        for change in changes:
            assert change["object_type"] == "goal"

    def test_delta_sync_empty_result(self, auth_headers):
        """Test delta sync with future timestamp (should be empty)."""
        # Use future timestamp
        future_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000) + 86400000  # +1 day
        response = client.get(f"/api/sync/delta/{future_timestamp}", 
                            headers=auth_headers)
        
        assert response.status_code == 200
        delta_data = response.json()
        assert len(delta_data["changes"]) == 0

class TestSyncStatus:
    """Test sync status endpoint."""
    
    def test_sync_status(self, auth_headers):
        """Test sync status endpoint returns proper statistics."""
        response = client.get("/api/sync/status", headers=auth_headers)
        
        assert response.status_code == 200
        status_data = response.json()
        
        assert "user_id" in status_data
        assert "sync_timestamp" in status_data
        assert "object_stats" in status_data
        
        # Check that we have stats for known object types
        object_stats = status_data["object_stats"]
        for object_type in ["goal"]:  # Test known types
            if object_type in object_stats:
                stats = object_stats[object_type]
                assert "total_objects" in stats
                assert "recent_changes" in stats
                assert isinstance(stats["total_objects"], int)
                assert isinstance(stats["recent_changes"], int)

class TestConflictResolution:
    """Test conflict resolution functionality."""
    
    def test_resolve_conflict(self, auth_headers):
        """Test manual conflict resolution."""
        # First create a goal that we'll resolve conflicts for
        create_request = {
            "operations": [
                {
                    "object_id": "conflict_resolve_goal",
                    "object_type": "goal",
                    "operation": "create",
                    "data": {
                        "title": "Conflict Resolution Test",
                        "status": "active",
                        "progress": 0.0
                    },
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=create_request, 
                             headers=auth_headers)
        assert response.status_code == 200
        create_results = response.json()
        # Get the actual database ID returned from create
        created_id = create_results[0]["object_id"]
        
        # Now resolve a "conflict" by providing resolution data
        resolution_data = {
            "object_type": "goal",
            "data": {
                "title": "Resolved Title",
                "progress": 100.0,
                "status": "completed"
            }
        }
        
        response = client.post(f"/api/sync/resolve-conflict/{created_id}",
                             json=resolution_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["object_id"] == created_id
        assert result["status"] == "resolved"
        assert result["new_version"] == 2  # Should increment version

class TestSyncValidation:
    """Test input validation for sync endpoints."""
    
    def test_batch_sync_missing_fields(self, auth_headers):
        """Test validation of required fields in batch sync."""
        # Missing object_id
        invalid_request = {
            "operations": [
                {
                    "object_type": "goal",
                    "operation": "create",
                    "data": {"title": "Test"},
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=invalid_request, 
                             headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

    def test_batch_sync_invalid_operation_type(self, auth_headers):
        """Test validation of operation types."""
        invalid_request = {
            "operations": [
                {
                    "object_id": "test_123",
                    "object_type": "goal",
                    "operation": "invalid_operation",  # Invalid
                    "data": {"title": "Test"},
                    "version": 1
                }
            ],
            "client_id": "test_client"
        }
        
        response = client.post("/api/sync/batch", 
                             json=invalid_request, 
                             headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

    def test_unauthorized_access(self):
        """Test that sync endpoints require authentication."""
        # Temporarily clear auth overrides to test unauthorized access
        original_user_override = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides.pop(get_current_user, None)
        
        try:
            # Test without auth headers
            batch_request = {
                "operations": [],
                "client_id": "test_client"
            }
            
            response = client.post("/api/sync/batch", json=batch_request)
            assert response.status_code == 401
            
            response = client.get("/api/sync/delta/0")
            assert response.status_code == 401
            
            response = client.get("/api/sync/status")
            assert response.status_code == 401
        finally:
            # Restore auth override
            if original_user_override:
                app.dependency_overrides[get_current_user] = original_user_override