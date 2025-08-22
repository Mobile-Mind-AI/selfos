"""Service for managing user preferences and tracking changes."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from models import UserPreferences, UserPreferencesHistory
from sqlalchemy.orm import Session


def log_preference_changes(
    db: Session, user_id: str, old_prefs: UserPreferences, new_data: dict[str, Any]
) -> None:
    """
    Compare old and new preferences and log changes to the history table.

    Args:
        db: Database session
        user_id: User ID
        old_prefs: Current preferences object from database
        new_data: New preference values (only changed fields)
    """
    for key, new_value in new_data.items():
        # Skip non-preference fields like 'updated_at'
        if key in ("id", "user_id", "created_at", "updated_at"):
            continue

        old_value = getattr(old_prefs, key, None)

        # Only log if value actually changed
        if old_value != new_value:
            history_entry = UserPreferencesHistory(
                id=str(uuid4()),
                user_id=user_id,
                preference_name=key,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
            )
            db.add(history_entry)


def update_user_preferences_with_history(
    db: Session, user_id: str, update_data: dict[str, Any]
) -> UserPreferences:
    """
    Update user preferences and automatically log changes to history.

    Args:
        db: Database session
        user_id: User ID
        update_data: Dictionary of preference updates (only changed values)

    Returns:
        Updated UserPreferences object

    Raises:
        ValueError: If user preferences not found and can't be created
    """
    # Get current preferences
    current_prefs = (
        db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    )

    if not current_prefs:
        # Create new preferences - no history needed for initial creation
        current_prefs = UserPreferences(user_id=user_id, **update_data)
        db.add(current_prefs)
    else:
        # Log changes BEFORE applying them
        log_preference_changes(db, user_id, current_prefs, update_data)

        # Apply the updates
        for key, value in update_data.items():
            if hasattr(current_prefs, key):
                setattr(current_prefs, key, value)

        current_prefs.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_prefs)
    return current_prefs


def get_user_preferences_history(
    db: Session,
    user_id: str,
    limit: int | None = None,
    preference_name: str | None = None,
) -> list[UserPreferencesHistory]:
    """
    Get preferences change history for a user.

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of records to return
        preference_name: Filter by specific preference name

    Returns:
        List of UserPreferencesHistory objects ordered by changed_at DESC
    """
    query = db.query(UserPreferencesHistory).filter(
        UserPreferencesHistory.user_id == user_id
    )

    if preference_name:
        query = query.filter(UserPreferencesHistory.preference_name == preference_name)

    query = query.order_by(UserPreferencesHistory.changed_at.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


def get_preference_change_summary(
    db: Session, user_id: str, days_back: int = 30
) -> dict[str, Any]:
    """
    Get summary of preference changes for a user in the last N days.

    Args:
        db: Database session
        user_id: User ID
        days_back: Number of days to look back

    Returns:
        Dictionary with change statistics
    """
    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    history_records = (
        db.query(UserPreferencesHistory)
        .filter(
            UserPreferencesHistory.user_id == user_id,
            UserPreferencesHistory.changed_at >= cutoff_date,
        )
        .all()
    )

    if not history_records:
        return {
            "total_changes": 0,
            "days_analyzed": days_back,
            "preferences_changed": [],
            "change_counts": {},
            "most_changed_preference": None,
            "latest_change": None,
        }

    # Count changes by preference name
    change_counts = {}
    for record in history_records:
        pref_name = record.preference_name
        change_counts[pref_name] = change_counts.get(pref_name, 0) + 1

    most_changed = (
        max(change_counts.items(), key=lambda x: x[1]) if change_counts else None
    )

    return {
        "total_changes": len(history_records),
        "days_analyzed": days_back,
        "preferences_changed": list(change_counts.keys()),
        "change_counts": change_counts,
        "most_changed_preference": (
            {"name": most_changed[0], "count": most_changed[1]}
            if most_changed
            else None
        ),
        "latest_change": (
            {
                "preference_name": history_records[0].preference_name,
                "old_value": history_records[0].old_value,
                "new_value": history_records[0].new_value,
                "changed_at": history_records[0].changed_at,
            }
            if history_records
            else None
        ),
    }


class PreferencesService:
    """Service class for managing user preferences."""

    @staticmethod
    def log_preference_changes(
        db: Session, user_id: str, old_prefs: UserPreferences, new_data: dict[str, Any]
    ) -> None:
        return log_preference_changes(db, user_id, old_prefs, new_data)

    @staticmethod
    def update_user_preferences_with_history(
        db: Session, user_id: str, update_data: dict[str, Any]
    ) -> UserPreferences:
        return update_user_preferences_with_history(db, user_id, update_data)

    @staticmethod
    def get_user_preferences_history(
        db: Session,
        user_id: str,
        limit: int | None = None,
        preference_name: str | None = None,
    ) -> list[UserPreferencesHistory]:
        return get_user_preferences_history(db, user_id, limit, preference_name)

    @staticmethod
    def get_preference_change_summary(
        db: Session, user_id: str, days_back: int = 30
    ) -> dict[str, Any]:
        return get_preference_change_summary(db, user_id, days_back)


# Export service instance
preferences_service = PreferencesService
