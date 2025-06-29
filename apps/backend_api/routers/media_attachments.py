from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas
from dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/media-attachments", response_model=schemas.MediaAttachment, status_code=201)
def create_media_attachment(
    attachment: schemas.MediaAttachmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new media attachment for the current user"""
    # Validate that either goal_id or task_id is provided (or both can be None for standalone)
    if attachment.goal_id is not None:
        # Verify goal exists and belongs to user
        goal = db.query(models.Goal).filter(
            models.Goal.id == attachment.goal_id,
            models.Goal.user_id == current_user["uid"]
        ).first()
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
    
    if attachment.task_id is not None:
        # Verify task exists and belongs to user
        task = db.query(models.Task).filter(
            models.Task.id == attachment.task_id,
            models.Task.user_id == current_user["uid"]
        ).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
    
    db_attachment = models.MediaAttachment(
        user_id=current_user["uid"],
        goal_id=attachment.goal_id,
        task_id=attachment.task_id,
        filename=attachment.filename,
        original_filename=attachment.original_filename,
        file_path=attachment.file_path,
        file_size=attachment.file_size,
        mime_type=attachment.mime_type,
        file_type=attachment.file_type,
        title=attachment.title,
        description=attachment.description,
        duration=attachment.duration,
        width=attachment.width,
        height=attachment.height,
    )
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment

@router.get("/media-attachments", response_model=List[schemas.MediaAttachment])
def list_media_attachments(
    goal_id: Optional[int] = None,
    task_id: Optional[int] = None,
    file_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get media attachments for the current user with optional filtering"""
    query = db.query(models.MediaAttachment).filter(
        models.MediaAttachment.user_id == current_user["uid"]
    )
    
    if goal_id is not None:
        query = query.filter(models.MediaAttachment.goal_id == goal_id)
    
    if task_id is not None:
        query = query.filter(models.MediaAttachment.task_id == task_id)
    
    if file_type is not None:
        query = query.filter(models.MediaAttachment.file_type == file_type)
    
    return query.order_by(models.MediaAttachment.created_at.desc()).all()

@router.get("/media-attachments/{attachment_id}", response_model=schemas.MediaAttachment)
def get_media_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific media attachment by ID"""
    attachment = db.query(models.MediaAttachment).filter(
        models.MediaAttachment.id == attachment_id,
        models.MediaAttachment.user_id == current_user["uid"]
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media attachment not found"
        )
    
    return attachment

@router.put("/media-attachments/{attachment_id}", response_model=schemas.MediaAttachment)
def update_media_attachment(
    attachment_id: int,
    attachment_update: schemas.MediaAttachmentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a media attachment's metadata (title, description, associations)"""
    db_attachment = db.query(models.MediaAttachment).filter(
        models.MediaAttachment.id == attachment_id,
        models.MediaAttachment.user_id == current_user["uid"]
    ).first()
    
    if not db_attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media attachment not found"
        )
    
    # Validate goal_id if provided
    if attachment_update.goal_id is not None:
        goal = db.query(models.Goal).filter(
            models.Goal.id == attachment_update.goal_id,
            models.Goal.user_id == current_user["uid"]
        ).first()
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
    
    # Validate task_id if provided
    if attachment_update.task_id is not None:
        task = db.query(models.Task).filter(
            models.Task.id == attachment_update.task_id,
            models.Task.user_id == current_user["uid"]
        ).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
    
    # Update only provided fields
    if attachment_update.title is not None:
        db_attachment.title = attachment_update.title
    if attachment_update.description is not None:
        db_attachment.description = attachment_update.description
    if attachment_update.goal_id is not None:
        db_attachment.goal_id = attachment_update.goal_id
    if attachment_update.task_id is not None:
        db_attachment.task_id = attachment_update.task_id
    
    db_attachment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_attachment)
    return db_attachment

@router.delete("/media-attachments/{attachment_id}")
def delete_media_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a media attachment (note: this doesn't delete the actual file)"""
    db_attachment = db.query(models.MediaAttachment).filter(
        models.MediaAttachment.id == attachment_id,
        models.MediaAttachment.user_id == current_user["uid"]
    ).first()
    
    if not db_attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media attachment not found"
        )
    
    db.delete(db_attachment)
    db.commit()
    return {"detail": "Media attachment deleted successfully"}

@router.get("/media-attachments/stats/summary")
def get_media_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get media attachment statistics for the current user"""
    total_attachments = db.query(models.MediaAttachment).filter(
        models.MediaAttachment.user_id == current_user["uid"]
    ).count()
    
    # Count by file type
    from sqlalchemy import func
    file_type_counts = db.query(
        models.MediaAttachment.file_type,
        func.count(models.MediaAttachment.id).label('count'),
        func.sum(models.MediaAttachment.file_size).label('total_size')
    ).filter(
        models.MediaAttachment.user_id == current_user["uid"]
    ).group_by(models.MediaAttachment.file_type).all()
    
    # Total storage used
    total_size = db.query(func.sum(models.MediaAttachment.file_size)).filter(
        models.MediaAttachment.user_id == current_user["uid"]
    ).scalar() or 0
    
    return {
        "total_attachments": total_attachments,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "by_file_type": [
            {
                "file_type": row.file_type,
                "count": row.count,
                "total_size_bytes": row.total_size or 0,
                "total_size_mb": round((row.total_size or 0) / (1024 * 1024), 2)
            }
            for row in file_type_counts
        ]
    }