"""
Project Service

This service encapsulates all business logic related to project management,
including CRUD operations, progress calculations, and hierarchy operations.
"""

import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

import models
import schemas

logger = logging.getLogger(__name__)


class ProjectService:
    """Service class for project-related business operations."""
    
    def get_project(self, db: Session, user_id: str, project_id: int) -> Optional[models.Project]:
        """
        Retrieve a single project by ID for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the project
            project_id: ID of the project to retrieve
            
        Returns:
            Project model instance or None if not found
        """
        try:
            project = db.query(models.Project).options(
                joinedload(models.Project.goals),
                joinedload(models.Project.tasks),
                joinedload(models.Project.life_area)
            ).filter(
                models.Project.id == project_id,
                models.Project.user_id == user_id
            ).first()
            
            if project:
                logger.info(f"Retrieved project {project_id} for user {user_id}")
            else:
                logger.warning(f"Project {project_id} not found for user {user_id}")
                
            return project
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving project {project_id}: {e}")
            raise
    
    def list_projects(self, db: Session, user_id: str) -> List[models.Project]:
        """
        Retrieve all projects for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user whose projects to retrieve
            
        Returns:
            List of project model instances
        """
        try:
            projects = db.query(models.Project).options(
                joinedload(models.Project.goals),
                joinedload(models.Project.tasks),
                joinedload(models.Project.life_area)
            ).filter(models.Project.user_id == user_id).all()
            
            logger.info(f"Retrieved {len(projects)} projects for user {user_id}")
            return projects
        except SQLAlchemyError as e:
            logger.error(f"Database error listing projects for user {user_id}: {e}")
            raise
    
    def create_project(self, db: Session, user_id: str, project_data: schemas.ProjectCreate) -> models.Project:
        """
        Create a new project for a user.

        Args:
            db: Database session
            user_id: ID of the user creating the project
            project_data: Project creation data
            
        Returns:
            Created project model instance
            
        Raises:
            ValueError: If parent_id creates a cycle or parent doesn't exist
        """
        try:
            # Validate parent_id if provided
            if project_data.parent_id:
                parent = self.get_project(db, user_id, project_data.parent_id)
                if not parent:
                    raise ValueError(f"Parent project {project_data.parent_id} not found")
            
            db_project = models.Project(
                user_id=user_id,
                title=project_data.title,
                description=project_data.description,
                status=project_data.status,
                priority=project_data.priority,
                progress=project_data.progress,
                life_area_id=project_data.life_area_id,
                parent_id=project_data.parent_id,
            )
            
            db.add(db_project)
            db.commit()
            db.refresh(db_project)
            
            parent_info = f" (parent: {project_data.parent_id})" if project_data.parent_id else ""
            logger.info(f"Created project {db_project.id} '{db_project.title}' for user {user_id}{parent_info}")
            return db_project
        except SQLAlchemyError as e:
            logger.error(f"Database error creating project for user {user_id}: {e}")
            db.rollback()
            raise
    
    def update_project(self, db: Session, user_id: str, project_id: int, project_data: schemas.ProjectCreate) -> Optional[models.Project]:
        """
        Update an existing project.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the project
            project_id: ID of the project to update
            project_data: Updated project data
            
        Returns:
            Updated project model instance or None if not found
            
        Raises:
            ValueError: If parent_id creates a cycle or parent doesn't exist
        """
        try:
            project = db.query(models.Project).options(
                joinedload(models.Project.goals),
                joinedload(models.Project.tasks),
                joinedload(models.Project.life_area)
            ).filter(
                models.Project.id == project_id,
                models.Project.user_id == user_id
            ).first()
            
            if not project:
                logger.warning(f"Project {project_id} not found for update by user {user_id}")
                return None
            
            # Validate parent_id if provided and different from current
            if project_data.parent_id and project_data.parent_id != project.parent_id:
                if project_data.parent_id == project_id:
                    raise ValueError("Project cannot be parent of itself")
                
                # Check if parent exists
                parent = self.get_project(db, user_id, project_data.parent_id)
                if not parent:
                    raise ValueError(f"Parent project {project_data.parent_id} not found")
                
                # Check for cycles by ensuring new parent is not a descendant
                if self._would_create_cycle(db, user_id, project_id, project_data.parent_id):
                    raise ValueError("Moving project would create a cycle in hierarchy")
            
            # Store old values for logging
            old_progress = project.progress
            old_parent = project.parent_id
            
            # Update project fields
            project.title = project_data.title
            project.description = project_data.description
            project.status = project_data.status
            project.priority = project_data.priority
            project.progress = project_data.progress
            project.life_area_id = project_data.life_area_id
            project.parent_id = project_data.parent_id
            project.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(project)
            
            parent_change = ""
            if old_parent != project_data.parent_id:
                parent_change = f" Parent: {old_parent} -> {project_data.parent_id}"
            
            logger.info(f"Updated project {project_id} for user {user_id}. Progress: {old_progress}% -> {project.progress}%{parent_change}")
            return project
        except SQLAlchemyError as e:
            logger.error(f"Database error updating project {project_id}: {e}")
            db.rollback()
            raise
    
    def delete_project(self, db: Session, user_id: str, project_id: int) -> bool:
        """
        Delete a project.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the project
            project_id: ID of the project to delete
            
        Returns:
            True if project was deleted, False if not found
        """
        try:
            project = db.query(models.Project).options(
                joinedload(models.Project.goals),
                joinedload(models.Project.tasks),
                joinedload(models.Project.life_area)
            ).filter(
                models.Project.id == project_id,
                models.Project.user_id == user_id
            ).first()
            
            if not project:
                logger.warning(f"Project {project_id} not found for deletion by user {user_id}")
                return False
            
            db.delete(project)
            db.commit()
            
            logger.info(f"Deleted project {project_id} '{project.title}' for user {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting project {project_id}: {e}")
            db.rollback()
            raise
    
    def get_projects_by_life_area(self, db: Session, user_id: str, life_area_id: int) -> List[models.Project]:
        """
        Retrieve all projects for a specific life area.
        
        Args:
            db: Database session
            user_id: ID of the user
            life_area_id: ID of the life area
            
        Returns:
            List of projects in the specified life area
        """
        try:
            projects = db.query(models.Project).options(
                joinedload(models.Project.goals),
                joinedload(models.Project.tasks),
                joinedload(models.Project.life_area)
            ).filter(
                models.Project.user_id == user_id,
                models.Project.life_area_id == life_area_id
            ).all()
            
            logger.info(f"Retrieved {len(projects)} projects for life area {life_area_id}, user {user_id}")
            return projects
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving projects for life area {life_area_id}: {e}")
            raise
    
    def get_projects_by_status(self, db: Session, user_id: str, status: str) -> List[models.Project]:
        """
        Retrieve all projects with a specific status.
        
        Args:
            db: Database session
            user_id: ID of the user
            status: Project status to filter by
            
        Returns:
            List of projects with the specified status
        """
        try:
            projects = db.query(models.Project).options(
                joinedload(models.Project.goals),
                joinedload(models.Project.tasks),
                joinedload(models.Project.life_area)
            ).filter(
                models.Project.user_id == user_id,
                models.Project.status == status
            ).all()
            
            logger.info(f"Retrieved {len(projects)} projects with status '{status}' for user {user_id}")
            return projects
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving projects with status '{status}': {e}")
            raise
    
    # Hierarchy-specific methods
    
    def _would_create_cycle(self, db: Session, user_id: str, project_id: int, new_parent_id: int) -> bool:
        """
        Check if setting new_parent_id as parent of project_id would create a cycle.
        
        Args:
            db: Database session
            user_id: ID of the user
            project_id: ID of the project being moved
            new_parent_id: ID of the proposed new parent
            
        Returns:
            True if cycle would be created, False otherwise
        """
        try:
            # Check if new_parent_id is a descendant of project_id
            descendants = self.get_project_descendants(db, user_id, project_id)
            descendant_ids = [desc.id for desc in descendants]
            return new_parent_id in descendant_ids
        except Exception as e:
            logger.error(f"Error checking for cycles: {e}")
            return True  # Assume cycle to be safe
    
    def get_project_children(self, db: Session, user_id: str, parent_id: int) -> List[models.Project]:
        """
        Get direct children of a project.
        
        Args:
            db: Database session
            user_id: ID of the user
            parent_id: ID of the parent project
            
        Returns:
            List of direct child projects
        """
        try:
            children = db.query(models.Project).options(
                joinedload(models.Project.goals),
                joinedload(models.Project.tasks),
                joinedload(models.Project.life_area)
            ).filter(
                models.Project.user_id == user_id,
                models.Project.parent_id == parent_id
            ).all()
            
            logger.info(f"Retrieved {len(children)} children for project {parent_id}, user {user_id}")
            return children
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving project children for {parent_id}: {e}")
            raise
    
    def get_project_descendants(self, db: Session, user_id: str, project_id: int) -> List[models.Project]:
        """
        Get all descendants (children, grandchildren, etc.) of a project.
        
        Args:
            db: Database session
            user_id: ID of the user
            project_id: ID of the ancestor project
            
        Returns:
            List of all descendant projects
        """
        descendants = []
        children = self.get_project_children(db, user_id, project_id)
        
        for child in children:
            descendants.append(child)
            # Recursively get descendants of each child
            child_descendants = self.get_project_descendants(db, user_id, child.id)
            descendants.extend(child_descendants)
        
        return descendants
    
    def get_project_path(self, db: Session, user_id: str, project_id: int) -> List[schemas.HierarchyPathItem]:
        """
        Get the full path from root to the specified project.
        
        Args:
            db: Database session
            user_id: ID of the user
            project_id: ID of the project
            
        Returns:
            List of HierarchyPathItem representing the path from root to project
        """
        path = []
        current_project = self.get_project(db, user_id, project_id)
        
        if not current_project:
            return path
        
        # Build path by traversing up to root
        while current_project:
            path.insert(0, schemas.HierarchyPathItem(
                id=current_project.id,
                title=current_project.title,
                entity_type="project",
                level=len(path)
            ))
            
            if current_project.parent_id:
                current_project = self.get_project(db, user_id, current_project.parent_id)
            else:
                current_project = None
        
        # Adjust levels to be correct (0-based from root)
        for i, item in enumerate(path):
            item.level = i
        
        return path
    
    def get_root_projects(self, db: Session, user_id: str) -> List[models.Project]:
        """
        Get all root-level projects (projects without parents).
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of root-level projects
        """
        try:
            projects = db.query(models.Project).options(
                joinedload(models.Project.goals),
                joinedload(models.Project.tasks),
                joinedload(models.Project.life_area)
            ).filter(
                models.Project.user_id == user_id,
                models.Project.parent_id.is_(None)
            ).all()
            
            logger.info(f"Retrieved {len(projects)} root projects for user {user_id}")
            return projects
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving root projects for user {user_id}: {e}")
            raise
    
    def move_project(self, db: Session, user_id: str, project_id: int, new_parent_id: Optional[int]) -> Optional[models.Project]:
        """
        Move a project to a new parent in the hierarchy.
        
        Args:
            db: Database session
            user_id: ID of the user
            project_id: ID of the project to move
            new_parent_id: ID of the new parent (None for root level)
            
        Returns:
            Updated project model instance or None if not found
            
        Raises:
            ValueError: If move would create a cycle or parent doesn't exist
        """
        try:
            project = self.get_project(db, user_id, project_id)
            if not project:
                return None
            
            # Validate new parent if provided
            if new_parent_id:
                if new_parent_id == project_id:
                    raise ValueError("Project cannot be parent of itself")
                
                new_parent = self.get_project(db, user_id, new_parent_id)
                if not new_parent:
                    raise ValueError(f"Parent project {new_parent_id} not found")
                
                # Check for cycles
                if self._would_create_cycle(db, user_id, project_id, new_parent_id):
                    raise ValueError("Moving project would create a cycle in hierarchy")
            
            old_parent = project.parent_id
            project.parent_id = new_parent_id
            project.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(project)
            
            logger.info(f"Moved project {project_id} from parent {old_parent} to {new_parent_id} for user {user_id}")
            return project
            
        except SQLAlchemyError as e:
            logger.error(f"Database error moving project {project_id}: {e}")
            db.rollback()
            raise


# Create a singleton instance of the service
project_service = ProjectService()
