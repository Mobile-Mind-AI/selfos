"""Life Areas API endpoints."""

from typing import List, Optional

from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models.goals import Goal
from models.life_areas import LifeArea
from models.projects import Project
from models.tasks import Task
from schemas import LifeAreaCreate, LifeAreaOut, LifeAreaUpdate
from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter(tags=["life_areas"])


@router.get("/life-areas", response_model=List[LifeAreaOut])
def get_life_areas(
    include_system: bool = True,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all life areas for the current user (including system defaults if requested)."""
    if include_system:
        # Get both user-specific and system life areas
        life_areas = (
            db.query(LifeArea)
            .filter(
                or_(
                    LifeArea.user_id == current_user["uid"],
                    LifeArea.user_id == "system",
                )
            )
            .order_by(LifeArea.weight.desc(), LifeArea.name)  # Higher weight first
            .all()
        )
    else:
        # Get only user-specific life areas
        life_areas = (
            db.query(LifeArea)
            .filter(LifeArea.user_id == current_user["uid"])
            .order_by(LifeArea.weight.desc(), LifeArea.name)  # Higher weight first
            .all()
        )

    return life_areas


@router.get("/life-areas/{life_area_id}", response_model=LifeAreaOut)
def get_life_area(
    life_area_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific life area by ID."""
    life_area = (
        db.query(LifeArea)
        .filter(
            LifeArea.id == life_area_id,
            or_(LifeArea.user_id == current_user["uid"], LifeArea.user_id == "system"),
        )
        .first()
    )

    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Life area not found"
        )

    return life_area


@router.post("/life-areas", response_model=LifeAreaOut, status_code=201)
def create_life_area(
    life_area: LifeAreaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new custom life area for the current user."""
    # Check if user already has a life area with the same name
    existing = (
        db.query(LifeArea)
        .filter(
            LifeArea.user_id == current_user["uid"], LifeArea.name == life_area.name
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Life area with this name already exists",
        )

    # Create new life area
    db_life_area = LifeArea(user_id=current_user["uid"], **life_area.model_dump())

    db.add(db_life_area)
    db.commit()
    db.refresh(db_life_area)

    return db_life_area


@router.put("/life-areas/{life_area_id}", response_model=LifeAreaOut)
def update_life_area(
    life_area_id: int,
    life_area_update: LifeAreaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a custom life area."""
    # Get the life area
    life_area = (
        db.query(LifeArea)
        .filter(LifeArea.id == life_area_id, LifeArea.user_id == current_user["uid"])
        .first()
    )

    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Life area not found"
        )

    # Can only update user's own life areas
    # System life areas are already filtered out by user_id check

    # Check for duplicate names if name is being updated
    update_data = life_area_update.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = (
            db.query(LifeArea)
            .filter(
                LifeArea.user_id == current_user["uid"],
                LifeArea.name == update_data["name"],
                LifeArea.id != life_area_id,  # Exclude current life area
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Life area with this name already exists",
            )

    # Update fields
    for field, value in update_data.items():
        setattr(life_area, field, value)

    db.commit()
    db.refresh(life_area)

    return life_area


@router.delete("/life-areas/{life_area_id}", status_code=204)
def delete_life_area(
    life_area_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a custom life area."""
    # Get the life area
    life_area = (
        db.query(LifeArea)
        .filter(LifeArea.id == life_area_id, LifeArea.user_id == current_user["uid"])
        .first()
    )

    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Life area not found"
        )

    # Can only delete user's own life areas
    # System life areas are already filtered out by user_id check

    # Check if there are any goals/tasks/projects associated

    associated_items = []

    goals_count = db.query(Goal).filter(Goal.life_area_id == life_area_id).count()
    if goals_count > 0:
        associated_items.append(f"{goals_count} goal(s)")

    projects_count = (
        db.query(Project).filter(Project.life_area_id == life_area_id).count()
    )
    if projects_count > 0:
        associated_items.append(f"{projects_count} project(s)")

    tasks_count = db.query(Task).filter(Task.life_area_id == life_area_id).count()
    if tasks_count > 0:
        associated_items.append(f"{tasks_count} task(s)")

    if associated_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete life area with associated items: {', '.join(associated_items)}",
        )

    # Delete the life area
    db.delete(life_area)
    db.commit()

    # Return None for 204 status
    return None


@router.get("/life-areas/stats/summary")
def get_life_areas_summary(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get life areas summary statistics."""
    life_areas = (
        db.query(LifeArea)
        .filter(
            or_(LifeArea.user_id == current_user["uid"], LifeArea.user_id == "system")
        )
        .all()
    )

    if not life_areas:
        return {
            "total_areas": 0,
            "total_weight": 0,
            "average_weight": 0,
            "custom_areas": 0,
            "system_areas": 0,
            "areas_by_weight": [],
        }

    total_count = len(life_areas)
    total_weight = sum(area.weight or 0 for area in life_areas)
    custom_count = sum(1 for area in life_areas if area.user_id != "system")
    system_count = sum(1 for area in life_areas if area.user_id == "system")
    average_weight = total_weight / total_count if total_count > 0 else 0

    # Sort areas by weight descending for areas_by_weight
    areas_by_weight = sorted(life_areas, key=lambda x: x.weight or 0, reverse=True)
    areas_by_weight_data = [
        {
            "name": area.name,
            "weight": area.weight or 0,
            "percentage": (
                round(((area.weight or 0) / total_weight * 100), 1)
                if total_weight > 0
                else 0
            ),
        }
        for area in areas_by_weight
    ]

    return {
        "total_areas": total_count,
        "total_weight": total_weight,
        "average_weight": average_weight,
        "custom_areas": custom_count,
        "system_areas": system_count,
        "areas_by_weight": areas_by_weight_data,
    }
