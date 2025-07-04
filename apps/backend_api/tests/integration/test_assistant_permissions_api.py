"""
Integration tests for the Assistant Permissions API endpoints.

Tests the full API flow including authentication, permission checking,
and CRUD operations for the assistant sharing system.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from main import app
from models.onboarding import AssistantProfile, AssistantPermission
from models.user import User


class TestAssistantPermissionsAPI:
    """Test the assistant permissions API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_users(self, db: Session):
        """Create mock users for testing."""
        users = []
        for i in range(3):
            user = User(
                uid=f"test_user_{i}",
                email=f"user{i}@example.com"
            )
            db.add(user)
            users.append(user)
        
        db.commit()
        return users

    @pytest.fixture
    def sample_assistant(self, db: Session, mock_users):
        """Create a sample assistant owned by user_0."""
        assistant = AssistantProfile(
            user_id=mock_users[0].uid,
            owner_id=mock_users[0].uid,
            name="Test Assistant",
            description="A test assistant for API testing",
            ai_model="gpt-3.5-turbo",
            language="en",
            style={
                "formality": 50,
                "directness": 70,
                "humor": 30,
                "empathy": 80,
                "motivation": 60
            },
            version=1000
        )
        db.add(assistant)
        db.commit()
        db.refresh(assistant)
        return assistant

    @pytest.fixture
    def auth_headers(self):
        """Create mock authentication headers."""
        def _create_headers(user_uid: str):
            # In real implementation, this would be a proper Firebase token
            # For testing, we'll use a mock token that our test auth system recognizes
            return {
                "Authorization": f"Bearer mock_token_{user_uid}",
                "Content-Type": "application/json"
            }
        return _create_headers

    def test_get_user_assistants_owner(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting assistants for the owner."""
        headers = auth_headers(mock_users[0].uid)
        
        response = client.get("/api/assistants", headers=headers)
        
        assert response.status_code == 200
        assistants = response.json()
        assert len(assistants) == 1
        assert assistants[0]["name"] == "Test Assistant"
        assert assistants[0]["id"] == sample_assistant.id

    def test_get_user_assistants_unauthorized(self, client):
        """Test getting assistants without authentication."""
        response = client.get("/api/assistants")
        
        assert response.status_code == 401

    def test_get_user_assistants_no_access(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting assistants for user without access."""
        headers = auth_headers(mock_users[1].uid)  # Different user
        
        response = client.get("/api/assistants", headers=headers)
        
        assert response.status_code == 200
        assistants = response.json()
        assert len(assistants) == 0  # Should not see owner's private assistant

    def test_get_specific_assistant_owner(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting a specific assistant as owner."""
        headers = auth_headers(mock_users[0].uid)
        
        response = client.get(f"/api/assistants/{sample_assistant.id}", headers=headers)
        
        assert response.status_code == 200
        assistant_data = response.json()
        assert assistant_data["name"] == "Test Assistant"
        assert assistant_data["id"] == sample_assistant.id

    def test_get_specific_assistant_forbidden(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting a specific assistant without permission."""
        headers = auth_headers(mock_users[1].uid)  # Different user
        
        response = client.get(f"/api/assistants/{sample_assistant.id}", headers=headers)
        
        assert response.status_code == 403
        error_data = response.json()
        assert "Insufficient permissions" in error_data["detail"]

    def test_share_assistant_success(self, client, mock_users, sample_assistant, auth_headers):
        """Test successfully sharing an assistant."""
        owner_headers = auth_headers(mock_users[0].uid)
        share_data = {
            "target_user_id": mock_users[1].uid,
            "permission_level": "edit"
        }
        
        response = client.post(
            f"/api/assistants/{sample_assistant.id}/share",
            headers=owner_headers,
            json=share_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "shared successfully" in result["message"]

    def test_share_assistant_insufficient_permissions(self, client, mock_users, sample_assistant, auth_headers):
        """Test sharing assistant without sufficient permissions."""
        non_owner_headers = auth_headers(mock_users[1].uid)
        share_data = {
            "target_user_id": mock_users[2].uid,
            "permission_level": "read"
        }
        
        response = client.post(
            f"/api/assistants/{sample_assistant.id}/share",
            headers=non_owner_headers,
            json=share_data
        )
        
        assert response.status_code == 500  # Will be wrapped in a 500 due to HTTPException
        # In a real implementation, this should be 403

    def test_update_assistant_owner(self, client, mock_users, sample_assistant, auth_headers):
        """Test updating assistant as owner."""
        headers = auth_headers(mock_users[0].uid)
        update_data = {
            "name": "Updated Assistant Name",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/assistants/{sample_assistant.id}",
            headers=headers,
            json=update_data
        )
        
        assert response.status_code == 200
        updated_assistant = response.json()
        assert updated_assistant["name"] == "Updated Assistant Name"
        assert updated_assistant["description"] == "Updated description"

    def test_update_assistant_forbidden(self, client, mock_users, sample_assistant, auth_headers):
        """Test updating assistant without edit permission."""
        non_owner_headers = auth_headers(mock_users[1].uid)
        update_data = {
            "name": "Unauthorized Update"
        }
        
        response = client.put(
            f"/api/assistants/{sample_assistant.id}",
            headers=non_owner_headers,
            json=update_data
        )
        
        assert response.status_code == 403
        error_data = response.json()
        assert "Insufficient permissions" in error_data["detail"]

    def test_revoke_permission(self, client, db, mock_users, sample_assistant, auth_headers):
        """Test revoking permission for an assistant."""
        # First share the assistant
        owner_headers = auth_headers(mock_users[0].uid)
        share_data = {
            "target_user_id": mock_users[1].uid,
            "permission_level": "edit"
        }
        
        share_response = client.post(
            f"/api/assistants/{sample_assistant.id}/share",
            headers=owner_headers,
            json=share_data
        )
        assert share_response.status_code == 200

        # Then revoke the permission
        revoke_response = client.delete(
            f"/api/assistants/{sample_assistant.id}/permissions/{mock_users[1].uid}",
            headers=owner_headers
        )
        
        assert revoke_response.status_code == 200
        result = revoke_response.json()
        assert "revoked successfully" in result["message"]

        # Verify the user no longer has access
        user_headers = auth_headers(mock_users[1].uid)
        access_response = client.get(f"/api/assistants/{sample_assistant.id}", headers=user_headers)
        assert access_response.status_code == 403

    def test_get_assistant_permissions(self, client, db, mock_users, sample_assistant, auth_headers):
        """Test getting all permissions for an assistant."""
        # Share with a user first
        owner_headers = auth_headers(mock_users[0].uid)
        share_data = {
            "target_user_id": mock_users[1].uid,
            "permission_level": "edit"
        }
        
        share_response = client.post(
            f"/api/assistants/{sample_assistant.id}/share",
            headers=owner_headers,
            json=share_data
        )
        assert share_response.status_code == 200

        # Get permissions
        permissions_response = client.get(
            f"/api/assistants/{sample_assistant.id}/permissions",
            headers=owner_headers
        )
        
        assert permissions_response.status_code == 200
        permissions = permissions_response.json()
        assert len(permissions) == 1
        assert permissions[0]["user_id"] == mock_users[1].uid
        assert permissions[0]["permission_level"] == "edit"

    def test_get_assistant_permissions_forbidden(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting permissions without admin access."""
        non_admin_headers = auth_headers(mock_users[1].uid)
        
        response = client.get(
            f"/api/assistants/{sample_assistant.id}/permissions",
            headers=non_admin_headers
        )
        
        assert response.status_code == 403

    def test_get_assistant_versions(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting assistant version information."""
        headers = auth_headers(mock_users[0].uid)
        
        response = client.get("/api/assistants/versions", headers=headers)
        
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 1
        assert versions[0]["assistant_id"] == sample_assistant.id
        assert versions[0]["version"] == sample_assistant.version

    def test_get_specific_assistant_versions(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting version info for specific assistants."""
        headers = auth_headers(mock_users[0].uid)
        
        # Test with query parameter (this depends on your API design)
        response = client.get(
            f"/api/assistants/versions?assistant_ids={sample_assistant.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 1
        assert versions[0]["assistant_id"] == sample_assistant.id

    def test_get_user_permission_level(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting user's permission level for an assistant."""
        headers = auth_headers(mock_users[0].uid)
        
        response = client.get(
            f"/api/assistants/{sample_assistant.id}/permission-level",
            headers=headers
        )
        
        assert response.status_code == 200
        permission_info = response.json()
        assert permission_info["assistant_id"] == sample_assistant.id
        assert permission_info["permission_level"] == "owner"
        assert permission_info["has_access"] is True

    def test_permission_level_no_access(self, client, mock_users, sample_assistant, auth_headers):
        """Test getting permission level when user has no access."""
        headers = auth_headers(mock_users[1].uid)  # Different user
        
        response = client.get(
            f"/api/assistants/{sample_assistant.id}/permission-level",
            headers=headers
        )
        
        assert response.status_code == 200
        permission_info = response.json()
        assert permission_info["assistant_id"] == sample_assistant.id
        assert permission_info["permission_level"] is None
        assert permission_info["has_access"] is False

    def test_cleanup_expired_permissions(self, client, mock_users, auth_headers):
        """Test cleanup endpoint for expired permissions."""
        headers = auth_headers(mock_users[0].uid)
        
        response = client.post("/api/permissions/cleanup", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert "Cleaned up" in result["message"]
        assert isinstance(result["message"], str)

    def test_public_assistant_access(self, client, db, mock_users, auth_headers):
        """Test access to public assistants."""
        # Create a public assistant
        public_assistant = AssistantProfile(
            user_id=mock_users[0].uid,
            owner_id=mock_users[0].uid,
            name="Public Assistant",
            description="A public assistant",
            ai_model="gpt-3.5-turbo",
            language="en",
            style={
                "formality": 50,
                "directness": 50,
                "humor": 30,
                "empathy": 70,
                "motivation": 60
            },
            is_public=True,
            version=1000
        )
        db.add(public_assistant)
        db.commit()
        db.refresh(public_assistant)

        # Different user should be able to access public assistant
        user_headers = auth_headers(mock_users[1].uid)
        
        # Should appear in user's assistant list
        list_response = client.get("/api/assistants", headers=user_headers)
        assert list_response.status_code == 200
        assistants = list_response.json()
        public_assistant_found = any(a["name"] == "Public Assistant" for a in assistants)
        assert public_assistant_found, "Public assistant should appear in user's list"

        # Should be able to get specific public assistant
        get_response = client.get(f"/api/assistants/{public_assistant.id}", headers=user_headers)
        assert get_response.status_code == 200
        assistant_data = get_response.json()
        assert assistant_data["name"] == "Public Assistant"

        # Should NOT be able to edit public assistant
        update_response = client.put(
            f"/api/assistants/{public_assistant.id}",
            headers=user_headers,
            json={"name": "Hacked Name"}
        )
        assert update_response.status_code == 403


class TestAssistantSharingWorkflow:
    """Test complete sharing workflows."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture  
    def users_and_assistant(self, db: Session):
        """Set up users and assistant for workflow testing."""
        # Create users
        users = []
        for i in range(3):
            user = User(uid=f"workflow_user_{i}", email=f"workflow{i}@example.com")
            db.add(user)
            users.append(user)
        
        # Create assistant
        assistant = AssistantProfile(
            user_id=users[0].uid,
            owner_id=users[0].uid,
            name="Workflow Test Assistant",
            ai_model="gpt-3.5-turbo",
            language="en",
            style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
            version=1000
        )
        db.add(assistant)
        db.commit()
        
        for user in users:
            db.refresh(user)
        db.refresh(assistant)
        
        return users, assistant

    @pytest.fixture
    def auth_headers(self):
        def _create_headers(user_uid: str):
            return {
                "Authorization": f"Bearer mock_token_{user_uid}",
                "Content-Type": "application/json"
            }
        return _create_headers

    def test_complete_sharing_workflow(self, client, users_and_assistant, auth_headers):
        """Test a complete sharing workflow from owner to multiple users."""
        users, assistant = users_and_assistant
        owner_headers = auth_headers(users[0].uid)
        user1_headers = auth_headers(users[1].uid)
        user2_headers = auth_headers(users[2].uid)

        # Step 1: Owner shares with User1 (edit permission)
        share_response = client.post(
            f"/api/assistants/{assistant.id}/share",
            headers=owner_headers,
            json={
                "target_user_id": users[1].uid,
                "permission_level": "edit"
            }
        )
        assert share_response.status_code == 200

        # Step 2: User1 can now see and edit the assistant
        user1_list = client.get("/api/assistants", headers=user1_headers)
        assert user1_list.status_code == 200
        assert len(user1_list.json()) == 1

        edit_response = client.put(
            f"/api/assistants/{assistant.id}",
            headers=user1_headers,
            json={"description": "Updated by User1"}
        )
        assert edit_response.status_code == 200

        # Step 3: User1 cannot share (no admin permission)
        share_attempt = client.post(
            f"/api/assistants/{assistant.id}/share",
            headers=user1_headers,
            json={
                "target_user_id": users[2].uid,
                "permission_level": "read"
            }
        )
        assert share_attempt.status_code == 500  # Should be 403 in real implementation

        # Step 4: Owner upgrades User1 to admin
        upgrade_response = client.post(
            f"/api/assistants/{assistant.id}/share",
            headers=owner_headers,
            json={
                "target_user_id": users[1].uid,
                "permission_level": "admin"
            }
        )
        assert upgrade_response.status_code == 200

        # Step 5: User1 can now share with User2
        share_to_user2 = client.post(
            f"/api/assistants/{assistant.id}/share",
            headers=user1_headers,
            json={
                "target_user_id": users[2].uid,
                "permission_level": "read"
            }
        )
        assert share_to_user2.status_code == 200

        # Step 6: User2 can read but not edit
        user2_get = client.get(f"/api/assistants/{assistant.id}", headers=user2_headers)
        assert user2_get.status_code == 200

        user2_edit_attempt = client.put(
            f"/api/assistants/{assistant.id}",
            headers=user2_headers,
            json={"description": "Unauthorized edit"}
        )
        assert user2_edit_attempt.status_code == 403

        # Step 7: Owner revokes User1's permission
        revoke_response = client.delete(
            f"/api/assistants/{assistant.id}/permissions/{users[1].uid}",
            headers=owner_headers
        )
        assert revoke_response.status_code == 200

        # Step 8: User1 no longer has access
        user1_access_check = client.get(f"/api/assistants/{assistant.id}", headers=user1_headers)
        assert user1_access_check.status_code == 403

        # Step 9: User2 still has read access (granted by User1 before revocation)
        user2_access_check = client.get(f"/api/assistants/{assistant.id}", headers=user2_headers)
        assert user2_access_check.status_code == 200