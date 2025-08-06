"""Life Areas API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from dependencies import get_current_user, get_db
from models.goals import LifeArea
from schemas import (
    LifeAreaCreate, 
    LifeAreaUpdate, 
    LifeAreaOut
)

router = APIRouter(tags=["life_areas"])


@router.get("/life-areas", response_model=List[LifeAreaOut])
def get_life_areas(
    include_system: bool = True,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all life areas for the current user (including system defaults if requested)."""
    if include_system:
        # Get both user-specific and system life areas
        life_areas = db.query(LifeArea).filter(
            or_(
                LifeArea.user_id == current_user["uid"],
                LifeArea.user_id == "system"
            )
        ).order_by(
            LifeArea.is_custom,  # System areas first
            LifeArea.weight.desc(),  # Higher weight first
            LifeArea.name
        ).all()
    else:
        # Get only user-specific life areas
        life_areas = db.query(LifeArea).filter(
            LifeArea.user_id == current_user["uid"]
        ).order_by(
            LifeArea.weight.desc(),  # Higher weight first
            LifeArea.name
        ).all()
    
    return life_areas


@router.get("/life-areas/{life_area_id}", response_model=LifeAreaOut)
def get_life_area(
    life_area_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific life area by ID."""
    life_area = db.query(LifeArea).filter(
        LifeArea.id == life_area_id,
        or_(
            LifeArea.user_id == current_user["uid"],
            LifeArea.user_id == "system"
        )
    ).first()
    
    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Life area not found"
        )
    
    return life_area


@router.post("/life-areas", response_model=LifeAreaOut, status_code=201)
def create_life_area(
    life_area: LifeAreaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new custom life area for the current user."""
    # Check if user already has a life area with the same name
    existing = db.query(LifeArea).filter(
        LifeArea.user_id == current_user["uid"],
        LifeArea.name == life_area.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Life area with this name already exists"
        )
    
    # Create new life area
    db_life_area = LifeArea(
        user_id=current_user["uid"],
        is_custom=True,  # User-created areas are always custom
        **life_area.dict()
    )
    
    db.add(db_life_area)
    db.commit()
    db.refresh(db_life_area)
    
    return db_life_area


@router.put("/life-areas/{life_area_id}", response_model=LifeAreaOut)
def update_life_area(
    life_area_id: int,
    life_area_update: LifeAreaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a custom life area."""
    # Get the life area
    life_area = db.query(LifeArea).filter(
        LifeArea.id == life_area_id,
        LifeArea.user_id == current_user["uid"]
    ).first()
    
    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Life area not found"
        )
    
    # Can only update custom life areas
    if not life_area.is_custom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update system life areas"
        )
    
    # Check for duplicate names if name is being updated
    update_data = life_area_update.dict(exclude_unset=True)
    if "name" in update_data:
        existing = db.query(LifeArea).filter(
            LifeArea.user_id == current_user["uid"],
            LifeArea.name == update_data["name"],
            LifeArea.id != life_area_id  # Exclude current life area
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Life area with this name already exists"
            )
    
    # Update fields
    for field, value in update_data.items():
        setattr(life_area, field, value)
    
    # Update version for sync
    life_area.version += 1
    
    db.commit()
    db.refresh(life_area)
    
    return life_area


@router.delete("/life-areas/{life_area_id}", status_code=204)
def delete_life_area(
    life_area_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a custom life area."""
    # Get the life area
    life_area = db.query(LifeArea).filter(
        LifeArea.id == life_area_id,
        LifeArea.user_id == current_user["uid"]
    ).first()
    
    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Life area not found"
        )
    
    # Can only delete custom life areas
    if not life_area.is_custom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system life areas"
        )
    
    # Check if there are any goals/tasks/projects associated
    from models.goals import Goal, Project, Task
    
    associated_items = []
    
    goals_count = db.query(Goal).filter(Goal.life_area_id == life_area_id).count()
    if goals_count > 0:
        associated_items.append(f"{goals_count} goal(s)")
    
    projects_count = db.query(Project).filter(Project.life_area_id == life_area_id).count()
    if projects_count > 0:
        associated_items.append(f"{projects_count} project(s)")
    
    tasks_count = db.query(Task).filter(Task.life_area_id == life_area_id).count()
    if tasks_count > 0:
        associated_items.append(f"{tasks_count} task(s)")
    
    if associated_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete life area with associated items: {', '.join(associated_items)}"
        )
    
    # Delete the life area
    db.delete(life_area)
    db.commit()
    
    # Return None for 204 status
    return None


@router.get("/life-areas/stats/summary")
def get_life_areas_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get life areas summary statistics."""
    life_areas = db.query(LifeArea).filter(
        or_(
            LifeArea.user_id == current_user["uid"],
            LifeArea.user_id == "system"
        )
    ).all()
    
    if not life_areas:
        return {
            "total_areas": 0,
            "total_weight": 0,
            "average_weight": 0,
            "custom_areas": 0,
            "system_areas": 0,
            "areas_by_weight": []
        }
    
    total_count = len(life_areas)
    total_weight = sum(area.weight or 0 for area in life_areas)
    custom_count = sum(1 for area in life_areas if area.is_custom)
    system_count = total_count - custom_count
    average_weight = total_weight / total_count if total_count > 0 else 0
    
    # Sort areas by weight descending for areas_by_weight
    areas_by_weight = sorted(life_areas, key=lambda x: x.weight or 0, reverse=True)
    areas_by_weight_data = [
        {
            "name": area.name, 
            "weight": area.weight or 0,
            "percentage": round(((area.weight or 0) / total_weight * 100), 1) if total_weight > 0 else 0
        } 
        for area in areas_by_weight
    ]
    
    return {
        "total_areas": total_count,
        "total_weight": total_weight,
        "average_weight": average_weight,
        "custom_areas": custom_count,
        "system_areas": system_count,
        "areas_by_weight": areas_by_weight_data
    }
