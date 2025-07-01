"""
Projects API Router

Handles CRUD operations for projects within the SelfOS system.
Projects serve as containers for multiple goals and tasks, enabling
hierarchical organization: Life Area → Project → Goal → Task.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, and_, or_, func
from typing import List, Optional
from datetime import datetime

from dependencies import get_db, get_current_user
from models import Project, Goal, Task, MediaAttachment, LifeArea
from schemas import (
    ProjectCreate, Project as ProjectSchema, ProjectOut,
    GoalOut, TaskOut, MediaAttachmentOut, LifeAreaOut
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    status: Optional[str] = Query(None, description="Filter by project status"),
    life_area_id: Optional[int] = Query(None, description="Filter by life area"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of projects to return"),
    offset: int = Query(0, ge=0, description="Number of projects to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List projects for the current user with optional filtering.
    
    Supports filtering by:
    - status: todo, in_progress, completed, paused
    - life_area_id: specific life area
    - priority: low, medium, high
    """
    query = db.query(Project).filter(Project.user_id == current_user["uid"])
    
    # Apply filters
    if status:
        query = query.filter(Project.status == status)
    if life_area_id:
        query = query.filter(Project.life_area_id == life_area_id)
    if priority:
        query = query.filter(Project.priority == priority)
    
    # Order by creation date (newest first)
    query = query.order_by(desc(Project.created_at))
    
    # Apply pagination
    projects = query.offset(offset).limit(limit).all()
    
    # Convert to ProjectOut with relationships
    result = []
    for project in projects:
        # Load related data
        goals = db.query(Goal).filter(Goal.project_id == project.id).all()
        tasks = db.query(Task).filter(Task.project_id == project.id).all()
        media = db.query(MediaAttachment).filter(MediaAttachment.project_id == project.id).all()
        life_area = db.query(LifeArea).filter(LifeArea.id == project.life_area_id).first() if project.life_area_id else None
        
        project_dict = ProjectSchema.from_orm(project).dict()
        project_dict["goals"] = [GoalOut.from_orm(goal).dict() for goal in goals]
        project_dict["tasks"] = [TaskOut.from_orm(task).dict() for task in tasks]
        project_dict["media"] = [MediaAttachmentOut.from_orm(m).dict() for m in media]
        project_dict["life_area"] = LifeAreaOut.from_orm(life_area).dict() if life_area else None
        
        result.append(ProjectOut(**project_dict))
    
    return result


@router.post("/", response_model=ProjectOut)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project for the current user.
    """
    # Validate life area exists if provided
    if project_data.life_area_id:
        life_area = db.query(LifeArea).filter(
            and_(
                LifeArea.id == project_data.life_area_id,
                LifeArea.user_id == current_user["uid"]
            )
        ).first()
        if not life_area:
            raise HTTPException(
                status_code=404, 
                detail="Life area not found"
            )
    
    # Create the project
    project = Project(
        **project_data.dict(),
        user_id=current_user["uid"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Return with relationships
    life_area = db.query(LifeArea).filter(LifeArea.id == project.life_area_id).first() if project.life_area_id else None
    
    project_dict = ProjectSchema.from_orm(project).dict()
    project_dict["goals"] = []
    project_dict["tasks"] = []
    project_dict["media"] = []
    project_dict["life_area"] = LifeAreaOut.from_orm(life_area).dict() if life_area else None
    
    return ProjectOut(**project_dict)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific project by ID.
    """
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.user_id == current_user["uid"]
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Load related data
    goals = db.query(Goal).filter(Goal.project_id == project.id).all()
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    media = db.query(MediaAttachment).filter(MediaAttachment.project_id == project.id).all()
    life_area = db.query(LifeArea).filter(LifeArea.id == project.life_area_id).first() if project.life_area_id else None
    
    project_dict = ProjectSchema.from_orm(project).dict()
    project_dict["goals"] = [GoalOut.from_orm(goal).dict() for goal in goals]
    project_dict["tasks"] = [TaskOut.from_orm(task).dict() for task in tasks]
    project_dict["media"] = [MediaAttachmentOut.from_orm(m).dict() for m in media]
    project_dict["life_area"] = LifeAreaOut.from_orm(life_area).dict() if life_area else None
    
    return ProjectOut(**project_dict)


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing project.
    """
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.user_id == current_user["uid"]
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate life area exists if provided
    if project_data.life_area_id:
        life_area = db.query(LifeArea).filter(
            and_(
                LifeArea.id == project_data.life_area_id,
                LifeArea.user_id == current_user["uid"]
            )
        ).first()
        if not life_area:
            raise HTTPException(
                status_code=404, 
                detail="Life area not found"
            )
    
    # Update project fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    # Return with relationships
    goals = db.query(Goal).filter(Goal.project_id == project.id).all()
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    media = db.query(MediaAttachment).filter(MediaAttachment.project_id == project.id).all()
    life_area = db.query(LifeArea).filter(LifeArea.id == project.life_area_id).first() if project.life_area_id else None
    
    project_dict = ProjectSchema.from_orm(project).dict()
    project_dict["goals"] = [GoalOut.from_orm(goal).dict() for goal in goals]
    project_dict["tasks"] = [TaskOut.from_orm(task).dict() for task in tasks]
    project_dict["media"] = [MediaAttachmentOut.from_orm(m).dict() for m in media]
    project_dict["life_area"] = LifeAreaOut.from_orm(life_area).dict() if life_area else None
    
    return ProjectOut(**project_dict)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project and all associated goals and tasks.
    
    Warning: This will also delete all goals and tasks within the project.
    """
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.user_id == current_user["uid"]
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # The cascade="all, delete-orphan" in the model relationships
    # will automatically delete associated goals and tasks
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/progress", response_model=dict)
async def get_project_progress(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed progress statistics for a project.
    """
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.user_id == current_user["uid"]
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Calculate progress statistics
    goals_query = db.query(Goal).filter(Goal.project_id == project_id)
    tasks_query = db.query(Task).filter(Task.project_id == project_id)
    
    total_goals = goals_query.count()
    completed_goals = goals_query.filter(Goal.status == "completed").count()
    
    total_tasks = tasks_query.count()
    completed_tasks = tasks_query.filter(Task.status == "completed").count()
    in_progress_tasks = tasks_query.filter(Task.status == "in_progress").count()
    
    # Calculate overall progress percentage
    if total_goals > 0:
        goals_progress = (completed_goals / total_goals) * 100
    else:
        goals_progress = 0
    
    if total_tasks > 0:
        tasks_progress = (completed_tasks / total_tasks) * 100
    else:
        tasks_progress = 0
    
    # Weighted average (goals 60%, tasks 40%)
    overall_progress = (goals_progress * 0.6) + (tasks_progress * 0.4)
    
    return {
        "project_id": project_id,
        "overall_progress": round(overall_progress, 2),
        "goals": {
            "total": total_goals,
            "completed": completed_goals,
            "progress": round(goals_progress, 2)
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "in_progress": in_progress_tasks,
            "progress": round(tasks_progress, 2)
        }
    }


@router.get("/{project_id}/timeline", response_model=List[dict])
async def get_project_timeline(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a timeline of events for a project (goals and tasks created/completed).
    """
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.user_id == current_user["uid"]
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    timeline_events = []
    
    # Add project creation
    timeline_events.append({
        "type": "project_created",
        "date": project.created_at,
        "title": f"Project '{project.title}' created",
        "description": project.description or "",
        "item_id": project.id
    })
    
    # Add goal events
    goals = db.query(Goal).filter(Goal.project_id == project_id).all()
    for goal in goals:
        timeline_events.append({
            "type": "goal_created",
            "date": goal.created_at,
            "title": f"Goal '{goal.title}' created",
            "description": goal.description or "",
            "item_id": goal.id
        })
    
    # Add task events
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    for task in tasks:
        timeline_events.append({
            "type": "task_created",
            "date": task.created_at,
            "title": f"Task '{task.title}' created",
            "description": task.description or "",
            "item_id": task.id
        })
        
        # Add completion events for completed tasks
        if task.status == "completed":
            timeline_events.append({
                "type": "task_completed",
                "date": task.updated_at,  # Using updated_at as completion date
                "title": f"Task '{task.title}' completed",
                "description": "",
                "item_id": task.id
            })
    
    # Sort by date (newest first)
    timeline_events.sort(key=lambda x: x["date"], reverse=True)
    
    return timeline_events