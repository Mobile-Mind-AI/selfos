"""
Assistant Permissions API Router

Handles permission-based assistant sharing and access control.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from dependencies import get_db, get_current_user
from models.onboarding import AssistantProfile, AssistantPermission
from services.permission_service import PermissionService, PermissionLevel
from schemas.assistant_schemas import (
    AssistantProfileOut,
    ShareAssistantRequest,
    ShareAssistantResponse,
    AssistantPermissionOut,
    AssistantVersionOut
)

router = APIRouter(tags=["assistant-permissions"])


@router.get("/assistants", response_model=List[AssistantProfileOut])
async def get_user_assistants(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all assistants user has access to (owned, shared, or public)."""
    
    assistants = await PermissionService.get_user_assistants(
        current_user["uid"], db
    )
    
    return [AssistantProfileOut.model_validate(assistant) for assistant in assistants]


@router.get("/assistants/{assistant_id}", response_model=AssistantProfileOut)
async def get_assistant(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific assistant (requires read permission)."""
    
    # Check read permission
    has_permission = await PermissionService.check_permission(
        current_user["uid"], assistant_id, PermissionLevel.READ, db
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this assistant"
        )
    
    assistant = db.query(AssistantProfile).filter(
        AssistantProfile.id == assistant_id
    ).first()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    return AssistantProfileOut.model_validate(assistant)


@router.put("/assistants/{assistant_id}", response_model=AssistantProfileOut)
async def update_assistant(
    assistant_id: str,
    update_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update assistant (requires edit permission)."""
    
    # Check edit permission
    has_permission = await PermissionService.check_permission(
        current_user["uid"], assistant_id, PermissionLevel.EDIT, db
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit this assistant"
        )
    
    assistant = db.query(AssistantProfile).filter(
        AssistantProfile.id == assistant_id
    ).first()
    
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(assistant, field):
            setattr(assistant, field, value)
    
    # Update version and timestamp
    assistant.update_version()
    assistant.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assistant)
    
    return AssistantProfileOut.model_validate(assistant)


@router.post("/assistants/{assistant_id}/share", response_model=ShareAssistantResponse)
async def share_assistant(
    assistant_id: str,
    share_request: ShareAssistantRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share assistant with another user (requires admin permission)."""
    
    try:
        await PermissionService.share_assistant(
            assistant_id=assistant_id,
            target_user_id=share_request.target_user_id,
            permission_level=PermissionLevel(share_request.permission_level),
            granted_by=current_user["uid"],
            db=db,
            expires_at=share_request.expires_at
        )
        
        return ShareAssistantResponse(
            success=True,
            message="Assistant shared successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share assistant: {str(e)}"
        )


@router.delete("/assistants/{assistant_id}/permissions/{user_id}")
async def revoke_permission(
    assistant_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke user's permission to assistant (requires admin permission)."""
    
    try:
        await PermissionService.revoke_permission(
            assistant_id=assistant_id,
            target_user_id=user_id,
            revoked_by=current_user["uid"],
            db=db
        )
        
        return {"message": "Permission revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke permission: {str(e)}"
        )


@router.get("/assistants/{assistant_id}/permissions", response_model=List[AssistantPermissionOut])
async def get_assistant_permissions(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all permissions for an assistant (requires admin permission)."""
    
    # Check admin permission
    has_permission = await PermissionService.check_permission(
        current_user["uid"], assistant_id, PermissionLevel.ADMIN, db
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view assistant permissions"
        )
    
    permissions = await PermissionService.get_assistant_permissions(
        assistant_id, db
    )
    
    return [AssistantPermissionOut(**perm) for perm in permissions]


@router.get("/assistants/versions", response_model=List[AssistantVersionOut])
async def get_assistant_versions(
    assistant_ids: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get version information for assistants (for sync purposes)."""
    
    if assistant_ids:
        # Get versions for specific assistants (check read permission for each)
        accessible_assistants = []
        
        for assistant_id in assistant_ids:
            has_permission = await PermissionService.check_permission(
                current_user["uid"], assistant_id, PermissionLevel.READ, db
            )
            
            if has_permission:
                assistant = db.query(AssistantProfile).filter(
                    AssistantProfile.id == assistant_id
                ).first()
                
                if assistant:
                    accessible_assistants.append(assistant)
    else:
        # Get versions for all accessible assistants
        accessible_assistants = await PermissionService.get_user_assistants(
            current_user["uid"], db
        )
    
    return [
        AssistantVersionOut(
            assistant_id=assistant.id,
            version=assistant.version,
            updated_at=assistant.updated_at
        )
        for assistant in accessible_assistants
    ]


@router.post("/permissions/cleanup")
async def cleanup_expired_permissions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up expired permissions (admin endpoint)."""
    
    # This could be restricted to admin users in the future
    count = await PermissionService.cleanup_expired_permissions(db)
    
    return {"message": f"Cleaned up {count} expired permissions"}


@router.get("/assistants/{assistant_id}/permission-level")
async def get_user_permission_level(
    assistant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's permission level for an assistant."""
    
    permission_level = await PermissionService.get_user_permission_level(
        current_user["uid"], assistant_id, db
    )
    
    return {
        "assistant_id": assistant_id,
        "permission_level": permission_level.value if permission_level else None,
        "has_access": permission_level is not None
    }