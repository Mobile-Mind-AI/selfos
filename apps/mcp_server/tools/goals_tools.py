"""
Goals Tools Handler

MCP tools for managing goals in the SelfOS system.
Provides CRUD operations and search functionality for goals.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from mcp.types import Tool

from tools.base_tools import BaseToolsHandler

logger = logging.getLogger(__name__)


class GoalsToolsHandler(BaseToolsHandler):
    """Handler for goal-related MCP tools."""
    
    def __init__(self):
        super().__init__()
        self.tool_prefix = "goals_"
    
    async def list_tools(self) -> List[Tool]:
        """Return list of goal-related tools."""
        return [
            Tool(
                name="goals_list",
                description="List goals for a user with optional filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "status": {"type": "string", "description": "Filter by goal status"},
                        "life_area_id": {"type": "integer", "description": "Filter by life area"},
                        "limit": {"type": "integer", "default": 50, "description": "Maximum number of goals"}
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="goals_get",
                description="Get a specific goal by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "goal_id": {"type": "integer", "description": "Goal identifier"}
                    },
                    "required": ["user_id", "goal_id"]
                }
            ),
            Tool(
                name="goals_create",
                description="Create a new goal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "title": {"type": "string", "description": "Goal title"},
                        "description": {"type": "string", "description": "Goal description"},
                        "project_id": {"type": "integer", "description": "Associated project ID"},
                        "life_area_id": {"type": "integer", "description": "Life area ID"},
                        "target_date": {"type": "string", "description": "Target completion date"},
                        "priority": {"type": "string", "description": "Goal priority (low, medium, high)"}
                    },
                    "required": ["user_id", "title"]
                }
            ),
            Tool(
                name="goals_update",
                description="Update an existing goal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "goal_id": {"type": "integer", "description": "Goal identifier"},
                        "title": {"type": "string", "description": "Goal title"},
                        "description": {"type": "string", "description": "Goal description"},
                        "status": {"type": "string", "description": "Goal status"},
                        "progress": {"type": "number", "description": "Goal progress percentage"},
                        "priority": {"type": "string", "description": "Goal priority"}
                    },
                    "required": ["user_id", "goal_id"]
                }
            ),
            Tool(
                name="goals_delete",
                description="Delete a goal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "goal_id": {"type": "integer", "description": "Goal identifier"}
                    },
                    "required": ["user_id", "goal_id"]
                }
            ),
            Tool(
                name="goals_search",
                description="Search goals by keywords",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 20, "description": "Maximum results"}
                    },
                    "required": ["user_id", "query"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict:
        """Execute a goal-related tool."""
        try:
            # Sanitize arguments
            arguments = self.sanitize_arguments(arguments)
            
            # Route to appropriate method
            if name == "goals_list":
                return await self._list_goals(arguments)
            elif name == "goals_get":
                return await self._get_goal(arguments)
            elif name == "goals_create":
                return await self._create_goal(arguments)
            elif name == "goals_update":
                return await self._update_goal(arguments)
            elif name == "goals_delete":
                return await self._delete_goal(arguments)
            elif name == "goals_search":
                return await self._search_goals(arguments)
            else:
                return {"error": f"Unknown goal tool: {name}", "success": False}
                
        except Exception as e:
            return self.handle_error(e, name)
    
    async def _list_goals(self, arguments: Dict) -> Dict:
        """List goals for a user."""
        # Validate required arguments
        error = self.validate_required_args(arguments, ["user_id"])
        if error:
            return {"error": error, "success": False}
        
        db = self.get_db_session()
        try:
            # Import models here to avoid circular imports
            from models import Goal, LifeArea, Project
            from sqlalchemy import and_, desc
            
            user_id = arguments["user_id"]
            
            # Validate user access
            if not await self.validate_user_access(user_id, db):
                return {"error": "User not found or access denied", "success": False}
            
            # Build query
            query = db.query(Goal).filter(Goal.user_id == user_id)
            
            # Apply filters
            if "status" in arguments:
                query = query.filter(Goal.status == arguments["status"])
            if "life_area_id" in arguments:
                query = query.filter(Goal.life_area_id == arguments["life_area_id"])
            if "project_id" in arguments:
                query = query.filter(Goal.project_id == arguments["project_id"])
            
            # Apply ordering and limit
            limit = arguments.get("limit", 50)
            goals = query.order_by(desc(Goal.created_at)).limit(limit).all()
            
            # Convert to dict format
            goals_data = []
            for goal in goals:
                goal_dict = {
                    "id": goal.id,
                    "title": goal.title,
                    "description": goal.description,
                    "status": goal.status,
                    "progress": goal.progress,
                    "priority": goal.priority,
                    "project_id": goal.project_id,
                    "life_area_id": goal.life_area_id,
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "created_at": goal.created_at.isoformat(),
                    "updated_at": goal.updated_at.isoformat()
                }
                goals_data.append(goal_dict)
            
            return self.format_success_response(goals_data, "goals_list")
            
        except Exception as e:
            return self.handle_error(e, "goals_list")
        finally:
            db.close()
    
    async def _get_goal(self, arguments: Dict) -> Dict:
        """Get a specific goal by ID."""
        error = self.validate_required_args(arguments, ["user_id", "goal_id"])
        if error:
            return {"error": error, "success": False}
        
        db = self.get_db_session()
        try:
            from models import Goal
            from sqlalchemy import and_
            
            user_id = arguments["user_id"]
            goal_id = arguments["goal_id"]
            
            # Validate user access
            if not await self.validate_user_access(user_id, db):
                return {"error": "User not found or access denied", "success": False}
            
            # Get goal
            goal = db.query(Goal).filter(
                and_(Goal.id == goal_id, Goal.user_id == user_id)
            ).first()
            
            if not goal:
                return {"error": "Goal not found", "success": False}
            
            goal_dict = {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "status": goal.status,
                "progress": goal.progress,
                "priority": goal.priority,
                "project_id": goal.project_id,
                "life_area_id": goal.life_area_id,
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "created_at": goal.created_at.isoformat(),
                "updated_at": goal.updated_at.isoformat()
            }
            
            return self.format_success_response(goal_dict, "goals_get")
            
        except Exception as e:
            return self.handle_error(e, "goals_get")
        finally:
            db.close()
    
    async def _create_goal(self, arguments: Dict) -> Dict:
        """Create a new goal."""
        error = self.validate_required_args(arguments, ["user_id", "title"])
        if error:
            return {"error": error, "success": False}
        
        db = self.get_db_session()
        try:
            from models import Goal
            
            user_id = arguments["user_id"]
            
            # Validate user access
            if not await self.validate_user_access(user_id, db):
                return {"error": "User not found or access denied", "success": False}
            
            # Create goal
            goal = Goal(
                user_id=user_id,
                title=arguments["title"],
                description=arguments.get("description"),
                project_id=arguments.get("project_id"),
                life_area_id=arguments.get("life_area_id"),
                priority=arguments.get("priority", "medium"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Parse target_date if provided
            if "target_date" in arguments:
                try:
                    goal.target_date = datetime.fromisoformat(arguments["target_date"])
                except ValueError:
                    return {"error": "Invalid target_date format", "success": False}
            
            db.add(goal)
            db.commit()
            db.refresh(goal)
            
            goal_dict = {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "status": goal.status,
                "progress": goal.progress,
                "priority": goal.priority,
                "project_id": goal.project_id,
                "life_area_id": goal.life_area_id,
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "created_at": goal.created_at.isoformat(),
                "updated_at": goal.updated_at.isoformat()
            }
            
            return self.format_success_response(goal_dict, "goals_create")
            
        except Exception as e:
            db.rollback()
            return self.handle_error(e, "goals_create")
        finally:
            db.close()
    
    async def _update_goal(self, arguments: Dict) -> Dict:
        """Update an existing goal."""
        error = self.validate_required_args(arguments, ["user_id", "goal_id"])
        if error:
            return {"error": error, "success": False}
        
        db = self.get_db_session()
        try:
            from models import Goal
            from sqlalchemy import and_
            
            user_id = arguments["user_id"]
            goal_id = arguments["goal_id"]
            
            # Validate user access
            if not await self.validate_user_access(user_id, db):
                return {"error": "User not found or access denied", "success": False}
            
            # Get goal
            goal = db.query(Goal).filter(
                and_(Goal.id == goal_id, Goal.user_id == user_id)
            ).first()
            
            if not goal:
                return {"error": "Goal not found", "success": False}
            
            # Update fields
            updatable_fields = ["title", "description", "status", "progress", "priority"]
            for field in updatable_fields:
                if field in arguments:
                    setattr(goal, field, arguments[field])
            
            goal.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(goal)
            
            goal_dict = {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "status": goal.status,
                "progress": goal.progress,
                "priority": goal.priority,
                "project_id": goal.project_id,
                "life_area_id": goal.life_area_id,
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "created_at": goal.created_at.isoformat(),
                "updated_at": goal.updated_at.isoformat()
            }
            
            return self.format_success_response(goal_dict, "goals_update")
            
        except Exception as e:
            db.rollback()
            return self.handle_error(e, "goals_update")
        finally:
            db.close()
    
    async def _delete_goal(self, arguments: Dict) -> Dict:
        """Delete a goal."""
        error = self.validate_required_args(arguments, ["user_id", "goal_id"])
        if error:
            return {"error": error, "success": False}
        
        db = self.get_db_session()
        try:
            from models import Goal
            from sqlalchemy import and_
            
            user_id = arguments["user_id"]
            goal_id = arguments["goal_id"]
            
            # Validate user access
            if not await self.validate_user_access(user_id, db):
                return {"error": "User not found or access denied", "success": False}
            
            # Get goal
            goal = db.query(Goal).filter(
                and_(Goal.id == goal_id, Goal.user_id == user_id)
            ).first()
            
            if not goal:
                return {"error": "Goal not found", "success": False}
            
            db.delete(goal)
            db.commit()
            
            return self.format_success_response({"deleted_goal_id": goal_id}, "goals_delete")
            
        except Exception as e:
            db.rollback()
            return self.handle_error(e, "goals_delete")
        finally:
            db.close()
    
    async def _search_goals(self, arguments: Dict) -> Dict:
        """Search goals by keywords."""
        error = self.validate_required_args(arguments, ["user_id", "query"])
        if error:
            return {"error": error, "success": False}
        
        db = self.get_db_session()
        try:
            from models import Goal
            from sqlalchemy import and_, or_, func
            
            user_id = arguments["user_id"]
            query = arguments["query"]
            limit = arguments.get("limit", 20)
            
            # Validate user access
            if not await self.validate_user_access(user_id, db):
                return {"error": "User not found or access denied", "success": False}
            
            # Search in title and description
            search_filter = or_(
                Goal.title.ilike(f"%{query}%"),
                Goal.description.ilike(f"%{query}%")
            )
            
            goals = db.query(Goal).filter(
                and_(Goal.user_id == user_id, search_filter)
            ).limit(limit).all()
            
            goals_data = []
            for goal in goals:
                goal_dict = {
                    "id": goal.id,
                    "title": goal.title,
                    "description": goal.description,
                    "status": goal.status,
                    "progress": goal.progress,
                    "priority": goal.priority,
                    "project_id": goal.project_id,
                    "life_area_id": goal.life_area_id,
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "created_at": goal.created_at.isoformat(),
                    "updated_at": goal.updated_at.isoformat()
                }
                goals_data.append(goal_dict)
            
            return self.format_success_response({
                "goals": goals_data,
                "query": query,
                "count": len(goals_data)
            }, "goals_search")
            
        except Exception as e:
            return self.handle_error(e, "goals_search")
        finally:
            db.close()