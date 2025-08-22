"""Integration tests for analytics API endpoints."""

from datetime import datetime, time
from uuid import uuid4

import pytest
from models import UserPreferences, UserPreferencesHistory


class TestAnalyticsAPI:
    """Integration tests for analytics endpoints."""

    @pytest.fixture
    def db_session(self, isolated_test_setup):
        """Create a database session for testing."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        try:
            yield session
        finally:
            session.close()

    def test_full_preferences_update_and_analytics_flow(
        self, client, mock_user, db_session
    ):
        """Test complete flow: update preferences -> get history -> get summary."""

        # Step 1: Update preferences (this should trigger history logging)
        update_payload = {
            "tone": "coach",
            "notifications_enabled": True,
            "default_view": "list",
        }

        response = client.put(
            "/api/user-preferences",
            json=update_payload,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        updated_prefs = response.json()
        assert updated_prefs["tone"] == "coach"
        assert updated_prefs["notifications_enabled"] is True
        assert updated_prefs["default_view"] == "list"

        # Step 2: Update preferences again to create more history
        second_update_payload = {"tone": "professional", "notifications_enabled": False}

        response = client.put(
            "/api/user-preferences",
            json=second_update_payload,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200

        # Step 3: Get preferences history via API
        response = client.get(
            "/api/analytics/preferences/history",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        history = response.json()

        # We should have history from the second update (tone and notifications_enabled changed)
        assert len(history) >= 2

        # Check that history items have the expected structure
        for item in history:
            assert "id" in item
            assert "preference_name" in item
            assert "old_value" in item
            assert "new_value" in item
            assert "changed_at" in item

        # Verify specific changes are recorded
        tone_changes = [h for h in history if h["preference_name"] == "tone"]
        notifications_changes = [
            h for h in history if h["preference_name"] == "notifications_enabled"
        ]

        assert len(tone_changes) >= 1
        assert len(notifications_changes) >= 1

        # Step 4: Get preferences change summary via API
        response = client.get(
            "/api/analytics/preferences/summary?days_back=7",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        summary = response.json()

        # Verify summary structure
        assert "total_changes" in summary
        assert "days_analyzed" in summary
        assert "preferences_changed" in summary
        assert "change_counts" in summary
        assert "most_changed_preference" in summary
        assert "latest_change" in summary

        # Verify summary data
        assert summary["total_changes"] >= 2
        assert summary["days_analyzed"] == 7
        assert "tone" in summary["preferences_changed"]
        assert "notifications_enabled" in summary["preferences_changed"]

    def test_get_preferences_history_with_filters(self, client, mock_user, db_session):
        """Test getting preferences history with limit and preference_name filters."""

        # First, create some preferences history manually for testing
        user_id = mock_user["uid"]

        # Create test history entries
        entries = [
            UserPreferencesHistory(
                id=str(uuid4()),
                user_id=user_id,
                preference_name="tone",
                old_value="friendly",
                new_value="coach",
                changed_at=datetime.utcnow(),
            ),
            UserPreferencesHistory(
                id=str(uuid4()),
                user_id=user_id,
                preference_name="tone",
                old_value="coach",
                new_value="professional",
                changed_at=datetime.utcnow(),
            ),
            UserPreferencesHistory(
                id=str(uuid4()),
                user_id=user_id,
                preference_name="notifications_enabled",
                old_value="False",
                new_value="True",
                changed_at=datetime.utcnow(),
            ),
        ]

        db_session.add_all(entries)
        db_session.commit()

        # Test filter by preference_name
        response = client.get(
            "/api/analytics/preferences/history?preference_name=tone",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        history = response.json()

        assert len(history) == 2
        for item in history:
            assert item["preference_name"] == "tone"

        # Test limit parameter
        response = client.get(
            "/api/analytics/preferences/history?limit=1",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        history = response.json()

        assert len(history) == 1

    def test_get_preferences_summary_with_different_time_windows(
        self, client, mock_user, db_session
    ):
        """Test getting preferences summary with different time windows."""

        # Create some test data
        user_id = mock_user["uid"]

        entry = UserPreferencesHistory(
            id=str(uuid4()),
            user_id=user_id,
            preference_name="tone",
            old_value="friendly",
            new_value="coach",
            changed_at=datetime.utcnow(),
        )

        db_session.add(entry)
        db_session.commit()

        # Test different time windows
        for days_back in [1, 7, 30]:
            response = client.get(
                f"/api/analytics/preferences/summary?days_back={days_back}",
                headers={"Authorization": "Bearer fake-token"},
            )

            assert response.status_code == 200
            summary = response.json()

            assert summary["days_analyzed"] == days_back
            # Since our test entry is from now, it should appear in all time windows
            assert summary["total_changes"] >= 1

    def test_empty_history_responses(self, client, mock_user):
        """Test API responses when no preference history exists."""

        # Test getting history for user with no changes
        response = client.get(
            "/api/analytics/preferences/history",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        history = response.json()
        assert history == []

        # Test getting summary for user with no changes
        response = client.get(
            "/api/analytics/preferences/summary",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        summary = response.json()

        assert summary["total_changes"] == 0
        assert summary["preferences_changed"] == []
        assert summary["most_changed_preference"] is None
        assert summary["latest_change"] is None

    def test_analytics_endpoints_return_valid_response_structure(self, client):
        """Test that analytics endpoints return valid response structures."""

        # Test preferences history endpoint
        response = client.get("/api/analytics/preferences/history/")
        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)

        # Test preferences summary endpoint
        response = client.get("/api/analytics/preferences/summary/")
        assert response.status_code == 200
        summary = response.json()

        # Check required fields in summary
        assert "total_changes" in summary
        assert "days_analyzed" in summary
        assert "preferences_changed" in summary
        assert "change_counts" in summary
        assert (
            "most_changed_preference" in summary
            or summary["most_changed_preference"] is None
        )
        assert "latest_change" in summary or summary["latest_change"] is None

    def test_preferences_update_creates_correct_history(
        self, client, mock_user, db_session
    ):
        """Test that different types of preference updates create correct history entries."""

        user_id = mock_user["uid"]

        # Create initial preferences
        initial_prefs = UserPreferences(
            id=str(uuid4()),
            user_id=user_id,
            tone="friendly",
            notifications_enabled=True,
            notification_time=time(9, 0),
            default_view="card",
        )
        db_session.add(initial_prefs)
        db_session.commit()

        # Test different types of updates

        # 1. String value change
        response = client.put(
            "/api/user-preferences",
            json={"tone": "coach"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 200

        # 2. Boolean value change
        response = client.put(
            "/api/user-preferences",
            json={"notifications_enabled": False},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 200

        # 3. Time value change
        response = client.put(
            "/api/user-preferences",
            json={"notification_time": "08:30:00"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 200

        # 4. New field addition (None to value)
        response = client.put(
            "/api/user-preferences",
            json={"prefers_video": True},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 200

        # Verify all changes were recorded
        response = client.get(
            "/api/analytics/preferences/history",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        history = response.json()

        # We should have at least 3 history entries (some fields like prefers_video might not exist)
        assert len(history) >= 3

        # Verify specific changes that we know should exist
        preference_names = [h["preference_name"] for h in history]
        assert "tone" in preference_names
        assert "notifications_enabled" in preference_names
        assert "notification_time" in preference_names

        # Check that tone changed from friendly to coach
        tone_changes = [h for h in history if h["preference_name"] == "tone"]
        assert len(tone_changes) >= 1
        tone_change = tone_changes[0]
        assert tone_change["old_value"] == "friendly"
        assert tone_change["new_value"] == "coach"

    def test_quick_setup_creates_history(self, client, mock_user, db_session):
        """Test that quick-setup endpoint also creates history when updating existing preferences."""

        user_id = mock_user["uid"]

        # Create initial preferences
        initial_prefs = UserPreferences(
            id=str(uuid4()),
            user_id=user_id,
            tone="friendly",
            notifications_enabled=False,
            default_view="card",
        )
        db_session.add(initial_prefs)
        db_session.commit()

        # Use quick-setup endpoint to update preferences
        response = client.post(
            "/api/user-preferences/quick-setup?tone=coach&notifications=true&default_view=list",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 201

        # Verify history was created
        response = client.get(
            "/api/analytics/preferences/history",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        history = response.json()

        # Should have history for tone, notifications_enabled, and default_view changes
        assert len(history) >= 3

        preference_names = [h["preference_name"] for h in history]
        assert "tone" in preference_names
        assert "notifications_enabled" in preference_names
        assert "default_view" in preference_names
