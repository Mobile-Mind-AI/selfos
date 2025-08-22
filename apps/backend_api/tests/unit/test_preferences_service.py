"""Unit tests for preferences service functionality."""

from datetime import datetime
from uuid import uuid4

import pytest
from models import UserPreferences, UserPreferencesHistory
from services.preferences_service import (
    get_preference_change_summary,
    get_user_preferences_history,
    log_preference_changes,
    update_user_preferences_with_history,
)


@pytest.fixture
def db_session(isolated_test_setup):
    """Create a database session for testing."""
    setup = isolated_test_setup
    session = setup["session_local"]()
    try:
        yield session
    finally:
        session.close()


class TestLogPreferenceChanges:
    """Tests for log_preference_changes function."""

    def test_logs_changes_for_modified_preferences(self, db_session):
        """Test that changes are logged when preferences are modified."""
        # Setup
        user_id = "test-user-123"
        old_prefs = UserPreferences(
            id=str(uuid4()),
            user_id=user_id,
            tone="friendly",
            notifications_enabled=True,
            default_view="card",
        )

        new_data = {
            "tone": "coach",
            "notifications_enabled": False,
            # default_view stays the same - should not be logged
        }

        # Execute
        log_preference_changes(db_session, user_id, old_prefs, new_data)
        db_session.commit()  # Commit the changes to make them visible

        # Verify
        history_entries = (
            db_session.query(UserPreferencesHistory)
            .filter(UserPreferencesHistory.user_id == user_id)
            .all()
        )

        assert len(history_entries) == 2

        # Check tone change
        tone_entry = next(e for e in history_entries if e.preference_name == "tone")
        assert tone_entry.old_value == "friendly"
        assert tone_entry.new_value == "coach"
        assert tone_entry.user_id == user_id

        # Check notifications change
        notifications_entry = next(
            e for e in history_entries if e.preference_name == "notifications_enabled"
        )
        assert notifications_entry.old_value == "True"
        assert notifications_entry.new_value == "False"
        assert notifications_entry.user_id == user_id

    def test_no_logging_for_unchanged_preferences(self, db_session):
        """Test that no changes are logged when preferences remain the same."""
        # Setup
        user_id = "test-user-123"
        old_prefs = UserPreferences(
            id=str(uuid4()),
            user_id=user_id,
            tone="friendly",
            notifications_enabled=True,
        )

        new_data = {
            "tone": "friendly",  # Same value
            "notifications_enabled": True,  # Same value
        }

        # Execute
        log_preference_changes(db_session, user_id, old_prefs, new_data)

        # Verify
        history_entries = (
            db_session.query(UserPreferencesHistory)
            .filter(UserPreferencesHistory.user_id == user_id)
            .all()
        )

        assert len(history_entries) == 0

    def test_skips_system_fields(self, db_session):
        """Test that system fields like id, created_at are not logged."""
        # Setup
        user_id = "test-user-123"
        old_prefs = UserPreferences(id=str(uuid4()), user_id=user_id, tone="friendly")

        new_data = {
            "id": "new-id",  # Should be skipped
            "user_id": "new-user",  # Should be skipped
            "created_at": datetime.utcnow(),  # Should be skipped
            "updated_at": datetime.utcnow(),  # Should be skipped
            "tone": "coach",  # Should be logged
        }

        # Execute
        log_preference_changes(db_session, user_id, old_prefs, new_data)
        db_session.commit()  # Commit the changes to make them visible

        # Verify
        history_entries = (
            db_session.query(UserPreferencesHistory)
            .filter(UserPreferencesHistory.user_id == user_id)
            .all()
        )

        # Only tone change should be logged
        assert len(history_entries) == 1
        assert history_entries[0].preference_name == "tone"

    def test_handles_none_values(self, db_session):
        """Test that None values are handled properly."""
        # Setup
        user_id = "test-user-123"
        old_prefs = UserPreferences(
            id=str(uuid4()), user_id=user_id, notification_time=None
        )

        new_data = {
            "notification_time": "08:00:00",  # From None to value
        }

        # Execute
        log_preference_changes(db_session, user_id, old_prefs, new_data)
        db_session.commit()  # Commit the changes to make them visible

        # Verify
        history_entries = (
            db_session.query(UserPreferencesHistory)
            .filter(UserPreferencesHistory.user_id == user_id)
            .all()
        )

        assert len(history_entries) == 1
        assert history_entries[0].old_value is None
        assert history_entries[0].new_value == "08:00:00"


class TestUpdateUserPreferencesWithHistory:
    """Tests for update_user_preferences_with_history function."""

    def test_creates_new_preferences_without_history(self, db_session):
        """Test that creating new preferences doesn't generate history."""
        # Setup
        user_id = "new-user-123"
        update_data = {"tone": "coach", "notifications_enabled": True}

        # Execute
        result = update_user_preferences_with_history(db_session, user_id, update_data)

        # Verify preferences were created
        assert result.user_id == user_id
        assert result.tone == "coach"
        assert result.notifications_enabled is True

        # Verify no history was created for new preferences
        history_entries = (
            db_session.query(UserPreferencesHistory)
            .filter(UserPreferencesHistory.user_id == user_id)
            .all()
        )
        assert len(history_entries) == 0

    def test_updates_existing_preferences_with_history(self, db_session):
        """Test that updating existing preferences generates history."""
        # Setup - create existing preferences
        user_id = "existing-user-123"
        existing_prefs = UserPreferences(
            id=str(uuid4()),
            user_id=user_id,
            tone="friendly",
            notifications_enabled=False,
        )
        db_session.add(existing_prefs)
        db_session.commit()

        update_data = {
            "tone": "coach",  # Change this
            "notifications_enabled": True,  # Change this
            "default_view": "list",  # Add this new field
        }

        # Execute
        result = update_user_preferences_with_history(db_session, user_id, update_data)

        # Verify preferences were updated
        assert result.tone == "coach"
        assert result.notifications_enabled is True
        assert result.default_view == "list"

        # Verify history was created
        history_entries = (
            db_session.query(UserPreferencesHistory)
            .filter(UserPreferencesHistory.user_id == user_id)
            .all()
        )

        # Should have 3 entries (tone, notifications_enabled, default_view)
        # default_view goes from None to "list" so it should be logged
        assert len(history_entries) == 3

    def test_updates_updated_at_timestamp(self, db_session):
        """Test that updated_at timestamp is properly set."""
        # Setup
        user_id = "test-user-123"
        original_time = datetime(2023, 1, 1, 12, 0, 0)
        existing_prefs = UserPreferences(
            id=str(uuid4()), user_id=user_id, tone="friendly", updated_at=original_time
        )
        db_session.add(existing_prefs)
        db_session.commit()

        update_data = {"tone": "coach"}

        # Execute
        result = update_user_preferences_with_history(db_session, user_id, update_data)

        # Verify updated_at was changed
        assert result.updated_at > original_time


class TestGetUserPreferencesHistory:
    """Tests for get_user_preferences_history function."""

    def test_returns_history_ordered_by_date(self, db_session):
        """Test that history is returned in descending order by changed_at."""
        # Setup
        user_id = "test-user-123"

        # Create history entries with different timestamps
        entry1 = UserPreferencesHistory(
            id=str(uuid4()),
            user_id=user_id,
            preference_name="tone",
            old_value="friendly",
            new_value="coach",
            changed_at=datetime(2023, 1, 1, 12, 0, 0),
        )
        entry2 = UserPreferencesHistory(
            id=str(uuid4()),
            user_id=user_id,
            preference_name="notifications_enabled",
            old_value="False",
            new_value="True",
            changed_at=datetime(2023, 1, 2, 12, 0, 0),  # Later date
        )

        db_session.add_all([entry1, entry2])
        db_session.commit()

        # Execute
        result = get_user_preferences_history(db_session, user_id)

        # Verify
        assert len(result) == 2
        # Should be ordered by changed_at DESC, so entry2 (later date) comes first
        assert result[0].preference_name == "notifications_enabled"
        assert result[1].preference_name == "tone"

    def test_filters_by_preference_name(self, db_session):
        """Test filtering by specific preference name."""
        # Setup
        user_id = "test-user-123"

        entry1 = UserPreferencesHistory(
            id=str(uuid4()),
            user_id=user_id,
            preference_name="tone",
            old_value="friendly",
            new_value="coach",
        )
        entry2 = UserPreferencesHistory(
            id=str(uuid4()),
            user_id=user_id,
            preference_name="notifications_enabled",
            old_value="False",
            new_value="True",
        )

        db_session.add_all([entry1, entry2])
        db_session.commit()

        # Execute
        result = get_user_preferences_history(
            db_session, user_id, preference_name="tone"
        )

        # Verify
        assert len(result) == 1
        assert result[0].preference_name == "tone"

    def test_applies_limit(self, db_session):
        """Test that limit parameter works correctly."""
        # Setup
        user_id = "test-user-123"

        # Create 5 entries
        entries = []
        for i in range(5):
            entry = UserPreferencesHistory(
                id=str(uuid4()),
                user_id=user_id,
                preference_name=f"pref_{i}",
                old_value="old",
                new_value="new",
                changed_at=datetime(2023, 1, 1, 12, i, 0),  # Different minutes
            )
            entries.append(entry)

        db_session.add_all(entries)
        db_session.commit()

        # Execute
        result = get_user_preferences_history(db_session, user_id, limit=3)

        # Verify
        assert len(result) == 3

    def test_returns_empty_list_for_no_history(self, db_session):
        """Test that empty list is returned when no history exists."""
        # Execute
        result = get_user_preferences_history(db_session, "nonexistent-user")

        # Verify
        assert result == []


class TestGetPreferenceChangeSummary:
    """Tests for get_preference_change_summary function."""

    def test_calculates_correct_summary_stats(self, db_session):
        """Test that summary statistics are calculated correctly."""
        # Setup
        user_id = "test-user-123"
        base_time = datetime.utcnow()

        # Create history entries within the time window
        entries = [
            UserPreferencesHistory(
                id=str(uuid4()),
                user_id=user_id,
                preference_name="tone",
                old_value="friendly",
                new_value="coach",
                changed_at=base_time,
            ),
            UserPreferencesHistory(
                id=str(uuid4()),
                user_id=user_id,
                preference_name="tone",
                old_value="coach",
                new_value="professional",
                changed_at=base_time,
            ),
            UserPreferencesHistory(
                id=str(uuid4()),
                user_id=user_id,
                preference_name="notifications_enabled",
                old_value="False",
                new_value="True",
                changed_at=base_time,
            ),
        ]

        db_session.add_all(entries)
        db_session.commit()

        # Execute
        result = get_preference_change_summary(db_session, user_id, days_back=30)

        # Verify
        assert result["total_changes"] == 3
        assert result["days_analyzed"] == 30
        assert set(result["preferences_changed"]) == {"tone", "notifications_enabled"}
        assert result["change_counts"]["tone"] == 2
        assert result["change_counts"]["notifications_enabled"] == 1
        assert result["most_changed_preference"]["name"] == "tone"
        assert result["most_changed_preference"]["count"] == 2
        assert result["latest_change"]["preference_name"] in [
            "tone",
            "notifications_enabled",
        ]

    def test_returns_empty_summary_for_no_changes(self, db_session):
        """Test that empty summary is returned when no changes exist."""
        # Execute
        result = get_preference_change_summary(
            db_session, "nonexistent-user", days_back=30
        )

        # Verify
        assert result["total_changes"] == 0
        assert result["days_analyzed"] == 30
        assert result["preferences_changed"] == []
        assert result["most_changed_preference"] is None
        assert result["latest_change"] is None
