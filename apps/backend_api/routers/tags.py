"""API endpoints for tag management."""

import logging
from typing import Any, Dict, List, Optional

from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas import Tag, TagCreate, TagOut, TagUpdate
from services.tag_service import TagService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("/", response_model=Tag, status_code=201)
async def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new tag."""
    try:
        tag_service = TagService(db, current_user)
        tag = tag_service.create_tag(tag_data)
        return tag
    except ValueError as e:
        logger.warning(f"Tag creation failed for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tag for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[TagOut])
async def get_tags(
    include_usage_count: bool = Query(
        False, description="Include usage count for each tag"
    ),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get all tags for the current user."""
    try:
        tag_service = TagService(db, current_user)
        return tag_service.get_tags(include_usage_count=include_usage_count)
    except Exception as e:
        logger.error(f"Error fetching tags for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=List[TagOut])
async def search_tags(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Search tags by name."""
    try:
        tag_service = TagService(db, current_user)
        return tag_service.search_tags(q, limit)
    except Exception as e:
        logger.error(f"Error searching tags for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_tag_statistics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get tag usage statistics."""
    try:
        tag_service = TagService(db, current_user)
        return tag_service.get_tag_statistics()
    except Exception as e:
        logger.error(
            f"Error fetching tag statistics for user {current_user['uid']}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tag_id}", response_model=TagOut)
async def get_tag(
    tag_id: int,
    include_usage_count: bool = Query(False, description="Include usage count"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a specific tag by ID."""
    try:
        tag_service = TagService(db, current_user)
        tag = tag_service.get_tag_by_id(tag_id, include_usage_count=include_usage_count)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        return tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tag {tag_id} for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{tag_id}", response_model=Tag)
async def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update an existing tag."""
    try:
        tag_service = TagService(db, current_user)
        tag = tag_service.update_tag(tag_id, tag_update)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        return tag
    except ValueError as e:
        logger.warning(f"Tag update failed for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tag {tag_id} for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete a tag and all its associations."""
    try:
        tag_service = TagService(db, current_user)
        deleted = tag_service.delete_tag(tag_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Tag not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id} for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tag_id}/entities", response_model=Dict[str, List[Dict]])
async def get_entities_by_tag(
    tag_id: int,
    entity_types: Optional[List[str]] = Query(
        None, description="Filter by entity types"
    ),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get all entities associated with a specific tag."""
    try:
        tag_service = TagService(db, current_user)
        entities = tag_service.get_entities_by_tag(tag_id, entity_types)
        return entities
    except Exception as e:
        logger.error(
            f"Error fetching entities for tag {tag_id} for user {current_user['uid']}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
