"""
Onboarding Tools Handler

MCP tools for handling the user onboarding flow, including assistant creation,
personality setup, life areas selection, and first goal creation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_tools import BaseToolsHandler

logger = logging.getLogger(__name__)


class OnboardingToolsHandler(BaseToolsHandler):
    """Handler for onboarding-related MCP tools."""
    
    def __init__(self):
        super().__init__()
        self.tool_prefix = "onboarding"
    
    async def list_tools(self) -> List[Dict]:
        """Return list of onboarding tools."""
        return [
            {
                "name": f"{self.tool_prefix}_get_state",
                "description": "Get current onboarding state for a user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID to get onboarding state for"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": f"{self.tool_prefix}_start_flow",
                "description": "Start onboarding flow for a new user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID to start onboarding for"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": f"{self.tool_prefix}_create_assistant",
                "description": "Create assistant profile during onboarding",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "name": {
                            "type": "string",
                            "description": "Assistant name"
                        },
                        "avatar_url": {
                            "type": "string",
                            "description": "Assistant avatar URL (optional)"
                        }
                    },
                    "required": ["user_id", "name"]
                }
            },
            {
                "name": f"{self.tool_prefix}_set_personality",
                "description": "Set assistant personality during onboarding",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "style": {
                            "type": "object",
                            "description": "Personality style configuration",
                            "properties": {
                                "formality": {"type": "integer", "minimum": 0, "maximum": 100},
                                "directness": {"type": "integer", "minimum": 0, "maximum": 100},
                                "humor": {"type": "integer", "minimum": 0, "maximum": 100},
                                "empathy": {"type": "integer", "minimum": 0, "maximum": 100},
                                "motivation": {"type": "integer", "minimum": 0, "maximum": 100}
                            },
                            "required": ["formality", "directness", "humor", "empathy", "motivation"]
                        }
                    },
                    "required": ["user_id", "style"]
                }
            },
            {
                "name": f"{self.tool_prefix}_set_language_preferences",
                "description": "Set language and interaction preferences",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "language": {
                            "type": "string",
                            "description": "Primary language code (e.g., 'en', 'es')"
                        },
                        "requires_confirmation": {
                            "type": "boolean",
                            "description": "Whether to require confirmation before actions"
                        }
                    },
                    "required": ["user_id", "language"]
                }
            },
            {
                "name": f"{self.tool_prefix}_select_life_areas",
                "description": "Select life areas during onboarding",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "life_area_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "IDs of selected life areas"
                        },
                        "custom_life_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Names of custom life areas to create"
                        }
                    },
                    "required": ["user_id", "life_area_ids"]
                }
            },
            {
                "name": f"{self.tool_prefix}_create_first_goal",
                "description": "Create the user's first goal during onboarding",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "title": {
                            "type": "string",
                            "description": "Goal title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Goal description (optional)"
                        },
                        "life_area_id": {
                            "type": "integer",
                            "description": "Associated life area ID (optional)"
                        },
                        "generate_tasks": {
                            "type": "boolean",
                            "description": "Whether to auto-generate tasks using AI",
                            "default": True
                        }
                    },
                    "required": ["user_id", "title"]
                }
            },
            {
                "name": f"{self.tool_prefix}_complete_flow",
                "description": "Complete onboarding flow and prepare dashboard",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID to complete onboarding for"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": f"{self.tool_prefix}_preview_personality",
                "description": "Preview how assistant will communicate with given personality",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "formality": {"type": "integer", "minimum": 0, "maximum": 100},
                        "humor": {"type": "integer", "minimum": 0, "maximum": 100},
                        "motivation": {"type": "integer", "minimum": 0, "maximum": 100},
                        "context": {
                            "type": "string",
                            "description": "Context for preview (greeting, encouragement, etc.)",
                            "default": "greeting"
                        }
                    },
                    "required": ["formality", "humor", "motivation"]
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict:
        """Execute an onboarding tool."""
        try:
            # Sanitize arguments
            arguments = self.sanitize_arguments(arguments)
            
            # Route to appropriate handler
            if name == f"{self.tool_prefix}_get_state":
                return await self._get_onboarding_state(arguments)
            elif name == f"{self.tool_prefix}_start_flow":
                return await self._start_onboarding_flow(arguments)
            elif name == f"{self.tool_prefix}_create_assistant":
                return await self._create_assistant(arguments)
            elif name == f"{self.tool_prefix}_set_personality":
                return await self._set_personality(arguments)
            elif name == f"{self.tool_prefix}_set_language_preferences":
                return await self._set_language_preferences(arguments)
            elif name == f"{self.tool_prefix}_select_life_areas":
                return await self._select_life_areas(arguments)
            elif name == f"{self.tool_prefix}_create_first_goal":
                return await self._create_first_goal(arguments)
            elif name == f"{self.tool_prefix}_complete_flow":
                return await self._complete_flow(arguments)
            elif name == f"{self.tool_prefix}_preview_personality":
                return await self._preview_personality(arguments)
            else:
                return self.handle_error(
                    ValueError(f"Unknown tool: {name}"),
                    "call_tool"
                )
                
        except Exception as e:
            return self.handle_error(e, f"call_tool({name})")
    
    async def _get_onboarding_state(self, arguments: Dict) -> Dict:
        """Get current onboarding state for a user."""
        error = self.validate_required_args(arguments, ["user_id"])
        if error:
            return self.handle_error(ValueError(error), "get_onboarding_state")
        
        user_id = arguments["user_id"]
        
        if not await self.validate_user_access(user_id):
            return self.handle_error(
                ValueError("Invalid user access"),
                "get_onboarding_state"
            )
        
        db = self.get_db_session()
        if not db:
            return self.handle_error(
                RuntimeError("Database connection failed"),
                "get_onboarding_state"
            )
        
        try:
            from models import OnboardingState
            
            state = db.query(OnboardingState).filter(
                OnboardingState.user_id == user_id
            ).first()
            
            if not state:
                # Create initial state
                state = OnboardingState(
                    user_id=user_id,
                    current_step=1,
                    completed_steps=[]
                )
                db.add(state)
                db.commit()
                db.refresh(state)
            
            state_data = {
                "id": state.id,
                "user_id": state.user_id,
                "current_step": state.current_step,
                "completed_steps": state.completed_steps,
                "onboarding_completed": state.onboarding_completed,
                "assistant_profile_id": state.assistant_profile_id,
                "selected_life_areas": state.selected_life_areas,
                "first_goal_id": state.first_goal_id,
                "first_task_id": state.first_task_id,
                "theme_preference": state.theme_preference,
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "completed_at": state.completed_at.isoformat() if state.completed_at else None
            }
            
            return self.format_success_response(state_data, "get_onboarding_state")
            
        except Exception as e:
            return self.handle_error(e, "get_onboarding_state")
        finally:
            db.close()
    
    async def _start_onboarding_flow(self, arguments: Dict) -> Dict:
        """Start onboarding flow for a new user."""
        error = self.validate_required_args(arguments, ["user_id"])
        if error:
            return self.handle_error(ValueError(error), "start_onboarding_flow")
        
        user_id = arguments["user_id"]
        
        if not await self.validate_user_access(user_id):
            return self.handle_error(
                ValueError("Invalid user access"),
                "start_onboarding_flow"
            )
        
        db = self.get_db_session()
        if not db:
            return self.handle_error(
                RuntimeError("Database connection failed"),
                "start_onboarding_flow"
            )
        
        try:
            from models import OnboardingState
            
            # Check if onboarding already started
            existing_state = db.query(OnboardingState).filter(
                OnboardingState.user_id == user_id
            ).first()
            
            if existing_state and existing_state.onboarding_completed:
                return self.format_success_response(
                    {"message": "Onboarding already completed", "state": "completed"},
                    "start_onboarding_flow"
                )
            
            if not existing_state:
                # Create new onboarding state
                state = OnboardingState(
                    user_id=user_id,
                    current_step=1,
                    completed_steps=[]
                )
                db.add(state)
                db.commit()
                db.refresh(state)
            else:
                state = existing_state
            
            return self.format_success_response(
                {
                    "message": "Onboarding flow started",
                    "current_step": state.current_step,
                    "state_id": state.id
                },
                "start_onboarding_flow"
            )
            
        except Exception as e:
            return self.handle_error(e, "start_onboarding_flow")
        finally:
            db.close()
    
    async def _create_assistant(self, arguments: Dict) -> Dict:
        """Create assistant profile during onboarding."""
        error = self.validate_required_args(arguments, ["user_id", "name"])
        if error:
            return self.handle_error(ValueError(error), "create_assistant")
        
        user_id = arguments["user_id"]
        name = arguments["name"]
        avatar_url = arguments.get("avatar_url")
        
        if not await self.validate_user_access(user_id):
            return self.handle_error(
                ValueError("Invalid user access"),
                "create_assistant"
            )
        
        db = self.get_db_session()
        if not db:
            return self.handle_error(
                RuntimeError("Database connection failed"),
                "create_assistant"
            )
        
        try:
            from models import OnboardingState
            
            # Get onboarding state
            state = db.query(OnboardingState).filter(
                OnboardingState.user_id == user_id
            ).first()
            
            if not state:
                return self.handle_error(
                    ValueError("Onboarding state not found"),
                    "create_assistant"
                )
            
            # Store assistant data in temp storage for later use
            temp_data = state.temp_data or {}
            temp_data.update({
                "assistant_name": name,
                "avatar_url": avatar_url
            })
            
            state.temp_data = temp_data
            state.last_activity = datetime.utcnow()
            
            # Mark step 2 as completed
            if 2 not in state.completed_steps:
                state.completed_steps = state.completed_steps + [2]
                state.current_step = 3
            
            db.commit()
            
            return self.format_success_response(
                {
                    "message": "Assistant created successfully",
                    "assistant_name": name,
                    "current_step": state.current_step
                },
                "create_assistant"
            )
            
        except Exception as e:
            return self.handle_error(e, "create_assistant")
        finally:
            db.close()
    
    async def _set_personality(self, arguments: Dict) -> Dict:
        """Set assistant personality during onboarding."""
        error = self.validate_required_args(arguments, ["user_id", "style"])
        if error:
            return self.handle_error(ValueError(error), "set_personality")
        
        user_id = arguments["user_id"]
        style = arguments["style"]
        
        # Validate style values
        required_traits = ["formality", "directness", "humor", "empathy", "motivation"]
        for trait in required_traits:
            if trait not in style:
                return self.handle_error(
                    ValueError(f"Missing personality trait: {trait}"),
                    "set_personality"
                )
            value = style[trait]
            if not isinstance(value, int) or value < 0 or value > 100:
                return self.handle_error(
                    ValueError(f"Invalid value for {trait}: must be integer 0-100"),
                    "set_personality"
                )
        
        if not await self.validate_user_access(user_id):
            return self.handle_error(
                ValueError("Invalid user access"),
                "set_personality"
            )
        
        db = self.get_db_session()
        if not db:
            return self.handle_error(
                RuntimeError("Database connection failed"),
                "set_personality"
            )
        
        try:
            from models import OnboardingState
            
            # Get onboarding state
            state = db.query(OnboardingState).filter(
                OnboardingState.user_id == user_id
            ).first()
            
            if not state:
                return self.handle_error(
                    ValueError("Onboarding state not found"),
                    "set_personality"
                )
            
            # Store personality in temp data
            temp_data = state.temp_data or {}
            temp_data["style"] = style
            
            state.temp_data = temp_data
            state.last_activity = datetime.utcnow()
            
            # Mark step 3 as completed
            if 3 not in state.completed_steps:
                state.completed_steps = state.completed_steps + [3]
                state.current_step = 4
            
            db.commit()
            
            return self.format_success_response(
                {
                    "message": "Personality set successfully",
                    "style": style,
                    "current_step": state.current_step
                },
                "set_personality"
            )
            
        except Exception as e:
            return self.handle_error(e, "set_personality")
        finally:
            db.close()
    
    async def _set_language_preferences(self, arguments: Dict) -> Dict:
        """Set language and interaction preferences."""
        error = self.validate_required_args(arguments, ["user_id", "language"])
        if error:
            return self.handle_error(ValueError(error), "set_language_preferences")
        
        user_id = arguments["user_id"]
        language = arguments["language"]
        requires_confirmation = arguments.get("requires_confirmation", True)
        
        if not await self.validate_user_access(user_id):
            return self.handle_error(
                ValueError("Invalid user access"),
                "set_language_preferences"
            )
        
        db = self.get_db_session()
        if not db:
            return self.handle_error(
                RuntimeError("Database connection failed"),
                "set_language_preferences"
            )
        
        try:
            from models import OnboardingState, AssistantProfile
            
            # Get onboarding state
            state = db.query(OnboardingState).filter(
                OnboardingState.user_id == user_id
            ).first()
            
            if not state:
                return self.handle_error(
                    ValueError("Onboarding state not found"),
                    "set_language_preferences"
                )
            
            # Create the assistant profile with all collected data
            temp_data = state.temp_data or {}
            
            assistant = AssistantProfile(
                user_id=user_id,
                name=temp_data.get("assistant_name", "Assistant"),
                avatar_url=temp_data.get("avatar_url"),
                style=temp_data.get("style", {
                    "formality": 50,
                    "directness": 50,
                    "humor": 30,
                    "empathy": 70,
                    "motivation": 60
                }),
                language=language,
                requires_confirmation=requires_confirmation,
                is_default=True
            )
            
            db.add(assistant)
            db.flush()
            
            # Update onboarding state
            state.assistant_profile_id = assistant.id
            state.last_activity = datetime.utcnow()
            
            # Mark step 4 as completed
            if 4 not in state.completed_steps:
                state.completed_steps = state.completed_steps + [4]
                state.current_step = 5
            
            db.commit()
            
            return self.format_success_response(
                {
                    "message": "Language preferences set and assistant created",
                    "assistant_id": assistant.id,
                    "language": language,
                    "current_step": state.current_step
                },
                "set_language_preferences"
            )
            
        except Exception as e:
            return self.handle_error(e, "set_language_preferences")
        finally:
            db.close()
    
    async def _select_life_areas(self, arguments: Dict) -> Dict:
        """Select life areas during onboarding."""
        error = self.validate_required_args(arguments, ["user_id", "life_area_ids"])
        if error:
            return self.handle_error(ValueError(error), "select_life_areas")
        
        user_id = arguments["user_id"]
        life_area_ids = arguments["life_area_ids"]
        custom_life_areas = arguments.get("custom_life_areas", [])
        
        if not await self.validate_user_access(user_id):
            return self.handle_error(
                ValueError("Invalid user access"),
                "select_life_areas"
            )
        
        db = self.get_db_session()
        if not db:
            return self.handle_error(
                RuntimeError("Database connection failed"),
                "select_life_areas"
            )
        
        try:
            from models import OnboardingState, LifeArea
            
            # Get onboarding state
            state = db.query(OnboardingState).filter(
                OnboardingState.user_id == user_id
            ).first()
            
            if not state:
                return self.handle_error(
                    ValueError("Onboarding state not found"),
                    "select_life_areas"
                )
            
            created_areas = []
            
            # Create custom life areas if provided
            for area_name in custom_life_areas:
                life_area = LifeArea(
                    user_id=user_id,
                    name=area_name,
                    weight=10
                )
                db.add(life_area)
                db.flush()
                created_areas.append(life_area.id)
            
            # Combine selected and created areas
            all_areas = life_area_ids + created_areas
            state.selected_life_areas = all_areas
            state.last_activity = datetime.utcnow()
            
            # Mark step 5 as completed
            if 5 not in state.completed_steps:
                state.completed_steps = state.completed_steps + [5]
                state.current_step = 6
            
            db.commit()
            
            return self.format_success_response(
                {
                    "message": "Life areas selected successfully",
                    "selected_areas": all_areas,
                    "created_areas": created_areas,
                    "current_step": state.current_step
                },
                "select_life_areas"
            )
            
        except Exception as e:
            return self.handle_error(e, "select_life_areas")
        finally:
            db.close()
    
    async def _create_first_goal(self, arguments: Dict) -> Dict:
        """Create the user's first goal during onboarding."""
        error = self.validate_required_args(arguments, ["user_id", "title"])
        if error:
            return self.handle_error(ValueError(error), "create_first_goal")
        
        user_id = arguments["user_id"]
        title = arguments["title"]
        description = arguments.get("description")
        life_area_id = arguments.get("life_area_id")
        generate_tasks = arguments.get("generate_tasks", True)
        
        if not await self.validate_user_access(user_id):
            return self.handle_error(
                ValueError("Invalid user access"),
                "create_first_goal"
            )
        
        db = self.get_db_session()
        if not db:
            return self.handle_error(
                RuntimeError("Database connection failed"),
                "create_first_goal"
            )
        
        try:
            from models import OnboardingState, Goal, Task
            
            # Get onboarding state
            state = db.query(OnboardingState).filter(
                OnboardingState.user_id == user_id
            ).first()
            
            if not state:
                return self.handle_error(
                    ValueError("Onboarding state not found"),
                    "create_first_goal"
                )
            
            # Create the goal
            goal = Goal(
                user_id=user_id,
                title=title,
                description=description,
                life_area_id=life_area_id,
                status="todo",
                progress=0.0
            )
            db.add(goal)
            db.flush()
            
            state.first_goal_id = goal.id
            
            # Create a sample first task if requested
            task_id = None
            if generate_tasks:
                first_task = Task(
                    user_id=user_id,
                    goal_id=goal.id,
                    life_area_id=life_area_id,
                    title=f"Start working on: {goal.title}",
                    description="Take the first step towards your goal",
                    status="todo",
                    progress=0.0
                )
                db.add(first_task)
                db.flush()
                
                state.first_task_id = first_task.id
                task_id = first_task.id
            
            state.last_activity = datetime.utcnow()
            
            # Mark step 6 as completed
            if 6 not in state.completed_steps:
                state.completed_steps = state.completed_steps + [6]
                state.current_step = 7  # Ready for completion
            
            db.commit()
            
            return self.format_success_response(
                {
                    "message": "First goal created successfully",
                    "goal_id": goal.id,
                    "task_id": task_id,
                    "current_step": state.current_step
                },
                "create_first_goal"
            )
            
        except Exception as e:
            return self.handle_error(e, "create_first_goal")
        finally:
            db.close()
    
    async def _complete_flow(self, arguments: Dict) -> Dict:
        """Complete onboarding flow and prepare dashboard."""
        error = self.validate_required_args(arguments, ["user_id"])
        if error:
            return self.handle_error(ValueError(error), "complete_flow")
        
        user_id = arguments["user_id"]
        
        if not await self.validate_user_access(user_id):
            return self.handle_error(
                ValueError("Invalid user access"),
                "complete_flow"
            )
        
        db = self.get_db_session()
        if not db:
            return self.handle_error(
                RuntimeError("Database connection failed"),
                "complete_flow"
            )
        
        try:
            from models import OnboardingState, AssistantProfile
            
            # Get onboarding state
            state = db.query(OnboardingState).filter(
                OnboardingState.user_id == user_id
            ).first()
            
            if not state:
                return self.handle_error(
                    ValueError("Onboarding state not found"),
                    "complete_flow"
                )
            
            # Check required steps are completed
            required_steps = [2, 3, 4, 5, 6]
            missing_steps = [s for s in required_steps if s not in state.completed_steps]
            
            if missing_steps:
                return self.handle_error(
                    ValueError(f"Cannot complete onboarding. Missing steps: {missing_steps}"),
                    "complete_flow"
                )
            
            # Mark onboarding as completed
            state.onboarding_completed = True
            state.completed_at = datetime.utcnow()
            
            # Get assistant for welcome message
            assistant = db.query(AssistantProfile).filter(
                AssistantProfile.id == state.assistant_profile_id
            ).first()
            
            welcome_message = f"Welcome! I'm {assistant.name if assistant else 'your assistant'}. "
            welcome_message += "I'm excited to help you achieve your goals. Let's get started!"
            
            db.commit()
            
            return self.format_success_response(
                {
                    "message": "Onboarding completed successfully",
                    "onboarding_completed": True,
                    "welcome_message": welcome_message,
                    "dashboard_data": {
                        "assistant_id": state.assistant_profile_id,
                        "first_goal_id": state.first_goal_id,
                        "first_task_id": state.first_task_id,
                        "life_areas": state.selected_life_areas
                    }
                },
                "complete_flow"
            )
            
        except Exception as e:
            return self.handle_error(e, "complete_flow")
        finally:
            db.close()
    
    async def _preview_personality(self, arguments: Dict) -> Dict:
        """Preview how assistant will communicate with given personality."""
        error = self.validate_required_args(arguments, ["formality", "humor", "motivation"])
        if error:
            return self.handle_error(ValueError(error), "preview_personality")
        
        formality = arguments["formality"]
        humor = arguments["humor"]
        motivation = arguments["motivation"]
        context = arguments.get("context", "greeting")
        
        # Generate sample responses based on personality
        samples = []
        
        if context == "greeting":
            if formality < 30:
                greeting = "Good day! How may I assist you today?"
            elif formality > 70:
                greeting = "Hey! What's up? How can I help?"
            else:
                greeting = "Hello! How can I help you today?"
            
            if humor > 70:
                greeting += " 😄"
            
            samples.append({"context": "greeting", "message": greeting})
        
        if context in ["encouragement", "greeting"]:
            if motivation > 70:
                encouragement = "You're doing amazing! Every step counts. Let's crush those goals! 💪"
            elif motivation < 30:
                encouragement = "Take your time. Progress is progress."
            else:
                encouragement = "Great job! Keep up the good work."
            
            samples.append({"context": "encouragement", "message": encouragement})
        
        return self.format_success_response(
            {
                "personality": {
                    "formality": formality,
                    "humor": humor,
                    "motivation": motivation
                },
                "samples": samples,
                "style_description": self._get_style_description(formality, humor, motivation)
            },
            "preview_personality"
        )
    
    def _get_style_description(self, formality: int, humor: int, motivation: int) -> str:
        """Generate a description of the personality style."""
        style_parts = []
        
        if formality < 30:
            style_parts.append("formal and professional")
        elif formality > 70:
            style_parts.append("casual and relaxed")
        else:
            style_parts.append("friendly and approachable")
        
        if humor > 70:
            style_parts.append("humorous and playful")
        elif humor < 30:
            style_parts.append("serious and focused")
        
        if motivation > 70:
            style_parts.append("highly motivating and energetic")
        elif motivation < 30:
            style_parts.append("gentle and supportive")
        else:
            style_parts.append("encouraging and positive")
        
        return f"Your assistant will be {', '.join(style_parts)}."