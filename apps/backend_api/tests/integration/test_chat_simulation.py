"""
Chat Simulation Integration Tests

Comprehensive tests that simulate realistic chat conversations and workflows
with the AI system, including multi-turn conversations, context awareness,
and integration with memory and goal systems.
"""

import pytest
from fastapi.testclient import TestClient
import json
import time

from main import app
# get_test_user_headers is available from conftest.py fixture


client = TestClient(app)


class TestChatSimulation:
    """Realistic chat conversation simulation tests."""
    
    def test_new_user_onboarding_chat(self, get_test_user_headers):
        """Simulate a new user's first conversation about setting goals."""
        headers = get_test_user_headers
        conversation_history = []
        
        # User's first message - vague goal
        user_message = "Hi, I want to improve my life but I'm not sure where to start"
        
        chat_request = {
            "message": user_message,
            "conversation_history": conversation_history,
            "user_context": {"new_user": True}
        }
        
        response = client.post("/api/ai/chat", headers=headers, json=chat_request)
        assert response.status_code == 200
        
        ai_response = response.json()
        assert ai_response["status"] == "success"
        assert len(ai_response["content"]) > 0
        
        # AI should ask clarifying questions
        assert len(ai_response["follow_up_questions"]) > 0
        
        # Update conversation history
        conversation_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response["content"]}
        ])
        
        # User provides more specific information
        user_message2 = "I want to focus on my health and maybe learn a new skill"
        
        chat_request2 = {
            "message": user_message2,
            "conversation_history": conversation_history,
            "user_context": {"new_user": True}
        }
        
        response2 = client.post("/api/ai/chat", headers=headers, json=chat_request2)
        assert response2.status_code == 200
        
        ai_response2 = response2.json()
        assert ai_response2["status"] == "success"
        
        # AI should provide more specific guidance
        content_lower = ai_response2["content"].lower()
        assert any(word in content_lower for word in ["health", "skill", "goal", "specific"])
    
    def test_goal_clarification_conversation(self, get_test_user_headers):
        """Simulate conversation about clarifying a vague goal."""
        headers = get_test_user_headers
        
        conversation_flow = [
            {
                "user": "I want to get better at cooking",
                "expected_keywords": ["cooking", "specific", "what", "type"]
            },
            {
                "user": "I want to learn Italian cooking, especially pasta dishes",
                "expected_keywords": ["italian", "pasta", "recipes", "practice"]
            },
            {
                "user": "I have about 2 hours per week to dedicate to this",
                "expected_keywords": ["time", "schedule", "practice", "realistic"]
            }
        ]
        
        conversation_history = []
        
        for turn in conversation_flow:
            chat_request = {
                "message": turn["user"],
                "conversation_history": conversation_history,
                "user_context": {"goal_type": "skill_learning"}
            }
            
            response = client.post("/api/ai/chat", headers=headers, json=chat_request)
            assert response.status_code == 200
            
            ai_response = response.json()
            assert ai_response["status"] == "success"
            
            # Check if AI response contains expected concepts
            content_lower = ai_response["content"].lower()
            has_expected = any(keyword in content_lower for keyword in turn["expected_keywords"])
            assert has_expected, f"Expected keywords {turn['expected_keywords']} not found in: {ai_response['content']}"
            
            # Update conversation history
            conversation_history.extend([
                {"role": "user", "content": turn["user"]},
                {"role": "assistant", "content": ai_response["content"]}
            ])
            
            # Conversation should maintain context
            assert len(conversation_history) == (conversation_flow.index(turn) + 1) * 2
    
    def test_goal_to_tasks_conversation_flow(self, get_test_user_headers):
        """Simulate flow from goal setting to task creation."""
        headers = get_test_user_headers
        
        # Step 1: User states a goal
        goal_message = "I want to run a 5K race in 3 months"
        
        chat_request = {
            "message": goal_message,
            "conversation_history": [],
            "user_context": {"fitness_level": "beginner"}
        }
        
        response = client.post("/api/ai/chat", headers=headers, json=chat_request)
        assert response.status_code == 200
        
        ai_response = response.json()
        assert ai_response["status"] == "success"
        
        # Should detect goal-setting intent
        assert ai_response["intent_detected"] in ["goal_setting", None]  # None is acceptable for mock
        
        conversation_history = [
            {"role": "user", "content": goal_message},
            {"role": "assistant", "content": ai_response["content"]}
        ]
        
        # Step 2: Use goal decomposition API
        goal_request = {
            "goal_description": "Run a 5K race in 3 months",
            "life_areas": [{"id": 1, "name": "Health", "description": "Physical fitness"}],
            "existing_goals": [],
            "user_preferences": {"fitness_level": "beginner", "time_available": "30min daily"},
            "additional_context": "Complete beginner to running"
        }
        
        goal_response = client.post("/api/ai/decompose-goal", headers=headers, json=goal_request)
        assert goal_response.status_code == 200
        
        goal_data = goal_response.json()
        assert goal_data["status"] == "success"
        
        # Step 3: Ask follow-up questions about the plan
        follow_up_message = "This looks good! How should I track my progress?"
        
        chat_request2 = {
            "message": follow_up_message,
            "conversation_history": conversation_history,
            "user_context": {
                "recent_goal": "5K running",
                "plan_provided": True
            }
        }
        
        response2 = client.post("/api/ai/chat", headers=headers, json=chat_request2)
        assert response2.status_code == 200
        
        ai_response2 = response2.json()
        assert ai_response2["status"] == "success"
        
        # Should provide tracking advice
        content_lower = ai_response2["content"].lower()
        assert any(word in content_lower for word in ["track", "progress", "measure", "log", "record"])
    
    def test_motivation_and_obstacles_conversation(self, get_test_user_headers):
        """Simulate conversation about motivation issues and obstacles."""
        headers = get_test_user_headers
        
        # Start with a motivation issue
        motivation_flow = [
            {
                "user": "I'm struggling to stay motivated with my fitness goal",
                "intent": "motivation",
                "expected_response_type": "support"
            },
            {
                "user": "I keep skipping workouts because I'm too tired after work",
                "intent": "obstacle_identification",
                "expected_response_type": "solution"
            },
            {
                "user": "Maybe I should try working out in the morning instead?",
                "intent": "planning",
                "expected_response_type": "encouragement"
            }
        ]
        
        conversation_history = []
        
        for turn in motivation_flow:
            chat_request = {
                "message": turn["user"],
                "conversation_history": conversation_history,
                "user_context": {
                    "current_goal": "fitness",
                    "struggling": True,
                    "support_needed": True
                }
            }
            
            response = client.post("/api/ai/chat", headers=headers, json=chat_request)
            assert response.status_code == 200
            
            ai_response = response.json()
            assert ai_response["status"] == "success"
            assert len(ai_response["content"]) > 0
            
            # Update conversation
            conversation_history.extend([
                {"role": "user", "content": turn["user"]},
                {"role": "assistant", "content": ai_response["content"]}
            ])
            
            # Check response appropriateness
            content_lower = ai_response["content"].lower()
            
            if turn["expected_response_type"] == "support":
                assert any(word in content_lower for word in ["understand", "common", "normal", "help"])
            elif turn["expected_response_type"] == "solution":
                assert any(word in content_lower for word in ["try", "consider", "schedule", "time"])
            elif turn["expected_response_type"] == "encouragement":
                assert any(word in content_lower for word in ["great", "good", "excellent", "smart"])
    
    def test_progress_review_conversation(self, get_test_user_headers):
        """Simulate conversation about reviewing progress on goals."""
        headers = get_test_user_headers
        
        # Simulate user checking in on progress
        progress_conversation = [
            "It's been 2 weeks since we talked about my cooking goal. I've tried 3 new recipes!",
            "I'm having trouble finding time to practice more than once a week though",
            "Do you think I should adjust my goal or find better ways to make time?"
        ]
        
        conversation_history = []
        
        for i, message in enumerate(progress_conversation):
            chat_request = {
                "message": message,
                "conversation_history": conversation_history,
                "user_context": {
                    "goal_type": "cooking",
                    "progress_update": True,
                    "weeks_elapsed": 2
                }
            }
            
            response = client.post("/api/ai/chat", headers=headers, json=chat_request)
            assert response.status_code == 200
            
            ai_response = response.json()
            assert ai_response["status"] == "success"
            
            conversation_history.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": ai_response["content"]}
            ])
            
            # Validate response context awareness
            content_lower = ai_response["content"].lower()
            
            if i == 0:  # First message - celebrating progress
                assert any(word in content_lower for word in ["great", "good", "progress", "well done"])
            elif i == 1:  # Second message - addressing time constraints
                assert any(word in content_lower for word in ["time", "schedule", "busy", "understand"])
            elif i == 2:  # Third message - providing guidance
                assert any(word in content_lower for word in ["adjust", "realistic", "suggest", "consider"])
    
    def test_multi_goal_management_conversation(self, get_test_user_headers):
        """Simulate conversation about managing multiple goals."""
        headers = get_test_user_headers
        
        # User has multiple goals and needs help prioritizing
        multi_goal_flow = [
            "I have several goals: learning Spanish, getting fit, and reading more books. I'm feeling overwhelmed.",
            "I think fitness is most important, but I also really want to practice Spanish for my trip next month.",
            "How should I balance these without burning out?"
        ]
        
        conversation_history = []
        
        for message in multi_goal_flow:
            chat_request = {
                "message": message,
                "conversation_history": conversation_history,
                "user_context": {
                    "multiple_goals": True,
                    "feeling_overwhelmed": True,
                    "goals": ["spanish", "fitness", "reading"]
                }
            }
            
            response = client.post("/api/ai/chat", headers=headers, json=chat_request)
            assert response.status_code == 200
            
            ai_response = response.json()
            assert ai_response["status"] == "success"
            
            conversation_history.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": ai_response["content"]}
            ])
            
            # Check for appropriate advice
            content_lower = ai_response["content"].lower()
            
            if "overwhelmed" in message:
                assert any(word in content_lower for word in ["prioritize", "focus", "one", "balance"])
            if "balance" in message:
                assert any(word in content_lower for word in ["schedule", "time", "realistic", "small"])


class TestChatMemoryIntegration:
    """Test chat integration with memory service."""
    
    def test_chat_with_memory_context(self, get_test_user_headers):
        """Test that chat can reference previous conversations from memory."""
        headers = get_test_user_headers
        
        # First conversation about fitness
        initial_chat = {
            "message": "I want to start exercising regularly",
            "conversation_history": [],
            "user_context": {}
        }
        
        response1 = client.post("/api/ai/chat", headers=headers, json=initial_chat)
        assert response1.status_code == 200
        
        # Wait a moment for memory storage
        time.sleep(0.1)
        
        # Later conversation referencing fitness
        follow_up_chat = {
            "message": "Remember when we talked about exercise? I'm ready to start now.",
            "conversation_history": [],
            "user_context": {"referring_to_past": True}
        }
        
        response2 = client.post("/api/ai/chat", headers=headers, json=follow_up_chat)
        assert response2.status_code == 200
        
        ai_response2 = response2.json()
        assert ai_response2["status"] == "success"
        
        # AI should acknowledge the context (though may not have perfect memory in mock mode)
        content_lower = ai_response2["content"].lower()
        assert any(word in content_lower for word in ["exercise", "fitness", "start", "plan"])
    
    def test_memory_search_integration(self, get_test_user_headers):
        """Test searching through conversation memories."""
        headers = get_test_user_headers
        
        # Have a conversation that should be stored
        chat_request = {
            "message": "I love hiking and want to plan more outdoor adventures this summer",
            "conversation_history": [],
            "user_context": {"activity_type": "outdoor"}
        }
        
        response = client.post("/api/ai/chat", headers=headers, json=chat_request)
        assert response.status_code == 200
        
        # Wait for memory storage
        time.sleep(0.1)
        
        # Search for hiking-related memories
        search_response = client.post(
            "/api/ai/memory/search",
            headers=headers,
            params={"query": "hiking outdoor summer", "limit": 5}
        )
        
        # Memory service might not be available in test environment
        assert search_response.status_code in [200, 503]
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            assert "results" in search_data
            assert "query" in search_data


class TestChatWorkflows:
    """Test complete chat-based workflows."""
    
    def test_complete_goal_planning_workflow(self, get_test_user_headers):
        """Test complete workflow from idea to actionable plan through chat."""
        headers = get_test_user_headers
        
        workflow_steps = [
            {
                "step": "initial_idea",
                "message": "I've been thinking about learning photography",
                "expected": ["photography", "learn", "what", "type"]
            },
            {
                "step": "clarification",
                "message": "I want to learn portrait photography and maybe start a side business",
                "expected": ["portrait", "business", "equipment", "skills"]
            },
            {
                "step": "constraints",
                "message": "I have about $500 to invest and 5 hours per week",
                "expected": ["budget", "time", "realistic", "start"]
            },
            {
                "step": "next_steps",
                "message": "What should be my first step?",
                "expected": ["first", "start", "basic", "camera"]
            }
        ]
        
        conversation_history = []
        
        for step in workflow_steps:
            chat_request = {
                "message": step["message"],
                "conversation_history": conversation_history,
                "user_context": {"workflow_step": step["step"]}
            }
            
            response = client.post("/api/ai/chat", headers=headers, json=chat_request)
            assert response.status_code == 200
            
            ai_response = response.json()
            assert ai_response["status"] == "success"
            
            # Validate appropriate response for each step
            content_lower = ai_response["content"].lower()
            has_expected = any(keyword in content_lower for keyword in step["expected"])
            assert has_expected, f"Step {step['step']}: Expected {step['expected']} in response"
            
            conversation_history.extend([
                {"role": "user", "content": step["message"]},
                {"role": "assistant", "content": ai_response["content"]}
            ])
        
        # Final conversation should build on all previous context
        assert len(conversation_history) == len(workflow_steps) * 2
    
    def test_error_recovery_in_conversation(self, get_test_user_headers):
        """Test how chat handles and recovers from unclear or problematic inputs."""
        headers = get_test_user_headers
        
        problematic_inputs = [
            "",  # Empty message
            "asdfgh qwerty",  # Nonsense
            "I don't know what I want",  # Vague/confused
            "Everything is terrible and nothing works"  # Negative/overwhelming
        ]
        
        for problem_input in problematic_inputs:
            chat_request = {
                "message": problem_input,
                "conversation_history": [],
                "user_context": {}
            }
            
            response = client.post("/api/ai/chat", headers=headers, json=chat_request)
            
            # Should handle gracefully (might return 422 for empty, which is fine)
            assert response.status_code in [200, 422]
            
            if response.status_code == 200:
                ai_response = response.json()
                # Should provide helpful response even to problematic input
                assert ai_response["status"] == "success"
                assert len(ai_response["content"]) > 0
                
                # Should try to be helpful and redirect
                content_lower = ai_response["content"].lower()
                assert any(word in content_lower for word in [
                    "help", "understand", "tell", "more", "specific", "clarify", 
                    "assist", "support", "focus", "work", "together", "discuss"
                ])


class TestChatPerformance:
    """Test chat performance and concurrent usage."""
    
    def test_multiple_concurrent_chats(self, get_test_user_headers):
        """Test handling multiple chat requests simultaneously."""
        headers = get_test_user_headers
        
        import asyncio
        import aiohttp
        
        # This would be better with async test client, but for now test sequentially
        messages = [
            "Tell me about goal setting",
            "How do I stay motivated?",
            "What's the best way to track progress?",
            "I need help with time management"
        ]
        
        responses = []
        for message in messages:
            chat_request = {
                "message": message,
                "conversation_history": [],
                "user_context": {}
            }
            
            response = client.post("/api/ai/chat", headers=headers, json=chat_request)
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["content"]) > 0
    
    def test_long_conversation_performance(self, get_test_user_headers):
        """Test performance with long conversation history."""
        headers = get_test_user_headers
        
        # Build up a long conversation
        conversation_history = []
        
        for i in range(10):  # 10 turns = 20 messages in history
            user_message = f"This is message {i+1} in our conversation about my fitness goals"
            
            chat_request = {
                "message": user_message,
                "conversation_history": conversation_history,
                "user_context": {"long_conversation": True}
            }
            
            start_time = time.time()
            response = client.post("/api/ai/chat", headers=headers, json=chat_request)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            ai_response = response.json()
            assert ai_response["status"] == "success"
            
            # Response should still be reasonably fast
            assert response_time < 30  # 30 seconds max (generous for mock)
            
            # Update conversation history
            conversation_history.extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response["content"]}
            ])
        
        # Final conversation should have 20 messages
        assert len(conversation_history) == 20


# Integration with existing test fixtures
def test_chat_requires_authentication():
    """Test that chat endpoints require authentication."""
    from main import app
    from dependencies import get_current_user
    
    # Temporarily clear auth override to test actual auth behavior
    original_override = app.dependency_overrides.get(get_current_user)
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
    
    try:
        chat_request = {
            "message": "Hello",
            "conversation_history": []
        }
        
        response = client.post("/api/ai/chat", json=chat_request)
        assert response.status_code == 401
    finally:
        # Restore override
        if original_override:
            app.dependency_overrides[get_current_user] = original_override