"""
Avatar management endpoints for custom avatar upload and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
import base64
import io
from PIL import Image
import uuid
from datetime import datetime

from dependencies import get_db, get_current_user
import models
from schemas.assistant_schemas import AssistantProfile

router = APIRouter(prefix="/api/avatars", tags=["avatars"])

# Maximum file size: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024

# Allowed content types
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg", 
    "image/png",
    "image/webp"
}

# Thumbnail size
THUMBNAIL_SIZE = (64, 64)


@router.post("/upload")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a custom avatar image.
    
    Returns:
        dict: Avatar ID and metadata
    """
    # Validate file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"
        )
    
    # Debug logging
    print(f"🔍 DEBUG: Received file - filename: {file.filename}, content_type: {file.content_type}, size: {len(file_content)}")
    
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        print(f"❌ DEBUG: Content type '{file.content_type}' not in allowed types: {ALLOWED_CONTENT_TYPES}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    try:
        # Open and validate image
        image = Image.open(io.BytesIO(file_content))
        width, height = image.size
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Create thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        # Convert images to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        image_data = img_byte_arr.getvalue()
        
        thumb_byte_arr = io.BytesIO()
        thumbnail.save(thumb_byte_arr, format='JPEG', quality=70)
        thumbnail_data = thumb_byte_arr.getvalue()
        
        # Create avatar record
        avatar_id = str(uuid.uuid4())
        db_avatar = models.AvatarImage(
            id=avatar_id,
            user_id=current_user["uid"],
            filename=file.filename or f"avatar_{avatar_id}.jpg",
            content_type="image/jpeg",  # We always save as JPEG
            size_bytes=len(image_data),
            storage_type="database",
            image_data=image_data,
            width=width,
            height=height,
            thumbnail_data=thumbnail_data,
            is_active=True,
            usage_count=0
        )
        
        db.add(db_avatar)
        db.commit()
        db.refresh(db_avatar)
        
        return {
            "avatar_id": avatar_id,
            "filename": db_avatar.filename,
            "width": width,
            "height": height,
            "size_bytes": len(image_data),
            "content_type": "image/jpeg",
            "created_at": db_avatar.created_at.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process image: {str(e)}"
        )


@router.get("/list")
def list_user_avatars(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """
    List all avatars for the current user.
    
    Args:
        include_inactive: Include deactivated avatars
        
    Returns:
        List of avatar metadata
    """
    query = db.query(models.AvatarImage).filter(
        models.AvatarImage.user_id == current_user["uid"]
    )
    
    if not include_inactive:
        query = query.filter(models.AvatarImage.is_active == True)
    
    avatars = query.order_by(models.AvatarImage.created_at.desc()).all()
    
    return [
        {
            "avatar_id": avatar.id,
            "filename": avatar.filename,
            "width": avatar.width,
            "height": avatar.height,
            "size_bytes": avatar.size_bytes,
            "content_type": avatar.content_type,
            "usage_count": avatar.usage_count,
            "is_active": avatar.is_active,
            "created_at": avatar.created_at.isoformat(),
            "last_used_at": avatar.last_used_at.isoformat() if avatar.last_used_at else None
        }
        for avatar in avatars
    ]


@router.get("/{avatar_id}/image")
def get_avatar_image(
    avatar_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    thumbnail: bool = False
):
    """
    Get avatar image data.
    
    Args:
        avatar_id: Avatar ID
        thumbnail: Return thumbnail instead of full image
        
    Returns:
        Image response
    """
    avatar = db.query(models.AvatarImage).filter(
        models.AvatarImage.id == avatar_id,
        models.AvatarImage.user_id == current_user["uid"],
        models.AvatarImage.is_active == True
    ).first()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # Update usage tracking
    avatar.usage_count += 1
    avatar.last_used_at = datetime.utcnow()
    db.commit()
    
    # Return image data
    image_data = avatar.thumbnail_data if thumbnail and avatar.thumbnail_data else avatar.image_data
    
    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image data not found"
        )
    
    return Response(
        content=image_data,
        media_type=avatar.content_type,
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "Content-Disposition": f"inline; filename={avatar.filename}"
        }
    )


@router.get("/{avatar_id}/base64")
def get_avatar_base64(
    avatar_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    thumbnail: bool = False
):
    """
    Get avatar image as base64 encoded string.
    
    Args:
        avatar_id: Avatar ID
        thumbnail: Return thumbnail instead of full image
        
    Returns:
        Base64 encoded image data
    """
    avatar = db.query(models.AvatarImage).filter(
        models.AvatarImage.id == avatar_id,
        models.AvatarImage.user_id == current_user["uid"],
        models.AvatarImage.is_active == True
    ).first()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # Update usage tracking
    avatar.usage_count += 1
    avatar.last_used_at = datetime.utcnow()
    db.commit()
    
    # Return base64 encoded image
    image_data = avatar.thumbnail_data if thumbnail and avatar.thumbnail_data else avatar.image_data
    
    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image data not found"
        )
    
    base64_data = base64.b64encode(image_data).decode('utf-8')
    
    return {
        "avatar_id": avatar_id,
        "base64_data": f"data:{avatar.content_type};base64,{base64_data}",
        "content_type": avatar.content_type,
        "width": avatar.width,
        "height": avatar.height,
        "is_thumbnail": thumbnail and avatar.thumbnail_data is not None
    }


@router.delete("/{avatar_id}")
def delete_avatar(
    avatar_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) an avatar.
    
    Args:
        avatar_id: Avatar ID to delete
        
    Returns:
        Success message
    """
    avatar = db.query(models.AvatarImage).filter(
        models.AvatarImage.id == avatar_id,
        models.AvatarImage.user_id == current_user["uid"]
    ).first()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    # Soft delete - mark as inactive
    avatar.is_active = False
    db.commit()
    
    return {"message": "Avatar deleted successfully", "avatar_id": avatar_id}


@router.post("/{avatar_id}/restore")
def restore_avatar(
    avatar_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restore a previously deleted avatar.
    
    Args:
        avatar_id: Avatar ID to restore
        
    Returns:
        Success message
    """
    avatar = db.query(models.AvatarImage).filter(
        models.AvatarImage.id == avatar_id,
        models.AvatarImage.user_id == current_user["uid"]
    ).first()
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    avatar.is_active = True
    db.commit()
    
    return {"message": "Avatar restored successfully", "avatar_id": avatar_id}