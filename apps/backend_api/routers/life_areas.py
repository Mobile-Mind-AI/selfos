from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas
from dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/life-areas", response_model=schemas.LifeArea, status_code=201)
def create_life_area(
    life_area: schemas.LifeAreaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new life area for the current user"""
    # Check if life area with same name already exists for this user
    existing = db.query(models.LifeArea).filter(
        models.LifeArea.user_id == current_user["uid"],
        models.LifeArea.name == life_area.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Life area with name '{life_area.name}' already exists"
        )
    
    db_life_area = models.LifeArea(
        user_id=current_user["uid"],
        name=life_area.name,
        weight=life_area.weight,
        icon=life_area.icon,
        color=life_area.color,
        description=life_area.description,
    )
    db.add(db_life_area)
    db.commit()
    db.refresh(db_life_area)
    return db_life_area

@router.get("/life-areas", response_model=List[schemas.LifeArea])
def list_life_areas(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all life areas for the current user, ordered by weight descending"""
    return db.query(models.LifeArea).filter(
        models.LifeArea.user_id == current_user["uid"]
    ).order_by(models.LifeArea.weight.desc()).all()

@router.get("/life-areas/{life_area_id}", response_model=schemas.LifeArea)
def get_life_area(
    life_area_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific life area by ID"""
    life_area = db.query(models.LifeArea).filter(
        models.LifeArea.id == life_area_id,
        models.LifeArea.user_id == current_user["uid"]
    ).first()
    
    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Life area not found"
        )
    return life_area

@router.put("/life-areas/{life_area_id}", response_model=schemas.LifeArea)
def update_life_area(
    life_area_id: int,
    life_area_update: schemas.LifeAreaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a specific life area"""
    life_area = db.query(models.LifeArea).filter(
        models.LifeArea.id == life_area_id,
        models.LifeArea.user_id == current_user["uid"]
    ).first()
    
    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Life area not found"
        )
    
    # Check for name conflicts if name is being updated
    if life_area_update.name and life_area_update.name != life_area.name:
        existing = db.query(models.LifeArea).filter(
            models.LifeArea.user_id == current_user["uid"],
            models.LifeArea.name == life_area_update.name,
            models.LifeArea.id != life_area_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Life area with name '{life_area_update.name}' already exists"
            )
    
    # Update only provided fields
    update_data = life_area_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(life_area, field, value)
    
    life_area.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(life_area)
    return life_area

@router.delete("/life-areas/{life_area_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_life_area(
    life_area_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific life area"""
    life_area = db.query(models.LifeArea).filter(
        models.LifeArea.id == life_area_id,
        models.LifeArea.user_id == current_user["uid"]
    ).first()
    
    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Life area not found"
        )
    
    db.delete(life_area)
    db.commit()
    return None

@router.get("/life-areas/stats/summary")
def get_life_areas_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get summary statistics for user's life areas"""
    life_areas = db.query(models.LifeArea).filter(
        models.LifeArea.user_id == current_user["uid"]
    ).all()
    
    total_weight = sum(area.weight for area in life_areas)
    
    return {
        "total_areas": len(life_areas),
        "total_weight": total_weight,
        "average_weight": total_weight / len(life_areas) if life_areas else 0,
        "areas_by_weight": [
            {
                "name": area.name,
                "weight": area.weight,
                "percentage": (area.weight / total_weight * 100) if total_weight > 0 else 0
            }
            for area in sorted(life_areas, key=lambda x: x.weight, reverse=True)
        ]
    }