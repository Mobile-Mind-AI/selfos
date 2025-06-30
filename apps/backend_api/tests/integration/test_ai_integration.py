"""
Integration Tests for AI API Endpoints

Tests the AI-powered goal decomposition and chat functionality
with actual AI orchestrator integration.
"""

import pytest
from fastapi.testclient import TestClient
import json

from main import app
# get_test_user_headers is available from conftest.py fixture


client = TestClient(app)


class TestAIIntegration:
    """Integration tests for AI endpoints."""
    
    def test_goal_decomposition_basic(self, get_test_user_headers):
        """Test basic goal decomposition functionality."""
        headers = get_test_user_headers
        
        goal_request = {
            "goal_description": "Learn to play guitar",
            "life_areas": [{"id": 1, "name": "Hobbies", "description": "Personal interests"}],
            "existing_goals": [],
            "user_preferences": {"learning_style": "hands-on"},
            "additional_context": "I'm a complete beginner"
        }
        
        response = client.post(
            "/api/ai/decompose-goal",
            headers=headers,
            json=goal_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "request_id" in data
        assert "status" in data
        assert "content" in data
        assert "suggested_tasks" in data
        assert "overall_timeline" in data
        assert "potential_challenges" in data
        assert "success_metrics" in data
        assert "next_steps" in data
        
        # Check that we got a reasonable response
        assert len(data["content"]) > 0
        assert data["status"] == "success"
        
        # For mock client, we should get some basic structure
        if data["model_used"] == "mock-model":
            assert "research" in data["content"].lower() or "plan" in data["content"].lower()
    
    def test_goal_decomposition_with_context(self, get_test_user_headers):
        """Test goal decomposition with rich context."""
        headers = get_test_user_headers
        
        goal_request = {
            "goal_description": "Start a small business selling handmade crafts",
            "life_areas": [
                {"id": 1, "name": "Career", "description": "Professional development"},
                {"id": 2, "name": "Finance", "description": "Financial goals"}
            ],
            "existing_goals": [
                {"id": 1, "title": "Save $5000", "status": "in_progress"}
            ],
            "user_preferences": {
                "work_style": "methodical",
                "time_availability": "evenings and weekends"
            },
            "additional_context": "I have experience with woodworking and jewelry making. Budget is limited."
        }
        
        response = client.post(
            "/api/ai/decompose-goal",
            headers=headers,
            json=goal_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the request was processed
        assert data["status"] == "success"
        assert len(data["content"]) > 0
        
        # Check for processing metrics
        assert "processing_time" in data
        assert isinstance(data["processing_time"], (int, float))
    
    def test_chat_basic(self, get_test_user_headers):
        """Test basic chat functionality."""
        headers = get_test_user_headers
        
        chat_request = {
            "message": "Help me plan my week",
            "conversation_history": [],
            "user_context": {"timezone": "America/New_York"}
        }
        
        response = client.post(
            "/api/ai/chat",
            headers=headers,
            json=chat_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "request_id" in data
        assert "status" in data
        assert "content" in data
        assert "intent_detected" in data
        assert "suggested_actions" in data
        assert "follow_up_questions" in data
        
        # Check that we got a reasonable response
        assert len(data["content"]) > 0
        assert data["status"] == "success"
    
    def test_chat_goal_intent(self, get_test_user_headers):
        """Test chat with goal-related intent."""
        headers = get_test_user_headers
        
        chat_request = {
            "message": "I want to learn Spanish this year",
            "conversation_history": [],
            "user_context": {}
        }
        
        response = client.post(
            "/api/ai/chat",
            headers=headers,
            json=chat_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert len(data["content"]) > 0
        
        # Should detect goal-related intent
        assert data["intent_detected"] == "goal_setting" or data["intent_detected"] is None
    
    def test_chat_with_history(self, get_test_user_headers):
        """Test chat with conversation history."""
        headers = get_test_user_headers
        
        chat_request = {
            "message": "What's the next step?",
            "conversation_history": [
                {"role": "user", "content": "I want to start exercising"},
                {"role": "assistant", "content": "Great! Let's create a fitness plan for you."}
            ],
            "user_context": {}
        }
        
        response = client.post(
            "/api/ai/chat",
            headers=headers,
            json=chat_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert len(data["content"]) > 0
    
    def test_health_check(self):
        """Test AI service health check."""
        response = client.get("/api/ai/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check health response structure
        assert "status" in data
        assert "providers" in data
        assert "cache_size" in data
        assert "metrics" in data
        
        # Should have at least local/mock provider
        assert len(data["providers"]) >= 1
    
    def test_memory_stats(self, get_test_user_headers):
        """Test memory statistics endpoint."""
        headers = get_test_user_headers
        
        response = client.get("/api/ai/memory/stats", headers=headers)
        
        # Memory service might not be available in test environment
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "vector_store_type" in data or "total_entries" in data
    
    def test_memory_search(self, get_test_user_headers):
        """Test memory search functionality."""
        headers = get_test_user_headers
        
        # First, make a goal decomposition to have something to search
        goal_request = {
            "goal_description": "Read 12 books this year",
            "life_areas": [],
            "existing_goals": []
        }
        
        goal_response = client.post(
            "/api/ai/decompose-goal",
            headers=headers,
            json=goal_request
        )
        
        assert goal_response.status_code == 200
        
        # Now search for it
        search_params = {
            "query": "books reading",
            "limit": 5
        }
        
        response = client.post(
            "/api/ai/memory/search",
            headers=headers,
            params=search_params
        )
        
        # Memory service might not be available
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert "total_results" in data
            assert isinstance(data["results"], list)
    
    def test_error_handling_invalid_goal(self, get_test_user_headers):
        """Test error handling for invalid goal description."""
        headers = get_test_user_headers
        
        goal_request = {
            "goal_description": "",  # Empty goal
            "life_areas": [],
            "existing_goals": []
        }
        
        response = client.post(
            "/api/ai/decompose-goal",
            headers=headers,
            json=goal_request
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            data = response.json()
            # Should still return a response, possibly with error status
            assert "status" in data
    
    def test_error_handling_invalid_chat(self, get_test_user_headers):
        """Test error handling for invalid chat message."""
        headers = get_test_user_headers
        
        chat_request = {
            "message": "",  # Empty message
            "conversation_history": []
        }
        
        response = client.post(
            "/api/ai/chat",
            headers=headers,
            json=chat_request
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_unauthorized_access(self):
        """Test that AI endpoints require authentication."""
        from main import app
        from dependencies import get_current_user
        
        # Temporarily clear auth override to test actual auth behavior
        original_override = app.dependency_overrides.get(get_current_user)
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        
        try:
            goal_request = {
                "goal_description": "Test goal",
                "life_areas": [],
                "existing_goals": []
            }
            
            response = client.post("/api/ai/decompose-goal", json=goal_request)
            assert response.status_code == 401
            
            chat_request = {
                "message": "Test message",
                "conversation_history": []
            }
            
            response = client.post("/api/ai/chat", json=chat_request)
            assert response.status_code == 401
        finally:
            # Restore override
            if original_override:
                app.dependency_overrides[get_current_user] = original_override
        
        response = client.get("/api/ai/memory/stats")
        assert response.status_code == 401


class TestAIWorkflow:
    """Test complete AI workflow scenarios."""
    
    def test_goal_to_chat_workflow(self, get_test_user_headers):
        """Test a complete workflow from goal decomposition to chat follow-up."""
        headers = get_test_user_headers
        
        # Step 1: Decompose a goal
        goal_request = {
            "goal_description": "Get fit and healthy this year",
            "life_areas": [{"id": 1, "name": "Health", "description": "Physical and mental health"}],
            "existing_goals": []
        }
        
        goal_response = client.post(
            "/api/ai/decompose-goal",
            headers=headers,
            json=goal_request
        )
        
        assert goal_response.status_code == 200
        goal_data = goal_response.json()
        assert goal_data["status"] == "success"
        
        # Step 2: Use chat to ask follow-up questions
        chat_request = {
            "message": "I'm interested in the fitness plan you suggested. How should I start?",
            "conversation_history": [
                {"role": "user", "content": goal_request["goal_description"]},
                {"role": "assistant", "content": goal_data["content"][:200] + "..."}
            ]
        }
        
        chat_response = client.post(
            "/api/ai/chat",
            headers=headers,
            json=chat_request
        )
        
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert chat_data["status"] == "success"
        
        # Both should have processed successfully
        assert len(goal_data["content"]) > 0
        assert len(chat_data["content"]) > 0
    
    def test_multiple_goals_workflow(self, get_test_user_headers):
        """Test handling multiple related goals."""
        headers = get_test_user_headers
        
        goals = [
            {"goal_description": "Learn a new programming language", "context": "career development"},
            {"goal_description": "Build a personal project", "context": "apply new skills"},
            {"goal_description": "Contribute to open source", "context": "give back to community"}
        ]
        
        responses = []
        
        for goal_info in goals:
            goal_request = {
                "goal_description": goal_info["goal_description"],
                "life_areas": [{"id": 1, "name": "Career", "description": "Professional growth"}],
                "existing_goals": [{"title": g["goal_description"], "status": "planned"} for g in goals[:len(responses)]],
                "additional_context": goal_info["context"]
            }
            
            response = client.post(
                "/api/ai/decompose-goal",
                headers=headers,
                json=goal_request
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            responses.append(data)
        
        # All goals should have been processed
        assert len(responses) == 3
        
        # Each should have meaningful content
        for response in responses:
            assert len(response["content"]) > 0
            assert response["processing_time"] is not None