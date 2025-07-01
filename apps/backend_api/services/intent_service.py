"""
Intent Classification and Entity Extraction Service

Provides multi-level analysis of natural language user inputs to determine:
- User intent (create_task, create_goal, update_settings, etc.)
- Extracted entities (title, due_date, life_area, etc.)
- Confidence scores for intent classification

Supports both LLM-based classification and rule-based fallback.
"""

import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import sys
import os

# Add ai_engine to path
ai_engine_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ai_engine')
if ai_engine_path not in sys.path:
    sys.path.insert(0, ai_engine_path)

from orchestrator import AIOrchestrator

# Import ConversationRequest from AI engine models explicitly
import importlib.util
ai_models_path = os.path.join(ai_engine_path, 'models.py')
ai_models_spec = importlib.util.spec_from_file_location("ai_models", ai_models_path)
ai_models = importlib.util.module_from_spec(ai_models_spec)
ai_models_spec.loader.exec_module(ai_models)
ConversationRequest = ai_models.ConversationRequest

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Supported intent types for conversation flow."""
    CREATE_GOAL = "create_goal"
    CREATE_TASK = "create_task"
    CREATE_PROJECT = "create_project"
    UPDATE_SETTINGS = "update_settings"
    RATE_LIFE_AREA = "rate_life_area"
    CHAT_CONTINUATION = "chat_continuation"
    GET_ADVICE = "get_advice"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Result of intent classification and entity extraction."""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    reasoning: Optional[str] = None
    fallback_used: bool = False


@dataclass
class ConversationLog:
    """Log entry for conversation analysis and debugging."""
    timestamp: datetime
    user_message: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    reasoning: Optional[str]
    fallback_used: bool
    processing_time_ms: float


class IntentClassifier:
    """
    Multi-level intent classification using LLM and rule-based fallback.
    """
    
    def __init__(self):
        self.ai_orchestrator = AIOrchestrator()
        self.confidence_threshold = 0.85
        
        # Rule-based patterns for fallback
        self.intent_patterns = {
            IntentType.CREATE_GOAL: [
                r'\b(create|add|set|make|new)\s+(a\s+)?goal\b',
                r'\bgoal\s*(is|:|to)\b',
                r'\bi\s+want\s+to\s+(achieve|accomplish|reach)\b',
                r'\bmy\s+goal\s+is\b',
                r'\bset\s+a\s+goal\b'
            ],
            IntentType.CREATE_TASK: [
                r'\b(create|add|make|new)\s+(a\s+)?task\b',
                r'\btask\s*(is|:|to)\b',
                r'\bi\s+need\s+to\s+(do|complete|finish)\b',
                r'\btodo\s*:\s*\b',
                r'\bremind\s+me\s+to\b',
                r'\bschedule\s+(a\s+)?(meeting|call|appointment)\b'
            ],
            IntentType.CREATE_PROJECT: [
                r'\b(create|start|begin|new)\s+(a\s+)?project\b',
                r'\bproject\s*(is|:|to)\b',
                r'\bworking\s+on\s+a\s+project\b',
                r'\bproject\s+called\b'
            ],
            IntentType.UPDATE_SETTINGS: [
                r'\b(change|update|modify|set)\s+settings\b',
                r'\bpreferences\s+(to|for)\b',
                r'\bi\s+prefer\b',
                r'\bchange\s+my\s+(name|email|theme)\b',
                r'\bnotifications?\s+(on|off|enable|disable)\b'
            ],
            IntentType.RATE_LIFE_AREA: [
                r'\brate\s+(my\s+)?\w+\s+area\b',
                r'\b(health|career|relationships?|finance|personal)\s+(is|rate|score)\b',
                r'\bgive\s+\w+\s+a\s+rating\b',
                r'\bhow\s+(good|bad)\s+is\s+my\s+\w+\b'
            ],
            IntentType.GET_ADVICE: [
                r'\b(advice|suggestion|help|guidance|recommend)\b',
                r'\bwhat\s+should\s+i\s+(do|try)\b',
                r'\bhow\s+(can|do)\s+i\s+\w+\b',
                r'\bany\s+ideas\s+(for|about)\b',
                r'\btips\s+(for|on)\b'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'due_date': [
                (r'\b(today|tomorrow)\b', self._parse_relative_date),
                (r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', self._parse_day_name),
                (r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', self._parse_date_format),
                (r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b', self._parse_date_format),
                (r'\bin\s+(\d+)\s+(days?|weeks?|months?)\b', self._parse_relative_duration),
                (r'\b(next|this)\s+(week|month|year)\b', self._parse_relative_period)
            ],
            'life_area': [
                (r'\b(health|fitness|exercise|diet|wellness)\b', 'Health'),
                (r'\b(career|work|job|professional|business)\b', 'Career'),
                (r'\b(family|friends|relationship|social|love)\b', 'Relationships'),
                (r'\b(money|finance|financial|budget|savings?)\b', 'Finance'),
                (r'\b(personal|self|growth|development|learning)\b', 'Personal'),
                (r'\b(education|study|school|university|course)\b', 'Education'),
                (r'\b(hobby|hobbies|fun|entertainment|leisure)\b', 'Recreation'),
                (r'\b(spiritual|religion|meditation|mindfulness)\b', 'Spiritual')
            ],
            'priority': [
                (r'\b(urgent|critical|asap|immediately)\b', 'high'),
                (r'\b(important|high)\s+priority\b', 'high'),
                (r'\b(low|minor)\s+priority\b', 'low'),
                (r'\b(normal|medium|regular)\s+priority\b', 'medium')
            ],
            'duration': [
                (r'\b(\d+)\s+(minutes?|mins?|hours?|days?)\b', self._parse_duration)
            ]
        }

    async def classify_intent(self, message: str, user_context: Optional[Dict] = None,
                             assistant_profile: Optional[Any] = None) -> IntentResult:
        """
        Classify user intent using LLM with rule-based fallback.
        
        Args:
            message: User's natural language input
            user_context: Optional context about user (preferences, recent activity)
            assistant_profile: Optional assistant personality profile
            
        Returns:
            IntentResult with intent, confidence, and extracted entities
        """
        start_time = datetime.now()
        
        try:
            # Try LLM-based classification first
            result = await self._llm_classify(message, user_context, assistant_profile)
            
            # If confidence is low, try rule-based fallback
            if result.confidence < self.confidence_threshold:
                logger.info(f"LLM confidence {result.confidence:.2f} below threshold, trying rule-based fallback")
                fallback_result = self._rule_based_classify(message)
                
                # Use fallback if it has higher confidence
                if fallback_result.confidence > result.confidence:
                    result = fallback_result
                    result.fallback_used = True
        
        except Exception as e:
            logger.error(f"LLM classification failed: {e}, falling back to rules")
            result = self._rule_based_classify(message)
            result.fallback_used = True
        
        # Extract entities
        result.entities.update(self._extract_entities(message, result.intent))
        
        # Log the conversation
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        await self._log_conversation(message, result, processing_time)
        
        return result

    async def _llm_classify(self, message: str, user_context: Optional[Dict] = None, assistant_profile: Optional[Any] = None) -> IntentResult:
        """Use LLM for intent classification and entity extraction."""
        
        system_prompt = self._build_classification_prompt(user_context)
        
        # Use assistant-specific temperature if available
        intent_temperature = 0.1  # Default low temperature for consistent classification
        if assistant_profile and hasattr(assistant_profile, 'intent_temperature'):
            intent_temperature = assistant_profile.intent_temperature
        
        # Create conversation request for AI orchestrator
        full_prompt = f"{system_prompt}\n\nUser: {message}"
        conversation_request = ConversationRequest(
            user_id="intent_classifier",  # Special identifier for intent classification
            prompt=full_prompt,
            message=message,
            temperature=intent_temperature,
            max_tokens=500
        )
        
        response = await self.ai_orchestrator.chat(conversation_request)
        
        try:
            result_data = json.loads(response.content)
            return IntentResult(
                intent=result_data.get("intent", "unknown"),
                confidence=float(result_data.get("confidence", 0.0)),
                entities=result_data.get("entities", {}),
                reasoning=result_data.get("reasoning"),
                fallback_used=False
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return IntentResult(
                intent="unknown",
                confidence=0.0,
                entities={},
                reasoning=f"Parse error: {e}",
                fallback_used=False
            )

    def _rule_based_classify(self, message: str) -> IntentResult:
        """Rule-based fallback classification."""
        message_lower = message.lower()
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        for intent_type, patterns in self.intent_patterns.items():
            confidence = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    matches += 1
                    confidence = min(0.95, 0.7 + (matches * 0.1))  # Max 0.95 for rule-based
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent_type
        
        # Default to chat if no strong pattern match
        if best_confidence < 0.5:
            best_intent = IntentType.CHAT_CONTINUATION
            best_confidence = 0.6
        
        return IntentResult(
            intent=best_intent.value,
            confidence=best_confidence,
            entities={},
            reasoning=f"Rule-based match for {best_intent.value}",
            fallback_used=True
        )

    def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """Extract entities from message using regex patterns."""
        entities = {}
        message_lower = message.lower()
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern, parser in patterns:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    if callable(parser):
                        entities[entity_type] = parser(match)
                    else:
                        entities[entity_type] = parser
                    break  # Use first match for each entity type
        
        # Extract title/description (everything after intent keywords)
        if intent in ['create_goal', 'create_task', 'create_project']:
            title = self._extract_title(message, intent)
            if title:
                entities['title'] = title
        
        return entities

    def _extract_title(self, message: str, intent: str) -> Optional[str]:
        """Extract title/description from create intent messages."""
        # Remove common intent keywords and extract remaining content
        patterns_to_remove = [
            r'\b(create|add|make|new|set)\s+(a\s+)?(goal|task|project)\s*(is|to|:|called)?\s*',
            r'\bi\s+(want|need)\s+to\s+',
            r'\bmy\s+(goal|task)\s+is\s+',
            r'\btodo\s*:\s*',
            r'\bremind\s+me\s+to\s+'
        ]
        
        cleaned = message
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()
        
        # Remove leading/trailing punctuation
        cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', cleaned).strip()
        
        return cleaned if len(cleaned) > 2 else None

    def _parse_relative_date(self, match) -> str:
        """Parse relative dates like 'today', 'tomorrow'."""
        word = match.group(0).lower()
        if word == 'today':
            return datetime.now().strftime('%Y-%m-%d')
        elif word == 'tomorrow':
            return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        return word

    def _parse_day_name(self, match) -> str:
        """Parse day names like 'monday', 'friday'."""
        day_name = match.group(0).lower()
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        if day_name in days:
            today = datetime.now()
            target_day = days.index(day_name)
            current_day = today.weekday()
            
            days_ahead = target_day - current_day
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            target_date = today + timedelta(days=days_ahead)
            return target_date.strftime('%Y-%m-%d')
        
        return day_name

    def _parse_date_format(self, match) -> str:
        """Parse date formats like MM/DD/YYYY or MM-DD-YYYY."""
        try:
            if len(match.groups()) == 3:
                month, day, year = match.groups()
                date = datetime(int(year), int(month), int(day))
                return date.strftime('%Y-%m-%d')
        except ValueError:
            pass
        return match.group(0)

    def _parse_relative_duration(self, match) -> str:
        """Parse relative durations like 'in 3 days', 'in 2 weeks'."""
        try:
            amount = int(match.group(1))
            unit = match.group(2).lower()
            
            if unit.startswith('day'):
                target_date = datetime.now() + timedelta(days=amount)
            elif unit.startswith('week'):
                target_date = datetime.now() + timedelta(weeks=amount)
            elif unit.startswith('month'):
                target_date = datetime.now() + timedelta(days=amount * 30)  # Approximation
            else:
                return match.group(0)
            
            return target_date.strftime('%Y-%m-%d')
        except ValueError:
            return match.group(0)

    def _parse_relative_period(self, match) -> str:
        """Parse relative periods like 'next week', 'this month'."""
        modifier = match.group(1).lower()
        period = match.group(2).lower()
        
        today = datetime.now()
        
        if period == 'week':
            if modifier == 'next':
                target_date = today + timedelta(weeks=1)
            else:  # 'this'
                target_date = today + timedelta(days=(6 - today.weekday()))
        elif period == 'month':
            if modifier == 'next':
                if today.month == 12:
                    target_date = datetime(today.year + 1, 1, 1)
                else:
                    target_date = datetime(today.year, today.month + 1, 1)
            else:  # 'this'
                target_date = datetime(today.year, today.month, 28)  # End of month approximation
        else:
            return match.group(0)
        
        return target_date.strftime('%Y-%m-%d')

    def _parse_duration(self, match) -> str:
        """Parse durations like '30 minutes', '2 hours'."""
        amount = match.group(1)
        unit = match.group(2).lower()
        return f"{amount} {unit}"

    def _build_classification_prompt(self, user_context: Optional[Dict] = None) -> str:
        """Build system prompt for LLM classification."""
        context_info = ""
        if user_context:
            context_info = f"""
User Context:
- Recent activity: {user_context.get('recent_activity', 'None')}
- Preferences: {user_context.get('preferences', {})}
- Life areas: {user_context.get('life_areas', [])}
"""

        return f"""You are an intent classification system for SelfOS, a personal productivity assistant.

Analyze the user's message and return a JSON response with:
1. Intent classification (one of: create_goal, create_task, create_project, update_settings, rate_life_area, chat_continuation, get_advice, unknown)
2. Confidence score (0.0 to 1.0)
3. Extracted entities relevant to the intent
4. Brief reasoning for your classification

{context_info}

Intent Definitions:
- create_goal: User wants to set a new goal or objective
- create_task: User wants to add a specific task or to-do item
- create_project: User wants to start a new project (collection of related goals/tasks)
- update_settings: User wants to modify preferences, notifications, or account settings
- rate_life_area: User wants to rate or evaluate a life area (health, career, relationships, etc.)
- chat_continuation: General conversation or follow-up questions
- get_advice: User is asking for suggestions, tips, or guidance
- unknown: Cannot determine intent with confidence

Entity Types to Extract:
- title: Main content/description for goals/tasks/projects
- due_date: Date information (format as YYYY-MM-DD)
- life_area: Health, Career, Relationships, Finance, Personal, Education, Recreation, Spiritual
- priority: high, medium, low
- duration: Time estimates for tasks
- settings: Any preference or configuration mentions

Response Format:
{{
  "intent": "create_task",
  "confidence": 0.96,
  "entities": {{
    "title": "Buy dumbbells",
    "life_area": "Health",
    "due_date": "2025-07-02"
  }},
  "reasoning": "User clearly wants to create a task with specific item and health context"
}}

Be conservative with confidence scores. Use confidence < 0.85 for ambiguous messages."""

    async def _log_conversation(self, message: str, result: IntentResult, processing_time: float):
        """Log conversation for debugging and tuning."""
        log_entry = ConversationLog(
            timestamp=datetime.now(),
            user_message=message,
            intent=result.intent,
            confidence=result.confidence,
            entities=result.entities,
            reasoning=result.reasoning,
            fallback_used=result.fallback_used,
            processing_time_ms=processing_time
        )
        
        # Log to system logger
        logger.info(f"Intent classified: {result.intent} (confidence: {result.confidence:.2f}, "
                   f"fallback: {result.fallback_used}, time: {processing_time:.1f}ms)")
        
        # TODO: Store in database for analytics and model improvement
        # This could be stored in a conversation_logs table for analysis


class ConversationFlowManager:
    """
    Manages conversation flow and context for multi-turn interactions.
    """
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.active_conversations: Dict[str, Dict] = {}  # user_id -> conversation state
    
    async def process_message(self, user_id: str, message: str, 
                            conversation_context: Optional[Dict] = None,
                            assistant_profile: Optional[Any] = None) -> Dict[str, Any]:
        """
        Process a user message with conversation flow management.
        
        Args:
            user_id: Unique user identifier
            message: User's message
            conversation_context: Optional conversation history/context
            assistant_profile: Optional assistant personality profile
            
        Returns:
            Dict with intent result and next action recommendations
        """
        # Get user context for better classification
        user_context = await self._get_user_context(user_id)
        
        # Add assistant profile context if available
        if assistant_profile:
            user_context["assistant_profile"] = {
                "id": assistant_profile.id,
                "style": assistant_profile.style,
                "language": assistant_profile.language,
                "intent_temperature": assistant_profile.intent_temperature
            }
        
        # Classify intent with assistant-specific temperature
        result = await self.intent_classifier.classify_intent(
            message, 
            user_context, 
            assistant_profile=assistant_profile
        )
        
        # Update conversation state
        conversation_state = self._update_conversation_state(user_id, result)
        
        # Determine next actions based on intent and confidence
        next_actions = self._determine_next_actions(result, conversation_state)
        
        return {
            "intent_result": asdict(result),
            "conversation_state": conversation_state,
            "next_actions": next_actions,
            "requires_clarification": result.confidence < 0.85
        }
    
    async def _get_user_context(self, user_id: str) -> Dict:
        """Get user context for better intent classification."""
        # TODO: Implement user context retrieval
        # This would fetch user's recent activity, preferences, life areas, etc.
        return {
            "recent_activity": [],
            "preferences": {},
            "life_areas": []
        }
    
    def _update_conversation_state(self, user_id: str, result: IntentResult) -> Dict:
        """Update conversation state for multi-turn interactions."""
        if user_id not in self.active_conversations:
            self.active_conversations[user_id] = {
                "current_intent": None,
                "incomplete_entities": {},
                "turn_count": 0,
                "last_update": datetime.now()
            }
        
        state = self.active_conversations[user_id]
        state["current_intent"] = result.intent
        state["turn_count"] += 1
        state["last_update"] = datetime.now()
        
        # Track incomplete entities for follow-up questions
        required_entities = self._get_required_entities(result.intent)
        missing_entities = [entity for entity in required_entities 
                          if entity not in result.entities]
        state["incomplete_entities"] = missing_entities
        
        return state
    
    def _get_required_entities(self, intent: str) -> List[str]:
        """Get required entities for each intent type."""
        entity_requirements = {
            "create_goal": ["title"],
            "create_task": ["title"],
            "create_project": ["title"],
            "update_settings": [],
            "rate_life_area": ["life_area"],
            "chat_continuation": [],
            "get_advice": [],
            "unknown": []
        }
        return entity_requirements.get(intent, [])
    
    def _determine_next_actions(self, result: IntentResult, conversation_state: Dict) -> List[Dict]:
        """Determine next actions based on intent and conversation state."""
        actions = []
        
        if result.confidence < 0.85:
            actions.append({
                "type": "clarification_request",
                "message": "I'm not sure what you'd like to do. Could you please be more specific?",
                "suggested_intents": ["create_goal", "create_task", "get_advice"]
            })
        
        elif result.intent in ["create_goal", "create_task", "create_project"]:
            if "title" not in result.entities:
                actions.append({
                    "type": "entity_request",
                    "message": f"What would you like to call this {result.intent.split('_')[1]}?",
                    "required_entity": "title"
                })
            else:
                actions.append({
                    "type": "execute_action",
                    "action": result.intent,
                    "entities": result.entities
                })
        
        elif result.intent == "get_advice":
            actions.append({
                "type": "provide_advice",
                "context": result.entities
            })
        
        elif result.intent == "chat_continuation":
            actions.append({
                "type": "continue_conversation",
                "context": conversation_state
            })
        
        return actions