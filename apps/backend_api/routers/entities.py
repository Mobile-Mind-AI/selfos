"""
Entity management API endpoints for knowledge graph.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from db import get_db
from dependencies import get_current_user
from models import (
    EntityType, Entity, EntityRelationship,
    GoalEntity, ProjectEntity, TaskEntity,
    Goal, Project, Task
)
from schemas import EntityTypeSchema, EntitySchema, EntityRelationshipSchema

router = APIRouter(prefix="/entities", tags=["entities"])

# ========================= Entity Types =========================

@router.get("/types", response_model=List[EntityTypeSchema])
def get_entity_types(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all available entity types for the user."""
    types = db.query(EntityType).filter(
        or_(
            EntityType.user_id == current_user["uid"],
            EntityType.is_system == True
        )
    ).all()
    return types


@router.post("/types", response_model=EntityTypeSchema)
def create_entity_type(
    entity_type: EntityTypeSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a custom entity type."""
    # Check if type already exists
    existing = db.query(EntityType).filter(
        EntityType.name == entity_type.name,
        EntityType.user_id == current_user["uid"]
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Entity type already exists")
    
    db_entity_type = EntityType(
        user_id=current_user["uid"],
        name=entity_type.name,
        description=entity_type.description,
        icon=entity_type.icon,
        color=entity_type.color,
        fields_schema=entity_type.fields_schema,
        is_system=False
    )
    
    db.add(db_entity_type)
    db.commit()
    db.refresh(db_entity_type)
    return db_entity_type


# ========================= Entities =========================

@router.get("/", response_model=List[EntitySchema])
def get_entities(
    type_id: Optional[int] = None,
    search: Optional[str] = None,
    min_importance: Optional[float] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get entities with optional filtering."""
    query = db.query(Entity).filter(Entity.user_id == current_user["uid"])
    
    if type_id:
        query = query.filter(Entity.type_id == type_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Entity.name.ilike(search_pattern),
                Entity.description.ilike(search_pattern)
            )
        )
    
    if min_importance is not None:
        query = query.filter(Entity.importance >= min_importance)
    
    # Order by importance and recency
    query = query.order_by(
        Entity.importance.desc(),
        Entity.last_interaction.desc().nullslast()
    )
    
    entities = query.offset(offset).limit(limit).all()
    return entities


@router.get("/{entity_id}", response_model=EntitySchema)
def get_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific entity by ID."""
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity


@router.post("/", response_model=EntitySchema)
def create_entity(
    entity: EntitySchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new entity."""
    # Verify entity type exists and user has access
    entity_type = db.query(EntityType).filter(
        EntityType.id == entity.type_id,
        or_(
            EntityType.user_id == current_user["uid"],
            EntityType.is_system == True
        )
    ).first()
    
    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    
    # Check for duplicate
    existing = db.query(Entity).filter(
        Entity.name == entity.name,
        Entity.type_id == entity.type_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Entity already exists")
    
    db_entity = Entity(
        user_id=current_user["uid"],
        type_id=entity.type_id,
        name=entity.name,
        description=entity.description,
        attributes=entity.attributes,
        importance=entity.importance or 0.5,
        is_active=True
    )
    
    db.add(db_entity)
    db.commit()
    db.refresh(db_entity)
    return db_entity


@router.put("/{entity_id}", response_model=EntitySchema)
def update_entity(
    entity_id: int,
    entity: EntitySchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing entity."""
    db_entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Update fields
    for field in ["name", "description", "attributes", "importance", "is_active"]:
        if hasattr(entity, field) and getattr(entity, field) is not None:
            setattr(db_entity, field, getattr(entity, field))
    
    db_entity.last_interaction = datetime.utcnow()
    
    db.commit()
    db.refresh(db_entity)
    return db_entity


@router.delete("/{entity_id}")
def delete_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an entity and its relationships."""
    db_entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Delete relationships
    db.query(EntityRelationship).filter(
        or_(
            EntityRelationship.source_entity_id == entity_id,
            EntityRelationship.target_entity_id == entity_id
        )
    ).delete()
    
    # Delete goal/project/task associations
    db.query(GoalEntity).filter(GoalEntity.entity_id == entity_id).delete()
    db.query(ProjectEntity).filter(ProjectEntity.entity_id == entity_id).delete()
    db.query(TaskEntity).filter(TaskEntity.entity_id == entity_id).delete()
    
    # Delete the entity
    db.delete(db_entity)
    db.commit()
    
    return {"message": "Entity deleted successfully"}


# ========================= Entity Relationships =========================

@router.get("/{entity_id}/relationships", response_model=List[EntityRelationshipSchema])
def get_entity_relationships(
    entity_id: int,
    direction: Optional[str] = Query(None, regex="^(outgoing|incoming|both)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get relationships for an entity."""
    # Verify entity belongs to user
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    if direction == "outgoing":
        relationships = db.query(EntityRelationship).filter(
            EntityRelationship.source_entity_id == entity_id
        ).all()
    elif direction == "incoming":
        relationships = db.query(EntityRelationship).filter(
            EntityRelationship.target_entity_id == entity_id
        ).all()
    else:  # both or None
        relationships = db.query(EntityRelationship).filter(
            or_(
                EntityRelationship.source_entity_id == entity_id,
                EntityRelationship.target_entity_id == entity_id
            )
        ).all()
    
    return relationships


@router.post("/relationships", response_model=EntityRelationshipSchema)
def create_relationship(
    relationship: EntityRelationshipSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a relationship between two entities."""
    # Verify both entities belong to user
    source = db.query(Entity).filter(
        Entity.id == relationship.source_entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    target = db.query(Entity).filter(
        Entity.id == relationship.target_entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not source or not target:
        raise HTTPException(status_code=404, detail="One or both entities not found")
    
    # Check if relationship already exists
    existing = db.query(EntityRelationship).filter(
        EntityRelationship.source_entity_id == relationship.source_entity_id,
        EntityRelationship.target_entity_id == relationship.target_entity_id,
        EntityRelationship.relationship_type == relationship.relationship_type
    ).first()
    
    if existing:
        # Update strength if exists
        existing.strength = max(existing.strength, relationship.strength or 0.5)
        existing.last_interaction = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new relationship
    db_relationship = EntityRelationship(
        source_entity_id=relationship.source_entity_id,
        target_entity_id=relationship.target_entity_id,
        relationship_type=relationship.relationship_type,
        strength=relationship.strength or 0.5,
        attributes=relationship.attributes
    )
    
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship


@router.delete("/relationships/{relationship_id}")
def delete_relationship(
    relationship_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a relationship between entities."""
    # Get relationship and verify ownership through entities
    relationship = db.query(EntityRelationship).filter(
        EntityRelationship.id == relationship_id
    ).first()
    
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    # Verify source entity belongs to user
    source = db.query(Entity).filter(
        Entity.id == relationship.source_entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not source:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(relationship)
    db.commit()
    
    return {"message": "Relationship deleted successfully"}


# ========================= Entity Associations =========================

@router.post("/goals/{goal_id}/entities/{entity_id}")
def associate_entity_with_goal(
    goal_id: int,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Associate an entity with a goal."""
    # Verify goal and entity belong to user
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user["uid"]
    ).first()
    
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not goal or not entity:
        raise HTTPException(status_code=404, detail="Goal or entity not found")
    
    # Check if association exists
    existing = db.query(GoalEntity).filter(
        GoalEntity.goal_id == goal_id,
        GoalEntity.entity_id == entity_id
    ).first()
    
    if existing:
        return {"message": "Association already exists"}
    
    # Create association
    association = GoalEntity(goal_id=goal_id, entity_id=entity_id)
    db.add(association)
    
    # Update entity importance
    entity.importance = min(1.0, entity.importance + 0.1)
    entity.last_interaction = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Entity associated with goal successfully"}


@router.post("/projects/{project_id}/entities/{entity_id}")
def associate_entity_with_project(
    project_id: int,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Associate an entity with a project."""
    # Verify project and entity belong to user
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user["uid"]
    ).first()
    
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not project or not entity:
        raise HTTPException(status_code=404, detail="Project or entity not found")
    
    # Check if association exists
    existing = db.query(ProjectEntity).filter(
        ProjectEntity.project_id == project_id,
        ProjectEntity.entity_id == entity_id
    ).first()
    
    if existing:
        return {"message": "Association already exists"}
    
    # Create association
    association = ProjectEntity(project_id=project_id, entity_id=entity_id)
    db.add(association)
    
    # Update entity importance
    entity.importance = min(1.0, entity.importance + 0.1)
    entity.last_interaction = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Entity associated with project successfully"}


@router.post("/tasks/{task_id}/entities/{entity_id}")
def associate_entity_with_task(
    task_id: int,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Associate an entity with a task."""
    # Verify task and entity belong to user
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user["uid"]
    ).first()
    
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not task or not entity:
        raise HTTPException(status_code=404, detail="Task or entity not found")
    
    # Check if association exists
    existing = db.query(TaskEntity).filter(
        TaskEntity.task_id == task_id,
        TaskEntity.entity_id == entity_id
    ).first()
    
    if existing:
        return {"message": "Association already exists"}
    
    # Create association
    association = TaskEntity(task_id=task_id, entity_id=entity_id)
    db.add(association)
    
    # Update entity importance
    entity.importance = min(1.0, entity.importance + 0.05)
    entity.last_interaction = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Entity associated with task successfully"}


# ========================= Graph Analysis =========================

@router.get("/graph/network/{entity_id}")
def get_entity_network(
    entity_id: int,
    depth: int = Query(2, ge=1, le=3),
    min_strength: float = Query(0.3, ge=0, le=1),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the network graph around an entity up to specified depth."""
    # Verify entity belongs to user
    entity = db.query(Entity).filter(
        Entity.id == entity_id,
        Entity.user_id == current_user["uid"]
    ).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Build network graph
    visited = set()
    network = {"nodes": [], "edges": []}
    
    def add_entity_to_network(entity_id: int, current_depth: int):
        if entity_id in visited or current_depth > depth:
            return
        
        visited.add(entity_id)
        
        # Get entity details
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return
        
        # Add node
        network["nodes"].append({
            "id": entity.id,
            "name": entity.name,
            "type": entity.type.name if entity.type else "unknown",
            "importance": entity.importance,
            "depth": current_depth
        })
        
        # Get relationships
        relationships = db.query(EntityRelationship).filter(
            and_(
                or_(
                    EntityRelationship.source_entity_id == entity_id,
                    EntityRelationship.target_entity_id == entity_id
                ),
                EntityRelationship.strength >= min_strength
            )
        ).all()
        
        for rel in relationships:
            # Add edge
            network["edges"].append({
                "source": rel.source_entity_id,
                "target": rel.target_entity_id,
                "type": rel.relationship_type,
                "strength": rel.strength
            })
            
            # Recursively add connected entities
            if current_depth < depth:
                if rel.source_entity_id == entity_id:
                    add_entity_to_network(rel.target_entity_id, current_depth + 1)
                else:
                    add_entity_to_network(rel.source_entity_id, current_depth + 1)
    
    add_entity_to_network(entity_id, 0)
    
    return network


@router.get("/graph/important")
def get_important_entities(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the most important entities for the user."""
    entities = db.query(Entity).filter(
        Entity.user_id == current_user["uid"],
        Entity.is_active == True
    ).order_by(
        Entity.importance.desc(),
        Entity.last_interaction.desc().nullslast()
    ).limit(limit).all()
    
    result = []
    for entity in entities:
        # Count associations
        goal_count = db.query(GoalEntity).filter(
            GoalEntity.entity_id == entity.id
        ).count()
        
        project_count = db.query(ProjectEntity).filter(
            ProjectEntity.entity_id == entity.id
        ).count()
        
        task_count = db.query(TaskEntity).filter(
            TaskEntity.entity_id == entity.id
        ).count()
        
        relationship_count = db.query(EntityRelationship).filter(
            or_(
                EntityRelationship.source_entity_id == entity.id,
                EntityRelationship.target_entity_id == entity.id
            )
        ).count()
        
        result.append({
            "id": entity.id,
            "name": entity.name,
            "type": entity.type.name if entity.type else "unknown",
            "importance": entity.importance,
            "last_interaction": entity.last_interaction,
            "associations": {
                "goals": goal_count,
                "projects": project_count,
                "tasks": task_count,
                "relationships": relationship_count
            }
        })
    
    return result
