"""
Assistants API endpoints for managing multiple assistant profiles.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models import AssistantPermission, AssistantProfile, PermissionLevel
from schemas.assistant_schemas import (
    AssistantProfileCreate,
    AssistantProfileOut,
    AssistantProfileUpdate,
)
from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.get("/", response_model=List[AssistantProfileOut])
def get_user_assistants(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all assistants owned by, shared with, or public for the current user."""
    # Get assistants owned by user OR shared with user OR public
    assistants = (
        db.query(AssistantProfile)
        .filter(
            or_(
                AssistantProfile.owner_id == current_user["uid"],
                AssistantProfile.permissions.any(
                    AssistantPermission.user_id == current_user["uid"]
                ),
                AssistantProfile.is_public == True,
            )
        )
        .all()
    )

    return assistants


@router.get("/{assistant_id}", response_model=AssistantProfileOut)
def get_assistant(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific assistant by ID."""
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )

    # Check if user has access
    has_access = (
        assistant.owner_id == current_user["uid"]
        or assistant.is_public
        or db.query(AssistantPermission)
        .filter(
            AssistantPermission.assistant_id == assistant_id,
            AssistantPermission.user_id == current_user["uid"],
        )
        .first()
        is not None
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return assistant


@router.post("/", response_model=AssistantProfileOut, status_code=201)
def create_assistant(
    assistant_data: AssistantProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new assistant profile."""
    assistant = AssistantProfile(
        user_id=current_user["uid"],
        owner_id=current_user["uid"],  # Set owner_id too
        **assistant_data.model_dump(),
    )

    db.add(assistant)
    db.commit()
    db.refresh(assistant)

    return assistant


@router.put("/{assistant_id}", response_model=AssistantProfileOut)
def update_assistant(
    assistant_id: str,
    assistant_update: AssistantProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an assistant profile."""
    # First check if assistant exists
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )

    # Then check if user has permission to update
    can_edit = assistant.owner_id == current_user["uid"]
    if not can_edit:
        # Check if user has edit permission
        permission = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == current_user["uid"],
                AssistantPermission.can_edit == True,
            )
            .first()
        )
        can_edit = permission is not None

    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    # Update fields
    for field, value in assistant_update.model_dump(exclude_unset=True).items():
        setattr(assistant, field, value)

    assistant.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(assistant)

    return assistant


@router.post("/{assistant_id}/share", status_code=200)
def share_assistant(
    assistant_id: str,
    share_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Share an assistant with another user."""
    # Check if user owns the assistant or has share permission
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )

    # Check if user can share (owner or has share permission)
    can_share = assistant.owner_id == current_user["uid"]
    if not can_share:
        permission = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == current_user["uid"],
                AssistantPermission.can_share == True,
            )
            .first()
        )
        can_share = permission is not None

    if not can_share:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to share this assistant",
        )

    # Create permission for target user
    target_user_id = share_data.get("target_user_id")
    permission_level_str = share_data.get("permission_level", "viewer").lower()

    # Map common permission names to enum values
    level_mapping = {
        "edit": "EDITOR",
        "editor": "EDITOR",
        "admin": "ADMIN",
        "viewer": "VIEWER",
        "view": "VIEWER",
        "owner": "OWNER",
    }
    permission_level = level_mapping.get(permission_level_str, "VIEWER")

    # Check if permission already exists
    existing = (
        db.query(AssistantPermission)
        .filter(
            AssistantPermission.assistant_id == assistant_id,
            AssistantPermission.user_id == target_user_id,
        )
        .first()
    )

    if existing:
        # Update existing permission
        existing.permission_level = PermissionLevel[permission_level]
        existing.can_edit = permission_level in ["EDITOR", "ADMIN", "OWNER"]
        existing.can_share = permission_level in ["ADMIN", "OWNER"]
        existing.can_delete = permission_level in ["ADMIN", "OWNER"]
        existing.updated_at = datetime.utcnow()
    else:
        # Create new permission
        new_permission = AssistantPermission(
            assistant_id=assistant_id,
            user_id=target_user_id,
            permission_level=PermissionLevel[permission_level],
            can_edit=permission_level in ["EDITOR", "ADMIN", "OWNER"],
            can_share=permission_level in ["ADMIN", "OWNER"],
            can_delete=permission_level in ["ADMIN", "OWNER"],
        )
        db.add(new_permission)

    db.commit()
    return {"message": "Assistant shared successfully"}


@router.delete("/{assistant_id}/permissions/{user_id}", status_code=204)
def revoke_permission(
    assistant_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke a user's permission to access an assistant."""
    # Check if current user owns the assistant
    assistant = (
        db.query(AssistantProfile)
        .filter(
            AssistantProfile.id == assistant_id,
            AssistantProfile.owner_id == current_user["uid"],
        )
        .first()
    )

    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found or you don't own it",
        )

    # Find and delete the permission
    permission = (
        db.query(AssistantPermission)
        .filter(
            AssistantPermission.assistant_id == assistant_id,
            AssistantPermission.user_id == user_id,
        )
        .first()
    )

    if permission:
        db.delete(permission)
        db.commit()

    return None


@router.get("/{assistant_id}/permissions", response_model=List[Dict[str, Any]])
def get_assistant_permissions(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all permissions for an assistant."""
    # Check if user owns the assistant or has admin permission
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )

    # Check if user can view permissions (owner or admin)
    can_view = assistant.owner_id == current_user["uid"]
    if not can_view:
        permission = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == current_user["uid"],
                AssistantPermission.permission_level == PermissionLevel.ADMIN,
            )
            .first()
        )
        can_view = permission is not None

    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view permissions",
        )

    # Get all permissions
    permissions = (
        db.query(AssistantPermission)
        .filter(AssistantPermission.assistant_id == assistant_id)
        .all()
    )

    return [
        {
            "user_id": p.user_id,
            "permission_level": p.permission_level.value,
            "can_edit": p.can_edit,
            "can_share": p.can_share,
            "can_delete": p.can_delete,
            "created_at": p.created_at,
            "expires_at": p.expires_at,
        }
        for p in permissions
    ]


@router.get("/{assistant_id}/permission-level", response_model=Dict[str, str])
def get_user_permission_level(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's permission level for an assistant."""
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )

    # Check if owner
    if assistant.owner_id == current_user["uid"]:
        return {"permission_level": "owner"}

    # Check if shared
    permission = (
        db.query(AssistantPermission)
        .filter(
            AssistantPermission.assistant_id == assistant_id,
            AssistantPermission.user_id == current_user["uid"],
        )
        .first()
    )

    if permission:
        return {"permission_level": permission.permission_level.value}

    # Check if public
    if assistant.is_public:
        return {"permission_level": "viewer"}

    return {"permission_level": "none"}


@router.delete("/{assistant_id}", status_code=204)
def delete_assistant(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an assistant profile."""
    assistant = (
        db.query(AssistantProfile)
        .filter(
            AssistantProfile.id == assistant_id,
            AssistantProfile.owner_id
            == current_user["uid"],  # Check owner_id not user_id
        )
        .first()
    )

    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found or access denied",
        )

    db.delete(assistant)
    db.commit()

    return None


@router.get("/versions/", response_model=List[dict])
def get_assistant_versions(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get version history for assistants."""
    # Placeholder for version history
    return []


@router.delete(
    "/{assistant_id}/permissions/{user_id}", response_model=dict, status_code=200
)
def revoke_permission(
    assistant_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke a user's permission for an assistant."""
    # Check if the current user is the owner or admin
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    # Check permission to revoke
    if assistant.owner_id != current_user["uid"]:
        # Check if current user is admin
        current_perm = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == current_user["uid"],
                AssistantPermission.permission_level.in_(
                    [PermissionLevel.OWNER, PermissionLevel.ADMIN]
                ),
            )
            .first()
        )

        if not current_perm:
            raise HTTPException(
                status_code=403, detail="No permission to revoke permissions"
            )

    # Can't revoke owner's permission
    if user_id == assistant.owner_id:
        raise HTTPException(status_code=400, detail="Cannot revoke owner's permission")

    # Delete the permission
    deleted = (
        db.query(AssistantPermission)
        .filter(
            AssistantPermission.assistant_id == assistant_id,
            AssistantPermission.user_id == user_id,
        )
        .delete()
    )

    db.commit()

    if deleted:
        return {"message": f"Permission revoked successfully for user {user_id}"}
    else:
        return {"message": "No permission found to revoke"}


@router.get("/{assistant_id}/permissions", response_model=List[dict])
def get_assistant_permissions(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all permissions for an assistant."""
    # Check if user has access to view permissions
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    # Check if user is owner or has permission
    if assistant.owner_id != current_user["uid"]:
        perm = (
            db.query(AssistantPermission)
            .filter(
                AssistantPermission.assistant_id == assistant_id,
                AssistantPermission.user_id == current_user["uid"],
            )
            .first()
        )

        if not perm:
            raise HTTPException(
                status_code=403, detail="No permission to view permissions"
            )

    # Get all permissions
    permissions = (
        db.query(AssistantPermission)
        .filter(AssistantPermission.assistant_id == assistant_id)
        .all()
    )

    # Include owner in the list
    result = [
        {
            "user_id": assistant.owner_id,
            "permission_level": "owner",
            "granted_at": assistant.created_at,
            "is_owner": True,
        }
    ]

    for perm in permissions:
        result.append(
            {
                "user_id": perm.user_id,
                "permission_level": perm.permission_level.value,
                "granted_at": perm.granted_at,
                "expires_at": perm.expires_at,
                "is_owner": False,
            }
        )

    return result


@router.get("/{assistant_id}/versions", response_model=List[dict])
def get_assistant_versions(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get version history for an assistant."""
    # Check access
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    # Check permissions
    if not _check_assistant_permission(
        db, assistant_id, current_user["uid"], PermissionLevel.VIEWER
    ):
        raise HTTPException(status_code=403, detail="No permission to view assistant")

    # For now, return current version as the only version
    return [
        {
            "version": assistant.version or 1,
            "created_at": assistant.created_at,
            "updated_at": assistant.updated_at,
            "is_current": True,
            "description": f"Version {assistant.version or 1}",
        }
    ]


@router.get("/{assistant_id}/permission-level", response_model=dict)
def get_user_permission_level(
    assistant_id: str,
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a user's permission level for an assistant."""
    # Use current user if no user_id specified
    check_user_id = user_id or current_user["uid"]

    # Get assistant
    assistant = (
        db.query(AssistantProfile).filter(AssistantProfile.id == assistant_id).first()
    )

    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    # Check if owner
    if check_user_id == assistant.owner_id:
        return {
            "user_id": check_user_id,
            "permission_level": "owner",
            "can_view": True,
            "can_edit": True,
            "can_share": True,
            "can_delete": True,
        }

    # Check permissions
    perm = (
        db.query(AssistantPermission)
        .filter(
            AssistantPermission.assistant_id == assistant_id,
            AssistantPermission.user_id == check_user_id,
        )
        .first()
    )

    if not perm:
        return {
            "user_id": check_user_id,
            "permission_level": None,
            "can_view": assistant.is_public,
            "can_edit": False,
            "can_share": False,
            "can_delete": False,
        }

    level = perm.permission_level.value
    return {
        "user_id": check_user_id,
        "permission_level": level,
        "can_view": True,
        "can_edit": level in ["owner", "admin", "editor"],
        "can_share": level in ["owner", "admin"],
        "can_delete": level == "owner",
    }


@router.post("/permissions/cleanup/", response_model=dict)
def cleanup_expired_permissions(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Clean up expired permissions."""
    from datetime import datetime

    # Delete expired permissions
    expired_count = (
        db.query(AssistantPermission)
        .filter(
            AssistantPermission.expires_at != None,
            AssistantPermission.expires_at < datetime.utcnow(),
        )
        .delete()
    )

    db.commit()
    return {"cleaned": expired_count}
