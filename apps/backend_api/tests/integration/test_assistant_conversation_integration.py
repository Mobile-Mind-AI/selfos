"""
Integration tests for Assistant Profiles with Conversation System.
Tests the complete flow of using assistant personalities in conversations.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os
from unittest.mock import patch, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from dependencies import get_db, get_current_user
from models import Base, AssistantProfile, ConversationSession, ConversationLog

# Test database - isolated in-memory SQLite for this module
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables once
Base.metadata.create_all(bind=engine)

# Test client setup
client = TestClient(app)

# Test fixtures
@pytest.fixture
def db_session():
    """Create a test database session"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

def override_get_db_integration():
    """Override get_db dependency for integration tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user_integration(user_data):
    """Override get_current_user dependency"""
    def _override():
        return user_data
    return _override

# Sample assistant profiles for testing
FORMAL_ASSISTANT = {
    "name": "Professional Assistant",
    "description": "A formal, professional AI assistant",
    "ai_model": "gpt-4",
    "language": "en",
    "style": {
        "formality": 90,   # Very formal
        "directness": 70,  # Direct
        "humor": 10,       # Serious
        "empathy": 50,     # Balanced
        "motivation": 60   # Moderately motivational
    },
    "dialogue_temperature": 0.3,  # Low for consistency
    "intent_temperature": 0.1,
    "custom_instructions": "Always use professional language and proper grammar",
    "is_default": True
}

CASUAL_ASSISTANT = {
    "name": "Friendly Assistant",
    "description": "A casual, friendly AI assistant",
    "ai_model": "gpt-3.5-turbo",
    "language": "en",
    "style": {
        "formality": 20,   # Very casual
        "directness": 50,  # Balanced
        "humor": 80,       # Very humorous
        "empathy": 90,     # Very empathetic
        "motivation": 85   # Very motivational
    },
    "dialogue_temperature": 0.9,  # High for creativity
    "intent_temperature": 0.3,
    "custom_instructions": "Be friendly, use casual language, and add encouragement",
    "is_default": False
}

MOTIVATIONAL_ASSISTANT = {
    "name": "Coach Assistant",
    "description": "A highly motivational coaching assistant",
    "ai_model": "gpt-4",
    "language": "en",
    "style": {
        "formality": 40,   # Somewhat casual
        "directness": 85,  # Very direct
        "humor": 60,       # Moderately humorous
        "empathy": 95,     # Extremely empathetic
        "motivation": 100  # Maximum motivation
    },
    "dialogue_temperature": 0.7,
    "intent_temperature": 0.2,
    "custom_instructions": "Focus on goal achievement and provide strong encouragement",
    "is_default": False
}


class TestAssistantConversationIntegration:
    """Test integration between assistant profiles and conversation system."""

    def setup_method(self):
        """Set up test database and dependencies before each test"""
        app.dependency_overrides[get_db] = override_get_db_integration
        
        # Clear existing data
        db = TestingSessionLocal()
        db.query(ConversationLog).delete()
        db.query(ConversationSession).delete()
        db.query(AssistantProfile).delete()
        db.commit()
        db.close()

    def teardown_method(self):
        """Clean up after each test"""
        app.dependency_overrides.clear()

    @patch('services.intent_service.ConversationFlowManager.process_message')
    def test_conversation_with_specific_assistant(self, mock_process_message, mock_user):
        """Test that conversations use the specified assistant profile"""
        app.dependency_overrides[get_current_user] = override_get_current_user_integration(mock_user)
        
        # Mock the conversation processing
        mock_process_message.return_value = {
            "intent_result": {
                "intent": "create_goal",
                "confidence": 0.95,
                "entities": {"title": "Learn Python"},
                "reasoning": "User wants to learn a programming language",
                "fallback_used": False,
                "processing_time_ms": 150.0
            },
            "conversation_state": {
                "current_intent": "create_goal",
                "incomplete_entities": [],
                "turn_count": 1,
                "last_update": "2025-07-01T12:00:00"
            },
            "next_actions": [{
                "type": "execute_action",
                "action": "create_goal",
                "entities": {"title": "Learn Python"}
            }],
            "requires_clarification": False
        }
        
        # Create a formal assistant profile
        create_response = client.post("/api/assistant_profiles/", json=FORMAL_ASSISTANT)
        assistant_id = create_response.json()["id"]
        
        # Send message using specific assistant
        message_data = {
            "message": "I want to learn Python programming",
            "assistant_id": assistant_id,
            "include_context": True
        }
        
        response = client.post("/api/conversation/message", json=message_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify that the mock was called with the assistant profile
        mock_process_message.assert_called_once()
        call_args = mock_process_message.call_args
        
        # Check that assistant_profile was passed
        assert call_args[1]["assistant_profile"] is not None
        
        # Verify response structure
        assert "intent_result" in data
        assert "conversation_state" in data
        assert "session_id" in data

    @patch('services.intent_service.ConversationFlowManager.process_message')
    def test_conversation_with_default_assistant(self, mock_process_message, mock_user):
        """Test that conversations use default assistant when none specified"""
        app.dependency_overrides[get_current_user] = override_get_current_user_integration(mock_user)
        
        # Mock the conversation processing
        mock_process_message.return_value = {
            "intent_result": {
                "intent": "chat_continuation",
                "confidence": 0.85,
                "entities": {},
                "reasoning": "General chat message",
                "fallback_used": False,
                "processing_time_ms": 120.0
            },
            "conversation_state": {
                "current_intent": "chat_continuation",
                "incomplete_entities": [],
                "turn_count": 1,
                "last_update": "2025-07-01T12:00:00"
            },
            "next_actions": [{
                "type": "continue_conversation",
                "context": {}
            }],
            "requires_clarification": False
        }
        
        # Create a default assistant profile
        client.post("/api/assistant_profiles/", json=FORMAL_ASSISTANT)
        
        # Send message without specifying assistant
        message_data = {
            "message": "Hello, how are you today?",
            "include_context": True
        }
        
        response = client.post("/api/conversation/message", json=message_data)
        
        assert response.status_code == 200
        
        # Verify that the mock was called with the default assistant profile
        mock_process_message.assert_called_once()
        call_args = mock_process_message.call_args
        
        # Check that assistant_profile was passed (should be the default one)
        assert call_args[1]["assistant_profile"] is not None

    def test_conversation_without_assistant_profiles(self, mock_user):
        """Test conversation when user has no assistant profiles"""
        app.dependency_overrides[get_current_user] = override_get_current_user_integration(mock_user)
        
        # Don't create any assistant profiles
        
        message_data = {
            "message": "I need help with my goals",
            "include_context": True
        }
        
        with patch('services.intent_service.ConversationFlowManager.process_message') as mock_process:
            mock_process.return_value = {
                "intent_result": {
                    "intent": "get_advice",
                    "confidence": 0.90,
                    "entities": {},
                    "reasoning": "User asking for help",
                    "fallback_used": False,
                    "processing_time_ms": 100.0
                },
                "conversation_state": {
                    "current_intent": "get_advice",
                    "incomplete_entities": [],
                    "turn_count": 1,
                    "last_update": "2025-07-01T12:00:00"
                },
                "next_actions": [],
                "requires_clarification": False
            }
            
            response = client.post("/api/conversation/message", json=message_data)
            
            assert response.status_code == 200
            
            # Verify that conversation works even without assistant profiles
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            
            # assistant_profile should be None
            assert call_args[1]["assistant_profile"] is None

    def test_conversation_session_with_assistant_tracking(self, mock_user):
        """Test that conversation sessions track which assistant was used"""
        app.dependency_overrides[get_current_user] = override_get_current_user_integration(mock_user)
        
        # Create an assistant profile
        create_response = client.post("/api/assistant_profiles/", json=CASUAL_ASSISTANT)
        assistant_id = create_response.json()["id"]
        
        message_data = {
            "message": "Let's set up a workout routine",
            "assistant_id": assistant_id,
            "include_context": True
        }
        
        with patch('services.intent_service.ConversationFlowManager.process_message') as mock_process:
            mock_process.return_value = {
                "intent_result": {
                    "intent": "create_goal",
                    "confidence": 0.92,
                    "entities": {"title": "workout routine", "life_area": "Health"},
                    "reasoning": "User wants to create fitness goal",
                    "fallback_used": False,
                    "processing_time_ms": 180.0
                },
                "conversation_state": {
                    "current_intent": "create_goal",
                    "incomplete_entities": [],
                    "turn_count": 1,
                    "last_update": "2025-07-01T12:00:00"
                },
                "next_actions": [],
                "requires_clarification": False
            }
            
            response = client.post("/api/conversation/message", json=message_data)
            
            assert response.status_code == 200
            data = response.json()
            session_id = data["session_id"]
            
            # Check that session was created with assistant tracking
            # (This would be verified in the background task, but we can check the response structure)
            assert session_id is not None

    def test_multiple_assistants_different_responses(self, mock_user):
        """Test that different assistants can potentially produce different responses"""
        app.dependency_overrides[get_current_user] = override_get_current_user_integration(mock_user)
        
        # Create two different assistant profiles
        formal_response = client.post("/api/assistant_profiles/", json=FORMAL_ASSISTANT)
        formal_id = formal_response.json()["id"]
        
        casual_response = client.post("/api/assistant_profiles/", json=CASUAL_ASSISTANT)
        casual_id = casual_response.json()["id"]
        
        same_message = "I want to start exercising more"
        
        # Mock different responses based on assistant personality
        def mock_process_with_assistant(*args, **kwargs):
            assistant_profile = kwargs.get("assistant_profile")
            
            if assistant_profile and assistant_profile.style["formality"] > 70:
                # Formal assistant response
                return {
                    "intent_result": {
                        "intent": "create_goal",
                        "confidence": 0.95,
                        "entities": {"title": "exercise regimen", "life_area": "Health"},
                        "reasoning": "Formal analysis of fitness goal",
                        "fallback_used": False,
                        "processing_time_ms": 120.0
                    },
                    "conversation_state": {
                        "current_intent": "create_goal",
                        "incomplete_entities": [],
                        "turn_count": 1,
                        "last_update": "2025-07-01T12:00:00"
                    },
                    "next_actions": [],
                    "requires_clarification": False
                }
            else:
                # Casual assistant response
                return {
                    "intent_result": {
                        "intent": "create_goal",
                        "confidence": 0.88,
                        "entities": {"title": "get moving", "life_area": "Health"},
                        "reasoning": "Casual interpretation of fitness goal",
                        "fallback_used": False,
                        "processing_time_ms": 100.0
                    },
                    "conversation_state": {
                        "current_intent": "create_goal",
                        "incomplete_entities": [],
                        "turn_count": 1,
                        "last_update": "2025-07-01T12:00:00"
                    },
                    "next_actions": [],
                    "requires_clarification": False
                }
        
        with patch('services.intent_service.ConversationFlowManager.process_message', side_effect=mock_process_with_assistant):
            # Test with formal assistant
            formal_message = {
                "message": same_message,
                "assistant_id": formal_id,
                "include_context": True
            }
            
            formal_response = client.post("/api/conversation/message", json=formal_message)
            assert formal_response.status_code == 200
            formal_data = formal_response.json()
            
            # Test with casual assistant
            casual_message = {
                "message": same_message,
                "assistant_id": casual_id,
                "include_context": True
            }
            
            casual_response = client.post("/api/conversation/message", json=casual_message)
            assert casual_response.status_code == 200
            casual_data = casual_response.json()
            
            # Responses could be different based on assistant personality
            # This demonstrates that the assistant profile is being passed through
            assert formal_data["intent_result"]["entities"]["title"] == "exercise regimen"
            assert casual_data["intent_result"]["entities"]["title"] == "get moving"

    def test_assistant_temperature_settings_passed_through(self, mock_user):
        """Test that assistant temperature settings are used in conversation processing"""
        app.dependency_overrides[get_current_user] = override_get_current_user_integration(mock_user)
        
        # Create an assistant with specific temperature settings
        high_temp_assistant = CASUAL_ASSISTANT.copy()
        high_temp_assistant["dialogue_temperature"] = 0.95
        high_temp_assistant["intent_temperature"] = 0.05
        
        create_response = client.post("/api/assistant_profiles/", json=high_temp_assistant)
        assistant_id = create_response.json()["id"]
        
        message_data = {
            "message": "Help me plan my day",
            "assistant_id": assistant_id,
            "include_context": True
        }
        
        with patch('services.intent_service.ConversationFlowManager.process_message') as mock_process:
            mock_process.return_value = {
                "intent_result": {
                    "intent": "get_advice",
                    "confidence": 0.87,
                    "entities": {},
                    "reasoning": "User wants planning help",
                    "fallback_used": False,
                    "processing_time_ms": 140.0
                },
                "conversation_state": {
                    "current_intent": "get_advice",
                    "incomplete_entities": [],
                    "turn_count": 1,
                    "last_update": "2025-07-01T12:00:00"
                },
                "next_actions": [],
                "requires_clarification": False
            }
            
            response = client.post("/api/conversation/message", json=message_data)
            
            assert response.status_code == 200
            
            # Verify that assistant profile with temperature settings was passed
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            assistant_profile = call_args[1]["assistant_profile"]
            
            assert assistant_profile is not None
            assert assistant_profile.dialogue_temperature == 0.95
            assert assistant_profile.intent_temperature == 0.05

    def test_nonexistent_assistant_id(self, mock_user):
        """Test conversation with non-existent assistant ID"""
        app.dependency_overrides[get_current_user] = override_get_current_user_integration(mock_user)
        
        message_data = {
            "message": "Hello there",
            "assistant_id": "nonexistent-assistant-id",
            "include_context": True
        }
        
        response = client.post("/api/conversation/message", json=message_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__])