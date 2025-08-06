"""
Goal Service

This service encapsulates all business logic related to goal management,
including CRUD operations, progress calculations, and goal-related workflows.
"""

import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

import models
import schemas

logger = logging.getLogger(__name__)


class GoalService:
    """Service class for goal-related business operations."""
    
    def get_goal(self, db: Session, user_id: str, goal_id: int) -> Optional[models.Goal]:
        """
        Retrieve a single goal by ID for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the goal
            goal_id: ID of the goal to retrieve
            
        Returns:
            Goal model instance or None if not found
        """
        try:
            goal = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.id == goal_id,
                models.Goal.user_id == user_id
            ).first()
            
            if goal:
                logger.info(f"Retrieved goal {goal_id} for user {user_id}")
            else:
                logger.warning(f"Goal {goal_id} not found for user {user_id}")
                
            return goal
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving goal {goal_id}: {e}")
            raise
    
    def list_goals(self, db: Session, user_id: str) -> List[models.Goal]:
        """
        Retrieve all goals for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user whose goals to retrieve
            
        Returns:
            List of goal model instances
        """
        try:
            goals = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(models.Goal.user_id == user_id).all()
            
            logger.info(f"Retrieved {len(goals)} goals for user {user_id}")
            return goals
        except SQLAlchemyError as e:
            logger.error(f"Database error listing goals for user {user_id}: {e}")
            raise
    
    def create_goal(self, db: Session, user_id: str, goal_data: schemas.GoalCreate) -> models.Goal:
        """
        Create a new goal for a user.

        Args:
            db: Database session
            user_id: ID of the user creating the goal
            goal_data: Goal creation data
            
        Returns:
            Created goal model instance
            
        Raises:
            ValueError: If parent_id creates a cycle or parent doesn't exist
        """
        try:
            # Validate parent_id if provided
            if goal_data.parent_id:
                parent = self.get_goal(db, user_id, goal_data.parent_id)
                if not parent:
                    raise ValueError(f"Parent goal {goal_data.parent_id} not found")
            
            db_goal = models.Goal(
                user_id=user_id,
                title=goal_data.title,
                description=goal_data.description,
                status=goal_data.status,
                progress=goal_data.progress,
                life_area_id=goal_data.life_area_id,
                project_id=goal_data.project_id,
                parent_id=goal_data.parent_id,
            )
            
            db.add(db_goal)
            db.commit()
            db.refresh(db_goal)
            
            parent_info = f" (parent: {goal_data.parent_id})" if goal_data.parent_id else ""
            logger.info(f"Created goal {db_goal.id} '{db_goal.title}' for user {user_id}{parent_info}")
            return db_goal
        except SQLAlchemyError as e:
            logger.error(f"Database error creating goal for user {user_id}: {e}")
            db.rollback()
            raise
    
    def update_goal(self, db: Session, user_id: str, goal_id: int, goal_data: schemas.GoalCreate) -> Optional[models.Goal]:
        """
        Update an existing goal.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the goal
            goal_id: ID of the goal to update
            goal_data: Updated goal data
            
        Returns:
            Updated goal model instance or None if not found
            
        Raises:
            ValueError: If parent_id creates a cycle or parent doesn't exist
        """
        try:
            goal = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.id == goal_id,
                models.Goal.user_id == user_id
            ).first()
            
            if not goal:
                logger.warning(f"Goal {goal_id} not found for update by user {user_id}")
                return None
            
            # Validate parent_id if provided and different from current
            if goal_data.parent_id and goal_data.parent_id != goal.parent_id:
                if goal_data.parent_id == goal_id:
                    raise ValueError("Goal cannot be parent of itself")
                
                # Check if parent exists
                parent = self.get_goal(db, user_id, goal_data.parent_id)
                if not parent:
                    raise ValueError(f"Parent goal {goal_data.parent_id} not found")
                
                # Check for cycles by ensuring new parent is not a descendant
                if self._would_create_cycle(db, user_id, goal_id, goal_data.parent_id):
                    raise ValueError("Moving goal would create a cycle in hierarchy")
            
            # Store old values for logging
            old_progress = goal.progress
            old_parent = goal.parent_id
            
            # Update goal fields
            goal.title = goal_data.title
            goal.description = goal_data.description
            goal.status = goal_data.status
            goal.progress = goal_data.progress
            goal.life_area_id = goal_data.life_area_id
            goal.project_id = goal_data.project_id
            goal.parent_id = goal_data.parent_id
            goal.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(goal)
            
            parent_change = ""
            if old_parent != goal_data.parent_id:
                parent_change = f" Parent: {old_parent} -> {goal_data.parent_id}"
            
            logger.info(f"Updated goal {goal_id} for user {user_id}. Progress: {old_progress}% -> {goal.progress}%{parent_change}")
            return goal
        except SQLAlchemyError as e:
            logger.error(f"Database error updating goal {goal_id}: {e}")
            db.rollback()
            raise
    
    def delete_goal(self, db: Session, user_id: str, goal_id: int) -> bool:
        """
        Delete a goal.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the goal
            goal_id: ID of the goal to delete
            
        Returns:
            True if goal was deleted, False if not found
        """
        try:
            goal = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.id == goal_id,
                models.Goal.user_id == user_id
            ).first()
            
            if not goal:
                logger.warning(f"Goal {goal_id} not found for deletion by user {user_id}")
                return False
            
            db.delete(goal)
            db.commit()
            
            logger.info(f"Deleted goal {goal_id} '{goal.title}' for user {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting goal {goal_id}: {e}")
            db.rollback()
            raise
    
    def get_goals_by_life_area(self, db: Session, user_id: str, life_area_id: int) -> List[models.Goal]:
        """
        Retrieve all goals for a specific life area.
        
        Args:
            db: Database session
            user_id: ID of the user
            life_area_id: ID of the life area
            
        Returns:
            List of goals in the specified life area
        """
        try:
            goals = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.user_id == user_id,
                models.Goal.life_area_id == life_area_id
            ).all()
            
            logger.info(f"Retrieved {len(goals)} goals for life area {life_area_id}, user {user_id}")
            return goals
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving goals for life area {life_area_id}: {e}")
            raise
    
    def get_goals_by_status(self, db: Session, user_id: str, status: str) -> List[models.Goal]:
        """
        Retrieve all goals with a specific status.
        
        Args:
            db: Database session
            user_id: ID of the user
            status: Goal status to filter by
            
        Returns:
            List of goals with the specified status
        """
        try:
            goals = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.user_id == user_id,
                models.Goal.status == status
            ).all()
            
            logger.info(f"Retrieved {len(goals)} goals with status '{status}' for user {user_id}")
            return goals
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving goals with status '{status}': {e}")
            raise
    
    # Hierarchy-specific methods
    
    def _would_create_cycle(self, db: Session, user_id: str, goal_id: int, new_parent_id: int) -> bool:
        """
        Check if setting new_parent_id as parent of goal_id would create a cycle.
        
        Args:
            db: Database session
            user_id: ID of the user
            goal_id: ID of the goal being moved
            new_parent_id: ID of the proposed new parent
            
        Returns:
            True if cycle would be created, False otherwise
        """
        try:
            # Check if new_parent_id is a descendant of goal_id
            descendants = self.get_goal_descendants(db, user_id, goal_id)
            descendant_ids = [desc.id for desc in descendants]
            return new_parent_id in descendant_ids
        except Exception as e:
            logger.error(f"Error checking for cycles: {e}")
            return True  # Assume cycle to be safe
    
    def get_goal_children(self, db: Session, user_id: str, parent_id: int) -> List[models.Goal]:
        """
        Get direct children of a goal.
        
        Args:
            db: Database session
            user_id: ID of the user
            parent_id: ID of the parent goal
            
        Returns:
            List of direct child goals
        """
        try:
            children = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.user_id == user_id,
                models.Goal.parent_id == parent_id
            ).all()
            
            logger.info(f"Retrieved {len(children)} children for goal {parent_id}, user {user_id}")
            return children
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving goal children for {parent_id}: {e}")
            raise
    
    def get_goal_descendants(self, db: Session, user_id: str, goal_id: int) -> List[models.Goal]:
        """
        Get all descendants (children, grandchildren, etc.) of a goal.
        
        Args:
            db: Database session
            user_id: ID of the user
            goal_id: ID of the ancestor goal
            
        Returns:
            List of all descendant goals
        """
        descendants = []
        children = self.get_goal_children(db, user_id, goal_id)
        
        for child in children:
            descendants.append(child)
            # Recursively get descendants of each child
            child_descendants = self.get_goal_descendants(db, user_id, child.id)
            descendants.extend(child_descendants)
        
        return descendants
    
    def get_goal_path(self, db: Session, user_id: str, goal_id: int) -> List[schemas.HierarchyPathItem]:
        """
        Get the full path from root to the specified goal.
        
        Args:
            db: Database session
            user_id: ID of the user
            goal_id: ID of the goal
            
        Returns:
            List of HierarchyPathItem representing the path from root to goal
        """
        path = []
        current_goal = self.get_goal(db, user_id, goal_id)
        
        if not current_goal:
            return path
        
        # Build path by traversing up to root
        while current_goal:
            path.insert(0, schemas.HierarchyPathItem(
                id=current_goal.id,
                title=current_goal.title,
                entity_type="goal",
                level=len(path)
            ))
            
            if current_goal.parent_id:
                current_goal = self.get_goal(db, user_id, current_goal.parent_id)
            else:
                current_goal = None
        
        # Adjust levels to be correct (0-based from root)
        for i, item in enumerate(path):
            item.level = i
        
        return path
    
    def get_root_goals(self, db: Session, user_id: str) -> List[models.Goal]:
        """
        Get all root-level goals (goals without parents).
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of root-level goals
        """
        try:
            goals = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.user_id == user_id,
                models.Goal.parent_id.is_(None)
            ).all()
            
            logger.info(f"Retrieved {len(goals)} root goals for user {user_id}")
            return goals
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving root goals for user {user_id}: {e}")
            raise
    
    def move_goal(self, db: Session, user_id: str, goal_id: int, new_parent_id: Optional[int]) -> Optional[models.Goal]:
        """
        Move a goal to a new parent in the hierarchy.
        
        Args:
            db: Database session
            user_id: ID of the user
            goal_id: ID of the goal to move
            new_parent_id: ID of the new parent (None for root level)
            
        Returns:
            Updated goal model instance or None if not found
            
        Raises:
            ValueError: If move would create a cycle or parent doesn't exist
        """
        try:
            goal = self.get_goal(db, user_id, goal_id)
            if not goal:
                return None
            
            # Validate new parent if provided
            if new_parent_id:
                if new_parent_id == goal_id:
                    raise ValueError("Goal cannot be parent of itself")
                
                new_parent = self.get_goal(db, user_id, new_parent_id)
                if not new_parent:
                    raise ValueError(f"Parent goal {new_parent_id} not found")
                
                # Check for cycles
                if self._would_create_cycle(db, user_id, goal_id, new_parent_id):
                    raise ValueError("Moving goal would create a cycle in hierarchy")
            
            old_parent = goal.parent_id
            goal.parent_id = new_parent_id
            goal.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(goal)
            
            logger.info(f"Moved goal {goal_id} from parent {old_parent} to {new_parent_id} for user {user_id}")
            return goal
            
        except SQLAlchemyError as e:
            logger.error(f"Database error moving goal {goal_id}: {e}")
            db.rollback()
            raise
    
    def get_goal_tree(self, db: Session, user_id: str) -> List[schemas.HierarchyTreeNode]:
        """
        Get complete hierarchical tree of goals for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of HierarchyTreeNode representing the complete goal hierarchy
        """
        try:
            root_goals = self.get_root_goals(db, user_id)
            tree = []
            
            for root in root_goals:
                tree_node = self._build_goal_tree_node(db, user_id, root)
                tree.append(tree_node)
            
            logger.info(f"Built goal tree with {len(tree)} root nodes for user {user_id}")
            return tree
            
        except Exception as e:
            logger.error(f"Error building goal tree for user {user_id}: {e}")
            raise
    
    def _build_goal_tree_node(self, db: Session, user_id: str, goal: models.Goal) -> schemas.HierarchyTreeNode:
        """
        Recursively build a tree node for a goal and its descendants.
        
        Args:
            db: Database session
            user_id: ID of the user
            goal: Goal model instance
            
        Returns:
            HierarchyTreeNode with nested children
        """
        # Get direct children
        children = self.get_goal_children(db, user_id, goal.id)
        child_nodes = []
        
        for child in children:
            child_node = self._build_goal_tree_node(db, user_id, child)
            child_nodes.append(child_node)
        
        return schemas.HierarchyTreeNode(
            id=goal.id,
            title=goal.title,
            entity_type="goal",
            level=0,  # Level will be calculated by the caller if needed
            parent_id=goal.parent_id,
            children=child_nodes,
            status=goal.status,
            progress=goal.progress,
            created_at=goal.created_at
        )


# Create a singleton instance of the service
goal_service = GoalService()
