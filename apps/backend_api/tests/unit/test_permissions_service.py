"""
Simple tests for the Permission Service functionality.

This module tests core permission checking and sharing functionality.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.onboarding import AssistantProfile, AssistantPermission
from models.user import User
from services.permission_service import PermissionService, PermissionLevel


class TestBasicPermissions:
    """Test basic permission functionality."""

    def test_owner_permissions(self, isolated_test_setup):
        """Test that owner has all permissions."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        try:
            # Create user and assistant
            user = User(uid="owner_123", email="owner@example.com")
            session.add(user)
            session.commit()
            
            assistant = AssistantProfile(
                user_id=user.uid,
                owner_id=user.uid,
                name="Test Assistant",
                ai_model="gpt-3.5-turbo",
                language="en",
                style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
                version=1000
            )
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            
            # Test all permission levels
            for level in PermissionLevel:
                # Use sync version by calling the method directly without await
                has_permission = PermissionService.check_permission.__wrapped__(
                    PermissionService, user.uid, assistant.id, level, session
                )
                assert has_permission, f"Owner should have {level} permission"
                
        finally:
            session.close()

    def test_non_owner_no_permissions(self, isolated_test_setup):
        """Test that non-owners have no permissions by default."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        try:
            # Create owner and assistant
            owner = User(uid="owner_123", email="owner@example.com")
            session.add(owner)
            
            # Create non-owner
            non_owner = User(uid="user_456", email="user@example.com")
            session.add(non_owner)
            session.commit()
            
            assistant = AssistantProfile(
                user_id=owner.uid,
                owner_id=owner.uid,
                name="Test Assistant",
                ai_model="gpt-3.5-turbo",
                language="en",
                style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
                version=1000
            )
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            
            # Test that non-owner has no permissions
            for level in PermissionLevel:
                has_permission = PermissionService.check_permission.__wrapped__(
                    PermissionService, non_owner.uid, assistant.id, level, session
                )
                assert not has_permission, f"Non-owner should not have {level} permission"
                
        finally:
            session.close()

    def test_public_assistant_read_access(self, isolated_test_setup):
        """Test that public assistants grant read access to everyone."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        try:
            # Create owner and non-owner
            owner = User(uid="owner_123", email="owner@example.com")
            non_owner = User(uid="user_456", email="user@example.com")
            session.add_all([owner, non_owner])
            session.commit()
            
            # Create public assistant
            assistant = AssistantProfile(
                user_id=owner.uid,
                owner_id=owner.uid,
                name="Public Assistant",
                ai_model="gpt-3.5-turbo",
                language="en",
                style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
                is_public=True,
                version=1000
            )
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            
            # Test that non-owner has read access
            has_read = PermissionService.check_permission.__wrapped__(
                PermissionService, non_owner.uid, assistant.id, PermissionLevel.READ, session
            )
            assert has_read, "Should have read access to public assistant"
            
            # Test that non-owner doesn't have edit access
            has_edit = PermissionService.check_permission.__wrapped__(
                PermissionService, non_owner.uid, assistant.id, PermissionLevel.EDIT, session
            )
            assert not has_edit, "Should not have edit access to public assistant"
                
        finally:
            session.close()

    def test_sharing_workflow(self, isolated_test_setup):
        """Test complete sharing workflow."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        try:
            # Create users
            owner = User(uid="owner_123", email="owner@example.com")
            grantee = User(uid="grantee_456", email="grantee@example.com")
            session.add_all([owner, grantee])
            session.commit()
            
            # Create assistant
            assistant = AssistantProfile(
                user_id=owner.uid,
                owner_id=owner.uid,
                name="Shared Assistant",
                ai_model="gpt-3.5-turbo",
                language="en",
                style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
                version=1000
            )
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            
            # Initially grantee has no access
            has_permission = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.READ, session
            )
            assert not has_permission, "Should not have permission initially"
            
            # Share with EDIT permission
            PermissionService.share_assistant.__wrapped__(
                PermissionService,
                assistant_id=assistant.id,
                target_user_id=grantee.uid,
                permission_level=PermissionLevel.EDIT,
                granted_by=owner.uid,
                db=session
            )
            
            # Now grantee should have READ and EDIT permissions
            has_read = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.READ, session
            )
            has_edit = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.EDIT, session
            )
            has_admin = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.ADMIN, session
            )
            
            assert has_read, "Should have READ permission"
            assert has_edit, "Should have EDIT permission"
            assert not has_admin, "Should not have ADMIN permission"
            
            # Test revocation
            PermissionService.revoke_permission.__wrapped__(
                PermissionService,
                assistant_id=assistant.id,
                target_user_id=grantee.uid,
                revoked_by=owner.uid,
                db=session
            )
            
            # Permission should be revoked
            has_permission_after = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.READ, session
            )
            assert not has_permission_after, "Permission should be revoked"
                
        finally:
            session.close()

    def test_get_user_assistants(self, isolated_test_setup):
        """Test getting all assistants a user has access to."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        try:
            # Create users
            user1 = User(uid="user_1", email="user1@example.com")
            user2 = User(uid="user_2", email="user2@example.com")
            session.add_all([user1, user2])
            session.commit()
            
            # Create assistants
            owned_assistant = AssistantProfile(
                user_id=user1.uid,
                owner_id=user1.uid,
                name="Owned Assistant",
                ai_model="gpt-3.5-turbo",
                language="en",
                style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
                version=1000
            )
            
            public_assistant = AssistantProfile(
                user_id=user2.uid,
                owner_id=user2.uid,
                name="Public Assistant",
                ai_model="gpt-3.5-turbo",
                language="en",
                style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
                is_public=True,
                version=1000
            )
            
            session.add_all([owned_assistant, public_assistant])
            session.commit()
            
            # Get user1's assistants
            user1_assistants = PermissionService.get_user_assistants.__wrapped__(
                PermissionService, user1.uid, session
            )
            
            assistant_names = {a.name for a in user1_assistants}
            expected_names = {"Owned Assistant", "Public Assistant"}
            
            assert assistant_names == expected_names, f"Expected {expected_names}, got {assistant_names}"
                
        finally:
            session.close()

    def test_permission_hierarchy(self, isolated_test_setup):
        """Test that permission hierarchy works correctly."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        try:
            # Create users
            owner = User(uid="owner_123", email="owner@example.com")
            grantee = User(uid="grantee_456", email="grantee@example.com")
            session.add_all([owner, grantee])
            session.commit()
            
            # Create assistant
            assistant = AssistantProfile(
                user_id=owner.uid,
                owner_id=owner.uid,
                name="Test Assistant",
                ai_model="gpt-3.5-turbo",
                language="en",
                style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
                version=1000
            )
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            
            # Share with EDIT permission
            PermissionService.share_assistant.__wrapped__(
                PermissionService,
                assistant_id=assistant.id,
                target_user_id=grantee.uid,
                permission_level=PermissionLevel.EDIT,
                granted_by=owner.uid,
                db=session
            )
            
            # Test hierarchy: EDIT should include READ but not ADMIN
            has_read = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.READ, session
            )
            has_edit = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.EDIT, session
            )
            has_admin = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.ADMIN, session
            )
            has_owner = PermissionService.check_permission.__wrapped__(
                PermissionService, grantee.uid, assistant.id, PermissionLevel.OWNER, session
            )
            
            assert has_read, "EDIT permission should include READ"
            assert has_edit, "Should have EDIT permission"
            assert not has_admin, "EDIT permission should not include ADMIN"
            assert not has_owner, "EDIT permission should not include OWNER"
                
        finally:
            session.close()


class TestVersioning:
    """Test assistant versioning."""

    def test_version_update(self, isolated_test_setup):
        """Test that version is updated when assistant is modified."""
        setup = isolated_test_setup
        session = setup["session_local"]()
        
        try:
            user = User(uid="user_123", email="user@example.com")
            session.add(user)
            session.commit()
            
            assistant = AssistantProfile(
                user_id=user.uid,
                owner_id=user.uid,
                name="Test Assistant",
                ai_model="gpt-3.5-turbo",
                language="en",
                style={"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60},
                version=1000
            )
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            
            original_version = assistant.version
            
            # Update version
            assistant.update_version()
            session.commit()
            
            assert assistant.version > original_version, "Version should be updated"
            
            # Version should be based on current timestamp
            current_timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
            assert abs(assistant.version - current_timestamp_ms) < 1000, "Version should be timestamp-based"
                
        finally:
            session.close()