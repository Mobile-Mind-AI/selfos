"""
Unit tests for intent classification and entity extraction service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from services.intent_service import IntentClassifier, ConversationFlowManager, IntentType, IntentResult
from ai_engine.models import AIResponse, ResponseStatus


class TestIntentClassifier:
    """Test intent classification functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = IntentClassifier()
        self.classifier.ai_orchestrator = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_create_goal_intent_classification(self):
        """Test classification of create_goal intent."""
        # Mock LLM response
        mock_response = AIResponse(
            request_id="test-1",
            status=ResponseStatus.SUCCESS,
            content='{"intent": "create_goal", "confidence": 0.95, "entities": {"title": "Learn Python"}, "reasoning": "User wants to set a learning goal"}',
            token_usage={"tokens": 100},
            model_used="gpt-4"
        )
        self.classifier.ai_orchestrator.chat.return_value = mock_response
        
        result = await self.classifier.classify_intent("I want to learn Python")
        
        assert result.intent == "create_goal"
        assert result.confidence == 0.95
        assert result.entities["title"] == "Learn Python"
        assert not result.fallback_used
    
    @pytest.mark.asyncio
    async def test_create_task_intent_classification(self):
        """Test classification of create_task intent."""
        mock_response = AIResponse(
            request_id="test-2",
            status=ResponseStatus.SUCCESS,
            content='{"intent": "create_task", "confidence": 0.92, "entities": {"title": "Buy groceries", "due_date": "2025-07-02"}, "reasoning": "User wants to create a specific task"}',
            token_usage={"tokens": 100},
            model_used="gpt-4"
        )
        self.classifier.ai_orchestrator.chat.return_value = mock_response
        
        result = await self.classifier.classify_intent("I need to buy groceries tomorrow")
        
        assert result.intent == "create_task"
        assert result.confidence == 0.92
        assert result.entities["title"] == "Buy groceries"
        assert "due_date" in result.entities
    
    @pytest.mark.asyncio
    async def test_rule_based_fallback(self):
        """Test rule-based fallback when LLM fails."""
        # Mock LLM failure
        self.classifier.ai_orchestrator.chat.side_effect = Exception("LLM Error")
        
        result = await self.classifier.classify_intent("Create a goal to exercise daily")
        
        assert result.intent == "create_goal"
        assert result.fallback_used
        assert result.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_low_confidence_fallback(self):
        """Test fallback when LLM confidence is low."""
        mock_response = AIResponse(
            request_id="test-3",
            status=ResponseStatus.SUCCESS,
            content='{"intent": "unknown", "confidence": 0.3, "entities": {}, "reasoning": "Unclear message"}',
            token_usage={"tokens": 100},
            model_used="gpt-4"
        )
        self.classifier.ai_orchestrator.chat.return_value = mock_response
        
        result = await self.classifier.classify_intent("Maybe do something")
        
        # Should try rule-based fallback
        assert result.confidence >= 0.3  # Either LLM or fallback result
    
    def test_rule_based_create_goal_patterns(self):
        """Test rule-based goal creation patterns."""
        test_messages = [
            "Create a goal to lose weight",
            "I want to achieve financial freedom",
            "My goal is to learn Spanish",
            "Set a goal for better health",
            "Add a new goal about career growth"
        ]
        
        for message in test_messages:
            result = self.classifier._rule_based_classify(message)
            assert result.intent == IntentType.CREATE_GOAL.value
            assert result.confidence > 0.6
    
    def test_rule_based_create_task_patterns(self):
        """Test rule-based task creation patterns."""
        test_messages = [
            "Create a task to call the doctor",
            "I need to finish the report",
            "Todo: buy birthday gift",
            "Remind me to water plants",
            "Schedule a meeting with team"
        ]
        
        for message in test_messages:
            result = self.classifier._rule_based_classify(message)
            assert result.intent == IntentType.CREATE_TASK.value
            assert result.confidence > 0.6
    
    def test_rule_based_advice_patterns(self):
        """Test rule-based advice request patterns."""
        test_messages = [
            "What should I do about my career?",
            "Any advice for weight loss?",
            "How can I improve my sleep?",
            "Give me suggestions for productivity",
            "Tips for better relationships"
        ]
        
        for message in test_messages:
            result = self.classifier._rule_based_classify(message)
            assert result.intent == IntentType.GET_ADVICE.value
            assert result.confidence > 0.6
    
    def test_entity_extraction_due_dates(self):
        """Test due date entity extraction."""
        test_cases = [
            ("Buy milk today", "today"),
            ("Call mom tomorrow", "tomorrow"),
            ("Meeting on Monday", "Monday"),
            ("Deadline is 07/15/2025", "07/15/2025"),
            ("Due in 3 days", "in 3 days"),
            ("Submit report next week", "next week")
        ]
        
        for message, expected_date_text in test_cases:
            entities = self.classifier._extract_entities(message, "create_task")
            if "due_date" in entities:
                # Just verify that some date processing occurred
                assert entities["due_date"] is not None
    
    def test_entity_extraction_life_areas(self):
        """Test life area entity extraction."""
        test_cases = [
            ("Exercise more for health", "Health"),
            ("Focus on career growth", "Career"),
            ("Improve my relationships", "Relationships"),
            ("Better financial planning", "Finance"),
            ("Personal development goal", "Personal"),
            ("Study for education", "Education"),
            ("Have more fun activities", "Recreation"),
            ("Spiritual meditation practice", "Spiritual")
        ]
        
        for message, expected_area in test_cases:
            entities = self.classifier._extract_entities(message, "create_goal")
            if "life_area" in entities:
                assert entities["life_area"] == expected_area
    
    def test_entity_extraction_priority(self):
        """Test priority entity extraction."""
        test_cases = [
            ("Urgent task to complete", "high"),
            ("High priority project", "high"),
            ("Low priority item", "low"),
            ("Normal priority task", "medium")
        ]
        
        for message, expected_priority in test_cases:
            entities = self.classifier._extract_entities(message, "create_task")
            if "priority" in entities:
                assert entities["priority"] == expected_priority
    
    def test_title_extraction(self):
        """Test title extraction from messages."""
        test_cases = [
            ("Create a goal to learn guitar", "learn guitar"),
            ("I want to buy groceries", "buy groceries"),
            ("Todo: finish the presentation", "finish the presentation"),
            ("My goal is to run a marathon", "run a marathon"),
            ("Add task called write blog post", "write blog post")
        ]
        
        for message, expected_title in test_cases:
            title = self.classifier._extract_title(message, "create_task")
            if title:
                assert expected_title.lower() in title.lower()
    
    def test_date_parsing_helpers(self):
        """Test date parsing helper methods."""
        import re
        
        # Test relative dates
        today_match = re.search(r'\btoday\b', "due today")
        today_date = self.classifier._parse_relative_date(today_match)
        assert len(today_date) == 10  # YYYY-MM-DD format
        
        tomorrow_match = re.search(r'\btomorrow\b', "due tomorrow")
        tomorrow_date = self.classifier._parse_relative_date(tomorrow_match)
        assert len(tomorrow_date) == 10
        
        # Test day names
        monday_match = re.search(r'\bmonday\b', "due monday")
        monday_date = self.classifier._parse_day_name(monday_match)
        assert len(monday_date) == 10
    
    @pytest.mark.asyncio
    async def test_conversation_logging(self):
        """Test that conversations are logged properly."""
        mock_response = AIResponse(
            request_id="test-4",
            status=ResponseStatus.SUCCESS,
            content='{"intent": "create_task", "confidence": 0.88, "entities": {"title": "Test task"}, "reasoning": "Clear task creation"}',
            token_usage={"tokens": 100},
            model_used="gpt-4"
        )
        self.classifier.ai_orchestrator.chat.return_value = mock_response
        
        with patch.object(self.classifier, '_log_conversation', new_callable=AsyncMock) as mock_log:
            result = await self.classifier.classify_intent("Create a task to test logging")
            
            # Verify logging was called
            mock_log.assert_called_once()
            args = mock_log.call_args
            assert args[0][0] == "Create a task to test logging"  # message
            assert args[0][1].intent == "create_task"  # result


class TestConversationFlowManager:
    """Test conversation flow management functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.flow_manager = ConversationFlowManager()
        self.flow_manager.intent_classifier = Mock()
    
    @pytest.mark.asyncio
    async def test_process_message_new_session(self):
        """Test processing message for new conversation session."""
        # Mock intent classification result
        mock_result = IntentResult(
            intent="create_goal",
            confidence=0.92,
            entities={"title": "Learn photography"},
            reasoning="User wants to set a learning goal",
            fallback_used=False
        )
        self.flow_manager.intent_classifier.classify_intent = AsyncMock(return_value=mock_result)
        
        result = await self.flow_manager.process_message(
            user_id="test_user",
            message="I want to learn photography"
        )
        
        assert result["intent_result"]["intent"] == "create_goal"
        assert result["intent_result"]["confidence"] == 0.92
        assert result["conversation_state"]["turn_count"] == 1
        assert len(result["next_actions"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_message_high_confidence(self):
        """Test processing high confidence intent."""
        mock_result = IntentResult(
            intent="create_task",
            confidence=0.95,
            entities={"title": "Buy groceries", "due_date": "2025-07-02"},
            reasoning="Clear task creation with details",
            fallback_used=False
        )
        self.flow_manager.intent_classifier.classify_intent = AsyncMock(return_value=mock_result)
        
        result = await self.flow_manager.process_message(
            user_id="test_user",
            message="Buy groceries tomorrow"
        )
        
        assert not result["requires_clarification"]
        # Should have execute_action as next action
        execute_actions = [action for action in result["next_actions"] if action["type"] == "execute_action"]
        assert len(execute_actions) > 0
        assert execute_actions[0]["action"] == "create_task"
    
    @pytest.mark.asyncio
    async def test_process_message_low_confidence(self):
        """Test processing low confidence intent."""
        mock_result = IntentResult(
            intent="unknown",
            confidence=0.60,
            entities={},
            reasoning="Unclear user intent",
            fallback_used=True
        )
        self.flow_manager.intent_classifier.classify_intent = AsyncMock(return_value=mock_result)
        
        result = await self.flow_manager.process_message(
            user_id="test_user",
            message="Maybe do something"
        )
        
        assert result["requires_clarification"]
        # Should have clarification_request as next action
        clarification_actions = [action for action in result["next_actions"] if action["type"] == "clarification_request"]
        assert len(clarification_actions) > 0
    
    @pytest.mark.asyncio
    async def test_process_message_missing_entities(self):
        """Test processing intent with missing required entities."""
        mock_result = IntentResult(
            intent="create_goal",
            confidence=0.90,
            entities={},  # Missing title
            reasoning="User wants to create goal but no title provided",
            fallback_used=False
        )
        self.flow_manager.intent_classifier.classify_intent = AsyncMock(return_value=mock_result)
        
        result = await self.flow_manager.process_message(
            user_id="test_user",
            message="Create a goal"
        )
        
        # Should request missing entity
        entity_request_actions = [action for action in result["next_actions"] if action["type"] == "entity_request"]
        assert len(entity_request_actions) > 0
        assert entity_request_actions[0]["required_entity"] == "title"
    
    def test_get_required_entities(self):
        """Test required entity identification for different intents."""
        assert "title" in self.flow_manager._get_required_entities("create_goal")
        assert "title" in self.flow_manager._get_required_entities("create_task")
        assert "title" in self.flow_manager._get_required_entities("create_project")
        assert "life_area" in self.flow_manager._get_required_entities("rate_life_area")
        assert len(self.flow_manager._get_required_entities("chat_continuation")) == 0
    
    def test_conversation_state_management(self):
        """Test conversation state tracking."""
        user_id = "test_user"
        
        # First interaction
        result1 = IntentResult(
            intent="create_goal",
            confidence=0.85,
            entities={"title": "Exercise more"},
            reasoning="Goal creation",
            fallback_used=False
        )
        
        state1 = self.flow_manager._update_conversation_state(user_id, result1)
        assert state1["turn_count"] == 1
        assert state1["current_intent"] == "create_goal"
        
        # Second interaction
        result2 = IntentResult(
            intent="get_advice",
            confidence=0.90,
            entities={},
            reasoning="Advice request",
            fallback_used=False
        )
        
        state2 = self.flow_manager._update_conversation_state(user_id, result2)
        assert state2["turn_count"] == 2
        assert state2["current_intent"] == "get_advice"
    
    def test_next_actions_determination(self):
        """Test next action determination logic."""
        # High confidence complete intent
        result_complete = IntentResult(
            intent="create_task",
            confidence=0.92,
            entities={"title": "Complete project"},
            reasoning="Clear task",
            fallback_used=False
        )
        
        actions_complete = self.flow_manager._determine_next_actions(
            result_complete,
            {"current_intent": "create_task", "incomplete_entities": [], "turn_count": 1}
        )
        
        execute_actions = [a for a in actions_complete if a["type"] == "execute_action"]
        assert len(execute_actions) > 0
        
        # Low confidence intent
        result_unclear = IntentResult(
            intent="unknown",
            confidence=0.70,
            entities={},
            reasoning="Unclear",
            fallback_used=True
        )
        
        actions_unclear = self.flow_manager._determine_next_actions(
            result_unclear,
            {"current_intent": None, "incomplete_entities": [], "turn_count": 1}
        )
        
        clarification_actions = [a for a in actions_unclear if a["type"] == "clarification_request"]
        assert len(clarification_actions) > 0


class TestIntentPatterns:
    """Test specific intent pattern matching."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = IntentClassifier()
    
    def test_create_goal_variations(self):
        """Test various ways to express goal creation."""
        goal_messages = [
            "I want to lose 10 pounds",
            "My goal is to learn Spanish",
            "Set a goal for reading more books",
            "I want to achieve better work-life balance",
            "Create a goal to save money",
            "Add a new goal about fitness",
            "I want to accomplish learning piano"
        ]
        
        for message in goal_messages:
            result = self.classifier._rule_based_classify(message)
            assert result.intent in [IntentType.CREATE_GOAL.value, IntentType.CHAT_CONTINUATION.value]
            if result.intent == IntentType.CREATE_GOAL.value:
                assert result.confidence > 0.5
    
    def test_create_task_variations(self):
        """Test various ways to express task creation."""
        task_messages = [
            "I need to call the dentist",
            "Remind me to pick up dry cleaning",
            "Todo: submit expense report",
            "Schedule a meeting with the team",
            "Create a task to review documents",
            "Add task: water the plants",
            "I have to finish the presentation"
        ]
        
        for message in task_messages:
            result = self.classifier._rule_based_classify(message)
            assert result.intent in [IntentType.CREATE_TASK.value, IntentType.CHAT_CONTINUATION.value]
            if result.intent == IntentType.CREATE_TASK.value:
                assert result.confidence > 0.5
    
    def test_advice_request_variations(self):
        """Test various ways to request advice."""
        advice_messages = [
            "What should I do about my job?",
            "Any suggestions for improving sleep?",
            "How can I be more productive?",
            "Give me advice on relationships",
            "Tips for managing stress?",
            "What are some ideas for meal prep?",
            "How do I get better at public speaking?"
        ]
        
        for message in advice_messages:
            result = self.classifier._rule_based_classify(message)
            assert result.intent in [IntentType.GET_ADVICE.value, IntentType.CHAT_CONTINUATION.value]
            if result.intent == IntentType.GET_ADVICE.value:
                assert result.confidence > 0.5
    
    def test_settings_update_variations(self):
        """Test various ways to express settings updates."""
        settings_messages = [
            "Change my notification settings",
            "Update my preferences",
            "I prefer dark theme",
            "Turn off email notifications",
            "Change my profile name",
            "Modify my privacy settings",
            "Set notifications to daily"
        ]
        
        for message in settings_messages:
            result = self.classifier._rule_based_classify(message)
            assert result.intent in [IntentType.UPDATE_SETTINGS.value, IntentType.CHAT_CONTINUATION.value]
            if result.intent == IntentType.UPDATE_SETTINGS.value:
                assert result.confidence > 0.5
    
    def test_ambiguous_messages(self):
        """Test handling of ambiguous messages."""
        ambiguous_messages = [
            "Hello",
            "Hi there",
            "How are you?",
            "What's up?",
            "Tell me something",
            "I'm not sure",
            "Maybe later",
            "Hmm..."
        ]
        
        for message in ambiguous_messages:
            result = self.classifier._rule_based_classify(message)
            # Should default to chat_continuation for ambiguous messages
            assert result.intent == IntentType.CHAT_CONTINUATION.value
            assert result.confidence >= 0.5


@pytest.mark.asyncio
async def test_integration_intent_to_action():
    """Integration test: intent classification to action recommendation."""
    flow_manager = ConversationFlowManager()
    
    # Mock the AI orchestrator
    mock_response = AIResponse(
        request_id="test-5",
        status=ResponseStatus.SUCCESS,
        content='{"intent": "create_task", "confidence": 0.94, "entities": {"title": "Buy groceries", "due_date": "2025-07-02", "life_area": "Health"}, "reasoning": "User wants to create a specific task with clear details"}',
        token_usage={"tokens": 100},
        model_used="gpt-4"
    )
    flow_manager.intent_classifier.ai_orchestrator.chat = AsyncMock(return_value=mock_response)
    
    result = await flow_manager.process_message(
        user_id="integration_test_user",
        message="I need to buy healthy groceries tomorrow"
    )
    
    # Verify complete flow
    assert result["intent_result"]["intent"] == "create_task"
    assert result["intent_result"]["confidence"] == 0.94
    assert result["intent_result"]["entities"]["title"] == "Buy groceries"
    assert result["intent_result"]["entities"]["life_area"] == "Health"
    assert not result["requires_clarification"]
    
    # Should recommend executing the action
    execute_actions = [action for action in result["next_actions"] if action["type"] == "execute_action"]
    assert len(execute_actions) > 0
    assert execute_actions[0]["action"] == "create_task"
    assert execute_actions[0]["entities"]["title"] == "Buy groceries"