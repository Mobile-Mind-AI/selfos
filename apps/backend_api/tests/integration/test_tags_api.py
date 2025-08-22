"""
Integration tests for tags API endpoints.
"""

from unittest.mock import patch


class TestTagsAPI:
    """Test cases for tags API endpoints."""

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_create_tag_success(self, mock_verify_token, client):
        """Test successful tag creation via API."""
        # Mock Firebase authentication
        mock_verify_token.return_value = {
            "uid": "test_user_123",
            "email": "test@example.com",
        }

        tag_data = {"name": "Test Tag", "color": "#FF5722"}

        response = client.post(
            "/api/tags/", json=tag_data, headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == "Test Tag"
        assert response_data["color"] == "#FF5722"
        assert response_data["user_id"] == "test_user_123"
        assert "id" in response_data
        assert "created_at" in response_data

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_create_tag_duplicate_name(self, mock_verify_token, client):
        """Test creating tag with duplicate name fails."""
        mock_verify_token.return_value = {
            "uid": "test_user_123",
            "email": "test@example.com",
        }

        tag_data = {"name": "Duplicate Tag", "color": "#FF5722"}

        # Create first tag
        response1 = client.post(
            "/api/tags/", json=tag_data, headers={"Authorization": "Bearer fake-token"}
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post(
            "/api/tags/", json=tag_data, headers={"Authorization": "Bearer fake-token"}
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_create_tag_validation_error(self, mock_verify_token, client):
        """Test tag creation with validation errors."""
        mock_verify_token.return_value = {
            "uid": "test_user_123",
            "email": "test@example.com",
        }

        # Missing required fields
        response = client.post(
            "/api/tags/", json={}, headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 422

        # Invalid color format
        response = client.post(
            "/api/tags/",
            json={"name": "Test", "color": "invalid"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 422

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_get_tags_empty(self, mock_verify_token, client):
        """Test getting tags when none exist."""
        mock_verify_token.return_value = {
            "uid": "test_user_empty",
            "email": "empty@example.com",
        }

        response = client.get(
            "/api/tags/", headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        assert response.json() == []

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_get_tags_with_data(self, mock_verify_token, client):
        """Test getting tags with data."""
        mock_verify_token.return_value = {
            "uid": "test_user_data",
            "email": "data@example.com",
        }

        # Create multiple tags
        tags_data = [
            {"name": "Tag 1", "color": "#FF5722"},
            {"name": "Tag 2", "color": "#2196F3"},
            {"name": "Tag 3", "color": "#4CAF50"},
        ]

        created_tags = []
        for tag_data in tags_data:
            response = client.post(
                "/api/tags/",
                json=tag_data,
                headers={"Authorization": "Bearer fake-token"},
            )
            assert response.status_code == 201
            created_tags.append(response.json())

        # Get all tags
        response = client.get(
            "/api/tags/", headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 200
        tags = response.json()
        assert len(tags) == 3

        tag_names = [tag["name"] for tag in tags]
        assert "Tag 1" in tag_names
        assert "Tag 2" in tag_names
        assert "Tag 3" in tag_names

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_get_tag_by_id_success(self, mock_verify_token, client):
        """Test successful tag retrieval by ID."""
        mock_verify_token.return_value = {
            "uid": "test_user_get",
            "email": "get@example.com",
        }

        # Create a tag
        tag_data = {"name": "Get Test Tag", "color": "#FF5722"}
        create_response = client.post(
            "/api/tags/", json=tag_data, headers={"Authorization": "Bearer fake-token"}
        )
        assert create_response.status_code == 201
        created_tag = create_response.json()

        # Get the tag by ID
        response = client.get(
            f"/api/tags/{created_tag['id']}",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == created_tag["id"]
        assert response_data["name"] == "Get Test Tag"
        assert response_data["color"] == "#FF5722"

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_get_tag_by_id_not_found(self, mock_verify_token, client):
        """Test getting non-existent tag returns 404."""
        mock_verify_token.return_value = {
            "uid": "test_user_404",
            "email": "404@example.com",
        }

        response = client.get(
            "/api/tags/999", headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_update_tag_success(self, mock_verify_token, client):
        """Test successful tag update."""
        mock_verify_token.return_value = {
            "uid": "test_user_update",
            "email": "update@example.com",
        }

        # Create a tag
        tag_data = {"name": "Original Tag", "color": "#FF5722"}
        create_response = client.post(
            "/api/tags/", json=tag_data, headers={"Authorization": "Bearer fake-token"}
        )
        assert create_response.status_code == 201
        created_tag = create_response.json()

        # Update the tag
        update_data = {"name": "Updated Tag", "color": "#2196F3"}
        response = client.put(
            f"/api/tags/{created_tag['id']}",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "Updated Tag"
        assert response_data["color"] == "#2196F3"
        assert response_data["id"] == created_tag["id"]

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_update_tag_partial(self, mock_verify_token, client):
        """Test partial tag update."""
        mock_verify_token.return_value = {
            "uid": "test_user_partial",
            "email": "partial@example.com",
        }

        # Create a tag
        tag_data = {"name": "Original Tag", "color": "#FF5722"}
        create_response = client.post(
            "/api/tags/", json=tag_data, headers={"Authorization": "Bearer fake-token"}
        )
        assert create_response.status_code == 201
        created_tag = create_response.json()

        # Update only name
        update_data = {"name": "Updated Name Only"}
        response = client.put(
            f"/api/tags/{created_tag['id']}",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "Updated Name Only"
        assert response_data["color"] == "#FF5722"  # Should remain unchanged

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_update_tag_not_found(self, mock_verify_token, client):
        """Test updating non-existent tag returns 404."""
        mock_verify_token.return_value = {
            "uid": "test_user_update_404",
            "email": "update404@example.com",
        }

        update_data = {"name": "Updated Tag"}
        response = client.put(
            "/api/tags/999",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_delete_tag_success(self, mock_verify_token, client):
        """Test successful tag deletion."""
        mock_verify_token.return_value = {
            "uid": "test_user_delete",
            "email": "delete@example.com",
        }

        # Create a tag
        tag_data = {"name": "Tag to Delete", "color": "#FF5722"}
        create_response = client.post(
            "/api/tags/", json=tag_data, headers={"Authorization": "Bearer fake-token"}
        )
        assert create_response.status_code == 201
        created_tag = create_response.json()

        # Delete the tag
        response = client.delete(
            f"/api/tags/{created_tag['id']}",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 204

        # Verify tag is deleted
        get_response = client.get(
            f"/api/tags/{created_tag['id']}",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert get_response.status_code == 404

    @patch("dependencies.firebase_admin.auth.verify_id_token")
    def test_delete_tag_not_found(self, mock_verify_token, client):
        """Test deleting non-existent tag returns 404."""
        mock_verify_token.return_value = {
            "uid": "test_user_delete_404",
            "email": "delete404@example.com",
        }

        response = client.delete(
            "/api/tags/999", headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Tag not found"

    def test_user_isolation(self, client):
        """Test that users can only access their own tags."""
        # User 1 creates a tag
        tag_data = {"name": "User1 Private Tag", "color": "#FF5722"}
        create_response = client.post(
            "/api/tags/",
            json=tag_data,
            headers={"Authorization": "Bearer mock_token_user1_isolation"},
        )
        assert create_response.status_code == 201
        user1_tag = create_response.json()

        # User 2 tries to access user1's tag
        # Should not be able to get user1's tag
        response = client.get(
            f"/api/tags/{user1_tag['id']}",
            headers={"Authorization": "Bearer mock_token_user2_isolation"},
        )
        assert response.status_code == 404

        # Should not be able to update user1's tag
        response = client.put(
            f"/api/tags/{user1_tag['id']}",
            json={"name": "Hacked Tag"},
            headers={"Authorization": "Bearer mock_token_user2_isolation"},
        )
        assert response.status_code == 404

        # Should not be able to delete user1's tag
        response = client.delete(
            f"/api/tags/{user1_tag['id']}",
            headers={"Authorization": "Bearer mock_token_user2_isolation"},
        )
        assert response.status_code == 404

        # User2's tag list should be empty
        response = client.get(
            "/api/tags/", headers={"Authorization": "Bearer mock_token_user2_isolation"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_unauthorized_access(self, client):
        """Test that all endpoints require authentication."""
        # Test all endpoints without auth token

        # POST /api/tags/
        response = client.post("/api/tags/", json={"name": "Test", "color": "#FF5722"})
        assert response.status_code == 401

        # GET /api/tags/
        response = client.get("/api/tags/")
        assert response.status_code == 401

        # GET /api/tags/1
        response = client.get("/api/tags/1/")
        assert response.status_code == 401

        # PUT /api/tags/1
        response = client.put("/api/tags/1/", json={"name": "Test"})
        assert response.status_code == 401

        # DELETE /api/tags/1
        response = client.delete("/api/tags/1/")
        assert response.status_code == 401
