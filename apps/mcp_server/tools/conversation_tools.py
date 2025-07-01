"""
MCP tools for conversation and intent processing.

Provides AI agents with access to:
- Intent classification and entity extraction
- Conversation flow management
- Action execution based on intents
- Conversation analytics
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from tools.base_tools import BaseToolsHandler
from mcp import Tool, TextContent

logger = logging.getLogger(__name__)


class ConversationToolsHandler(BaseToolsHandler):
    """MCP tools for conversation and intent processing."""
    
    async def list_tools(self) -> List[Tool]:
        """List available conversation tools."""
        return [
            Tool(
                name="conversation_process_message",
                description="Process a user message with intent classification and conversation flow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID for conversation context"
                        },
                        "message": {
                            "type": "string",
                            "description": "User's natural language message"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Optional conversation session ID",
                            "optional": True
                        },
                        "include_context": {
                            "type": "boolean",
                            "description": "Include user context in classification",
                            "default": True
                        }
                    },
                    "required": ["user_id", "message"]
                }
            ),
            Tool(
                name="conversation_classify_intent",
                description="Classify intent only without conversation flow management",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to classify"
                        },
                        "include_entities": {
                            "type": "boolean",
                            "description": "Include entity extraction",
                            "default": True
                        }
                    },
                    "required": ["message"]
                }
            ),
            Tool(
                name="conversation_execute_intent",
                description="Execute an action based on classified intent and entities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID for the action"
                        },
                        "intent": {
                            "type": "string",
                            "description": "Classified intent (create_goal, create_task, etc.)"
                        },
                        "entities": {
                            "type": "object",
                            "description": "Extracted entities for the action"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence score of the intent classification"
                        }
                    },
                    "required": ["user_id", "intent", "entities"]
                }
            ),
            Tool(
                name="conversation_get_analytics",
                description="Get conversation and intent analytics for a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID for analytics"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to analyze",
                            "default": 30,
                            "minimum": 1,
                            "maximum": 365
                        },
                        "analytics_type": {
                            "type": "string",
                            "description": "Type of analytics (intent, conversation, or both)",
                            "enum": ["intent", "conversation", "both"],
                            "default": "both"
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="conversation_get_sessions",
                description="Get user's conversation sessions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of sessions to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by session status",
                            "enum": ["active", "completed", "abandoned"],
                            "optional": True
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="conversation_provide_feedback",
                description="Provide feedback on intent classification accuracy",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "conversation_log_id": {
                            "type": "integer",
                            "description": "ID of the conversation log entry to provide feedback on"
                        },
                        "original_intent": {
                            "type": "string",
                            "description": "Original classified intent"
                        },
                        "original_confidence": {
                            "type": "number",
                            "description": "Original confidence score"
                        },
                        "corrected_intent": {
                            "type": "string",
                            "description": "Corrected intent classification"
                        },
                        "feedback_type": {
                            "type": "string",
                            "description": "Type of feedback",
                            "enum": ["wrong_intent", "missing_entity", "wrong_entity"]
                        },
                        "user_comment": {
                            "type": "string",
                            "description": "Optional user comment",
                            "optional": True
                        }
                    },
                    "required": ["user_id", "conversation_log_id", "original_intent", "original_confidence", "corrected_intent", "feedback_type"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a conversation tool."""
        try:
            if name == "conversation_process_message":
                return await self._handle_process_message(arguments)
            elif name == "conversation_classify_intent":
                return await self._handle_classify_intent(arguments)
            elif name == "conversation_execute_intent":
                return await self._handle_execute_intent(arguments)
            elif name == "conversation_get_analytics":
                return await self._handle_get_analytics(arguments)
            elif name == "conversation_get_sessions":
                return await self._handle_get_sessions(arguments)
            elif name == "conversation_provide_feedback":
                return await self._handle_provide_feedback(arguments)
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown conversation tool: {name}"
                )]
        
        except Exception as e:
            logger.error(f"Error executing conversation tool {name}: {e}")
            return [TextContent(
                type="text",
                text=f"Error executing {name}: {str(e)}"
            )]
    
    async def _handle_process_message(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle message processing with intent classification and conversation flow."""
        try:
            # Import here to avoid circular imports
            from services.intent_service import ConversationFlowManager
            
            flow_manager = ConversationFlowManager()
            
            result = await flow_manager.process_message(
                user_id=arguments["user_id"],
                message=arguments["message"],
                conversation_context={
                    "session_id": arguments.get("session_id"),
                    "include_context": arguments.get("include_context", True)
                }
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "intent": result["intent_result"]["intent"],
                    "confidence": result["intent_result"]["confidence"],
                    "entities": result["intent_result"]["entities"],
                    "reasoning": result["intent_result"].get("reasoning"),
                    "fallback_used": result["intent_result"]["fallback_used"],
                    "requires_clarification": result["requires_clarification"],
                    "next_actions": result["next_actions"],
                    "session_id": result.get("session_id"),
                    "conversation_state": {
                        "turn_count": result["conversation_state"]["turn_count"],
                        "current_intent": result["conversation_state"]["current_intent"],
                        "incomplete_entities": result["conversation_state"]["incomplete_entities"]
                    }
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return [TextContent(
                type="text",
                text=f"Error processing message: {str(e)}"
            )]
    
    async def _handle_classify_intent(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle intent classification only."""
        try:
            from services.intent_service import IntentClassifier
            
            classifier = IntentClassifier()
            
            user_context = None
            if arguments.get("include_entities", True):
                user_context = {}  # Could include user preferences, etc.
            
            result = await classifier.classify_intent(arguments["message"], user_context)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "intent": result.intent,
                    "confidence": result.confidence,
                    "entities": result.entities,
                    "reasoning": result.reasoning,
                    "fallback_used": result.fallback_used
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return [TextContent(
                type="text",
                text=f"Error classifying intent: {str(e)}"
            )]
    
    async def _handle_execute_intent(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle intent execution by calling appropriate backend APIs."""
        try:
            intent = arguments["intent"]
            entities = arguments["entities"]
            user_id = arguments["user_id"]
            confidence = arguments.get("confidence", 1.0)
            
            # Route to appropriate action based on intent
            if intent == "create_goal":
                return await self._execute_create_goal(user_id, entities, confidence)
            elif intent == "create_task":
                return await self._execute_create_task(user_id, entities, confidence)
            elif intent == "create_project":
                return await self._execute_create_project(user_id, entities, confidence)
            elif intent == "update_settings":
                return await self._execute_update_settings(user_id, entities, confidence)
            elif intent == "rate_life_area":
                return await self._execute_rate_life_area(user_id, entities, confidence)
            elif intent in ["chat_continuation", "get_advice"]:
                return await self._execute_chat_response(user_id, intent, entities, confidence)
            else:
                return [TextContent(
                    type="text",
                    text=f"Intent '{intent}' execution not implemented yet. Entities: {json.dumps(entities, indent=2)}"
                )]
                
        except Exception as e:
            logger.error(f"Error executing intent: {e}")
            return [TextContent(
                type="text",
                text=f"Error executing intent: {str(e)}"
            )]
    
    async def _execute_create_goal(self, user_id: str, entities: Dict[str, Any], confidence: float) -> List[TextContent]:
        """Execute goal creation."""
        try:
            # Use the goals tools to create the goal
            from tools.goals_tools import GoalsToolsHandler
            
            goals_handler = GoalsToolsHandler()
            
            goal_data = {
                "user_id": user_id,
                "title": entities.get("title", "Untitled Goal"),
                "description": entities.get("description", ""),
                "life_area_id": None  # Would need to map life_area name to ID
            }
            
            # If we have life_area entity, we could look it up
            if "life_area" in entities:
                goal_data["description"] += f" (Life Area: {entities['life_area']})"
            
            result = await goals_handler.call_tool("goals_create", goal_data)
            
            return [TextContent(
                type="text",
                text=f"✅ Goal created successfully!\n\n{result[0].text}"
            )]
            
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error creating goal: {str(e)}"
            )]
    
    async def _execute_create_task(self, user_id: str, entities: Dict[str, Any], confidence: float) -> List[TextContent]:
        """Execute task creation."""
        try:
            # Use the tasks tools to create the task
            from tools.tasks_tools import TasksToolsHandler
            
            tasks_handler = TasksToolsHandler()
            
            task_data = {
                "user_id": user_id,
                "title": entities.get("title", "Untitled Task"),
                "description": entities.get("description", ""),
                "due_date": entities.get("due_date"),
                "priority": entities.get("priority", "medium")
            }
            
            result = await tasks_handler.call_tool("tasks_create", task_data)
            
            return [TextContent(
                type="text",
                text=f"✅ Task created successfully!\n\n{result[0].text}"
            )]
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error creating task: {str(e)}"
            )]
    
    async def _execute_create_project(self, user_id: str, entities: Dict[str, Any], confidence: float) -> List[TextContent]:
        """Execute project creation."""
        try:
            # Use the projects tools to create the project
            from tools.projects_tools import ProjectsToolsHandler
            
            projects_handler = ProjectsToolsHandler()
            
            project_data = {
                "user_id": user_id,
                "title": entities.get("title", "Untitled Project"),
                "description": entities.get("description", ""),
                "start_date": entities.get("start_date"),
                "target_date": entities.get("target_date"),
                "priority": entities.get("priority", "medium")
            }
            
            result = await projects_handler.call_tool("projects_create", project_data)
            
            return [TextContent(
                type="text",
                text=f"✅ Project created successfully!\n\n{result[0].text}"
            )]
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error creating project: {str(e)}"
            )]
    
    async def _execute_update_settings(self, user_id: str, entities: Dict[str, Any], confidence: float) -> List[TextContent]:
        """Execute settings update."""
        return [TextContent(
            type="text",
            text=f"🔧 Settings update requested for user {user_id}. Entities: {json.dumps(entities, indent=2)}\n\n(Settings update execution not yet implemented)"
        )]
    
    async def _execute_rate_life_area(self, user_id: str, entities: Dict[str, Any], confidence: float) -> List[TextContent]:
        """Execute life area rating."""
        return [TextContent(
            type="text",
            text=f"⭐ Life area rating requested for user {user_id}. Entities: {json.dumps(entities, indent=2)}\n\n(Life area rating execution not yet implemented)"
        )]
    
    async def _execute_chat_response(self, user_id: str, intent: str, entities: Dict[str, Any], confidence: float) -> List[TextContent]:
        """Execute chat response or advice."""
        if intent == "get_advice":
            return [TextContent(
                type="text",
                text=f"💡 I'd be happy to help with advice! Based on your message, here are some suggestions:\n\n(AI-powered advice generation not yet implemented)\n\nContext: {json.dumps(entities, indent=2)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"💬 I understand you'd like to continue our conversation. How can I help you today?\n\n(Enhanced conversation handling not yet implemented)\n\nContext: {json.dumps(entities, indent=2)}"
            )]
    
    async def _handle_get_analytics(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle conversation analytics request."""
        try:
            user_id = arguments["user_id"]
            days = arguments.get("days", 30)
            analytics_type = arguments.get("analytics_type", "both")
            
            # This would make API calls to the backend analytics endpoints
            analytics_data = {
                "user_id": user_id,
                "period_days": days,
                "analytics_type": analytics_type,
                "note": "Analytics data would be fetched from backend API endpoints"
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(analytics_data, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return [TextContent(
                type="text",
                text=f"Error getting analytics: {str(e)}"
            )]
    
    async def _handle_get_sessions(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle conversation sessions request."""
        try:
            user_id = arguments["user_id"]
            limit = arguments.get("limit", 10)
            status = arguments.get("status")
            
            # This would make API calls to the backend sessions endpoints
            sessions_data = {
                "user_id": user_id,
                "limit": limit,
                "status_filter": status,
                "note": "Sessions data would be fetched from backend API endpoints"
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(sessions_data, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return [TextContent(
                type="text",
                text=f"Error getting sessions: {str(e)}"
            )]
    
    async def _handle_provide_feedback(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle intent feedback submission."""
        try:
            feedback_data = {
                "user_id": arguments["user_id"],
                "conversation_log_id": arguments["conversation_log_id"],
                "original_intent": arguments["original_intent"],
                "original_confidence": arguments["original_confidence"],
                "corrected_intent": arguments["corrected_intent"],
                "feedback_type": arguments["feedback_type"],
                "user_comment": arguments.get("user_comment"),
                "note": "Feedback would be submitted to backend API"
            }
            
            return [TextContent(
                type="text",
                text=f"✅ Feedback submitted successfully!\n\n{json.dumps(feedback_data, indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Error providing feedback: {e}")
            return [TextContent(
                type="text",
                text=f"Error providing feedback: {str(e)}"
            )]