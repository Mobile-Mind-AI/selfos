import os
import sys

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)



def test_create_task(client, db):
    """Test creating a new task"""
    # First create a goal using the client from conftest
    goal_data = {"title": "Test Goal for Task"}
    goal_response = client.post("/api/goals/", json=goal_data)

    # Check if goal was created successfully
    assert (
        goal_response.status_code == 201
    ), f"Failed to create goal: {goal_response.text}"
    goal_id = goal_response.json()["id"]

    # Create task
    task_data = {
        "goal_id": goal_id,
        "title": "Test Task",
        "description": "Test Task Description",
        "due_date": "2024-12-31T23:59:59",
        "estimated_hours": 2.0,
        "status": "in_progress",
        "progress": 25.0,
        "life_area_id": None,
        "dependencies": [],
    }

    response = client.post("/api/tasks/", json=task_data)

    if response.status_code != 201:
        print(f"Task creation failed: {response.status_code}")
        print(f"Response: {response.text}")

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Task Description"
    assert data["goal_id"] == goal_id
    assert data["status"] == "in_progress"
    assert data["progress"] == 25.0


def test_create_task_minimal(client, db):
    """Test creating a task with minimal data"""
    # First create a goal
    goal_data = {"title": "Test Goal"}
    goal_response = client.post("/api/goals/", json=goal_data)
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]

    # Create task with minimal data
    task_data = {"goal_id": goal_id, "title": "Minimal Task"}

    response = client.post("/api/tasks/", json=task_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Task"
    assert data["goal_id"] == goal_id
    assert data["status"] == "todo"  # Default status


def test_list_tasks(client, db):
    """Test listing tasks"""
    # First create a goal and task
    goal_data = {"title": "Test Goal"}
    goal_response = client.post("/api/goals/", json=goal_data)
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]

    # Create multiple tasks
    for i in range(3):
        task_data = {"goal_id": goal_id, "title": f"Task {i+1}"}
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == 201

    # List tasks
    response = client.get("/api/tasks/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    # Tasks should be sorted by created_at desc
    for i, task in enumerate(data):
        assert task["title"] == f"Task {3-i}"


def test_get_task(client, db):
    """Test getting a specific task"""
    # First create a goal and task
    goal_data = {"title": "Test Goal"}
    goal_response = client.post("/api/goals/", json=goal_data)
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]

    task_data = {
        "goal_id": goal_id,
        "title": "Test Task",
        "description": "Test Description",
    }
    create_response = client.post("/api/tasks/", json=task_data)
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    # Get the task
    response = client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"


def test_update_task(client, db):
    """Test updating a task"""
    # First create a goal and task
    goal_data = {"title": "Test Goal"}
    goal_response = client.post("/api/goals/", json=goal_data)
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]

    task_data = {"goal_id": goal_id, "title": "Original Title", "status": "todo"}
    create_response = client.post("/api/tasks/", json=task_data)
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    # Update the task (must include goal_id for TaskCreate schema)
    update_data = {
        "goal_id": goal_id,
        "title": "Updated Title",
        "description": "New Description",
        "status": "completed",
        "progress": 100.0,
    }
    response = client.put(f"/api/tasks/{task_id}", json=update_data)

    if response.status_code != 200:
        print(f"Update failed: {response.status_code}")
        print(f"Response: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "New Description"
    assert data["status"] == "completed"
    assert data["progress"] == 100.0


def test_delete_task(client, db):
    """Test deleting a task"""
    # First create a goal and task
    goal_data = {"title": "Test Goal"}
    goal_response = client.post("/api/goals/", json=goal_data)
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]

    task_data = {"goal_id": goal_id, "title": "Task to Delete"}
    create_response = client.post("/api/tasks/", json=task_data)
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    # Delete the task
    response = client.delete(f"/api/tasks/{task_id}")

    assert response.status_code == 204

    # Verify task is deleted
    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404
