import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from dependencies import get_db, get_current_user
from models import Base

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

def override_get_db_integration():
    """Override database dependency for testing integration"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user_integration():
    """Override authentication dependency for testing integration"""
    return {
        "uid": "test_user_123",  # Use consistent test user ID
        "email": "integration@example.com",
        "roles": ["user"]
    }

# Override dependencies - clear any existing overrides first
app.dependency_overrides.clear()
app.dependency_overrides[get_db] = override_get_db_integration
app.dependency_overrides[get_current_user] = override_get_current_user_integration

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before each test"""
    # Clear all data before each test
    db = TestingSessionLocal()
    try:
        from sqlalchemy import text
        # Clear tables in dependency order
        db.execute(text("DELETE FROM media_attachments"))
        db.execute(text("DELETE FROM tasks"))
        db.execute(text("DELETE FROM goals"))
        db.execute(text("DELETE FROM life_areas"))
        db.execute(text("DELETE FROM users"))
        db.commit()
    finally:
        db.close()
    yield
    # Cleanup after test if needed


class TestGoalsAndTasksIntegration:
    """Integration tests for Goals and Tasks workflow"""
    
    def test_complete_workflow_goal_to_tasks(self):
        """Test complete workflow: create goal, add tasks, update, delete"""
        
        # Step 1: Create a goal
        goal_data = {
            "title": "Learn Python Programming",
            "description": "Master Python for web development",
            "status": "in_progress",
            "progress": 0.0,
            "life_area_id": None
        }
        
        goal_response = client.post("/api/goals", json=goal_data)
        assert goal_response.status_code == 200
        goal = goal_response.json()
        goal_id = goal["id"]
        
        assert goal["title"] == "Learn Python Programming"
        assert goal["user_id"] == "test_user_123"
        
        # Step 2: Create multiple tasks for the goal
        task1_data = {
            "goal_id": goal_id,
            "title": "Setup Python Environment",
            "description": "Install Python and IDE",
            "duration": 60,
            "status": "completed",
            "progress": 100.0
        }
        
        task1_response = client.post("/api/tasks", json=task1_data)
        assert task1_response.status_code == 200
        task1 = task1_response.json()
        task1_id = task1["id"]
        
        task2_data = {
            "goal_id": goal_id,
            "title": "Learn Basic Syntax",
            "description": "Variables, loops, functions",
            "duration": 180,
            "status": "in_progress",
            "progress": 50.0,
            "dependencies": [task1_id]
        }
        
        task2_response = client.post("/api/tasks", json=task2_data)
        assert task2_response.status_code == 200
        task2 = task2_response.json()
        task2_id = task2["id"]
        
        task3_data = {
            "goal_id": goal_id,
            "title": "Build First Web App",
            "description": "Create a simple Flask application",
            "duration": 300,
            "status": "todo",
            "progress": 0.0,
            "dependencies": [task2_id]
        }
        
        task3_response = client.post("/api/tasks", json=task3_data)
        assert task3_response.status_code == 200
        task3 = task3_response.json()
        
        # Step 3: Verify all tasks are linked to goal
        tasks_response = client.get("/api/tasks")
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()
        
        assert len(tasks) == 3
        for task in tasks:
            assert task["goal_id"] == goal_id
            assert task["user_id"] == "test_user_123"
        
        # Step 4: Update task progress
        task2_update = {
            "goal_id": goal_id,
            "title": "Learn Basic Syntax",
            "description": "Variables, loops, functions - COMPLETED!",
            "duration": 180,
            "status": "completed",
            "progress": 100.0,
            "dependencies": [task1_id]
        }
        
        task2_update_response = client.put(f"/api/tasks/{task2_id}", json=task2_update)
        assert task2_update_response.status_code == 200
        updated_task2 = task2_update_response.json()
        assert updated_task2["status"] == "completed"
        assert updated_task2["progress"] == 100.0
        
        # Step 5: Update goal progress based on tasks
        goal_update = {
            "title": "Learn Python Programming",
            "description": "Master Python for web development - Making Progress!",
            "status": "in_progress",
            "progress": 50.0,  # 2 of 3 tasks completed
            "life_area_id": None
        }
        
        goal_update_response = client.put(f"/api/goals/{goal_id}", json=goal_update)
        assert goal_update_response.status_code == 200
        updated_goal = goal_update_response.json()
        assert updated_goal["progress"] == 50.0
        
        # Step 6: Complete final task
        task3_update = {
            "goal_id": goal_id,
            "title": "Build First Web App",
            "description": "Create a simple Flask application - DONE!",
            "duration": 300,
            "status": "completed",
            "progress": 100.0,
            "dependencies": [task2_id]
        }
        
        task3_update_response = client.put(f"/api/tasks/{task3['id']}", json=task3_update)
        assert task3_update_response.status_code == 200
        
        # Step 7: Complete the goal
        goal_complete = {
            "title": "Learn Python Programming",
            "description": "Master Python for web development - COMPLETED!",
            "status": "completed",
            "progress": 100.0,
            "life_area_id": None
        }
        
        goal_complete_response = client.put(f"/api/goals/{goal_id}", json=goal_complete)
        assert goal_complete_response.status_code == 200
        completed_goal = goal_complete_response.json()
        assert completed_goal["status"] == "completed"
        assert completed_goal["progress"] == 100.0
        
        # Step 8: Verify final state
        final_goal_response = client.get(f"/api/goals/{goal_id}")
        assert final_goal_response.status_code == 200
        final_goal = final_goal_response.json()
        assert final_goal["status"] == "completed"
        
        final_tasks_response = client.get("/api/tasks")
        final_tasks = final_tasks_response.json()
        completed_tasks = [t for t in final_tasks if t["status"] == "completed"]
        assert len(completed_tasks) == 3
    
    def test_cascade_operations(self):
        """Test operations that might affect related data"""
        
        # Create goal with tasks
        goal_data = {"title": "Test Cascade Goal"}
        goal_response = client.post("/api/goals", json=goal_data)
        goal_id = goal_response.json()["id"]
        
        # Create tasks
        for i in range(3):
            task_data = {
                "goal_id": goal_id,
                "title": f"Task {i+1}",
                "description": f"Description for task {i+1}"
            }
            client.post("/api/tasks", json=task_data)
        
        # Verify tasks exist
        tasks_response = client.get("/api/tasks")
        tasks = tasks_response.json()
        goal_tasks = [t for t in tasks if t["goal_id"] == goal_id]
        assert len(goal_tasks) == 3
        
        # Delete goal (cascades to delete tasks due to relationship)
        delete_response = client.delete(f"/api/goals/{goal_id}")
        assert delete_response.status_code == 204
        
        # Verify goal is deleted
        get_goal_response = client.get(f"/api/goals/{goal_id}")
        assert get_goal_response.status_code == 404
        
        # Tasks should be deleted too (cascade delete implemented)
        tasks_after_delete = client.get("/api/tasks").json()
        remaining_goal_tasks = [t for t in tasks_after_delete if t["goal_id"] == goal_id]
        assert len(remaining_goal_tasks) == 0  # Tasks cascaded delete
    
    def test_user_isolation(self):
        """Test that users can only access their own data"""
        
        # Create data as integration_test_user
        goal_data = {"title": "User Isolation Test Goal"}
        goal_response = client.post("/api/goals", json=goal_data)
        goal_id = goal_response.json()["id"]
        
        task_data = {"goal_id": goal_id, "title": "User Isolation Test Task"}
        task_response = client.post("/api/tasks", json=task_data)
        task_id = task_response.json()["id"]
        
        # Verify user can access their data
        user_goals = client.get("/api/goals").json()
        user_tasks = client.get("/api/tasks").json()
        
        assert len(user_goals) >= 1  # May have data from previous tests
        assert len(user_tasks) >= 1   # May have data from previous tests
        # Check that all data belongs to the test user
        for goal in user_goals:
            assert goal["user_id"] == "test_user_123"
        for task in user_tasks:
            assert task["user_id"] == "test_user_123"
        
        # Simulate different user (change override)
        def override_get_different_user():
            return {
                "uid": "different_user_123",
                "email": "different@example.com", 
                "roles": ["user"]
            }
        
        app.dependency_overrides[get_current_user] = override_get_different_user
        
        # Different user should see no data
        different_user_goals = client.get("/api/goals").json()
        different_user_tasks = client.get("/api/tasks").json()
        
        assert len(different_user_goals) == 0
        assert len(different_user_tasks) == 0
        
        # Different user should not be able to access specific items
        goal_response = client.get(f"/api/goals/{goal_id}")
        task_response = client.get(f"/api/tasks/{task_id}")
        
        assert goal_response.status_code == 404
        assert task_response.status_code == 404
        
        # Restore original user
        app.dependency_overrides[get_current_user] = override_get_current_user_integration
    
    def test_data_consistency(self):
        """Test data consistency across operations"""
        
        # Create goal
        goal_data = {
            "title": "Consistency Test",
            "status": "todo",
            "progress": 0.0
        }
        goal_response = client.post("/api/goals", json=goal_data)
        goal_id = goal_response.json()["id"]
        
        # Create task
        task_data = {
            "goal_id": goal_id,
            "title": "Consistency Task",
            "status": "todo",
            "progress": 0.0
        }
        task_response = client.post("/api/tasks", json=task_data)
        task_id = task_response.json()["id"]
        
        # Get creation timestamps
        initial_goal = client.get(f"/api/goals/{goal_id}").json()
        initial_task = client.get(f"/api/tasks/{task_id}").json()
        
        created_at_goal = initial_goal["created_at"]
        created_at_task = initial_task["created_at"]
        
        # Update task
        task_update = {
            "goal_id": goal_id,
            "title": "Updated Consistency Task",
            "status": "completed",
            "progress": 100.0
        }
        client.put(f"/api/tasks/{task_id}", json=task_update)
        
        # Verify timestamps
        updated_task = client.get(f"/api/tasks/{task_id}").json()
        
        # Created timestamp should not change
        assert updated_task["created_at"] == created_at_task
        # Updated timestamp should change
        assert updated_task["updated_at"] != updated_task["created_at"]
        
        # Verify data integrity
        assert updated_task["title"] == "Updated Consistency Task"
        assert updated_task["status"] == "completed"
        assert updated_task["progress"] == 100.0
        assert updated_task["goal_id"] == goal_id


# Module cleanup
def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session"""
    # Clean up dependency overrides for this module
    app.dependency_overrides.clear()
    engine.dispose()