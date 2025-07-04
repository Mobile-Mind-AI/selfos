"""
Tests for the Assistant Permissions System.

This module tests the permission-based sharing system for assistants,
including permission checking, sharing, and CRUD operations.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.onboarding import AssistantProfile, AssistantPermission
from models.user import User
from services.permission_service import PermissionService, PermissionLevel


class TestPermissionService:
    """Test the PermissionService functionality."""

    @pytest.fixture
    def sample_users(self, isolated_test_setup):
        """Create sample users for testing."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        users = []
        for i in range(3):
            user = User(
                uid=f"user_{i}",
                email=f"user{i}@example.com"
            )
            session.add(user)
            users.append(user)
        
        session.commit()
        for user in users:
            session.refresh(user)
        
        try:
            yield users
        finally:
            session.close()

    @pytest.fixture
    def sample_assistant(self, isolated_test_setup, sample_users):
        """Create a sample assistant profile owned by user_0."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        assistant = AssistantProfile(
            user_id=sample_users[0].uid,
            owner_id=sample_users[0].uid,
            name="Test Assistant",
            description="A test assistant",
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
        session.add(assistant)
        session.commit()
        session.refresh(assistant)
        
        try:
            yield assistant
        finally:
            session.close()

    @pytest.fixture
    def db_session(self, isolated_test_setup):
        """Provide database session for tests."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        try:
            yield session
        finally:
            session.close()

    @pytest.mark.asyncio
    async def test_owner_has_all_permissions(self, db_session: Session, sample_assistant, sample_users):
        """Test that the owner has all permission levels."""
        owner_id = sample_users[0].uid
        assistant_id = sample_assistant.id

        # Test all permission levels
        for level in PermissionLevel:
            has_permission = await PermissionService.check_permission(
                owner_id, assistant_id, level, db_session
            )
            assert has_permission, f"Owner should have {level} permission"

    @pytest.mark.asyncio
    async def test_non_owner_no_permissions(self, db_session: Session, sample_assistant, sample_users):
        """Test that non-owners have no permissions by default."""
        non_owner_id = sample_users[1].uid
        assistant_id = sample_assistant.id

        for level in PermissionLevel:
            has_permission = await PermissionService.check_permission(
                non_owner_id, assistant_id, level, db_session
            )
            assert not has_permission, f"Non-owner should not have {level} permission"

    @pytest.mark.asyncio
    async def test_public_assistant_read_access(self, db_session: Session, sample_assistant, sample_users):
        """Test that public assistants grant read access to everyone."""
        # Make assistant public
        sample_assistant.is_public = True
        db.commit()

        non_owner_id = sample_users[1].uid
        assistant_id = sample_assistant.id

        # Should have read access
        has_read = await PermissionService.check_permission(
            non_owner_id, assistant_id, PermissionLevel.READ, db
        )
        assert has_read, "Should have read access to public assistant"

        # Should not have write access
        has_edit = await PermissionService.check_permission(
            non_owner_id, assistant_id, PermissionLevel.EDIT, db
        )
        assert not has_edit, "Should not have edit access to public assistant"

    @pytest.mark.asyncio
    async def test_permission_hierarchy(self, db: Session, sample_assistant, sample_users):
        """Test that permission hierarchy works correctly."""
        # Grant EDIT permission to user_1
        owner_id = sample_users[0].uid
        grantee_id = sample_users[1].uid
        assistant_id = sample_assistant.id

        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=grantee_id,
            permission_level=PermissionLevel.EDIT,
            granted_by=owner_id,
            db=db
        )

        # Should have READ permission (lower in hierarchy)
        has_read = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.READ, db
        )
        assert has_read, "EDIT permission should include READ"

        # Should have EDIT permission
        has_edit = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.EDIT, db
        )
        assert has_edit, "Should have EDIT permission"

        # Should NOT have ADMIN permission (higher in hierarchy)
        has_admin = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.ADMIN, db
        )
        assert not has_admin, "EDIT permission should not include ADMIN"

    @pytest.mark.asyncio
    async def test_expired_permissions_ignored(self, db: Session, sample_assistant, sample_users):
        """Test that expired permissions are ignored."""
        owner_id = sample_users[0].uid
        grantee_id = sample_users[1].uid
        assistant_id = sample_assistant.id

        # Grant permission that expires in the past
        expired_time = datetime.utcnow() - timedelta(hours=1)
        
        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=grantee_id,
            permission_level=PermissionLevel.EDIT,
            granted_by=owner_id,
            db=db,
            expires_at=expired_time
        )

        # Should not have permission
        has_permission = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.READ, db
        )
        assert not has_permission, "Expired permissions should be ignored"

    @pytest.mark.asyncio
    async def test_share_assistant_requires_admin(self, db: Session, sample_assistant, sample_users):
        """Test that sharing requires admin permission."""
        # Grant EDIT permission to user_1
        owner_id = sample_users[0].uid
        editor_id = sample_users[1].uid
        target_id = sample_users[2].uid
        assistant_id = sample_assistant.id

        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=editor_id,
            permission_level=PermissionLevel.EDIT,
            granted_by=owner_id,
            db=db
        )

        # user_1 (with EDIT) should NOT be able to share with user_2
        with pytest.raises(HTTPException) as exc_info:
            await PermissionService.share_assistant(
                assistant_id=assistant_id,
                target_user_id=target_id,
                permission_level=PermissionLevel.READ,
                granted_by=editor_id,
                db=db
            )
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_cannot_grant_higher_permission(self, db: Session, sample_assistant, sample_users):
        """Test that users cannot grant permissions higher than their own."""
        # Grant EDIT permission to user_1
        owner_id = sample_users[0].uid
        admin_id = sample_users[1].uid
        target_id = sample_users[2].uid
        assistant_id = sample_assistant.id

        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=admin_id,
            permission_level=PermissionLevel.ADMIN,
            granted_by=owner_id,
            db=db
        )

        # user_1 (with ADMIN) should NOT be able to grant OWNER permission
        with pytest.raises(HTTPException) as exc_info:
            await PermissionService.share_assistant(
                assistant_id=assistant_id,
                target_user_id=target_id,
                permission_level=PermissionLevel.OWNER,
                granted_by=admin_id,
                db=db
            )
        
        assert exc_info.value.status_code == 403
        assert "Cannot grant higher permission" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_revoke_permission(self, db: Session, sample_assistant, sample_users):
        """Test permission revocation."""
        owner_id = sample_users[0].uid
        grantee_id = sample_users[1].uid
        assistant_id = sample_assistant.id

        # Grant permission
        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=grantee_id,
            permission_level=PermissionLevel.EDIT,
            granted_by=owner_id,
            db=db
        )

        # Verify permission exists
        has_permission = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.EDIT, db
        )
        assert has_permission, "Permission should exist before revocation"

        # Revoke permission
        await PermissionService.revoke_permission(
            assistant_id=assistant_id,
            target_user_id=grantee_id,
            revoked_by=owner_id,
            db=db
        )

        # Verify permission is revoked
        has_permission = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.EDIT, db
        )
        assert not has_permission, "Permission should be revoked"

    @pytest.mark.asyncio
    async def test_get_user_assistants(self, db: Session, sample_users):
        """Test getting all assistants a user has access to."""
        user1_id = sample_users[0].uid
        user2_id = sample_users[1].uid

        # Create assistants for different scenarios
        owned_assistant = AssistantProfile(
            user_id=user1_id,
            owner_id=user1_id,
            name="Owned Assistant",
            ai_model="gpt-3.5-turbo",
            language="en",
            style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
            version=1000
        )
        
        public_assistant = AssistantProfile(
            user_id=user2_id,
            owner_id=user2_id,
            name="Public Assistant",
            ai_model="gpt-3.5-turbo",
            language="en",
            style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
            is_public=True,
            version=1000
        )
        
        shared_assistant = AssistantProfile(
            user_id=user2_id,
            owner_id=user2_id,
            name="Shared Assistant",
            ai_model="gpt-3.5-turbo",
            language="en",
            style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
            version=1000
        )

        db.add_all([owned_assistant, public_assistant, shared_assistant])
        db.commit()
        db.refresh(owned_assistant)
        db.refresh(public_assistant)
        db.refresh(shared_assistant)

        # Share the shared_assistant with user1
        await PermissionService.share_assistant(
            assistant_id=shared_assistant.id,
            target_user_id=user1_id,
            permission_level=PermissionLevel.EDIT,
            granted_by=user2_id,
            db=db
        )

        # Get all assistants for user1
        user1_assistants = await PermissionService.get_user_assistants(user1_id, db)
        
        # Should have access to: owned, public, and shared assistants
        assistant_names = {a.name for a in user1_assistants}
        expected_names = {"Owned Assistant", "Public Assistant", "Shared Assistant"}
        
        assert assistant_names == expected_names, f"Expected {expected_names}, got {assistant_names}"

    @pytest.mark.asyncio
    async def test_update_existing_permission(self, db: Session, sample_assistant, sample_users):
        """Test that sharing with an existing user updates the permission."""
        owner_id = sample_users[0].uid
        grantee_id = sample_users[1].uid
        assistant_id = sample_assistant.id

        # Grant READ permission
        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=grantee_id,
            permission_level=PermissionLevel.READ,
            granted_by=owner_id,
            db=db
        )

        # Verify READ permission
        has_read = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.READ, db
        )
        assert has_read, "Should have READ permission"

        has_edit = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.EDIT, db
        )
        assert not has_edit, "Should not have EDIT permission yet"

        # Upgrade to EDIT permission
        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=grantee_id,
            permission_level=PermissionLevel.EDIT,
            granted_by=owner_id,
            db=db
        )

        # Verify EDIT permission
        has_edit = await PermissionService.check_permission(
            grantee_id, assistant_id, PermissionLevel.EDIT, db
        )
        assert has_edit, "Should now have EDIT permission"

        # Verify there's only one permission record
        permissions = db.query(AssistantPermission).filter(
            AssistantPermission.assistant_id == assistant_id,
            AssistantPermission.user_id == grantee_id
        ).all()
        
        assert len(permissions) == 1, "Should have only one permission record per user"

    @pytest.mark.asyncio
    async def test_get_user_permission_level(self, db: Session, sample_assistant, sample_users):
        """Test getting a user's specific permission level."""
        owner_id = sample_users[0].uid
        grantee_id = sample_users[1].uid
        assistant_id = sample_assistant.id

        # Owner should have OWNER level
        owner_level = await PermissionService.get_user_permission_level(
            owner_id, assistant_id, db
        )
        assert owner_level == PermissionLevel.OWNER

        # Grantee should have no permission initially
        grantee_level = await PermissionService.get_user_permission_level(
            grantee_id, assistant_id, db
        )
        assert grantee_level is None

        # Grant EDIT permission
        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=grantee_id,
            permission_level=PermissionLevel.EDIT,
            granted_by=owner_id,
            db=db
        )

        # Grantee should now have EDIT level
        grantee_level = await PermissionService.get_user_permission_level(
            grantee_id, assistant_id, db
        )
        assert grantee_level == PermissionLevel.EDIT

    @pytest.mark.asyncio
    async def test_cleanup_expired_permissions(self, db: Session, sample_assistant, sample_users):
        """Test cleanup of expired permissions."""
        owner_id = sample_users[0].uid
        grantee_id = sample_users[1].uid
        assistant_id = sample_assistant.id

        # Create expired permission
        expired_time = datetime.utcnow() - timedelta(hours=1)
        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=grantee_id,
            permission_level=PermissionLevel.EDIT,
            granted_by=owner_id,
            db=db,
            expires_at=expired_time
        )

        # Create non-expired permission
        future_time = datetime.utcnow() + timedelta(hours=1)
        grantee2_id = sample_users[2].uid
        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=grantee2_id,
            permission_level=PermissionLevel.READ,
            granted_by=owner_id,
            db=db,
            expires_at=future_time
        )

        # Verify both permissions exist
        all_permissions = db.query(AssistantPermission).filter(
            AssistantPermission.assistant_id == assistant_id
        ).all()
        assert len(all_permissions) == 2

        # Run cleanup
        cleaned_count = await PermissionService.cleanup_expired_permissions(db)
        assert cleaned_count == 1, "Should clean up 1 expired permission"

        # Verify only non-expired permission remains
        remaining_permissions = db.query(AssistantPermission).filter(
            AssistantPermission.assistant_id == assistant_id
        ).all()
        assert len(remaining_permissions) == 1
        assert remaining_permissions[0].user_id == grantee2_id

    @pytest.mark.asyncio
    async def test_nonexistent_assistant(self, db: Session, sample_users):
        """Test permission check on non-existent assistant."""
        user_id = sample_users[0].uid
        fake_assistant_id = "non-existent-id"

        has_permission = await PermissionService.check_permission(
            user_id, fake_assistant_id, PermissionLevel.READ, db
        )
        assert not has_permission, "Should not have permission on non-existent assistant"


class TestAssistantVersioning:
    """Test assistant versioning for sync purposes."""

    @pytest.fixture
    def sample_user(self, db: Session):
        """Create a sample user."""
        user = User(uid="test_user", email="test@example.com")
        db.add(user)
        db.commit()
        return user

    @pytest.fixture
    def sample_assistant(self, db: Session, sample_user):
        """Create a sample assistant."""
        assistant = AssistantProfile(
            user_id=sample_user.uid,
            owner_id=sample_user.uid,
            name="Test Assistant",
            ai_model="gpt-3.5-turbo",
            language="en",
            style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
            version=1000
        )
        db.add(assistant)
        db.commit()
        db.refresh(assistant)
        return assistant

    def test_version_update(self, db: Session, sample_assistant):
        """Test that version is updated when assistant is modified."""
        original_version = sample_assistant.version
        
        # Simulate update
        sample_assistant.update_version()
        db.commit()
        
        assert sample_assistant.version > original_version, "Version should be updated"

    def test_version_is_timestamp(self, db: Session, sample_assistant):
        """Test that version is based on timestamp."""
        import time
        
        # Update version and check it's close to current timestamp
        sample_assistant.update_version()
        current_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
        
        # Allow for small timing differences (within 1 second)
        assert abs(sample_assistant.version - current_timestamp_ms) < 1000