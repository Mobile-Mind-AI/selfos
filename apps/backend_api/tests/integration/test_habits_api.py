"""
Integration tests for Habits API

Tests the full API endpoints for habit management.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHabitsAPI:
    """Integration test suite for Habits API"""

    def test_create_habit_success(self, client: TestClient, isolated_test_setup):
        """Test successful habit creation"""
        # Setup
        habit_data = {
            "title": "Exercise Daily",
            "description": "Go for a 30-minute walk",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
            "is_active": True,
        }

        # Execute
        response = client.post("/api/habits/", json=habit_data)

        # Verify
        assert response.status_code == 201
        created_habit = response.json()
        assert created_habit["title"] == habit_data["title"]
        assert created_habit["description"] == habit_data["description"]
        assert created_habit["is_active"]
        assert created_habit["current_streak"] == 0
        assert created_habit["total_completions"] == 0
        assert "id" in created_habit

    def test_create_habit_invalid_data(self, client: TestClient, isolated_test_setup):
        """Test habit creation with invalid data"""
        # Setup - missing required fields
        habit_data = {"description": "Missing title"}

        # Execute
        response = client.post("/api/habits/", json=habit_data)

        # Verify
        assert response.status_code == 422  # Validation error

    def test_list_habits_empty(self, client: TestClient, isolated_test_setup):
        """Test listing habits when user has none"""
        # Execute
        response = client.get("/api/habits/")

        # Verify
        assert response.status_code == 200
        habits = response.json()
        assert habits == []

    def test_list_habits_with_data(self, client: TestClient, isolated_test_setup):
        """Test listing habits when user has some"""
        # Setup - create test habits
        habit_data_1 = {
            "title": "Morning Exercise",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
        }
        habit_data_2 = {
            "title": "Weekly Reading",
            "recurrence_rule": {
                "type": "weekly",
                "target_count": 3,
                "target_type": "count",
            },
            "is_active": False,
        }

        client.post("/api/habits/", json=habit_data_1)
        client.post("/api/habits/", json=habit_data_2)

        # Execute
        response = client.get("/api/habits/")

        # Verify
        assert response.status_code == 200
        habits = response.json()
        assert len(habits) == 2

        # Check that habits have enriched data
        for habit in habits:
            assert "current_period_progress" in habit
            assert "recent_completions" in habit

    def test_list_habits_filter_active(self, client: TestClient, isolated_test_setup):
        """Test filtering habits by active status"""
        # Setup - create one active, one inactive habit
        active_habit = {
            "title": "Active Habit",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
            "is_active": True,
        }
        inactive_habit = {
            "title": "Inactive Habit",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
            "is_active": False,
        }

        client.post("/api/habits/", json=active_habit)
        client.post("/api/habits/", json=inactive_habit)

        # Execute - get only active habits
        response = client.get("/api/habits?is_active=true")

        # Verify
        assert response.status_code == 200
        habits = response.json()
        assert len(habits) == 1
        assert habits[0]["title"] == "Active Habit"
        assert habits[0]["is_active"]

    def test_get_habit_success(self, client: TestClient, isolated_test_setup):
        """Test getting a specific habit"""
        # Setup - create a habit
        habit_data = {
            "title": "Test Habit",
            "recurrence_rule": {
                "type": "weekly",
                "target_count": 3,
                "target_type": "count",
            },
        }

        create_response = client.post("/api/habits/", json=habit_data)
        created_habit = create_response.json()
        habit_id = created_habit["id"]

        # Execute
        response = client.get(f"/api/habits/{habit_id}")

        # Verify
        assert response.status_code == 200
        habit = response.json()
        assert habit["id"] == habit_id
        assert habit["title"] == habit_data["title"]
        assert "current_period_progress" in habit
        assert "recent_completions" in habit

    def test_get_habit_not_found(self, client: TestClient, isolated_test_setup):
        """Test getting a non-existent habit"""
        # Execute
        response = client.get("/api/habits/999/")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_habit_success(self, client: TestClient, isolated_test_setup):
        """Test updating a habit"""
        # Setup - create a habit
        habit_data = {
            "title": "Original Title",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
        }

        create_response = client.post("/api/habits/", json=habit_data)
        created_habit = create_response.json()
        habit_id = created_habit["id"]

        # Execute - update the habit
        update_data = {"title": "Updated Title", "description": "Updated description"}

        response = client.put(f"/api/habits/{habit_id}", json=update_data)

        # Verify
        assert response.status_code == 200
        updated_habit = response.json()
        assert updated_habit["title"] == "Updated Title"
        assert updated_habit["description"] == "Updated description"

    def test_update_habit_not_found(self, client: TestClient, isolated_test_setup):
        """Test updating a non-existent habit"""
        # Execute
        update_data = {"title": "New Title"}
        response = client.put("/api/habits/999/", json=update_data)

        # Verify
        assert response.status_code == 404

    def test_delete_habit_success(self, client: TestClient, isolated_test_setup):
        """Test deleting a habit"""
        # Setup - create a habit
        habit_data = {
            "title": "Habit to Delete",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
        }

        create_response = client.post("/api/habits/", json=habit_data)
        created_habit = create_response.json()
        habit_id = created_habit["id"]

        # Execute - delete the habit
        response = client.delete(f"/api/habits/{habit_id}")

        # Verify deletion
        assert response.status_code == 204

        # Verify habit no longer exists
        get_response = client.get(f"/api/habits/{habit_id}")
        assert get_response.status_code == 404

    def test_delete_habit_not_found(self, client: TestClient, isolated_test_setup):
        """Test deleting a non-existent habit"""
        # Execute
        response = client.delete("/api/habits/999/")

        # Verify
        assert response.status_code == 404

    def test_complete_habit_success(self, client: TestClient, isolated_test_setup):
        """Test completing a habit"""
        # Setup - create a habit
        habit_data = {
            "title": "Daily Exercise",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
        }

        create_response = client.post("/api/habits/", json=habit_data)
        created_habit = create_response.json()
        habit_id = created_habit["id"]

        # Execute - complete the habit
        completion_data = {
            "notes": "Great workout today!",
            "duration_minutes": 30,
            "intensity_rating": 8,
        }

        response = client.post(f"/api/habits/{habit_id}/complete", json=completion_data)

        # Verify
        assert response.status_code == 201
        completion = response.json()
        assert completion["habit_id"] == habit_id
        assert completion["notes"] == "Great workout today!"
        assert completion["duration_minutes"] == 30
        assert completion["intensity_rating"] == 8
        assert "completion_date" in completion
        assert "id" in completion

    def test_complete_habit_duplicate_same_day(
        self, client: TestClient, isolated_test_setup
    ):
        """Test completing a habit twice on the same day"""
        # Setup - create and complete a habit
        habit_data = {
            "title": "Daily Exercise",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
        }

        create_response = client.post("/api/habits/", json=habit_data)
        habit_id = create_response.json()["id"]

        # First completion
        completion_data = {"notes": "First completion"}
        first_response = client.post(
            f"/api/habits/{habit_id}/complete", json=completion_data
        )
        assert first_response.status_code == 201

        # Execute - try to complete again on the same day
        second_response = client.post(
            f"/api/habits/{habit_id}/complete", json=completion_data
        )

        # Verify - should return existing completion
        assert second_response.status_code == 201  # Returns existing completion

        first_completion = first_response.json()
        second_completion = second_response.json()
        assert first_completion["id"] == second_completion["id"]

    def test_complete_habit_not_found(self, client: TestClient, isolated_test_setup):
        """Test completing a non-existent habit"""
        # Execute
        completion_data = {"notes": "Test completion"}
        response = client.post("/api/habits/999/complete/", json=completion_data)

        # Verify
        assert response.status_code == 404

    def test_get_habit_completions(self, client: TestClient, isolated_test_setup):
        """Test getting completions for a habit"""
        # Setup - create habit and add completions
        habit_data = {
            "title": "Daily Exercise",
            "recurrence_rule": {
                "type": "daily",
                "target_count": 1,
                "target_type": "count",
            },
        }

        create_response = client.post("/api/habits/", json=habit_data)
        habit_id = create_response.json()["id"]

        # Add some completions (mocking different dates would require more setup)
        completion_data = {"notes": "Test completion"}
        client.post(f"/api/habits/{habit_id}/complete", json=completion_data)

        # Execute
        response = client.get(f"/api/habits/{habit_id}/completions")

        # Verify
        assert response.status_code == 200
        completions = response.json()
        assert len(completions) == 1
        assert completions[0]["habit_id"] == habit_id
        assert completions[0]["notes"] == "Test completion"

    @pytest.mark.skip(reason="Progress calculation not implemented")
    def test_get_habit_progress(self, client: TestClient, isolated_test_setup):
        """Test getting progress for a habit"""
        # Setup - create a weekly habit
        habit_data = {
            "title": "Weekly Exercise",
            "recurrence_rule": {
                "type": "weekly",
                "target_count": 3,
                "target_type": "count",
            },
        }

        create_response = client.post("/api/habits/", json=habit_data)
        habit_id = create_response.json()["id"]

        # Execute
        response = client.get(f"/api/habits/{habit_id}/progress")

        # Verify
        assert response.status_code == 200
        progress = response.json()
        assert progress["habit_id"] == habit_id
        assert progress["target_count"] == 3
        assert progress["actual_count"] == 0  # No completions yet
        assert progress["completion_rate"] == 0.0
        assert not progress["is_completed"]
        assert "period_start" in progress
        assert "period_end" in progress

    def test_get_habit_progress_not_found(
        self, client: TestClient, isolated_test_setup
    ):
        """Test getting progress for non-existent habit"""
        # Execute
        response = client.get("/api/habits/999/progress/")

        # Verify
        assert response.status_code == 404

    def test_habit_lifecycle_with_completions(
        self, client: TestClient, isolated_test_setup
    ):
        """Test complete habit lifecycle with completions and progress tracking"""
        # Step 1: Create a weekly habit
        habit_data = {
            "title": "Weekly Reading",
            "description": "Read books 3 times per week",
            "recurrence_rule": {
                "type": "weekly",
                "target_count": 3,
                "target_type": "count",
            },
        }

        create_response = client.post("/api/habits/", json=habit_data)
        assert create_response.status_code == 201
        habit = create_response.json()
        habit_id = habit["id"]

        # Step 2: Complete the habit once
        completion_data = {
            "notes": "Read 'The Pragmatic Programmer'",
            "duration_minutes": 60,
            "intensity_rating": 7,
        }

        complete_response = client.post(
            f"/api/habits/{habit_id}/complete", json=completion_data
        )
        assert complete_response.status_code == 201

        # Step 3: Check progress
        progress_response = client.get(f"/api/habits/{habit_id}/progress")
        assert progress_response.status_code == 200
        progress = progress_response.json()
        assert progress["actual_count"] == 1
        assert progress["target_count"] == 3
        assert progress["completion_rate"] == 1.0 / 3.0
        assert not progress["is_completed"]

        # Step 4: Check habit details (should include recent completions)
        habit_response = client.get(f"/api/habits/{habit_id}")
        assert habit_response.status_code == 200
        updated_habit = habit_response.json()
        assert updated_habit["total_completions"] == 1
        assert len(updated_habit["recent_completions"]) == 1

        # Step 5: Update habit
        update_data = {"description": "Updated description"}
        update_response = client.put(f"/api/habits/{habit_id}", json=update_data)
        assert update_response.status_code == 200

        # Step 6: List habits (should show our habit with progress)
        list_response = client.get("/api/habits/")
        assert list_response.status_code == 200
        habits = list_response.json()
        assert len(habits) == 1
        assert habits[0]["id"] == habit_id

    @pytest.mark.parametrize(
        "recurrence_type,target_count",
        [
            ("daily", 1),
            ("weekly", 5),
            ("monthly", 15),
        ],
    )
    def test_different_recurrence_types(
        self, client: TestClient, isolated_test_setup, recurrence_type, target_count
    ):
        """Test creating habits with different recurrence types"""
        # Setup
        habit_data = {
            "title": f"{recurrence_type.capitalize()} Habit",
            "recurrence_rule": {
                "type": recurrence_type,
                "target_count": target_count,
                "target_type": "count",
            },
        }

        # Execute
        response = client.post("/api/habits/", json=habit_data)

        # Verify
        assert response.status_code == 201
        habit = response.json()
        assert habit["recurrence_rule"]["type"] == recurrence_type
        assert habit["recurrence_rule"]["target_count"] == target_count

    def test_habit_validation_errors(self, client: TestClient, isolated_test_setup):
        """Test various validation errors in habit creation"""
        # Test cases for invalid data
        invalid_cases = [
            # Missing title
            {
                "data": {
                    "recurrence_rule": {
                        "type": "daily",
                        "target_count": 1,
                        "target_type": "count",
                    }
                },
                "description": "missing title",
            },
            # Missing recurrence_rule
            {"data": {"title": "Test Habit"}, "description": "missing recurrence_rule"},
            # Invalid recurrence type
            {
                "data": {
                    "title": "Test Habit",
                    "recurrence_rule": {
                        "type": "invalid",
                        "target_count": 1,
                        "target_type": "count",
                    },
                },
                "description": "invalid recurrence type",
            },
            # Invalid target_count
            {
                "data": {
                    "title": "Test Habit",
                    "recurrence_rule": {
                        "type": "daily",
                        "target_count": 0,
                        "target_type": "count",
                    },
                },
                "description": "zero target_count",
            },
            # Target count too high
            {
                "data": {
                    "title": "Test Habit",
                    "recurrence_rule": {
                        "type": "daily",
                        "target_count": 101,
                        "target_type": "count",
                    },
                },
                "description": "target_count too high",
            },
        ]

        for case in invalid_cases:
            response = client.post("/api/habits/", json=case["data"])
            assert (
                response.status_code == 422
            ), f"Failed for case: {case['description']}"
