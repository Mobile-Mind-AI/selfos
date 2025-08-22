"""
Permission Service for Assistant Sharing System
"""

from datetime import datetime
from enum import Enum

from fastapi import HTTPException
from models.onboarding import AssistantPermission, AssistantProfile
from sqlalchemy.orm import Session


class PermissionLevel(str, Enum):
    """Permission levels in hierarchy order."""

    READ = "read"  # Can view and use assistant
    EDIT = "edit"  # Can modify assistant settings
    ADMIN = "admin"  # Can share with others
    OWNER = "owner"  # Full control, can delete


class PermissionService:
    """Service for managing assistant permissions and sharing."""

    # Permission hierarchy for comparison
    _HIERARCHY = {
        PermissionLevel.READ: 1,
        PermissionLevel.EDIT: 2,
        PermissionLevel.ADMIN: 3,
        PermissionLevel.OWNER: 4,
    }

    @classmethod
    async def check_permission(
        cls,
        user_id: str,
        assistant_id: str,
        required_level: PermissionLevel,
        db: Session,
    ) -> bool:
        """
        Check if user has required permission level for assistant.

        Args:
            user_id: ID of the user to check
            assistant_id: ID of the assistant
            required_level: Minimum permission level required
            db: Database session

        Returns:
            bool: True if user has sufficient permission
        """

        # Get assistant
        assistant = (
            db.query(AssistantProfile)
            .filter(AssistantProfile.id == assistant_id)
            .first()
        )

        if not assistant:
            return False

        # Check if user is owner
        if assistant.owner_id == user_id:
            return True  # Owner has all permissions

        # Check if assistant is public (read-only access)
        if assistant.is_public and required_level == PermissionLevel.READ:
            return True

        # Check explicit permissions
        permission = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == user_id,
                (AssistantPermission.expires_at.is_(None))
                | (AssistantPermission.expires_at > datetime.utcnow()),
            )
            .first()
        )

        if not permission:
            return False

        # Check permission hierarchy
        user_level = cls._HIERARCHY.get(PermissionLevel(permission.permission_level), 0)
        required_level_value = cls._HIERARCHY.get(required_level, 0)

        return user_level >= required_level_value

    @classmethod
    async def get_user_assistants(
        cls, user_id: str, db: Session
    ) -> list[AssistantProfile]:
        """
        Get all assistants user has access to.

        Args:
            user_id: ID of the user
            db: Database session

        Returns:
            List of AssistantProfile objects user can access
        """

        # Direct ownership
        owned = (
            db.query(AssistantProfile)
            .filter(AssistantProfile.owner_id == user_id)
            .all()
        )

        # Shared assistants (with valid permissions)
        shared_assistant_ids = (
            db.query(AssistantPermission.assistant_id)
            .filter(
                AssistantPermission.user_id == user_id,
                (AssistantPermission.expires_at.is_(None))
                | (AssistantPermission.expires_at > datetime.utcnow()),
            )
            .subquery()
        )

        shared = (
            db.query(AssistantProfile)
            .filter(AssistantProfile.id.in_(shared_assistant_ids))
            .all()
        )

        # Public assistants (read-only) - exclude owned to avoid duplicates
        public = (
            db.query(AssistantProfile)
            .filter(
                AssistantProfile.is_public, AssistantProfile.owner_id != user_id
            )
            .all()
        )

        # Combine and return unique assistants
        all_assistants = owned + shared + public
        seen_ids = set()
        unique_assistants = []

        for assistant in all_assistants:
            if assistant.id not in seen_ids:
                seen_ids.add(assistant.id)
                unique_assistants.append(assistant)

        return unique_assistants

    @classmethod
    async def share_assistant(
        cls,
        assistant_id: str,
        target_user_id: str,
        permission_level: PermissionLevel,
        granted_by: str,
        db: Session,
        expires_at: datetime | None = None,
    ) -> None:
        """
        Share assistant with another user.

        Args:
            assistant_id: ID of assistant to share
            target_user_id: ID of user to share with
            permission_level: Permission level to grant
            granted_by: ID of user granting permission
            db: Database session
            expires_at: Optional expiration date

        Raises:
            HTTPException: If granter lacks permission or other error
        """

        # Check if granter has admin/owner permission
        can_share = await cls.check_permission(
            granted_by, assistant_id, PermissionLevel.ADMIN, db
        )

        if not can_share:
            raise HTTPException(
                status_code=403, detail="Insufficient permissions to share assistant"
            )

        # Prevent granting higher permission than granter has
        granter_permission = await cls.get_user_permission_level(
            granted_by, assistant_id, db
        )

        if cls._HIERARCHY.get(permission_level, 0) > cls._HIERARCHY.get(
            granter_permission, 0
        ):
            raise HTTPException(
                status_code=403, detail="Cannot grant higher permission than you have"
            )

        # Create or update permission
        existing_permission = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == target_user_id,
            )
            .first()
        )

        if existing_permission:
            # Update existing permission
            existing_permission.permission_level = permission_level.value
            existing_permission.granted_by = granted_by
            existing_permission.granted_at = datetime.utcnow()
            existing_permission.expires_at = expires_at
        else:
            # Create new permission
            new_permission = AssistantPermission(
                assistant_id=assistant_id,
                user_id=target_user_id,
                permission_level=permission_level.value,
                granted_by=granted_by,
                expires_at=expires_at,
            )
            db.add(new_permission)

        db.commit()

    @classmethod
    async def revoke_permission(
        cls, assistant_id: str, target_user_id: str, revoked_by: str, db: Session
    ) -> None:
        """
        Revoke user's permission to assistant.

        Args:
            assistant_id: ID of assistant
            target_user_id: ID of user to revoke permission from
            revoked_by: ID of user revoking permission
            db: Database session

        Raises:
            HTTPException: If revoker lacks permission
        """

        # Check if revoker has admin/owner permission
        can_revoke = await cls.check_permission(
            revoked_by, assistant_id, PermissionLevel.ADMIN, db
        )

        if not can_revoke:
            raise HTTPException(
                status_code=403, detail="Insufficient permissions to revoke access"
            )

        # Find and delete permission
        permission = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == target_user_id,
            )
            .first()
        )

        if permission:
            db.delete(permission)
            db.commit()

    @classmethod
    async def get_user_permission_level(
        cls, user_id: str, assistant_id: str, db: Session
    ) -> PermissionLevel | None:
        """
        Get user's permission level for an assistant.

        Args:
            user_id: ID of the user
            assistant_id: ID of the assistant
            db: Database session

        Returns:
            PermissionLevel or None if no permission
        """

        # Check if user is owner
        assistant = (
            db.query(AssistantProfile)
            .filter(AssistantProfile.id == assistant_id)
            .first()
        )

        if assistant and assistant.owner_id == user_id:
            return PermissionLevel.OWNER

        # Check explicit permissions
        permission = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == user_id,
                (AssistantPermission.expires_at.is_(None))
                | (AssistantPermission.expires_at > datetime.utcnow()),
            )
            .first()
        )

        if permission:
            return PermissionLevel(permission.permission_level)

        # Check public access
        if assistant and assistant.is_public:
            return PermissionLevel.READ

        return None

    @classmethod
    async def get_assistant_permissions(
        cls, assistant_id: str, db: Session
    ) -> list[dict]:
        """
        Get all permissions for an assistant.

        Args:
            assistant_id: ID of the assistant
            db: Database session

        Returns:
            List of permission dictionaries
        """

        permissions = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                (AssistantPermission.expires_at.is_(None))
                | (AssistantPermission.expires_at > datetime.utcnow()),
            )
            .all()
        )

        return [
            {
                "user_id": perm.user_id,
                "permission_level": perm.permission_level,
                "granted_by": perm.granted_by,
                "granted_at": perm.granted_at,
                "expires_at": perm.expires_at,
            }
            for perm in permissions
        ]

    @classmethod
    async def cleanup_expired_permissions(cls, db: Session) -> int:
        """
        Clean up expired permissions.

        Args:
            db: Database session

        Returns:
            Number of permissions cleaned up
        """

        expired_permissions = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.expires_at.isnot(None),
                AssistantPermission.expires_at < datetime.utcnow(),
            )
            .all()
        )

        count = len(expired_permissions)

        for permission in expired_permissions:
            db.delete(permission)

        db.commit()

        return count
